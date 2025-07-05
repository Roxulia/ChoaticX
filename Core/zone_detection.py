import numpy as np
class ZoneDetector:
    def __init__(self, df, timeframe="1h"):
        self.df = df
        self.timeframe = timeframe

    def detect_fvg(self,threshold = 300):
        """
        Detect Fair Value Gaps (FVGs)
        """

        fvg_indices = []

        highs = self.df['high'].values
        lows = self.df['low'].values
        opens = self.df['open'].values
        closes = self.df['close'].values
        volumes = self.df['volume'].values
        ema20 = self.df['ema20'].values
        ema50 = self.df['ema50'].values
        atr = self.df['atr'].values
        rsi = self.df['rsi'].values
        atr_mean = self.df['atr_mean'].values

        length = len(self.df)

        close_rolling = self.df['close'].rolling(window=5)
        volume_rolling = self.df['volume'].rolling(window=5)

        avg_volume_past_5 = volume_rolling.mean().values
        prev_volatility_5 = close_rolling.std().values
        momentum_5 = closes - np.roll(closes, 5)

        for i in range(5, length - 1):
            prev_high = highs[i - 1]
            prev_low = lows[i - 1]
            next_high = highs[i + 1]
            next_low = lows[i + 1]

            body = abs(opens[i] - closes[i])
            candle_range = highs[i] - lows[i]
            body_ratio = body / candle_range if candle_range != 0 else 0
            wick_ratio = 1 - body_ratio
            body_size = body
            volume_on_creation = volumes[i]

            if next_low > prev_high:
                gap = next_low - prev_high
                if gap >= threshold:
                    # Touch index search — can be optimized further with precomputed conditions if needed
                    touch_indx = next(
                        (j for j in range(i + 2, length) if opens[j] > next_low and lows[j] < next_low), None
                    )
                    fvg_indices.append({
                        'index': i,
                        'type': 'Bullish FVG',
                        'ema 20': ema20[i],
                        'ema 50': ema50[i],
                        'atr': atr[i],
                        'rsi': rsi[i],
                        'atr_mean': atr_mean[i],
                        'zone_high': next_low,
                        'zone_low': prev_high,
                        'zone_width': gap,
                        'body_size': body_size,
                        'wick_ratio': wick_ratio,
                        'volume_on_creation': volume_on_creation,
                        'avg_volume_past_5': avg_volume_past_5[i],
                        'prev_volatility_5': prev_volatility_5[i],
                        'momentum_5': momentum_5[i],
                        'touch_index': touch_indx,
                        'time_frame': self.timeframe,
                    })

            elif next_high < prev_low:
                gap = prev_low - next_high
                if gap >= threshold:
                    touch_indx = next(
                        (j for j in range(i + 2, length) if opens[j] < next_high and highs[j] > next_high), None
                    )
                    fvg_indices.append({
                        'index': i,
                        'type': 'Bearish FVG',
                        'ema 20': ema20[i],
                        'ema 50': ema50[i],
                        'atr': atr[i],
                        'rsi': rsi[i],
                        'atr_mean': atr_mean[i],
                        'zone_high': prev_low,
                        'zone_low': next_high,
                        'zone_width': gap,
                        'body_size': body_size,
                        'wick_ratio': wick_ratio,
                        'volume_on_creation': volume_on_creation,
                        'avg_volume_past_5': avg_volume_past_5[i],
                        'prev_volatility_5': prev_volatility_5[i],
                        'momentum_5': momentum_5[i],
                        'touch_index': touch_indx,
                        'time_frame': self.timeframe,
                    })

        return fvg_indices
    
    def detect_order_blocks(self, min_body_ratio=0.3):
        """
        Optimized detection of bullish and bearish Order Blocks (OB).
        """
        ob_list = []

        highs = self.df['high'].values
        lows = self.df['low'].values
        opens =self.df['open'].values
        closes = self.df['close'].values
        volumes = self.df['volume'].values
        ema20 = self.df['ema20'].values
        ema50 = self.df['ema50'].values
        atr = self.df['atr'].values
        rsi = self.df['rsi'].values
        atr_mean = self.df['atr_mean'].values

        for i in range(5, len(self.df) - 2):
            open_, close_ = opens[i], closes[i]
            high_, low_ = highs[i], lows[i]
            prev_close = closes[i - 1]
            next_close = closes[i + 1]
            next2_close = closes[i + 2]

            body = abs(open_ - close_)
            candle_range = high_ - low_
            if candle_range == 0:
                continue

            body_ratio = body / candle_range
            if body_ratio < min_body_ratio:
                continue

            wick_ratio = 1 - body_ratio
            zone_high, zone_low = high_, low_
            zone_width = zone_high - zone_low
            body_size = body
            volume_on_creation = volumes[i]

            avg_volume_past_5 = volumes[i-5:i].mean()
            prev_volatility_5 = closes[i-5:i].std()
            momentum_5 = close_ - closes[i - 5]

            # --- Bullish OB Detection ---
            if close_ < open_:
                if (prev_close > low_ and
                    next_close > high_ and
                    next2_close > closes[i + 1]):

                    # Delay touch check until required
                    touch_indx = next(
                        (j for j in range(i + 3, len(self.df))
                        if opens[j] > zone_high and lows[j] < zone_high),
                        None
                    )

                    ob_list.append({
                        'index': i,
                        'type': 'Bullish OB',
                        'ema 20': ema20[i],
                        'ema 50': ema50[i],
                        'atr': atr[i],
                        'rsi': rsi[i],
                        'atr_mean': atr_mean[i],
                        'zone_high': zone_high,
                        'zone_low': zone_low,
                        'zone_width': zone_width,
                        'body_size': body_size,
                        'wick_ratio': wick_ratio,
                        'volume_on_creation': volume_on_creation,
                        'avg_volume_past_5': avg_volume_past_5,
                        'prev_volatility_5': prev_volatility_5,
                        'momentum_5': momentum_5,
                        'touch_index': touch_indx,
                        'time_frame': self.timeframe,
                    })

            # --- Bearish OB Detection ---
            elif close_ > open_:
                if (prev_close < high_ and
                    next_close < low_ and
                    next2_close < closes[i + 1]):

                    touch_indx = next(
                        (j for j in range(i + 3, len(self.df))
                        if opens[j] < zone_low and highs[j] > zone_low),
                        None
                    )

                    ob_list.append({
                        'index': i,
                        'type': 'Bearish OB',
                        'ema 20': ema20[i],
                        'ema 50': ema50[i],
                        'atr': atr[i],
                        'rsi': rsi[i],
                        'atr_mean': atr_mean[i],
                        'zone_high': zone_high,
                        'zone_low': zone_low,
                        'zone_width': zone_width,
                        'body_size': body_size,
                        'wick_ratio': wick_ratio,
                        'volume_on_creation': volume_on_creation,
                        'avg_volume_past_5': avg_volume_past_5,
                        'prev_volatility_5': prev_volatility_5,
                        'momentum_5': momentum_5,
                        'touch_index': touch_indx,
                        'time_frame': self.timeframe,
                    })

        return ob_list
