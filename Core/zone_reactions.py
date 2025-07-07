class ZoneReactor:
    def __init__(self, candles, zones):
        self.candles = candles
        self.zones = zones

    def analyze_reactions(self):
        """
        Analyze how price reacts to each merged zone.

        Returns:
            List of zone dictionaries with added reaction metadata.
        """
        zone_reactions = []

        for zone in self.zones:
            zone_high = zone['zone_high']
            zone_low = zone['zone_low']
            start_index = min(src['index'] for src in zone['sources'])

            touches = 0
            bounces = 0
            penetrations = 0
            invalidations = 0
            first_touch_index = None

            for i in range(start_index + 1, len(self.candles)):
                row = self.candles.iloc[i]
                high, low, close, open_ = row['high'], row['low'], row['close'], row['open']

                if low <= zone_high and high >= zone_low:
                    if first_touch_index is None:
                        first_touch_index = i

                    touches += 1

                    if zone_low <= close <= zone_high:
                        penetrations += 1
                    elif (close < zone_low and open_ > zone_high) or (close > zone_high and open_ < zone_low):
                        invalidations += 1
                    else:
                        bounces += 1

            zone_copy = zone.copy()
            zone_copy.update({
                'reaction_meta': {
                    'touches': touches,
                    'first_touch_index': first_touch_index,
                    'bounces': bounces,
                    'penetrations': penetrations,
                    'invalidations': invalidations
                }
            })
            zone_reactions.append(zone_copy)

        return zone_reactions
