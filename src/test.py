import json
import time
import pandas as pd
import argparse
import asyncio
import traceback

from Market import Candles, BinanceRestAPI
from Core import *
from Exceptions import asyncerrorHandling,errorHandling
from Utility import ConfigReader, Logger, utility

Logger.set_context("test_system")

@errorHandling
def test_TA():
    df_gen = Candles()
    data = asyncio.run(df_gen.getLatestCandle("BNBUSDT","1h"))
    print(data)

@errorHandling
def test_Structure():
    candles = asyncio.run(Candles().getCandleData("BNBUSDT","1h","1 year"))
    df_gen = Structures(candles,"1h")
    data = asyncio.run(df_gen.detect())
    print(data[0])
    
@errorHandling
def test_Regime():
    candles = asyncio.run(Candles().getCandleData("BNBUSDT","1h", "1 year"))
    print(candles)
        
def test_DataGeneration():
    candles = asyncio.run(BinanceRestAPI().get_ohlcv("BNBUSDT","1h","1 year"))
    config = ConfigReader("config.json")
    indicators = TA(config.getIndicatorsConfig())
    candles = asyncio.run(indicators.add(candles))
    regimes = Regimes(config.getRegimesConfig())
    RR = config.getRollingRegression()
    if RR['enabled']: 
        rr = RollingRegression()
        market_data = asyncio.run(BinanceRestAPI().get_ohlcv(RR['base'],"1h","1 year"))
        candles = asyncio.run(rr.AddRegressionValues(candles,market_data))
    structures = Structures(candles,"1h")
    zones = asyncio.run(structures.detect())
    try:
        with open("test_result.json", 'w') as f:
            json.dump(zones, f, indent=4,default=utility.default_json_serializer)
        
    except:
        print("File Storage Error")
    candles = asyncio.run(regimes.add(candles, zones.get("SMC",{})))
    print(candles.iloc[-1])

def test_metadata():
    print(FEATURE_META_REGISTRY.get_meta("Swings").get("is_zone"))

def test_getZone():
    datagen = Generator()
    data = asyncio.run(datagen.getZones())
    print(data[0])

def generate_process_map():
    process = {
        "test-TA" : test_TA,
        "test-Structure" : test_Structure,
        "test-Regime" : test_Regime,
        "test-DataGeneration" : test_DataGeneration,
        "test-meta" : test_metadata,
        "test-getZone" : test_getZone
    }
    return process


if __name__ == "__main__":
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