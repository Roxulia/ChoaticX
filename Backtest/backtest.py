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
import pandas as pd
import json
from dotenv import load_dotenv
from tqdm import tqdm
import os

class BackTestHandler:
    def __init__(self,time_frames = ['1h','4h','1D'],lookback = '3 years'):
        load_dotenv()
        self.api = BinanceAPI()
        self.ohclv_paths=[]
        self.time_frames = time_frames
        self.lookback = lookback
        self.output_path = os.getenv(key='RAW_DATA')
        self.train_path = os.getenv(key='TRAIN_DATA')
        self.test_path = os.getenv(key='TEST_DATA')
        self.model_path = os.getenv(key='MODEL_PATH')
        self.storage_path = os.getenv(key='ZONE_STORAGE')
        self.model_handler = ModelHandler(model_path=self.model_path, model_type='xgb')
        self.signal_gen = SignalGenerator(self.model_handler.get_model())

    def run_backtest(self, interval, lookback):
        zones = self.get_latest_zones()
        if zones is None:
            return "No zones found for backtesting."
        
        signals = []
        for zone in tqdm(zones, desc="Processing zones"):
            signal = self.signal_gen.generate(zone)
            if signal != 'None':
                signals.append(signal)
        
        return signals
    
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
                zones.append(detector.get_zones())
            confluentfinder = ConfluentsFinder(zones)
            confluent_zones = confluentfinder.getConfluents()
            based_candles = warm_up_dfs[0]
            nearby_zones = NearbyZones(confluent_zones, based_candles)
            confluent_zones = nearby_zones.getNearbyZone()
            reactor = ZoneReactor()
            result_zones = reactor.get_zones_reaction(confluent_zones,df)
            result_zones = reactor.getTargetFromTwoZones(result_zones,df)
            self.warmups = result_zones
        except Exception as e:
            print(f"Error during warm-up: {e}")
            return False
        return True

    def load_warm_up_dfs(self):
        warm_up_dfs = []
        for path in tqdm(self.ohclv_paths, desc="Warming up with OHLCV data"):
            df = pd.read_csv(path)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            start_date = df['timestamp'].min()
            cutoff_date = start_date + pd.DateOffset(months=3)
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
