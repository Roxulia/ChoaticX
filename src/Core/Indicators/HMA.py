import numpy as np
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
            half = int(w / 2)
            sqrt_w = int(np.sqrt(w))

            wma_half = ta.trend.wma_indicator(data[self.source], window=half)
            wma_full = ta.trend.wma_indicator(data[self.source], window=w)

            raw = 2 * wma_half - wma_full
            data[f'hma_{w}'] = ta.trend.wma_indicator(raw, window=sqrt_w)
        return data