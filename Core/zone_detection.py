import numpy as np
from tqdm import tqdm
from Utility.MemoryUsage import MemoryUsage as mu
class ZoneDetector:
    def __init__(self, df, timeframe="1h"):
        self.df = df
        self.timeframe = timeframe
        self.initialize()
        self.detect_swings()

    def initialize(self):
        self.highs = self.df['high'].values
        self.lows = self.df['low'].values
        self.opens =self.df['open'].values
        self.closes = self.df['close'].values
        self.volumes = self.df['volume'].values
        self.ma_short = self.df['ma_short'].values
        self.ma_long = self.df['ma_long'].values
        self.ema_short = self.df['ema_short'].values
        self.ema_long = self.df['ema_long'].values
        self.atr = self.df['atr'].values
        self.rsi = self.df['rsi'].values
        self.bb_high = self.df['bb_high'].values
        self.bb_low = self.df['bb_low'].values
        self.bb_mid = self.df['bb_mid'].values
        self.atr_mean = self.df['atr_mean'].values
        self.timestamps = self.df['timestamp'].values
        self.trades = self.df['number_of_trades'].values
        self.alphas = self.df['alpha'].values if 'alpha' in self.df else None
        self.betas = self.df['beta'].values if 'beta' in self.df else None
        self.gammas = self.df['gamma'].values if 'gamma' in self.df else None
        self.r2s = self.df['r2'].values if 'r2' in self.df else None

    @mu.log_memory
    def detect_fvg(self,threshold = 300,inner_func = False):
        """
        Detect Fair Value Gaps (FVGs)
        """

        fvg_indices = []
        length = len(self.df)

        close_rolling = self.df['close'].rolling(window=5)
        volume_rolling = self.df['volume'].rolling(window=5)

        avg_volume_past_5 = volume_rolling.mean().values
        prev_volatility_5 = close_rolling.std().values
        momentum_5 = self.closes - np.roll(self.closes, 5)

        for i in tqdm(range(5, length - 1),desc='Extracting FVG',disable=inner_func):
            prev_high = self.highs[i - 1]
            prev_low = self.lows[i - 1]
            next_high = self.highs[i + 1]
            next_low = self.lows[i + 1]

            body = abs(self.opens[i] - self.closes[i])
            candle_range = self.highs[i] - self.lows[i]
            body_ratio = body / candle_range if candle_range != 0 else 0
            wick_ratio = 1 - body_ratio
            body_size = body
            volume_on_creation = self.volumes[i]

            if next_low > prev_high:
                gap = next_low - prev_high
                if gap >= threshold:
                    # Touch index search — can be optimized further with precomputed conditions if needed
                    touch_indx = next(
                        (j for j in range(i + 2, length) if self.opens[j] > next_low and self.closes[j] < next_low), None
                    )
                    fvg_indices.append({
                        
                        'zone_type': 'Bullish FVG',
                        'trades' : self.trades[i],
                        'ma_short': self.ma_short[i],
                        'ma_long': self.ma_long[i],
                        'ema_short': self.ema_short[i],
                        'ema_long': self.ema_long[i],
                        'atr': self.atr[i],
                        'rsi': self.rsi[i],
                        'atr_mean': self.atr_mean[i],
                        'bb_high':self.bb_high[i],
                        'bb_low' : self.bb_low[i],
                        'bb_mid' : self.bb_mid[i],
                        'alpha' : self.alphas[i] if self.alphas is not None else None,
                        'beta' : self.betas[i] if self.betas is not None else None,
                        'gamma' : self.gammas[i] if self.gammas is not None else None,
                        'r2' : self.r2s[i] if self.r2s is not None else None,
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
                        'touch_time' : self.timestamps[touch_indx] if touch_indx is not None and touch_indx < len(self.timestamps) else None,
                        'time_frame': self.timeframe,
                        'timestamp' : self.timestamps[i]
                    })

            elif next_high < prev_low:
                gap = prev_low - next_high
                if gap >= threshold:
                    touch_indx = next(
                        (j for j in range(i + 2, length) if self.opens[j] < next_high and self.closes[j] > next_high), None
                    )
                    fvg_indices.append({
                        
                        'zone_type': 'Bearish FVG',
                        'trades' : self.trades[i],
                        'ma_short': self.ma_short[i],
                        'ma_long': self.ma_long[i],
                        'ema_short': self.ema_short[i],
                        'ema_long': self.ema_long[i],
                        'atr': self.atr[i],
                        'rsi': self.rsi[i],
                        'atr_mean': self.atr_mean[i],
                        'bb_high': self.bb_high[i],
                        'bb_low' : self.bb_low[i],
                        'bb_mid' : self.bb_mid[i],
                        'alpha' : self.alphas[i] if self.alphas is not None else None,
                        'beta' : self.betas[i] if self.betas is not None else None,
                        'gamma' : self.gammas[i] if self.gammas is not None else None,
                        'r2' : self.r2s[i] if self.r2s is not None else None,
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
                        'touch_time' : self.timestamps[touch_indx] if touch_indx is not None and touch_indx < len(self.timestamps) else None,
                        'time_frame': self.timeframe,
                        'timestamp' : self.timestamps[i]
                    })

        return fvg_indices
    
    @mu.log_memory
    def detect_order_blocks(self, threshold = 300,inner_func = False):
        """
        Optimized detection of bullish and bearish Order Blocks (OB).
        """
        ob_list = []

        for i in tqdm(range(5, len(self.df) - 2),desc='Extracting OBs',disable=inner_func):
            open_, close_ = self.opens[i], self.closes[i]
            high_, low_ = self.highs[i], self.lows[i]
            prev_close = self.closes[i - 1]
            next_close = self.closes[i + 1]
            next2_close = self.closes[i + 2]

            body = abs(open_ - close_)
            candle_range = high_ - low_
            if candle_range == 0:
                continue

            body_ratio = body / candle_range
            if candle_range < threshold:
                continue

            wick_ratio = 1 - body_ratio
            zone_high, zone_low = high_, low_
            zone_width = zone_high - zone_low
            body_size = body
            volume_on_creation = self.volumes[i]

            avg_volume_past_5 = self.volumes[i-5:i].mean()
            prev_volatility_5 = self.closes[i-5:i].std()
            momentum_5 = close_ - self.closes[i - 5]

            # --- Bullish OB Detection ---
            if close_ < open_:
                if (prev_close > low_ and
                    next_close > high_ and
                    next2_close > self.closes[i + 1]):

                    # Delay touch check until required
                    touch_indx = next(
                        (j for j in range(i + 3, len(self.df))
                        if self.opens[j] > zone_high and self.closes[j] < zone_high),
                        None
                    )

                    ob_list.append({
                        
                        'zone_type': 'Bullish OB',
                        'trades' : self.trades[i],
                        'ema_short': self.ema_short[i],
                        'ema_long': self.ema_long[i],
                        'ma_short' : self.ma_short[i],
                        'ma_long' : self.ma_long[i],
                        'atr': self.atr[i],
                        'rsi': self.rsi[i],
                        'atr_mean': self.atr_mean[i],
                        'bb_high':self.bb_high[i],
                        'bb_low' : self.bb_low[i],
                        'bb_mid' : self.bb_mid[i],
                        'alpha' : self.alphas[i] if self.alphas is not None else None,
                        'beta' : self.betas[i] if self.betas is not None else None,
                        'gamma' : self.gammas[i] if self.gammas is not None else None,
                        'r2' : self.r2s[i] if self.r2s is not None else None,
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
                        'touch_time' : self.timestamps[touch_indx] if touch_indx is not None and touch_indx < len(self.timestamps) else None,
                        'time_frame': self.timeframe,
                        'timestamp' : self.timestamps[i]
                    })

            # --- Bearish OB Detection ---
            elif close_ > open_:
                if (prev_close < high_ and
                    next_close < low_ and
                    next2_close < self.closes[i + 1]):

                    touch_indx = next(
                        (j for j in range(i + 3, len(self.df))
                        if self.opens[j] < zone_low and self.closes[j] > zone_low),
                        None
                    )

                    ob_list.append({
                        
                        'zone_type': 'Bearish OB',
                        'trades' : self.trades[i],
                        'ma_short' : self.ma_short[i],
                        'ma_long' : self.ma_long[i],
                        'ema_short': self.ema_short[i],
                        'ema_long': self.ema_long[i],
                        'atr': self.atr[i],
                        'rsi': self.rsi[i],
                        'atr_mean': self.atr_mean[i],
                        'bb_high':self.bb_high[i],
                        'bb_low' : self.bb_low[i],
                        'bb_mid' : self.bb_mid[i],
                        'alpha' : self.alphas[i] if self.alphas is not None else None,
                        'beta' : self.betas[i] if self.betas is not None else None,
                        'gamma' : self.gammas[i] if self.gammas is not None else None,
                        'r2' : self.r2s[i] if self.r2s is not None else None,
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
                        'touch_time' : self.timestamps[touch_indx] if touch_indx is not None and touch_indx < len(self.timestamps) else None,
                        'time_frame': self.timeframe,
                        'timestamp' : self.timestamps[i]
                    })

        return ob_list
    
    @mu.log_memory
    def detect_swings(self, window=20):
        self.swings = []

        for i in range(0, len(self.df)):

            if(i < window):
                high_window = self.highs[i:i + window + 1]
                low_window = self.lows[i:i + window + 1]
            elif(i+window >= len(self.df)):
                high_window = self.highs[i - window:]
                low_window = self.lows[i - window:]
            else:
                high_window = self.highs[i - window:i + window + 1]
                low_window = self.lows[i - window:i + window + 1]

            center_high = self.highs[i]
            center_low = self.lows[i]

            is_swing_high = center_high == high_window.max()
            is_swing_low = center_low == low_window.min()

            if is_swing_high:
                self.swings.append({'index': i, 'Type': 'Swing High', 'Price': center_high,'swing_strength':window,
                            'trades' : self.trades[i],
                            'ema_short' : self.ema_short[i],
                            'ema_long' : self.ema_long[i],
                            'ma_short' : self.ma_short[i],
                            'ma_long' : self.ma_long[i],
                            'atr' : self.atr[i],
                            'rsi' : self.rsi[i],
                            'atr_mean' : self.atr_mean[i],
                            'bb_high' : self.bb_high[i],
                            'bb_low' : self.bb_low[i],
                            'bb_mid' : self.bb_mid[i],
                            'alpha' : self.alphas[i] if 'alpha' in self.df else None,
                            'beta' : self.betas[i] if 'beta' in self.df else None,
                            'gamma' : self.gammas[i] if 'gamma' in self.df else None,
                            'r2' : self.r2s[i] if 'r2' in self.df else None,
                            'timestamp' : self.timestamps[i]
                            })
            elif is_swing_low:
                self.swings.append({'index': i, 'Type': 'Swing Low', 'Price': center_low,'swing_strength':window,
                            'trades' : self.trades[i],
                            'ema_short' : self.ema_short[i],
                            'ema_long' : self.ema_long[i],
                            'ma_short' : self.ma_short[i],
                            'ma_long' : self.ma_long[i],
                            'atr' : self.atr[i],
                            'rsi' : self.rsi[i],
                            'atr_mean' : self.atr_mean[i],
                            'bb_high' : self.bb_high[i],
                            'bb_low' : self.bb_low[i],
                            'bb_mid' : self.bb_mid[i],
                            'alpha' : self.alphas[i] if 'alpha' in self.df else None,
                            'beta' : self.betas[i] if 'beta' in self.df else None,
                            'gamma' : self.gammas[i] if 'gamma' in self.df else None,
                            'r2' : self.r2s[i] if 'r2' in self.df else None,
                            'timestamp' : self.timestamps[i]
                            })

    def label_structure_from_swings(self):
        labeled_swings = []
        last_high = None
        last_low = None
        trend = None

        for s in self.swings:
            idx = s['index']
            stype = s['Type']
            price = s['Price']
            label = None

            if stype == 'Swing High':
                label = 'HH' if last_high is None or price > last_high else 'LH'
                last_high = price
            elif stype == 'Swing Low':
                label = 'HL' if last_low is None or price > last_low else 'LL'
                last_low = price

            trend = 'Bullish' if label == 'HH' else ('Bearish' if label == 'LL' else trend)

            labeled_swings.append({
                'index': idx,
                'swing_type': stype,
                'price': price,
                'structure_label': label,
                'trend': trend
            })
        self.swings = labeled_swings

    @mu.log_memory
    def detect_liquidity_zones(self, range_pct=0.01,inner_func = False):
        """
        Detect buy-side and sell-side liquidity zones based on repeated highs/lows.

        Args:
            df (pd.DataFrame): OHLCV dataframe with 'high' and 'low' columns.
            swings (list): Output of detect_swings(), containing swing highs/lows.
            range_pct (float): Percent range to cluster equal highs/lows.

        Returns:
            List of liquidity zones with type, level, start/end index, and swept index.
        """
        n = len(self.df)
        liquidity_zones = []

        highs = [s for s in self.swings if s['Type'] == 'Swing High']
        lows = [s for s in self.swings if s['Type'] == 'Swing Low']

        pip_range = (self.highs.max() - self.lows.min()) * range_pct

        def process_zone(candidates, direction):
            result = []
            used = set()
            for i, base in tqdm(enumerate(candidates),desc = 'extracting Liquidity Zones',disable=inner_func):
                if base['timestamp'] in used:
                    continue

                base_level = base['Price']
                range_low = base_level - pip_range
                range_high = base_level + pip_range

                group = [base]
                prices = [base['Price']]
                end_idx = base['timestamp']

                for other in candidates[i+1:]:
                    if other['timestamp'] in used:
                        continue
                    if range_low <= other['Price'] <= range_high:
                        group.append(other)
                        used.add(other['timestamp'])
                        prices.append(other['Price'])
                        end_idx = other['timestamp']

                if len(group) < 2:
                    continue  # not enough for liquidity

                avg_level = sum(prices) / len(prices)
                zone_high = avg_level + pip_range
                zone_low = avg_level - pip_range
                equal_level_deviation = np.std(prices)
                duration = end_idx - group[0]['timestamp']

                # Average volume around touches
                volumes = [self.df.loc[self.df['timestamp'] == g['timestamp'], 'volume'].iloc[0] for g in group]

                avg_volume = np.mean(volumes) if volumes else None
                trades = [g['trades'] for g in group if 'trades' in g]
                ma_shorts = [g['ma_short'] for g in group if 'ma_short' in g]
                ma_longs = [g['ma_long'] for g in group if 'ma_long' in g]
                ema_shorts = [g['ema_short'] for g in group if 'ema_short' in g]
                ema_longs = [g['ema_long'] for g in group if 'ema_long' in g]
                rsis = [g['rsi'] for g in group if 'rsi' in g]
                atrs = [g['atr'] for g in group if 'atr' in g]
                atr_means = [g['atr_mean'] for g in group if 'atr_mean' in g]
                bb_highs = [g['bb_high'] for g in group if 'bb_high' in g]
                bb_lows = [g['bb_low'] for g in group if 'bb_low' in g]
                bb_mids = [g['bb_mid'] for g in group if 'bb_mid' in g]
                alphas = [g['alpha'] for g in group if 'alpha' in g and g['alpha'] is not None]
                betas = [g['beta'] for g in group if 'beta' in g and g['beta'] is not None]
                gammas = [g['gamma'] for g in group if 'gamma' in g and g['gamma'] is not None]
                r2s = [g['r2'] for g in group if 'r2' in g and g['r2'] is not None]
                timestamps = [g['timestamp'] for g in group if 'timestamp' in g]
                # Find sweep candle
                
                swept_index = None
                swept_time = None
                df = self.df.loc[(self.df['timestamp'] > end_idx)]
                ohlc_high = df['high'].values
                ohlc_low = df['low'].values
                if direction == 'Sell-Side':
                    cond = ohlc_high >= range_high
                else:
                    cond = ohlc_low <= range_low

                if np.any(cond):
                    swept_index =  int(np.argmax(cond))
                    swept_time = df['timestamp'].iloc[swept_index]

                result.append({
                    'zone_type': f'{direction} Liq',
                    'trades' : np.mean(trades),
                    'level': avg_level,
                    'zone_high': zone_high,
                    'zone_low': zone_low,
                    'count': len(group),
                    'swept_time': swept_time,
                    'equal_level_deviation': equal_level_deviation,
                    'avg_volume_around_zone': avg_volume,
                    'duration_between_first_last_touch': duration / np.timedelta64(1, 's'),
                    'ma_short' : np.mean(ma_shorts),
                    'ma_long' : np.mean(ma_longs),
                    'ema_short' : np.mean(ema_shorts),
                    'ema_long' : np.mean(ema_longs),
                    'rsi' : np.mean(rsis),
                    'atr' : np.mean(atrs),
                    'atr_mean' : np.mean(atr_means),
                    'bb_high': np.mean(bb_highs),
                    'bb_mid': np.mean(bb_mids),
                    'bb_low': np.mean(bb_lows),
                    'alpha': np.mean(alphas) if alphas else None,
                    'beta': np.mean(betas) if betas else None,
                    'gamma': np.mean(gammas) if gammas else None,
                    'r2': np.mean(r2s) if r2s else None,
                    'time_frame' : self.timeframe,
                    'timestamp' : timestamps[0]
                })


            return result

        buy_side = process_zone(lows, 'Buy-Side')
        sell_side = process_zone(highs, 'Sell-Side')
        #result = self.get_liq_touches(buy_side + sell_side)

        return buy_side+sell_side
    
    def get_liq_touches(self, liquidity_zones):
        lows = self.df['low'].values
        highs = self.df['high'].values
        opens = self.df['open'].values

        results = []
        for zone in liquidity_zones:
            zone_high = zone['zone_high']
            zone_low = zone['zone_low']
            start_idx = zone['index'] + 2
            end_idx = zone['end_index'] - 2

            touches = []
            for i in range(start_idx, min(end_idx, len(self.df))):
                low = lows[i]
                high = highs[i]
                open_price = opens[i]

                if (high >= zone_low and open_price < zone_low) or (open_price > zone_high and low <= zone_high):
                    touches.append(i)

            results.append({**zone, 'touch_indexs': touches})

        return results
    
    @mu.log_memory
    def get_zones(self,threshold = 300,inner_func = False):
        fvg = self.detect_fvg(threshold=threshold,inner_func=inner_func)
        ob = self.detect_order_blocks(threshold=threshold,inner_func=inner_func)
        liq = self.detect_liquidity_zones(inner_func=inner_func)
        return fvg+ob+liq



