import sys
import os
from typing import List, Optional
from .logger import LogLevel

def parse_log_level(args: Optional[List[str]] = None) -> LogLevel:
    if args is None:
        args = sys.argv[1:]
    for arg in args:
        if arg.lower().startswith("loglevel="):
            level_str = arg.split("=", 1)[1].upper()
            try:
                return LogLevel[level_str]
            except KeyError:
                pass
    return LogLevel.ALL

def parse_app_env(args: Optional[List[str]] = None) -> str:
    if args is None:
        args = sys.argv[1:]
    # 1. 명령행 인자 우선
    for arg in args:
        if arg.lower().startswith("app_env="):
            return arg.split("=", 1)[1].upper()
    # 2. 환경변수
    return os.environ.get("APP_ENV", "RELEASE").upper() 