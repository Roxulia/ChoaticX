from tqdm import tqdm
class ZoneReactor:
    def __init__(self, candles):
        self.candles = candles

    def get_zone_reaction(self,zone):
        candles = self.candles[['high', 'low', 'open', 'close']].to_numpy()
        num_candles = len(candles)
        zone_high = zone['zone_high']
        zone_low = zone['zone_low']
        end_idx = zone['index']

        touch_type = None
        touch_index = None
        touch_candle = None

        # Skip zones that go beyond candles
        if end_idx >= num_candles - 1:
            return zone
        i = end_idx+1
        while i < num_candles:
            high, low, open_, close = candles[i]

            if (open_ > zone_high and low < zone_high) or (open_ < zone_low and high > zone_low):
                touch_index = i
                touch_candle = self.candles.iloc[i]  # Only access DataFrame here if touched

                if zone_low <= close <= zone_high:
                    touch_type = 'body_close_inside'
                elif (open_ > zone_high and close < zone_low) or (open_ < zone_low and close > zone_high):
                    touch_type = 'engulf'
                elif close > zone_high and open_ > zone_high:
                    touch_type = 'body_close_above'
                elif close < zone_low and open_ < zone_low:
                    touch_type = 'body_close_below'
                else:
                    touch_type = 'wick_touch'
                break
            i+=1

        zone_copy = zone.copy()
        zone_copy['touch_type'] = touch_type
        zone_copy['touch_index'] = touch_index
        zone_copy['touch_candle'] = touch_candle
        return zone_copy
    
    def get_zones_reaction(self,zones):
        results = []
        candles = self.candles[['high', 'low', 'open', 'close']].to_numpy()
        num_candles = len(candles)

        for zone in tqdm(zones, desc="Getting Zone Reactions"):
            zone_high = zone['zone_high']
            zone_low = zone['zone_low']
            end_idx = zone['index']

            touch_type = None
            touch_index = None
            touch_candle = None

            # Skip zones that go beyond candles
            if end_idx >= num_candles - 1:
                results.append(zone)
                continue
            i = end_idx+1
            while i < num_candles:
                high, low, open_, close = candles[i]

                if (open_ > zone_high and low < zone_high) or (open_ < zone_low and high > zone_low):
                    touch_index = i
                    touch_candle = self.candles.iloc[i]  # Only access DataFrame here if touched

                    if zone_low <= close <= zone_high:
                        touch_type = 'body_close_inside'
                    elif (open_ > zone_high and close < zone_low) or (open_ < zone_low and close > zone_high):
                        touch_type = 'engulf'
                    elif close > zone_high and open_ > zone_high:
                        touch_type = 'body_close_above'
                    elif close < zone_low and open_ < zone_low:
                        touch_type = 'body_close_below'
                    else:
                        touch_type = 'wick_touch'
                    break
                i+=1

            zone_copy = zone.copy()
            zone_copy['touch_type'] = touch_type
            zone_copy['touch_index'] = touch_index
            zone_copy['touch_candle'] = touch_candle
            results.append(zone_copy)

        return results

    def get_next_target_zone(self, zones):
        """
        For each zone, identify the next target zone (price moves into it after touch).
        Optimized for speed.
        """
        zone_targets = []
        candles = self.candles  # avoid attribute access in loop
        candle_len = len(candles)

        for zone in tqdm(zones, desc='Adding Target zones'):
            touch_index = zone.get('touch_index')
            available_zones = zone.get('available_core', []) + zone.get('available_liquidity', [])

            target_zone = None
            if touch_index is not None and 0 <= touch_index < candle_len - 1:
                future_candles = candles.iloc[touch_index + 1:]

                for next_zone in available_zones:
                    if next_zone == zone:
                        continue

                    next_high = next_zone['zone_high']
                    next_low = next_zone['zone_low']

                    # Vectorized mask for better performance
                    condition = (
                        ((future_candles['open'] > next_high) & (future_candles['close'] < next_high)) |
                        ((future_candles['open'] < next_low) & (future_candles['close'] > next_low)) |
                        ((future_candles['high'] < next_high) & (future_candles['low'] > next_low))
                    )

                    if condition.any():
                        target_zone = next_zone
                        break  # found the first valid target

            # No deep copy, just build dict as needed
            zone_targets.append({**zone, 'target_zone': target_zone})

        return zone_targets


    
    def get_last_candle_reaction(self,zones):
        candle = self.candles.iloc[-1]
        high, low, close, open_ = candle['high'], candle['low'], candle['close'], candle['open']
        for zone in zones:
            zone_high = zone['zone_high']
            zone_low = zone['zone_low']
            if zone_low <= close <= zone_high:
                return 'body_close_inside',zone['index']
            elif (open_ > zone_high and close < zone_low) or (open_ < zone_low and close > zone_high):
                return 'engulf',zone['index']
            elif close > zone_high and open_ > zone_high:
                return 'body_close_above',zone['index']
            elif close < zone_low and open_ < zone_low:
                return 'body_close_below',zone['index']
            else:
                return 'wick_touch',zone['index']
        return 'None'
