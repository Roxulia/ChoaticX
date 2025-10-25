from Core.ATH_Handler import ATHHandler
from Core.zone_confluents import ConfluentsFinder
from Core.zone_detection import ZoneDetector
from Core.zone_nearby import NearbyZones
from Core.zone_reactions import ZoneReactor
from Core.RollingRegression import RollingRegression
from ML.datasetGeneration import DatasetGenerator
from Exceptions.ServiceExceptions import *
from Data.binanceAPI import BinanceAPI
from Database.DataModels.FVG import FVG
from Database.DataModels.OB import OB
from Database.DataModels.Liq import LIQ
from Database.Cache import Cache
from Utility.MemoryUsage import MemoryUsage as mu
from Utility.UtilityClass import UtilityFunctions as utility
from dotenv import load_dotenv
import os,json,logging

class ZoneHandlingService():
    def __init__(self,symbol,threshold,timeframes):
        self.api = BinanceAPI()
        self.symbol = symbol
        self.threshold = threshold 
        self.timeframes = timeframes
        self.logger = logging.getLogger("ZoneHandlingService")
        self.logger.setLevel(logging.DEBUG)
        self.initiate_logging()

    def initiate_logging(self):
        load_dotenv()
        # File handler
        file_handler = logging.FileHandler(os.path.join(os.getenv(key='LOG_PATH'), f"zone_handling_service_{self.symbol}.log"))
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

    def get_zones(self,interval,lookback):
        try:
            df = self.api.get_ohlcv(symbol=self.symbol,interval=interval,lookback=lookback)
            if self.symbol != 'BTCUSDT':
                df_btc= self.api.get_ohlcv(symbol='BTCUSDT',interval=interval,lookback=lookback)
                roller = RollingRegression(df,df_btc)
                df = roller.AddRegressionValues()
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
        confluentfinder = ConfluentsFinder(t_zones,threshold=self.threshold)
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
        

    def get_dataset(self,initial_state=True,for_predict=False):
        try:
            df = self.get_latest_zones('3 years',initial_state=initial_state)
        except CantFetchCandleData:
            raise CantFetchCandleData
        datagen = DatasetGenerator(self.symbol,self.timeframes)
        datagen.get_dataset_list(df,for_predict=for_predict)
        return datagen.total_line
    
    def getUpdatedATH(self):
        athHandler = ATHHandler(self.symbol)
        ATH = athHandler.getATHFromStorage()
        return ATH
