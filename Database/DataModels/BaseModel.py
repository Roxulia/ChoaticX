from ..DB import MySQLDB as DB

class BaseModel:
    table :str = None  # to override in subclasses
    columns : dict = None

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
