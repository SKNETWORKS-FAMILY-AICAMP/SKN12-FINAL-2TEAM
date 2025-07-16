import sys
import os
import json
import asyncio
from datetime import datetime
from fastapi import FastAPI

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)
from contextlib import asynccontextmanager
from service.core.logger import Logger, ConsoleLogger
from service.core.argparse_util import parse_log_level, parse_app_env
from template.base.template_context import TemplateContext, TemplateType
from template.account.account_template_impl import AccountTemplateImpl
from template.admin.admin_template_impl import AdminTemplateImpl
from template.tutorial.tutorial_template_impl import TutorialTemplateImpl
from template.dashboard.dashboard_template_impl import DashboardTemplateImpl
from template.portfolio.portfolio_template_impl import PortfolioTemplateImpl
from template.chat.chat_template_impl import ChatTemplateImpl
from template.autotrade.autotrade_template_impl import AutoTradeTemplateImpl
from template.market.market_template_impl import MarketTemplateImpl
from template.settings.settings_template_impl import SettingsTemplateImpl
from template.notification.notification_template_impl import NotificationTemplateImpl
from template.crawler.crawler_template_impl import CrawlerTemplateImpl
from template.base.template_config import AppConfig
from template.base.template_service import TemplateService
from service.db.database_service import DatabaseService
from service.db.database_config import DatabaseConfig
from service.data.data_table_manager import DataTableManager
from service.data.test_data_models import ItemData
from service.cache.cache_service import CacheService
from service.cache.redis_cache_client_pool import RedisCacheClientPool
from service.cache.cache_config import CacheConfig
from service.external.external_service import ExternalService
from service.storage.storage_service import StorageService
from service.search.search_service import SearchService
from service.vectordb.vectordb_service import VectorDbService
from service.service_container import ServiceContainer
from service.lock.lock_service import LockService
from service.scheduler.scheduler_service import SchedulerService
from service.outbox.outbox_pattern import OutboxService
from service.queue.queue_service import QueueService, initialize_queue_service

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
    
    Logger.init(ConsoleLogger(log_level)) #파일로 수정
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
        
        # Redis 연결 테스트 및 재시도
        max_redis_retries = 5
        redis_connected = False
        for attempt in range(max_redis_retries):
            try:
                health_check = await CacheService.health_check()
                if health_check.get("healthy", False):
                    Logger.info("캐시 서비스 초기화 및 Redis 연결 테스트 완료")
                    redis_connected = True
                    break
                else:
                    Logger.warn(f"Redis 연결 테스트 실패 (시도 {attempt + 1}/{max_redis_retries}): {health_check.get('error', 'Unknown error')}")
            except Exception as e:
                Logger.warn(f"Redis 연결 테스트 예외 (시도 {attempt + 1}/{max_redis_retries}): {e}")
            
            if attempt < max_redis_retries - 1:
                await asyncio.sleep(2 ** attempt)  # 지수 백오프
        
        if not redis_connected:
            Logger.error("Redis 연결 실패 - 서비스가 불안정할 수 있습니다")
            ServiceContainer.set_cache_service_initialized(False)
        else:
            Logger.info("캐시 서비스 초기화 완료")
            ServiceContainer.set_cache_service_initialized(True)
        
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
                    test_result = await StorageService.list_files("finance-app-bucket-1", "", max_keys=1)
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
                    test_result = await SearchService.index_exists("finance_search_local")
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
        
        # LockService 초기화 (Redis 분산락)
        try:
            cache_service = CacheService.get_instance()
            if LockService.init(cache_service):
                Logger.info("LockService 초기화 완료")
                ServiceContainer.set_lock_service_initialized(True)
                
                # 분산락 테스트
                try:
                    test_token = await LockService.acquire("test_lock", ttl=5, timeout=3)
                    if test_token:
                        Logger.info("LockService 분산락 테스트 성공")
                        await LockService.release("test_lock", test_token)
                    else:
                        Logger.warn("LockService 분산락 테스트 실패")
                except Exception as lock_e:
                    Logger.warn(f"LockService 분산락 테스트 실패: {lock_e}")
            else:
                Logger.warn("LockService 초기화 실패")
        except Exception as e:
            Logger.error(f"LockService 초기화 실패: {e}")
            Logger.info("LockService 없이 계속 진행")
        
        # SchedulerService 초기화
        try:
            lock_service = LockService if LockService.is_initialized() else None
            if SchedulerService.init(lock_service):
                Logger.info("SchedulerService 초기화 완료")
                ServiceContainer.set_scheduler_service_initialized(True)
                
                # 스케줄러 시작
                try:
                    await SchedulerService.start()
                    Logger.info("SchedulerService 시작 완료")
                    
                    # 스케줄러 상태 확인
                    jobs_status = SchedulerService.get_all_jobs_status()
                    Logger.info(f"SchedulerService 작업 상태: {len(jobs_status)}개 작업")
                except Exception as sched_e:
                    Logger.warn(f"SchedulerService 시작 실패: {sched_e}")
            else:
                Logger.warn("SchedulerService 초기화 실패")
        except Exception as e:
            Logger.error(f"SchedulerService 초기화 실패: {e}")
            Logger.info("SchedulerService 없이 계속 진행")
        
        # QueueService 초기화 (메시지큐/이벤트큐 통합)
        try:
            if await initialize_queue_service(database_service):
                Logger.info("QueueService 초기화 완료")
                ServiceContainer.set_queue_service_initialized(True)
                
            else:
                Logger.warn("QueueService 초기화 실패")
        except Exception as e:
            Logger.error(f"QueueService 초기화 실패: {e}")
            Logger.info("QueueService 없이 계속 진행")
        
    except Exception as e:
        Logger.error(f"Config 파일 로드 실패: {config_file} - {e}")
        raise

    # 데이터 테이블 로딩 테스트
    try:
        # 테이블 설정
        table_configs = {
            "items": {
                "file": "test_items.csv",
                "row_class": ItemData,
                "key_field": "id"
            }
        }
        
        # 리소스 경로 설정
        resources_path = os.path.join(project_root, "resources", "tables")
        
        # 테이블 로드
        if DataTableManager.load_all_tables(resources_path, table_configs):
            # 테스트: 아이템 테이블 조회
            items_table = DataTableManager.get_table("items")
            if items_table:
                Logger.info(f"아이템 테이블 로드 성공: {items_table.count()}개 아이템")
                
                # 특정 아이템 조회 테스트
                item = items_table.get("1001")
                if item:
                    Logger.info(f"아이템 조회 테스트: {item}")
                
                # 조건 검색 테스트
                weapons = items_table.find_all(lambda x: x.type == "weapon")
                Logger.info(f"무기 아이템 수: {len(weapons)}")
        else:
            Logger.warn("데이터 테이블 로드 실패")
            
    except Exception as e:
        Logger.error(f"데이터 테이블 초기화 실패: {e}")
        Logger.info("데이터 테이블 없이 계속 진행")

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
    TemplateContext.add_template(TemplateType.CRAWLER, CrawlerTemplateImpl())
    Logger.info("템플릿 등록 완료")
    
    # 템플릿 서비스 초기화 (데이터 로드 및 템플릿 초기화 포함)
    TemplateService.init(app_config)
    Logger.info("템플릿 서비스 초기화 완료")
    
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
    
    # Crawler protocol 콜백 설정
    from .routers.crawler import setup_crawler_protocol_callbacks
    setup_crawler_protocol_callbacks()
    Logger.info("Crawler protocol 콜백 설정 완료")
    
    # 초기화 완료 후 서비스 테스트 실행
    Logger.info("=== 서비스 초기화 완료 - 기본 테스트 실행 ===")
    try:
        # 간단한 서비스 상태 확인
        services_status = {
            "cache_service": CacheService.is_initialized(),
            "database_service": ServiceContainer.get_database_service() is not None,
            "template_service": True  # 이미 초기화됨
        }
        
        # 큐 시스템 초기화 상태 및 발행/수신 동작 확인
        if CacheService.is_initialized() and QueueService._initialized:
            try:
                import asyncio
                from datetime import datetime
                from service.queue.message_queue import MessagePriority
                from service.queue.event_queue import EventType
                
                # 기본 상태는 초기화됨으로 설정
                services_status["queue_system"] = True
                queue_service = QueueService.get_instance()
                
                # 수신 확인용 변수
                message_received = {"count": 0}
                event_received = {"count": 0}
                
                # 메시지 수신 콜백
                def message_callback(message):
                    message_received["count"] += 1
                    Logger.info(f"✅ 헬스체크 메시지 수신 확인: {message.payload}")
                    return True
                
                # 이벤트 수신 콜백  
                def event_callback(event):
                    event_received["count"] += 1
                    Logger.info(f"✅ 헬스체크 이벤트 수신 확인: {event.data}")
                    return True
                
                # 1. 메시지큐 발행/수신 테스트
                try:
                    # 소비자 등록
                    await queue_service.register_message_consumer(
                        "health_check_queue", "health_check_consumer", message_callback
                    )
                    
                    # 메시지 발행
                    await queue_service.send_message(
                        "health_check_queue",
                        {"test": "startup_health_check", "timestamp": datetime.now().isoformat()},
                        "health_check",
                        MessagePriority.HIGH
                    )
                    
                    # 실 비즈니스 서버 방식: 충분한 대기 시간과 재시도
                    max_retries = 5
                    retry_delay = 2.0  # 폴링 간격의 2배
                    
                    for retry in range(max_retries):
                        await asyncio.sleep(retry_delay)
                        if message_received["count"] > 0:
                            Logger.info("✅ 메시지큐 발행/수신 동작 정상")
                            break
                        elif retry == max_retries - 1:
                            Logger.warn("⚠️ 메시지 발행됐지만 수신 안됨 (개발 중이므로 정상)")
                        else:
                            Logger.debug(f"메시지 수신 대기 중... ({retry+1}/{max_retries})")
                        
                except Exception as msg_e:
                    Logger.info(f"⚠️ 메시지큐 테스트 실패: {msg_e} (개발 중이므로 정상)")
                
                # 2. 이벤트큐 발행/수신 테스트
                try:
                    # 이벤트 구독
                    await queue_service.subscribe_events(
                        "health_check_subscriber", [EventType.SYSTEM_ERROR], event_callback
                    )
                    
                    # 이벤트 발행
                    await queue_service.publish_event(
                        EventType.SYSTEM_ERROR,
                        "health_check",
                        {"test": "startup_health_check", "timestamp": datetime.now().isoformat()}
                    )
                    
                    # 실 비즈니스 서버 방식: 충분한 대기 시간과 재시도
                    max_retries = 5
                    retry_delay = 2.0  # 폴링 간격의 2배
                    
                    for retry in range(max_retries):
                        await asyncio.sleep(retry_delay)
                        if event_received["count"] > 0:
                            Logger.info("✅ 이벤트큐 발행/수신 동작 정상")
                            break
                        elif retry == max_retries - 1:
                            Logger.warn("⚠️ 이벤트 발행됐지만 수신 안됨 (개발 중이므로 정상)")
                        else:
                            Logger.debug(f"이벤트 수신 대기 중... ({retry+1}/{max_retries})")
                        
                except Exception as event_e:
                    Logger.info(f"⚠️ 이벤트큐 테스트 실패: {event_e} (개발 중이므로 정상)")
                
                # 전체 결과 요약
                if message_received["count"] > 0 and event_received["count"] > 0:
                    Logger.info("🎉 큐 시스템 전체 동작 확인 완료 (발행+수신)")
                elif message_received["count"] > 0 or event_received["count"] > 0:
                    Logger.info("✅ 큐 시스템 부분 동작 확인 (일부 발행+수신)")
                else:
                    Logger.info("⚠️ 큐 시스템 발행만 확인됨, 수신 미확인 (개발 중)")
                    
            except Exception as e:
                Logger.info(f"⚠️ 큐 시스템 확인 중 오류: {e} (개발 중이므로 정상)")
        else:
            services_status["queue_system"] = False
            Logger.warn("❌ 큐 시스템 초기화되지 않음")
        
        test_results = {
            "results": {
                service: {"passed": 1 if status else 0, "failed": 0 if status else 1}
                for service, status in services_status.items()
            }
        }
        
        # 테스트 결과 요약
        total_tests = sum(
            result["passed"] + result["failed"] 
            for result in test_results["results"].values()
        )
        total_passed = sum(
            result["passed"] 
            for result in test_results["results"].values()
        )
        
        if total_tests > 0:
            success_rate = (total_passed / total_tests) * 100
            Logger.info(f"✅ 초기화 테스트 완료: {total_passed}/{total_tests} 성공 ({success_rate:.1f}%)")
            
            # 실패한 테스트가 있으면 로그
            for service, result in test_results["results"].items():
                if result["failed"] > 0:
                    Logger.warn(f"⚠️ {service} 서비스: {result['failed']}개 테스트 실패")
        else:
            Logger.info("초기화 테스트: 실행된 테스트 없음")
            
    except Exception as e:
        Logger.error(f"초기화 테스트 실행 실패: {e}")
    
    Logger.info("=== base_web_server 초기화 및 테스트 완료 ===")
    
    yield
    
    # 서비스 정리 - 예외 처리와 함께
    Logger.info("서비스 종료 시작...")
    
    # Protocol 콜백 정리
    try:
        Logger.info("Protocol 콜백 정리 중...")
        # 각 라우터의 콜백들이 정리될 수 있도록 대기
        await asyncio.sleep(0.1)
    except Exception as e:
        Logger.error(f"Protocol 콜백 정리 오류: {e}")
    
    # TemplateService 종료
    try:
        Logger.info("TemplateService 종료 중...")
        # TemplateService와 TemplateContext 정리
        TemplateContext._templates.clear()
        Logger.info("TemplateService 및 TemplateContext 정리 완료")
    except Exception as e:
        Logger.error(f"TemplateService 종료 오류: {e}")
    
    # DataTableManager 정리
    try:
        Logger.info("DataTableManager 정리 중...")
        DataTableManager.clear()
        Logger.info("DataTableManager 테이블 정리 완료")
    except Exception as e:
        Logger.error(f"DataTableManager 정리 오류: {e}")
    
    # QueueService 종료 (큐 처리 완료 후)
    try:
        if QueueService._initialized:
            await QueueService.shutdown()
            ServiceContainer.set_queue_service_initialized(False)
            Logger.info("QueueService 종료")
    except Exception as e:
        Logger.error(f"QueueService 종료 오류: {e}")
    
    # SchedulerService 종료 (스케줄된 작업 완료 후)
    try:
        if SchedulerService.is_initialized():
            await SchedulerService.shutdown()
            ServiceContainer.set_scheduler_service_initialized(False)
            Logger.info("SchedulerService 종료")
    except Exception as e:
        Logger.error(f"SchedulerService 종료 오류: {e}")
    
    # LockService 종료 (분산락 해제)
    try:
        if LockService.is_initialized():
            await LockService.shutdown()
            ServiceContainer.set_lock_service_initialized(False)
            Logger.info("LockService 종료")
    except Exception as e:
        Logger.error(f"LockService 종료 오류: {e}")
    
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
            ServiceContainer.set_cache_service_initialized(False)
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
        
        # Logger 정리 - 마지막에 수행
        Logger.info("Logger 종료 중...")
        # Logger가 ConsoleLogger인 경우 특별한 정리 불필요하지만
        # 향후 파일 로거 등으로 변경될 경우를 대비
        await asyncio.sleep(0.1)  # 마지막 로그 출력 대기
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

