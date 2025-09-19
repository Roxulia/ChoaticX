from Scheduler.scheduler import SchedulerManager
from Services.signalService import SignalService
import time
if __name__ == "__main__":
    service = SignalService()
    scheduler_manager = SchedulerManager(service)
    scheduler_manager.start()
    try:
        while True:
            time.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        print("Scheduler stopped.")
