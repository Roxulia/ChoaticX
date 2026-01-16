import ta
from .registry import register_indicator
from Core.Features.meta_registry import register_feature_meta

@register_indicator
@register_feature_meta
class WMA:
    META = {
        'name': 'Weighted Moving Average',
        'short_name': 'WMA',
        'description': 'Calculates WMA with customizable windows.',
        'parameters': {
            'windows': {
                'type': 'list',
                'default': [20, 50],
                "description": "The window sizes for the WMA calculation."
            },
            'source': {
                'type': 'str',
                'default': "close",
                "description": "The source price column to calculate WMA from."
            }
        },
        "provides": lambda self: {f"wma_{w}": f"WMA {w}" for w in self.windows},
        "requires": lambda self: {self.source}
    }

    def __init__(self, windows = [20,50],source = 'close'):
        """
        Initialize WeightedMovingAverage with default or custom WMA periods.
        """
        self.windows = windows
        self.source = source
        self.previous_crossover = None  # Store previous crossover info
    
    async def add(self,df):
        data = df.copy()
        for w in self.windows:
            data[f'wma_{w}'] = ta.trend.wma_indicator(data[self.source], window=w)
        return data