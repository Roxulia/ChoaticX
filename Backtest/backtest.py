from Core.zone_detection import ZoneDetector
from Core.zone_reactions import ZoneReactor
from Core.zone_merge import ZoneMerger
from Core.zone_confluents import ConfluentsFinder
from Core.SignalGeneration import SignalGenerator
from Core.Filter import Filter
from Core.zone_nearby import NearbyZones
from Core.ATH_Handler import ATHHandler
from ML.Model import ModelHandler
from ML.dataCleaning import DataCleaner
from ML.datasetGeneration import DatasetGenerator
from Data.binanceAPI import BinanceAPI
from Data.Paths import Paths
from Utility.UtilityClass import UtilityFunctions
from .Portfolio import Portfolio,Trade
import pandas as pd
import json
from dotenv import load_dotenv
from tqdm import tqdm
import os
from Utility.MemoryUsage import MemoryUsage as mu

class BackTestHandler:
    def __init__(self,time_frames = ['1h','4h','1D'],lookback = '1 years'):
        load_dotenv()
        self.api = BinanceAPI()
        self.utility = UtilityFunctions()
        self.reaction = ZoneReactor()
        self.ohclv_paths=[]
        self.time_frames = time_frames
        self.lookback = lookback
        self.Paths = Paths()
        self.portfolio = Portfolio()

    @mu.log_memory
    def run_backtest(self, zone_update_interval=5):
        dfs = self.load_OHLCV_for_backtest(inner_func=True)
        based_candles = dfs[0]  # pandas DataFrame: must have columns like timestamp, open, high, low, close, volume, ema20, ema50, rsi, atr
        with mu.disable_memory_logging():
            with tqdm(total=len(based_candles), desc="Running Backtest") as pbar:
                signal = None  # make scope explicit
                
                for pos, (_, candle) in enumerate(based_candles.iterrows()):
                    prev_signal = signal
                    
                    # Enter on pullback into entry range after a signal exists
                    if prev_signal is not None:
                        side = prev_signal['side']
                        if side == 'Long' and (prev_signal['sl'] < candle['close'] <= prev_signal['entry_price']):
                            self.EnterTrade(prev_signal,candle['timestamp'])
                        elif side == 'Short' and (prev_signal['sl'] > candle['close'] >= prev_signal['entry_price']):
                            self.EnterTrade(prev_signal,candle['timestamp'])

                    # Update zones on schedule
                    if pos % zone_update_interval == 0:
                        timestamp = based_candles.iloc[pos]['timestamp']
                        self.update_zones(dfs, timestamp)

                    # History up to (but not including) current candle
                    candles = based_candles.iloc[:pos]
                    if candles.shape[0] > 0:
                        # Generate signal if current candle touched a zone
                        touch_type, zone_timestamp = self.reaction.get_last_candle_reaction(self.warmup_zones, candle)
                        if touch_type is not None:
                            nearbyzone = NearbyZones()
                            datagen = DatasetGenerator(timeframes=self.time_frames)
                            athHandler = ATHHandler(candles)
                            ATH = athHandler.getATHFromCandles()
                            
                            use_zones = []
                            for z_idx, zone in enumerate(self.warmup_zones):
                                curr_timestamp = pd.to_datetime(zone['timestamp'])
                                if curr_timestamp == zone_timestamp:
                                    zone['candle_volume'] = candle['volume']
                                    zone['candle_open'] = candle['open']
                                    zone['candle_close'] = candle['close']
                                    zone['candle_ema20'] = candle['ema20']
                                    zone['candle_ema50'] = candle['ema50']
                                    zone['candle_rsi'] = candle['rsi']
                                    zone['candle_atr'] = candle['atr']
                                    zone['touch_type'] = touch_type

                                    zone = nearbyzone.getAboveBelowZones(zone, self.warmup_zones, ATH)
                                    use_zones.append(zone)
                            use_zones = datagen.extract_confluent_tf(use_zones)
                            datacleaner = DataCleaner(timeframes=self.time_frames)
                            use_zones = datacleaner.preprocess_input(use_zones)
                            modelHandler = ModelHandler()
                            modelHandler.load()
                            model = modelHandler.get_model()
                            signalGen = SignalGenerator(model)
                            signal = signalGen.generate(use_zones,backtest=True)

                    # Manage open trades with current candle
                    for trade in list(self.portfolio.open_trades):
                        deadline = trade.entry_time + pd.DateOffset(days=7)
                        if trade.status == "OPEN" and deadline > candle['timestamp'] >= trade.entry_time:
                            if trade.side == "Long":
                                if candle['low'] <= trade.sl:
                                    exit_price = self.portfolio._apply_slippage_price(trade.sl, trade.side, is_entry=False)
                                    self.portfolio.close_trade(trade, candle['timestamp'], exit_price)
                                elif trade.tp is not None and candle['high'] >= trade.tp:
                                    exit_price = self.portfolio._apply_slippage_price(trade.tp, trade.side, is_entry=False)
                                    self.portfolio.close_trade(trade, candle['timestamp'], exit_price)
                            elif trade.side == "Short":
                                if candle['high'] >= trade.sl:
                                    exit_price = self.portfolio._apply_slippage_price(trade.sl, trade.side, is_entry=False)
                                    self.portfolio.close_trade(trade, candle['timestamp'], exit_price)
                                elif trade.tp is not None and candle['low'] <= trade.tp:
                                    exit_price = self.portfolio._apply_slippage_price(trade.tp, trade.side, is_entry=False)
                                    self.portfolio.close_trade(trade, candle['timestamp'], exit_price)
                    pbar.update(1)
        print("Backtest completed.")
        print(self.portfolio.stats())

    

    def EnterTrade(self,signal,timestamp):
        if(self.portfolio.can_open()):
            
            entry_price = signal['entry_price']
            sl = signal['sl']
            tp = signal['tp']
            side = signal['side']
            meta = signal['meta']
            qty = self.portfolio.risk_position_size(entry_price,sl)
            trade = Trade(side=side,entry_time=timestamp,entry_price=entry_price,qty=qty,sl=sl,tp=tp,meta=meta)
            self.portfolio.open_trade(trade)

    def load_OHLCV_for_backtest(self,warmup_month =3,candle_interval = '1D',inner_func = False):
        temp_dfs = []
        days,hours,minutes,seconds = self.utility.getDHMS(candle_interval)
        for path in tqdm(self.ohclv_paths, desc="Warming up with OHLCV data",disable=inner_func):
            df = pd.read_csv(path)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            start_date = df['timestamp'].min()
            cutoff_date = start_date + pd.DateOffset(months=warmup_month)
            max_date = cutoff_date + pd.DateOffset(days=days,hours=hours,minutes=minutes,seconds=seconds)
            temp_df = df[(df['timestamp'] > cutoff_date)]

            temp_dfs.append(temp_df)
        return temp_dfs
    
    def update_zones(self,dfs,timestamp):
        temp_zones = []
        try:
            zones = []
            for df in tqdm(dfs, desc="Warming up with OHLCV data",disable= True):
                data = df.loc[df['timestamp'] <= timestamp]
                detector = ZoneDetector(data)
                zones = zones + detector.get_zones(inner_func=True)
            confluentfinder = ConfluentsFinder(zones)
            confluent_zones = confluentfinder.getConfluents(inner_func=True)
            datagen = DatasetGenerator(confluent_zones)
            temp_zones = datagen.extract_confluent_tf(confluent_zones)
            self.warmup_zones =  self.utility.merge_lists_by_key(self.warmup_zones,temp_zones,"timestamp")
        except Exception as e:
            print(f"error updating zones : {e}")
            return False
        return True

    
    def warm_up(self):
        if not self.initial_state():
            print("Failed to initialize state with OHLCV data.")
            return False
        
        warm_up_dfs = self.load_warm_up_dfs()
        if not warm_up_dfs:
            print("No warm-up data loaded.")
            return False
        try:
            zones = []
            for df in tqdm(warm_up_dfs, desc="Warming up with OHLCV data"):
                detector = ZoneDetector(df)
                zones = zones + detector.get_zones()
            confluentfinder = ConfluentsFinder(zones)
            confluent_zones = confluentfinder.getConfluents()
            datagen = DatasetGenerator(confluent_zones)
            self.warmup_zones = datagen.extract_confluent_tf(confluent_zones)
        except Exception as e:
            print(f"Error during warm-up: {e}")
            return False
        return True

    def load_warm_up_dfs(self,month=3):
        warm_up_dfs = []
        for path in tqdm(self.ohclv_paths, desc="Warming up with OHLCV data"):
            df = pd.read_csv(path)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            start_date = df['timestamp'].min()
            cutoff_date = start_date + pd.DateOffset(months=month)
            warmup_df = df[df['timestamp'] < cutoff_date]
            warm_up_dfs.append(warmup_df)
        return warm_up_dfs

    def initial_state(self):
        for tf in self.time_frames:
            path = self.api.store_OHLCV(symbol='BTCUSDT', interval=tf, lookback=self.lookback)
            if path is not None:
                self.ohclv_paths.append(path)
        
        if not self.ohclv_paths:
            print("No data fetched for the specified time frames.")
            return False
        return True
