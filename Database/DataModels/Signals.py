from .BaseModel import BaseModel 
from ..DB import MySQLDB as DB
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
    def getPendingSignals(cls):
        sql = f"SELECT * FROM {cls.table} WHERE result = 'PENDING'"
        return DB.execute(sql,fetchall= True)
    
    