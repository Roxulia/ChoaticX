from Core.zone_detection import ZoneDetector
from Core.zone_reactions import ZoneReactor
from Core.zone_merge import ZoneMerger
from Core.zone_confluents import ConfluentsFinder
from Core.SignalGeneration import SignalGenerator
from Core.Filter import Filter
from Core.zone_nearby import NearbyZones
from ML.Model import ModelHandler
from ML.dataCleaning import DataCleaner
from ML.datasetGeneration import DatasetGenerator
from Data.binanceAPI import BinanceAPI
import pandas as pd
import json
from dotenv import load_dotenv
from tqdm import tqdm

import os
class SignalService:
    def __init__(self):
        load_dotenv()
        self.api = BinanceAPI()
        self.output_path = os.getenv(key='RAW_DATA')
        self.train_path = os.getenv(key='TRAIN_DATA')
        self.test_path = os.getenv(key='TEST_DATA')
        self.model_path = os.getenv(key='MODEL_PATH')
        self.storage_path = os.getenv(key='ZONE_STORAGE')
        self.model = ModelHandler(model_path=self.model_path,model_type='xgb').get_model()
        self.signal_gen = SignalGenerator(self.model)

    def get_zones(self,interval,lookback):
        df = self.api.get_ohlcv(interval=interval,lookback=lookback)
        if df is None:
            return None
        detector = ZoneDetector(df)
        zones = detector.get_zones()
        return zones

    def get_latest_zones(self):
        #zone_15m = self.get_zones('15min','1 years')
        zone_1h = self.get_zones('1h','1 years')
        if zone_1h is None:
            return None
        zone_4h = self.get_zones('4h',' 1 years')
        if zone_4h is None:
            return None
        confluentfinder = ConfluentsFinder(zone_1h+zone_4h)
        zones = confluentfinder.getConfluents()
        
        df = self.api.get_ohlcv(interval='1h',lookback='1 years')
        nearByZones = NearbyZones(zones,df)
        zones = nearByZones.getNearbyZone()
        reactor = ZoneReactor()
        zones = reactor.get_zones_reaction(zones,df)
        zones = reactor.getTargetFromTwoZones(zones,df)
        return zones

    def get_untouched_zones(self):
        
        zones = []
        with open(self.storage_path,'r') as f:
            for line in f:
                data = json.loads(line)
                zones.append(data)
        return zones

    def get_current_signals(self):
        candle = self.api.get_latest_candle()
        zones = self.get_untouched_zones()
        reactor = ZoneReactor()
        reaction,zone_index = reactor.get_last_candle_reaction(zones,candle)
        if not reaction == 'None':
            use_zones = []
            for i,zone in tqdm(enumerate(zones),desc = 'Getting Touched Zone Data'):
                if zone['index'] == zone_index:
                    zone['candle_volume'] = candle['volume']
                    zone['candle_open'] = candle['open']
                    zone['candle_close'] = candle['close']
                    zone['candle_ema20'] = candle['ema20']
                    zone['candle_ema50'] = candle['ema50']
                    zone['candle_rsi'] = candle['rsi']
                    zone['candle_atr'] = candle['atr']
                    zone['touch_type'] = reaction
                    use_zones.append(zone)
            datacleaner = DataCleaner(self.output_path,train_path=self.train_path,test_path=self.test_path)
            use_zones = datacleaner.preprocess_input(use_zones)
            return self.signal_gen.generate(use_zones)
        else:
            print('Zones are not touched yet')
            return 'None'
    
    def get_dataset(self):
        df = self.get_latest_zones()
        if df is None:
            return None,None
        datagen = DatasetGenerator(df)
        cols = datagen.get_dataset_list(self.output_path,self.storage_path)
        return datagen.total_line,cols
    
    def clean_dataset(self,total,cols):
        datacleaner = DataCleaner(cols,self.output_path,batch_size=1000,total_line=total,train_path=self.train_path,test_path=self.test_path)
        return datacleaner.perform_clean()
        
    def train_model(self,total):
        model_trainer = ModelHandler(model_path=self.model_path,model_type='xgb',total_line=total)
        model_trainer.train(self.train_path)

    def test_model(self):
        model_trainer = ModelHandler(model_path=self.model_path,model_type='xgb')
        model_trainer.load()
        model_trainer.test_result(self.test_path)

    def test_dataset(self):
        with open(self.output_path) as f:
            keys = set()
            for i, line in enumerate(f):
                obj = json.loads(line)
                keys.update(obj.keys())
            print(f"🧩 Total unique keys: {len(keys)}")
            print(keys)

    def data_extraction(self):
        total,cols = self.get_dataset()
        if total is None:
            return None
        total = self.clean_dataset(total,cols)
        return total

    def training_process(self,total):
        self.train_model(total)
        self.test_model()

    def test_process(self):
        df = self.get_latest_zones()
        
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
