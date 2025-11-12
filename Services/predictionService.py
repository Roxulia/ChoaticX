from ML.dataCleaning import DataCleaner
from ML.Model import ModelHandler
from Core.SignalGeneration import SignalGenerator
from .zoneHandlingService import ZoneHandlingService
from Data.Columns import IgnoreColumns
class PredictionService():
    def __init__(self,symbol,timeframes,threshold=0):
        self.symbol = symbol
        self.threshold = threshold
        self.timeframes = timeframes
        self.zonehandler = ZoneHandlingService(symbol,threshold,timeframes)
        
        self.model_handler = ModelHandler(symbol=symbol,timeframes=timeframes,model_type='xgb')
        self.ignore_cols = IgnoreColumns().predictionModelV1

    def train_process(self):
        self.zonehandler.get_dataset(initial_state=False,for_predict=True)
        self.datacleaner = DataCleaner(self.symbol,self.timeframes)
        self.datacleaner.perform_clean(self.ignore_cols)
        self.model_handler.train()
        self.model_handler.load()
        self.model_handler.test_result()

    def predict(self,data):
        if not data:
            raise Exception("Empty Data")
        use_zones = []
        zone = {
            'touch_from' : data.get('touch_from',None),
            'below_body_size' : data.get('below_body_size', None),
            'below_zone_low': data.get('below_zone_low', None),
            'above_zone_low' : data.get('above_zone_low', None),
            'candle_volume' : data.get('candle_volume', None),
            'zone_low' : data.get('zone_low', None),
            'candle_high' : data.get('candle_high', None),
            'count' : data.get('count', None),
            'below_volume_on_creation' : data.get('below_volume_on_creation', None),
            'volume_on_creation' : data.get('volume_on_creation', None),
            'above_zone_high' : data.get('above_zone_high', None),
            'above_zone_width' : data.get('above_zone_width', None),
            'above_count' : data.get('above_count', None),
            'zone_width' : data.get('zone_width', None),
            'zone_high' : data.get('zone_high', None),
            'above_volume_on_creation' : data.get('above_volume_on_creation', None),
            'zone_type' : data.get('zone_type', None),
            'touch_type' : data.get('touch_type', None),
            'below_zone_width' : data.get('below_zone_width', None),
            'below_zone_high' : data.get('below_zone_high', None),
            'body_size' : data.get('body_size', None),
            'above_type' : data.get('above_type', None),
            'candle_open'  : data.get('candle_open', None),
            'below_duration_between_first_last_touch' : data.get('below_duration_between_first_last_touch', None),
            'below_count' : data.get('below_count', None),
            'below_type' : data.get('below_type', None),
            'distance_to_nearest_zone_below' : data.get('distance_to_nearest_zone_below', None),
            'candle_low' : data.get('candle_low', None),
            'candle_close' : data.get('candle_close', None),
            'distance_to_nearest_zone_above' : data.get('distance_to_nearest_zone_above', None),
            'above_body_size' : data.get('above_body_size', None),
            'duration_between_first_last_touch' : data.get('duration_between_first_last_touch', None),
            'above_duration_between_first_last_touch' : data.get('above_duration_between_first_last_touch', None),
        }
        use_zones.append(zone)
        signal_gen = SignalGenerator([self.model_handler],DataCleaner(self.symbol,self.timeframes),[self.ignore_cols])
        signal = signal_gen.generate(use_zones)
        return signal
    
    def getRequiredColumns(self):
        
        return self.model_handler.getFeatureName()
