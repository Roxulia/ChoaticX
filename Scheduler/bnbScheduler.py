from .baseScheduler import BaseScheduler
from Services.signalService import SignalService
class BnbScheduler(BaseScheduler):
    def __init__(self,api):
        service = SignalService(symbol="BNBUSDT",threshold=3)
        name = "BNB"
        super().__init__(service, api, name)

    def register_jobs(self):
        self.scheduler.add_job(
            lambda: self._put_task(1, self.service.update_untouched_zones),
            "interval", hours=24, id="bnb_update_zones"
        )
        self.scheduler.add_job(
            lambda: self._put_task(2, self.service.update_running_signals),
            "interval", hours=24, id="bnb_update_signals"
        )

    async def _handle_kline(self, kline):
        interval = kline.get("i")
        symbol = kline.get("s")

        if interval == "1h" and symbol == "BNBUSDT":
            self._put_task(1, self.service.update_running_signals)
            self._put_task(2, self.service.update_pending_signals)
            self._put_task(3, self.service.get_current_signals)
            self.logger.info("📡 1h BNB closed → triggered signals")

        elif interval == "4h" and symbol == "BNBUSDT":
            self._put_task(1, self.service.update_untouched_zones)
            self.logger.info("📡 4h BNB closed → triggered zones")
