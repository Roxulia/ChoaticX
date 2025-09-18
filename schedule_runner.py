from Scheduler.scheduler import SchedulerManager
from Services.signalService import SignalService
import time
if __name__ == "__main__":
    
    scheduler_manager = SchedulerManager(SignalService())
    t = threading.Thread(target=scheduler_manager.start, daemon=True)
    t.start()
    # Keep the process alive
    try:
        while True:
            time.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        print("Scheduler stopped.")
