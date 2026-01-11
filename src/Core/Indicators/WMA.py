import ta
from .registry import register_indicator

@register_indicator
class WMA:
    

    def __init__(self, windows = [20,50],source = 'close'):
        """
        Initialize WeightedMovingAverage with default or custom WMA periods.
        """
        self.windows = windows
        self.source = source
        self.previous_crossover = None  # Store previous crossover info
    
    def add(self,df):
        data = df.copy()
        for w in self.windows:
            data[f'wma_{w}'] = ta.trend.wma_indicator(data[self.source], window=w)
        return data