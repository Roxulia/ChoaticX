import pandas as pd 
import numpy as np
from Data.timeFrames import timeFrame
from Data.indexCalculate import IndexCalculator

class ConfluentsFinder():
    def __init__(self,zones):
        self.zones = zones
        self. timeframes = timeFrame()
        self.indexCalculate = IndexCalculator(self.zones)
        
        

    def seperate(self):
        self.liq_zones = [z for z in self.zones if  z['type'] in ['Buy-Side Liq','Sell-Side Liq']]
        self.core_zones = [z for z in self.zones if z['type'] not in ['Buy-Side Liq','Sell-Side Liq']]
        self.based_zones = self.timeframes.getBasedZone(self.zones)

    def add_core_confluence(self):
        for m in self.based_zones:
            confluents = []
            available_zones = [z for z in self.core_zones if (z['touch_index'] is not None and z['touch_index'] > m['index'] ) or (z['touch_index'] is None) ]
            for lz in available_zones:
                if lz['zone_low'] <= m['zone_high'] and lz['zone_high'] >= m['zone_low']:
                    confluents.append({
                        'type': lz['type'],
                        'timeframe': lz['time_frame'],
                        'zone_low': lz['zone_low'],
                        'zone_high': lz['zone_high'],
                        'touched': lz.get('touch_index') is not None
                    })
            m['core_confluence'] = confluents

    def add_liq_confluence(self):
        for m in self.based_zones:
            confluents = []
            available_zones = [z for z in self.liq_zones if (z['swept_index'] is not None and z['swept_index'] > m['index'] ) or (z['swept_index'] is None) ]
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
    
    def getConfluents(self):
        self.zones = self.indexCalculate.calculate()
        self.seperate()
        self.add_core_confluence()
        self.add_liq_confluence()
        return self.zones
