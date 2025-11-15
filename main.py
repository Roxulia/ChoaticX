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

# ----------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------
local = True

symbols = {
    "BTCUSDT": [500, 125, 1000],
    "BNBUSDT": [5, 2, 10],
    "PAXGUSDT": [10, 4, 20],
    "ETHUSDT": [10, 4, 20],
    "SOLUSDT": [2.5, 0.875, 5]
}

timeframes_1h = ['1h', '4h', '1D']
timeframes_15m = ['15min', '1h', '4h']
timeframes_1D = ['1D', '3D', '1W']

# ----------------------------------------------------------------------
# SERVICE FACTORIES
# ----------------------------------------------------------------------
def make_signal_service(symbol, timeframe_type):
    tf_map = {
        "1h": (timeframes_1h, symbols[symbol][0]),
        "15min": (timeframes_15m, symbols[symbol][1]),
        "1D": (timeframes_1D, symbols[symbol][2]),
    }
    tfs, threshold = tf_map[timeframe_type]
    return SignalService(symbol=symbol, threshold=threshold, timeframes=tfs, Local=local, initial=True)


services_based_1h = {s: make_signal_service(s, "1h") for s in symbols}
services_based_15m = {s: make_signal_service(s, "15min") for s in symbols}
services_based_1D = {s: make_signal_service(s, "1D") for s in symbols}


# ----------------------------------------------------------------------
# UTILITY WRAPPERS
# ----------------------------------------------------------------------
def run_training(service,initiate_all = False):
    """Extract + Train wrapper with uniform exception handling."""
    try:
        if not initiate_all:
            initiate_database()
        total = service.data_extraction()
        service.training_process(total)
    except (CantFetchCandleData, TrainingFail) as e:
        print(str(e))
        raise FailInitialState
    except Exception as e:
        print(str(e))
        raise


# ----------------------------------------------------------------------
# MAIN ACTIONS
# ----------------------------------------------------------------------
@mu.log_memory
def initiateAll():
    print("Initiating All Model and System")
    try:
        initiate_database()

        # Train 1h models
        for service in services_based_1h.values():
            run_training(service,True)

        # Train 15 min models
        for service in services_based_15m.values():
            run_training(service,True)

        for service in services_based_1D.values():
            run_training(service,True)

        # Train prediction models
        initiate_prediction_models()

    except Exception as e:
        print(str(e))
        raise FailInitialState


@mu.log_memory
def initiate_prediction_models():
    print("Initiating Prediction Models")
    try:
        for symbol, (h_th, m_th, d_th) in symbols.items():
            for tf in ['15min', '1h', '4h', '1D']:
                th = m_th if tf == '15min' else (d_th if tf == '1D' else h_th)
                PredictionService(symbol, [tf], th).train_process()
    except Exception as e:
        print(str(e))
        raise


@mu.log_memory
def initiate_prediction_model(symbol, timeframe):
    print("Initiating Prediction Model:")
    try:
        if timeframe == '15min':
            th = symbols[symbol][1]  
        elif timeframe == '1D':
            th = symbols[symbol][2]  
        else:
            th = symbols[symbol][0]  
        PredictionService(symbol, [timeframe], th).train_process()
    except Exception as e:
        print(str(e))
        raise


@mu.log_memory
def initialState1H(symbol):
    run_training(services_based_1h[symbol])


@mu.log_memory
def initialState15Min(symbol):
    run_training(services_based_15m[symbol])

@mu.log_memory
def initialState1D(symbol):
    run_training(services_based_1D[symbol])

@mu.log_memory
def initiate_database():
    try:
        FVG.initiate()
        OB.initiate()
        LIQ.initiate()
        Signals.initiate()
        Subscribers.initiate()

        FVG.create_index(['symbol', 'timestamp', 'time_frame'])
        OB.create_index(['symbol', 'timestamp', 'time_frame'])
        LIQ.create_index(['symbol', 'timestamp', 'time_frame'])
        Signals.create_index(['result', 'symbol', 'timestamp'])
        Subscribers.create_index(['chat_id'])
        Subscribers.create_index(['tier', 'is_admin'])

    except Exception as e:
        print(str(e))
        raise


@mu.log_memory
def train_model(symbol):
    run_training(services_based_1h[symbol])


@mu.log_memory
def backtest(symbol, threshold):
    handler = BackTestHandler(symbol=symbol, threshold=threshold,
                              time_frames=['1h', '4h', '1D'], lookback='1 years')

    if handler.warm_up():
        try:
            handler.run_backtest()
        except:
            raise BackTestFail
    else:
        raise WarmUpFail


@mu.log_memory
def run_all_process():
    try:
        initiateAll()
        # You did backtest() but missing args → now removed to avoid crash
    except Exception as e:
        print(str(e))


# ----------------------------------------------------------------------
# PROCESS REGISTRATION
# ----------------------------------------------------------------------
def generate_process_map():
    process = {
        "*": run_all_process,
        "update-database": initiate_database,
        "initiate-system": initiateAll,
        "initiate-predict": initiate_prediction_models,
        #"initiate-predict-btc-15min": lambda: initiate_prediction_model("BTCUSDT", "15min")
    }

    # dynamic generation for all symbols
    for sym in symbols:
        process[f"initiate-{sym.lower()}-1h"] = lambda s=sym: initialState1H(s)
        process[f"initiate-{sym.lower()}-15m"] = lambda s=sym: initialState15Min(s)
        process[f"initiate-{sym.lower()}-1D"] = lambda s=sym: initialState1D(s)
        process[f"train-{sym.lower()}"] = lambda s=sym: train_model(s)

        # backtest threshold
        thr = symbols[sym][0]
        process[f"backtest-{sym.lower()}"] = lambda s=sym, t=thr: backtest(s, t)

    for sym in symbols.keys():
        lower = sym.replace("USDT", "").lower()
        for tf in ['15min','1h','4h','1D']:  # ['15min','1h','4h','1D']
            tf_key = tf.lower()
            process[f"initiate-predict-{lower}-{tf_key}"] = \
                lambda s=sym, t=tf: initiate_prediction_model(s, t)
    return process


# ----------------------------------------------------------------------
# ENTRY POINT
# ----------------------------------------------------------------------
if __name__ == "__main__":
    if not local:
        Cache.init()
    DB.init_logger("initialdb.log")
    pd.set_option('future.no_silent_downcasting', True)

    parser = argparse.ArgumentParser(description="run training program")
    parser.add_argument("option")
    args = parser.parse_args()

    process_map = generate_process_map()

    if args.option not in process_map:
        print(f"❌ Invalid option: {args.option}")
        print("Available options:")
        for key in process_map:
            print("  -", key)
        exit(1)

    start = time.perf_counter()
    process_map[args.option]()
    end = time.perf_counter()

    print(f"Execution time: {end - start:.6f} seconds")

