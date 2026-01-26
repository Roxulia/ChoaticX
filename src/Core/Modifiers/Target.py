from tqdm import tqdm
import pandas as pd
from Utility.MemoryUsage import  MemoryUsage as mu
import os
from dotenv import load_dotenv
from Exceptions import *
class Target:
    def __init__(self):
        pass

    def get_next_target_zone(self, zones,candles_data):
        """
        For each zone, identify the next target zone (price moves into it after touch).
        Optimized for speed.
        """
        zone_targets = []
        candles = candles_data.copy()
        candles['timestamp'] = pd.to_datetime(candles['timestamp'])

        for zone in tqdm(zones, desc='Adding Target zones'):
            touch_candle = zone.get('touch_candle',None)
            available_zones = zone.get('available_core', []) + zone.get('available_liquidity', [])

            target_zone = None
            if touch_candle is not None:
                touch_time = pd.to_datetime(touch_candle['timestamp'])
                future_candles = candles.loc[candles['timestamp'] > touch_time]

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
        
        candles_data['timestamp'] = pd.to_datetime(candles_data['timestamp'])

        for zone in tqdm(zones, desc='Adding Target zones'):
            touch_candle = zone.get('touch_candle',None)
            above_zone = zone.get('above_timestamp', None)
            below_zone = zone.get('below_timestamp', None)

            if above_zone is None or below_zone is None:
                yield ({**zone, 'target': None})
                continue

            if touch_candle is not None:
                touch_time = pd.to_datetime(touch_candle['timestamp'])
                future_candles = candles_data.loc[candles_data['timestamp'] > touch_time ]

                # Above zone conditions
                next_high1 = zone.get('above_zone_high',None)
                next_low1 = zone.get('above_zone_low',None)
                cond1 = (
                    ((future_candles['open'] > next_high1) & (future_candles['close'] < next_high1)) |
                    ((future_candles['open'] < next_low1) & (future_candles['close'] > next_low1)) |
                    ((future_candles['high'] < next_high1) & (future_candles['low'] > next_low1))
                )

                # Below zone conditions
                next_high2 = zone.get('below_zone_high',None)
                next_low2 = zone.get('below_zone_low',None)
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

                yield({**zone, 'target': target_zone})

