import ta
from .registry import register_indicator

@register_indicator
class MACD:
    def __init__(self, slow_period=26, fast_period=12, signal_period=9, source='close'):
        """
        Initialize MovingAverageConvergenceDivergence with default or custom MACD parameters.
        """
        self.slow_period = slow_period
        self.fast_period = fast_period
        self.signal_period = signal_period
        self.source = source
    
    def add(self, df):
        data = df.copy()
        macd = ta.trend.MACD(data[self.source], window_slow=self.slow_period,
                             window_fast=self.fast_period, window_sign=self.signal_period)
        data['macd'] = macd.macd()
        data['macd_signal'] = macd.macd_signal()
        data['macd_diff'] = macd.macd_diff()
        return data