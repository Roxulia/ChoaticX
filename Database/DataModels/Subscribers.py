from .BaseModel import BaseModel
from ..DB import MySQLDB as DB
class Subscribers(BaseModel):
    table = 'subscribers'
    columns = {
        "id": "BIGINT AUTO_INCREMENT PRIMARY KEY",
        "chat_id": "BIGINT NOT NULL UNIQUE",
        "username": "VARCHAR(255)",
        "is_active": "BOOLEAN DEFAULT TRUE",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
    }

    @classmethod
    def getByChatID(cls,chat_id):
        sql = f"SELECT * FROM {cls.table} WHERE chat_id = %s"
        return DB.execute(sql, [chat_id], fetchone=True)
    
    @classmethod
    def getActiveSubscribers(cls):
        sql = f"SELECT * FROM {cls.table} WHERE is_active = True"
        return DB.execute(sql,fetchall=True)