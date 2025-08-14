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
    return LogLevel.ERROR

def parse_app_env(args: Optional[List[str]] = None) -> str:
    """
    애플리케이션 환경을 결정합니다.
    
    🎯 목적: main.py에서 어떤 config 파일을 로드할지 결정
    - LOCAL → base_web_server-config_local.json
    - DEBUG → base_web_server-config_debug.json  
    - PROD/RELEASE → base_web_server-config.json
    
    🔄 우선순위 (Docker/CI/CD 친화적으로 환경변수 우선):
    1. 환경변수 APP_ENV (Docker에서 -e APP_ENV=PROD)
    2. 명령행 인자 app_env=VALUE (로컬 개발용, 기존 호환성)
    3. 기본값 RELEASE (아무것도 설정 안 했을 때)
    
    📝 사용 예시:
    - Docker: docker run -e APP_ENV=PROD 
    - 로컬: uvicorn main:app app_env=LOCAL
    - CI/CD: export APP_ENV=DEBUG
    
    Args:
        args: 명령행 인자 리스트 (None이면 sys.argv 사용)
        
    Returns:
        str: 환경 이름 (LOCAL, DEBUG, PROD, RELEASE 등 - 항상 대문자)
    """
    if args is None:
        args = sys.argv[1:]
    
    # 🥇 1순위: 환경변수 APP_ENV (Docker/CI/CD에서 표준적)
    env_from_env = os.environ.get("APP_ENV")
    if env_from_env:
        return env_from_env.upper()
    
    # 🥈 2순위: 명령행 인자 app_env=VALUE (로컬 개발용, 기존 호환성 유지)
    for arg in args:
        if arg.lower().startswith("app_env="):
            return arg.split("=", 1)[1].upper()
    
    # 🥉 3순위: 기본값 RELEASE (아무 설정도 없을 때)
    return "RELEASE" 