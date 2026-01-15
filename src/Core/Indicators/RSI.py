import ta
from .registry import register_indicator

@register_indicator
class RSI:
    """
    Detects RSI-based signals such as overbought, oversold, and midline crossovers.
    Suitable for momentum and reversal detection.
    """

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

    