from .zoneHandlingService import ZoneHandlingService
from Core.TA import TA
from Utility.UtilityClass import UtilityFunctions as utility
import asyncio
class predictionWithTA:
    def __init__(self,symbol,timeframes,threshold=0):
        self.symbol = symbol
        self.threshold = threshold
        self.timeframes = timeframes
        self.zonehandler = ZoneHandlingService(symbol,threshold,timeframes)
        self.ta = TA()

    async def prepareData(self):
        base_zones = await self.zonehandler.get_zones(self.timeframes[0],self.zonehandler.lookback)
        crosses_overs = await self.ta.detectCrossOvers(self.zonehandler.based_candles)
        data = []
        for zone in base_zones:
            touch_time = zone.get('touch_time',None)
            if touch_time:
                last_cross = utility.get_last_cross_before(crosses_overs,touch_time)
                next_candles = self.zonehandler.based_candles.loc[self.zonehandler.based_candles['timestamp'] > touch_time]
                