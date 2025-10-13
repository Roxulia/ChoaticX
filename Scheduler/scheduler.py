from apscheduler.schedulers.background import BackgroundScheduler
from Services.signalService import SignalService
from Data.binanceAPI import BinanceAPI
import queue, threading, asyncio, itertools, time, traceback,json
from Database.Cache import Cache

class SchedulerManager:
    def __init__(self, api: BinanceAPI):
        self.scheduler = BackgroundScheduler()
        self.btcservice = SignalService(symbol="BTCUSDT", threshold=300)
        self.bnbservice = SignalService(symbol="BNBUSDT", threshold=3)
        self.paxgservice = SignalService(symbol="PAXGUSDT", threshold=10)
        self.binance_api = api

        self.task_queue = queue.PriorityQueue()
        self._counter = itertools.count()
        self.db_lock = threading.Lock()
        self.runningthread = []

        # Start watchdog threads
        self._start_thread(self._worker_watchdog, name="WorkerWatchdog")
        self._start_thread(self._listener_watchdog, name="ListenerWatchdog")

    # -------------------- Utility --------------------
    def _put_task(self, priority, func):
        self.task_queue.put((priority, next(self._counter), func))

    def _start_thread(self, target, name):
        """Start a thread that restarts itself if it crashes."""
        def wrapper():
            while True:
                try:
                    target()
                except Exception as e:
                    print(f"❌ Thread [{name}] crashed: {e}")
                    Cache._client.publish("service_error",json.dump({"error":f"❌ Thread [{name}] crashed: {e}" }))
                    traceback.print_exc()
                    print(f"🔄 Restarting [{name}] in 5s...")
                    time.sleep(5)
        t = threading.Thread(target=wrapper, daemon=True, name=name)
        self.runningthread.append(t)
        t.start()

    # -------------------- Watchdogs --------------------
    def _worker_watchdog(self):
        """Ensures worker thread restarts on crash"""
        print("🧵 Worker thread started")
        self._worker()

    def _listener_watchdog(self):
        """Ensures listener thread restarts on crash"""
        print("🧩 Binance listener thread started")
        self._start_binance_listener()

    # -------------------- Worker Logic --------------------
    def _worker(self):
        while True:
            try:
                priority, _, func = self.task_queue.get()
                with self.db_lock:
                    result = func()
                    if result is not None:
                        print(f"[Worker] Task result: {result}")
            except Exception as e:
                print(f"[Worker] Error running task: {e}")
                traceback.print_exc()
            finally:
                self.task_queue.task_done()

    # -------------------- APScheduler --------------------
    def start(self):
        try:
            # Add your jobs safely
            jobs = [
                ("update_btc_zones", 1, self.btcservice.update_untouched_zones),
                ("update_btc_signals", 2, self.btcservice.update_running_signals),
                ("update_bnb_zones", 1, self.bnbservice.update_untouched_zones),
                ("update_bnb_signals", 2, self.bnbservice.update_running_signals),
                ("update_paxg_zones", 1, self.paxgservice.update_untouched_zones),
                ("update_paxg_signals", 2, self.paxgservice.update_running_signals),
            ]
            for job_id, prio, func in jobs:
                self.scheduler.add_job(lambda f=func, p=prio: self._put_task(p, f),
                                       'interval', hours=24, id=job_id)
            self.scheduler.start()
            print("✅ APScheduler started successfully")
        except Exception as e:
            print(f"❌ Scheduler start failed: {e}")
            traceback.print_exc()

    # -------------------- Binance Listener --------------------
    def _start_binance_listener(self):
        """Run async Binance listener inside a thread."""
        while True:
            try:
                asyncio.run(self._binance_loop())
            except Exception as e:
                print(f"❌ Binance listener thread crashed: {e}")
                traceback.print_exc()
                print("🔄 Restarting Binance listener in 5s...")
                time.sleep(5)

    async def _binance_loop(self):
        max_retries = 10           # stop after 10 consecutive failures
        base_delay = 5             # seconds
        retry_count = 0

        while True:
            try:
                print("🔌 Connecting to Binance WebSocket...")
                await self.binance_api.connect()

                async def on_kline_close(kline):
                    try:
                        interval = kline.get("i")
                        symbol = kline.get("s")
                        candle = {
                            "open": float(kline["o"]),
                            "close": float(kline["c"]),
                            "high": float(kline["h"]),
                            "low": float(kline["l"]),
                        }

                        # --- Candle handling logic ---
                        if interval == "15m":
                            if symbol == "BTCUSDT":
                                self._put_task(3, lambda: self.btcservice.update_running_signals(candle))
                                self._put_task(4, lambda: self.btcservice.update_pending_signals(candle))
                                print("📡 15min BTC closed → triggered signals update")
                            elif symbol == "BNBUSDT":
                                self._put_task(3, lambda: self.bnbservice.update_running_signals(candle))
                                self._put_task(4, lambda: self.bnbservice.update_pending_signals(candle))
                                print("📡 15min BNB closed → triggered signals update")
                            elif symbol == "PAXGUSDT":
                                self._put_task(3, lambda: self.paxgservice.update_running_signals(candle))
                                self._put_task(4, lambda: self.paxgservice.update_pending_signals(candle))
                                print("📡 15min PAXG closed → triggered signals update")

                        elif interval == "1h":
                            if symbol == "BTCUSDT":
                                self._put_task(1, lambda: self.btcservice.update_ATHzone(candle))
                                self._put_task(5, self.btcservice.get_current_signals)
                                print("📡 1h BTC closed → triggered ATH update and signal generation")
                            elif symbol == "BNBUSDT":
                                self._put_task(1, lambda: self.bnbservice.update_ATHzone(candle))
                                self._put_task(5, self.bnbservice.get_current_signals)
                                print("📡 1h BNB closed → triggered ATH update and signal generation")
                            elif symbol == "PAXGUSDT":
                                self._put_task(1, lambda: self.paxgservice.update_ATHzone(candle))
                                self._put_task(5, self.paxgservice.get_current_signals)
                                print("📡 1h PAXG closed → triggered ATH update and signal generation")

                        elif interval == "4h":
                            if symbol == "BTCUSDT":
                                self._put_task(2, self.btcservice.update_untouched_zones)
                            elif symbol == "BNBUSDT":
                                self._put_task(2, self.bnbservice.update_untouched_zones)
                            elif symbol == "PAXGUSDT":
                                self._put_task(2, self.paxgservice.update_untouched_zones)
                            print("📡 4h closed → triggered zones")
                    except Exception as e:
                        print(f"❌ Error inside on_kline_close: {e}")
                        traceback.print_exc()

                # Start listening
                await self.binance_api.listen_kline(
                    ["BTCUSDT", "BNBUSDT", "PAXGUSDT"],
                    ["15m", "1h", "4h"],
                    on_kline_close,
                )

                # If listen_kline completes normally, reset retry counter
                retry_count = 0

            except Exception as e:
                retry_count += 1
                delay = min(base_delay * (2 ** (retry_count - 1)), 300)  # exponential backoff up to 5min

                if "ConnectionClosedOK" in str(e):
                    print("⚠️ WebSocket closed normally. Reconnecting in 5s...")
                    delay = 5
                else:
                    print(f"❌ Binance listener crashed (attempt {retry_count}/{max_retries}): {e}")
                    traceback.print_exc()

                # Stop trying after too many consecutive failures
                if retry_count >= max_retries:
                    print("🚨 Too many connection failures. Stopping Binance listener.")
                    break

                await asyncio.sleep(delay)
                print(f"🔄 Retrying connection (waited {delay}s)...")
                continue

        print("🛑 Binance listener exited permanently.")
        Cache._client.publish("service_error",json.dump({'error':'binance socket error'}))

    def stop(self):
        for t in self.runningthread:
            t.join()
