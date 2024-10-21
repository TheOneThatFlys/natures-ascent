from __future__ import annotations
from typing import Callable, TypeVar, Optional

import datetime, time

_MAGIC_VALUE = "$CONSOLE"

_logger_instance: Logger = None

T = TypeVar("T")

class TerminalColours:
    END = "\033[0m"
    INFO = "\033[94m"
    DEBUG = "\033[92m"
    WARN = "\033[93m"
    ERROR = "\033[91m"
    TIME = "\033[38;2;255;179;38m"

class Logger:
    INFO = "INFO"
    DEBUG = "DEBUG"
    WARNING = "WARN"
    ERROR = "ERROR"

    def __init__(self, path: str = _MAGIC_VALUE, use_colours: bool = False) -> None:
        self.out_path = path
        self.allowed_values: list[str] = []
        self.use_colours = use_colours

        if self.out_path != _MAGIC_VALUE:
            with open(self.out_path, "a"):
                ...

    @staticmethod
    def set_path(path: str):
        """Set out path for logging. Magic value '$CONSOLE' causes logs to be output to console instead"""
        Logger.get().out_path = path

    @staticmethod
    def allow_all():
        Logger.get().allowed_values = [Logger.INFO, Logger.DEBUG, Logger.WARNING, Logger.ERROR]
    
    @staticmethod
    def disable_all():
        Logger.get().allowed_values = []

    @staticmethod
    def info(msg: str) -> None:
        Logger.get()._log(msg, Logger.INFO)

    @staticmethod
    def debug(msg: str) -> None:
        Logger.get()._log(msg, Logger.DEBUG)

    @staticmethod
    def warn(msg: str) -> None:
        Logger.get()._log(msg, Logger.WARNING)

    @staticmethod
    def error(msg: str, e: Exception) -> None:
        Logger.get()._log(f"{msg} ({e})", Logger.ERROR)

    @staticmethod
    def time(msg: str = "%t"):
        def outer(func):
            def wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                a = func(*args, **kwargs)
                Logger.debug(msg.replace("%t", str(round(time.perf_counter() - start_time, 3))))
                return a
            return wrapper
        return outer

    @staticmethod
    def start(path: str = _MAGIC_VALUE) -> None:
        global _logger_instance
        _logger_instance = Logger(path)

    @staticmethod
    def get() -> Logger:
        if not _logger_instance:
            raise RuntimeError("Logger not initialised. Initialise logger by calling logger.start()")
        return _logger_instance
    
    def _log(self, msg: str, level: str) -> None:
        if level not in self.allowed_values: return

        rn = datetime.datetime.now()
        time = f"{rn:%H:%M:%S}.{str(rn.microsecond)[0:3]}"
        if self.out_path == _MAGIC_VALUE:
            if self.use_colours:
                logged_msg = f"{TerminalColours.TIME}{time} {getattr(TerminalColours, level)}{level} {TerminalColours.END}{msg}"
            else:
                logged_msg = f"{time} {level} {msg}"
            print(logged_msg)
        else:
            logged_msg = f"[{time}] [{level}] {msg}"
            with open(self.out_path, "a") as f:
                f.write(logged_msg + "\n")

if __name__ == "__main__":
    Logger.start()
    # test timing
    @Logger.time("executed in %t seconds")
    def foo(test: int) -> int:
        time.sleep(test)
        return test
    
    Logger.allow_all()
    Logger.info("test info")
    Logger.debug("test debug")
    Logger.warn("test warn")
    Logger.error("test error", Exception())

    a = foo(5)
    print("return: " + str(a))
