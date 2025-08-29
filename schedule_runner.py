from Scheduler.scheduler import SchedulerManager
import time
if __name__ == "__main__":
    scheduler_manager = SchedulerManager()
    scheduler_manager.start()

    # Keep the process alive
    
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        print("Scheduler stopped.")