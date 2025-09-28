import time
import pandas as pd
import argparse
from Services.signalService import SignalService
from Utility.MemoryUsage import MemoryUsage as mu
from Backtest.backtest import BackTestHandler
from Exceptions.ServiceExceptions import *
from Database.DB import MySQLDB as DB
from Database.DataModels.FVG import FVG
from Database.DataModels.OB import OB
from Database.DataModels.Liq import LIQ
from Database.DataModels.Signals import Signals
from Database.DataModels.Subscribers import Subscribers
from Database.Cache import Cache

@mu.log_memory
def initialState(symbol):
    print('Running Model Training')
    try:
        initiate_database()
        test = SignalService(symbol=symbol,timeframes=['1h','4h','1D'])
        total = test.data_extraction()
        test.training_process(total)
    except CantFetchCandleData as e:
        print(f'{e}')
        raise FailInitialState
    except TrainingFail as e:
        print(f'{e}')
        raise FailInitialState
    except Exception as e:
        print(f'{e}')
        raise e
        
@mu.log_memory
def initiate_database():
    try:
        DB.init_logger("initialdb.log")
        FVG.initiate()
        OB.initiate()
        LIQ.initiate()
        Signals.initiate()
        Subscribers.initiate()
    except Exception as e:
        print(f'{str(e)}')
        raise e

@mu.log_memory
def backtest():
    backtest = BackTestHandler(time_frames = ['1h','4h','1D'],lookback = '1 years')
    if backtest.warm_up():
        try:
            backtest.run_backtest()
        except:
            raise BackTestFail
    else:
        print("Warm-up failed. Exiting.")
        raise WarmUpFail

@mu.log_memory
def run_all_process():
    try:
        initialState()
        backtest()
    except FailInitialState as e:
        print(f'{e}')
    except WarmUpFail as e:
        print(f'{e}')
    except:
        print("Process Fail")

if __name__ == "__main__" :
    Cache.init()
    pd.set_option('future.no_silent_downcasting', True)
    parser = argparse.ArgumentParser(description="run training program")
    parser.add_argument("option",help="'*' to do all process\n'train' to Train Model\n'backtest' to Test the Model",default='*')
    start = time.perf_counter()
    args = parser.parse_args()
    process = {
        '*' : run_all_process,
        'update-database' : initiate_database,
        'initiate-btc' : lambda : initialState("BTCUSDT"),
        'initiate-bnb' : lambda : initialState("BNBUSDT"),
        'backtest' : backtest
    }
    process[args.option]()
    end = time.perf_counter()
    print(f"Execution time: {end - start:.6f} seconds")
