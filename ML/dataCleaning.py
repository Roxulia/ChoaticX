from sklearn.preprocessing import StandardScaler
import pandas as pd
import numpy as np
import json
from tqdm import tqdm
from .dataSplitting import DataSplit
from Utility.MemoryUsage import MemoryUsage as mu
from Data.Paths import Paths
class DataCleaner:
    def __init__(self,timeframes = ['1h','4h','1D'],total_line=1000,batch_size=1000):
        self.Paths = Paths()
        self.total_line = np.ceil(total_line / batch_size)
        self.datasplit =  DataSplit(random_state=42,shuffle=False,train_size=0.6,test_size=0.4)
        self.batch_size = batch_size
        self.below_above_col = ['distance_to_above','distance_to_below',
                                'below_zone_high','below_zone_low','below_zone_width','below_zone_count',
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
        self.zone_types = [
            'Bearish FVG',
            'Bullish FVG',
            'Bearish OB',
            'Bullish OB' ,
            'Buy-Side Liq' ,
            'Sell-Side Liq' ,
            'ATH'
        ]
        self.timeframes = [
            '1min',
            '3min',
            '5min',
            '15min',
            '1h',
            '4h',
            '1D'
        ]
        self.columns = self.load_columns(timeframes)
        self.columns_to_remove = ['swept_index','end_index',
                                  'touch_index','level','az_touch_index','az_touch_type','az_swept_index',
                                  'az_end_index','az_level','az_duration_between_first_last_touch',
                                  'above_touch_type','above_touch_index','above_level',
                                  'above_swept_index','above_end_index',
                                  'below_touch_type','below_touch_index','below_level',
                                  'below_swept_index','below_end_index',
                                  'index','az_index','above_index','below_index',
                                  'timestamp','az_timestamp',
                                  'candle_timestamp','touch_time','swept_time',
                                  'az_touch_time','above_zone_touch_time','below_zone_touch_time',
                                  'az_swept_time','above_zone_swept_time','below_zone_swept_time',
                                  'above_touch_time','below_touch_time','above_swept_time','below_swept_time','above_timestamp','below_timestamp',
                                  'time_frame','az_time_frame','above_time_frame','below_time_frame',
                                  
                                  ]

    
    def to_dataframe(self,ignore_cols=[]):
        batch = []
        for i,record in enumerate(self.get_data_from_file()):
            batch.append(record)
            if len(batch) == self.batch_size:
                df =  pd.DataFrame(batch)
                df = df.reindex(columns=self.columns, fill_value=pd.NA)
                df = self.remove_columns(df)
                df = df.dropna(subset=['target'])
                df = self.transformCategoryTypes(df)
                df = self.fillNaN(df)
                df = self.makeValuesRatioByZonePrice(df)
                df = df.drop(columns=[col for col in ignore_cols if col in df.columns])
                df = df.astype('float32')
                batch = []
                yield df
                
        if batch:
            
            df =  pd.DataFrame(batch)
            df = df.reindex(columns=self.columns, fill_value=pd.NA)
            df = self.remove_columns(df)
            
            df = df.dropna(subset=['target'])
            df = self.transformCategoryTypes(df)
            df = self.fillNaN(df)
            df = self.makeValuesRatioByZonePrice(df)
            df = df.drop(columns=[col for col in ignore_cols if col in df.columns])
            df = df.astype('float32')

            yield df
    
    def get_data_from_file(self):
        with open(self.Paths.raw_data,'r') as f:
            for line in f:
                data = json.loads(line)
                yield data

    @mu.log_memory
    def perform_clean(self,ignore_cols = []):
        
        header = True
        for i,df in tqdm(enumerate(self.to_dataframe(ignore_cols)),desc='Performing Data Cleaning',total=self.total_line,dynamic_ncols=True):
            train,test = self.datasplit.split(df)
            if header:
                train.to_csv(self.Paths.train_data, mode='w', header=True, index=False)
                test.to_csv(self.Paths.test_data,mode='w', header=True, index=False)
                header = False
            else:
                train.to_csv(self.Paths.train_data, mode='a', header=False, index=False)
                test.to_csv(self.Paths.test_data,mode='a', header=False, index=False)

        return int(np.ceil(self.total_line*0.7))
            

    def transformCategoryTypes(self,df):
        columns = list(df.columns)
        if 'touch_type' in columns : 
            df['touch_type'] = df['touch_type'].apply(lambda x : self.touch_types[x] if x is not None else 0)
        if 'type' in columns : 
            df['type'] = df['type'].apply(lambda x : self.zone_types.index(x)+1 if x  in self.zone_types else 0)
        if 'above_type' in columns : 
            df['above_type'] = df['above_type'].apply(lambda x : self.zone_types.index(x)+1 if not pd.isna(x) and x in self.zone_types else 0)
        if 'below_type' in columns : 
            df['below_type'] = df['below_type'].apply(lambda x : self.zone_types.index(x)+1 if not pd.isna(x) and x in self.zone_types else 0)
        
        return df

    def fillNaN(self,df):
        columns = list(df.columns)
        valid_cols = [col for col in self.below_above_col if col in columns]
        df[valid_cols] = df[valid_cols].fillna(0)
        df[columns] = df[columns].fillna(0.0)
        df.replace([float('inf'), float('-inf')], 0, inplace=True)
        return df
    
    def checkColandCalculate(self,column_names,df):
        columns = list(df.columns)
        if column_names in columns:
            avg =  (df[column_names[0]] + df[column_names[1]])/2
            return df[column_names[2]] / avg
        return None

    def makeValuesRatioByZonePrice(self,df):
        columns = list(df.columns)
        df['ema_20_by_price'] = self.checkColandCalculate(['zone_high','zone_low','ema_20'],df)
        df['ema_50_by_price'] = self.checkColandCalculate(['zone_high','zone_low','ema_50'],df)
        df['above_ema_20_by_price'] = self.checkColandCalculate(['above_zone_high','above_zone_low','above_ema_20'],df)
        df['above_ema_50_by_price'] = self.checkColandCalculate(['above_zone_high','above_zone_low','above_ema_50'],df)
        df['below_ema_20_by_price'] = self.checkColandCalculate(['below_zone_high','below_zone_low','below_ema_20'],df)
        df['below_ema_50_by_price'] = self.checkColandCalculate(['below_zone_high','below_zone_low','below_ema_50'],df)
        df['candle_ema_20_by_price'] = self.checkColandCalculate(['candle_open','candle_close','candle_ema20'],df)
        df['candle_ema_50_by_price'] = self.checkColandCalculate(['candle_open','candle_close','candle_ema50'],df)
        calculated_cols = ['ema_20','ema_50','above_ema_20','above_ema_50','below_ema_20','below_ema_50','candle_ema20','candle_ema50']
        
        df = df.drop(columns =[col for col in calculated_cols if col in columns])
        return df

    
    def remove_columns(self,df):
        columns = list(df.columns)
        df_new = df.drop(columns=[col for col in self.columns_to_remove if col in columns])
        return df_new

    def preprocess_input(self,input,ignore_cols=[]):
        df =  pd.DataFrame(input)
        df = df.reindex(columns=self.columns, fill_value=pd.NA)
        df = self.remove_columns(df)
        df = self.transformCategoryTypes(df)
        df = self.fillNaN(df)
        df = self.makeValuesRatioByZonePrice(df)
        df = df.drop(columns=[col for col in ignore_cols if col in df.columns])
        df = df.astype('float32')
        columns = ['is_target','target']
        return df.drop(columns=[col for col in columns if col in df.columns])

    def load_columns(self,timeframes):
        filename = "_".join(timeframes)
        path = f"{self.Paths.columns_list}/{filename}.json"
        with open(path, "r") as f:
            columns = json.load(f)
        return columns