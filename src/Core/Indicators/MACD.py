import ta
from .registry import register_indicator
from Core.Features.meta_registry import register_feature_meta

@register_indicator
@register_feature_meta
class MACD:
    META = {
        'name': 'Moving Average Convergence Divergence',
        'short_name': 'MACD',
        'description': 'Calculates MACD with customizable periods.',
        'parameters': {
            'slow_period': {
                'type': 'int',
                'default': 26,
                'description': 'The slow period for the MACD calculation.'
            },
            'fast_period': {
                'type': 'int',
                'default': 12,
                'description': 'The fast period for the MACD calculation.'
            },
            'signal_period': {
                'type': 'int',
                'default': 9,
                'description': 'The signal period for the MACD calculation.'
            },
            'source': {
                'type': 'str',
                'default': "close",
                "description": "The source price column to calculate MACD from."
            }
        },
        "provides": {
            "macd": "MACD line",
            "macd_signal": "Signal line",
            "macd_diff": "MACD histogram"
        },
        "requires": lambda self: {self.source}
    }

    def __init__(self, slow_period=26, fast_period=12, signal_period=9, source='close'):
        """
        Initialize MovingAverageConvergenceDivergence with default or custom MACD parameters.
        """
        self.slow_period = slow_period
        self.fast_period = fast_period
        self.signal_period = signal_period
        self.source = source
    
    async def add(self, df):
        data = df.copy()
        macd = ta.trend.MACD(data[self.source], window_slow=self.slow_period,
                             window_fast=self.fast_period, window_sign=self.signal_period)
        data['macd'] = macd.macd()
        data['macd_signal'] = macd.macd_signal()
        data['macd_diff'] = macd.macd_diff()
        return data