from dataclasses import dataclass,field
import os
from dotenv import load_dotenv

@dataclass
class Paths :
    model_root: str = field(init=False)
    raw_data: str = field(init=False)
    train_data: str = field(init=False)
    test_data: str = field(init=False)
    zone_storage: str = field(init=False)
    ath_data: str = field(init=False)
    signal_storage: str = field(init=False)
    root: str = field(init=False)
    columns_list : str = field(init= False)

    def __post_init__(self):
        load_dotenv()  
        self.model_root = os.getenv("MODEL_ROOT")
        self.raw_data = os.getenv("RAW_DATA")
        self.train_data = os.getenv("TRAIN_DATA")
        self.test_data = os.getenv("TEST_DATA")
        self.zone_storage = os.getenv("ZONE_STORAGE")
        self.ath_data = os.getenv("ATH_DATA")
        self.signal_storage = os.getenv("SIGNAL_STORAGE")
        self.root = os.getenv("DATA_PATH")
        self.columns_list = os.getenv("COLUMNS_LIST")