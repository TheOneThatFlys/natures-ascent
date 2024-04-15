from __future__ import annotations
from typing import Literal

import datetime

_logger_instance: Logger = None

class Logger:
    INFO = "INFO"
    DEBUG = "DEBUG"
    WARNING = "WARN"
    ERROR = "ERROR"

    def __init__(self) -> None:
        self.log_time = True
        self.out_path = "$CONSOLE"

        self.allowed_values: list[str] = []

    @staticmethod
    def set_path(path: str | Literal["$CONSOLE"]):
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
    def error(msg: str) -> None:
        Logger.get()._log(msg, Logger.ERROR)

    @staticmethod
    def get() -> Logger:
        global _logger_instance
        if not _logger_instance:
            _logger_instance = Logger()
        return _logger_instance
    
    def _log(self, msg: str, level: str) -> None:
        if level not in self.allowed_values: return

        rn = datetime.datetime.now()
        time = f"[{rn:%H:%M:%S}] " if self.log_time else ""
        logged_msg = f"{time}[{level}] {msg}"
            
        if self.out_path == "$CONSOLE":
            print(logged_msg)
        else:
            with open(self.out_path, "a") as f:
                f.write(logged_msg)