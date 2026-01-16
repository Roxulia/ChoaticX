import numpy as np
import ta
from .registry import register_indicator
from Core.Features.meta_registry import register_feature_meta

@register_indicator
@register_feature_meta
class HMA:
    META = {
        'name': 'Hull Moving Average',
        'short_name': 'HMA',
        'description': 'Calculates Hull Moving Averages for specified windows.',
        'parameters': {
            'windows': {
                'type': 'list[int]',
                'default': [20, 50],
                'description': 'The periods for the HMA calculations.'
            },
            'source': {
                'type': 'str',
                'default': 'close',
                'description': 'The source price column to calculate HMA from.'
            }
        },
        'provides': lambda self: {f'hma_{w}': f'Hull Moving Average for window {w}' for w in self.windows},
        'requires': lambda self: {self.source}
    }

    def __init__(self, windows = [20,50],source = 'close'):
        """
        Initialize HullMovingAverage with default or custom HMA periods.
        """
        self.windows = windows
        self.source = source
    
    async def add(self,df):
        data = df.copy()
        for w in self.windows:
            half = int(w / 2)
            sqrt_w = int(np.sqrt(w))

            wma_half = ta.trend.wma_indicator(data[self.source], window=half)
            wma_full = ta.trend.wma_indicator(data[self.source], window=w)

            raw = 2 * wma_half - wma_full
            data[f'hma_{w}'] = ta.trend.wma_indicator(raw, window=sqrt_w)
        return data