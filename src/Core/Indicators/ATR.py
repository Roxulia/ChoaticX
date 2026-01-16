import ta
from .registry import register_indicator
from Core.Features.meta_registry import register_feature_meta

@register_indicator
@register_feature_meta
class ATR:
    META = {
        'name': 'Average True Range',
        'short_name': 'ATR',
        'description': 'Calculates the Average True Range (ATR) using Exponential Moving Average (EMA).',
        'parameters': {
            'window': {
                'type': 'int',
                'default': 20,
                'description': 'The period for the EMA calculation of ATR.'
            },
            'source': {
                'type': 'str',
                'default': 'close',
                'description': 'The source price column to calculate ATR from.'
            }
        },
        'provides': {
            'atr': 'The calculated Average True Range values.',
            'atr_mean': 'The 50-period rolling mean of the ATR values.'
        },
        'requires': lambda self: {self.source}
    }
    def __init__(self, window=20 , source = 'close'):
        """
        Initialize MovingAverageCrossOver with default or custom MA periods.
        """
        self.window = window
        self.source = source
    
    async def add(self,df):
        data = df.copy()
        atr = ta.trend.ema_indicator(data[self.source], window=self.window)
        data['atr'] = atr
        data['atr_mean'] = data['atr'].rolling(window=50).mean()
        return data
