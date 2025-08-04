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


class SignalService:
    def __init__(self):
        self.api = BinanceAPI()
        #self.model = Model(...)  # Load pretrained model and transformer
        self.model = None
        self.signal_gen = SignalGenerator(models={'entry_model': self.model})
        self.output_path = 'dataset.jsonl'

    def get_zones(self,interval,lookback):
        df = self.api.get_ohlcv(interval=interval,lookback=lookback)
        detector = ZoneDetector(df)
        zones = detector.get_zones()
        return zones

    def get_latest_zones(self):
        zone_15m = self.get_zones('15min','1 years')
        zone_1h = self.get_zones('1h','1 years')
        zone_4h = self.get_zones('4h','1 years')
        confluentfinder = ConfluentsFinder(zone_15m+zone_1h+zone_4h)
        zones = confluentfinder.getConfluents()
        df = self.api.get_ohlcv(interval='15min',lookback='1 years')
        reactor = ZoneReactor(df)
        zones = reactor.get_zones_reaction(zones)
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
        datacleaner = DataCleaner(self.output_path,batch_size=1000,total_line=total)
        datacleaner.perform_clean()

    def test_dataset(self):
        with open(self.output_path, "r") as f:
            first = f.readline()
            first_obj = json.loads(first)
        with open('dataset.json','w') as f:
            f.write(json.dumps(first_obj))

if __name__ == "__main__" :
    test = SignalService()
    start = time.perf_counter()
    total = test.get_dataset()
    test.clean_dataset(total)
    #test.test_dataset()
    end = time.perf_counter()
    print(f"Execution time: {end - start:.6f} seconds")
