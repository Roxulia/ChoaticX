import time
import pandas as pd
import argparse
from Services.signalService import SignalService
from Services.predictionService import PredictionService
from Utility.MemoryUsage import MemoryUsage as mu
from Utility.Logger import Logger
from Backtest.backtest import BackTestHandler
from Exceptions.ServiceExceptions import *
from Database.DB import MySQLDB as DB
from Database.DataModels.FVG import FVG
from Database.DataModels.OB import OB
from Database.DataModels.Liq import LIQ
from Database.DataModels.Signals import Signals
from Database.DataModels.Subscribers import Subscribers
from Database.Cache import Cache

Logger.set_context("main_system")
local = False
symbols = {
    "BTCUSDT" : [500,125],
    "BNBUSDT" : [5,2],
    "PAXGUSDT": [10,4],
    "ETHUSDT" : [10,4],
    "SOLUSDT" : [2,0.75]
    }
services_based_1h = {
    "BTCUSDT" : SignalService(symbol="BTCUSDT",threshold=symbols['BTCUSDT'][0],timeframes=['1h','4h','1D'],Local=local,initial=True),
    "BNBUSDT" : SignalService(symbol="BNBUSDT",threshold=symbols['BNBUSDT'][0],timeframes=['1h','4h','1D'],Local=local,initial=True),
    "ETHUSDT" : SignalService(symbol="ETHUSDT",threshold=symbols['ETHUSDT'][0],timeframes=['1h','4h','1D'],Local=local,initial=True),
    "SOLUSDT" : SignalService(symbol="SOLUSDT",threshold=symbols['SOLUSDT'][0],timeframes=['1h','4h','1D'],Local=local,initial=True),
    "PAXGUSDT" : SignalService(symbol="PAXGUSDT",threshold=symbols['PAXGUSDT'][0],timeframes=['1h','4h','1D'],Local=local,initial=True),
}
services_based_15min = {
    "BTCUSDT" : SignalService(symbol="BTCUSDT",threshold=symbols['BTCUSDT'][1],timeframes=['15min','1h','4h'],Local=local,initial=True),
    "BNBUSDT" : SignalService(symbol="BNBUSDT",threshold=symbols['BNBUSDT'][1],timeframes=['15min','1h','4h'],Local=local,initial=True),
    "ETHUSDT" : SignalService(symbol="ETHUSDT",threshold=symbols['ETHUSDT'][1],timeframes=['15min','1h','4h'],Local=local,initial=True),
    "SOLUSDT" : SignalService(symbol="SOLUSDT",threshold=symbols['SOLUSDT'][1],timeframes=['15min','1h','4h'],Local=local,initial=True),
    "PAXGUSDT" : SignalService(symbol="PAXGUSDT",threshold=symbols['PAXGUSDT'][1],timeframes=['15min','1h','4h'],Local=local,initial=True),
}
"""services_based_1D = {
    "BTCUSDT" : SignalService(symbol="BTCUSDT",threshold=symbols['BTCUSDT'],timeframes=['1D','3D','1W'],Local=local,initial=True),
    "BNBUSDT" : SignalService(symbol="BNBUSDT",threshold=symbols['BNBUSDT'],timeframes=['1D','3D','1W'],Local=local,initial=True),
    "ETHUSDT" : SignalService(symbol="ETHUSDT",threshold=symbols['ETHUSDT'],timeframes=['1D','3D','1W'],Local=local,initial=True),
    "SOLUSDT" : SignalService(symbol="SOLUSDT",threshold=symbols['SOLUSDT'],timeframes=['1D','3D','1W'],Local=local,initial=True),
    "PAXGUSDT" : SignalService(symbol="PAXGUSDT",threshold=symbols['PAXGUSDT'],timeframes=['1D','3D','1W'],Local=local,initial=True),
}"""
timeframes = ['15min','1h','4h','1D']
@mu.log_memory
def initiateAll():
    print("Initiating All Model and System")
    try:
        initiate_database()
        for k,v in services_based_1h.items():
            total = v.data_extraction()
            v.training_process(total)
        for k,v in services_based_15min.items():
            total = v.data_extraction()
            v.training_process(total)
        initiate_prediction_models()
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
def initiate_prediction_models():
    print("Initiating Prediction Models")
    try:
        for s,threshold in symbols.items():
            for t in timeframes:
                if t == '15min':
                    predictor = PredictionService(s,[t],threshold[1])
                    predictor.train_process()
                else:
                    predictor = PredictionService(s,[t],threshold[0])
                    predictor.train_process()
    except Exception as e:
        print(f'{e}')
        raise e

