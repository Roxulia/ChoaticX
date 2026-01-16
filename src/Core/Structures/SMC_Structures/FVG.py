from .BaseZone import BaseZone
from tqdm import tqdm
import numpy as np
from Utility.MemoryUsage import MemoryUsage as mu
from ..registry import register_structure
from Core.Features.meta_registry import register_feature_meta

@register_structure
@register_feature_meta
class FVG(BaseZone):

    META = {
        'name': 'FVG',
        'short_name': 'FVG',
        'description': 'Detects FVG in price data.',
        'parameters': {
            'threshold': {
                'type': 'float',
                'default': 0.02,
                "description": "The threshold for FVG detection."
            }
        },
        "provides": {
            "fvg": "Detected FVG points"
        },
        "requires": {}
    }

    def __init__(self, df = ...,threshold = 0.02):
        super().__init__(df)
        self.threshold = threshold

    @mu.log_memory
    def detect(self,inner_func = False):
        fvg_indices = []
        length = len(self.df)
        close_rolling = self.df['close'].rolling(window=5)
        volume_rolling = self.df['volume'].rolling(window=5)
        avg_volume_past_5 = volume_rolling.mean().values
        prev_volatility_5 = close_rolling.std().values
        momentum_5 = self.closes - np.roll(self.closes, 5)
        pip_range = (self.highs.max() - self.lows.min()) * self.threshold
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
            if next_low > prev_high and (next_low - prev_high) >= pip_range:
                touch_indx = next((j for j in range(i+2, length)
                                   if self.opens[j] > next_low and self.closes[j] < next_low), None)
                fvg_indices.append(self._build_zone_dict(i, 'Bullish FVG', prev_high, next_low, touch_indx, wick_ratio, body_size, avg_volume_past_5, prev_volatility_5, momentum_5))

            # Bearish FVG
            elif next_high < prev_low and (prev_low - next_high) >= pip_range:
                touch_indx = next((j for j in range(i+2, length)
                                   if self.opens[j] < next_high and self.closes[j] > next_high), None)
                fvg_indices.append(self._build_zone_dict(i, 'Bearish FVG', next_high, prev_low, touch_indx, wick_ratio, body_size, avg_volume_past_5, prev_volatility_5, momentum_5))
        self.fvg = fvg_indices
        return fvg_indices

    def _build_zone_dict(self, i, zone_type, zone_low, zone_high, touch_index, wick_ratio, body_size, avg_vol, prev_vol, momentum):
        return {
            'timestamp': self.timestamps[i],
            'zone_type': zone_type,
            'zone_high': zone_high,
            'zone_low': zone_low,
            'zone_width': abs(zone_high - zone_low),
            'body_size': body_size,
            'wick_ratio': wick_ratio,
            'volume_on_creation': self.volumes[i],
            'trades': self.trades[i],
            'avg_volume_past_5': avg_vol[i],
            'prev_volatility_5': prev_vol[i],
            'momentum_5': momentum[i],
            'touch_index': touch_index,
            'touch_time': self.timestamps[touch_index] if touch_index is not None and touch_index < len(self.timestamps) else None,
            **self.df.iloc[i],
        }