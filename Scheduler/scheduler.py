from apscheduler.schedulers.background import BackgroundScheduler
from Services.signalService import SignalService
import queue,threading

class SchedulerManager:
    def __init__(self,service : SignalService):
        self.scheduler = BackgroundScheduler()
        self.service = service
        # PriorityQueue: lower number = higher priority
        self.task_queue = queue.PriorityQueue()

        # Global DB lock
        self.db_lock = threading.Lock()

        # Worker thread to consume tasks
        worker = threading.Thread(target=self._worker, daemon=True)
        worker.start()

    def start(self):
        # Plan B example:
        # 1. Update zones every 3 hours
        self.scheduler.add_job(lambda: self.task_queue.put((1, self.service.update_untouched_zones)),
            'interval',
            hours=4,
            id="update_zones")

        # 2. Check signals on every 1h candle close
        self.scheduler.add_job(lambda: self.task_queue.put((2, self.service.get_current_signals)),
            'interval',
            hours=1,
            id="get_signals")

        self.scheduler.start()

    def _worker(self):
        while True:
            priority, func = self.task_queue.get()
            try:
                with self.db_lock:  # 🔒 Ensure only one DB write at a time
                    func()
            except Exception as e:
                # Never crash systemd service — just log
                print(f"[Worker] Error running task: {e}")
            finally:
                self.task_queue.task_done()