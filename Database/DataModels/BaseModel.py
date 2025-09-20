from ..DB import MySQLDB as DB

class BaseModel:
    table :str = None  # to override in subclasses
    columns : dict = None

    @classmethod
    def initiate(cls):
        if not cls.table or not cls.columns:
            raise ValueError("Table name and columns must be defined in subclass")

        # Build SQL from dict
        col_defs = []
        for col_name, col_type in cls.columns.items():
            col_defs.append(f"{col_name} {col_type}")
        
        sql = f"""
        CREATE TABLE IF NOT EXISTS {cls.table} (
            {', '.join(col_defs)}
        )
        """
        DB.execute(sql, commit=True)
        DB._logger.info(f"✅ Table `{cls.table}` ensured in DB")

    @classmethod
    def create(cls, data: dict):
        keys = ", ".join(data.keys())
        values = ", ".join(["%s"] * len(data))
        sql = f"INSERT INTO {cls.table} ({keys}) VALUES ({values})"
        DB.execute(sql, list(data.values()), commit=True)
        print(f"✅ Inserted into {cls.table}")

    @classmethod
    def all(cls):
        sql = f"SELECT * FROM {cls.table}"
        return DB.execute(sql, fetchall=True)

    @classmethod
    def find(cls, record_id):
        sql = f"SELECT * FROM {cls.table} WHERE id = %s"
        return DB.execute(sql, [record_id], fetchone=True)

    @classmethod
    def update(cls, record_id, data: dict):
        set_clause = ", ".join([f"{k}=%s" for k in data.keys()])
        sql = f"UPDATE {cls.table} SET {set_clause} WHERE id = %s"
        DB.execute(sql, list(data.values()) + [record_id], commit=True)
        print(f"✅ Updated {cls.table} id={record_id}")

    @classmethod
    def delete(cls, record_id):
        sql = f"DELETE FROM {cls.table} WHERE id = %s"
        DB.execute(sql, [record_id], commit=True)
        print(f"🗑 Deleted from {cls.table} id={record_id}")
