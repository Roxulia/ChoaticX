import os
import json
from dotenv import load_dotenv
import datetime
import decimal
import numpy as np
from Data.Paths import Paths
class ATHHandler():
    def __init__(self,symbol = "BTCUSDT",candles=[]):
        self.candles = candles
        self.symbol = symbol
        self.Paths = Paths()

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
    
    def getATHFromCandles(self):
        data = self.candles
        if data is None or data.empty:
            print("candle is None")
            return None
        # Find ATH index (timestamp) and integer position
        ath_idx = data['high'].idxmax()
        index = data.index.get_loc(ath_idx)  # integer position
        ATH_zone = data.iloc[index]

        # Rolling stats
        close_rolling = data['close'].rolling(window=5)
        volume_rolling = data['volume'].rolling(window=5)

        avg_volume_past_5 = volume_rolling.mean().values
        prev_volatility_5 = close_rolling.std().values
        momentum_5 = data['close'] - data['close'].shift(5)

        # Build ATH zone dict
        ath = {
            'zone_high': float(ATH_zone['high']),
            'zone_low': float(ATH_zone['low']),
            'ema 20': float(ATH_zone['ema20']),
            'ema 50': float(ATH_zone['ema50']),
            'rsi': float(ATH_zone['rsi']),
            'atr': float(ATH_zone['atr']),
            'volume_on_creation': float(ATH_zone['volume']),
            'avg_volume_past_5': float(avg_volume_past_5[index]),
            'prev_volatility_5': float(prev_volatility_5[index]),
            'momentum_5': float(momentum_5.iloc[index]),
            'zone_type': 'ATH',
            'index': index,
            'timestamp' : ATH_zone['timestamp']
        }

        return ath
    
    def getATHFromStorage(self):
        if not os.path.exists(f"{self.Paths.ath_data}/{self.symbol}.json"):
            return None

        with open(f"{self.Paths.ath_data}/{self.symbol}.json", "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return None

    def updateATH(self):
        candleATH = self.getATHFromCandles()
        storageATH = self.getATHFromStorage()
        if storageATH is None:
            if candleATH is None:
                return False
            else:
                return self.store(candleATH)
        else:
            if candleATH is None:
                return False
            else:
                if candleATH['zone_low'] > storageATH['zone_low']:
                    return self.store(candleATH)
                else:
                    return self.store(storageATH)

    def store(self,data):
        try:
            with open(f"{self.Paths.ath_data}/{self.symbol}.json", 'w') as f:
                json.dump(data, f, indent=4,default=self.default_json_serializer)
            return True
        except:
            print("File Storage Error")
            return False
        
