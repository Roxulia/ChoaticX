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

        return swings
    
    def label_market_structure(self):
        last_high = None
        last_low = None
        swings = self.detect()
        for swing in swings:
            if swing["Type"] == "Swing High":
                if last_high is None:
                    swing["swing_type"] = "HH"  # first high, neutral bullish
                else:
                    swing["swing_type"] = "HH" if swing["Price"] > last_high else "LH"
                last_high = swing["Price"]

            elif swing["Type"] == "Swing Low":
                if last_low is None:
                    swing["swing_type"] = "LL"  # first low, neutral bearish
                else:
                    swing["swing_type"] = "HL" if swing["Price"] > last_low else "LL"
                last_low = swing["Price"]
        return swings