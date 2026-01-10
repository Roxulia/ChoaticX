import ta
from .registry import register_indicator

@register_indicator
class ATR:
    def __init__(self, window=20 , source = 'close'):
        """
        Initialize MovingAverageCrossOver with default or custom MA periods.
        """
        self.window = window
        self.source = source
    
    def add(self,df):
        data = df.copy()
        atr = ta.trend.ema_indicator(data[self.source], window=self.window)
        data['atr'] = atr
        data['atr_mean'] = data['atr'].rolling(window=50).mean()
        return data
