from tqdm import tqdm
class ZoneReactor:
    def __init__(self):
        pass

    def get_zone_reaction(self,zone,candles_data):
        candles = candles_data[['high', 'low', 'open', 'close']].to_numpy()
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
                touch_candle = candles_data.iloc[i]  # Only access DataFrame here if touched

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
    
    def get_zones_reaction(self,zones,candles_data):
        results = []
        candles = candles_data[['high', 'low', 'open', 'close']].to_numpy()
        num_candles = len(candles)

        for zone in tqdm(zones, desc="Getting Zone Reactions"):
            zone_high = zone['zone_high']
            zone_low = zone['zone_low']
            end_idx = zone['index']
            zone_type = zone['type']
            if zone_type  in ['Buy-Side Liq','Sell-Side Liq']:
                touch_index = zone.get('swept_index',None)
                if touch_index is not None:
                    touch_candle = candles_data.iloc[touch_index]
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
                    zone_copy = zone.copy()
                    zone_copy['touch_type'] = touch_type
                    zone_copy['touch_index'] = touch_index
                    zone_copy['touch_candle'] = touch_candle
                    results.append(zone_copy)
                    continue
                else:
                    zone_copy = zone.copy()
                    zone_copy['touch_type'] = None
                    zone_copy['touch_index'] = None
                    zone_copy['touch_candle'] = None
                    results.append(zone_copy)
                    continue
            else:
                touch_type = None
                touch_index = None
                touch_candle = None

                # Skip zones that go beyond candles
                if end_idx >= num_candles - 1:
                    results.append(zone)
                    continue
                i = end_idx+2
                while i < num_candles:
                    high, low, open_, close = candles[i]

                    if (open_ > zone_high and low < zone_high) or (open_ < zone_low and high > zone_low):
                        touch_index = i
                        touch_candle = candles_data.iloc[i]  # Only access DataFrame here if touched

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

    def get_next_target_zone(self, zones,candles_data):
        """
        For each zone, identify the next target zone (price moves into it after touch).
        Optimized for speed.
        """
        zone_targets = []
        candles = candles_data  # avoid attribute access in loop
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

    def getTargetFromTwoZones(self, zones, candles_data):
        zone_targets = []
        candles = candles_data
        candle_len = len(candles)

        for zone in tqdm(zones, desc='Adding Target zones'):
            touch_index = zone.get('touch_index')
            above_zone = zone.get('nearest_zone_above', None)
            below_zone = zone.get('nearest_zone_below', None)

            if above_zone is None or below_zone is None:
                zone_targets.append({**zone, 'target': None})
                continue

            if touch_index is not None and 0 <= touch_index < candle_len - 1:
                future_candles = candles.iloc[touch_index + 1:]

                # Above zone conditions
                next_high1 = above_zone['zone_high']
                next_low1 = above_zone['zone_low']
                cond1 = (
                    ((future_candles['open'] > next_high1) & (future_candles['close'] < next_high1)) |
                    ((future_candles['open'] < next_low1) & (future_candles['close'] > next_low1)) |
                    ((future_candles['high'] < next_high1) & (future_candles['low'] > next_low1))
                )

                # Below zone conditions
                next_high2 = below_zone['zone_high']
                next_low2 = below_zone['zone_low']
                cond2 = (
                    ((future_candles['open'] > next_high2) & (future_candles['close'] < next_high2)) |
                    ((future_candles['open'] < next_low2) & (future_candles['close'] > next_low2)) |
                    ((future_candles['high'] < next_high2) & (future_candles['low'] > next_low2))
                )

                # Find the first True index for each condition
                first_above = cond1.idxmax() if cond1.any() else None
                first_below = cond2.idxmax() if cond2.any() else None

                # Pick whichever happened first
                if first_above is not None and (first_below is None or first_above < first_below):
                    target_zone = 1
                elif first_below is not None and (first_above is None or first_below < first_above):
                    target_zone = 0
                else:
                    target_zone = None  # No target

                zone_targets.append({**zone, 'target': target_zone})

        return zone_targets

    
    def get_last_candle_reaction(self,zones,candle):
        high, low, close, open_ = candle['high'], candle['low'], candle['close'], candle['open']
        for zone in zones:
            zone_high = zone['zone_high']
            zone_low = zone['zone_low']
            if (zone_low > open_ and zone_low <= high) or (zone_high < open_ and zone_high >= low):
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
        return 'None','None'
