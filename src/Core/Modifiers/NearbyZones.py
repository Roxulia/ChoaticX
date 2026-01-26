import pandas as pd
import numpy as np
from tqdm import tqdm
import asyncio
from Utility.MemoryUsage import MemoryUsage as mu
from Features.Generators.BaseDataGenerator import BaseDataGenerator


class NearbyZones():
    def __init__(self,threshold = 300):
        self.threshold = threshold
    
    @mu.log_memory
    def getNearbyZone(self,inner_func = False):
        results = []
        bdg = BaseDataGenerator()
        self.based_zones = asyncio.run(bdg.getZonesByInterval(None))
        self.candles = asyncio.run(bdg.getRawCandleData())

        for i, zone in tqdm(enumerate(self.based_zones),desc="Adding Nearby Zones",dynamic_ncols=True,disable=inner_func):
            this_high = zone.get('zone_high')
            this_low = zone.get('zone_low')
            valid_zones = zone.get('available_core',[])+zone.get('available_liquidity',[])
            base_data = {k:v for k,v in zone.items() if k not in ['available_core','available_liquidity']}
            zone_id = zone.get('timestamp')
            def compute_nearest(valid_zones):
                
                min_dist_below = float('inf')
                nearest_above_zone = self.getATHzone(zone_id)
                min_dist_above = nearest_above_zone['zone_low'] - this_high
                nearest_below_zone = None

                for other in valid_zones:
                    
                    other_high = other.get('zone_high')
                    other_low = other.get('zone_low')
                    if other_low > this_high:
                        dist = other_low - this_high
                        if dist < min_dist_above and dist >= self.threshold:
                            min_dist_above = dist
                            nearest_above_zone = other.copy()
                    elif other_high < this_low:
                        dist = this_low - other_high
                        if dist < min_dist_below and dist>=self.threshold:
                            min_dist_below = dist
                            nearest_below_zone = other.copy()

                return min_dist_above, nearest_above_zone, min_dist_below, nearest_below_zone
            if valid_zones == []:
                
                base_data['distance_to_nearest_zone_above'] = None
                base_data['distance_to_nearest_zone_below'] = None

                results.append(base_data)
            else:

                # Handle liquidity zones with multiple touches
                min_above, above_zone, min_below, below_zone = compute_nearest(valid_zones)
                temp_above,temp_below = {},{}
                base_data['distance_to_nearest_zone_above'] = min_above
                if above_zone is not None:
                    temp_above = {f'above_{k}':v for k,v in above_zone.items() if k not in ['available_core','available_liquidity']}
                base_data['distance_to_nearest_zone_below'] = min_below
                if below_zone is not None:
                    temp_below = {f'below_{k}':v for k,v in below_zone.items() if k not in ['available_core','available_liquidity']}

                results.append({**base_data,**temp_above,**temp_below})

        return results
    
    def getATHzone(self,zone_id):
        data = self.candles.loc[self.candles['timestamp'] <= zone_id]
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
            'symbol' : self.symbol,
            'zone_high': float(ATH_zone['high']),
            'zone_low': float(ATH_zone['low']),
            'trades' : float(ATH_zone['number_of_trades']),
            'volume_on_creation': float(ATH_zone['volume']),
            'avg_volume_past_5': float(avg_volume_past_5[index]),
            'prev_volatility_5': float(prev_volatility_5[index]),
            'momentum_5': float(momentum_5.iloc[index]),
            'zone_type': 'ATH',
            'index': index,
            'timestamp' : ATH_zone['timestamp'],
            **ATH_zone,
        }

        return ath
    
    def getAboveBelowZones(self,zone,zones,ATH):
        this_high = zone.get('zone_high',None)
        this_low = zone.get('zone_low',None)
        min_dist_below = float('inf')
        nearest_above_zone = ATH
        min_dist_above =  nearest_above_zone['zone_low'] - this_high
        nearest_below_zone = None

        for other in zones:
            if other['timestamp'] == zone['timestamp']:
                continue
            
            other_high = other.get('zone_high')
            other_low = other.get('zone_low')
            if other_low > this_high:
                dist = other_low - this_high
                if dist < min_dist_above and dist >= self.threshold:
                    min_dist_above = dist
                    nearest_above_zone = other.copy()
            elif other_high < this_low:
                dist = this_low - other_high
                if dist < min_dist_below and dist>=self.threshold:
                    min_dist_below = dist
                    nearest_below_zone = other.copy()
        temp_above,temp_below = {},{}
        base_data = zone.copy()
        base_data['distance_to_nearest_zone_above'] = min_dist_above
        if nearest_above_zone is not None:
            temp_above = {f'above_{k}':v for k,v in nearest_above_zone.items() if k not in ['available_core','available_liquidity']}
        base_data['distance_to_nearest_zone_below'] = min_dist_below
        if nearest_below_zone is not None:
            temp_below = {f'below_{k}':v for k,v in nearest_below_zone.items() if k not in ['available_core','available_liquidity']}

        return {**base_data,**temp_above,**temp_below}




    