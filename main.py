from Core.zone_detection import ZoneDetector
from Core.zone_reactions import ZoneReactor
from Core.zone_merge import ZoneMerger
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

    def get_latest_zones(self):
        df_15min = self.api.get_ohlcv(interval= '15min',lookback='2 years')
        detector = ZoneDetector(df_15min)
        zones_15min = detector.get_zones()
        df_1h = self.api.get_ohlcv(interval= '1h',lookback='2 years')
        detector = ZoneDetector(df_1h)
        zones_1h = detector.get_zones()
        df = self.api.get_ohlcv(interval= '4h',lookback= '2 years')
        detector = ZoneDetector(df,'4h')
        zones_4h = detector.get_zones()
        
        merger = ZoneMerger(df_15min,zones_15min+zones_1h+zones_4h)
        zones = merger.merge()
        zones = merger.getNearbyZone(zones)
        return zones

    def get_current_signals(self):
        df = self.api.get_ohlcv()
        zones = self.get_latest_zones()
        reactor = ZoneReactor(df, zones)
        reaction = reactor.get_last_candle_reaction()
        if not reaction == 'None':
            return self.signal_gen.generate(df.iloc[-1],zones,reaction)
        return 'None'

if __name__ == "__main__" :
    test = SignalService()
    start = time.perf_counter()
    df = test.get_latest_zones()
    datagen = DatasetGenerator(df)
    built_by = datagen.extract_built_by_zones(10)
    with open('output.txt', 'w') as f:
        f.write(f'{built_by}')
    df = datagen.to_dataframe()
    df.to_csv('dataset.csv')
    end = time.perf_counter()
    print(f"Execution time: {end - start:.6f} seconds")
