import ta
from .registry import register_indicator

@register_indicator
class SMA:
    """
    Detects moving average crossover signals (Golden Cross & Death Cross).
    Can be extended for multiple timeframes and custom moving averages.
    """

    def __init__(self, windows = [20,50] , source = 'close'):
        """
        Initialize MovingAverageCrossOver with default or custom MA periods.
        """
        self.windows = windows
        self.source = source
        self.previous_crossover = None  # Store previous crossover info
    
    def add(self,df):
        data = df.copy()
        for w in self.windows:
            data[f'sma_{w}'] = ta.trend.sma_indicator(data[self.source], window=w)
        return data
