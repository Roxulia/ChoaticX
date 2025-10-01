from apscheduler.schedulers.background import BackgroundScheduler
from Services.signalService import SignalService
from Data.binanceAPI import BinanceAPI
import queue,threading,asyncio,itertools,logging,os
from dotenv import load_dotenv

class BaseScheduler():
    def __init__(self, service:SignalService, api:BinanceAPI, name: str):
        self.name = name
        self.service = service
        self.api = api
        self.scheduler = BackgroundScheduler()
        self.task_queue = queue.PriorityQueue()
        self._counter = itertools.count()
        self.db_lock = threading.Lock()
        self.logger = logging.getLogger(f"{name}_scheduler_logs")
        self.logger.setLevel(logging.DEBUG)
        self.initiate_logging()
        # Start worker thread
        worker = threading.Thread(target=self._worker, daemon=True)
        worker.start()


    def initiate_logging(self):
        load_dotenv()
        # File handler
        file_handler = logging.FileHandler(os.path.join(os.getenv(key='LOG_PATH'), f"{self.name}_scheduler.log"))
        file_handler.setLevel(logging.DEBUG)

        # Console handler (optional)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)


    def _put_task(self, priority, func):
        """ Helper to safely put tasks into queue """
        self.task_queue.put((priority, next(self._counter), func))

    def _worker(self):
        """ Worker consumes tasks with global DB lock """
        while True:
            priority, _, func = self.task_queue.get()
            try:
                with self.db_lock:  # ensure only one DB write
                    result = func()
                    if result is not None:
                        self.logger.info(f"[{self.name}-Worker] Task result: {result}")
            except Exception as e:
                self.logger.error(f"[{self.name}-Worker] Error: {e}")
            finally:
                self.task_queue.task_done()

    def _start_binance_listener(self):
        asyncio.run(self._binance_loop())

    async def _binance_loop(self):
        try:
            await self.api.connect()
        except Exception as e:
            self.logger.error(f"[{self.name}-API] Connect error: {e}")

        async def on_kline_close(kline):
            try:
                await self._handle_kline(kline)
            except Exception as e:
                self.logger.error(f"[{self.name}-Listener] Error: {e}")

        try:
            await self.api.listen_kline([self.service.symbol], ["1h", "4h"], on_kline_close)
        except Exception as e:
            self.logger.error(f"[{self.name}-Listener] Fatal error: {e}")

    # to be overridden in subclasses
    async def _handle_kline(self, kline: dict):
        pass

    # to be overridden in subclasses
    def register_jobs(self):
        pass

    def start(self):
        self.register_jobs()
        self.scheduler.start()
        self.logger.info(f"[{self.name}] Scheduler started")