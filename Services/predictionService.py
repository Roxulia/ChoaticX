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

    async def predict(self,data):
        if not data:
            raise Exception("Empty Data")
        use_zones = []
        use_zones.append(data)
        signal_gen = SignalGenerator([self.model_handler],DataCleaner(self.symbol,self.timeframes),[self.ignore_cols])
        signal = await signal_gen.generate(use_zones)
        return signal
    
    def getRequiredColumns(self):
        
        return self.model_handler.getFeatureName()
