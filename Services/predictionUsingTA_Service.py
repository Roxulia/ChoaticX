from .zoneHandlingService import ZoneHandlingService
from Core.TA import TA
from Utility.UtilityClass import UtilityFunctions as utility
from Data.Paths import Paths
import asyncio,os,json
class predictionWithTA:
    def __init__(self,symbol,timeframes,threshold=0):
        self.symbol = symbol
        self.threshold = threshold
        self.timeframes = timeframes
        self.zonehandler = ZoneHandlingService(symbol,threshold,timeframes)
        self.ta = TA()
        self.paths = Paths()
        ma_crossover_file = "_".join(self.timeframes)
        base = os.path.dirname(os.path.dirname(__file__))
        self.ma_crossover_path = f'{base}/{self.paths.ma_crossover_data}/{self.symbol}_{ma_crossover_file}.json'

    async def prepareData(self,analysis = False):
        candles_df = await self.zonehandler.getBasedCandle()
        crossovers = await self.ta.detectMaLinesCrossOvers(candles_df)
        if not analysis:
            self.storeCrossOver(crossovers[-1])
        labeled = []
        max_size = len(crossovers)

        for i in range(max_size):

            time_stamp = crossovers[i]["timestamp"]
            type = crossovers[i]["type"]

            # Filter candles for this segment
            candles = candles_df.loc[candles_df["timestamp"] >= time_stamp]

            if i + 1 < max_size:
                next_ts = crossovers[i + 1]["timestamp"]
                candles = candles.loc[candles["timestamp"] <= next_ts]

            # Identify start / end candle
            if candles.empty:
                labeled.append({
                    "timestamp": time_stamp,
                    "type": type,
                    "label": None,
                    "percent_move": None,
                    "movement_type": None
                })
                continue

            start_candle = candles.iloc[0]
            end_candle = candles.iloc[-1]

            # Original label logic
            label = (
                start_candle["high"] < end_candle["low"]
                if len(candles) > 1
                else None
            )

            # Price movement
            price_move = end_candle["close"] - start_candle["open"]
            percent_move = (price_move / start_candle["open"]) * 100

            
            labeled.append({
                **crossovers[i],
                "label": label,
                "percent_move": percent_move,
            })
        
        return labeled[:-1]

    def storeCrossOver(self,crossover):
        try:
            with open(self.ma_crossover_path, 'w') as f:
                json.dump(crossover, f, indent=4,default=utility.default_json_serializer)
            return True
        except:
            print("File Storage Error")
            return False

    def readFromStorage(self):
        if not os.path.exists(self.ma_crossover_path):
            return None

        with open(self.ma_crossover_path, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return None

    async def updateCrossOver(self):
        candles = await self.zonehandler.getBasedCandle(limit=True)
        crossovers = await self.ta.detectMaLinesCrossOvers(candles)
        self.storeCrossOver(crossovers[-1])

                