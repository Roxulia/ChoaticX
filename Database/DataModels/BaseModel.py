from ..DB import MySQLDB as DB
from ..Cache import Cache
from functools import wraps
import re

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

        for col_name, col_type in cls.columns.items():
            if col_name in existing_cols and existing_cols[col_name].lower() != col_type.lower() and col_name != "id":
                alter_sql = f"ALTER TABLE {cls.table} MODIFY COLUMN {col_name} {col_type}"
                DB.execute(alter_sql, commit=True)
                DB._logger.info(
                    f"🔄 Updated column `{col_name}` type from {existing_cols[col_name]} to {col_type} in `{cls.table}`"
                )
                
    @staticmethod
    def _quote_ident_mysql(name: str) -> str:
        # simple sanitizer: allow alphanum, underscore; otherwise quote
        if re.match(r'^[A-Za-z0-9_]+$', name):
            return f"`{name}`"
        # fallback to backticks with escaping
        return "`" + name.replace("`", "``") + "`"

    @classmethod
    def create_index(cls, columns: list[str], unique: bool = False):
        """
        Create an index in MySQL if it does not already exist.
        Uses information_schema.statistics to check existence.
        """
        if not cls.table:
            raise ValueError("cls.table must be set")

        if not columns:
            raise ValueError("columns list cannot be empty")

        # build index name (keep it reasonably short)
        index_name = f"{cls.table}_{'_'.join(columns)}_idx"
        # MySQL has 64 char limit for index names; truncate if needed
        if len(index_name) > 60:
            index_name = index_name[:60]

        quoted_index = cls._quote_ident_mysql(index_name)
        quoted_table = cls._quote_ident_mysql(cls.table)
        quoted_cols = ", ".join(cls._quote_ident_mysql(c) for c in columns)

        # Check existence in information_schema.statistics
        check_sql = """
            SELECT COUNT(*) AS idx_count
            FROM information_schema.statistics
            WHERE table_schema = DATABASE()
              AND table_name = %s
              AND index_name = %s
        """
        try:
            row = DB.execute(check_sql, [cls.table, index_name],fetchone=True)
            # try to get a row from cursor-like return
            exists = bool(row['idx_count'] > 0)
        except Exception as e:
            # If we can't query information_schema for any reason, be conservative:
            print("⚠️ Could not check index existence:", e)
            exists = False

        if exists:
            print(f"ℹ️ Index already exists: {index_name}")
            return

        create_sql = f"CREATE {'UNIQUE ' if unique else ''}INDEX {quoted_index} ON {quoted_table} ({quoted_cols})"
        try:
            DB.execute(create_sql, commit=True)
            print(f"✅ Created index: {index_name} on {cls.table} ({', '.join(columns)})")
        except Exception as e:
            print(f"❌ Failed to create index {index_name}: {e}")
            raise

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
    @islimitExist
    def getRecentZones(cls,limit,symbol):
        sql = f"((SELECT * FROM fvg_zones where symbol = %s) union (select * from ob_zones where symbol = %s) union (select * from liq_zones where symbol = %s)) order by timestamp desc {limit}"
        result = DB.execute(sql,[symbol,symbol,symbol],fetchall= True)
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
    
    @classmethod
    def GetByUniqueZone(cls,timestamp,symbol,time_frame):
        raw_key = f"{cls.table}:find:timestamp:{timestamp}:symbol:{symbol}:timeframe:{time_frame}"
        cached = Cache.get(raw_key)
        if cached is not None:
            return cached
        sql = f"SELECT * FROM {cls.table} WHERE timestamp = %s and symbol = %s and time_frame = %s"
        result =  DB.execute(sql,[timestamp,symbol,time_frame],fetchone=True)
        Cache.set(raw_key,result)
        return result
