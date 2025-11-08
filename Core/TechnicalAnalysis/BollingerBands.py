import ta
class BollingerBands:
    """
    Detects moving average crossover signals (Golden Cross & Death Cross).
    Can be extended for multiple timeframes and custom moving averages.
    """

    def __init__(self, window=20, window_dev = 2):
        """
        Initialize MovingAverageCrossOver with default or custom MA periods.
        """
        self.window = window
        self.window_dev = window_dev
    
    def add(self,df):
        data = df.copy()
        bb = ta.volatility.BollingerBands(close=data["close"], window=self.window, window_dev=self.window_dev)
        data["bb_high"] = bb.bollinger_hband()
        data["bb_low"] = bb.bollinger_lband()
        data["bb_mid"] = bb.bollinger_mavg()
        return data


    
