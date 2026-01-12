import numpy as np
from Utility.MemoryUsage import MemoryUsage as mu
import pandas as pd

class BaseZone:
    def __init__(self,df: pd.DataFrame = []):
        self.df = df
        self.initialize()

    def initialize(self):
        """Extract all commonly used arrays from df"""
        self.highs = self.df['high'].values
        self.lows = self.df['low'].values
        self.opens = self.df['open'].values
        self.closes = self.df['close'].values
        self.volumes = self.df['volume'].values
        self.trades = self.df['number_of_trades'].values
        self.timestamps = self.df['timestamp'].values
        
    @mu.log_memory
    def detect(self):
        """Detect zones, to be implemented by child classes"""
        raise NotImplementedError("Child class must implement detect() method.")