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

class BinanceAPI:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("BINANCE_API_KEY")
        self.api_secret = os.getenv("BINANCE_SECRET_KEY")
        self.data_root = os.getenv("DATA_PATH")
        self.apiclient = Client(self.api_key, self.api_secret)
        self.broadcast_client = None
        self.bm = None

    async def connect(self):
        """Initialize async client + socket manager."""
        try:
            self.broadcast_client= await AsyncClient.create(self.api_key, self.api_secret)
            self.bm = BinanceSocketManager(self.broadcast_client)
        except Exception as e:
            raise e

    async def close(self):
        """Close connection gracefully."""
        try:
            if self.broadcast_client:
                await self.broadcast_client.close_connection()
        except Exception as e:
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
        except websockets.exceptions.ConnectionClosedOK:
            # graceful disconnect
            print("⚠️ Binance WebSocket closed normally (1001 Going Away).")
            raise Exception("ConnectionClosedOK")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            raise e

    def get_ohlcv(self, symbol='BTCUSDT', interval='1h', lookback='3 years'):
        """
        Fetch historical OHLCV data and return as formatted DataFrame
        """
        print(f'Fetching {lookback} worth of {interval} timeframe {symbol} data...')
        tf = timeFrame()
        try:
            klines = self.apiclient.get_historical_klines(symbol,tf.getTimeFrame(interval) , lookback)

            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])

            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)

            df = df[['open', 'high', 'low', 'close', 'volume','number_of_trades']]
            df = df.apply(pd.to_numeric).astype('float32')
            df = self.add_TA(df)
            df['timestamp'] = df.index
            return df
        except Exception as e:
            print(f'{str(e)}')
            raise CantFetchCandleData
        
    
    def add_TA(self,df):
        data = df.copy()
        data['ema20'] = ta.trend.ema_indicator(data['close'], window=20)
        data['ema50'] = ta.trend.ema_indicator(data['close'], window=50)
        data['atr'] = ta.volatility.average_true_range(data['high'], data['low'], data['close'], window=14)
        data['rsi'] = ta.momentum.rsi(data['close'], window=5)  # Faster RSI for quicker signal
        data['atr_mean'] = data['atr'].rolling(window=50).mean()

        bb = ta.volatility.BollingerBands(close=data["close"], window=20, window_dev=2)
        data["bb_high"] = bb.bollinger_hband()
        data["bb_low"] = bb.bollinger_lband()
        data["bb_mid"] = bb.bollinger_mavg()
        return data
    
    def get_latest_candle(self,symbol='BTCUSDT',interval = '1h'):
        tf = timeFrame()
        try:
            klines = self.apiclient.get_historical_klines(symbol,tf.getTimeFrame(interval) , limit = 100)

            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])

            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)

            df = df[['open', 'high', 'low', 'close', 'volume']]
            df = df.apply(pd.to_numeric).astype('float32')
            df = self.add_TA(df)
            df['timestamp'] = df.index
            return df.iloc[-1]
        except Exception as e:
            print(f'{str(e)}')
            raise CantFetchCandleData
    
    def store_OHLCV(self, symbol='BTCUSDT', interval='1h',lookback='3 years'):
        """
        Store OHLCV data to a CSV file
        """
        try:
            try:
                df = self.get_ohlcv(symbol, interval, lookback)
            except CantFetchCandleData as e:
                raise CantFetchCandleData
            file_path = f"{self.data_root}/OHLCV/{symbol}_{interval}_{lookback}.csv"
            df.to_csv(file_path)
            print(f"Data stored to {file_path}")
            return file_path
        except:
            raise CantSaveToCSV
            
                
            

    




