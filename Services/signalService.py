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
        
    @mu.log_memory
    def get_current_signals(self):
        self.logger.info(f"{self.symbol} : getting current signal")
        try:
            
            candle = self.api.getLatestCandle(symbol=self.symbol,interval=self.timeframes[0])
            zones = self.zoneHandler.get_untouched_zones()
            ATH = self.zoneHandler.getUpdatedATH()
            reactor = ZoneReactor()
            datagen = DatasetGenerator(self.symbol)
            reaction_data = reactor.get_last_candle_reaction(zones,candle)
            nearbyzone = NearbyZones(threshold=self.threshold)
            use_zones = []
            
            for i,zone in tqdm(enumerate(zones),desc = 'Getting Touched Zone Data'):
                curr_timestamp = pd.to_datetime(zone['timestamp'])
                if curr_timestamp == reaction_data['touch_time']:
                    zone['candle_volume'] = candle['volume']
                    zone['candle_open'] = candle['open']
                    zone['candle_close'] = candle['close']
                    zone['candle_ema20'] = candle['ema20']
                    zone['candle_ema50'] = candle['ema50']
                    zone['candle_rsi'] = candle['rsi']
                    zone['candle_atr'] = candle['atr']
                    zone['candle_bb_high'] = candle['bb_high']
                    zone['candle_bb_low'] = candle['bb_low']
                    zone['candle_bb_mid'] = candle['bb_mid']
                    if self.symbol != 'BTCUSDT':
                        zone['candle_alpha'] = candle['alpha']
                        zone['candle_beta'] = candle['beta']
                        zone['candle_gamma'] = candle['gamma']
                        zone['candle_r2'] = candle['r2']
                    zone['touch_type'] = reaction_data['touch_type']
                    zone['touch_from'] = reaction_data['touch_from']
                    zone = nearbyzone.getAboveBelowZones(zone, zones, ATH)
                    use_zones.append(zone)
                    
            input_set = list(datagen.extract_input_data(use_zones))
            signal = self.signal_gen.generate(input_set)
            if signal != 'None' and signal is not None:
                for zone in use_zones:
                    id = zone.get('id',None)
                    if id is not None:
                        zone_type = zone.get('zone_type',None)
                        if zone_type in ['Bearish FVG','Bullish FVG'] : 
                            FVG.delete(id)
                        elif zone_type in ['Bearish OB','Bullish OB'] :
                            OB.delete(id)
                        elif zone_type in ['Buy-Side Liq','Sell-Side Liq']:
                            LIQ.delete(id)
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
        
    def update_running_signals(self,candle,chunk_size=20):
        self.logger.info(f"{self.symbol}:Updating Running Signals")
        offset = 0
        try:
            
            while True:
                signals = self.signal_gen.get_running_signals(
                    symbol=self.symbol, limit=chunk_size, offset=offset
                )
                if not signals:
                    break

                win_ids, lose_ids = [], []
                for s in signals:
                    pos = s['position']
                    if pos == 'Long':
                        if s['sl'] >= candle['low']:
                            lose_ids.append(s['id'])
                        elif s['tp'] <= candle['high']:
                            win_ids.append(s['id'])
                    elif pos == 'Short':
                        if s['sl'] <= candle['high']:
                            lose_ids.append(s['id'])
                        elif s['tp'] >= candle['low']:
                            win_ids.append(s['id'])

                if win_ids:
                    self.signal_gen.bulkUpdateSignals("WIN",win_ids)
                if lose_ids:
                    self.signal_gen.bulkUpdateSignals("LOSE",lose_ids)

                offset += chunk_size  # move to next chunk

        except Exception as e:
            self.logger.error(f'Error:Updating Runnning Signals : {self.symbol}:{str(e)}')

    def update_pending_signals(self, candle, chunk_size=20):
        self.logger.info(f"{self.symbol}: Updating Pending Signals in chunks")
        offset = 0

        try:
            while True:
                # ✅ Fetch a batch of pending signals
                signals = self.signal_gen.get_pending_signals(
                    symbol=self.symbol, limit=chunk_size, offset=offset
                )
                if not signals:
                    break

                running_ids = []

                for s in signals:
                    pos = s['position']
                    if pos == 'Long':
                        diff = abs(s['sl'] - candle['low'])
                        if diff > self.threshold and s['sl'] < candle['low'] < s['entry_price']:
                            running_ids.append(s['id'])
                    elif pos == 'Short':
                        diff = abs(s['sl'] - candle['high'])
                        if diff > self.threshold and s['sl'] > candle['high'] > s['entry_price']:
                            running_ids.append(s['id'])

                # ✅ Batch update instead of one-by-one
                if running_ids:
                    self.signal_gen.bulkUpdateSignals("RUNNING",running_ids)

                offset += chunk_size

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


    
