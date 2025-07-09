
import numpy as np
from Data.timeFrames import timeFrame
class ZoneMerger:
    def __init__(self, zones, threshold=0.002):
        self.zones = zones
        self.threshold = threshold
        self.changeIndexNumber()
        self.seperate()

    def seperate(self):
        self.liq_zones = [z for z in self.zones if  z['type'] in ['Buy-Side Liq','Sell-Side Liq']]
        self.core_zones = [z for z in self.zones if z['type'] not in ['Buy-Side Liq','Sell-Side Liq']]
        
    
    def merge(self):
        merged = []
        used = set()

        for i, zone in enumerate(self.core_zones):
            if i in used:
                continue

            group = [zone]
            used.add(i)

            z_high = zone['zone_high'] * (1 + self.threshold)
            z_low = zone['zone_low'] * (1 - self.threshold)
            available_zones = [z for z in self.core_zones if (z['touch_index'] is not None and z['touch_index'] > zone['index']  ) or z['touch_index'] is None]
            for j, other in enumerate(available_zones):
                orig_index = self.core_zones.index(other)
                if orig_index in used or i == orig_index:
                    continue

                other_high = other['zone_high'] * (1 + self.threshold)
                other_low = other['zone_low'] * (1 - self.threshold)

                # Check if zones overlap
                if (
                    (other_low <= z_high and other_high >= z_high) or
                    (other_high >= z_low and other_low <= z_low) or
                    (other_low >= z_low and other_high <= z_high) or
                    (other_low <= z_low and other_high >= z_high)
                ):
                    group.append(other)
                    used.add(orig_index)

                    # Expand merged zone bounds
                    z_high = max(z_high, other['zone_high'] * (1 + self.threshold))
                    z_low = min(z_low, other['zone_low'] * (1 - self.threshold))

            # Merge metadata
            merged_zone = {
                'zone_high': max(z['zone_high'] for z in group),
                'zone_low': min(z['zone_low'] for z in group),
                'zone_width': max(z['zone_high'] for z in group) - min(z['zone_low'] for z in group),
                'types': list(set(z['type'] for z in group)),
                'timeframes': list(set(z['time_frame'] for z in group)),
                'count': len(group),
                'start_index': min(z['index'] for z in group),
                'end_index': max(z['index'] for z in group),
                'mid_index': int(np.mean([z['index'] for z in group])), 
            }

            merged.append(merged_zone)

        return merged
    
    def add_liq_confluence(self,merged):
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
        return merged
    
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

