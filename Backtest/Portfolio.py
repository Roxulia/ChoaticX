from dataclasses import dataclass, field ,asdict
from typing import Optional, List, Dict
import math
import numpy as np
import pandas as pd
from Data.Paths import Paths
from tqdm import tqdm
import os
import json
from Exceptions.ServiceExceptions import *

@dataclass
class Trade:
    side: str                     # "long" or "short"
    entry_time: pd.Timestamp
    entry_price: float
    qty: float
    sl: Optional[float] = None
    tp: Optional[float] = None
    status: str = "OPEN"          # OPEN / CLOSED
    exit_time: Optional[pd.Timestamp] = None
    exit_price: Optional[float] = None
    pnl: float = 0.0
    meta: Dict = field(default_factory=dict)  # store zone info, features, signal probs, etc.

class Portfolio:
    def __init__(self, starting_balance: float = 10000.0, fee_bps: float = 5.0, slippage_bps: float = 1.0, max_concurrent: int = 10):
        self.balance = starting_balance
        self.equity = starting_balance
        self.starting = starting_balance
        self.fee_bps = fee_bps
        self.slippage_bps = slippage_bps
        self.max_concurrent = max_concurrent
        self.open_trades: List[Trade] = []
        self.closed_trades: List[Trade] = []
        self.equity_curve: List[Dict] = []   # [{'time': ts, 'equity': val}]
        self._last_time: Optional[pd.Timestamp] = None
        self.paths = Paths()
        if not os.path.exists(self.paths.backtest_history):
            open(self.paths.backtest_history,'w')

    def _apply_fees(self, notional: float) -> float:
        return notional * (self.fee_bps / 10000.0)

    def _apply_slippage_price(self, price: float, side: str, is_entry: bool = True) -> float:
        # Entry: worsen price; Exit: also worsen price; change direction by side.
        drift = price * (self.slippage_bps / 10000.0)
        if side == "long":
            return price + drift if is_entry else price - drift
        else:  # short
            return price - drift if is_entry else price + drift

    def risk_position_size(self, entry: float, sl: float, risk_pct: float = 0.01) -> float:
        # Risk fixed % of balance per trade
        if sl is None or sl == entry:
            # fallback: 1% notional if SL is missing
            return (self.starting * risk_pct) / entry
        risk_amt = self.starting * risk_pct
        per_unit_risk = abs(entry - sl)
        if per_unit_risk <= 0:
            return (self.starting * risk_pct) / entry
        qty = risk_amt / per_unit_risk
        return max(qty, 0.0)

    def can_open(self) -> bool:
        return len(self.open_trades) < self.max_concurrent

    def open_trade(self, trade: Trade):
        # Pay entry fee on notional
        if self.balance < 100:
            raise BalanceZero()
        notional = trade.entry_price * trade.qty
        fee = self._apply_fees(notional)
        self.balance -= fee
        self.open_trades.append(trade)

    def close_trade(self, trade: Trade, exit_time: pd.Timestamp, exit_price: float):
        notional = exit_price * trade.qty
        fee = self._apply_fees(notional)

        # PnL for long = (exit-entry)*qty; for short = (entry-exit)*qty
        gross = (exit_price - trade.entry_price) * trade.qty if trade.side == "Long" else (trade.entry_price - exit_price) * trade.qty
        pnl = gross - fee

        trade.status = "CLOSED"
        trade.exit_time = exit_time
        trade.exit_price = exit_price
        trade.pnl = gross

        self.closed_trades.append(trade)
        self.open_trades.remove(trade)
        self.balance += pnl
        self.write_history(trade)

    def write_history(self,trade:Trade):
        meta = trade.meta
        based_zone = {
            'timestamp' : str(meta.get('timestamp',None)),
            'zone_high' : float(meta.get('zone_high',0.0)),
            'zone_low' : float(meta.get('zone_low',0.0)),
            'zone_type' : str(meta.get('zone_type',None))
        }
        above_zone = {
            'timestamp' : str(meta.get('above_timestamp',None)),
            'zone_high' : float(meta.get('above_zone_high',0.0)),
            'zone_low' : float(meta.get('above_zone_low',0.0)),
            'zone_type' : str(meta.get('above_zone_type',None))
        }
        
        below_zone = {
            'timestamp' : str(meta.get("below_timestamp",None)),
            'zone_high' : float(meta.get('below_zone_high',0.0)),
            'zone_low' : float(meta.get('below_zone_low',0.0)),
            'zone_type' : str(meta.get('below_zone_type',None))
        }
        record = {
            'entry time' : str(trade.entry_time),
            'side' : trade.side,
            'entry price' : float(trade.entry_price),
            'tp' : float(trade.tp),
            'sl' : float(trade.sl),
            'lot size' : float(trade.qty),
            'end time' : str(trade.exit_time),
            'exit price' : float(trade.exit_price),
            'based_zone' : based_zone,
            'above_zone' : above_zone,
            'below_zone' : below_zone,
            'result' : float(trade.pnl)
        }
        with open(self.paths.backtest_history,'a') as f:
            f.write(json.dumps(record) + "\n")

    def mark_to_market(self, time: pd.Timestamp, price: float):
        # Unrealized PnL to compute equity curve (simple marking on close)
        upnl = 0.0
        for t in self.open_trades:
            upnl += (price - t.entry_price) * t.qty if t.side == "long" else (t.entry_price - price) * t.qty
        self.equity = self.balance + upnl
        self._last_time = time
        self.equity_curve.append({"time": time, "equity": self.equity})

    def stats(self) -> Dict:
        pnl_series = pd.Series([t.pnl for t in self.closed_trades], dtype=float)
        total_pnl = pnl_series.sum() if not pnl_series.empty else 0.0
        wins = (pnl_series > 0).sum() if not pnl_series.empty else 0
        losses = (pnl_series <= 0).sum() if not pnl_series.empty else 0
        winrate = wins / max(wins + losses, 1)

        eq = pd.DataFrame(self.equity_curve)
        max_dd = 0.0
        if not eq.empty:
            eq['cummax'] = eq['equity'].cummax()
            dd = (eq['equity'] - eq['cummax'])
            max_dd = dd.min()

        print(f"closed_trades : {int(len(self.closed_trades))},")
        print(f"open_trades: {int(len(self.open_trades))},")
        print(f"total_pnl: {float(total_pnl)},")
        print(f'wins : {int(wins)}')
        print(f'losses : {int(losses)}')
        print(f"winrate: {float(winrate * 100)}%,")
        print(f"max_drawdown: {float(max_dd)},")
        print(f"ending_balance: {float(self.balance)},")
        print(f"ending_equity: {float(self.equity)},")
            
            
            
            
        
