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

    def generate(self,zones:pd.DataFrame):
        signal = None
        tp = None
        sl = None
        predicted_result = self.models.predict(zones)
        zones['is_target'] = predicted_result
        target = zones.loc[zones['is_target']==1]
        if not target.empty:
            row = target[0]
            if row['zone_low'] > row['az_zone_high']:
                tp = row['az_zone_high']
                sl = row['zone_high']
                entry = row['zone_low']
                signal = 'Short'
            else:
                tp = row['az_zone_low']
                sl = row['zone_low']
                entry = row['zone_high']
                signal = 'Long'
            if self.filter(entry,sl,tp):
                row['signal'] = signal
                row['entry'] = entry
                row['tp'] = tp  
                row['sl'] = sl
                row['result'] = 'Pending'
                header = self.get_signals_count() == 0
                if header:
                    row.to_csv(self.signal_storage, mode='w', header=True, index=False)
                else:
                    row.to_csv(self.signal_storage, mode='a', header=False, index=False)
                return {"side":signal,"entry_price" : entry,"tp" : tp,"sl":sl,"meta":row }
            else:
                return 'None'
        else:
            return 'None'
        
    def get_signals_count(self):
        signals = []
        if os.path.exists(self.signal_storage):
            with open(self.signal_storage, 'r') as f:
                for line in f:
                    data = pd.read_csv(line)
                    signals.append(data)
        return len(signals) if signals else 0