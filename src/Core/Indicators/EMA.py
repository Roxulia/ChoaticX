import ta
from .registry import register_indicator

@register_indicator
class EMA:
    

    def __init__(self, windows = [20,50],source = 'close'):
        """
        Initialize MovingAverageCrossOver with default or custom MA periods.
        """
        self.windows = windows
        self.source = source
        self.previous_crossover = None  # Store previous crossover info
    
    async def add(self,df):
        data = df.copy()
        for w in self.windows:
            data[f'ema_{w}'] = ta.trend.ema_indicator(data[self.source], window=w)
        return data


