import sys
import os
import json
from fastapi import FastAPI

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)
from contextlib import asynccontextmanager
from service.core.logger import Logger, ConsoleLogger
from service.core.argparse_util import parse_log_level, parse_app_env
from template.base.template_context import TemplateContext, TemplateType
from template.account.account_template_impl import AccountTemplateImpl
from template.admin.admin_template_impl_simple import AdminTemplateImpl
from template.base.template_config import AppConfig
from service.db.database_service import DatabaseService
from service.db.database_config import DatabaseConfig
from service.cache.cache_service import CacheService
from service.cache.redis_cache_client_pool import RedisCacheClientPool
from service.cache.cache_config import CacheConfig
from service.service_container import ServiceContainer

# uvicorn base_server.application.base_web_server.main:app --reload --  logLevel=Debug

# 로그레벨, 환경 읽기
log_level = parse_log_level()
app_env = parse_app_env()

# 환경에 따라 config 파일명 결정
def get_config_filename():
    # 현재 파일의 디렉토리 경로
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    if app_env == "LOCAL":
        filename = "base_web_server-config_local.json"
    elif app_env == "DEBUG":
        filename = "base_web_server-config_debug.json"
    else:
        filename = "base_web_server-config.json"
    
    return os.path.join(current_dir, filename)

config_file = get_config_filename()

# 글로벌 데이터베이스 서비스
database_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global database_service
    
    Logger.init(ConsoleLogger(log_level))
    Logger.info(f"base_web_server 시작 (로그레벨: {log_level.name}, 환경: {app_env}, config: {config_file})")
    
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        Logger.info(f"Config 파일 로드 성공: {config_file}")
        
        # AppConfig 객체 생성
        app_config = AppConfig(**config_data)
        
        # 데이터베이스 서비스 초기화
        try:
            database_service = DatabaseService(app_config.databaseConfig)
            await database_service.init_service()
            
            # 서비스 컨테이너에 등록
            ServiceContainer.init(database_service)
            Logger.info("데이터베이스 서비스 초기화 및 컨테이너 등록 완료")
        except Exception as e:
            Logger.error(f"데이터베이스 서비스 초기화 실패: {e}")
            Logger.info("데이터베이스 없이 계속 진행")
        
        # 캐시 서비스 초기화
        cache_client_pool = RedisCacheClientPool(
            host=app_config.cacheConfig.host,
            port=app_config.cacheConfig.port,
            session_expire_time=app_config.cacheConfig.session_expire_seconds,
            app_id=app_config.templateConfig.appId,
            env=app_config.templateConfig.env,
            db=app_config.cacheConfig.db,
            password=app_config.cacheConfig.password
        )
        CacheService.Init(cache_client_pool)
        Logger.info("캐시 서비스 초기화 완료")
        
    except Exception as e:
        Logger.error(f"Config 파일 로드 실패: {config_file} - {e}")
        raise

    # 템플릿 등록
    TemplateContext.add_template(TemplateType.ADMIN, AdminTemplateImpl())
    TemplateContext.add_template(TemplateType.ACCOUNT, AccountTemplateImpl())
    Logger.info("템플릿 등록 완료")
    
    # Account protocol 콜백 설정
    from .routers.account import setup_account_protocol_callbacks
    setup_account_protocol_callbacks()
    Logger.info("Account protocol 콜백 설정 완료")
    
    yield
    
    # 정리
    if database_service:
        await database_service.close_service()
        Logger.info("데이터베이스 서비스 종료")
    
    # 캐시 서비스 정리
    if CacheService.is_initialized():
        await CacheService.shutdown()
        Logger.info("캐시 서비스 종료")



app = FastAPI(lifespan=lifespan)

# 라우터 등록
from .routers import account, admin
app.include_router(account.router, prefix="/api/account", tags=["account"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

@app.get("/")
def root():
    Logger.info("base_web_server 동작 중")
    return {
        "message": "base_web_server 동작 중",
        "log_level": log_level.name,
        "env": app_env,
        "config_file": config_file
    }