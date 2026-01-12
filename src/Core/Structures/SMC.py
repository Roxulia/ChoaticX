from .SMC_Structures.FVG import FVG
from .SMC_Structures.LIQ import LIQ
from .SMC_Structures.OB import OB
from .SMC_Structures.Swings import Swings
from .registry import get_structure,register_structure

@register_structure
class SMC:
    """Combine all detectors"""
    def __init__(self, df , zones = None):
        self.df = df
        self.configs = zones or []
        self.initialize()

    def get_zones(self):
        zones  = []
        for name, structure in self.structures.items():
            detected_zones = structure.detect(inner_func=True)
            zones.extend(detected_zones)

        # return all zones
        return zones
    
    def initialize(self):
        self.structures = {}
        for indicator in self.configs:
            cls_name = indicator['name']
            params = indicator['params']
            cls = get_structure(cls_name)
            print({cls_name : cls})
            if cls is not None:
                self.structures[cls_name] = cls(self.df, **params)