from Core.zone_detection import ZoneDetector
from Core.zone_reactions import ZoneReactor
from Core.zone_merge import ZoneMerger
from Core.zone_confluents import ConfluentsFinder
from Core.SignalGeneration import SignalGenerator
from Core.Filter import Filter
from ML.Model import ModelHandler
from ML.dataCleaning import DataCleaner
from ML.datasetGeneration import DatasetGenerator
from Data.binanceAPI import BinanceAPI
import time
import pandas as pd
import json
from dotenv import load_dotenv
import os
class SignalService:
    def __init__(self):
        load_dotenv()
        self.api = BinanceAPI()
        #self.model = Model(...)  # Load pretrained model and transformer
        self.model = None
        self.signal_gen = SignalGenerator(models={'entry_model': self.model})
        self.output_path = os.getenv(key='RAW_DATA')
        self.train_path = os.getenv(key='TRAIN_DATA')
        self.test_path = os.getenv(key='TEST_DATA')
        self.model_path = os.getenv(key='MODEL_PATH')

    def get_zones(self,interval,lookback):
        df = self.api.get_ohlcv(interval=interval,lookback=lookback)
        detector = ZoneDetector(df)
        zones = detector.get_zones()
        return zones

    def get_latest_zones(self):
        zone_15m = self.get_zones('15min','3 months')
        zone_1h = self.get_zones('1h','3 months')
        zone_4h = self.get_zones('4h','3 months')
        confluentfinder = ConfluentsFinder(zone_15m+zone_1h+zone_4h)
        zones = confluentfinder.getConfluents()
        df = self.api.get_ohlcv(interval='15min',lookback='3 months')
        reactor = ZoneReactor(df)
        zones = reactor.get_zones_reaction(zones)
        zones = reactor.get_next_target_zone(zones)
        return zones

    def get_current_signals(self):
        df = self.api.get_ohlcv()
        zones = self.get_latest_zones()
        reactor = ZoneReactor(df, zones)
        reaction = reactor.get_last_candle_reaction()
        if not reaction == 'None':
            return self.signal_gen.generate(df.iloc[-1],zones,reaction)
        return 'None'
    
    def get_dataset(self):
        df = self.get_latest_zones()
        datagen = DatasetGenerator(df)
        datagen.get_dataset_list(self.output_path)
        return datagen.total_line
    
    def clean_dataset(self,total):
        datacleaner = DataCleaner(self.output_path,batch_size=1000,total_line=total,train_path=self.train_path,test_path=self.test_path)
        return datacleaner.perform_clean()
        
    def train_model(self,total):
        model_trainer = ModelHandler(model_path=self.model_path,model_type='xgb',total_line=total)
        model_trainer.train(self.train_path)

    def test_model(self):
        model_trainer = ModelHandler(model_path=self.model_path,model_type='xgb',total_line=total)
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


if __name__ == "__main__" :
    pd.set_option('future.no_silent_downcasting', True)
    test = SignalService()
    start = time.perf_counter()
    total = test.get_dataset()
    total = test.clean_dataset(total)
    #test.test_dataset()
    test.train_model(total)
    test.test_model()
    end = time.perf_counter()
    print(f"Execution time: {end - start:.6f} seconds")
