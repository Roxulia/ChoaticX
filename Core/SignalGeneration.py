import pandas as pd
from .Filter import Filter
from dotenv import load_dotenv
from ML.dataCleaning import DataCleaner
from ML.Model import ModelHandler
import os
from datetime import datetime,timezone
from Database.DataModels.Signals import Signals
from Exceptions.ServiceExceptions import *
from Utility.UtilityClass import UtilityFunctions as utility

class SignalGenerator:
    def __init__(self, modelHandler : ModelHandler = None,datacleaner : DataCleaner = None,ignore_cols = []):
        self.modelhandler = modelHandler
        self.datacleaner = datacleaner
        self.ignore_cols = ignore_cols
        self.filter = Filter()

    def generate(self, zones: list,backtest = False):
        if len(zones) == 0:
            raise EmptyDataInput
        try:
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
                position = "Short"
            else:  # Long
                tp = row["above_zone_high"]
                sl = row["zone_low"]
                entry = row["zone_high"]
                position = "Long"
        except Exception as e:
            raise e

        # Validate with filter
        if not self.filter.is_valid(entry, sl, tp):
            raise NotEnoughRR

        signal = {
            'position' : position,
            'entry_price' : entry,
            'tp' : tp,
            'sl' : sl,
            'result' : "Pending",
        }
        
        try:
            if not backtest:
                sql_data = {k: utility.to_sql_friendly(v) for k, v in signal.items()}
                Signals.create(signal)
        except Exception as e:
            raise e
        finally:
            return {
                "side": position,
                "entry_price": entry,
                "tp": tp,
                "sl": sl,
                "timestamp" : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "meta": row.to_dict(),  # safer for later use
            }

    
    def get_running_signals(self):
        try:
            signals = Signals.getPendingSignals()
            if signals:
                return signals
            else:
                raise EmptySignalException
        except Exception as e:
            raise e
        
    def updateSignalStatus(self,id,status):
        try:
            signal = Signals.find(id)
            if signal:
                Signals.update(id,{'result':status})  
            else:
                raise EmptySignalException
        except Exception as e:
            raise e 