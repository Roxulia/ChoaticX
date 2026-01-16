from .registry import get_structure,list_structures
from Utility import ConfigReader,Logger
from Exceptions.ServiceExceptions import asyncerrorHandling,errorHandling
class Structures:
    def __init__(self,candlestick_data,timeframe = '1h'):
        self.df = candlestick_data
        self.timeframe = timeframe
        self.configs = ConfigReader("config.json").getStructuresConfig()
        self.initialize()

    def initialize(self):
        self.detectors = {}
        for structure in self.configs:
            if structure['enabled'] :
                name = structure['name']
                params = structure['params']
                cls = get_structure(name)
                if cls is not None:
                    self.detectors[name] = cls(self.df,**params)

    @asyncerrorHandling
    async def detect(self):
        Logger.info("Detecting Structures...")
        zones = {}
        for name,detectors in self.detectors.items():
            if name != "ATH" : 
                zones[name] = detectors.get_zones()
        zones["timeframe"] = self.timeframe
        return zones