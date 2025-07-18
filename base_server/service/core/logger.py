import enum
import datetime
import threading
import os
from typing import Optional
from queue import Queue, Empty

class LogLevel(enum.IntEnum):
    FATAL = 1
    ERROR = 2
    INFO = 3
    WARN = 4
    DEBUG = 5
    TRACE = 6
    ALL = 7

class LoggerInterface:
    def set_level(self, level: LogLevel):
        raise NotImplementedError
    def info(self, text: str):
        raise NotImplementedError
    def fatal(self, text: str):
        raise NotImplementedError
    def error(self, text: str):
        raise NotImplementedError
    def warn(self, text: str):
        raise NotImplementedError
    def debug(self, text: str):
        raise NotImplementedError
    def trace(self, text: str):
        raise NotImplementedError

class ConsoleLogger(LoggerInterface):
    def __init__(self, log_level: LogLevel):
        self._log_level = log_level
        self._color_codes = {
            LogLevel.FATAL: "\033[41;97m",  # 빨간색 배경 + 흰색 글자
            LogLevel.ERROR: "\033[91m",     # 빨간색
            LogLevel.WARN: "\033[93m",      # 노란색
            LogLevel.INFO: "\033[92m",      # 녹색
            LogLevel.DEBUG: "\033[94m",     # 파란색
            LogLevel.TRACE: "\033[95m"      # 자주색
        }
        self._reset = "\033[0m"
    
    def _colorize_log(self, level: LogLevel, message: str) -> str:
        color = self._color_codes.get(level, "")
        return f"{color}{message}{self._reset}"
    
    def set_level(self, level: LogLevel):
        self._log_level = level
    def info(self, log: str):
        if self._log_level != LogLevel.ALL and self._log_level < LogLevel.INFO:
            return
        print(self._colorize_log(LogLevel.INFO, f"[Info] : {log}"))
    def fatal(self, log: str):
        if self._log_level != LogLevel.ALL and self._log_level < LogLevel.FATAL:
            return
        print(self._colorize_log(LogLevel.FATAL, f"[Fatal] : {log}"))
    def error(self, log: str):
        if self._log_level != LogLevel.ALL and self._log_level < LogLevel.ERROR:
            return
        print(self._colorize_log(LogLevel.ERROR, f"[Error] : {log}"))
    def warn(self, log: str):
        if self._log_level != LogLevel.ALL and self._log_level < LogLevel.WARN:
            return
        print(self._colorize_log(LogLevel.WARN, f"[Warn] : {log}"))
    def debug(self, log: str):
        if self._log_level != LogLevel.ALL and self._log_level < LogLevel.DEBUG:
            return
        print(self._colorize_log(LogLevel.DEBUG, f"[Debug] : {log}"))
    def trace(self, log: str):
        if self._log_level != LogLevel.ALL and self._log_level < LogLevel.TRACE:
            return
        print(self._colorize_log(LogLevel.TRACE, f"[Trace] : {log}"))

