class EmptySignalException(Exception):
    def __init__(self):
        super().__init__("No running Signal Found")

class NoUntouchedZone(Exception):
    def __init__(self):
        super().__init__("No Untouched Zone Found")

class CantFetchCandleData(Exception):
    def __init__(self):
        super().__init__("Cannot Fetch OHCLV Candle Data")

class CantSaveToCSV(Exception):
    def __init__(self):
        super().__init__("Cannot Save to CSV File")

class TrainingFail(Exception):
    def __init__(self, *args):
        super().__init__("Model Training Failed")

class FailInitialState(Exception):
    def __init__(self):
        super().__init__("Failed to initiate program")

class WarmUpFail(Exception):
    def __init__(self):
        super().__init__("Failed To load Warmup Data")

class BackTestFail(Exception):
    def __init__(self):
        super().__init__("Error Occur in Backtest Process")