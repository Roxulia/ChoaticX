from apscheduler.schedulers.background import BackgroundScheduler
from Services.signalService import SignalService

class SchedulerManager:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.service = SignalService()

    def start(self):
        # Plan B example:
        # 1. Update zones every 3 hours
        self.scheduler.add_job(self.service.update_untouched_zones, 'interval', hours=3)

        # 2. Check signals on every 1h candle close
        self.scheduler.add_job(self.service.get_current_signals, 'interval', hours=1)

        self.scheduler.start()
