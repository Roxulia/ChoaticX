from .BaseZone import BaseZone
from tqdm import tqdm
import numpy as np
from Utility.MemoryUsage import MemoryUsage as mu

class OB(BaseZone):

    @mu.log_memory
    def detect(self, threshold = 300,inner_func = False):
        ob_list = []
        close_rolling = self.df['close'].rolling(window=5)
        volume_rolling = self.df['volume'].rolling(window=5)
        avg_vol = volume_rolling.mean().values
        prev_vol= close_rolling.std().values
        momentum = self.closes - np.roll(self.closes, 5)
        
        for i in tqdm(range(5, len(self.df) - 2), desc='Extracting OBs', disable=inner_func):
            open_, close_ = self.opens[i], self.closes[i]
            high_, low_ = self.highs[i], self.lows[i]
            prev_close = self.closes[i - 1]
            next_close = self.closes[i + 1]
            next2_close = self.closes[i + 2]

            body = abs(open_ - close_)
            candle_range = high_ - low_
            if candle_range == 0 or candle_range < threshold:
                continue

            wick_ratio = 1 - (body / candle_range)
            zone_high, zone_low = high_, low_
            body_size = body
            

            # Bullish OB
            if close_ < open_ and prev_close > low_ and next_close > high_ and next2_close > next_close:
                touch_indx = next((j for j in range(i+3, len(self.df))
                                   if self.opens[j] > zone_high and self.closes[j] < zone_high), None)
                ob_list.append(self._build_zone_dict(i, 'Bullish OB', zone_low, zone_high, touch_indx, wick_ratio, body_size, avg_vol,prev_vol,momentum))

            # Bearish OB
            elif close_ > open_ and prev_close < high_ and next_close < low_ and next2_close < next_close:
                touch_indx = next((j for j in range(i+3, len(self.df))
                                   if self.opens[j] < zone_low and self.closes[j] > zone_low), None)
                ob_list.append(self._build_zone_dict(i, 'Bearish OB', zone_low, zone_high, touch_indx, wick_ratio, body_size, avg_vol,prev_vol,momentum))

        return ob_list
    
    def _build_zone_dict(self, i, zone_type, zone_low, zone_high, touch_index, wick_ratio, body_size, avg_vol, prev_vol, momentum):
        return {
            'zone_type': zone_type,
            'trades': self.trades[i],
            'ma_short': self.ma_short[i],
            'ma_long': self.ma_long[i],
            'ema_short': self.ema_short[i],
            'ema_long': self.ema_long[i],
            'atr': self.atr[i],
            'rsi': self.rsi[i],
            'atr_mean': self.atr_mean[i],
            'bb_high': self.bb_high[i],
            'bb_low': self.bb_low[i],
            'bb_mid': self.bb_mid[i],
            'alpha': self.alphas[i] if self.alphas is not None else None,
            'beta': self.betas[i] if self.betas is not None else None,
            'gamma': self.gammas[i] if self.gammas is not None else None,
            'r2': self.r2s[i] if self.r2s is not None else None,
            'zone_high': zone_high,
            'zone_low': zone_low,
            'zone_width': abs(zone_high - zone_low),
            'body_size': body_size,
            'wick_ratio': wick_ratio,
            'volume_on_creation': self.volumes[i],
            'avg_volume_past_5': avg_vol[i],
            'prev_volatility_5': prev_vol[i],
            'momentum_5': momentum[i],
            'touch_index': touch_index,
            'touch_time': self.timestamps[touch_index] if touch_index is not None and touch_index < len(self.timestamps) else None,
            'time_frame': self.timeframe,
            'timestamp': self.timestamps[i]
        }