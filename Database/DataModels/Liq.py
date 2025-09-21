from .BaseModel import BaseModel
from ..DB import MySQLDB as DB
class LIQ(BaseModel):
    table = 'liq_zones'
    columns = {
        'id' : 'BIGINT AUTO_INCREMENT PRIMARY KEY',
        'timestamp' : 'TIMESTAMP UNIQUE',
        'time_frame' : 'VARCHAR(5)',
        'level': 'FLOAT',
        'zone_high': 'FLOAT',
        'zone_low': 'FLOAT',
        'count': 'FLOAT',
        'swept_time': 'TIMESTAMP',
        'equal_level_deviation': 'FLOAT',
        'avg_volume_around_zone': 'FLOAT',
        'duration_between_first_last_touch': 'FLOAT',
        'ema_20' : 'FLOAT',
        'ema_50' : 'FLOAT',
        'rsi' : 'FLOAT',
        'atr' : 'FLOAT',
        'atr_mean' : 'FLOAT',
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