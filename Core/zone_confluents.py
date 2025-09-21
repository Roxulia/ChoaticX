import pandas as pd 
import numpy as np
from Data.timeFrames import timeFrame
from Data.indexCalculate import IndexCalculator
from Utility.MemoryUsage import MemoryUsage as mu
from tqdm import tqdm
class ConfluentsFinder():
    def __init__(self,zones):
        self.zones = zones
        self. timeframes = timeFrame()
        self.indexCalculate = IndexCalculator(self.zones)

    def seperate(self):
        self.liq_zones = [z for z in self.zones if  z['zone_type'] in ['Buy-Side Liq','Sell-Side Liq']]
        self.core_zones = [z for z in self.zones if z['zone_type'] not in ['Buy-Side Liq','Sell-Side Liq']]
        self.based_zones = self.timeframes.getBasedZone(self.zones)

    def getTimeFrameList(self):
        tfs = set()
        for zone in self.zones:
            timeframe = zone.get('timeframe',None)
            if timeframe is not None:
                tfs.add(timeframe)
        return list(tfs)

    def get_available_cores(self,zone):
        available_core = []
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
                if lz['zone_low'] <= m['zone_high'] and lz['zone_high'] >= m['zone_low']:
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
                if lz['zone_low'] <= m['zone_high'] and lz['zone_high'] >= m['zone_low']:
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
    def getConfluents(self,inner_func = False):
        self.zones = self.indexCalculate.calculate()
        self.seperate()
        self.add_core_confluence(inner_func=inner_func)
        self.add_liq_confluence(inner_func=inner_func)
        self.add_available_zones(inner_func=inner_func)
        return self.zones

