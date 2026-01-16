import ta
from .registry import register_indicator
from Core.Features.meta_registry import register_feature_meta
@register_indicator
@register_feature_meta
class EMA:
    META = {
        'name': 'Exponential Moving Average',
        'short_name': 'EMA',
        'description': 'Calculates Exponential Moving Averages for specified windows.',
        'parameters': {
            'windows': {
                'type': 'list[int]',
                'default': [20, 50],
                'description': 'The periods for the EMA calculations.'
            },
            'source': {
                'type': 'str',
                'default': 'close',
                'description': 'The source price column to calculate EMA from.'
            }
        },
        'provides': lambda self: {f'ema_{w}': f'Exponential Moving Average for window {w}' for w in self.windows},
        'requires': lambda self: {self.source}
    }

    def __init__(self, windows = [20,50],source = 'close'):
        """
        Initialize MovingAverageCrossOver with default or custom MA periods.
        """
        self.windows = windows
        self.source = source
    
    async def add(self,df):
        data = df.copy()
        for w in self.windows:
            data[f'ema_{w}'] = ta.trend.ema_indicator(data[self.source], window=w)
        return data