class FileLogger(LoggerInterface):
    def __init__(self, log_level: LogLevel = LogLevel.INFO, use_console: bool = True, prefix: str = "App", folder: str = "log", crash_report_url: Optional[str] = None):
        self._log_level = log_level
        self._use_console = use_console
        self._prefix = prefix
        self._folder = folder
        self._crash_report_url = crash_report_url
        self._log_queue = Queue()
        self._running = True
        self._log_file_path = self._make_log_file_path()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._color_codes = {
            LogLevel.FATAL: "\033[41;97m",  # 빨간색 배경 + 흰색 글자
            LogLevel.ERROR: "\033[91m",     # 빨간색
            LogLevel.WARN: "\033[93m",      # 노란색
            LogLevel.INFO: "\033[92m",      # 녹색
            LogLevel.DEBUG: "\033[94m",     # 파란색
            LogLevel.TRACE: "\033[95m"      # 자주색
        }
        self._reset = "\033[0m"

    def _make_log_file_path(self):
        os.makedirs(self._folder, exist_ok=True)
        filename = f"{self._prefix}_{datetime.datetime.utcnow().strftime('%Y-%m-%d_%H_%M_%S')}.log"
        return os.path.join(self._folder, filename)

    def set_level(self, level: LogLevel):
        self._log_level = level

    def log(self, level: LogLevel, msg: str):
        if level < self._log_level:
            return
        now = datetime.datetime.now().strftime("[%Y/%m/%d-%H:%M:%S]")
        log_line = f"{now} [{level.name}] : {msg}"
        self._log_queue.put(log_line)
        if self._use_console:
            self._print_console(level, log_line)
        if level == LogLevel.FATAL:
            raise Exception(msg)

    def info(self, msg: str):
        self.log(LogLevel.INFO, msg)
    def fatal(self, msg: str):
        self.log(LogLevel.FATAL, msg)
    def error(self, msg: str):
        self.log(LogLevel.ERROR, msg)
    def warn(self, msg: str):
        self.log(LogLevel.WARN, msg)
    def debug(self, msg: str):
        self.log(LogLevel.DEBUG, msg)
    def trace(self, msg: str):
        self.log(LogLevel.TRACE, msg)

    def _colorize_log(self, level: LogLevel, message: str) -> str:
        color = self._color_codes.get(level, "")
        return f"{color}{message}{self._reset}"
    
    def _print_console(self, level: LogLevel, log: str):
        # 로그 레벨별 색상 적용
        print(self._colorize_log(level, log))

    def _run(self):
        while self._running:
            try:
                log_line = self._log_queue.get(timeout=1)
                with open(self._log_file_path, "a", encoding="utf-8") as f:
                    f.write(log_line + "\n")
            except Empty:
                continue

    def destroy(self):
        self._running = False
        self._thread.join(timeout=2)

    def write_exception_log(self, exc: Exception, folder: str = "exception"):
        os.makedirs(folder, exist_ok=True)
        file_path = os.path.join(folder, f"Exception_{datetime.datetime.now().strftime('%Y%m%d')}.log")
        with open(file_path, "a", encoding="utf-8") as f:
            f.write("=============Error Logging ===========\n")
            f.write(f"Time : {datetime.datetime.now()}\n")
            f.write(f"Exception Message : {str(exc)}\n")
            import traceback
            f.write(f"Stack Trace:\n{traceback.format_exc()}\n")
        self._print_console(LogLevel.FATAL, f"Exception: {exc}")
        # crash_report_url로 전송 등은 필요시 구현 

class Logger:
    _logger: Optional[LoggerInterface] = None

    @classmethod
    def init(cls, logger: LoggerInterface):
        cls._logger = logger
    @classmethod
    def is_active(cls) -> bool:
        return cls._logger is not None
    @classmethod
    def set_level(cls, level: LogLevel):
        if cls._logger:
            cls._logger.set_level(level)
    @classmethod
    def info(cls, log: str):
        if cls._logger:
            cls._logger.info(log)
    @classmethod
    def fatal(cls, log: str):
        if cls._logger:
            cls._logger.fatal(log)
    @classmethod
    def error(cls, log: str):
        if cls._logger:
            cls._logger.error(log)
    @classmethod
    def warn(cls, log: str):
        if cls._logger:
            cls._logger.warn(log)
    @classmethod
    def debug(cls, log: str):
        if cls._logger:
            cls._logger.debug(log)
    @classmethod
    def trace(cls, log: str):
        if cls._logger:
            cls._logger.trace(log) 

# 로그 레벨 파싱 함수
def parse_log_level(args):
    for arg in args:
        if arg.startswith("logLevel="):
            level_str = arg.split("=", 1)[1].upper()
            try:
                return LogLevel[level_str]
            except KeyError:
                pass
    return LogLevel.ALL