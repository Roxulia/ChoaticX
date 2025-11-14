
import pandas as pd
import numpy as np
from tqdm import tqdm
import json
from Utility.MemoryUsage import MemoryUsage as mu
from Data.Paths import Paths
from Database.DataModels.FVG import FVG 
from Database.DataModels.OB import OB
from Database.DataModels.Liq import LIQ
from Database.Cache import Cache
from Utility.UtilityClass import UtilityFunctions as utility

class DatasetGenerator:
    def __init__(self,symbol = "BTCUSDT",timeframes = ['1h','4h','1D']):
        self.Paths = Paths()
        self.symbol = symbol
        self.filename = f'{symbol}_' + "_".join(timeframes)+"_raw.jsonl"
        self.dataset = []
        self.total_line = 0
        self.timeframes = timeframes

    def perform_counts(self,types = [],timeframes = []):
        type_counts = {
                "Bullish OB": 0,
                "Bullish FVG": 0,
                "Bearish OB": 0,
                "Bearish FVG": 0,
                "Buy-Side Liq":0,
                "Sell-Side Liq" : 0
            }
        tf_counts = {
            key : 0 for key in self.timeframes
        }

        # Count types
        for t in types:
            if t in type_counts:
                type_counts[t] += 1

        # Count timeframes
        for tf in timeframes:
            if tf in tf_counts:
                tf_counts[tf] += 1

        # Aggregate zone class
        buyzones = type_counts["Bullish OB"] + type_counts["Bullish FVG"] + type_counts['Buy-Side Liq']
        sellzones = type_counts["Bearish OB"] + type_counts["Bearish FVG"] + type_counts['Sell-Side Liq']
        return type_counts,tf_counts,buyzones,sellzones

    def extract_built_by_zones(self,index):
        return self.zones[index]['built_by']
    
    def preform_zone_confluent_extraction(self,confluents,prefix=''):
        types = []
        timeframes = []
        for c in confluents:
            c_type = c.get('type',None)
            if c_type is not None:
                types.append(c_type)
            c_tf = c.get('timeframe',None)
            if c_tf is not None:
                timeframes.append(c_tf)
        type_counts,tf_counts,buyzones,sellzones = self.perform_counts(types,timeframes)
        data = {}
        data[f'{prefix}conf_is_buy_zone'] =   1 if buyzones > sellzones else 0
        data[f'{prefix}conf_count_BuOB']   = type_counts['Bullish OB']
        data[f'{prefix}conf_count_BrOB']   = type_counts['Bearish OB']
        data[f'{prefix}conf_count_BuFVG']   = type_counts['Bullish FVG']
        data[f'{prefix}conf_count_BrFVG']   = type_counts['Bearish FVG']
        data[f'{prefix}conf_count_BuLiq']   = type_counts['Buy-Side Liq']
        data[f'{prefix}conf_count_BrLiq']   = type_counts['Sell-Side Liq']
        tfs = { f'{prefix}conf_{key}_count' : value for key,value in tf_counts.items()}
        return {**data,**tfs}

    def extract_based_zone_confluent_tf(self,features):
        for zone in features:
            confluents = zone.get('liquidity_confluence',[]) + zone.get('core_confluence',[])
            data = {k: v for k, v in zone.items() if k not in ['liquidity_confluence','core_confluence']}
            extracted = self.preform_zone_confluent_extraction(confluents)
            yield {**data,**extracted}
    
    def extract_nearby_zones_confluent_tf(self,zone):
        above_confluents = zone.get('above_liquidity_confluence',[]) + zone.get('above_core_confluence',[])
        below_confluents = zone.get('below_liquidity_confluence',[]) + zone.get('below_core_confluence',[])
        data = {k: v for k, v in zone.items() if k not in ['above_liquidity_confluence','above_core_confluence','below_liquidity_confluence','below_core_confluence']}
        above_extracted = self.preform_zone_confluent_extraction(above_confluents,prefix='above_')
        below_extracted = self.preform_zone_confluent_extraction(below_confluents,prefix='below_')
        return {**data,**above_extracted,**below_extracted}

    def extract_features_and_labels(self,zone):
        touch_candle = zone.get('touch_candle')
        features= {k: v for k, v in zone.items() if k not in ['touch_candle','available_core','available_liquidity']}
        if touch_candle is None:
            features['candle_volume'] = None
            features['candle_open'] = None
            features['candle_close'] = None
            features['candle_number_of_trades'] = None
            features['candle_ma_short'] = None
            features['candle_ma_long'] = None
            features['candle_ema_short'] = None
            features['candle_ema_long'] = None
            features['candle_bb_high'] = None
            features['candle_bb_low'] = None
            features['candle_bb_mid'] = None
            features['candle_alpha'] = None
            features['candle_beta'] = None
            features['candle_gamma'] = None
            features['candle_r2'] = None
            features['candle_rsi'] = None
            features['candle_atr'] = None
            features['candle_timestamp'] = None
        else:
            features = {**features,**{f'candle_{k}': v for k,v in touch_candle.items()}}
        return features
    
    def clearNoneTarget(self,data):
        for row in data:
            if row.get('target') is not None:
                yield row
    
    def store_untouch_zones(self,zones,start = True):
        data = self.extract_based_zone_confluent_tf(zones)
        for i,row in enumerate(tqdm(data,desc="Writing to untouch zone storage file")):
            try:
                zone_type = row.get('zone_type',None)
                sql_data = {k: utility.to_sql_friendly(v) for k, v in row.items()}
                if zone_type in ['Bearish FVG','Bullish FVG'] : 
                    fvg_columns = [k for k,v in FVG.columns.items()]
                    sql_data = {k:v for k,v in sql_data.items() if k in fvg_columns}
                    sql_data['symbol'] = self.symbol
                    existed_zone = FVG.GetByUniqueZone(sql_data['timestamp'],self.symbol,sql_data['time_frame'])
                    if existed_zone:
                        FVG.update(existed_zone['id'],sql_data)
                    else:
                        FVG.create(sql_data)
                elif zone_type in ['Bearish OB','Bullish OB'] :
                    ob_columns = [k for k,v in OB.columns.items()]
                    sql_data = {k:v for k,v in sql_data.items() if k in ob_columns}
                    sql_data['symbol'] = self.symbol
                    existed_zone = OB.GetByUniqueZone(sql_data['timestamp'],self.symbol,sql_data['time_frame'])
                    if existed_zone:
                        OB.update(existed_zone['id'],sql_data)
                    else:
                        OB.create(sql_data)
                elif zone_type in ['Buy-Side Liq','Sell-Side Liq']:
                    liq_columns = [k for k,v in LIQ.columns.items()]
                    sql_data = {k:v for k,v in sql_data.items() if k in liq_columns}
                    sql_data['symbol'] = self.symbol
                    existed_zone = LIQ.GetByUniqueZone(sql_data['timestamp'],self.symbol,sql_data['time_frame'])
                    if existed_zone:
                        LIQ.update(existed_zone['id'],sql_data)
                    else:
                        LIQ.create(sql_data)
            except Exception as e:
                print(f'{e}')
                raise e

    @mu.log_memory
    def get_dataset_list(self,zones,for_predict=False):
        
        data = self.extract_based_zone_confluent_tf(zones)
        
        columns = set()
        dataset_start = True
        
        for i, row in enumerate(tqdm(data, desc="Writing to JSONL",total=self.total_line, dynamic_ncols=True)):
            touch_type = row.get('touch_type',None)
            try:
                if touch_type is not None :
                    features = self.extract_features_and_labels(row)
                    to_write = self.extract_nearby_zones_confluent_tf(features)
                    if dataset_start:
                        with open(f"{self.Paths.raw_data}/{self.filename}", "w") as f:
                            
                            f.write(json.dumps(to_write , default=utility.default_json_serializer) + "\n")
                            for k,v in to_write.items():
                                columns.add(k)
                        dataset_start = False
                    else:
                        with open(f"{self.Paths.raw_data}/{self.filename}", "a") as f:
                            f.write(json.dumps(to_write , default=utility.default_json_serializer) + "\n")
                            for k,v in to_write.items():
                                columns.add(k)
                elif not for_predict:
                    zone_type = row.get('zone_type',None)
                    sql_data = {k: utility.to_sql_friendly(v) for k, v in row.items()}
                    if zone_type in ['Bearish FVG','Bullish FVG'] : 
                        fvg_columns = [k for k,v in FVG.columns.items()]
                        sql_data = {k:v for k,v in sql_data.items() if k in fvg_columns}
                        sql_data['symbol'] = self.symbol
                        existed_zone = FVG.GetByUniqueZone(sql_data['timestamp'],self.symbol,sql_data['time_frame'])
                        if existed_zone:
                            FVG.update(existed_zone['id'],sql_data)
                        else:
                            FVG.create(sql_data)
                    elif zone_type in ['Bearish OB','Bullish OB'] :
                        ob_columns = [k for k,v in OB.columns.items()]
                        sql_data = {k:v for k,v in sql_data.items() if k in ob_columns}
                        sql_data['symbol'] = self.symbol
                        existed_zone = OB.GetByUniqueZone(sql_data['timestamp'],self.symbol,sql_data['time_frame'])
                        if existed_zone:
                            OB.update(existed_zone['id'],sql_data)
                        else:
                            OB.create(sql_data)
                    elif zone_type in ['Buy-Side Liq','Sell-Side Liq']:
                        liq_columns = [k for k,v in LIQ.columns.items()]
                        sql_data = {k:v for k,v in sql_data.items() if k in liq_columns}
                        sql_data['symbol'] = self.symbol
                        existed_zone = LIQ.GetByUniqueZone(sql_data['timestamp'],self.symbol,sql_data['time_frame'])
                        if existed_zone:
                            LIQ.update(existed_zone['id'],sql_data)
                        else:
                            LIQ.create(sql_data)
                else:
                    continue
            except TypeError as e:
                print(f"\n🚨 JSON serialization error at row {i}")
                for k, v in row.items():
                    try:
                        json.dumps(v,default=utility.default_json_serializer)  # test if this key's value is serializable
                    except TypeError:
                        print(f"  ❌ Key '{k}' is not serializable. Value: {v} (type: {type(v)})")
                raise e  
            except ValueError as e:
                print(f"\n🚨 JSON serialization error at row {i}")
                for k,v in row.items():
                    try:
                        json.dumps(v,default=utility.default_json_serializer)  # test if this key's value is serializable
                    except ValueError:
                        print(f"  ❌ Key '{k}' is not serializable. Value: {v} (type: {type(v)})")
                raise e
            except Exception as e:
                print(f'{e}')
                raise e
        self.store_column_list(list(columns))

    def store_column_list(self,columns : list):
        filename = "_".join(self.timeframes)
        path = f'{self.Paths.columns_list}/{self.symbol}_{filename}.json'
        with open(path,'w') as f :
            json.dump(columns,f)

    def extract_input_data(self,zones):
        data = list(self.extract_based_zone_confluent_tf(zones))
        for z in data:

            yield self.extract_nearby_zones_confluent_tf(z)
