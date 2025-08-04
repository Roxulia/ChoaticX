from sklearn.preprocessing import StandardScaler
import pandas as pd
import numpy as np
import json
from tqdm import tqdm
class DataCleaner:
    def __init__(self,data_path,batch_size,total_line,csv_path='dataset.csv'):
        self.scaler = StandardScaler()
        self.data_path = data_path
        self.total_line = total_line
        self.csv_path = csv_path    
        self.batch_size = batch_size
        self.below_above_col = ['below_zone_high','below_zone_low','below_zone_width','below_zone_count',
                                'above_zone_high','above_zone_low','above_zone_width','above_zone_count',
                                'above_is_buy_zone','above_count_BuOB','above_count_BrOB','above_count_BuFVG','above_count_BrFVG','above_count_BuLiq','above_count_BrLiq',
                                'above_1min_count','above_3min_count','above_5min_count','above_15min_count','above_1h_count','above_4h_count','above_1D_count',
                                'below_is_buy_zone','below_count_BuOB','below_count_BrOB','below_count_BuFVG','below_count_BrFVG','below_count_BuLiq','below_count_BrLiq',
                                'below_1min_count','below_3min_count','below_5min_count','below_15min_count','below_1h_count','below_4h_count','below_1D_count']
        self.touch_types = {
            'body_close_inside' : 1,
            'engulf' : 2,
            'body_close_above' : 3,
            'body_close_below' : 4,
            'wick_touch' : 5
        }
        self.zone_types = {
            'Bearish FVG' : 1,
            'Bullish FVG' : 2,
            'Bearish OB' : 3,
            'Bullish OB' : 4,
            'Buy-Side Liq' : 5,
            'Sell-Side Liq' : 6
        }
        self.timeframes = {
            '1min' : 1,
            '3min' : 2,
            '5min' : 3,
            '15min': 4,
            '1h'   : 5,
            '4h'   : 6,
            '1D'   : 7
        }
        self.columns = [
            "index", "type", "ema 20", "ema 50", "atr", "rsi", "atr_mean", "zone_high", "zone_low", "zone_width",
            "body_size", "wick_ratio", "volume_on_creation", "avg_volume_past_5", "prev_volatility_5", "momentum_5",
            "touch_index", "time_frame", "touch_type", "candle_volume", "candle_open", "candle_close",
            "candle_ema20", "candle_ema50", "candle_rsi", "candle_atr", "conf_is_buy_zone",
            "conf_count_BuOB", "conf_count_BrOB", "conf_count_BuFVG", "conf_count_BrFVG", "conf_count_BuLiq",
            "conf_count_BrLiq", "conf_1min_count", "conf_3min_count", "conf_5min_count", "conf_15min_count",
            "conf_1h_count", "conf_4h_count", "conf_1D_count", "is_target", "level", "count", "end_index",
            "swept_index", "liquidity_height", "equal_level_deviation", "avg_volume_around_zone",
            "duration_between_first_last_touch", "avg_swing_strength", "avg_ema_20", "avg_ema_50", "avg_rsi",
            "avg_atr", "avg_atr_mean", "az_index", "az_type", "az_ema 20", "az_ema 50", "az_atr",
            "az_rsi", "az_atr_mean", "az_zone_high", "az_zone_low", "az_zone_width", "az_body_size", "az_wick_ratio",
            "az_volume_on_creation", "az_avg_volume_past_5", "az_prev_volatility_5", "az_momentum_5", "az_time_frame",
            "az_conf_is_buy_zone", "az_conf_count_BuOB", "az_conf_count_BrOB", "az_conf_count_BuFVG",
            "az_conf_count_BrFVG", "az_conf_count_BuLiq", "az_conf_count_BrLiq", "az_conf_1min_count",
            "az_conf_3min_count", "az_conf_5min_count", "az_conf_15min_count", "az_conf_1h_count",
            "az_conf_4h_count", "az_conf_1D_count", "az_level", "az_count", "az_end_index",
            "az_swept_index", "az_liquidity_height", "az_equal_level_deviation", "az_avg_volume_around_zone",
            "az_duration_between_first_last_touch", "az_avg_swing_strength", "az_avg_ema_20", "az_avg_ema_50",
            "az_avg_rsi", "az_avg_atr", "az_avg_atr_mean"
        ]

    
    def to_dataframe(self):
        batch = []
        for i,record in enumerate(self.get_data_from_file()):
            batch.append(record)
            if len(batch) == self.batch_size:
                df =  pd.DataFrame(batch)
                for col in self.columns:
                    if col not in df.columns:
                        df[col] = pd.NA
                df = df[self.columns]
                df = self.remove_untouched(df)
                df = self.remove_columns(df)
                df = self.transformCategoryTypes(df)
                
                yield df
                batch = []
        if batch:
            df =  pd.DataFrame(batch)
            for col in self.columns:
                if col not in df.columns:
                    df[col] = pd.NA
            df = df[self.columns]
            df = self.remove_untouched(df)
            df = self.remove_columns(df)
            df = self.transformCategoryTypes(df)
            
            yield df
    
    def get_data_from_file(self):
        with open(self.data_path,'r') as f:
            for line in f:
                data = json.loads(line)
                yield data

    def perform_clean(self):
        is_first = True
        for i,df in tqdm(enumerate(self.to_dataframe()),desc='Performing Data Cleaning'):
            df.to_csv(self.csv_path, mode='a', header=is_first, index=False)
            is_first = False

    def transformCategoryTypes(self,df):
        columns = list(df.columns)
        if 'touch_type' in columns : 
            df['touch_type'] = df['touch_type'].apply(lambda x : self.touch_types[x])
        if 'type' in columns : 
            df['type'] = df['type'].apply(lambda x : self.zone_types[x])
        if 'time_frame' in columns : 
            df['time_frame'] = df['time_frame'].apply(lambda x : self.timeframes[x])
        if 'az_type' in columns : 
            df['az_type'] = df['az_type'].apply(lambda x : self.zone_types[x])
        if 'az_time_frame' in columns : 
            df['az_time_frame'] = df['az_time_frame'].apply(lambda x : self.timeframes[x])
        return df

    def fillNaN(self,df):
        df['distance_to_above'] = df['distance_to_above'].fillna(0)
        df['distance_to_below'] = df['distance_to_below'].fillna(0)
        df[self.below_above_col] = df[self.below_above_col].fillna(0)
        df.replace([float('inf'), float('-inf')], 0, inplace=True)
        return df
    
    def remove_untouched(self,df):
        df = df.dropna(subset = ['touch_type'])
        return df

    def remove_columns(self,df):
        df_new = df.drop(columns=[col for col in ['az_touch_index','az_touch_type'] if col in df.columns])
        return df_new


    def fit_transform(self, df):
        X = df.drop('label', axis=1)
        y = df['label']
        X_scaled = self.scaler.fit_transform(X)
        return X_scaled, y

    def transform(self, df):
        X = df.drop('label', axis=1)
        return self.scaler.transform(X)
