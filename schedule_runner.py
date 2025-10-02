from Scheduler.scheduler import SchedulerManager
from Scheduler.bnbScheduler import BnbScheduler
from Scheduler.btcScheduler import BtcScheduler
from Services.signalService import SignalService
from Data.binanceAPI import BinanceAPI
from Database.DB import MySQLDB as DB
import time,asyncio
from Database.Cache import Cache


Cache.init()
if __name__ == "__main__":
    DB.init_logger("schedule_runner_db.log")
    api = BinanceAPI()
    scheduler = SchedulerManager(api = api)
    scheduler.start()
    """bnbscheduler = BnbScheduler(api)
    btcscheduler = BtcScheduler(api)
    bnbscheduler.start()
    btcscheduler.start()
    async def dispatch_kline(kline):
        # This runs in the main asyncio loop. Call scheduler sync handlers
        try:
            # call sync handler; they will enqueue tasks for worker threads
            btcscheduler._handle_kline(kline)
            bnbscheduler._handle_kline(kline)
        except Exception as e:
            print(f"[dispatch] error handling kline: {e}")

    async def listen_and_dispatch():
        await api.connect()
        async def on_kline_close(kline):
            # run dispatch quickly, non-blocking
            asyncio.create_task(dispatch_kline(kline))

        # subscribe to both symbols/timeframes in one listener
        await api.listen_kline(["BTCUSDT", "BNBUSDT"], ["1h", "4h"], on_kline_close)"""
    try:
        #asyncio.run(listen_and_dispatch())
        time.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        print("Scheduler stopped.")
