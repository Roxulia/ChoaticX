import numpy as np
import pandas as pd
from datetime import datetime,date
import decimal
class UtilityFunctions():
    @staticmethod
    def merge_lists_by_key(old_list, new_list, key="id"):
        # Convert old list to dict keyed by primary key
        merged = {d[key]: d for d in old_list}

        for new_item in new_list:
            pk = new_item[key]
            if pk in merged:
                # Update existing entry with new values
                merged[pk].update(new_item)
            else:
                # Insert new entry
                merged[pk] = new_item

        # Return back as list
        return list(merged.values())
    
    @staticmethod
    def removeDataFromListByKeyValueList( data_list,to_remove, key ):
        """
        Remove items from a list of dictionaries where the specified key matches the given value.
        """
        result = []
        for item in data_list:
            if item[key] not in to_remove:
                result.append(item)
        return result
    
    @staticmethod
    def removeDataFromListByKeyValue(data,key,value):
        result = []
        for item in data:
            if item[key] != value:
                result.append(item)
        return result

    @staticmethod
    def getDHMS(timestring:str = '1D-1h-1m-1s'):
        #get day,hour,minutes,seconds from string
        times = timestring.split('-')
        codes = ['D','h','m','s']
        result = {'D': 0, 'h': 0, 'm': 0, 's': 0}
        for part in times:
            for code in codes:
                if part.endswith(code):
                    try:
                        result[code] = int(part[:-1])
                    except ValueError:
                        result[code] = 0
                    break
        
        return result['D'], result['h'], result['m'], result['s']

    @staticmethod
    def filter_features(importance_dict: dict, threshold: float, normalize: bool = False):
        """
        Remove features with importance lower than threshold.

        Args:
            importance_dict (dict): Feature importance dictionary {feature: importance_value}.
            threshold (float): Minimum importance value (or percentage if normalize=True).
            normalize (bool): If True, threshold is treated as a fraction of total (0–1).

        Returns:
            dict: Filtered feature importances.
        """
        if normalize:
            total = sum(importance_dict.values())
            return {
                f: v for f, v in importance_dict.items()
                if (v / total) >= threshold
            }
        else:
            return {
                f: v for f, v in importance_dict.items()
                if v >= threshold
            }
    @staticmethod
    def to_sql_friendly(value):
        """Convert numpy / python objects into SQL-friendly types."""
        if isinstance(value, (int, np.int32, np.int64)):
            return int(value)
        elif isinstance(value, (float, np.float32, np.float64)):
            return float(value)
        elif isinstance(value, (bool, np.bool_)):
            return bool(value)
        elif isinstance(value, (pd.Timestamp, np.datetime64)):
            return pd.to_datetime(value).to_pydatetime()  # convert to Python datetime
        elif isinstance(value, datetime):
            return value  # already fine
        elif isinstance(value, (list, dict)):
            return str(value)  # store as JSON/text
        else:
            return value
    
    @staticmethod
    def default_json_serializer(obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, decimal.Decimal):
            return float(obj)
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif hasattr(obj, '__str__'):
            return str(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
