
import numpy as np
from Data.timeFrames import timeFrame
from .zone_reactions import ZoneReactor

class ZoneMerger:
    def __init__(self,candles, zones, threshold=0.002):
        self.zones = zones
        self.threshold = threshold
        self.reactor = ZoneReactor(candles)
        self.changeIndexNumber()
        self.seperate()

    def seperate(self):
        self.liq_zones = [z for z in self.zones if  z['type'] in ['Buy-Side Liq','Sell-Side Liq']]
        self.core_zones = [z for z in self.zones if z['type'] not in ['Buy-Side Liq','Sell-Side Liq']]
        
    
    def merge(self):
        merged = []
        core_zones = self.core_zones
        liq_zones = self.liq_zones
        threshold = self.threshold

        for i, zone in enumerate(core_zones):
            group = [zone]
            z_high = zone['zone_high'] 
            z_low = zone['zone_low'] 
            z_index = zone['index']
            matched = False

            # Filter once instead of combining inside loop
            
            available_liq = [
                z for z in liq_zones 
                if z['index'] < z_index and (z['swept_index'] is None or z['swept_index'] > z_index)
            ]
            
            available_merged = [ z for z in merged if z['touch_index'] is None or (not z['touch_index'] is None and z['touch_index'] < z_index)]
            for other in available_liq:
                other_high = other['zone_high'] 
                other_low = other['zone_low'] 

                # Check overlap using simple range logic
                if not (z_high < other_low or z_low > other_high):
                    group.append(other)
                    z_high = max(z_high, other_high)
                    z_low = min(z_low, other_low)

            # Use generator expressions for memory efficiency
            for merged_zone in available_merged:
                m_high = merged_zone['zone_high'] 
                m_low = merged_zone['zone_low'] 

                # Check for overlap
                if not (z_high < m_low or z_low > m_high):
                    # Merge zone into existing merged zone
                    merged_zone['zone_high'] = max(merged_zone['zone_high'], zone['zone_high'])
                    merged_zone['zone_low'] = min(merged_zone['zone_low'], zone['zone_low'])
                    merged_zone['zone_width'] = merged_zone['zone_high'] - merged_zone['zone_low']
                    merged_zone['types'].append(zone['type'])
                    merged_zone['timeframes'].append(zone['time_frame'])
                    merged_zone['count'] += 1
                    merged_zone['end_index'] = z_index  # optional
                    matched = True
                    break
            if not matched:  
                z = {
                    'zone_high': max(z['zone_high'] for z in group),
                    'zone_low': min(z['zone_low'] for z in group),
                    'zone_width': max(z['zone_high'] for z in group) - min(z['zone_low'] for z in group),
                    'types': [z['type'] for z in group],
                    'timeframes': [z['time_frame'] for z in group],
                    'count': len(group),
                    'zone_index' : z_index,
                    'end_index' : z_index
                }  
                z = self.reactor.get_zone_reaction(z)
                merged.append(z)

        return merged

    
    '''def add_liq_confluence(self,merged):
        for m in merged:
            confluents = []
            available_zones = [z for z in self.liq_zones if (z['swept_index'] is not None and z['swept_index'] > m['start_index'] ) or (z['swept_index'] is None) ]
            for lz in available_zones:
                if lz['zone_low'] <= m['zone_high'] and lz['zone_high'] >= m['zone_low']:
                    confluents.append({
                        'type': lz['type'],
                        'timeframe': lz['time_frame'],
                        'zone_low': lz['zone_low'],
                        'zone_high': lz['zone_high'],
                        'swept': lz.get('swept_index') is not None
                    })
            m['liquidity_confluence'] = confluents
        return merged'''
    
    def changeIndexNumber(self):
        tf = timeFrame()
        smallest_tf = tf.getSmallestTF(self.zones)
        for zone in self.zones:
            if zone['type'] in ['Buy-Side Liq','Sell-Side Liq']:
                if zone.get('index') is not None:
                    zone['index'] = zone['index'] * tf.getMultiplier(smallest_tf,zone['time_frame'])
                if zone.get('swept_index') is not None:
                    zone['swept_index'] = zone['swept_index'] * tf.getMultiplier(smallest_tf,zone['time_frame'])
                if zone.get('end_index') is not None:
                    zone['end_index'] = zone['end_index'] * tf.getMultiplier(smallest_tf,zone['time_frame'])
                if zone.get('touch_indexs') is not None:
                    zone['touch_indexs'] = [i * tf.getMultiplier(smallest_tf,zone['time_frame']) for i in zone['touch_indexs'] if i is not None]
            else :
                if zone.get('index') is not None:
                    zone['index'] = zone['index'] * tf.getMultiplier(smallest_tf,zone['time_frame'])
                if zone.get('touch_index') is not None:
                    zone['touch_index'] = zone['touch_index'] * tf.getMultiplier(smallest_tf,zone['time_frame'])
    
    def getNearbyZone(self,merged):
        results = []
        total = len(merged)

        for i, zone in enumerate(merged):
            this_high = zone.get('zone_high')
            this_low = zone.get('zone_low')
            this_index = zone.get('zone_index')
            #print(f'{i}/{total}')

            def compute_nearest(index):
                min_dist_above = float('inf')
                min_dist_below = float('inf')
                nearest_above_zone = None
                nearest_below_zone = None

                # Cache index-based filtering
                valid_zones = [
                                    z for z in merged if (z.get('zone_index',0) < index) and (z['touch_index'] is None or (not z['touch_index'] is None and z['touch_index'] > index))
                                ]

                for other in valid_zones:
                    if other is zone:
                        continue

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
            min_above, above_zone, min_below, below_zone = compute_nearest(this_index)

            updated = zone.copy()
            updated['distance_to_nearest_zone_above'] = min_above
            updated['nearest_zone_above'] = above_zone
            updated['distance_to_nearest_zone_below'] = min_below
            updated['nearest_zone_below'] = below_zone

            results.append(updated)

        return results

