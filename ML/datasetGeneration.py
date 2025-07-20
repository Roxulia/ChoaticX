
import pandas as pd
import numpy as np

class DatasetGenerator:
    def __init__(self,  zones_with_targets):
        
        self.zones = zones_with_targets
        self.dataset = []

    def extract_types_tf_counts(self):
        dataset = []
        for zone in self.dataset:
        # Initialize counts
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
            for t in zone.get('types', []):
                if t in type_counts:
                    type_counts[t] += 1

            # Count timeframes
            for tf in zone.get('timeframes', []):
                if tf in tf_counts:
                    tf_counts[tf] += 1

            # Aggregate zone class
            buyzones = type_counts["Bullish OB"] + type_counts["Bullish FVG"] + type_counts['Buy-Side Liq']
            sellzones = type_counts["Bearish OB"] + type_counts["Bearish FVG"] + type_counts['Sell-Side Liq']

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
    
    def extract_features_and_labels(self):
        dataset = []

        for zone in self.zones:
            touch_candle = zone.get('touch_candle')
            if touch_candle is None:
                continue
            features = {
                'zone_index' : zone['zone_index'],
                'end_index' : zone['end_index'],
                'zone_high': zone['zone_high'],
                'zone_low': zone['zone_low'],
                'zone_width': zone['zone_high'] - zone['zone_low'],
                'types' : zone['types'],
                'timeframes' : zone['timeframes'],
                'distance_to_above' : zone.get('distance_to_nearest_zone_above'),
                'distance_to_below' : zone.get('distance_to_nearest_zone_below'),
                'above_zone' : zone.get('nearest_above_zone'),
                'below_zone' : zone.get('nearest_below_zone'),
                

                # Misc zone features
                'count': zone.get('count'),
                'touch_type': zone.get('touch_type'),

                # Price action
                'close': touch_candle['close'],
                'open': touch_candle['open'],
                'high': touch_candle['high'],
                'low': touch_candle['low'],
                'volume': touch_candle['volume'],

                # TA indicators
                'ema20': touch_candle.get('ema20', 0),
                'ema50': touch_candle.get('ema50', 0),
                'rsi': touch_candle.get('rsi', 0),
                'atr': touch_candle.get('atr', 0),

                # Categorical encoding
                
                'touch_wick': 1 if zone.get('touch_type') == 'wick_touch' else 0,
                'touch_body_inside': 1 if zone.get('touch_type') == 'body_close_inside' else 0
            }
            dataset.append((features))
        self.dataset = dataset
        return dataset

    def to_dataframe(self):
        data = self.extract_features_and_labels()
        data = self.extract_types_tf_counts()
        df = pd.DataFrame(data)
        df = df.drop(columns=['types','timeframes','above_zone','below_zone'])
        df = df.sort_values(by=['end_index'])
        return df
