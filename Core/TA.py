from TechnicalAnalysis.ATR import ATR
from TechnicalAnalysis.BollingerBands import BollingerBands
from TechnicalAnalysis.MA import MovingAverage
from TechnicalAnalysis.EMA import EMA
from TechnicalAnalysis.RSI import RSI

class TA:
    def __init__(self,candle_data,symbol):
        self.candle_data = candle_data
        self.symbol = symbol
        self.ATR = ATR()
        self.BollingerBands = BollingerBands()
        self.MA = MovingAverage()
        self.EMA = EMA()
        self.RSI = RSI()

    def add(self):
        data = self.ATR.add(self.candle_data)
        data = self.MA.add(data)
        data = self.EMA.add(data)
        data = self.RSI.add(data)
        data = self.BollingerBands.add(data)
        return data

