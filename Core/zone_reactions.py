class ZoneReactor:
    def __init__(self, candles, zones):
        self.candles = candles
        self.zones = zones

    def get_next_target_zone(self):
        """
        For each zone, identify the next target zone (price moves into it after touch).

        Returns:
            List of zones with `target_zone` metadata.
        """
        zone_targets = []

        for zone in self.zones:
            zone_high = zone['zone_high']
            zone_low = zone['zone_low']
            end_indx = zone['end_index']
            touch_type = None
            touch_index = None
            touch_candle = None

            # Step 1: Find first touch after zone ends
            for i in range(end_indx + 1, len(self.candles)):
                candle = self.candles.iloc[i]
                high, low, open_, close = candle['high'], candle['low'], candle['open'], candle['close']

                # Price touches the zone
                if (open_ > zone_high and low < zone_high ) or (open_ < zone_low and high > zone_low ):
                    touch_index = i
                    touch_candle = candle
                    if(zone_low <= close <= zone_high):
                        touch_type = 'body_close_inside'
                    elif (open_ > zone_high and close < zone_low) or (open_ < zone_low and close > zone_high):
                        touch_type =  'engulf'
                    elif close > zone_high and open_ > zone_high:
                        touch_type = 'body_close_above'
                    elif close < zone_low and open_ < zone_low:
                        touch_type =  'body_close_below'
                    else:
                        touch_type =  'wick_touch'
                    break

            if touch_index is not None:
                # Step 2: Look for next zone that price touches
                target_zone = None
                for next_zone in self.zones:
                    if next_zone == zone:
                        continue
                    next_high = next_zone['zone_high']
                    next_low = next_zone['zone_low']

                    # Check from touch_index forward
                    for j in range(touch_index + 1, len(self.candles)):
                        next_candle = self.candles.iloc[j]
                        high, low = next_candle['high'], next_candle['low']

                        if low <= next_high and high >= next_low:
                            target_zone = {
                                'zone_low': next_low,
                                'zone_high': next_high,
                                'index': next_zone['start_index'],
                                'type': next_zone.get('type', 'Unknown')
                            }
                            break

                    if target_zone:
                        break  # Stop after finding first target zone

                zone_copy = zone.copy()
                zone_copy['touch_type'] = touch_type
                zone_copy['touch_candle'] = touch_candle
                zone_copy['target_zone'] = target_zone
                zone_targets.append(zone_copy)

            else:
                zone_copy = zone.copy()
                zone_copy['touch_type'] = touch_type
                zone_copy['touch_candle'] = touch_candle
                zone_copy['target_zone'] = None
                zone_targets.append(zone_copy)

        return zone_targets

    
    def get_last_candle_reaction(self):
        candle = self.candles.iloc[-1]
        high, low, close, open_ = candle['high'], candle['low'], candle['close'], candle['open']
        for zone in self.zones:
            zone_high = zone['zone_high']
            zone_low = zone['zone_low']
            if zone_low <= close <= zone_high:
                return 'body_close_inside'
            elif (open_ > zone_high and close < zone_low) or (open_ < zone_low and close > zone_high):
                return 'engulf'
            elif close > zone_high and open_ > zone_high:
                return 'body_close_above'
            elif close < zone_low and open_ < zone_low:
                return 'body_close_below'
            else:
                return 'wick_touch'
        return 'None'
