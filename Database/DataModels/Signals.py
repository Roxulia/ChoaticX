from .BaseModel import BaseModel 
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