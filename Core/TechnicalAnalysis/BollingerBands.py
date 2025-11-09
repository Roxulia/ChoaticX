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
    
    def detectCrossOver(self, data):
        """
        Detect all Bollinger Band crossover points.

        Parameters:
            data (pd.DataFrame): Must contain columns:
                'close', 'bb_high', 'bb_mid', 'bb_low', and 'timestamp'

        Returns:
            list[dict]: Each dict contains:
                {
                    'timestamp': ...,
                    'type': 'upper_breakout' | 'lower_breakout' | 'upper_rejection' | 'lower_rejection' | 'mid_cross_up' | 'mid_cross_down',
                    'close': ...,
                    'bb_high': ...,
                    'bb_mid': ...,
                    'bb_low': ...
                }
        """
        close = data['close']
        high = data['bb_high']
        mid = data['bb_mid']
        low = data['bb_low']
        timestamps = data['timestamp']

        crossovers = []

        for i in range(1, len(data)):
            prev_close = close.iloc[i-1]
            curr_close = close.iloc[i]
            prev_high, curr_high = high.iloc[i-1], high.iloc[i]
            prev_low, curr_low = low.iloc[i-1], low.iloc[i]
            prev_mid, curr_mid = mid.iloc[i-1], mid.iloc[i]

            # === Upper Band Cross ===
            if prev_close <= prev_high and curr_close > curr_high:
                crossovers.append({
                    'timestamp': timestamps.iloc[i],
                    'type': 'upper_breakout',
                    'close': curr_close,
                    'bb_high': curr_high,
                    'bb_mid': curr_mid,
                    'bb_low': curr_low
                })

            elif prev_close >= prev_high and curr_close < curr_high:
                crossovers.append({
                    'timestamp': timestamps.iloc[i],
                    'type': 'upper_rejection',
                    'close': curr_close,
                    'bb_high': curr_high,
                    'bb_mid': curr_mid,
                    'bb_low': curr_low
                })

            # === Lower Band Cross ===
            elif prev_close >= prev_low and curr_close < curr_low:
                crossovers.append({
                    'timestamp': timestamps.iloc[i],
                    'type': 'lower_breakout',
                    'close': curr_close,
                    'bb_high': curr_high,
                    'bb_mid': curr_mid,
                    'bb_low': curr_low
                })

            elif prev_close <= prev_low and curr_close > curr_low:
                crossovers.append({
                    'timestamp': timestamps.iloc[i],
                    'type': 'lower_rejection',
                    'close': curr_close,
                    'bb_high': curr_high,
                    'bb_mid': curr_mid,
                    'bb_low': curr_low
                })

            # === Middle Band Cross ===
            elif prev_close < prev_mid and curr_close > curr_mid:
                crossovers.append({
                    'timestamp': timestamps.iloc[i],
                    'type': 'mid_cross_up',
                    'close': curr_close,
                    'bb_high': curr_high,
                    'bb_mid': curr_mid,
                    'bb_low': curr_low
                })

            elif prev_close > prev_mid and curr_close < curr_mid:
                crossovers.append({
                    'timestamp': timestamps.iloc[i],
                    'type': 'mid_cross_down',
                    'close': curr_close,
                    'bb_high': curr_high,
                    'bb_mid': curr_mid,
                    'bb_low': curr_low
                })

        return crossovers



    
