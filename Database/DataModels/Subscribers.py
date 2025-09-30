from .BaseModel import BaseModel
from ..DB import MySQLDB as DB
from ..Cache import Cache
class Subscribers(BaseModel):
    table = 'subscribers'
    columns = {
        "id": "BIGINT AUTO_INCREMENT PRIMARY KEY",
        "chat_id": "BIGINT NOT NULL UNIQUE",
        "username": "VARCHAR(255)",
        "is_active": "BOOLEAN DEFAULT TRUE",
        "is_admin" : "BOOLEAN DEFAULT FALSE",
        "tier" : "BIGINT DEFAULT 1",
        "capital" : "BIGINT DEFAULT 1000",
        "risk_size" : "FLOAT DEFAULT 0.01",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
    }

    @classmethod
    def getByChatID(cls,chat_id):
        raw_key = f"{cls.table}:find:chat_id:{chat_id}"
        cached = Cache.get(raw_key)
        if cached is not None:
            return cached
        sql = f"SELECT * FROM {cls.table} WHERE chat_id = %s"
        result =  DB.execute(sql, [chat_id], fetchone=True)
        Cache.set(raw_key,result,60)
        return result
    
    @classmethod
    def getActiveSubscribers(cls):
        raw_key = f"{cls.table}:find:is_active:true"
        cached = Cache.get(raw_key)
        if cached is not None:
            return cached
        sql = f"SELECT * FROM {cls.table} WHERE is_active = True OR is_admin = True"
        result =  DB.execute(sql,fetchall=True)
        Cache.set(raw_key,result)
        return result
    
    @classmethod
    def getActiveSubscriberWithTier(cls,tier:int):
        raw_key = f"{cls.table}:find:is_active:True:tier:{tier}"
        cached = Cache.get(raw_key)
        if cached is not None:
            return cached
        sql = f"SELECT * FROM {cls.table} WHERE (is_active = True and tier = %s) OR is_admin = True "
        result = DB.execute(sql,[tier],fetchall=True)
        Cache.set(raw_key,result)
        return result