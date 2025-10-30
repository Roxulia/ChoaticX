from dataclasses import dataclass,field
from Services.signalService import SignalService

@dataclass
class ServiceData:
    thresholds : dict = {
        "BTCUSDT" : 500,
        "BNBUSDT" : 5,
        "PAXGUSDT": 10,
        "ETHUSDT" : 10,
        "SOLUSDT" : 2
    }