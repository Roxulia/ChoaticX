from .BaseZone import BaseZone
from tqdm import tqdm
from Utility.MemoryUsage import MemoryUsage as mu

class Swings(BaseZone):
    @mu.log_memory
    def detect(self, window=20):
        swings = []

        for i in range(len(self.df)):
            # window slice
            high_window = self.highs[max(0, i - window):min(len(self.df), i + window + 1)]
            low_window = self.lows[max(0, i - window):min(len(self.df), i + window + 1)]
            center_high = self.highs[i]
            center_low = self.lows[i]

            is_swing_high = center_high == max(high_window)
            is_swing_low = center_low == min(low_window)

            base_data = {
                'index': i,
                'trades': self.trades[i],
                'ema_short': self.ema_short[i],
                'ema_long': self.ema_long[i],
                'ma_short': self.ma_short[i],
                'ma_long': self.ma_long[i],
                'atr': self.atr[i],
                'rsi': self.rsi[i],
                'atr_mean': self.atr_mean[i],
                'bb_high': self.bb_high[i],
                'bb_low': self.bb_low[i],
                'bb_mid': self.bb_mid[i],
                'alpha': self.alphas[i] if self.alphas is not None else None,
                'beta': self.betas[i] if self.betas is not None else None,
                'gamma': self.gammas[i] if self.gammas is not None else None,
                'r2': self.r2s[i] if self.r2s is not None else None,
                'timestamp': self.timestamps[i]
            }

            if is_swing_high:
                swings.append({**base_data, 'Type': 'Swing High', 'Price': center_high, 'swing_strength': window})
            elif is_swing_low:
                swings.append({**base_data, 'Type': 'Swing Low', 'Price': center_low, 'swing_strength': window})

        self.swings = swings
        return swings