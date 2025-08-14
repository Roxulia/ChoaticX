import pandas as pd
import numpy as np
from tqdm import tqdm
class NearbyZones():
    def __init__(self,based_zones,candles,threshold = 0.002):
        self.based_zones = based_zones
        self.threshold = threshold
        self.candles = candles
    
    def getNearbyZone(self):
        results = []

        for i, zone in tqdm(enumerate(self.based_zones),desc="Adding Nearby Zones",dynamic_ncols=True):
            this_high = zone.get('zone_high')
            this_low = zone.get('zone_low')
            valid_zones = zone.get('available_core',[])+zone.get('available_liquidity',[])
            zone_id = zone.get('index')
            def compute_nearest(valid_zones):
                
                min_dist_below = float('inf')
                nearest_above_zone = self.getATHzone(zone_id)
                min_dist_above = this_high - nearest_above_zone['zone_low']
                nearest_below_zone = None

                for other in valid_zones:
                    
                    other_high = other.get('zone_high')
                    other_low = other.get('zone_low')
                    price_diff = other_high * self.threshold
                    if other_low > this_high:
                        dist = other_low - this_high
                        if dist < min_dist_above and dist >= price_diff:
                            min_dist_above = dist
                            nearest_above_zone = other.copy()
                    elif other_high < this_low:
                        dist = this_low - other_high
                        if dist < min_dist_below and dist>=price_diff:
                            min_dist_below = dist
                            nearest_below_zone = other.copy()

                return min_dist_above, nearest_above_zone, min_dist_below, nearest_below_zone

            # Handle liquidity zones with multiple touches
            min_above, above_zone, min_below, below_zone = compute_nearest(valid_zones)

            updated = zone.copy()
            updated['distance_to_nearest_zone_above'] = min_above
            updated['nearest_zone_above'] = above_zone
            updated['distance_to_nearest_zone_below'] = min_below
            updated['nearest_zone_below'] = below_zone

            results.append(updated)

        return results
    
    def getATHzone(self,zone_id):
        data = self.candles.iloc[:zone_id]
        # Find ATH index (timestamp) and integer position
        ath_idx = data['high'].idxmax()
        index = data.index.get_loc(ath_idx)  # integer position
        ATH_zone = data.iloc[index]

        # Rolling stats
        close_rolling = data['close'].rolling(window=5)
        volume_rolling = data['volume'].rolling(window=5)

        avg_volume_past_5 = volume_rolling.mean().values
        prev_volatility_5 = close_rolling.std().values
        momentum_5 = data['close'] - data['close'].shift(5)

        # Build ATH zone dict
        ath = {
            'zone_high': ATH_zone['high'],
            'zone_low': ATH_zone['low'],
            'ema 20': ATH_zone['ema20'],
            'ema 50': ATH_zone['ema50'],
            'rsi': ATH_zone['rsi'],
            'atr': ATH_zone['atr'],
            'volume_on_creation': ATH_zone['volume'],
            'avg_volume_past_5': avg_volume_past_5[index],
            'prev_volatility_5': prev_volatility_5[index],
            'momentum_5': momentum_5.iloc[index],
            'type': 'ATH',
            'index': index,
        }

        return ath




    