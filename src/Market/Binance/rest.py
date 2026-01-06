import os
import pandas as pd
import asyncio
from binance.client import Client
from dotenv import load_dotenv
from .timeFrames import timeFrame
from Exceptions.ServiceExceptions import *
from Utility.Logger import Logger

class BinanceRestAPI:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("BINANCE_API_KEY")
        self.api_secret = os.getenv("BINANCE_SECRET_KEY")
        
        self.apiclient = Client(self.api_key, self.api_secret)
        self.broadcast_client = None
        self.bm = None
        self.logger = Logger()

    async def get_ohlcv(self, symbol, interval, lookback=None,limit=None):
        """
        Fetch historical OHLCV data and return as formatted DataFrame
        """
        if lookback is not None:
            self.logger.info(f'Fetching {lookback} worth of {interval} timeframe {symbol} data...')
        elif limit is not None:
            self.logger.info(f'Fetching {limit} candle worth of {interval} timeframe {symbol} data...')
        else:
            lookback = '3 years'
        tf = timeFrame()
        try:
            if lookback is not None :
                klines = self.apiclient.get_historical_klines(symbol,tf.getTimeFrame(interval) , lookback)
            else:
                klines = self.apiclient.get_historical_klines(symbol,tf.getTimeFrame(interval) , limit = 100)

            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])

            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)

            df = df[['open', 'high', 'low', 'close', 'volume','number_of_trades']]
            df = df.apply(pd.to_numeric).astype('float32')
            df['timestamp'] = df.index
            return df
        except Exception as e:
            self.logger.error(f"{self.__class__}:Error:{e}")
            raise CantFetchCandleData