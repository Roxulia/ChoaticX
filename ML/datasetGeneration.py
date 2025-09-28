
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

    def extract_confluent_tf_per_zone(self,zone):
        confluents = zone.get('liquidity_confluence',[]) + zone.get('core_confluence',[])
        data = {k: v for k, v in zone.items() if k not in ['liquidity_confluence','core_confluence']}
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
        
        data['conf_is_buy_zone'] =   1 if buyzones > sellzones else 0
        data['conf_count_BuOB']   = type_counts['Bullish OB']
        data['conf_count_BrOB']   = type_counts['Bearish OB']
        data['conf_count_BuFVG']   = type_counts['Bullish FVG']
        data['conf_count_BrFVG']   = type_counts['Bearish FVG']
        data['conf_count_BuLiq']   = type_counts['Buy-Side Liq']
        data['conf_count_BrLiq']   = type_counts['Sell-Side Liq']
        data['conf_1min_count'] = tf_counts["1min"]
        data['conf_3min_count'] = tf_counts["3min"]
        data['conf_5min_count'] = tf_counts["5min"]
        data['conf_15min_count'] = tf_counts["15min"]
        data['conf_1h_count'] = tf_counts["1h"]
        data['conf_4h_count'] = tf_counts["4h"]
        data['conf_1D_count'] = tf_counts["1D"]
        return data

    def extract_types_tf_counts(self):
        dataset = []
        for zone in self.dataset:
            types = zone.get('types',[])
            timeframes = zone.get('timeframes',[])
            type_counts,tf_counts,buyzones,sellzones = self.perform_counts(types,timeframes)
            data = zone.copy()
            data['is_buy_zone'] =   1 if buyzones > sellzones else 0
            data['count_BuOB']   = type_counts['Bullish OB']
            data['count_BrOB']   = type_counts['Bearish OB']
            data['count_BuFVG']   = type_counts['Bullish FVG']
            data['count_BrFVG']   = type_counts['Bearish FVG']
            data['count_BuLiq']   = type_counts['Buy-Side Liq']
            data['count_BrLiq']   = type_counts['Sell-Side Liq']
            data['1min_count'] = tf_counts["1min"]
            data['3min_count'] = tf_counts["3min"]
            data['5min_count'] = tf_counts["5min"]
            data['15min_count'] = tf_counts["15min"]
            data['1h_count'] = tf_counts["1h"]
            data['4h_count'] = tf_counts["4h"]
            data['1D_count'] = tf_counts["1D"]
            dataset.append(data)
        self.dataset = dataset
        return dataset
    
    def extract_nearby_zones(self):
        dataset = []
        for zone in self.dataset:
            above_zone = zone.get('above_zone')
            below_zone = zone.get('below_zone')

            if above_zone is None and below_zone is None:
                data = zone.copy()
                data['below_zone_high'] = None
                data['below_zone_low'] = None
                data['below_zone_width'] = None
                data['below_zone_count'] = None
                data['below_types'] = []
                data['below_timeframes'] = []
                data['above_zone_high'] = None
                data['above_zone_low'] = None
                data['above_zone_width'] = None
                data['above_zone_count'] = None
                data['above_types'] = []
                data['above_timeframes'] = []
                dataset.append(data)
            else:
                data = zone.copy()
                if above_zone is not None:
                    
                    data['above_zone_high'] = above_zone.get('zone_high')
                    data['above_zone_low'] = above_zone.get('zone_low')
                    data['above_zone_width'] = above_zone.get('zone_width')
                    data['above_zone_count'] = above_zone.get('count')
                    data['above_types'] = above_zone.get('types',[])
                    data['above_timeframes'] = above_zone.get('timeframes',[])
                else:
                    data['above_zone_high'] = None
                    data['above_zone_low'] = None
                    data['above_zone_width'] = None
                    data['above_zone_count'] = None
                    data['above_types'] = []
                    data['above_timeframes'] = []

                if below_zone is not None:
                    
                    data['below_zone_high'] = below_zone.get('zone_high')
                    data['below_zone_low'] = below_zone.get('zone_low')
                    data['below_zone_width'] = below_zone.get('zone_width')
                    data['below_zone_count'] = below_zone.get('count')
                    data['below_types'] = below_zone.get('types',[])
                    data['below_timeframes'] = below_zone.get('timeframes',[])
                else:
                    data['below_zone_high'] = None
                    data['below_zone_low'] = None
                    data['below_zone_width'] = None
                    data['below_zone_count'] = None
                    data['below_types'] = []
                    data['below_timeframes'] = []

                dataset.append(data)
        self.dataset = dataset
        return dataset

    def extract_nearby_zones_types_tf(self):
        dataset = []
        for zone in self.dataset:
            data = zone.copy()
            above_types = zone.get('above_types',[])
            above_tfs = zone.get('above_timeframes',[])
            type_counts,tf_counts,buyzones,sellzones = self.perform_counts(above_types,above_tfs)
            
            data['above_is_buy_zone'] =   1 if buyzones > sellzones else 0
            data['above_count_BuOB']   = type_counts['Bullish OB']
            data['above_count_BrOB']   = type_counts['Bearish OB']
            data['above_count_BuFVG']   = type_counts['Bullish FVG']
            data['above_count_BrFVG']   = type_counts['Bearish FVG']
            data['above_count_BuLiq']   = type_counts['Buy-Side Liq']
            data['above_count_BrLiq']   = type_counts['Sell-Side Liq']
            data['above_1min_count'] = tf_counts["1min"]
            data['above_3min_count'] = tf_counts["3min"]
            data['above_5min_count'] = tf_counts["5min"]
            data['above_15min_count'] = tf_counts["15min"]
            data['above_1h_count'] = tf_counts["1h"]
            data['above_4h_count'] = tf_counts["4h"]
            data['above_1D_count'] = tf_counts["1D"]
            
            above_types = zone.get('below_types',[])
            above_tfs = zone.get('below_timeframes',[])
            type_counts,tf_counts,buyzones,sellzones = self.perform_counts(above_types,above_tfs)
            data['below_is_buy_zone'] =   1 if buyzones > sellzones else 0
            data['below_count_BuOB']   = type_counts['Bullish OB']
            data['below_count_BrOB']   = type_counts['Bearish OB']
            data['below_count_BuFVG']   = type_counts['Bullish FVG']
            data['below_count_BrFVG']   = type_counts['Bearish FVG']
            data['below_count_BuLiq']   = type_counts['Buy-Side Liq']
            data['below_count_BrLiq']   = type_counts['Sell-Side Liq']
            data['below_1min_count'] = tf_counts["1min"]
            data['below_3min_count'] = tf_counts["3min"]
            data['below_5min_count'] = tf_counts["5min"]
            data['below_15min_count'] = tf_counts["15min"]
            data['below_1h_count'] = tf_counts["1h"]
            data['below_4h_count'] = tf_counts["4h"]
            data['below_1D_count'] = tf_counts["1D"]
            dataset.append(data)
        self.dataset = dataset
        return dataset

    def extract_features_and_labels(self,zone):
        touch_candle = zone.get('touch_candle')
        features= {k: v for k, v in zone.items() if k not in ['touch_candle','available_core','available_liquidity']}
        if touch_candle is None:
            features['candle_volume'] = None
            features['candle_open'] = None
            features['candle_close'] = None
            features['candle_ema20'] = None
            features['candle_ema50'] = None
            features['candle_bb_high'] = None
            features['candle_bb_low'] = None
            features['candle_bb_mid'] = None
            features['candle_rsi'] = None
            features['candle_atr'] = None
            features['candle_timestamp'] = None
        else:
            features = {**features,**{f'candle_{k}': v for k,v in touch_candle.items()}}
        return features
    
    def extract_available_zones(self,confluents):
        for zone in confluents:
            availables = zone.get('available_zones', [])
            base_data = {k: v for k, v in zone.items() if k != 'available_zones'}
            if not availables:
                continue

            for a_zone in availables:
                temp_zone = self.extract_confluent_tf_per_zone(a_zone)
                yield {**base_data, **{f'az_{k}': v for k, v in temp_zone.items() if k not in ['available_core','available_liquidity']}}
    
    def extract_nearby_zone_data(self,confluents):
        for zone in confluents:
            above_zone = zone.get('nearest_zone_above',None)
            below_zone = zone.get('nearest_zone_below',None)
            base_data = {k: v for k, v in zone.items() if k not in ['nearest_zone_above','nearest_zone_below','available_zones']}
            if above_zone is None and below_zone is None:
                yield {**base_data}
            else:
                temp_ab = {}
                temp_bl = {}
                if above_zone:
                    temp_zone = self.extract_confluent_tf_per_zone(above_zone)
                    temp_ab = {f'above_zone_{k}': v for k, v in temp_zone.items() if k not in ['available_core','available_liquidity','nearest_zone_above','nearest_zone_below']}
                if below_zone:
                    temp_zone = self.extract_confluent_tf_per_zone(below_zone)
                    temp_bl = {f'below_zone_{k}': v for k, v in temp_zone.items() if k not in ['available_core','available_liquidity','nearest_zone_above','nearest_zone_below']}
                yield {**base_data, **temp_ab,**temp_bl}

    def extract_nearby_zone_data_per_zone(self,zone):
        above_zone = zone.get('nearest_zone_above',None)
        below_zone = zone.get('nearest_zone_below',None)
        base_data = {k: v for k, v in zone.items() if k not in ['nearest_zone_above','nearest_zone_below','available_zones']}
        if above_zone is None and below_zone is None:
            return {**base_data}
        else:
            temp_ab = {}
            temp_bl = {}
            if above_zone:
                temp_zone = self.extract_confluent_tf_per_zone(above_zone)
                temp_ab = {f'above_zone_{k}': v for k, v in temp_zone.items() if k not in ['available_core','available_liquidity','nearest_zone_above','nearest_zone_below']}
            if below_zone:
                temp_zone = self.extract_confluent_tf_per_zone(below_zone)
                temp_bl = {f'below_zone_{k}': v for k, v in temp_zone.items() if k not in ['available_core','available_liquidity','nearest_zone_above','nearest_zone_below']}
            return {**base_data, **temp_ab,**temp_bl}
    
    def extract_label(self,availables):
        for zone in availables:
            target = zone.get('target_zone')
            base_data = {k: v for k, v in zone.items() if k != 'target_zone'}
            if target is not None :
                if target['index'] == zone['az_index']:
                    base_data['is_target'] = 1
                else:
                    base_data['is_target'] = 0
            else:
                base_data['is_target'] = None
            yield {**base_data}

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
                    existed_zone = FVG.GetByTimeStamp(sql_data['timestamp'])
                    if existed_zone:
                        FVG.update(existed_zone['id'],sql_data)
                    else:
                        FVG.create(sql_data)
                elif zone_type in ['Bearish OB','Bullish OB'] :
                    ob_columns = [k for k,v in OB.columns.items()]
                    sql_data = {k:v for k,v in sql_data.items() if k in ob_columns}
                    sql_data['symbol'] = self.symbol
                    existed_zone = OB.GetByTimeStamp(sql_data['timestamp'])
                    if existed_zone:
                        OB.update(existed_zone['id'],sql_data)
                    else:
                        OB.create(sql_data)
                elif zone_type in ['Buy-Side Liq','Sell-Side Liq']:
                    liq_columns = [k for k,v in LIQ.columns.items()]
                    sql_data = {k:v for k,v in sql_data.items() if k in liq_columns}
                    sql_data['symbol'] = self.symbol
                    existed_zone = LIQ.GetByTimeStamp(sql_data['timestamp'])
                    if existed_zone:
                        LIQ.update(existed_zone['id'],sql_data)
                    else:
                        LIQ.create(sql_data)
            except Exception as e:
                print(f'{e}')
                raise e

    @mu.log_memory
    def get_dataset_list(self,zones):
        
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
                        with open(f"{self.Paths.raw_data}/{self.symbol}_raw.jsonl", "w") as f:
                            
                            f.write(json.dumps(to_write , default=utility.default_json_serializer) + "\n")
                            for k,v in to_write.items():
                                columns.add(k)
                        dataset_start = False
                    else:
                        with open(f"{self.Paths.raw_data}/{self.symbol}_raw.jsonl", "a") as f:
                            f.write(json.dumps(to_write , default=utility.default_json_serializer) + "\n")
                            for k,v in to_write.items():
                                columns.add(k)
                else:
                    zone_type = row.get('zone_type',None)
                    sql_data = {k: utility.to_sql_friendly(v) for k, v in row.items()}
                    if zone_type in ['Bearish FVG','Bullish FVG'] : 
                        fvg_columns = [k for k,v in FVG.columns.items()]
                        sql_data = {k:v for k,v in sql_data.items() if k in fvg_columns}
                        sql_data['symbol'] = self.symbol
                        existed_zone = FVG.GetByTimeStamp(sql_data['timestamp'])
                        if existed_zone:
                            FVG.update(existed_zone['id'],sql_data)
                        else:
                            FVG.create(sql_data)
                    elif zone_type in ['Bearish OB','Bullish OB'] :
                        ob_columns = [k for k,v in OB.columns.items()]
                        sql_data = {k:v for k,v in sql_data.items() if k in ob_columns}
                        sql_data['symbol'] = self.symbol
                        existed_zone = OB.GetByTimeStamp(sql_data['timestamp'])
                        if existed_zone:
                            OB.update(existed_zone['id'],sql_data)
                        else:
                            OB.create(sql_data)
                    elif zone_type in ['Buy-Side Liq','Sell-Side Liq']:
                        liq_columns = [k for k,v in LIQ.columns.items()]
                        sql_data = {k:v for k,v in sql_data.items() if k in liq_columns}
                        sql_data['symbol'] = self.symbol
                        existed_zone = LIQ.GetByTimeStamp(sql_data['timestamp'])
                        if existed_zone:
                            LIQ.update(existed_zone['id'],sql_data)
                        else:
                            LIQ.create(sql_data)
                    
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