from .BaseModel import BaseModel
from ..DB import MySQLDB as DB
class OB(BaseModel):
    table = 'ob_zones'
    columns = {
        'id' : 'BIGINT AUTO_INCREMENT PRIMARY KEY',
        'timestamp' : 'TIMESTAMP UNIQUE',
        'zone_type':'VARCHAR(30)',
        'time_frame':'VARCHAR(5)',
        'zone_high':'FLOAT',
        'zone_low': 'FLOAT',
        'zone_width' : 'FLOAT',
        'ema_20' : 'FLOAT',
        'ema_50' : 'FLOAT',
        'atr': 'FLOAT',
        'atr_mean' : 'FLOAT',
        'rsi' : 'FLOAT',
        'zone_width': 'FLOAT',
        'body_size': 'FLOAT',
        'wick_ratio': 'FLOAT',
        'volume_on_creation': 'FLOAT',
        'avg_volume_past_5': 'FLOAT',
        'prev_volatility_5': 'FLOAT',
        'momentum_5': 'FLOAT',
        'touch_type' : 'VARCHAR(20)',
        'touch_candle' : 'VARCHAR(20)',
        'conf_is_buy_zone' : 'INTEGER',
        'conf_count_BuOB' : 'INTEGER',
        'conf_count_BrOB' : 'INTEGER',
        'conf_count_BuFVG' : 'INTEGER',
        'conf_count_BrFVG' : 'INTEGER',
        'conf_count_BuLiq' : 'INTEGER',
        'conf_count_BrLiq' : 'INTEGER',
        'conf_1min_count' : 'INTEGER',
        'conf_3min_count' : 'INTEGER',
        'conf_5min_count' : 'INTEGER',
        'conf_15min_count' : 'INTEGER',
        'conf_1h_count' : 'INTEGER',
        'conf_4h_count' : 'INTEGER',
        'conf_1D_count' : 'INTEGER',
    }

    @classmethod
    def GetByTimeStamp(cls,timestamp):
        sql = f"SELECT * FROM {cls.table} WHERE timestamp = %s"
        return DB.execute(sql,[timestamp],fetchone=True)