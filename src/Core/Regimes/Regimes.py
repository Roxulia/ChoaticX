from .registry import get_regime
import asyncio
class Regimes:
    def __init__(self,configs = None):
        self.configs = configs or []
        self.initialize()

    def add(self,data):
        for k,v in self.regimes.items() :
            data = asyncio.run(v.detect(data))
        return data
    
    def initialize(self):
        self.regimes = {}
        for regime in self.configs:
            cls_name = regime['name']
            params = regime['params']
            cls = get_regime(cls_name)
            # print({cls_name : cls})
            if cls is not None:
                self.regimes[cls_name] = cls(**params)
    

