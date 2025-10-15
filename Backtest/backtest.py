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
from Data.Columns import IgnoreColumns
from Utility.UtilityClass import UtilityFunctions as utility
from .Portfolio import Portfolio,Trade
import pandas as pd
import json
from dotenv import load_dotenv
from tqdm import tqdm
import os
from Utility.MemoryUsage import MemoryUsage as mu
from Exceptions.ServiceExceptions import *
import traceback


class BackTestHandler:
    def __init__(self,symbol,threshold,time_frames = ['1h','4h','1D'],lookback = '1 years'):
        load_dotenv()
        self.api = BinanceAPI()
        self.reaction = ZoneReactor()
        self.ohclv_paths=[]
        self.time_frames = time_frames
        self.symbol = symbol
        self.threshold = threshold
        self.ignore_cols = IgnoreColumns()
        self.lookback = lookback
        self.Paths = Paths()
        self.portfolio = Portfolio()
        self.used_zones = []

    @mu.log_memory
    def run_backtest(self,zone_update_interval=24):
        print(f'{self.warmup_zones[0]['timestamp']}-{(self.warmup_zones[-1]['timestamp'])}')
        dfs = self.load_OHLCV_for_backtest(inner_func=True)
        based_candles = dfs[0]

        # Pre-init heavy objects
        nearbyzone = NearbyZones(threshold=self.threshold)
        datagen = DatasetGenerator(symbol=self.symbol,timeframes=self.time_frames)
        datacleaner = DataCleaner(symbol=self.symbol,timeframes=self.time_frames)
        modelHandler1 = ModelHandler(symbol=self.symbol,timeframes=self.time_frames,model_type='xgb')
        modelHandler2 = ModelHandler(symbol=self.symbol,timeframes=[self.time_frames[0]],model_type='xgb')
        signalGen = SignalGenerator([modelHandler1,modelHandler2],datacleaner,[self.ignore_cols.signalGenModelV1,self.ignore_cols.predictionModelV1])

        # Pre-convert zone timestamps
        for z in self.warmup_zones:
            z["timestamp"] = pd.to_datetime(z["timestamp"])

        try:
            with mu.disable_memory_logging():
                with tqdm(total=len(based_candles), desc="Running Backtest") as pbar:
                    signal = None
                    history = []  # rolling list instead of slicing

                    for pos, (_, candle) in enumerate(based_candles.iterrows()):
                        history.append(candle)
                        # Entry handling
                        if signal is not None:
                            side = signal["side"]
                            diff = abs(signal['sl'] - candle['close'])
                            if diff > self.threshold:
                                if side == "Long" and (signal["sl"] < candle["close"] <= signal["entry_price"]):
                                    signal['entry_price'] = candle['close']
                                    self.EnterTrade(signal, candle["timestamp"])
                                elif side == "Short" and (signal["sl"] > candle["close"] >= signal["entry_price"]):
                                    signal["entry_price"] = candle['close']
                                    self.EnterTrade(signal, candle["timestamp"])
                        # Update zones periodically
                        if pos % zone_update_interval == 0:
                            self.update_zones(dfs, candle["timestamp"])
                        # Generate signal only if touch
                        if len(history) > 1:
                            touch_type, zone_timestamp = self.reaction.get_last_candle_reaction(self.warmup_zones, candle)
                            if touch_type is not None:
                                tempATH = ATHHandler(pd.DataFrame(history)).getATHFromCandles()
                                if self.ATH['zone_high'] < tempATH['zone_high']:
                                    self.ATH = tempATH
                                use_zones = []
                                for zone in self.warmup_zones:
                                    if zone["timestamp"] == zone_timestamp:
                                        zone.update({
                                            "candle_volume": candle["volume"],
                                            "candle_open": candle["open"],
                                            "candle_close": candle["close"],
                                            "candle_ema20": candle["ema20"],
                                            "candle_ema50": candle["ema50"],
                                            "candle_rsi": candle["rsi"],
                                            "candle_atr": candle["atr"],
                                            "touch_type": touch_type,
                                        })
                                        use_zones.append(nearbyzone.getAboveBelowZones(zone, self.warmup_zones, self.ATH))

                                if use_zones:
                                    
                                    self.used_zones =  self.used_zones + [item['timestamp'] for item in use_zones]
                                    self.warmup_zones = utility.removeDataFromListByKeyValueList(self.warmup_zones,key='timestamp',to_remove=self.used_zones)
                                    use_zones = list(datagen.extract_input_data(use_zones))
                                    try:
                                        signal = signalGen.generate(use_zones, backtest=True)
                                    except NotEnoughRR as e:
                                        continue
                                    
                        # Manage trades
                        for trade in self.portfolio.open_trades:  # no list() copy
                            deadline = trade.entry_time + pd.DateOffset(days=7)
                            starttime = trade.entry_time + pd.DateOffset(hours=1)
                            if trade.status == "OPEN" and deadline > candle["timestamp"] >= starttime:
                                if trade.side == "Long":
                                    if candle["low"] <= trade.sl:
                                        self.portfolio.close_trade(trade, candle["timestamp"],trade.sl)
                                    elif trade.tp and candle["high"] >= trade.tp:
                                        self.portfolio.close_trade(trade, candle["timestamp"],trade.tp)
                                elif trade.side == "Short":
                                    if candle["high"] >= trade.sl:
                                        self.portfolio.close_trade(trade, candle["timestamp"],trade.sl)
                                    elif trade.tp and candle["low"] <= trade.tp:
                                        self.portfolio.close_trade(trade, candle["timestamp"],trade.tp)

                        self.portfolio.mark_to_market(candle["timestamp"], candle["close"])
                        pbar.update(1)
        except BalanceZero as e:
            print("No Balance Left")
        except Exception as e:
            stack_trace = traceback.format_exc()
            print(f"Unknown Error Occurred : {e}")
            print(stack_trace)
        finally:
            print("Backtest completed.")
            self.portfolio.stats()

    def EnterTrade(self,signal,timestamp):
        if(self.portfolio.can_open()):
            sl = signal['sl']
            tp = signal['tp']
            side = signal['side']
            meta = signal['meta']
            entry_price = self.portfolio._apply_slippage_price(signal['entry_price'],side)
            qty = self.portfolio.risk_position_size(entry_price,sl)
            trade = Trade(side=side,entry_time=timestamp,entry_price=entry_price,qty=qty,sl=sl,tp=tp,meta=meta)
            try:
                self.portfolio.open_trade(trade)
            except BalanceZero as e:
                print("Balance Zero")

    def load_OHLCV_for_backtest(self,warmup_month =3,candle_interval = '1D',inner_func = False):
        temp_dfs = []
        days,hours,minutes,seconds = utility.getDHMS(candle_interval)
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
            min_date = timestamp - pd.DateOffset(days = 7)
            for df in tqdm(dfs, desc="Warming up with OHLCV data",disable= True):
                data = df.loc[(df['timestamp'] <= timestamp) & (df['timestamp'] >= min_date)]
                detector = ZoneDetector(data)
                zones = zones + detector.get_zones(inner_func=True,threshold=self.threshold)
            confluentfinder = ConfluentsFinder(zones,threshold=self.threshold)
            confluent_zones = confluentfinder.getConfluents(inner_func=True)
            datagen = DatasetGenerator(symbol=self.symbol,timeframes=self.time_frames)
            temp_zones = list(datagen.extract_input_data(confluent_zones))
            self.warmup_zones =  utility.merge_lists_by_key(self.warmup_zones,temp_zones,"timestamp")
            self.warmup_zones = utility.removeDataFromListByKeyValueList(self.warmup_zones,self.used_zones,'timestamp')
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
                with mu.disable_memory_logging():
                    zones = zones + detector.get_zones(threshold=self.threshold,inner_func=True)
            self.ATH = ATHHandler(warm_up_dfs[0]).getATHFromCandles()
            confluentfinder = ConfluentsFinder(zones,threshold=self.threshold)
            confluent_zones = confluentfinder.getConfluents()
            datagen = DatasetGenerator(symbol=self.symbol,timeframes=self.time_frames)
            zones = list(datagen.extract_input_data(confluent_zones))
            zones = sorted(zones,key=lambda x : x.get("timestamp",None))
            self.warmup_zones = zones
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
