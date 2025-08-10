import pandas as pd
class SignalGenerator:
    def __init__(self, models):
        self.models = models

    def generate(self,zones:pd.DataFrame):
        signal = None
        tp = None
        sl = None
        predicted_result = self.models.predict(zones)
        zones['is_target'] = predicted_result
        target = zones.loc[zones['is_target']==1]
        if target:
            if target['zone_low'] > target['az_zone_high']:
                tp = target['az_zone_high']
                sl = target['zone_high']
                signal = 'Short'
            else:
                tp = target['az_zone_low']
                sl = target['zone_low']
                signal = 'Long'
        return signal,tp,sl