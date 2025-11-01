import os
import logging
from logging.handlers import RotatingFileHandler
from threading import Lock
from dotenv import load_dotenv

class Logger:
    _instances = {}
    _lock = Lock()
    _context = "app"  # default context (will be overridden by main file)

    @classmethod
    def set_context(cls, context_name: str):
        """
        Set logging context globally (e.g. 'signal', 'analysis', etc.)
        Must be called once in each main entrypoint.
        """
        cls._context = context_name

    def __new__(cls):
        """
        Create or reuse a Singleton logger per context.
        Example: Logger() inside signal_main.py and inside services
                 will all point to the same 'signal.log'.
        """
        with cls._lock:
            context = cls._context
            if context not in cls._instances:
                instance = super(Logger, cls).__new__(cls)
                instance._initialize(context)
                cls._instances[context] = instance
            return cls._instances[context]

    def _initialize(self, context):
        load_dotenv()

        base_path = os.getenv("LOG_PATH", "logs")
        os.makedirs(base_path, exist_ok=True)

        log_file = os.path.join(base_path, f"{context}.log")
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        max_bytes = int(os.getenv("LOG_MAX_BYTES", 5_000_000))
        backup_count = int(os.getenv("LOG_BACKUP_COUNT", 3))

        self.logger = logging.getLogger(f"ChaoticXLogger:{context}")
        self.logger.setLevel(getattr(logging, log_level, logging.INFO))
        self.logger.propagate = False

        if not self.logger.handlers:
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(threadName)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )

            file_handler = RotatingFileHandler(
                log_file, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    # Shortcut methods
    def info(self, msg): self.logger.info(msg)
    def warning(self, msg): self.logger.warning(msg)
    def error(self, msg, exc_info=False): self.logger.error(msg, exc_info=exc_info)
    def debug(self, msg): self.logger.debug(msg)
    def critical(self, msg): self.logger.critical(msg)
