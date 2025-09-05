import pandas as pd
from .Filter import Filter
from dotenv import load_dotenv
import os
class SignalGenerator:
    def __init__(self, models):
        self.models = models
        self.filter = Filter()
        self.signal_storage = os.getenv(key='SIGNAL_STORAGE')
        if not os.path.exists(self.signal_storage):
            open(self.signal_storage,'w')

    def generate(self, zones: pd.DataFrame,backtest = False):
        if zones.shape[0] == 0:
            return None

        # Defragment before adding column
        zones = zones.copy()

        # Predict
        predicted_result = self.models.predict(zones)
        zones["target"] = predicted_result

        # Take the first row only
        row = zones.iloc[0].copy()

        if row["target"] == 0:  # Short
            tp = row["below_zone_high"]
            sl = row["zone_high"]
            entry = row["zone_low"]
            signal = "Short"
        else:  # Long
            tp = row["above_zone_low"]
            sl = row["zone_low"]
            entry = row["zone_high"]
            signal = "Long"

        # Validate with filter
        if not self.filter.is_valid(entry, sl, tp):
            return None

        # Prepare row
        row["signal"] = signal
        row["entry"] = entry
        row["tp"] = tp
        row["sl"] = sl
        row["result"] = "Pending"

        # Save to CSV
        if not backtest:
            header = self.get_signals_count() == 0
            row.to_frame().T.to_csv(
                self.signal_storage, 
                mode="w" if header else "a", 
                header=header, 
                index=False
            )

        return {
            "side": signal,
            "entry_price": entry,
            "tp": tp,
            "sl": sl,
            "meta": row.to_dict(),  # safer for later use
        }

    def get_signals_count(self):
        signals = []
        if os.path.exists(self.signal_storage):
            with open(self.signal_storage, 'r') as f:
                for line in f:
                    data = pd.read_csv(line)
                    signals.append(data)
        return len(signals)