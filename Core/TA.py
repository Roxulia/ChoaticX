from .TechnicalAnalysis.ATR import ATR
from .TechnicalAnalysis.BollingerBands import BollingerBands
from .TechnicalAnalysis.MA import MovingAverage
from .TechnicalAnalysis.EMA import EMA
from .TechnicalAnalysis.RSI import RSI
from .TechnicalAnalysis.RollingRegression import RollingRegression

class TA:
    def __init__(self,candle_data):
        self.ATR = ATR()
        self.BollingerBands = BollingerBands()
        self.MA = MovingAverage()
        self.EMA = EMA()
        self.RSI = RSI()

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
    
    def detectCrossOvers(self,data):
        MA_cross = self.MA.detectCrossOver(data)
        EMA_cross = self.EMA.detectCrossOver(data)
        BB_cross = self.BollingerBands.detectCrossOver(data)
        zones = MA_cross+EMA_cross+BB_cross
        return zones.sort(key='timestamp')

