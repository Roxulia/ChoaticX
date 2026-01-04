from .BaseZone import BaseZone
from tqdm import tqdm
from Utility.MemoryUsage import MemoryUsage as mu

class FVG(BaseZone):

    @mu.log_memory
    def detect(self,threshold = 300,inner_func = False):
        fvg_indices = []
        length = len(self.df)
        close_rolling = self.df['close'].rolling(window=5)
        volume_rolling = self.df['volume'].rolling(window=5)
        avg_volume_past_5 = volume_rolling.mean().values
        prev_volatility_5 = close_rolling.std().values
        momentum_5 = self.closes - np.roll(self.closes, 5)

        for i in tqdm(range(5, length - 1), desc='Extracting FVG', disable=inner_func):
            prev_high, prev_low = self.highs[i - 1], self.lows[i - 1]
            next_high, next_low = self.highs[i + 1], self.lows[i + 1]
            body = abs(self.opens[i] - self.closes[i])
            candle_range = self.highs[i] - self.lows[i]
            if candle_range == 0:
                continue
            wick_ratio = 1 - (body / candle_range)
            body_size = body

            # Bullish FVG
            if next_low > prev_high and (next_low - prev_high) >= threshold:
                touch_indx = next((j for j in range(i+2, length)
                                   if self.opens[j] > next_low and self.closes[j] < next_low), None)
                fvg_indices.append(self._build_zone_dict(i, 'Bullish FVG', prev_high, next_low, touch_indx, wick_ratio, body_size, avg_volume_past_5, prev_volatility_5, momentum_5))

            # Bearish FVG
            elif next_high < prev_low and (prev_low - next_high) >= threshold:
                touch_indx = next((j for j in range(i+2, length)
                                   if self.opens[j] < next_high and self.closes[j] > next_high), None)
                fvg_indices.append(self._build_zone_dict(i, 'Bearish FVG', next_high, prev_low, touch_indx, wick_ratio, body_size, avg_volume_past_5, prev_volatility_5, momentum_5))

        return fvg_indices

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