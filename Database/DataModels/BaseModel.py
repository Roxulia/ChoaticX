from ..DB import MySQLDB as DB
from ..Cache import Cache
from functools import wraps

class BaseModel:
    table :str = None  # to override in subclasses
    columns : dict = None

    def islimitExist(func):
        @wraps(func)
        def wrapper(cls, limit=0, *args, **kwargs):
            # Prepare LIMIT clause if needed
            limit_clause = f"LIMIT {limit}" if limit else ""
            # Run the original function
            result = func(cls, limit_clause, *args, **kwargs)
            return result
        return wrapper
    
    @classmethod
    def initiate(cls):
        if not cls.table or not cls.columns:
            raise ValueError("Table name and columns must be defined in subclass")

        # Ensure table exists (empty shell if needed)
        col_defs = [f"{col} {ctype}" for col, ctype in cls.columns.items()]
        sql = f"""
        CREATE TABLE IF NOT EXISTS {cls.table} (
            {', '.join(col_defs)}
        )
        """
        DB.execute(sql, commit=True)
        DB._logger.info(f"✅ Table `{cls.table}` ensured in DB")

        # Fetch existing columns
        query = f"""
        SELECT COLUMN_NAME, COLUMN_TYPE 
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
        """
        existing = DB.execute(query, (cls.table,),fetchall=True)
        existing_cols = {row['COLUMN_NAME']: row['COLUMN_TYPE'] for row in existing}

        # Add missing columns
        for col_name, col_type in cls.columns.items():
            if col_name not in existing_cols:
                alter_sql = f"ALTER TABLE {cls.table} ADD COLUMN {col_name} {col_type}"
                DB.execute(alter_sql, commit=True)
                DB._logger.info(f"➕ Added column `{col_name}` {col_type} to `{cls.table}`")

        # (Optional) Warn if column types differ
        for col_name, col_type in cls.columns.items():
            if col_name in existing_cols and existing_cols[col_name].lower() != col_type.lower():
                DB._logger.warning(
                    f"⚠ Column `{col_name}` type mismatch: DB has {existing_cols[col_name]}, "
                    f"expected {col_type}"
                )


    @classmethod
    def create(cls, data: dict):
        keys = ", ".join(data.keys())
        values = ", ".join(["%s"] * len(data))
        sql = f"INSERT INTO {cls.table} ({keys}) VALUES ({values})"
        DB.execute(sql, list(data.values()), commit=True)
        keys = Cache._client.keys(f"{cls.table}:*")
        for k in keys:
            Cache._client.delete(k)
        print(f"✅ Inserted into {cls.table}")

    @classmethod
    def all(cls):
        sql = f"SELECT * FROM {cls.table}"
        return DB.execute(sql, fetchall=True)

    @classmethod
    def find(cls, record_id):
        raw_key = f"{cls.table}:find:id:{record_id}"
        cached = Cache.get(raw_key)
        if cached is not None:
            return cached
        sql = f"SELECT * FROM {cls.table} WHERE id = %s"
        result =  DB.execute(sql, [record_id], fetchone=True)
        Cache.set(raw_key,result,60)
        return result

    @classmethod
    def update(cls, record_id, data: dict):
        set_clause = ", ".join([f"{k}=%s" for k in data.keys()])
        sql = f"UPDATE {cls.table} SET {set_clause} WHERE id = %s"
        DB.execute(sql, list(data.values()) + [record_id], commit=True)
        keys = Cache._client.keys(f"{cls.table}:*")
        for k in keys:
            Cache._client.delete(k)
        print(f"✅ Updated {cls.table} id={record_id}")

    @classmethod
    def delete(cls, record_id):
        sql = f"DELETE FROM {cls.table} WHERE id = %s"
        DB.execute(sql, [record_id], commit=True)
        keys = Cache._client.keys(f"{cls.table}:*")
        for k in keys:
            Cache._client.delete(k)
        print(f"🗑 Deleted from {cls.table} id={record_id}")

    @classmethod
    @islimitExist
    def getRecentData(cls,limit,key,symbol):
        raw_key = f"{cls.table}:find:{key}:{symbol}:{limit}:ORDER"
        cached = Cache.get(raw_key)
        if cached is not None:
            return cached
        sql = f"SELECT * FROM {cls.table} WHERE symbol = %s ORDER BY {key} DESC {limit}"
        result = DB.execute(sql,[symbol],fetchall= True)
        Cache.set(raw_key,result,60)
        return result
    
    @classmethod
    def GetByTimeStamp(cls,timestamp):
        raw_key = f"{cls.table}:find:timestamp:{timestamp}"
        cached = Cache.get(raw_key)
        if cached is not None:
            return cached
        sql = f"SELECT * FROM {cls.table} WHERE timestamp = %s"
        result =  DB.execute(sql,[timestamp],fetchall=True)
        Cache.set(raw_key,result)
        return result
    
    @classmethod
    def GetBySymbol(cls,symbol):
        raw_key = f"{cls.table}:find:symbol:{symbol}"
        cached = Cache.get(raw_key)
        if cached is not None:
            return cached
        sql = f"SELECT * FROM {cls.table} WHERE symbol = %s"
        result =  DB.execute(sql,[symbol],fetchall=True)
        Cache.set(raw_key,result)
        return result
    
    @classmethod
    def GetBySymbolTimeStamp(cls,timestamp,symbol):
        raw_key = f"{cls.table}:find:timestamp:{timestamp}:symbol:{symbol}"
        cached = Cache.get(raw_key)
        if cached is not None:
            return cached
        sql = f"SELECT * FROM {cls.table} WHERE timestamp = %s and symbol = %s"
        result =  DB.execute(sql,[timestamp,symbol],fetchone=True)
        Cache.set(raw_key,result)
        return result