@mu.log_memory
def initialState1H(symbol):
    print('Running Model Training')
    try:
        initiate_database()
        test = services_based_1h[symbol]
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
def initialState15Min(symbol):
    print('Running Model Training')
    try:
        initiate_database()
        test = services_based_15min[symbol]
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
        
        FVG.initiate()
        OB.initiate()
        LIQ.initiate()
        Signals.initiate()
        Subscribers.initiate()
        FVG.create_index(['symbol','timestamp','time_frame'])
        OB.create_index(['symbol','timestamp','time_frame'])
        LIQ.create_index(['symbol','timestamp','time_frame'])
        Signals.create_index(['result','symbol','timestamp'])
        Subscribers.create_index(['chat_id'])
        Subscribers.create_index(['tier','is_admin'])
    except Exception as e:
        print(f'{str(e)}')
        raise e

@mu.log_memory
def train_model(symbol):
    try:
        test = services_based_1h[symbol]
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
def backtest(symbol,threshold):
    backtest = BackTestHandler(symbol=symbol,threshold=threshold,time_frames = ['1h','4h','1D'],lookback = '1 years')
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
        initiateAll()
        backtest()
    except FailInitialState as e:
        print(f'{e}')
    except WarmUpFail as e:
        print(f'{e}')
    except:
        print("Process Fail")

if __name__ == "__main__" :
    if not local:
        Cache.init()
    DB.init_logger("initialdb.log")
    pd.set_option('future.no_silent_downcasting', True)
    parser = argparse.ArgumentParser(description="run training program")
    parser.add_argument("option",help="'*' to do all process\n'train' to Train Model\n'backtest' to Test the Model",default='*')
    start = time.perf_counter()
    args = parser.parse_args()
    process = {
        '*' : run_all_process,
        'update-database' : initiate_database,
        'initiate-btc-1h' : lambda : initialState1H("BTCUSDT"),
        'initiate-bnb-1h' : lambda : initialState1H("BNBUSDT"),
        'initiate-paxg-1h' : lambda : initialState1H("PAXGUSDT"),
        'initiate-eth-1h' : lambda : initialState1H("ETHUSDT"),
        'initiate-sol-1h' : lambda : initialState1H("SOLUSDT"),
        
        'initiate-btc-15m' : lambda : initialState15Min("BTCUSDT"),
        'initiate-bnb-15m' : lambda : initialState15Min("BNBUSDT"),
        'initiate-paxg-15m' : lambda : initialState15Min("PAXGUSDT"),
        'initiate-eth-15m' : lambda : initialState15Min("ETHUSDT"),
        'initiate-sol-15m' : lambda : initialState15Min("SOLUSDT"),
        'train-btc' : lambda : train_model("BTCUSDT"),
        'train-bnb' : lambda : train_model("BNBUSDT"),
        'train-paxg' : lambda : train_model("PAXGUSDT"),
        'train-eth' : lambda : train_model("ETHUSDT"),
        'train-sol' : lambda : train_model("SOLUSDT"),
        'backtest-btc' : lambda : backtest("BTCUSDT",500),
        'backtest-bnb' : lambda : backtest("BNBUSDT",5),
        'backtest-paxg' : lambda : backtest("PAXGUSDT",10),
        'backtest-eth' : lambda : backtest("ETHUSDT",10),
        'backtest-sol' : lambda : backtest("SOLUSDT",10),
        'initiate-system' : initiateAll,
        'initiate-predict' : initiate_prediction_models,
    }
    process[args.option]()
    end = time.perf_counter()
    print(f"Execution time: {end - start:.6f} seconds")










