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
        def wrapper(cls, limit=0,symbol = "BTCUSDT", *args, **kwargs):
            # build cache key with table + function name + limit
            cache_key = f"{cls.table}:{func.__name__}:{limit or 'ALL'}:symbol:{symbol}"
            cached = Cache.get(cache_key)
            if cached is not None:
                return cached

            # Prepare LIMIT clause if needed
            limit_clause = f"LIMIT {limit}" if limit else ""

            # Run the original function
            result = func(cls, limit_clause,symbol, *args, **kwargs)

            # Store in cache (default 60s, tweak if needed)
            Cache.set(cache_key, result, 60)
            return result
        return wrapper
    
    @classmethod
    @islimitExist
    def getPendingSignals(cls, limit, symbol, offset=0):
        sql = f"""
            SELECT * FROM {cls.table}
            WHERE result = 'PENDING' AND symbol = %s
            ORDER BY timestamp DESC
            LIMIT %s OFFSET %s
        """
        result = DB.execute(sql, [symbol, limit, offset], fetchall=True)
        return result
    
    @classmethod
    @islimitExist
    def getRunningSignals(cls, limit, symbol, offset=0):
        sql = f"""
            SELECT * FROM {cls.table}
            WHERE result = 'RUNNING' AND symbol = %s
            ORDER BY timestamp DESC
            LIMIT %s OFFSET %s
        """
        result = DB.execute(sql, [symbol, limit, offset], fetchall=True)
        return result
    
    @classmethod
    @islimitExist
    def getWonSignals(cls,limit,symbol):
        sql = f"SELECT * FROM {cls.table} WHERE result = 'WIN' and symbol = %s ORDER BY timestamp DESC {limit}"
        result = DB.execute(sql,[symbol],fetchall= True)
        return result
    
    @classmethod
    @islimitExist
    def getLostSignals(cls,limit,symbol):
        sql = f"SELECT * FROM {cls.table} WHERE result = 'LOSE' and symbol = %s ORDER BY timestamp DESC {limit}"
        result = DB.execute(sql,[symbol],fetchall= True)
        return result
    
    @classmethod
    @islimitExist
    def getGivenSignals(cls,limit,symbol):
        sql = f"SELECT * FROM {cls.table} WHERE (result = 'RUNNING' or result = 'PENDING') and symbol = %s ORDER BY timestamp DESC {limit}"
        result = DB.execute(sql,[symbol],fetchall= True)
        return result
    
    @classmethod
    def bulk_update_status(cls, ids, status):
        if not ids:
            return
        placeholders = ', '.join(['%s'] * len(ids))
        sql = f"UPDATE {cls.table} SET result = %s WHERE id IN ({placeholders})"
        DB.execute(sql, [status] + ids,commit=True)
        keys = Cache._client.keys(f"{cls.table}:*")
        for k in keys:
            Cache._client.delete(k)

    @classmethod
    def update_pending_signals_query(cls,symbol,threshold, candle):
        sql = f"""
            UPDATE {cls.table}
            SET result = 'RUNNING'
            WHERE result = 'PENDING' AND symbol = %s
            AND (
                (position = 'Long'
                AND ABS(sl - %s) > %s
                AND sl < %s AND %s < entry_price)
                OR
                (position = 'Short'
                AND ABS(sl - %s) > %s
                AND sl > %s AND %s > entry_price)
            )
        """
        DB.execute(sql, [
            symbol,
            candle['low'], threshold, candle['low'], candle['low'],
            candle['high'], threshold, candle['high'], candle['high']
        ])
        keys = Cache._client.keys(f"{cls.table}:*")
        for k in keys:
            Cache._client.delete(k)

    @classmethod
    def update_running_signals_query(cls,symbol, candle):
        sql = f"""
            UPDATE {cls.table}
            SET result = CASE
                WHEN position = 'Long' AND sl >= %s THEN 'LOSE'
                WHEN position = 'Long' AND tp <= %s THEN 'WIN'
                WHEN position = 'Short' AND sl <= %s THEN 'LOSE'
                WHEN position = 'Short' AND tp >= %s THEN 'WIN'
                ELSE result
            END
            WHERE symbol = %s AND result = 'RUNNING';
        """
        DB.execute(sql, [candle['low'], candle['high'], candle['high'], candle['low'], symbol])
        keys = Cache._client.keys(f"{cls.table}:*")
        for k in keys:
            Cache._client.delete(k)


    

    
    
