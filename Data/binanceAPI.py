import os
import pandas as pd
from binance.client import Client
from dotenv import load_dotenv
import ta

class BinanceAPI:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("BINANCE_API_KEY")
        api_secret = os.getenv("BINANCE_SECRET_KEY")
        self.client = Client(api_key, api_secret)

    def get_ohlcv(self, symbol='BTCUSDT', interval=Client.KLINE_INTERVAL_1HOUR, lookback='3 years'):
        """
        Fetch historical OHLCV data and return as formatted DataFrame
        """
        klines = self.client.get_historical_klines(symbol, interval, lookback)

        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])

        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)

        df = df[['open', 'high', 'low', 'close', 'volume']]
        df = df.apply(pd.to_numeric).astype('float32')

        return df
    
    def generate_4H(self,df):
        df_4h = df.resample('4h').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        })
        return df_4h
    
    def generate_1D(self,df):
        df_1d = df.resample('1D').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        })
        return df_1d
    
    def add_TA(self,df):
        data = df.copy()
        data['ema20'] = ta.trend.ema_indicator(data['close'], window=20)
        data['ema50'] = ta.trend.ema_indicator(data['close'], window=50)
        data['atr'] = ta.volatility.average_true_range(data['high'], data['low'], data['close'], window=14)
        data['rsi'] = ta.momentum.rsi(data['close'], window=5)  # Faster RSI for quicker signal
        data['atr_mean'] = data['atr'].rolling(window=50).mean()
        return data



