
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
                continue

            # Initialize counts
            type_counts = {
                "Bullish OB": 0,
                "Bullish FVG": 0,
                "Bearish OB": 0,
                "Bearish FVG": 0
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
            buyzones = type_counts["Bullish OB"] + type_counts["Bullish FVG"]
            sellzones = type_counts["Bearish OB"] + type_counts["Bearish FVG"]

            features = {
                'zone_high': zone['zone_high'],
                'zone_low': zone['zone_low'],
                'zone_width': zone['zone_high'] - zone['zone_low'],

                # Type counts
                'bullish_OB_count': type_counts["Bullish OB"],
                'bullish_FVG_count': type_counts["Bullish FVG"],
                'bearish_OB_count': type_counts["Bearish OB"],
                'bearish_FVG_count': type_counts["Bearish FVG"],

                # Timeframe counts
                '1min_count': tf_counts["1min"],
                '3min_count': tf_counts["3min"],
                '5min_count': tf_counts["5min"],
                '15min_count': tf_counts["15min"],
                '1h_count': tf_counts["1h"],
                '4h_count': tf_counts["4h"],
                '1D_count': tf_counts["1D"],

                # Misc zone features
                'count': zone.get('count'),
                'confluent_count': len(zone.get('liquidity_confluence', [])),
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
                'is_buy_zone': 1 if buyzones > sellzones else 0,
                'touch_wick': 1 if zone.get('touch_type') == 'wick_touch' else 0,
                'touch_body_inside': 1 if zone.get('touch_type') == 'body_close_inside' else 0
            }

            # Label: 1 if price reached another target zone, else 0
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
