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
    def __init__(self, modelHandlers : list[ModelHandler] = [],datacleaner : DataCleaner = None,ignore_cols = []):
        if len(modelHandlers) == 0:
            raise EmptyDataInput
        self.modelhandlers = modelHandlers
        self.datacleaner = datacleaner
        self.ignore_cols = ignore_cols
        self.filter = Filter()

    def generate(self, zones: list,backtest = False):
        
        if len(zones) == 0:
            raise EmptyDataInput
        try:
            predicted_result = []
            for i,modelhandler in enumerate(self.modelhandlers,start=0):
                modelhandler.load()
                temp_zones = zones
                temp_zones = self.datacleaner.preprocess_input(temp_zones,ignore_cols=self.ignore_cols[i])
                zones = pd.DataFrame(zones)
                # Predict
                predicted_result.append(modelhandler.predict(temp_zones))
            zones["target"] = sum(predicted_result) / len(predicted_result)

            # Take the first row only
            row = zones.iloc[0].copy()
            symbol = row['symbol']
            if row["target"] < 0.5:  # Short
                position = "Short"
                if row["touch_from"] == "Above":  # touched from above
                    entry = row["zone_high"]
                    sl = row["candle_bb_high"]  if 'candle_bb_high' in row else row['zone_high']+(row['zone_high']*0.02)
                    tp = row["below_zone_high"] if "below_zone_high" in row else row['candle_bb_low']
                else:
                    # edge case: price touches supply from below (rare, breakout retest)
                    entry = row["zone_low"]
                    sl = row["zone_high"]  # add buffer
                    tp = row["below_zone_high"] if "below_zone_high" in row else row['candle_bb_low']
            
            else:  # Long
                position = "Long"
                if row["touch_from"] == "Below":  # touched from below
                    entry = row["zone_low"]   # aggressive
                    # entry = row["zone_low"]  # safer option
                    sl = row["candle_bb_low"] if 'candle_bb_low' in row else row['zone_low']-(row['zone_low']*0.02)
                    tp = row["above_zone_low"]
                else:
                    # edge case: price touches demand from above (breakout retest)
                    entry = row["zone_high"]
                    sl = row["zone_low"]
                    tp = row["above_zone_low"]
        except Exception as e:
            raise e

        # Validate with filter
        if not self.filter.is_valid(entry, sl, tp):
            raise NotEnoughRR

        signal = {
            'position' : position,
            'symbol' : symbol,
            'entry_price' : entry,
            'tp' : tp,
            'sl' : sl,
            'result' : "Pending",
        }
        
        try:
            if not backtest:
                sql_data = {k: utility.to_sql_friendly(v) for k, v in signal.items()}
                Signals.create(sql_data)
        except Exception as e:
            raise e
        finally:
            return {
                "position": position ,
                "symbol" : symbol,
                "entry_price": entry,
                "tp": tp,
                "sl": sl,
                "timestamp" : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "meta": row.to_dict(),  # safer for later use
            }

    
    def get_running_signals(self,limit = 0,symbol = "BTCUSDT"):
        try:
            signals = Signals.getRunningSignals(limit,symbol)
            if signals:
                return signals
            else:
                raise EmptySignalException
        except Exception as e:
            raise e
        
    def get_pending_signals(self,limit = 0,symbol = "BTCUSDT"):
        try:
            signals = Signals.getPendingSignals(limit,symbol)
            if signals:
                return signals
            else:
                raise EmptySignalException
        except Exception as e :
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
        
    def get_given_signals(self,symbol="BTCUSDT"):
        try:
            signals = Signals.getGivenSignals(limit=5,symbol=symbol)
            if signals:
                return signals
            else:
                raise EmptySignalException
        except Exception as e:
            raise e

    def bulkUpdateSignals(self,status,ids):
        try:
            Signals.bulk_update_status(ids,status)
        except Exception as e :
            raise e
