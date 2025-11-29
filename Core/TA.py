from .TechnicalAnalysis.ATR import ATR
from .TechnicalAnalysis.BollingerBands import BollingerBands
from .TechnicalAnalysis.MA import MovingAverage
from .TechnicalAnalysis.EMA import EMA
from .TechnicalAnalysis.RSI import RSI
from .TechnicalAnalysis.RollingRegression import RollingRegression
from Data.Services_data import ServiceData
class TA:
    def __init__(self):
        self.ATR = ATR()
        self.BollingerBands = BollingerBands()
        self.MA = MovingAverage()
        self.EMA = EMA()
        self.RSI = RSI()
        self.CrossOverTypes = ServiceData().crossOverTypes

    def add(self,data):
        data = self.ATR.add(data)
        data = self.MA.add(data)
        data = self.EMA.add(data)
        data = self.RSI.add(data)
        data = self.BollingerBands.add(data)
        return data
    
    def add_RollingRegression(self,data,market_data):
        RR = RollingRegression(data,market_data)
        return RR.AddRegressionValues()
    
    async def detectCrossOvers(self,data):
        MA_cross = await self.MA.detectCrossOver(data)
        EMA_cross = await self.EMA.detectCrossOver(data)
        BB_cross = await self.BollingerBands.detectCrossOver(data)
        zones = MA_cross+EMA_cross+BB_cross
        return sorted(zones, key=lambda z: z['timestamp'])

    async def detectMaLinesCrossOvers(self,data):
        crossovers = []
        timestamps = data["timestamp"]

        for i in range(1, len(data)):
            for a, b , c ,d in self.CrossOverTypes:
                prev_rsi , curr_rsi = data['rsi'].iloc[i-1],data['rsi'].iloc[i]
                prev_a, prev_b = data[a].iloc[i-1], data[b].iloc[i-1]
                curr_a, curr_b = data[a].iloc[i], data[b].iloc[i]
                if not (d is None and c is None):
                    prev_c, prev_d = data[c].iloc[i-1], data[d].iloc[i-1]
                    curr_c, curr_d = data[c].iloc[i], data[d].iloc[i]
                    if (prev_a > prev_b and curr_a < curr_b) and (prev_a > prev_c and curr_a < curr_c) and (prev_a > prev_d and curr_a < curr_d):
                        crossovers.append({
                            "timestamp": timestamps.iloc[i],
                            "type": f"{a}_dip_{b}_{c}_{d}",
                            "rsi_change" : curr_rsi - prev_rsi,
                            "ema_long" : data['ema_long'].iloc[i],
                            "ma_long" : data['ma_long'].iloc[i],
                            "ema_short" : data['ema_short'].iloc[i],
                            "ma_short" : data['ma_short'].iloc[i],
                    })
                elif c is not None:
                    prev_c,curr_c = data[c].iloc[i-1],data[c].iloc[i]
                    if (prev_a > prev_b and curr_a < curr_b) and (prev_a > prev_c and curr_a < curr_c) :
                        crossovers.append({
                            "timestamp": timestamps.iloc[i],
                            "type": f"{a}_dip_{b}_{c}",
                            "rsi_change" : curr_rsi - prev_rsi,
                            "ema_long" : data['ema_long'].iloc[i],
                            "ma_long" : data['ma_long'].iloc[i],
                            "ema_short" : data['ema_short'].iloc[i],
                            "ma_short" : data['ma_short'].iloc[i],
                    })
                else:
                    # Detect crossover (A dips below B)
                    if prev_a > prev_b and curr_a < curr_b:
                        crossovers.append({
                            "timestamp": timestamps.iloc[i],
                            "type": f"{a}_dip_{b}",
                            "rsi_change" : curr_rsi - prev_rsi,
                            "ema_long" : data['ema_long'].iloc[i],
                            "ma_long" : data['ma_long'].iloc[i],
                            "ema_short" : data['ema_short'].iloc[i],
                            "ma_short" : data['ma_short'].iloc[i],
                        })
        return crossovers
    

