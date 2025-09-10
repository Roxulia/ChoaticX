class EmptySignalException(Exception):
    def __init__(self):
        super().__init__("No running Signal Found")

class NoUntouchedZone(Exception):
    def __init__(self):
        super().__init__("No Untouched Zone Found")

class CantFetchCandleData(Exception):
    def __init__(self):
        super().__init__("Cannot Fetch OHCLV Candle Data")