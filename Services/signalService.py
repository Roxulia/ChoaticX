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
from Utility.UtilityClass import UtilityFunctions as utility
from Utility.MemoryUsage import MemoryUsage as mu
from Exceptions.ServiceExceptions import *
import pandas as pd
import json
from dotenv import load_dotenv
from tqdm import tqdm
from Data.Paths import Paths
from flask_socketio import SocketIO
import os
class SignalService:
    def __init__(self,socketio : SocketIO = None,timeframes = ['1h','4h','1D'],ignore_cols = ['zone_high','zone_low','below_zone_low','above_zone_low','below_zone_high','above_zone_high','candle_open','candle_close','candle_high','candle_low']):
        
        self.api = BinanceAPI()
        self.Paths = Paths()
        self.timeframes = timeframes
        self.socketio = socketio
        self.ignore_cols = ignore_cols

    def get_zones(self,interval,lookback):
        try:
            df = self.api.get_ohlcv(interval=interval,lookback=lookback)
        except CantFetchCandleData as e:
            raise CantFetchCandleData
        if interval ==  self.timeframes[0]:
            self.based_candles = df
        detector = ZoneDetector(df)
        zones = detector.get_zones()
        return zones

    @mu.log_memory
    def get_latest_zones(self,lookback='1 years'):
        t_zones = []
        for tf in self.timeframes:
            try:
                zone = self.get_zones(tf,lookback)
                
                t_zones = t_zones + zone
            except CantFetchCandleData:
                raise CantFetchCandleData
        confluentfinder = ConfluentsFinder(t_zones)
        zones = confluentfinder.getConfluents()
        athHandler = ATHHandler(self.based_candles)
        athHandler.updateATH()
        nearByZones = NearbyZones(zones,self.based_candles)
        zones = nearByZones.getNearbyZone()
        reactor = ZoneReactor()
        zones = reactor.perform_reaction_check(zones,self.based_candles)
        zones = sorted(zones,key=lambda x : x.get("timestamp",None))
        return zones

    def get_untouched_zones(self):
        zones = []
        with open(self.Paths.zone_storage,'r') as f:
            for line in f:
                data = json.loads(line)
                zones.append(data)
        if zones:
            return zones
        else:
            raise NoUntouchedZone

    @mu.log_memory
    def get_current_signals(self):
        candle = self.api.get_latest_candle()
        zones = self.get_untouched_zones()
        athHandler = ATHHandler()
        ATH = athHandler.getATHFromStorage()
        reactor = ZoneReactor()
        datagen = DatasetGenerator()
        reaction,zone_timestamp = reactor.get_last_candle_reaction(zones,candle)
        zone_to_remove = []
        if not reaction == 'None':
            nearbyzone = NearbyZones()
            use_zones = []
            datacleaner = DataCleaner(self.timeframes)
            model_handler = ModelHandler(model_type='xgb')
            model_handler.load()
            signal_gen = SignalGenerator(model_handler,datacleaner,self.ignore_cols)
            for i,zone in tqdm(enumerate(zones),desc = 'Getting Touched Zone Data'):
                curr_timestamp = pd.to_datetime(zone['timestamp'])
                if curr_timestamp == zone_timestamp:
                    zone_to_remove.append(zone_timestamp)
                    zone['candle_volume'] = candle['volume']
                    zone['candle_open'] = candle['open']
                    zone['candle_close'] = candle['close']
                    zone['candle_ema20'] = candle['ema20']
                    zone['candle_ema50'] = candle['ema50']
                    zone['candle_rsi'] = candle['rsi']
                    zone['candle_atr'] = candle['atr']
                    zone['touch_type'] = reaction
                    zone = nearbyzone.getAboveBelowZones(zone, zones, ATH)
                    
                    use_zones.append(zone)
            use_zones = datagen.extract_confluent_tf(use_zones)
            
            signal = signal_gen.generate(use_zones)
        else:
            print('Zones are not touched yet')
            signal = 'None'
        dataToStore = utility.removeDataFromListByKeyValueList(zones,zone_to_remove,key='timestamp')
        try:
            with open(self.Paths.zone_storage, "w") as f:
                for i, row in enumerate(tqdm(dataToStore, desc="Writing to untouch zone storage file")):
                    f.write(json.dumps(row) + "\n")
        except Exception as e:
            print(f"Error writing to file: {e}")
        self.socketio.emit("new_signal",signal,broadcast = True)
        return signal
    
    def get_signals_with_input(self,data):
        if not data:
            return {'error': 'No data provided'}, 400
        use_zones = []
        zone = {
            'avg_volume_past_5' : data.get('avg_volume_past_5', None),
            'atr_mean' : data.get('atr_mean', None),
            'above_atr' : data.get('above_atr', None),
            'below_atr' : data.get('below_atr', None),
            'below_conf_count_BuFVG' : data.get('below_conf_count_BuFVG', None),
            'conf_count_BuLiq' : data.get('conf_count_BuLiq', None),
            'below_conf_4h_count' : data.get('below_conf_4h_count', None),
            'below_body_size' : data.get('below_body_size', None),
            'below_zone_low': data.get('below_zone_low', None),
            'above_conf_count_BuLiq' : data.get('above_conf_count_BuLiq', None),
            'wick_ratio' : data.get('wick_ratio', None),
            'above_zone_low' : data.get('above_zone_low', None),
            'conf_4h_count' : data.get('conf_4h_count', None),
            'prev_volatility_5': data.get('prev_volatility_5', None),
            'below_ema 20': data.get('below_ema 20', None),
            'below_prev_volatility_5': data.get('below_prev_volatility_5', None),
            'above_conf_count_BrLiq': data.get('above_conf_count_BrLiq', None),
            'below_equal_level_deviation': data.get('below_equal_level_deviation', None),
            'ema 20':   data.get('ema 20', None),
            'below_ema_50' : data.get('below_ema_50', None),
            'candle_volume' : data.get('candle_volume', None),
            'below_momentum_5' : data.get('below_momentum_5', None),
            'above_ema 20' : data.get('above_ema 20', None),
            'zone_low' : data.get('zone_low', None),
            'below_conf_count_BrOB' : data.get('below_conf_count_BrOB', None),
            'candle_high' : data.get('candle_high', None),
            'below_ema_20': data.get('below_ema_20', None),
            'count' : data.get('count', None),
            'below_volume_on_creation' : data.get('below_volume_on_creation', None),
            'volume_on_creation' : data.get('volume_on_creation', None),
            'above_zone_high' : data.get('above_zone_high', None),
            'conf_is_buy_zone' : data.get('conf_is_buy_zone', None),
            'above_zone_width' : data.get('above_zone_width', None),
            'above_avg_volume_around_zone' : data.get('above_avg_volume_around_zone', None),
            'conf_count_BrOB' : data.get('conf_count_BrOB', None),
            'below_conf_1h_count' : data.get('below_conf_1h_count', None),
            'above_count' : data.get('above_count', None),
            'equal_level_deviation': data.get('equal_level_deviation', None),
            'zone_width' : data.get('zone_width', None),
            'candle_ema50' : data.get('candle_ema50', None),
            'candle_rsi' : data.get('candle_rsi', None),
            'momentum_5' : data.get('momentum_5', None),
            'below_conf_is_buy_zone' : data.get('below_conf_is_buy_zone', None),
            'above_ema_20' : data.get('above_ema_20', None),
            'above_rsi' : data.get('above_rsi', None),
            'zone_high' : data.get('zone_high', None),
            'above_conf_count_BrOB' : data.get('above_conf_count_BrOB', None),
            'conf_count_BrFVG' : data.get('conf_count_BrFVG', None),
            'ema_50' : data.get('ema_50', None),
            'above_ema_50' : data.get('above_ema_50', None),
            'above_volume_on_creation' : data.get('above_volume_on_creation', None),
            'above_conf_count_BuFVG' : data.get('above_conf_count_BuFVG', None),
            'type' : data.get('type', None),
            'touch_type' : data.get('touch_type', None),
            'conf_1h_count' : data.get('conf_1h_count', None),
            'below_conf_count_BrLiq' : data.get('below_conf_count_BrLiq', None),
            'below_zone_width' : data.get('below_zone_width', None),
            'below_ema 50' : data.get('below_ema 50', None),
            'below_avg_volume_around_zone' : data.get('below_avg_volume_around_zone', None),
            'below_rsi' : data.get('below_rsi', None),
            'conf_1D_count' : data.get('conf_1D_count', None),
            'above_equal_level_deviation' : data.get('above_equal_level_deviation', None),
            'below_atr_mean' : data.get('below_atr_mean', None),
            'avg_volume_around_zone' : data.get('avg_volume_around_zone', None),
            'above_conf_1h_count' : data.get('above_conf_1h_count', None),
            'below_zone_high' : data.get('below_zone_high', None),
            'conf_count_BuOB' : data.get('conf_count_BuOB', None),
            'body_size' : data.get('body_size', None),
            'below_avg_volume_past_5' : data.get('below_avg_volume_past_5', None),
            'above_type' : data.get('above_type', None),
            'below_conf_1D_count' : data.get('below_conf_1D_count', None),
            'above_ema 50' : data.get('above_ema 50', None),
            'candle_open'  : data.get('candle_open', None),
            'below_conf_count_BuOB' : data.get('below_conf_count_BuOB', None),
            'rsi' : data.get('rsi', None),
            'ema_20' : data.get('ema_20', None),
            'candle_atr' : data.get('candle_atr', None),
            'conf_count_BrLiq' : data.get('conf_count_BrLiq', None),
            'above_conf_count_BrFVG' : data.get('above_conf_count_BrFVG', None),
            'below_duration_between_first_last_touch' : data.get('below_duration_between_first_last_touch', None),
            'below_conf_count_BuLiq' : data.get('below_conf_count_BuLiq', None),
            'above_conf_1D_count' : data.get('above_conf_1D_count', None),
            'above_prev_volatility_5' : data.get('above_prev_volatility_5', None),
            'below_count' : data.get('below_count', None),
            'below_type' : data.get('below_type', None),
            'candle_ema20' : data.get('candle_ema20', None),
            'atr' :    data.get('atr', None),
            'below_wick_ratio' : data.get('below_wick_ratio', None),
            'below_conf_count_BrFVG' : data.get('below_conf_count_BrFVG', None),
            'above_conf_is_buy_zone' : data.get('above_conf_is_buy_zone', None),
            'distance_to_nearest_zone_below' : data.get('distance_to_nearest_zone_below', None),
            'above_avg_volume_past_5' : data.get('above_avg_volume_past_5', None),
            'above_momentum_5' : data.get('above_momentum_5', None),
            'candle_low' : data.get('candle_low', None),
            'ema 50': data.get('ema 50', None),
            'candle_close' : data.get('candle_close', None),
            'distance_to_nearest_zone_above' : data.get('distance_to_nearest_zone_above', None),
            'above_atr_mean' : data.get('above_atr_mean', None),
            'above_body_size' : data.get('above_body_size', None),
            'above_wick_ratio' : data.get('above_wick_ratio', None),
            'above_conf_count_BuOB' : data.get('above_conf_count_BuOB', None),
            'duration_between_first_last_touch' : data.get('duration_between_first_last_touch', None),
            'above_conf_4h_count' : data.get('above_conf_4h_count', None),
            'conf_count_BuFVG' : data.get('conf_count_BuFVG', None),
            'above_duration_between_first_last_touch' : data.get('above_duration_between_first_last_touch', None),
            'candle_atr_mean' : data.get('candle_atr_mean', None),
        }
        use_zones.append(zone)
        datacleaner = DataCleaner(self.timeframes)
        model_handler = ModelHandler(model_type='xgb')
        model_handler.load()
        signal_gen = SignalGenerator(model_handler,datacleaner,self.ignore_cols)
        signal = signal_gen.generate(use_zones)
        return signal
    
    def get_running_signals(self):
        signal_gen = SignalGenerator()
        signals = signal_gen.get_running_signals()
        if signals is None:
            raise EmptySignalException
        return signals

    def update_untouched_zones(self):
        try:
            df_from_candle = self.get_latest_zones('6 months')
        except CantFetchCandleData:
            raise CantFetchCandleData
        temp_df = []
        for i,row in enumerate(df_from_candle):
            if row['touch_type'] is not None:
                continue
            else:
                temp_df.append(row)
        df_from_storage = self.get_untouched_zones()
        if df_from_storage is None:
            datagen = DatasetGenerator(temp_df)
            datagen.store_untouch_zones()
        else:
            df_final = utility.merge_lists_by_key(df_from_storage,temp_df,key="timestamp")
            datagen = DatasetGenerator(df_final)
            datagen.store_untouch_zones()

    def get_dataset(self):
        try:
            df = self.get_latest_zones('3 years')
        except CantFetchCandleData:
            raise CantFetchCandleData
        datagen = DatasetGenerator(df,self.timeframes)
        datagen.get_dataset_list()
        return datagen.total_line
    
    def clean_dataset(self,total):
        datacleaner = DataCleaner(timeframes=self.timeframes,batch_size=1000,total_line=total)
        return datacleaner.perform_clean(self.ignore_cols)
        
    def train_model(self,total):
        model_trainer = ModelHandler(timeframes=self.timeframes,model_type='xgb',total_line=total)
        model_trainer.train()

    def test_model(self):
        model_trainer = ModelHandler(model_type='xgb',timeframes=self.timeframes)
        model_trainer.load()
        model_trainer.test_result()

    def test_dataset(self):
        with open(self.Paths.raw_data) as f:
            keys = set()
            for i, line in enumerate(f):
                obj = json.loads(line)
                keys.update(obj.keys())
            print(f"🧩 Total unique keys: {len(keys)}")
            print(keys)

    def data_extraction(self):
        try:
            total = self.get_dataset()
        except CantFetchCandleData:
            raise CantFetchCandleData
        total = self.clean_dataset(total)
        return total

    def training_process(self,total):
        try:
            self.train_model(total)
            self.test_model()
        except:
            raise TrainingFail

    def test_process(self):
        try:
            df = self.get_latest_zones()
        except CantFetchCandleData:
            raise CantFetchCandleData
        datagen = DatasetGenerator(df)
        data = datagen.extract_features_and_labels()
        data = datagen.extract_confluent_tf(data)
        data = datagen.extract_nearby_zone_data(data)
        count = 0
        for d in data:
            if count > 0:
                break
            for k,v in d.items():
                print(k)
            count+=1

    