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
from Utility.UtilityClass import UtilityFunctions
import pandas as pd
import json
from dotenv import load_dotenv
from tqdm import tqdm
import os

class BackTestHandler:
    def __init__(self,time_frames = ['1h','4h','1D'],lookback = '1 years'):
        load_dotenv()
        self.api = BinanceAPI()
        self.utility = UtilityFunctions()
        self.reaction = ZoneReactor()
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

    def run_backtest(self,zone_update_interval = 5):
        dfs = self.load_OHLCV_for_backtest()
        based_candles = dfs[0]
        for i,candle in tqdm(enumerate(based_candles),desc = "Running Backtest"):
            if(i%5 == 0):
                self.update_zones(dfs)
            touch_type,zone_timestamp = self.reaction.get_last_candle_reaction(self.warmup_zones,candle)
            if touch_type is not None:
                nearbyzone = NearbyZones()
                datagen = DatasetGenerator()
                use_zones = []
                for i,zone in tqdm(enumerate(self.warmup_zones),desc = 'Getting Touched Zone Data'):
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
                        dist_above,above_zone,dist_below,below_zone = nearbyzone.getAboveBelowZones(zone,zones,ATH)
                        zone['distance_to_nearest_zone_above'] = dist_above
                        zone['nearest_zone_above'] = above_zone
                        zone['distance_to_nearest_zone_below'] = dist_below
                        zone['nearest_zone_below'] = below_zone
                        temp_zone = datagen.extract_nearby_zone_data_per_zone(zone)
                        use_zones.append(temp_zone)
                datacleaner = DataCleaner(self.output_path,train_path=self.train_path,test_path=self.test_path)
                use_zones = datacleaner.preprocess_input(use_zones)
                signal = self.signal_gen.generate(use_zones)
    
    def load_OHLCV_for_backtest(self,warmup_month =3,candle_interval = '1D'):
        temp_dfs = []
        days,hours,minutes,seconds = self.utility.getDHMS(candle_interval)
        for path in tqdm(self.ohclv_paths, desc="Warming up with OHLCV data"):
            df = pd.read_csv(path)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            start_date = df['timestamp'].min()
            cutoff_date = start_date + pd.DateOffset(months=warmup_month)
            max_date = cutoff_date + pd.DateOffset(days=days,hours=hours,minutes=minutes,seconds=seconds)
            temp_df = df[df['timestamp'] > cutoff_date & df['timestamp'] <= max_date]
            temp_dfs.append(temp_df)
        return temp_dfs
    
    def update_zones(self,dfs):
        temp_zones = []
        try:
            zones = []
            for df in tqdm(dfs, desc="Warming up with OHLCV data"):
                detector = ZoneDetector(df)
                zones.append(detector.get_zones())
            confluentfinder = ConfluentsFinder(zones)
            confluent_zones = confluentfinder.getConfluents()
            datagen = DatasetGenerator(confluent_zones)
            temp_zones = datagen.extract_confluent_tf()
            self.warmup_zones =  self.utility.merge_lists_by_key(self.warmup_zones,temp_zones,"timestamp")
        except:
            print("error updating zones")
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
                zones.append(detector.get_zones())
            confluentfinder = ConfluentsFinder(zones)
            confluent_zones = confluentfinder.getConfluents()
            datagen = DatasetGenerator(confluent_zones)
            self.warmup_zones = datagen.extract_confluent_tf()
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
