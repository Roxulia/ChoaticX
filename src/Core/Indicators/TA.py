from .registry import get_indicator
from Data.Services_data import ServiceData
class TA:
    def __init__(self,configs = None):
        self.configs = configs or []
        self.initialize()

    def add(self,data):
        for k,v in self.indicators.items() :
            data = v.add(data)
        return data
    
    def initialize(self):
        self.indicators = {}
        for indicator in self.configs:
            cls_name = indicator['name']
            params = indicator['params']
            cls = get_indicator(cls_name)
            # print({cls_name : cls})
            if cls is not None:
                self.indicators[cls_name] = cls(**params)

    

