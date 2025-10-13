from Scheduler.scheduler import SchedulerManager
from Scheduler.bnbScheduler import BnbScheduler
from Scheduler.btcScheduler import BtcScheduler
from Services.signalService import SignalService
from Data.binanceAPI import BinanceAPI
from Database.DB import MySQLDB as DB
import time,asyncio,signal,sys
from Database.Cache import Cache


Cache.init()
stop_requested = False

def handle_shutdown(signum, frame):
    global stop_requested
    print(f"\n⚠️ Received signal {signum}, shutting down gracefully...")
    stop_requested = True

# Catch systemctl stop (SIGTERM) and Ctrl+C (SIGINT)
signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)

if __name__ == "__main__":
    DB.init_logger("schedule_runner_db.log")
    api = BinanceAPI()
    scheduler = SchedulerManager(api=api)
    scheduler.start()  # <-- assuming this starts internal threads or loops

    try:
        while not stop_requested:
            time.sleep(1)
    except Exception as e:
        print(f"❌ Unknown exception: {e}")
    finally:
        print("🛑 Stopping SchedulerManager...")
        try:
            scheduler.stop()  # ✅ implement this in SchedulerManager if not yet
        except Exception as e:
            print(f"Error stopping scheduler: {e}")
        print("✅ All threads stopped, exiting.")
        sys.exit(0)
