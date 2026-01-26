import pandas as pd 
import numpy as np
import asyncio
from Data.timeFrames import timeFrame
from Data.indexCalculate import IndexCalculator
from Utility.MemoryUsage import MemoryUsage as mu
from Utility.Logger import Logger
from Features.Generators.BaseDataGenerator import BaseDataGenerator
from tqdm import tqdm
from .registry import register_modifier

@register_modifier
class Confluents():
    def __init__(self,timeFrames,threshold):
        self.threshold = threshold
        self.timeFrames = timeFrames

    def load_zones(self):
        zones = []
        for tf in self.timeFrames:
            bdg = BaseDataGenerator()
            data = asyncio.run(bdg.getZonesByInterval(tf))
            zones.extend(data)
        return zones

    def seperate(self,zones):
        self.liq_zones = [z for z in zones if  z['zone_type'] in ['Buy-Side Liq','Sell-Side Liq']]
        self.core_zones = [z for z in zones if z['zone_type'] not in ['Buy-Side Liq','Sell-Side Liq']]
        

    def get_available_cores(self,zone):
        available_core = []
        touch_time = zone.get('touch_time')
        swept_time = zone.get('swept_time')

        # Pick whichever is available as the reference
        ref_time = touch_time or swept_time
        if ref_time is None:
            return []

        for z in self.core_zones:
            z_touch_time = z.get('touch_time')

            # If zone never swept, always available
            if z_touch_time is None:
                available_core.append(z)
            # Compare safely
            elif ref_time < z_touch_time:
                available_core.append(z)

        return available_core



    def get_available_liq(self, zone):
        available_liq = []
        touch_time = zone.get('touch_time')
        swept_time = zone.get('swept_time')

        # Pick whichever is available as the reference
        ref_time = touch_time or swept_time
        if ref_time is None:
            return []

        for z in self.liq_zones:
            z_touch_time = z.get('swept_time')

            # If zone never swept, always available
            if z_touch_time is None:
                available_liq.append(z)
            # Compare safely
            elif ref_time < z_touch_time:
                available_liq.append(z)

        return available_liq


    @mu.log_memory
    def add_core_confluence(self,inner_func = False):
        for m in tqdm(self.based_zones,desc='Adding Core Confluents',disable=inner_func):
            confluents = []
            available_zones = [z for z in self.core_zones if ( (z['touch_time'] is not None and z['touch_time'] > m['timestamp'] ) or (z['touch_time'] is None )) ]
            for lz in available_zones:
                high = m['zone_high']+self.threshold
                low = m['zone_high'] - self.threshold
                if lz['zone_low'] <= high and lz['zone_high'] >= low:
                    confluents.append({
                        'type': lz['zone_type'],
                        'timeframe': lz['time_frame'],
                    })
            m['core_confluence'] = confluents
            
    @mu.log_memory
    def add_liq_confluence(self,inner_func = False):
        for m in tqdm(self.based_zones,desc = 'Adding Liq Confluents',disable=inner_func):
            confluents = []
            available_zones = [z for z in self.liq_zones if ( (z['swept_time'] is not None and z['swept_time'] > m['timestamp'] ) or (z['swept_time'] is None )) ]
            for lz in available_zones:
                high = m['zone_high']+self.threshold
                low = m['zone_high'] - self.threshold
                if lz['zone_low'] <= high and lz['zone_high'] >= low:
                    confluents.append({
                        'type': lz['zone_type'],
                        'timeframe': lz['time_frame'],
                    })
            m['liquidity_confluence'] = confluents

    @mu.log_memory
    def add_available_zones(self,inner_func = False):
        for zone in tqdm(self.based_zones,desc='Adding Available Zones',disable= inner_func):
            zone['available_liquidity'] = self.get_available_liq(zone)
            zone['available_core'] = self.get_available_cores(zone)
    
    @mu.log_memory
    def get(self, data, inner_func = False):
        self.based_zones = data
        data = self.load_zones() + self.based_zones
        self.seperate(data)
        self.add_core_confluence(inner_func=inner_func)
        self.add_liq_confluence(inner_func=inner_func)
        self.add_available_zones(inner_func=inner_func)
        return self.based_zones

