import time
import pandas as pd
from Services.signalService import SignalService
from Utility.MemoryUsage import MemoryUsage as mu

@mu.log_memory
def initialState():
    total = test.data_extraction()
    if total is None:
        print("Unexcepted Error Occured")
    else:
        test.training_process(total)

if __name__ == "__main__" :
    pd.set_option('future.no_silent_downcasting', True)
    test = SignalService()
    start = time.perf_counter()
    #test.test_process()
    initialState()
    #test.get_latest_zones('3 years')
    #print(test.get_current_signals())
    end = time.perf_counter()
    print(f"Execution time: {end - start:.6f} seconds")
