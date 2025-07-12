
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

            # --- Features ---
            features = {
                'zone_high': zone['zone_high'],
                'zone_low': zone['zone_low'],
                'zone_width': zone['zone_high'] - zone['zone_low'],
                'zone_type': zone.get('types', [zone.get('type')])[0],
                'touch_type': zone.get('touch_type'),
                'timeframe': zone.get('timeframes', [zone.get('time_frame')])[0],
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

            # Encode categorical features manually
            features['is_buy_zone'] = 1 if features['zone_type'] in ['Demand', 'Buy OB', 'Buy Side Liq'] else 0
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
