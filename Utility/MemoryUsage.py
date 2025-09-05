import psutil, os, functools
from contextlib import contextmanager

class MemoryUsage:
    _LOG_MEMORY_ENABLED = True  # class-level flag

    @staticmethod
    @contextmanager
    def disable_memory_logging():
        old_state = MemoryUsage._LOG_MEMORY_ENABLED
        MemoryUsage._LOG_MEMORY_ENABLED = False
        try:
            yield
        finally:
            MemoryUsage._LOG_MEMORY_ENABLED = old_state

    @staticmethod
    def log_memory(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not MemoryUsage._LOG_MEMORY_ENABLED:
                return func(*args, **kwargs)

            process = psutil.Process(os.getpid())
            before = process.memory_info().rss / 1024 ** 2
            result = func(*args, **kwargs)
            after = process.memory_info().rss / 1024 ** 2
            print(
                f"[MEM] {func.__name__}: "
                f"{before:.2f} MB -> {after:.2f} MB (Δ {after-before:.2f} MB)"
            )
            return result
        return wrapper
