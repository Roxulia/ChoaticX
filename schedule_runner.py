from Scheduler.scheduler import SchedulerManager
from Services.signalService import SignalService
import time
if __name__ == "__main__":
    
    scheduler_manager = SchedulerManager(SignalService())
    scheduler_manager.start()
    try:
        while True:
            time.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        print("Scheduler stopped.")
