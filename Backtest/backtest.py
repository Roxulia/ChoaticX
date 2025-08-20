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
    def __init__(self):
        load_dotenv()
        self.api = BinanceAPI()
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

    def get_latest_zones(self):
        # Implementation similar to SignalService
        pass