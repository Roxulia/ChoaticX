
import numpy as np
from Data.timeFrames import timeFrame
from .zone_reactions import ZoneReactor
from Data.indexCalculate import IndexCalculator

class ZoneMerger:
    def __init__(self,candles, zones, threshold=0.002):
        self.zones = zones
        self.threshold = threshold
        self.reactor = ZoneReactor(candles)
        self.indexcalculator = IndexCalculator(self.zones)
        self.zones  = self.indexcalculator.calculate()
        self.seperate()

    def seperate(self):
        self.liq_zones = [z for z in self.zones if  z['type'] in ['Buy-Side Liq','Sell-Side Liq']]
        self.core_zones = [z for z in self.zones if z['type'] not in ['Buy-Side Liq','Sell-Side Liq']]
        
    
    def merge(self):
        merged = []
        core_zones = self.core_zones
        liq_zones = self.liq_zones

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
                    merged_zone['built_by'].append(zone)
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
                    'end_index' : z_index,
                    'built_by' : [zone for zone in group],
                }  
                z = self.reactor.get_zone_reaction(z)
                merged.append(z)

        return merged
   
    

