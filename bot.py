from Services.signalService import SignalService
from Telegram.TelegramBot import TelegramBot
from Database.DB import MySQLDB as DB
from Database.Cache import Cache
import time,signal,sys
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
    DB.init_logger("bot_db.log")
    service = SignalService()
    bot = TelegramBot(service)
    bot.run()
    try:
        while not stop_requested:
            time.sleep(1)
    except Exception as e:
        print(f"❌ Unknown exception: {e}")
    finally:
        print("🛑 Stopping SchedulerManager...")
        try:
            bot.stop()  # ✅ implement this in SchedulerManager if not yet
        except Exception as e:
            print(f"Error stopping scheduler: {e}")
        print("✅ All threads stopped, exiting.")
        sys.exit(0)
    
    
