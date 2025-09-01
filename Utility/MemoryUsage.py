import psutil, os, functools

class MemoryUsage():
    @staticmethod
    def log_memory(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            process = psutil.Process(os.getpid())
            before = process.memory_info().rss / 1024 ** 2
            result = func(*args, **kwargs)
            after = process.memory_info().rss / 1024 ** 2
            print(f"[MEM] {func.__name__}: {before:.2f} MB -> {after:.2f} MB (Δ {after-before:.2f} MB)")
            return result
        return wrapper