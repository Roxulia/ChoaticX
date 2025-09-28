from apscheduler.schedulers.background import BackgroundScheduler
from Services.signalService import SignalService
from Data.binanceAPI import BinanceAPI
import queue,threading,asyncio

class SchedulerManager:
    def __init__(self,service : SignalService,api : BinanceAPI):
        self.scheduler = BackgroundScheduler()
        self.service = service
        self.binance_api = api
        # PriorityQueue: lower number = higher priority
        self.task_queue = queue.PriorityQueue()

        # Global DB lock
        self.db_lock = threading.Lock()

        # Worker thread to consume tasks
        worker = threading.Thread(target=self._worker, daemon=True)
        worker.start()
        listener = threading.Thread(target=self._start_binance_listener, daemon=True)
        listener.start()

    def start(self):
        # Plan B example:
        # 1. Update zones every 3 hours
        self.scheduler.add_job(lambda: self.task_queue.put((1, self.service.update_untouched_zones())),
            'interval',
            hours=24,
            id="update_zones")
        
        self.scheduler.add_job(lambda : self.task_queue.put((2,self.service.update_running_signals())),'interval',hours=24,id = "update_signals")

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

    def _start_binance_listener(self):
        asyncio.run(self._binance_loop())

    async def _binance_loop(self):
        try:
            await self.binance_api.connect()
        except Exception as e:
            print(f'{str(e)}')

        async def on_kline_close(kline):
            try:
                interval = kline.get("i")  # e.g. "1h" or "4h"
                if interval == "1h":
                    self.task_queue.put((1, self.service.update_running_signals()))
                    self.task_queue.put((2,self.service.update_pending_signals(300)))
                    self.task_queue.put((3, self.service.get_current_signals))
                    print("📡 1h closed → triggered signals")

                elif interval == "4h":
                    self.task_queue.put((1, self.service.update_untouched_zones()))
                    print("📡 4h closed → triggered zones")
            except Exception as e:
                print(f'{str(e)}')
        # listen to both 1h + 4h
        try:
            await self.binance_api.listen_kline(["BTCUSDT"], ["1h", "4h"], on_kline_close)
        except Exception as e:
            print(f'{str(e)}')