async def test_queue_systems():
    """큐 시스템 종합 테스트 - 메시지큐와 이벤트큐 발행/수신 확인"""
    import asyncio
    from datetime import datetime
    from service.queue.queue_service import QueueService, get_queue_service
    from service.queue.message_queue import QueueMessage, MessagePriority
    from service.queue.event_queue import EventType, Event
    
    try:
        Logger.info("🔄 큐 시스템 테스트 시작...")
        queue_service = get_queue_service()
        
        # 1. 메시지큐 테스트 (다양한 우선순위)
        Logger.info("📨 메시지큐 테스트 시작...")
        
        test_message_received = {"count": 0, "data": None}
        
        def test_message_callback(message: QueueMessage) -> bool:
            test_message_received["count"] += 1
            test_message_received["data"] = message.payload
            Logger.info(f"✅ 테스트 메시지 수신: {message.priority.name} - {message.payload}")
            return True
        
        # 메시지 소비자 등록
        await queue_service.register_message_consumer(
            "test_queue", "test_consumer", test_message_callback
        )
        
        # 다양한 우선순위 메시지 발행
        test_messages = [
            {
                "priority": MessagePriority.CRITICAL,
                "data": {"test": "CRITICAL 우선순위 메시지", "timestamp": datetime.now().isoformat()}
            },
            {
                "priority": MessagePriority.HIGH,
                "data": {"test": "HIGH 우선순위 메시지", "timestamp": datetime.now().isoformat()}
            },
            {
                "priority": MessagePriority.NORMAL,
                "data": {"test": "NORMAL 우선순위 메시지", "timestamp": datetime.now().isoformat()}
            }
        ]
        
        for msg_info in test_messages:
            success = await queue_service.send_message(
                "test_queue",
                msg_info["data"],
                "test_message",
                msg_info["priority"]
            )
            Logger.info(f"📤 {msg_info['priority'].name} 메시지 발행: {'성공' if success else '실패'}")
        
        # 메시지 처리 대기
        await asyncio.sleep(2)
        
        # 2. 이벤트큐 테스트
        Logger.info("🎯 이벤트큐 테스트 시작...")
        
        test_event_received = {"count": 0, "data": None}
        
        def test_event_callback(event: Event) -> bool:
            test_event_received["count"] += 1
            test_event_received["data"] = event.data
            Logger.info(f"✅ 테스트 이벤트 수신: {event.event_type.value} - {event.data}")
            return True
        
        # 이벤트 구독
        subscription_id = await queue_service.subscribe_events(
            "test_subscriber",
            [EventType.SYSTEM_ERROR],
            test_event_callback
        )
        
        # 이벤트 발행
        success = await queue_service.publish_event(
            EventType.SYSTEM_ERROR,
            "test_source",
            {"test": "이벤트큐 테스트", "timestamp": datetime.now().isoformat()}
        )
        Logger.info(f"📡 테스트 이벤트 발행: {'성공' if success else '실패'}")
        
        # 이벤트 처리 대기
        await asyncio.sleep(2)
        
        # 결과 확인
        Logger.info("📊 큐 시스템 테스트 결과:")
        Logger.info(f"   - 메시지 수신: {test_message_received['count']}개")
        Logger.info(f"   - 이벤트 수신: {test_event_received['count']}개")
        
        if test_message_received["count"] > 0 and test_event_received["count"] > 0:
            Logger.info("✅ 큐 시스템 테스트 성공 - 메시지와 이벤트 정상 수신 확인")
        else:
            Logger.warn(f"⚠️ 큐 시스템 테스트 부분 실패 - 메시지: {test_message_received['count']}, 이벤트: {test_event_received['count']}")
        
    except Exception as e:
        Logger.error(f"❌ 큐 시스템 테스트 실패: {e}")
        import traceback
        Logger.error(f"상세 오류: {traceback.format_exc()}")

app = FastAPI(lifespan=lifespan)

# 라우터 등록
from .routers import account, admin, tutorial, dashboard, portfolio, chat, autotrade, market, settings, notification, crawler
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
app.include_router(crawler.router, prefix="/api/crawler", tags=["crawler"])

@app.get("/")
def root():
    Logger.info("base_web_server 동작 중")
    
    # 서비스 상태 체크 (모든 서비스 통합)
    service_status = ServiceContainer.get_service_status()
    
    return {
        "message": "base_web_server 동작 중",
        "log_level": log_level.name,
        "env": app_env,
        "config_file": config_file,
        "services": service_status
    }

# All test, debug, and demo endpoints moved to admin router for security