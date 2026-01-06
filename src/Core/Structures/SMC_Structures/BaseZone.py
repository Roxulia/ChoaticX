import numpy as np
from Utility.MemoryUsage import MemoryUsage as mu

class BaseZone:
    def __init__(self,df=[],timeframe = '1h'):
        self.df = df
        self.timeframe = timeframe
        self.initialize()

    def initialize(self):
        """Extract all commonly used arrays from df"""
        self.highs = self.df['high'].values
        self.lows = self.df['low'].values
        self.opens = self.df['open'].values
        self.closes = self.df['close'].values
        self.volumes = self.df['volume'].values
        self.ma_short = self.df['ma_short'].values
        self.ma_long = self.df['ma_long'].values
        self.ema_short = self.df['ema_short'].values
        self.ema_long = self.df['ema_long'].values
        self.atr = self.df['atr'].values
        self.rsi = self.df['rsi'].values
        self.atr_mean = self.df['atr_mean'].values
        self.bb_high = self.df['bb_high'].values
        self.bb_low = self.df['bb_low'].values
        self.bb_mid = self.df['bb_mid'].values
        self.trades = self.df['number_of_trades'].values
        self.timestamps = self.df['timestamp'].values
        # Optional fields
        self.alphas = self.df['alpha'].values if 'alpha' in self.df else None
        self.betas = self.df['beta'].values if 'beta' in self.df else None
        self.gammas = self.df['gamma'].values if 'gamma' in self.df else None
        self.r2s = self.df['r2'].values if 'r2' in self.df else None

    @mu.log_memory
    def detect(self):
        """Detect zones, to be implemented by child classes"""
        raise NotImplementedError("Child class must implement detect() method.")