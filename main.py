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

    def get_zones(self,interval,lookback):
        df = self.api.get_ohlcv(interval=interval,lookback=lookback)
        detector = ZoneDetector(df)
        zones = detector.get_zones()
        return zones

    def get_latest_zones(self):
        zone_15m = self.get_zones('15min','2 years')
        zone_1h = self.get_zones('1h','2 years')
        zone_4h = self.get_zones('4h','2 years')
        confluentfinder = ConfluentsFinder(zone_15m+zone_1h+zone_4h)
        zones = confluentfinder.getConfluents()
        df = self.api.get_ohlcv(interval='15min',lookback='2 years')
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

if __name__ == "__main__" :
    test = SignalService()
    start = time.perf_counter()
    df = test.get_latest_zones()
    df = pd.DataFrame(df)
    df.to_csv('dataset.csv')
    end = time.perf_counter()
    print(f"Execution time: {end - start:.6f} seconds")
