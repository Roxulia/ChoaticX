import ta
class ATR:
    def __init__(self, window=20):
        """
        Initialize MovingAverageCrossOver with default or custom MA periods.
        """
        self.window = window
    
    def add(self,df):
        data = df.copy()
        atr = ta.trend.ema_indicator(data['close'], window=self.window)
        data['atr'] = atr
        data['atr_mean'] = data['atr'].rolling(window=50).mean()
        return data
