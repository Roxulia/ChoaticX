from .BaseZone import BaseZone
from tqdm import tqdm
import numpy as np
import pandas as pd
from Utility.MemoryUsage import MemoryUsage as mu

class LIQ(BaseZone):
    @mu.log_memory
    def detect(self, swings=None, range_pct=0.01, inner_func=False):
        if swings is None:
            raise ValueError("LiquidityDetector requires swings detected first")
        self.swings = swings
        liquidity_zones = []

        highs = [s for s in swings if s['Type'] == 'Swing High']
        lows = [s for s in swings if s['Type'] == 'Swing Low']
        pip_range = (self.highs.max() - self.lows.min()) * range_pct

        def process_zone(candidates, direction):
            result = []
            used = set()
            for i, base in enumerate(candidates):
                if base['timestamp'] in used:
                    continue
                base_level = base['Price']
                range_low, range_high = base_level - pip_range, base_level + pip_range
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
                    continue
                group_df = pd.DataFrame(group)

                ta_means = group_df.select_dtypes(include='number').mean()

                avg_level = np.mean(prices)
                zone_high = avg_level + pip_range
                zone_low = avg_level - pip_range
                equal_level_deviation = np.std(prices)
                duration = end_idx - group[0]['timestamp']
                avg_volume = np.mean([self.df.loc[self.df['timestamp'] == g['timestamp'], 'volume'].iloc[0] for g in group])
                result.append({
                    'zone_type': f'{direction} Liq',
                    'level': avg_level,
                    'zone_high': zone_high,
                    'zone_low': zone_low,
                    'count': len(group),
                    'equal_level_deviation': equal_level_deviation,
                    'avg_volume_around_zone': avg_volume,
                    'duration_between_first_last_touch': duration / np.timedelta64(1, 's'),
                    'time_frame': self.timeframe,
                    'timestamp': group[0]['timestamp'],
                    **ta_means
                })
            return result

        buy_side = process_zone(lows, 'Buy-Side')
        sell_side = process_zone(highs, 'Sell-Side')
        liquidity_zones = buy_side + sell_side
        return liquidity_zones