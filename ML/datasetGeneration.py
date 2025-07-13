
import pandas as pd
import numpy as np

class DatasetGenerator:
    def __init__(self, candles, zones_with_targets):
        self.candles = candles
        self.zones = zones_with_targets

    def extract_features_and_labels(self):
        dataset = []

        for zone in self.zones:
            touch_candle = zone.get('touch_candle')
            target_zone = zone.get('target_zone')
            if touch_candle is None:
                continue  # skip if no touch happened
            zone_types = zone.get('types',[])
            timeframes = zone.get('timeframes',[])
            bull_ob = 0
            bull_fvg = 0
            bear_ob = 0
            bear_fvg = 0
            min1 = 0
            min3 = 0
            min5 = 0
            min15 = 0
            h1 =0
            h4 = 0
            d1 = 0
            for a in zone_types:
                if a == "Bullish OB" :
                    bull_ob +=1
                elif a == "Bullish FVG" :
                    bull_fvg += 1
                elif a == "Bearish OB":
                    bear_ob += 1
                elif a == "Bearish FVG":
                    bear_fvg += 1

            for t in timeframes:
                if t == "1min" :
                    min1 +=1
                elif t == "3min" :
                    min3 += 1
                elif t == "5min":
                    min5 += 1
                elif t == "15min":
                    min15 += 1
                elif t == "1h" :
                    h1 += 1
                elif t == "4h" :
                    h4 += 1
                elif t == "1D" :
                    d1 += 1

            # --- Features ---
            features = {
                'zone_high': zone['zone_high'],
                'zone_low': zone['zone_low'],
                'zone_width': zone['zone_high'] - zone['zone_low'],
                'bullish_OB_count' : bull_ob, 
                'bullish_FVG_count' : bull_fvg, 
                'bearish_OB_count' : bear_ob, 
                'bearish_FVG_count' : bear_fvg, 
                '1min_count' : min1,
                '3min_count' : min3,
                '5min_count' : min5,
                '15min_count' : min15,
                '1h_count' : h1,
                '4h_count' : h4,
                '1D_count' : d1,
                'touch_type': zone.get('touch_type'),
                'count': zone.get('count'),
                'confluent_count' : len(zone.get('liquidity_confluence')),
                # Candle TA features (assumes TA columns present in candles DataFrame)
                'close': touch_candle['close'],
                'open': touch_candle['open'],
                'high': touch_candle['high'],
                'low': touch_candle['low'],
                'volume': touch_candle['volume'],
                'ema20': touch_candle.get('ema20', 0),
                'ema50': touch_candle.get('ema50', 0),
                'rsi': touch_candle.get('rsi', 0),
                'atr': touch_candle.get('atr', 0)
            }
            buyzones = bull_fvg + bull_ob
            sellzones = bear_fvg + bear_ob
            # Encode categorical features manually
            features['is_buy_zone'] = 1 if buyzones > sellzones else 0
            features['touch_wick'] = 1 if features['touch_type'] == 'wick_touch' else 0
            features['touch_body_inside'] = 1 if features['touch_type'] == 'body_close_inside' else 0

            # --- Label ---
            # Binary classification: 1 if there is a valid target zone touched after, else 0
            label = 1 if target_zone is not None else 0

            dataset.append((features, label))

        return dataset

    def to_dataframe(self):
        data = self.extract_features_and_labels()
        features = [x[0] for x in data]
        labels = [x[1] for x in data]
        df = pd.DataFrame(features)
        df['label'] = labels
        return df
