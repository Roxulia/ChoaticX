from Exceptions.ServiceExceptions import errorHandling
from .BaseZone import BaseZone
from tqdm import tqdm
from Utility.MemoryUsage import MemoryUsage as mu
from ..registry import register_structure,register_zone
from Core.Features.meta_registry import register_feature_meta


@register_zone
@register_feature_meta
class Swings(BaseZone):

    META = {
        'name': 'Swings',
        'short_name': 'Swings',
        'is_zone': False,
        'description': 'Detects swing highs and lows in price data.',
        'parameters': {
            'window': {
                'type': 'int',
                'default': 10,
                "description": "The window size for swing detection."
            }
        },
        "provides": {
            "swings": "Detected swing points"
        },
        "requires": {}
    }

    def __init__(self, df = [], window=10):
        super().__init__(df)
        self.window = window

    @mu.log_memory
    @errorHandling
    def detect(self, inner_func=False):
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
        swings = self.label_market_structure(swings)
        self.swings = swings
        return swings
    
    def label_market_structure(self,swings=None):
        last_high = None
        last_low = None
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
        self.swings = swings
        return swings