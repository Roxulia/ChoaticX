import pandas as pd
from .Filter import Filter
from dotenv import load_dotenv
from ML.dataCleaning import DataCleaner
from ML.Model import ModelHandler
import os
from datetime import datetime,timezone
class SignalGenerator:
    def __init__(self, modelHandler : ModelHandler = None,datacleaner : DataCleaner = None,ignore_cols = []):
        self.modelhandler = modelHandler
        self.datacleaner = datacleaner
        self.ignore_cols = ignore_cols
        self.filter = Filter()
        self.signal_storage = os.getenv(key='SIGNAL_STORAGE')
        if not os.path.exists(self.signal_storage):
            open(self.signal_storage,'w')

    def generate(self, zones: list,backtest = False):
        if len(zones) == 0:
            return None
        temp_zones = zones
        temp_zones = self.datacleaner.preprocess_input(temp_zones,ignore_cols=self.ignore_cols)
        zones = pd.DataFrame(zones)
        # Predict
        predicted_result = self.modelhandler.predict(temp_zones)
        zones["target"] = predicted_result

        # Take the first row only
        row = zones.iloc[0].copy()

        if row["target"] == 0:  # Short
            tp = row["below_zone_low"]
            sl = row["zone_high"]
            entry = row["zone_low"]
            signal = "Short"
        else:  # Long
            tp = row["above_zone_high"]
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
        row["signal_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
    
    def get_running_signals(self):
        signals = []
        if os.path.exists(self.signal_storage):
            with open(self.signal_storage,'r') as f:
                for line in f:
                    data = pd.read_csv(line)
                    if data['result'] == 'pending':
                        signal = {
                            "timestamp" : data["signal_timestamp"],
                            "side" : data['side'],
                            "entry_price" : data['entry_price'],
                            "tp" : data['tp'],
                            "sl" : data['sl']
                        }
                        signals.append(signal)
        if signals:
            return signals
        else:
            return None