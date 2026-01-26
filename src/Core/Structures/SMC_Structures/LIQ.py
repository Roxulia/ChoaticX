from Exceptions.ServiceExceptions import errorHandling
from .BaseZone import BaseZone
from .Swings import Swings
from tqdm import tqdm
import numpy as np
import pandas as pd
from Utility.MemoryUsage import MemoryUsage as mu
from ..registry import register_structure, register_zone
from Core.Features.meta_registry import register_feature_meta

@register_zone  
@register_feature_meta
class LIQ(BaseZone):

    META = {
        'name': 'LIQ',
        'short_name': 'LIQ',
        'is_zone': True,
        'description': 'Detects liquidity zones in price data.',
        'parameters': {
            'range_pct': {
                'type': 'float',
                'default': 0.01,
                "description": "The percentage range for liquidity zone detection."
            },
            'window': {
                'type': 'int',
                'default': 10,
                "description": "The window size for swing detection."
            }
        },
        "provides": {
            "liquidity_zones": "list"
        },
        "requires": {"swings": "list"}
    }

    def __init__(self, df = [],range_pct=0.01,window=10):
        super().__init__(df)
        self.range_pct = range_pct
        self.swingDetector = Swings(df, window)

    @mu.log_memory
    @errorHandling
    def detect(self,  inner_func=False):
        swings = self.swingDetector.detect()
        liquidity_zones = []

        highs = [s for s in swings if s['Type'] == 'Swing High']
        lows = [s for s in swings if s['Type'] == 'Swing Low']
        pip_range = (self.highs.max() - self.lows.min()) * self.range_pct

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
                    
                    'timestamp': group[0]['timestamp'],
                    **ta_means
                })
            return result

        buy_side = process_zone(lows, 'Buy-Side')
        sell_side = process_zone(highs, 'Sell-Side')
        self.liquidity_zones = buy_side + sell_side
        return self.liquidity_zones