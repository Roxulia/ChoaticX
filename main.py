import time
import pandas as pd
from Services.signalService import SignalService
from Utility.MemoryUsage import MemoryUsage as mu
from Backtest.backtest import BackTestHandler

@mu.log_memory
def initialState():
    test = SignalService(timeframes=['1h','4h','1D'])
    total = test.data_extraction()
    if total is None:
        print("Unexcepted Error Occured")
    else:
        test.training_process(total)

@mu.log_memory
def backtest():
    backtest = BackTestHandler(time_frames = ['1h','4h','1D'],lookback = '1 years')
    if backtest.warm_up():
        backtest.run_backtest(zone_update_interval = 5)
    else:
        print("Warm-up failed. Exiting.")

if __name__ == "__main__" :
    pd.set_option('future.no_silent_downcasting', True)
    
    start = time.perf_counter()
    #initialState()
    backtest()
    end = time.perf_counter()
    print(f"Execution time: {end - start:.6f} seconds")
