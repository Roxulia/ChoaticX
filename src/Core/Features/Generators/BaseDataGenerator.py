from Core import *
from Core.Structures.registry import list_structures
from Core.Features.meta_registry import FEATURE_META_REGISTRY
from Market.Binance.rest import  BinanceRestAPI
from Exceptions import asyncerrorHandling,errorHandling
from Utility import ConfigReader, Logger

class BaseDataGenerator:
    
    def __init__(self):
        self.binance_api = BinanceRestAPI()
        self.config = ConfigReader("config.json")
        self.symbol = self.config.getSymbol()
        self.interval = self.config.getTimeframe()
        self.lookback = self.config.getLookbackPeriod()

    @asyncerrorHandling
    async def getRawCandleData(self):
        candles = await self.binance_api.get_ohlcv(self.symbol,self.interval,self.lookback)
        return candles
    
    @asyncerrorHandling
    async def getCandleDataWithIndicators(self,candles):
        indicators = TA(self.config.getIndicatorsConfig())
        data = await indicators.add(candles)
        return data
    
    @asyncerrorHandling
    async def getZones(self,candles):

        structures = Structures(candles, self.interval)
        data = await structures.detect()

        structure_set = set(list_structures())  # faster lookup
        response_data = []

        for name, structure_values in data.items():
            if name not in structure_set:
                continue

            for zone_name, zone_values in structure_values.items():
                meta = FEATURE_META_REGISTRY.get_meta(zone_name) or {}
                if meta.get("is_zone", True):
                    response_data.extend(zone_values)

        return response_data
    
    @asyncerrorHandling
    async def getStructures(self,candles):
        structures = Structures(candles, self.interval)
        data = await structures.detect()

        return data
    
    @asyncerrorHandling
    async def getRegimes(self,candles,context):
        if context is None:
            context = {}
        regimes = Regimes(self.config.getRegimesConfig())
        data = await regimes.add(candles,context)

        return data

    @asyncerrorHandling
    async def getCandleFeatures(self):
        candles = await self.getRawCandleData()
        data = await self.getCandleDataWithIndicators(candles)
        structures_data = None
        if(self.config.getConfig().get("Structure_contain_TA", False)):
            structures_data = await self.getStructures(data)
        else:
            structures_data = await self.getStructures(candles)
        data = await self.getRegimes(data,structures_data)
        return data
    
    @asyncerrorHandling
    async def getZonesByInterval(self,interval):
        if interval is None:
            interval = self.interval    
        candles = await self.binance_api.get_ohlcv(self.symbol,interval,self.lookback)
        zones = await self.getZones(candles)
        return zones