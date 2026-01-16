import ta
from .registry import register_indicator
from Core.Features.meta_registry import register_feature_meta

@register_indicator
@register_feature_meta
class SMA:
    """
    Detects moving average crossover signals (Golden Cross & Death Cross).
    Can be extended for multiple timeframes and custom moving averages.
    """
    META = {
        'name': 'Simple Moving Average',
        'short_name': 'SMA',
        'description': 'Calculates SMA with customizable windows.',
        'parameters': {
            'windows': {
                'type': 'list',
                'default': [20, 50],
                "description": "The window sizes for the SMA calculation."
            },
            'source': {
                'type': 'str',
                'default': "close",
                "description": "The source price column to calculate SMA from."
            }
        },
        "provides": lambda self: {f"sma_{w}": f"SMA {w}" for w in self.windows},
        "requires": lambda self: {self.source}
    }

    def __init__(self, windows = [20,50] , source = 'close'):
        """
        Initialize MovingAverageCrossOver with default or custom MA periods.
        """
        self.windows = windows
        self.source = source
        self.previous_crossover = None  # Store previous crossover info
    
    async def add(self,df):
        data = df.copy()
        for w in self.windows:
            data[f'sma_{w}'] = ta.trend.sma_indicator(data[self.source], window=w)
        return data
