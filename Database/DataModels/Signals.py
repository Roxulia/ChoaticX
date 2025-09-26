from .BaseModel import BaseModel 
from ..DB import MySQLDB as DB
from ..Cache import Cache
class Signals(BaseModel):
    table = 'signals'
    columns = {
        'id' : 'BIGINT AUTO_INCREMENT PRIMARY KEY',
        'position' : 'VARCHAR(20) NOT NULL',
        'entry_price' : 'FLOAT NOT NULL',
        'tp' : 'FLOAT NOT NULL',
        'sl' : "FLOAT NOT NULL",
        'result' : "ENUM('PENDING','WIN','LOSE') DEFAULT 'PENDING'",
        'timestamp' : "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    }

    @classmethod
    def getPendingSignals(cls,limit):
        raw_key = f"{cls.table}:result:PENDING:{limit}"
        cached = Cache.get(raw_key)
        if cached is not None:
            return cached
        sql = f"SELECT * FROM {cls.table} WHERE result = 'PENDING' ORDER BY timestamp LIMIT {limit}"
        result = DB.execute(sql,fetchall= True)
        Cache.set(raw_key,result,60)
        return result
    
    
