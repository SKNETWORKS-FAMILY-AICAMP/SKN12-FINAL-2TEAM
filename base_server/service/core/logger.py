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
    def close(self):
        """리소스 정리 - 필요한 경우 구현"""
        pass

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
    
    def close(self):
        """ConsoleLogger는 정리할 것 없음"""
        pass

class FileLogger(LoggerInterface):
    def __init__(self, log_level: LogLevel = LogLevel.INFO, use_console: bool = True, prefix: str = "App", folder: str = "log", crash_report_url: Optional[str] = None, timezone: str = "UTC", max_file_size_kb: int = 1024):
        self._log_level = log_level
        self._use_console = use_console
        self._prefix = prefix
        self._folder = folder
        self._crash_report_url = crash_report_url
        self._timezone = timezone
        self._max_file_size_bytes = max_file_size_kb * 1024  # KB to bytes
        self._log_queue = Queue()
        self._running = True
        self._current_date = None
        self._file_counter = 0
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
        
        # 시간대에 따른 현재 시간 구하기
        if self._timezone == "KST" or self._timezone == "Asia/Seoul":
            # 한국 시간 (UTC+9)
            import datetime as dt
            now = dt.datetime.utcnow() + dt.timedelta(hours=9)
            tz_suffix = "_KST"
        elif self._timezone == "UTC":
            now = datetime.datetime.utcnow()
            tz_suffix = "_UTC"
        else:
            # 기본값은 UTC
            now = datetime.datetime.utcnow()
            tz_suffix = "_UTC"
        
        # 현재 날짜 저장
        current_date_str = now.strftime('%Y-%m-%d')
        
        # 날짜가 변경되었으면 카운터 리셋
        if self._current_date != current_date_str:
            self._current_date = current_date_str
            self._file_counter = 0
        
        # 파일명 생성 (날짜_카운터_시간대) - 항상 카운터 포함
        filename = f"{self._prefix}_{current_date_str}_{self._file_counter:03d}{tz_suffix}.log"
            
        return os.path.join(self._folder, filename)

    def set_level(self, level: LogLevel):
        self._log_level = level

    def log(self, level: LogLevel, msg: str):
        if self._log_level != LogLevel.ALL and level > self._log_level:
            return
        
        # 시간대에 따른 현재 시간 구하기
        if self._timezone == "KST" or self._timezone == "Asia/Seoul":
            # 한국 시간 (UTC+9)
            now = (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).strftime("[%Y/%m/%d-%H:%M:%S KST]")
        else:
            # UTC
            now = datetime.datetime.utcnow().strftime("[%Y/%m/%d-%H:%M:%S UTC]")
            
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

    def _check_and_rotate_file(self):
        """파일 크기와 날짜를 체크하여 필요시 새 파일로 전환"""
        # 현재 날짜 체크 (시간대 반영)
        if self._timezone == "KST" or self._timezone == "Asia/Seoul":
            now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
        else:
            now = datetime.datetime.utcnow()
        
        current_date_str = now.strftime('%Y-%m-%d')
        
        # 날짜가 변경되었거나 파일이 없으면 새 파일 생성
        if self._current_date != current_date_str or not os.path.exists(self._log_file_path):
            self._log_file_path = self._make_log_file_path()
            return
            
        # 파일 크기 체크
        try:
            file_size = os.path.getsize(self._log_file_path)
            if file_size >= self._max_file_size_bytes:
                self._file_counter += 1
                self._log_file_path = self._make_log_file_path()
        except OSError:
            # 파일 접근 오류시 그대로 진행
            pass
    
    def _run(self):
        while self._running:
            try:
                log_line = self._log_queue.get(timeout=1)
                
                # 파일 로테이션 체크
                self._check_and_rotate_file()
                
                with open(self._log_file_path, "a", encoding="utf-8") as f:
                    f.write(log_line + "\n")
            except Empty:
                continue

    def close(self):
        """파일 로거 정리 - 큐에 있는 로그를 파일에 쓰고 스레드 종료"""
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
    def shutdown(cls):
        """Logger 종료"""
        if cls._logger:
            cls._logger.close()
            cls._logger = None
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