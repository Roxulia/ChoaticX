from .Binance.rest import BinanceRestAPI
from Core.Indicators.TA import TA
from Core import Regimes
from Exceptions.ServiceExceptions import *
from Core import RollingRegression
from Utility import Logger
from Utility import ConfigReader
from dotenv import load_dotenv
import os
class Candles:
    def __init__(self):
        load_dotenv()
        self.api = BinanceRestAPI()
        self.data_root = os.getenv("DATA_PATH")
        self.logger = Logger()
        self.config = ConfigReader("config.json")
        self.TA = TA(self.config.getIndicatorsConfig())
        self.regimes = Regimes(self.config.getRegimesConfig())
        self.RR = self.config.getRollingRegression()

    async def getCandleData(self,symbol,interval,lookback,limit = False):
        if limit:
            based_data = await self.api.get_ohlcv(symbol,interval,limit=100)
            data = self.TA.add(based_data)
            data = self.regimes.add(data)
            if self.RR['enabled']: 
                rr = RollingRegression()
                market_data = await self.api.get_ohlcv(self.RR['base'],interval,limit = 100)
                data = rr.AddRegressionValues(data,market_data)
        else:
            based_data = await self.api.get_ohlcv(symbol,interval,lookback)
            data = self.TA.add(based_data)
            data = self.regimes.add(data)
            if self.RR['enabled']: 
                rr = RollingRegression()
                market_data = await self.api.get_ohlcv(self.RR['base'],interval,lookback)
                data = rr.AddRegressionValues(data,market_data)
        return data
    
    async def getLatestCandle(self,symbol,interval):
        based_data = await self.api.get_ohlcv(symbol,interval,limit = 100)
        data = self.TA.add(based_data)
        data = self.regimes.add(data)
        if self.RR['enabled']: 
                rr = RollingRegression()
                market_data = await self.api.get_ohlcv(self.RR['base'],interval,limit = 100)
                data = rr.AddRegressionValues(data,market_data)
        return data.iloc[-1]

    def store_OHLCV(self, symbol, interval,lookback):
        """
        Store OHLCV data to a CSV file
        """
        try:
            try:
                df = self.api.get_ohlcv(symbol, interval, lookback)
            except CantFetchCandleData as e:
                raise CantFetchCandleData
            file_path = f"{self.data_root}/OHLCV/{symbol}_{interval}_{lookback}.csv"
            df.to_csv(file_path)
            self.logger.info(f"Data stored to {file_path}")
            return file_path
        except:
            raise CantSaveToCSV


    async def performFeatureEngineering(self, df):
        """
        Perform feature engineering on the DataFrame
        """
        try:
            data = self.TA.add(df)
            if self.RR['enabled']: 
                rr = RollingRegression()
                market_data = await self.api.get_ohlcv(self.RR['base'],interval,lookback)
                data = rr.AddRegressionValues(data,market_data)
            return data
        except Exception as e:
            self.logger.error(f"Error in feature engineering: {e}")
            raise

