from Scheduler.scheduler import SchedulerManager
from Services.signalService import SignalService
from Database.DB import MySQLDB as DB
import time
if __name__ == "__main__":
    DB.init_logger("schedule_runner_db.log")
    service = SignalService()
    scheduler_manager = SchedulerManager(service)
    scheduler_manager.start()
    try:
        while True:
            time.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        print("Scheduler stopped.")
