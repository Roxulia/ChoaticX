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
from Data.Columns import IgnoreColumns
from Utility.UtilityClass import UtilityFunctions as utility
from Utility.MemoryUsage import MemoryUsage as mu
from Exceptions.ServiceExceptions import *
from Database.DataModels.FVG import FVG
from Database.DataModels.OB import OB
from Database.DataModels.Liq import LIQ
from Database.Cache import Cache
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
    def __init__(self,symbol = "BTCUSDT",threshold = 300,timeframes = ['1h','4h','1D'],Local = False):
        
        self.api = BinanceAPI()
        self.local = Local
        self.symbol = symbol
        self.threshold = threshold
        self.Paths = Paths()
        self.timeframes = timeframes
        self.ignore_cols = IgnoreColumns()
        self.subscribers = []
        datacleaner = DataCleaner(symbol=self.symbol,timeframes=self.timeframes)
        model_handler1 = ModelHandler(symbol=self.symbol,model_type='xgb')
        model_handler2 = ModelHandler(symbol=self.symbol,timeframes=[self.timeframes[0]],model_type='xgb')
        self.signal_gen = SignalGenerator([model_handler1,model_handler2],datacleaner,[self.ignore_cols.signalGenModelV1,self.ignore_cols.predictionModelV1])
        self.logger = logging.getLogger("SignalService")
        self.logger.setLevel(logging.DEBUG)
        self.initiate_logging()

    def initiate_logging(self):
        load_dotenv()
        # File handler
        file_handler = logging.FileHandler(os.path.join(os.getenv(key='LOG_PATH'), f"signal_service_{self.symbol}.log"))
        file_handler.setLevel(logging.DEBUG)

        # Console handler (optional)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def register_subscribers(self,callback):
        self.subscribers.append(callback)

    def get_zones(self,interval,lookback):
        try:
            df = self.api.get_ohlcv(symbol=self.symbol,interval=interval,lookback=lookback)
        except CantFetchCandleData as e:
            raise CantFetchCandleData
        if interval ==  self.timeframes[0]:
            self.based_candles = df
        detector = ZoneDetector(df)
        zones = detector.get_zones(threshold=self.threshold)
        return zones

    @mu.log_memory
    def get_latest_zones(self,lookback='1 years',initial_state = False):
        t_zones = []
        for tf in self.timeframes:
            try:
                zone = self.get_zones(tf,lookback)
                
                t_zones = t_zones + zone
            except CantFetchCandleData:
                raise CantFetchCandleData
        confluentfinder = ConfluentsFinder(t_zones,self.threshold)
        zones = confluentfinder.getConfluents()
        if initial_state:
            athHandler = ATHHandler(self.symbol,self.based_candles)
            athHandler.updateATH()
        nearByZones = NearbyZones(zones,self.based_candles,threshold=self.threshold)
        zones = nearByZones.getNearbyZone()
        reactor = ZoneReactor()
        zones = reactor.perform_reaction_check(zones,self.based_candles)
        zones = sorted(zones,key=lambda x : x.get("timestamp",None))
        return zones

    def get_untouched_zones(self,limit=0):
        try:
            zones = FVG.getRecentData(symbol=self.symbol,key="timestamp",limit=limit) + OB.getRecentData(symbol=self.symbol,key="timestamp",limit=limit) + LIQ.getRecentData(symbol=self.symbol,key="timestamp",limit=limit)
            if zones:
                return zones
            else:
                raise NoUntouchedZone
        except Exception as e:
            raise e
    
    @mu.log_memory
    def update_ATHzone(self,candle):
        try:
            self.logger.info("Performing ATH update")
            ATH = ATHHandler(self.symbol).getATHFromStorage()
            if ATH['zone_high'] < candle['high']:
                candle_data = self.api.get_ohlcv(symbol=self.symbol,interval= '1h' , lookback= '7 days')
                athHandler = ATHHandler(symbol=self.symbol,candles=candle_data)
                new_ATH = athHandler.getATHFromCandles()
                athHandler.store(new_ATH)
                Cache._client.publish("ath_channel",json.dumps(new_ATH,default=utility.default_json_serializer))
                self.logger.info(f"New ATH FORMED in {self.symbol} with price {new_ATH['zone_high']}")
        except Exception as e:
            self.logger.error(f"Error Occured in Updating ATH : {str(e)}")

    @mu.log_memory
    def get_current_signals(self):
        try:
            self.logger.info(f"{self.symbol} : getting current signal")
            candle = self.api.get_latest_candle(symbol=self.symbol)
            zones = self.get_untouched_zones()
            athHandler = ATHHandler(self.symbol)
            ATH = athHandler.getATHFromStorage()
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
        
    def update_running_signals(self,candle):
        self.logger.info(f"{self.symbol}:Updating Running Signals")
        try:
            
            signals = self.signal_gen.get_running_signals(symbol=self.symbol)
            for s in signals:
                signal_position = s['position']
                if signal_position == 'Long' : 
                    if s['sl'] >= candle['low']:
                        signal_gen.updateSignalStatus(s['id'],"LOSE")
                    elif s['tp'] <= candle['high']:
                        signal_gen.updateSignalStatus(s['id'],"WIN")
                    else:
                        continue
                elif signal_position == 'Short':
                    if s['sl'] <= candle['high']:
                        signal_gen.updateSignalStatus(s['id'],"LOSE")
                    elif s['tp'] >= candle['low']:
                        signal_gen.updateSignalStatus(s['id'],"WIN")
                    else:
                        continue
                else:
                    continue
        except Exception as e:
            self.logger.error(f'Error:Updating Runnning Signals : {self.symbol}:{str(e)}')

    def update_pending_signals(self,candle):
        self.logger.info(f"{self.symbol}:Updating Pending Signals")
        try:
            
            signals = self.signal_gen.get_pending_signals(symbol=self.symbol)
            for s in signals:
                signal_position = s['position']
                if signal_position == 'Long' : 
                    diff = abs(s['sl'] - candle['low'])
                    if diff > self.threshold:
                        if s['sl'] < candle['low'] < s['entry_price']:
                            signal_gen.updateSignalStatus(s['id'],"RUNNING")
                        else:
                            continue
                elif signal_position == 'Short':
                    diff = abs(s['sl'] - candle['high'])
                    if diff>self.threshold:
                        if s['sl'] > candle['high'] > s['entry_price']:
                            signal_gen.updateSignalStatus(s['id'],"RUNNING")
                        else:
                            continue
                    else:
                        continue
        except Exception as e:
            self.logger.error(f'Error:Updating Pending Signals:{self.symbol}:{str(e)}')

    def update_untouched_zones(self):
        try:
            self.logger.info(f"{self.symbol}:Updating Untouch Zones")
            df_from_candle = self.get_latest_zones('6 months')
            temp_df = []
            for i,row in enumerate(df_from_candle):
                #print(row['touch_type'])
                touch_type = row.get('touch_type',None)
                if touch_type is not None:
                    continue
                else:
                    temp_df.append(row)
            datagen = DatasetGenerator(symbol=self.symbol)
            datagen.store_untouch_zones(temp_df)
        except CantFetchCandleData as e:
            self.logger.exception(f'Error : Updating Untouch Zones{self.symbol}:{(e)}')
        except Exception as e:
            self.logger.exception(f'Error : Updating Untouch Zones{self.symbol}:{(e)}')
        

    def get_dataset(self,initial_state=True):
        try:
            df = self.get_latest_zones('3 years',initial_state=initial_state)
        except CantFetchCandleData:
            raise CantFetchCandleData
        datagen = DatasetGenerator(self.symbol,self.timeframes)
        datagen.get_dataset_list(df,for_predict=self.local)
        return datagen.total_line
    
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

    def default_json_serializer(self,obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        elif isinstance(obj, decimal.Decimal):
            return float(obj)
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif hasattr(obj, '__str__'):
            return str(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    
