from apscheduler.schedulers.background import BackgroundScheduler
from Services.signalService import SignalService
from Data.binanceAPI import BinanceAPI
import queue, threading, asyncio, itertools, time, traceback,json,logging,os
from dotenv import load_dotenv
from Database.Cache import Cache
from Utility.Logger import Logger

class SchedulerManager:
    def __init__(self, api: BinanceAPI):
        self.scheduler = BackgroundScheduler()
        self.services_based_1h = {
            "BTCUSDT": SignalService(symbol="BTCUSDT", threshold=500),
            "BNBUSDT": SignalService(symbol="BNBUSDT", threshold=5),
            "PAXGUSDT": SignalService(symbol="PAXGUSDT", threshold=10),
            "ETHUSDT": SignalService(symbol="ETHUSDT", threshold=10),
            "SOLUSDT": SignalService(symbol="SOLUSDT", threshold=2),
        }
        self.services_based_15min = {
            "BTCUSDT": SignalService(symbol="BTCUSDT",timeframes=['15min','1h','4h'], threshold=125),
            "BNBUSDT": SignalService(symbol="BNBUSDT",timeframes=['15min','1h','4h'], threshold=2),
            "PAXGUSDT": SignalService(symbol="PAXGUSDT",timeframes=['15min','1h','4h'], threshold=4),
            "ETHUSDT": SignalService(symbol="ETHUSDT",timeframes=['15min','1h','4h'], threshold=4),
            "SOLUSDT": SignalService(symbol="SOLUSDT",timeframes=['15min','1h','4h'], threshold=0.75),
        }
        self.binance_api = api
        self.logger = Logger()

        # Worker system
        self.task_queue = queue.PriorityQueue()
        self._counter = itertools.count()
        self.db_lock = threading.Lock()

        # Threading controls
        self._stop_event = threading.Event()
        self.running_threads = []
        self._listener_thread = None

        # Reconnect controls
        self.max_retries = 10
        self.base_delay = 5
        self.inactivity_timeout = 300  # seconds

        # Start worker & listener
        self._start_thread(self._worker_loop, name="WorkerThread")
        self._start_thread(self._listener_entry, name="BinanceListener")

    # 🧱 Utility
    def _put_task(self, priority, func):
        self.task_queue.put_nowait((priority,next(self._counter), func))
        # avoid calling func.__name__ blindly if func can be a coroutine object
        try:
            name = getattr(func, "__name__", func.__class__.__name__)
        except Exception:
            name = str(func)
        self.logger.info(f"Added {name} to queue with priority={priority}")

    def _start_thread(self, target, name, daemon=True):
        """Thread wrapper with auto-restart if it crashes.
        If target is a coroutine function, we treat target as a callable that
        returns a coroutine and we run it on the thread's event loop.
        """
        def runner():
            while not self._stop_event.is_set():
                try:
                    # Create a dedicated event loop for this thread:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    # If the target is an async coroutine function, run it until completion
                    if asyncio.iscoroutinefunction(target):
                        loop.run_until_complete(target())
                    else:
                        # If target is a normal callable (sync def), just call it
                        target()
                except Exception as e:
                    self.logger.error(f"❌ Thread [{name}] crashed: {e}")
                    traceback.print_exc()
                    time.sleep(5)
                finally:
                    try:
                        loop.close()
                    except Exception:
                        pass
        t = threading.Thread(target=runner, name=name, daemon=daemon)
        t.start()
        self.running_threads.append(t)
        return t

    # -------------------------------------------------------------------------
    # ⚙️ Worker Loop (make this synchronous, run async callables inside thread loop)
    def _worker_loop(self):
        """Worker loop (runs in its own thread with dedicated event loop)."""
        self.logger.info("🧵 Worker loop started.")
    
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
        while not self._stop_event.is_set():
            try:
                priority, _, func = self.task_queue.get(timeout=1)
                self.logger.info(f"Worker picked task priority={priority}, func={getattr(func,'__name__',str(func))}")
    
                with self.db_lock:
                    # Call the task
                    result = func()  # call lambda or sync function
    
                    # If the result is a coroutine, await it
                    if asyncio.iscoroutine(result):
                        loop.run_until_complete(result)
    
                self.task_queue.task_done()
    
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Worker error: {e}")
                traceback.print_exc()

    # -------------------------------------------------------------------------
    # 🕒 Scheduler
    def start(self):
        """Start APScheduler jobs."""
        try:
            for symbol, service in self.services_based_1h.items():
                self.scheduler.add_job(
                    lambda s=service: self._put_task(1, s.zoneHandler.update_untouched_zones),
                    'interval', hours=24, id=f"update_{symbol.lower()}_zones"
                )
            self.scheduler.start()
            self.logger.info("✅ APScheduler started successfully.")
        except Exception as e:
            self.logger.error(f"Failed to start scheduler: {e}")
            traceback.print_exc()

    def stop(self):
        """Graceful shutdown."""
        self.logger.info("🛑 Stopping SchedulerManager...")
        self._stop_event.set()
        '''try:
            self.scheduler.shutdown(wait=False)
        except Exception:
            pass'''

        # Close Binance broadcast client
        try:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(self.binance_api.close())
            loop.close()
        except Exception as e:
            self.logger.warning(f"Binance close failed: {e}")

        for t in self.running_threads:
            t.join(timeout=3)

        self.logger.info("✅ SchedulerManager stopped cleanly.")

    # -------------------------------------------------------------------------
    # 📡 Binance Listener Entry
    def _listener_entry(self):
        """Launch async listener in its own event loop."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._binance_listener_main())
            loop.close()
        except Exception as e:
            self.logger.error(f"{self.__class__}:Error:{e}")

    async def _binance_listener_main(self):
        """Main loop: reconnect if websocket closes or times out."""
        retry = 0
        while not self._stop_event.is_set():
            try:
                await self._start_binance_listener()
                retry = 0  # reset on success
            except Exception as e:
                retry += 1
                delay = min(self.base_delay * (2 ** (retry - 1)), 300)
                self.logger.error(f"Listener error ({retry}/{self.max_retries}): {e}")
                traceback.print_exc()
                if retry >= self.max_retries:
                    self.logger.error("🚨 Too many reconnect failures. Stopping listener.")
                    break
                await asyncio.sleep(delay)
                self.logger.info(f"🔄 Retrying in {delay}s...")

    async def _start_binance_listener(self):
        """Connect and listen using binance_api.listen_kline()."""
        try:
            await self.binance_api.connect()
            symbols = list(self.services_based_1h.keys())
            intervals = ["5m","15m", "1h", "4h"]
        
            async def callback(kline):
                try:
                    symbol = kline.get("s")
                    interval = kline.get("i")
                    service_1h = self.services_based_1h.get(symbol)
                    service_15m = self.services_based_15min.get(symbol)
                    if not service_1h:
                        return
                    elif not service_15m:
                        return
                    candle = {
                        "open": float(kline["o"]),
                        "high": float(kline["h"]),
                        "low": float(kline["l"]),
                        "close": float(kline["c"]),
                    }

                    if interval == "5m":
                        self._put_task(6, lambda s=service_1h, c=candle: s.update_running_signals(c))
                        self._put_task(7, lambda s=service_1h, c=candle: s.update_pending_signals(c))
                        self.logger.info(f"📊 {symbol} {interval} → signal updates.")
                    elif interval == "15m":
                        self._put_task(5, lambda s=service_1h, c=candle: s.zoneHandler.update_ATHzone(c))
                        self._put_task(3, service_15m.get_current_signals)
                        self.logger.info(f"📊 {symbol} {interval} → ATH + 15m current signals.")
                    elif interval == "1h":
                        self._put_task(1, service_15m.zoneHandler.update_untouched_zones)
                        self._put_task(4, service_1h.get_current_signals)
                        self.logger.info(f"📊 {symbol} {interval} →15m zone refresh + 1h current signals.")
                    elif interval == "4h":
                        self._put_task(2, service_1h.zoneHandler.update_untouched_zones)
                        self.logger.info(f"📊 {symbol} {interval} →1h zone refresh.")
                except Exception as e:
                    self.logger.error(f"Callback error: {e}")
                    raise e

            self.logger.info(f"🔌 Connected to Binance WebSocket for {len(symbols)} symbols.")
            await self.binance_api.listen_kline(symbols, intervals, callback)
        except Exception as e:
            raise e
