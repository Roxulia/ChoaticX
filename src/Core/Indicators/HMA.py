import ta
from .registry import register_indicator

@register_indicator
class HMA:
    

    def __init__(self, windows = [20,50],source = 'close'):
        """
        Initialize HullMovingAverage with default or custom HMA periods.
        """
        self.windows = windows
        self.source = source
        self.previous_crossover = None  # Store previous crossover info
    
    def add(self,df):
        data = df.copy()
        for w in self.windows:
            data[f'ma_{w}'] = ta.trend.hma_indicator(data[self.source], window=w)
        return data