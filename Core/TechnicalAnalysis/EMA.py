import ta
class EMA:
    

    def __init__(self, short_window=20, long_window=50):
        """
        Initialize MovingAverageCrossOver with default or custom MA periods.
        """
        self.short_window = short_window
        self.long_window = long_window
        self.previous_crossover = None  # Store previous crossover info
    
    def add(self,df):
        data = df.copy()
        ema_short = ta.trend.ema_indicator(data['close'], window=self.short_window)
        ema_long = ta.trend.ema_indicator(data['close'], window=self.long_window)
        data['ema_short'] = ema_short
        data['ema_long'] = ema_long
        return data


    def detectCrossOver(self, data):
        """
        Detect crossover signals from a DataFrame containing OHLC data.

        Parameters:
            data (pd.DataFrame): Must contain a 'close' column.
        
        Returns:
            str: 'golden_cross', 'death_cross', or None
        """
        short_ema = data['ema_short']
        long_ema = data['ema_long']

        # Check latest and previous crossover state
        if short_ema.iloc[-2] < long_ema.iloc[-2] and short_ema.iloc[-1] > long_ema.iloc[-1]:
            self.updatePreviousCrossOver('golden_cross')
            return 'golden_cross'

        elif short_ema.iloc[-2] > long_ema.iloc[-2] and short_ema.iloc[-1] < long_ema.iloc[-1]:
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
