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
from template.tutorial.tutorial_template_impl import TutorialTemplateImpl
from template.dashboard.dashboard_template_impl import DashboardTemplateImpl
from template.portfolio.portfolio_template_impl import PortfolioTemplateImpl
from template.chat.chat_template_impl import ChatTemplateImpl
from template.autotrade.autotrade_template_impl import AutoTradeTemplateImpl
from template.market.market_template_impl import MarketTemplateImpl
from template.settings.settings_template_impl import SettingsTemplateImpl
from template.notification.notification_template_impl import NotificationTemplateImpl
from template.base.template_config import AppConfig
from service.db.database_service import DatabaseService
from service.db.database_config import DatabaseConfig
from service.cache.cache_service import CacheService
from service.cache.redis_cache_client_pool import RedisCacheClientPool
from service.cache.cache_config import CacheConfig
from service.external.external_service import ExternalService
from service.storage.storage_service import StorageService
from service.search.search_service import SearchService
from service.vectordb.vectordb_service import VectorDbService
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
            password=app_config.cacheConfig.password,
            max_retries=app_config.cacheConfig.max_retries,
            connection_timeout=app_config.cacheConfig.connection_timeout
        )
        CacheService.Init(cache_client_pool)
        Logger.info("캐시 서비스 초기화 완료")
        
        # External 서비스 초기화
        try:
            await ExternalService.init(app_config.externalConfig)
            Logger.info("External 서비스 초기화 완료")
            
            # 테스트 API 호출 (httpbin.org/get - 무조건 응답하는 테스트 엔드포인트)
            test_result = await ExternalService.get("test_api", "/get")
            if test_result["success"]:
                Logger.info(f"External 서비스 테스트 성공: {test_result['data'].get('url', 'N/A')}")
            else:
                Logger.warn(f"External 서비스 테스트 실패: {test_result.get('error', 'Unknown')}")
                
        except Exception as e:
            Logger.error(f"External 서비스 초기화 실패: {e}")
            Logger.info("External 서비스 없이 계속 진행")
        
        # Storage 서비스 초기화 (S3)
        try:
            if StorageService.init(app_config.storageConfig):
                Logger.info("Storage 서비스 초기화 완료")
                
                # AWS 연결 테스트
                try:
                    test_result = await StorageService.list_files("test-bucket", "", max_keys=1)
                    if test_result["success"]:
                        Logger.info("Storage 서비스 AWS 연결 성공")
                    else:
                        Logger.warn(f"Storage 서비스 AWS 연결 실패: {test_result.get('error', 'Unknown')}")
                except Exception as conn_e:
                    Logger.warn(f"Storage 서비스 AWS 연결 테스트 실패: {conn_e}")
            else:
                Logger.warn("Storage 서비스 초기화 실패")
        except Exception as e:
            Logger.error(f"Storage 서비스 초기화 실패: {e}")
            Logger.info("Storage 서비스 없이 계속 진행")
        
        # Search 서비스 초기화 (OpenSearch)
        try:
            if SearchService.init(app_config.searchConfig):
                Logger.info("Search 서비스 초기화 완료")
                
                # OpenSearch 연결 테스트
                try:
                    test_result = await SearchService.index_exists("test-index")
                    if test_result["success"]:
                        Logger.info("Search 서비스 OpenSearch 연결 성공")
                    else:
                        Logger.warn(f"Search 서비스 OpenSearch 연결 실패: {test_result.get('error', 'Unknown')}")
                except Exception as conn_e:
                    Logger.warn(f"Search 서비스 OpenSearch 연결 테스트 실패: {conn_e}")
            else:
                Logger.warn("Search 서비스 초기화 실패")
        except Exception as e:
            Logger.error(f"Search 서비스 초기화 실패: {e}")
            Logger.info("Search 서비스 없이 계속 진행")
        
        # VectorDB 서비스 초기화 (Bedrock)
        try:
            if VectorDbService.init(app_config.vectordbConfig):
                Logger.info("VectorDB 서비스 초기화 완료")
                
                # Bedrock 연결 테스트
                try:
                    test_result = await VectorDbService.embed_text("test connection")
                    if test_result["success"]:
                        Logger.info("VectorDB 서비스 Bedrock 연결 성공")
                    else:
                        Logger.warn(f"VectorDB 서비스 Bedrock 연결 실패: {test_result.get('error', 'Unknown')}")
                except Exception as conn_e:
                    Logger.warn(f"VectorDB 서비스 Bedrock 연결 테스트 실패: {conn_e}")
            else:
                Logger.warn("VectorDB 서비스 초기화 실패")
        except Exception as e:
            Logger.error(f"VectorDB 서비스 초기화 실패: {e}")
            Logger.info("VectorDB 서비스 없이 계속 진행")
        
    except Exception as e:
        Logger.error(f"Config 파일 로드 실패: {config_file} - {e}")
        raise

    # 템플릿 등록
    TemplateContext.add_template(TemplateType.ADMIN, AdminTemplateImpl())
    TemplateContext.add_template(TemplateType.ACCOUNT, AccountTemplateImpl())
    TemplateContext.add_template(TemplateType.TUTORIAL, TutorialTemplateImpl())
    TemplateContext.add_template(TemplateType.DASHBOARD, DashboardTemplateImpl())
    TemplateContext.add_template(TemplateType.PORTFOLIO, PortfolioTemplateImpl())
    TemplateContext.add_template(TemplateType.CHAT, ChatTemplateImpl())
    TemplateContext.add_template(TemplateType.AUTOTRADE, AutoTradeTemplateImpl())
    TemplateContext.add_template(TemplateType.MARKET, MarketTemplateImpl())
    TemplateContext.add_template(TemplateType.SETTINGS, SettingsTemplateImpl())
    TemplateContext.add_template(TemplateType.NOTIFICATION, NotificationTemplateImpl())
    Logger.info("템플릿 등록 완료")
    
    # Account protocol 콜백 설정
    from .routers.account import setup_account_protocol_callbacks
    setup_account_protocol_callbacks()
    Logger.info("Account protocol 콜백 설정 완료")
    
    # Admin protocol 콜백 설정
    from .routers.admin import setup_admin_protocol_callbacks
    setup_admin_protocol_callbacks()
    Logger.info("Admin protocol 콜백 설정 완료")
    
    # Tutorial protocol 콜백 설정
    from .routers.tutorial import setup_tutorial_protocol_callbacks
    setup_tutorial_protocol_callbacks()
    Logger.info("Tutorial protocol 콜백 설정 완료")
    
    # Dashboard protocol 콜백 설정
    from .routers.dashboard import setup_dashboard_protocol_callbacks
    setup_dashboard_protocol_callbacks()
    Logger.info("Dashboard protocol 콜백 설정 완료")
    
    # Portfolio protocol 콜백 설정
    from .routers.portfolio import setup_portfolio_protocol_callbacks
    setup_portfolio_protocol_callbacks()
    Logger.info("Portfolio protocol 콜백 설정 완료")
    
    # Chat protocol 콜백 설정
    from .routers.chat import setup_chat_protocol_callbacks
    setup_chat_protocol_callbacks()
    Logger.info("Chat protocol 콜백 설정 완료")
    
    # AutoTrade protocol 콜백 설정
    from .routers.autotrade import setup_autotrade_protocol_callbacks
    setup_autotrade_protocol_callbacks()
    Logger.info("AutoTrade protocol 콜백 설정 완료")
    
    # Market protocol 콜백 설정
    from .routers.market import setup_market_protocol_callbacks
    setup_market_protocol_callbacks()
    Logger.info("Market protocol 콜백 설정 완료")
    
    # Settings protocol 콜백 설정
    from .routers.settings import setup_settings_protocol_callbacks
    setup_settings_protocol_callbacks()
    Logger.info("Settings protocol 콜백 설정 완료")
    
    # Notification protocol 콜백 설정
    from .routers.notification import setup_notification_protocol_callbacks
    setup_notification_protocol_callbacks()
    Logger.info("Notification protocol 콜백 설정 완료")
    
    yield
    
    # 서비스 정리 - 예외 처리와 함께
    Logger.info("서비스 종료 시작...")
    
    # VectorDB 서비스 종료 (Bedrock 세션 먼저)
    try:
        if VectorDbService.is_initialized():
            await VectorDbService.shutdown()
            Logger.info("VectorDB 서비스 종료")
    except Exception as e:
        Logger.error(f"VectorDB 서비스 종료 오류: {e}")
    
    # Search 서비스 종료 (OpenSearch 세션)
    try:
        if SearchService.is_initialized():
            await SearchService.shutdown()
            Logger.info("Search 서비스 종료")
    except Exception as e:
        Logger.error(f"Search 서비스 종료 오류: {e}")
    
    # Storage 서비스 종료 (S3 세션)
    try:
        if StorageService.is_initialized():
            await StorageService.shutdown()
            Logger.info("Storage 서비스 종료")
    except Exception as e:
        Logger.error(f"Storage 서비스 종료 오류: {e}")
        
    # External 서비스 종료 (HTTP 세션)  
    try:
        if ExternalService.is_initialized():
            await ExternalService.shutdown()
            Logger.info("External 서비스 종료")
    except Exception as e:
        Logger.error(f"External 서비스 종료 오류: {e}")
        
    # 캐시 서비스 종료 (Redis 연결)
    try:
        if CacheService.is_initialized():
            await CacheService.shutdown()
            Logger.info("캐시 서비스 종료")
    except Exception as e:
        Logger.error(f"캐시 서비스 종료 오류: {e}")
    
    # 데이터베이스 서비스 종료 (마지막)
    try:
        if database_service:
            await database_service.close_service()
            Logger.info("데이터베이스 서비스 종료")
    except Exception as e:
        Logger.error(f"데이터베이스 서비스 종료 오류: {e}")
    
    # 진행 중인 작업들 완료 대기
    try:
        import asyncio
        import gc
        
        # 가비지 컬렉션 강제 실행
        gc.collect()
        
        # 간단한 대기만 수행 (작업 취소는 uvicorn에 맡김)
        await asyncio.sleep(0.2)  # 짧은 대기
        Logger.info("모든 서비스 종료 완료")
        
        # 활성 스레드 수 확인
        import threading
        active_threads = threading.active_count()
        Logger.info(f"Active threads: {active_threads}")
        
    except Exception as e:
        Logger.error(f"종료 대기 오류: {e}")
    
    # 리소스 정리 완료 로그
    try:
        Logger.info("전역 리소스 정리 완료")
        Logger.info("Application lifespan ended")
    except Exception as e:
        Logger.error(f"전역 리소스 정리 오류: {e}")


# 전역 종료 핸들러 추가
import signal
import sys

def signal_handler(signum, frame):
    """SIGINT/SIGTERM 시그널 핸들러"""
    Logger.info(f"Signal {signum} received. Shutting down gracefully...")
    
    # 정상 종료 시도
    try:
        sys.exit(0)
    except SystemExit:
        # 만약 정상 종료가 실패하면 강제 종료
        import os
        Logger.info("Force exiting...")
        os._exit(0)

# 시그널 핸들러 등록
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

app = FastAPI(lifespan=lifespan)

# 라우터 등록
from .routers import account, admin, tutorial, dashboard, portfolio, chat, autotrade, market, settings, notification
app.include_router(account.router, prefix="/api/account", tags=["account"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(tutorial.router, prefix="/api/tutorial", tags=["tutorial"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["portfolio"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(autotrade.router, prefix="/api/autotrade", tags=["autotrade"])
app.include_router(market.router, prefix="/api/market", tags=["market"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(notification.router, prefix="/api/notification", tags=["notification"])

@app.get("/")
def root():
    Logger.info("base_web_server 동작 중")
    return {
        "message": "base_web_server 동작 중",
        "log_level": log_level.name,
        "env": app_env,
        "config_file": config_file
    }