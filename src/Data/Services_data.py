from dataclasses import dataclass,field

@dataclass
class ServiceData:
    thresholds : dict = field( default_factory= lambda : {
        "BTCUSDT" : 500,
        "BNBUSDT" : 5,
        "PAXGUSDT": 10,
        "ETHUSDT" : 10,
        "SOLUSDT" : 2
    })

    crossOverTypes :list  = field(default_factory= lambda: [
        ('ma_short','ma_long',None,None),
        ('ma_short','ema_long',None,None),
        ('ma_short','ema_short',None,None),
        ('ema_short','ma_long',None,None),
        ('ema_short','ma_short',None,None),
        ('ema_short','ema_long',None,None),
        ('ma_long','ma_short',None,None),
        ('ma_long','ema_short',None,None),
        ('ma_long','ema_long',None,None),
        ('ema_long','ma_short',None,None),
        ('ema_long','ema_short',None,None),
        ('ema_long','ma_long',None,None),
        ('ma_short','ma_long','ema_short',None),
        ('ma_short','ema_long','ema_short',None),
        ('ma_short','ma_long','ema_long',None),
        ('ema_short','ma_long','ma_short',None),
        ('ema_short','ema_long','ma_short',None),
        ('ema_short','ma_long','ema_long',None),
        ('ma_long','ma_short','ema_short',None),
        ('ma_long','ma_short','ema_long',None),
        ('ma_long','ema_short','ema_long',None),
        ('ema_long','ma_short','ema_short',None),
        ('ema_long','ma_short','ma_long',None),
        ('ema_long','ema_short','ma_long',None),
        ('ma_short','ema_short','ma_long','ema_long'),
        ('ema_short','ma_short','ma_long','ema_long'),
        ('ma_long','ema_short','ma_short','ema_long'),
        ('ema_long','ema_short','ma_long','ma_short'),
    ])