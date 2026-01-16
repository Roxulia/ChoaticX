import ta
from .registry import register_indicator
from Core.Features.meta_registry import register_feature_meta

@register_indicator
@register_feature_meta
class RSI:
    """
    Detects RSI-based signals such as overbought, oversold, and midline crossovers.
    Suitable for momentum and reversal detection.
    """
    META = {
        'name': 'Relative Strength Index',
        'short_name': 'RSI',
        'description': 'Calculates RSI with customizable window.',
        'parameters': {
            'window': {
                'type': 'int',
                'default': 5,
                'description': 'The window for the RSI calculation.'
            },
            'source': {
                'type': 'str',
                'default': "close",
                "description": "The source price column to calculate RSI from."
            }
        },
        "provides": {
            "rsi": "RSI value"
        },
        "requires": lambda self: {self.source}
    }

    def __init__(self, window = 5,source = 'close'):
        """
        Initialize RSIAnalyzer with threshold values.
        """
        self.source = source
        self.window = window

    async def add(self,df):
        data = df.copy()
        data['rsi'] = ta.momentum.rsi(data[self.source], window=self.window)
        return data

    