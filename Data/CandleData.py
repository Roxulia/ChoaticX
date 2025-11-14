from .binanceAPI import BinanceAPI
from Core.TA import TA
from Exceptions.ServiceExceptions import *
from Utility.Logger import Logger
from dotenv import load_dotenv
import os
class CandleData:
    def __init__(self):
        load_dotenv()
        self.api = BinanceAPI()
        self.data_root = os.getenv("DATA_PATH")
        self.logger = Logger()

    async def getCandleData(self,symbol,interval,lookback):
        based_data = await self.api.get_ohlcv(symbol,interval,lookback)
        self.TA = TA()
        data = self.TA.add(based_data)
        if symbol != 'BTCUSDT' : 
            market_data = await self.api.get_ohlcv('BTCUSDT',interval,lookback)
            data = self.TA.add_RollingRegression(data,market_data)
        return data
    
    async def getLatestCandle(self,symbol,interval):
        based_data = await self.api.get_ohlcv(symbol,interval,limit = 100)
        self.TA = TA()
        data = self.TA.add(based_data)
        if symbol != 'BTCUSDT' : 
            market_data = await self.api.get_ohlcv('BTCUSDT',interval,limit = 100)
            data = self.TA.add_RollingRegression(data,market_data)
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

