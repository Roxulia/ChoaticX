from Core.zone_detection import ZoneDetector
from Core.zone_reactions import ZoneReactor
from Core.zone_merge import ZoneMerger
from Core.SignalGeneration import SignalGenerator
from Core.Filter import Filter
from ML.Model import ModelHandler
from ML.transform import DataTransformer
from Data.binanceAPI import BinanceAPI

class SignalService:
    def __init__(self):
        self.api = BinanceAPI()
        #self.model = Model(...)  # Load pretrained model and transformer
        self.model = None
        self.signal_gen = SignalGenerator(models={'entry_model': self.model})

    def get_latest_zones(self):
        df_1h = self.api.get_ohlcv(interval= '1h')
        detector = ZoneDetector(df_1h)
        zones_1h = detector.get_zones()
        df = self.api.get_ohlcv(interval= '4h')
        detector = ZoneDetector(df,'4h')
        zones_4h = detector.get_zones()
        df = self.api.get_ohlcv(interval= '1D')
        detector = ZoneDetector(df,'1D')
        zones_1D = detector.get_zones()
        merger = ZoneMerger(zones_1h+zones_4h+zones_1D)
        zones = merger.merge()
        reactor = ZoneReactor(df_1h, zones)
        zones = reactor.get_zone_reaction()
        zones = merger.getNearbyZone(zones)
        return zones

    def get_current_signals(self):
        df = self.api.get_ohlcv()
        zones = self.get_latest_zones()
        reactor = ZoneReactor(df, zones)
        reaction = reactor.get_last_candle_reaction()
        if not reaction == 'None':
            return self.signal_gen.generate(df.iloc[-1],zones,reaction)
        return 'None'

if __name__ == "__main__" :
    test = SignalService()
    df = test.get_latest_zones()
    print(df[-1])
