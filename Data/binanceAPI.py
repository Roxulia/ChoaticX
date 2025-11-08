import os
import pandas as pd
import asyncio
import websockets
from binance import AsyncClient, BinanceSocketManager
from binance.client import Client
from dotenv import load_dotenv
import ta
from .timeFrames import timeFrame
from Exceptions.ServiceExceptions import *
from Utility.Logger import Logger
from Core.TechnicalAnalysis.RollingRegression import RollingRegression

class BinanceAPI:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("BINANCE_API_KEY")
        self.api_secret = os.getenv("BINANCE_SECRET_KEY")
        
        self.apiclient = Client(self.api_key, self.api_secret)
        self.broadcast_client = None
        self.bm = None
        self.logger = Logger()

    async def connect(self):
        """Initialize async client + socket manager."""
        try:
            self.broadcast_client= await AsyncClient.create(self.api_key, self.api_secret)
            self.bm = BinanceSocketManager(self.broadcast_client)
        except Exception as e:
            self.logger.error(f"{self.__class__}:Error:{e}")
            raise e

    async def close(self):
        """Close connection gracefully."""
        try:
            if self.broadcast_client:
                await self.broadcast_client.close_connection()
        except Exception as e:
            self.logger.error(f"{self.__class__}:Error:{e}")
            raise e

    async def listen_kline(self, symbols, intervals, callback):
        """
        Subscribe to Binance kline broadcasts.
        - symbols: list of trading pairs, e.g. ["BTCUSDT"]
        - intervals: list of intervals, e.g. ["1h", "4h"]
        - callback: function to call when candle closes
        """
        if not self.bm:
            raise RuntimeError("Call connect() before listen_kline()")
        try:
            streams = []
            for sym in symbols:
                for itv in intervals:
                    streams.append(f"{sym.lower()}@kline_{itv}")

            ms = self.bm.multiplex_socket(streams)

            async with ms as stream:
                while True:
                    msg = await stream.recv()
                    data = msg.get("data", {})
                    kline = data.get("k", {})

                    if kline.get("x"):  # ✅ candle closed
                        await callback(kline)
        except websockets.exceptions.ConnectionClosedOK as e:
            # graceful disconnect
            self.logger.info("⚠️ Binance WebSocket closed normally (1001 Going Away).")
            self.logger.error(f"{self.__class__}:Error:{e}")
            raise e
        except asyncio.CancelledError as e:
            self.logger.error(f"{self.__class__}:Error:{e}")
            raise 
        except Exception as e:
            self.logger.error(f"{self.__class__}:Error:{e}")
            raise e

    def get_ohlcv(self, symbol, interval, lookback,limit):
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
        
    
    
    
    
            
                
            

    




