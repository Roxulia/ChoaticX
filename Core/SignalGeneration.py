import pandas as pd
from .Filter import Filter
class SignalGenerator:
    def __init__(self, models):
        self.models = models
        self.filter = Filter()

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
                return f'Signal : {signal},Entry price : {entry},TP : {tp},SL : {sl}'
            else:
                return 'None'
        else:
            return 'None'