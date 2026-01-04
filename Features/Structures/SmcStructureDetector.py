from .SMC_Structures.FVG import FVG
from .SMC_Structures.LIQ import LIQ
from .SMC_Structures.OB import OB
from .SMC_Structures.Swings import Swings
from ..registry import register_feature

@register_feature
class SMCStructureDetector:
    """Combine all detectors"""
    def __init__(self, df, timeframe="1h"):
        self.df = df
        self.timeframe = timeframe

    def get_zones(self):
        # 1️⃣ Detect Swings first
        swing_detector = Swings(self.df, self.timeframe)
        swings = swing_detector.detect()

        # 2️⃣ FVG
        fvg_detector = FVG(self.df, self.timeframe)
        fvg_zones = fvg_detector.detect()

        # 3️⃣ OB
        ob_detector = OB(self.df, self.timeframe)
        ob_zones = ob_detector.detect()

        # 4️⃣ Liquidity Zones
        liq_detector = LIQ(self.df, self.timeframe)
        liq_zones = liq_detector.detect(swings=swings)

        # return all zones
        return ob_zones + liq_zones  + fvg_zones 