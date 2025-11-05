class MovingAverageCrossOver:
    """
    Detects moving average crossover signals (Golden Cross & Death Cross).
    Can be extended for multiple timeframes and custom moving averages.
    """

    def __init__(self, short_window=20, long_window=50):
        """
        Initialize MovingAverageCrossOver with default or custom MA periods.
        """
        self.short_window = short_window
        self.long_window = long_window
        self.previous_crossover = None  # Store previous crossover info

    def detect(self, data):
        """
        Detect crossover signals from a DataFrame containing OHLC data.

        Parameters:
            data (pd.DataFrame): Must contain a 'close' column.
        
        Returns:
            str: 'golden_cross', 'death_cross', or None
        """
        short_ma = data['close'].rolling(window=self.short_window).mean()
        long_ma = data['close'].rolling(window=self.long_window).mean()

        if len(data) < self.long_window:
            return None  # not enough data

        # Check latest and previous crossover state
        if short_ma.iloc[-2] < long_ma.iloc[-2] and short_ma.iloc[-1] > long_ma.iloc[-1]:
            self.updatePreviousCrossOver('golden_cross')
            return 'golden_cross'

        elif short_ma.iloc[-2] > long_ma.iloc[-2] and short_ma.iloc[-1] < long_ma.iloc[-1]:
            self.updatePreviousCrossOver('death_cross')
            return 'death_cross'

        return None

    def getPreviousCrossOver(self):
        """
        Get the most recent crossover signal.
        """
        return self.previous_crossover

    def updatePreviousCrossOver(self, crossover_type):
        """
        Update the last detected crossover.
        """
        self.previous_crossover = crossover_type
