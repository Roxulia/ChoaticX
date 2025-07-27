from sklearn.preprocessing import StandardScaler
import pandas as pd
import numpy as np

class DataCleaner:
    def __init__(self,zone_data : pd.DataFrame):
        self.scaler = StandardScaler()
        self.zoneDataset = zone_data
        self.below_above_col = ['below_zone_high','below_zone_low','below_zone_width','below_zone_count',
                                'above_zone_high','above_zone_low','above_zone_width','above_zone_count',
                                'above_is_buy_zone','above_count_BuOB','above_count_BrOB','above_count_BuFVG','above_count_BrFVG','above_count_BuLiq','above_count_BrLiq',
                                'above_1min_count','above_3min_count','above_5min_count','above_15min_count','above_1h_count','above_4h_count','above_1D_count',
                                'below_is_buy_zone','below_count_BuOB','below_count_BrOB','below_count_BuFVG','below_count_BrFVG','below_count_BuLiq','below_count_BrLiq',
                                'below_1min_count','below_3min_count','below_5min_count','below_15min_count','below_1h_count','below_4h_count','below_1D_count']

    def transformTouchType(self):
        touchType = list(self.zoneDataset['touch_type'].unique())
        self.zoneDataset['touch_type'] = self.zoneDataset['touch_type'].apply(lambda x : touchType.index(x))

    def fillNaN(self):
        self.zoneDataset['distance_to_above'] = self.zoneDataset['distance_to_above'].fillna(0)
        self.zoneDataset['distance_to_below'] = self.zoneDataset['distance_to_below'].fillna(0)
        self.zoneDataset[self.below_above_col] = self.zoneDataset[self.below_above_col].fillna(0)
        self.zoneDataset.replace([float('inf'), float('-inf')], 0, inplace=True)


    def fit_transform(self, df):
        X = df.drop('label', axis=1)
        y = df['label']
        X_scaled = self.scaler.fit_transform(X)
        return X_scaled, y

    def transform(self, df):
        X = df.drop('label', axis=1)
        return self.scaler.transform(X)
