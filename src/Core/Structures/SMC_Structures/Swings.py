from .BaseZone import BaseZone
from tqdm import tqdm
from Utility.MemoryUsage import MemoryUsage as mu
from ..registry import register_structure


@register_structure
class Swings(BaseZone):

    def __init__(self, df = [], window=10):
        super().__init__(df)
        self.window = window

    @mu.log_memory
    def detect(self):
        swings = []

        for i in range(len(self.df)):
            # window slice
            high_window = self.highs[max(0, i - self.window):min(len(self.df), i + self.window + 1)]
            low_window = self.lows[max(0, i - self.window):min(len(self.df), i + self.window + 1)]
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
                swings.append({**base_data, 'Type': 'Swing High', 'Price': center_high, 'swing_strength': self.window})
            elif is_swing_low:
                swings.append({**base_data, 'Type': 'Swing Low', 'Price': center_low, 'swing_strength': self.window})

        self.swings = swings
        return swings