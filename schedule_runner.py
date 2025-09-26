from Scheduler.scheduler import SchedulerManager
from Services.signalService import SignalService
from Data.binanceAPI import BinanceAPI
from Database.DB import MySQLDB as DB
import time
from Database.Cache import Cache

Cache.init()
if __name__ == "__main__":
    DB.init_logger("schedule_runner_db.log")
    service = SignalService()
    api = BinanceAPI()
    scheduler_manager = SchedulerManager(service,api)
    scheduler_manager.start()
    try:
        while True:
            time.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        print("Scheduler stopped.")
