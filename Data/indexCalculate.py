import numpy as np
from .timeFrames import timeframe

class IndexCalculator():
    def __init__(self,zones):
        self.zones = zones
        self.timeframe = timeFrame()

    def calculate(self):
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
        return self.zones
