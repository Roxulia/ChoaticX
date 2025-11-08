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
        Detect all crossover points between short and long ema.

        Parameters:
            data (pd.DataFrame): Must contain columns 'close', 'ema_short', 'ema_long', and 'timestamp'.

        Returns:
            list[dict]: Each dict contains:
                {
                    'timestamp': ...,
                    'type': 'golden_cross' or 'death_cross',
                    'short_ema': ...,
                    'long_ema': ...
                }
        """
        short_ema = data['ema_short']
        long_ema = data['ema_long']
        timestamps = data['timestamp']

        crossovers = []

        for i in range(1, len(data)):
            prev_short, prev_long = short_ema.iloc[i-1], long_ema.iloc[i-1]
            curr_short, curr_long = short_ema.iloc[i], long_ema.iloc[i]

            # Golden cross
            if prev_short < prev_long and curr_short > curr_long:
                crossovers.append({
                    'timestamp': timestamps.iloc[i],
                    'type': 'golden_cross',
                    'short_ema': curr_short,
                    'long_ema': curr_long
                })

            # Death cross
            elif prev_short > prev_long and curr_short < curr_long:
                crossovers.append({
                    'timestamp': timestamps.iloc[i],
                    'type': 'death_cross',
                    'short_ema': curr_short,
                    'long_ema': curr_long
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
