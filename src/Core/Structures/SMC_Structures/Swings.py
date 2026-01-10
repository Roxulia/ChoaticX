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
                'timestamp': self.timestamps[i],
                **self.df.iloc[i]
            }

            if is_swing_high:
                swings.append({**base_data, 'Type': 'Swing High', 'Price': center_high, 'swing_strength': window})
            elif is_swing_low:
                swings.append({**base_data, 'Type': 'Swing Low', 'Price': center_low, 'swing_strength': window})

        self.swings = swings
        return swings