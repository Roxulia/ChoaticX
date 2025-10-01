from .baseScheduler import BaseScheduler
from Services.signalService import SignalService

class BtcScheduler(BaseScheduler):
    def __init__(self,api):
        service = SignalService(symbol="BTCUSDT",threshold=300)
        name = "BTC"
        super().__init__(service, api, name)

    def register_jobs(self):
        self.scheduler.add_job(
            lambda: self._put_task(1, self.service.update_untouched_zones),
            "interval", hours=24, id="btc_update_zones"
        )
        self.scheduler.add_job(
            lambda: self._put_task(2, self.service.update_running_signals),
            "interval", hours=24, id="btc_update_signals"
        )

    async def _handle_kline(self, kline):
        interval = kline.get("i")
        symbol = kline.get("s")

        if interval == "1h" and symbol == "BTCUSDT":
            self._put_task(1, self.service.update_running_signals)
            self._put_task(2, self.service.update_pending_signals)
            self._put_task(3, self.service.get_current_signals)
            print("📡 1h BTC closed → triggered signals")

        elif interval == "4h" and symbol == "BTCUSDT":
            self._put_task(1, self.service.update_untouched_zones)
            print("📡 4h BTC closed → triggered zones")
        else:
            print(f"{self.name}-testing")