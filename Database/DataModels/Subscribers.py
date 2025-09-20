from .BaseModel import BaseModel
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