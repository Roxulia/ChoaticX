from .BaseModel import BaseModel 
from ..DB import MySQLDB as DB
from ..Cache import Cache
from functools import wraps


class Signals(BaseModel):
    table = 'signals'
    columns = {
        'id' : 'BIGINT AUTO_INCREMENT PRIMARY KEY',
        'symbol' : 'VARCHAR(10)',
        'position' : 'VARCHAR(20) NOT NULL',
        'entry_price' : 'FLOAT NOT NULL',
        'tp' : 'FLOAT NOT NULL',
        'sl' : "FLOAT NOT NULL",
        'result' : "ENUM('PENDING','WIN','LOSE','RUNNING') DEFAULT 'PENDING'",
        'timestamp' : "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    }

    def islimitExist(func):
        @wraps(func)
        def wrapper(cls, limit=0, *args, **kwargs):
            # build cache key with table + function name + limit
            cache_key = f"{cls.table}:{func.__name__}:{limit or 'ALL'}"
            cached = Cache.get(cache_key)
            if cached is not None:
                return cached

            # Prepare LIMIT clause if needed
            limit_clause = f"LIMIT {limit}" if limit else ""

            # Run the original function
            result = func(cls, limit_clause, *args, **kwargs)

            # Store in cache (default 60s, tweak if needed)
            Cache.set(cache_key, result, 60)
            return result
        return wrapper
    
    @classmethod
    @islimitExist
    def getPendingSignals(cls,limit,symbol):
        
        sql = f"SELECT * FROM {cls.table} WHERE result = 'PENDING' and symbol = %s ORDER BY timestamp {limit}"
        result = DB.execute(sql,[symbol],fetchall= True)
        return result
    
    @classmethod
    @islimitExist
    def getRunningSignals(cls,limit,symbol):
        sql = f"SELECT * FROM {cls.table} WHERE result = 'RUNNING' and symbol = %s ORDER BY timestamp {limit}"
        result = DB.execute(sql,[symbol],fetchall= True)
        return result
    
    @classmethod
    @islimitExist
    def getWonSignals(cls,limit,symbol):
        sql = f"SELECT * FROM {cls.table} WHERE result = 'WIN' and symbol = %s ORDER BY timestamp {limit}"
        result = DB.execute(sql,[symbol],fetchall= True)
        return result
    
    @classmethod
    @islimitExist
    def getLostSignals(cls,limit,symbol):
        sql = f"SELECT * FROM {cls.table} WHERE result = 'LOSE' and symbol = %s ORDER BY timestamp {limit}"
        result = DB.execute(sql,[symbol],fetchall= True)
        return result
    
    @classmethod
    @islimitExist
    def getGivenSignals(cls,limit,symbol):
        sql = f"SELECT * FROM {cls.table} WHERE (result = 'RUNNING' or result = 'PENDING') and symbol = %s ORDER BY timestamp {limit}"
        result = DB.execute(sql,[symbol],fetchall= True)
        return result
    

    
    
