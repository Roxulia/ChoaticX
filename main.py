import time
import pandas as pd
from Services.signalService import SignalService

if __name__ == "__main__" :
    pd.set_option('future.no_silent_downcasting', True)
    test = SignalService()
    start = time.perf_counter()
    #test.test_process()
    total = test.data_extraction()
    test.training_process(total)
    #print(test.get_current_signals())
    end = time.perf_counter()
    print(f"Execution time: {end - start:.6f} seconds")
