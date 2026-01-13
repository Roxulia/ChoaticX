import time
import pandas as pd
import argparse
import asyncio
import traceback
from Market import Candles
from Core import Structures
from Core import Volatility

def test_TA():
    try:
        df_gen = Candles()
        data = asyncio.run(df_gen.getLatestCandle("BNBUSDT","1h"))
        print(data)
    except Exception as e:
        print(str(e))

def test_Structure():
    try:
        candles = asyncio.run(Candles().getCandleData("BNBUSDT","1h","1 year"))
        df_gen = Structures(candles,"1h")
        data = asyncio.run(df_gen.detect())
        print(data[0])
    except Exception as e:
        print(str(e))
        traceback.print_stack()
    
def test_Regime():
    try:
        candles = asyncio.run(Candles().getCandleData("BNBUSDT","1h","1 year"))
        df_gen = Volatility()
        data = asyncio.run(df_gen.detect(candles))
        print(data.iloc[-1])
    except Exception as e:
        print(str(e))
        traceback.print_stack()
        

def generate_process_map():
    process = {
        "test-TA" : test_TA,
        "test-Structure" : test_Structure,
        "test-Volatility" : test_Regime
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