import numpy as np
from .timeFrames import timeframe

class IndexCalculator():
    def __init__(self,zones):
        self.zones = zones
        self.timeframe = timeFrame()

    def calculate(self):
        
