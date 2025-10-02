from apscheduler.schedulers.background import BackgroundScheduler
from Services.signalService import SignalService
from Data.binanceAPI import BinanceAPI
import queue,threading,asyncio,itertools

class SchedulerManager:
    def __init__(self, api: BinanceAPI):
        self.scheduler = BackgroundScheduler()
        self.btcservice = SignalService(symbol="BTCUSDT", threshold=300)
        self.bnbservice = SignalService(symbol="BNBUSDT", threshold=3)
        self.binance_api = api

        # PriorityQueue: (priority, counter, func)
        self.task_queue = queue.PriorityQueue()
        self._counter = itertools.count()

        # Global DB lock
        self.db_lock = threading.Lock()

        # Worker & listener threads
        worker = threading.Thread(target=self._worker, daemon=True)
        worker.start()
        listener = threading.Thread(target=self._start_binance_listener, daemon=True)
        listener.start()

    def _put_task(self, priority, func):
        """ Helper to safely put tasks into queue """
        self.task_queue.put((priority, next(self._counter), func))

    def start(self):
        # Use function refs, not return values
        self.scheduler.add_job(
            lambda: self._put_task(1, self.btcservice.update_untouched_zones),
            'interval', hours=24, id="update_btc_zones"
        )
        self.scheduler.add_job(
            lambda: self._put_task(2, self.btcservice.update_running_signals),
            'interval', hours=24, id="update_btc_signals"
        )
        self.scheduler.add_job(
            lambda: self._put_task(1, self.bnbservice.update_untouched_zones),
            'interval', hours=24, id="update_bnb_zones"
        )
        self.scheduler.add_job(
            lambda: self._put_task(2, self.bnbservice.update_running_signals),
            'interval', hours=24, id="update_bnb_signals"
        )
        self.scheduler.start()

    def _worker(self):
        while True:
            priority, _, func = self.task_queue.get()
            try:
                with self.db_lock:  # 🔒 Ensure only one DB write at a time
                    result = func()
                    if result is not None:
                        # broadcast message or log
                        print(f"[Worker] Task result: {result}")
            except Exception as e:
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
                interval = kline.get("i")
                symbol = kline.get("s")

                if interval == "1h":
                    if symbol == "BTCUSDT":
                        self._put_task(1, self.btcservice.update_running_signals)
                        self._put_task(2, self.btcservice.update_pending_signals)
                        self._put_task(3, self.btcservice.get_current_signals)
                        print("📡 1h BTC closed → triggered signals")

                    elif symbol == "BNBUSDT":
                        self._put_task(1, self.bnbservice.update_running_signals)
                        self._put_task(2, self.bnbservice.update_pending_signals)
                        self._put_task(3, self.bnbservice.get_current_signals)
                        print("📡 1h BNB closed → triggered signals")

                elif interval == "4h":
                    if symbol == "BTCUSDT":
                        self._put_task(1, self.btcservice.update_untouched_zones)
                    elif symbol == "BNBUSDT":
                        self._put_task(1, self.bnbservice.update_untouched_zones)
                    print("📡 4h closed → triggered zones")

            except Exception as e:
                print(f'{str(e)}')

        try:
            await self.binance_api.listen_kline(
                ["BTCUSDT", "BNBUSDT"], ["1h", "4h"], on_kline_close
            )
        except Exception as e:
            print(f'{str(e)}')
