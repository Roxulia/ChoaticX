
import pandas as pd
import numpy as np
from tqdm import tqdm
import json
import datetime
import decimal

class DatasetGenerator:
    def __init__(self,  zones_with_targets):
        
        self.zones = zones_with_targets
        self.dataset = []
        self.total_line = 0

    def default_json_serializer(self,obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
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
            "1min": 0, "3min": 0, "5min": 0, "15min": 0, "1h": 0, "4h": 0, "1D": 0
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
    
    def extract_confluent_tf(self,features):
        
        for zone in features:
            confluents = zone.get('liquidity_confluence',[]) + zone.get('core_confluence',[])
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
            data = {k: v for k, v in zone.items() if k not in ['liquidity_confluence','core_confluence']}
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
            yield {**data}
        
    def extract_confluent_tf_per_zone(self,zone):
        confluents = zone.get('liquidity_confluence',[]) + zone.get('core_confluence',[])
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
        data = {k: v for k, v in zone.items() if k not in ['liquidity_confluence','core_confluence']}
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

    def extract_features_and_labels(self):
        dataset = []
        for zone in self.zones:
            touch_candle = zone.get('touch_candle')
            available_zones = zone.get('available_core',[])+zone.get('available_liquidity',[])
            if touch_candle is None:
                continue
            
            features= {k: v for k, v in zone.items() if k not in ['touch_candle','available_core','available_liquidity']}
            features['candle_volume'] = touch_candle['volume']
            features['candle_open'] = touch_candle['open']
            features['candle_close'] = touch_candle['close']
            features['candle_ema20'] = touch_candle['ema20']
            features['candle_ema50'] = touch_candle['ema50']
            features['candle_rsi'] = touch_candle['rsi']
            features['candle_atr'] = touch_candle['atr']
            features['available_zones'] = available_zones
            self.total_line += len(available_zones)
            dataset.append(features)
        return dataset
    
    def extract_available_zones(self,confluents):
        for zone in confluents:
            availables = zone.get('available_zones', [])
            if not availables:
                continue

            base_data = {k: v for k, v in zone.items() if k != 'available_zones'}

            for a_zone in availables:
                temp_zone = self.extract_confluent_tf_per_zone(a_zone)
                yield {**base_data, **{f'az_{k}': v for k, v in temp_zone.items() if k not in ['available_core','available_liquidity']}}
    
    def extract_label(self,availables):
        for zone in availables:
            target = zone.get('target_zone')
            base_data = {k: v for k, v in zone.items() if k != 'target_zone'}
            if target is not None :
                if target['index'] == zone['az_index']:
                    base_data['is_target'] = 1
            else:
                base_data['is_target'] = 0
            yield {**base_data}

    def to_dataframe(self):
        data = self.extract_features_and_labels()
        data = self.extract_confluent_tf()
        data = self.extract_label()
        df = pd.DataFrame(data)
        return df
    
    def get_dataset_list(self,output_path):
        features = self.extract_features_and_labels()
        confluents = self.extract_confluent_tf(features)
        availables = self.extract_available_zones(confluents)
        data = self.extract_label(availables)
        
        with open(output_path, "w") as f:
            for i, row in enumerate(tqdm(data, desc="Writing to JSONL",total=self.total_line, dynamic_ncols=True)):
                try:
                    f.write(json.dumps(row , default=self.default_json_serializer) + "\n")
                except TypeError as e:
                    print(f"\n🚨 JSON serialization error at row {i}")
                    for k, v in row.items():
                        try:
                            json.dumps(v,default=self.default_json_serializer)  # test if this key's value is serializable
                        except TypeError:
                            print(f"  ❌ Key '{k}' is not serializable. Value: {v} (type: {type(v)})")
                    raise e  
                except ValueError as e:
                    print(f"\n🚨 JSON serialization error at row {i}")
                    for k,v in row.items():
                        try:
                            json.dumps(v,default=self.default_json_serializer)  # test if this key's value is serializable
                        except ValueError:
                            print(f"  ❌ Key '{k}' is not serializable. Value: {v} (type: {type(v)})")
                    raise e
