import os
import pandas as pd
from binance.client import Client
from dotenv import load_dotenv

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



