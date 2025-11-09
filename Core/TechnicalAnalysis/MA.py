import ta
class MovingAverage:
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
    
    def add(self,df):
        data = df.copy()
        ma_short = ta.trend.ma_indicator(data['close'], window=self.short_window)
        ma_long = ta.trend.ma_indicator(data['close'], window=self.long_window)
        data['ma_short'] = ma_short
        data['ma_long'] = ma_long
        return data


    def detectCrossOver(self, data):
        """
        Detect all crossover points between short and long moving averages.

        Parameters:
            data (pd.DataFrame): Must contain columns 'close', 'ma_short', 'ma_long', and 'timestamp'.

        Returns:
            list[dict]: Each dict contains:
                {
                    'timestamp': ...,
                    'type': 'golden_cross' or 'death_cross',
                    'short_ma': ...,
                    'long_ma': ...
                }
        """
        short_ma = data['ma_short']
        long_ma = data['ma_long']
        timestamps = data['timestamp']

        crossovers = []

        for i in range(1, len(data)):
            prev_short, prev_long = short_ma.iloc[i-1], long_ma.iloc[i-1]
            curr_short, curr_long = short_ma.iloc[i], long_ma.iloc[i]

            # Golden cross
            if prev_short < prev_long and curr_short > curr_long:
                crossovers.append({
                    'timestamp': timestamps.iloc[i],
                    'type': 'golden_cross',
                    'short_ma': curr_short,
                    'long_ma': curr_long
                })

            # Death cross
            elif prev_short > prev_long and curr_short < curr_long:
                crossovers.append({
                    'timestamp': timestamps.iloc[i],
                    'type': 'death_cross',
                    'short_ma': curr_short,
                    'long_ma': curr_long
                })

        return crossovers


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
