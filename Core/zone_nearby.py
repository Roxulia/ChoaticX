import pandas as pd
import numpy as np
from tqdm import tqdm
class NearbyZones():
    def __init__(self,based_zones,threshold = 0.002):
        self.based_zones = based_zones
        self.threshold = threshold
    
    def getNearbyZone(self):
        results = []

        for i, zone in tqdm(enumerate(self.based_zones),desc="Adding Nearby Zones"):
            this_high = zone.get('zone_high')
            this_low = zone.get('zone_low')
            valid_zones = zone.get('available_core',[])+zone.get('available_liquidity',[])

            def compute_nearest(valid_zones):
                min_dist_above = float('inf')
                min_dist_below = float('inf')
                nearest_above_zone = None
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

    