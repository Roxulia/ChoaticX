import time
import pandas as pd
from Services.signalService import SignalService
from Utility.MemoryUsage import MemoryUsage as mu
from Backtest.backtest import BackTestHandler
from Exceptions.ServiceExceptions import *

@mu.log_memory
def initialState():
    test = SignalService(timeframes=['1h','4h','1D'])
    try:
        total = test.data_extraction()
        test.training_process(total)
    except CantFetchCandleData as e:
        print(f'{e}')
        

@mu.log_memory
def backtest():
    backtest = BackTestHandler(time_frames = ['1h','4h','1D'],lookback = '1 years')
    if backtest.warm_up():
        backtest.run_backtest()
    else:
        print("Warm-up failed. Exiting.")

if __name__ == "__main__" :
    pd.set_option('future.no_silent_downcasting', True)
    
    start = time.perf_counter()
    initialState()
    backtest()
    end = time.perf_counter()
    print(f"Execution time: {end - start:.6f} seconds")
