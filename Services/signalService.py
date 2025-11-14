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
from Data.CandleData import CandleData
from Data.Columns import IgnoreColumns
from Utility.UtilityClass import UtilityFunctions as utility
from Utility.MemoryUsage import MemoryUsage as mu
from Utility.Logger import Logger
from Exceptions.ServiceExceptions import *
from Database.DataModels.FVG import FVG
from Database.DataModels.OB import OB
from Database.DataModels.Liq import LIQ
from Database.Cache import Cache
from .zoneHandlingService import ZoneHandlingService
import pandas as pd
import json
from dotenv import load_dotenv
from tqdm import tqdm
from Data.Paths import Paths
from flask_socketio import SocketIO
import os
import redis
import logging
import numpy as np
import datetime,decimal

class SignalService:
    def __init__(self,symbol = "BTCUSDT",threshold = 300,timeframes = ['1h','4h','1D'],Local = False,initial = False):
        
        self.api = CandleData()
        self.local = Local
        self.symbol = symbol
        self.threshold = threshold
        self.Paths = Paths()
        self.timeframes = timeframes
        self.ignore_cols = IgnoreColumns()
        self.subscribers = []
        self.zoneHandler = ZoneHandlingService(self.symbol,self.threshold,self.timeframes)
        if not initial:
            datacleaner = DataCleaner(symbol=self.symbol,timeframes=self.timeframes)
            model_handler1 = ModelHandler(symbol=self.symbol,model_type='xgb')
            model_handler2 = ModelHandler(symbol=self.symbol,timeframes=[self.timeframes[0]],model_type='xgb')
            self.signal_gen = SignalGenerator([model_handler1,model_handler2],datacleaner,[self.ignore_cols.signalGenModelV1,self.ignore_cols.predictionModelV1])
        self.logger = Logger()
        
    async def get_predicted_result(self,zones,candle,ATH,datagen : DatasetGenerator,nearbyzone : NearbyZones,reaction_data):
        use_zones = []
        for i,zone in tqdm(enumerate(zones),desc = 'Getting Touched Zone Data'):
            curr_timestamp = pd.to_datetime(zone['timestamp'])
            if curr_timestamp == reaction_data['touch_time']:
                zone['candle_number_of_trades'] = candle['number_of_trades']
                zone['candle_volume'] = candle['volume']
                zone['candle_open'] = candle['open']
                zone['candle_close'] = candle['close']
                zone['candle_ema_short'] = candle['ema_short']
                zone['candle_ema_long'] = candle['ema_long']
                zone['candle_ma_short'] = candle['ma_short']
                zone['candle_ma_long'] = candle['ma_long']
                zone['candle_rsi'] = candle['rsi']
                zone['candle_atr'] = candle['atr']
                zone['candle_bb_high'] = candle['bb_high']
                zone['candle_bb_low'] = candle['bb_low']
                zone['candle_bb_mid'] = candle['bb_mid']
                if self.symbol != 'BTCUSDT' : 
                    zone['candle_alpha'] = candle['alpha'] if 'alpha' in candle else None
                    zone['candle_beta'] = candle['beta'] if 'beta' in candle else None
                    zone['candle_gamma'] = candle['gamma'] if 'gamma' in candle else None
                    zone['candle_r2'] = candle['r2'] if 'r2' in candle else None
                zone['touch_type'] = reaction_data['touch_type']
                zone['touch_from'] = reaction_data['touch_from']
                zone = nearbyzone.getAboveBelowZones(zone, zones, ATH)
                use_zones.append(zone)
                
        input_set = list(datagen.extract_input_data(use_zones))
        signal = await self.signal_gen.generate(input_set)
        return signal,use_zones
    
    @mu.log_memory
    async def get_current_signals(self):
        try:
            self.logger.info(f"{self.symbol} : getting current signal")
            candle = await self.api.getLatestCandle(symbol=self.symbol,interval=self.timeframes[0])
            zones = await self.zoneHandler.get_untouched_zones()
            ATH = await self.zoneHandler.getUpdatedATH()

            reactor = ZoneReactor()
            datagen = DatasetGenerator(self.symbol,self.timeframes)
            reaction_data = reactor.get_last_candle_reaction(zones,candle)
            nearbyzone = NearbyZones(threshold=self.threshold)
            signal,use_zones = await self.get_predicted_result(zones,candle,ATH,datagen,nearbyzone,reaction_data)
            if signal != 'None' and signal is not None:
                await self.zoneHandler.deleteUsedZones(use_zones)
                data = {k:v for k,v in signal.items() if k != "meta"}
                Cache._client.publish("signals_channel", json.dumps(data,default=utility.default_json_serializer))
                self.logger.info(f"new signal generated : {signal['symbol']},{signal['position']},{signal['tp']},{signal['sl']},{signal['entry_price']}")
            return signal
        except Exception as e:
            self.logger.error(f'Error:Getting New Signal:{self.symbol}:{str(e)}')
    
    def get_given_signals(self):
        
        try:
            signals = self.signal_gen.get_given_signals(symbol=self.symbol)
            return signals
        except Exception as e:
            raise e
        
    async def update_running_signals(self,candle):
        self.logger.info(f"{self.symbol}:Updating Running Signals")
        try:
            await self.signal_gen.updateSignals(self.symbol,self.threshold,candle,'RUNNING')
        except Exception as e:
            self.logger.error(f'Error:Updating Runnning Signals : {self.symbol}:{str(e)}')

    async def update_pending_signals(self, candle):
        self.logger.info(f"{self.symbol}: Updating Pending Signals in chunks")
        try:
            await self.signal_gen.updateSignals(self.symbol,self.threshold,candle,'PENDING')
        except Exception as e:
            self.logger.error(f"Error Updating Pending Signals: {self.symbol}: {str(e)}")      
    
    def clean_dataset(self,total):
        datacleaner = DataCleaner(symbol = self.symbol,timeframes=self.timeframes,batch_size=1000,total_line=total)
        return datacleaner.perform_clean(self.ignore_cols.signalGenModelV1)
        
    def train_model(self,total):
        model_trainer = ModelHandler(symbol=self.symbol,timeframes=self.timeframes,model_type='xgb',total_line=total)
        model_trainer.train()

    def test_model(self):
        model_trainer = ModelHandler(symbol=self.symbol,model_type='xgb',timeframes=self.timeframes)
        model_trainer.load()
        model_trainer.test_result()

    def data_extraction(self):
        try:
            total = self.zoneHandler.get_dataset(for_predict=self.local)
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


    
