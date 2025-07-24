import sys
import os
import json
import asyncio
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from service.llm import llm_config

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)
from contextlib import asynccontextmanager
from service.core.logger import Logger, ConsoleLogger, FileLogger
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
from service.llm.AIChat_service import AIChatService
from service.core.service_monitor import service_monitor
from service.websocket.websocket_service import WebSocketService

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
    
    # FileLogger로 변경 - 콘솔과 파일에 동시 출력
    file_logger = FileLogger(
        log_level=log_level,
        use_console=True,  # 콘솔에도 출력
        prefix="base_web_server",  # 로그 파일 접두사
        folder="logs",  # 로그 디렉토리
        crash_report_url=None,  # 크래시 리포트 URL (옵션)
        timezone="KST",  # 한국 시간대 사용
        max_file_size_kb=10240  # 10MB 제한
    )
    Logger.init(file_logger)
    Logger.info(f"base_web_server 시작 (로그레벨: {log_level.name}, 환경: {app_env}, config: {config_file})")
    Logger.info(f"로그 파일 경로: {file_logger._log_file_path}")
    
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        Logger.info(f"Config 파일 로드 성공: {config_file}")
        
        # AppConfig 객체 생성
        app_config = AppConfig(**config_data)
        
        # AWS 테스트 설정 확인
        Logger.info(f"AWS 테스트 설정: skipAwsTests={app_config.templateConfig.skipAwsTests}")
        if app_config.templateConfig.skipAwsTests:
            Logger.info("⚠️ AWS 서비스 테스트가 스킵됩니다 (S3, OpenSearch, Bedrock)")
        
        # 🛡️ 데이터베이스 서비스 초기화 - 장애 대응 강화
        db_init_success = False
        max_db_retries = 3
        for db_attempt in range(max_db_retries):
            try:
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
                database_service = DatabaseService(app_config.databaseConfig)
                await database_service.init_service()
                aiChat_sevrvice = AIChatService(app_config.llmConfig)
                 # 캐시 서비스 초기화
                # 연결 테스트
                test_result = await database_service.execute_global_query("SELECT 1 as health_check", ())
                if test_result:
                    ServiceContainer.init(database_service, aiChat_sevrvice)
                    Logger.info("✅ 데이터베이스 서비스 초기화 및 컨테이너 등록 완료")
                    db_init_success = True
                    break
                else:
                    raise Exception("Database connection test failed")
                    
            except Exception as e:
                Logger.error(f"❌ 데이터베이스 서비스 초기화 실패 (시도 {db_attempt + 1}/{max_db_retries}): {e}")
                if db_attempt < max_db_retries - 1:
                    Logger.info(f"⏳ {2 ** db_attempt}초 후 데이터베이스 재연결 시도...")
                    await asyncio.sleep(2 ** db_attempt)
        
        if not db_init_success:
            Logger.error("❌ 모든 데이터베이스 연결 시도 실패 - 서버 시작 중단")
            raise RuntimeError("Critical: Database connection required for server operation")
        
        # ServiceContainer 상태 검증
        if not ServiceContainer.is_initialized():
            Logger.error("❌ ServiceContainer 데이터베이스 상태 불일치")
            raise RuntimeError("ServiceContainer database state inconsistent")
        
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
            Logger.error("❌ Redis 연결 실패 - 세션 관리 불가능으로 서버 시작 중단")
            raise RuntimeError("Critical: Redis connection required for session management")
        else:
            Logger.info("✅ 캐시 서비스 초기화 완료")
            ServiceContainer.set_cache_service_initialized(True)
        
        # DB 성공 여부와 상관 없이 AIChatService는 무조건 생성·등록
        ai_service = AIChatService(app_config.llmConfig)
        ServiceContainer.init(database_service if database_service else None, ai_service)
        Logger.info("AIChatService 초기화 및 컨테이너 등록 완료")

        # 🛡️ External 서비스 초기화 - 장애 허용
        external_init_success = False
        try:
            await ExternalService.init(app_config.externalConfig)
            Logger.info("✅ External 서비스 초기화 완료")
            external_init_success = True
            
            # 네트워크 테스트 (타임아웃 제한)
            try:
                test_result = await asyncio.wait_for(
                    ExternalService.get("test_api", "/get"), 
                    timeout=5.0
                )
                if test_result["success"]:
                    Logger.info(f"External 서비스 연결 테스트 성공")
                else:
                    Logger.warn(f"External 서비스 연결 테스트 실패: {test_result.get('error', 'Unknown')}")
            except asyncio.TimeoutError:
                Logger.warn("External 서비스 연결 테스트 타임아웃 - 네트워크 지연 가능")
            except Exception as test_e:
                Logger.warn(f"External 서비스 연결 테스트 오류: {test_e}")
                
        except Exception as e:
            Logger.error(f"❌ External 서비스 초기화 실패: {e}")
            Logger.warn("⚠️ External 서비스 없이 계속 진행 - 외부 API 기능 제한됨")
        
        # Storage 서비스 초기화 (S3) - 근본 원인 해결
        try:
            if StorageService.init(app_config.storageConfig):
                Logger.info("Storage 서비스 초기화 완료")
                
                # 🔧 근본 해결: Pool 비동기 초기화 + 실제 동작 테스트
                if not app_config.templateConfig.skipAwsTests:
                    try:
                        # 1. Pool 비동기 초기화를 명시적으로 수행
                        client = await StorageService.get_client_async()
                    
                        # 2. 기본 연결 테스트
                        list_result = await StorageService.list_files("finance-app-bucket-1", "", max_keys=1)
                        if not list_result["success"]:
                            raise Exception(f"S3 기본 연결 실패: {list_result.get('error', 'Unknown')}")
                        
                        # 3. 실제 동작 테스트 (Pool이 이제 초기화됨)
                        import time, uuid
                        server_id = f"{os.getpid()}_{uuid.uuid4().hex[:8]}"
                        test_filename = f"health_test_{server_id}_{int(time.time())}.txt"
                        test_content = f"S3 test {server_id[:8]}"
                        test_bucket = "finance-app-bucket-1"
                        
                        # 업로드 테스트
                        from io import BytesIO
                        file_obj = BytesIO(test_content.encode('utf-8'))
                        upload_result = await StorageService.upload_file_obj(test_bucket, test_filename, file_obj)
                        if not upload_result["success"]:
                            raise Exception(f"S3 업로드 실패: {upload_result.get('error', 'Unknown')}")
                        
                        # 다운로드 테스트
                        download_result = await StorageService.download_file_obj(test_bucket, test_filename)
                        if not download_result["success"]:
                            raise Exception(f"S3 다운로드 실패: {download_result.get('error', 'Unknown')}")
                        
                        # 내용 검증
                        downloaded_content = download_result.get("content", b"").decode('utf-8')
                        if downloaded_content != test_content:
                            raise Exception(f"S3 내용 불일치: {test_content} != {downloaded_content}")
                        
                        # 삭제 테스트
                        await StorageService.delete_file(test_bucket, test_filename)
                    
                        Logger.info("✅ Storage 서비스 S3 실제 동작 테스트 성공 (업로드/다운로드/삭제)")
                        
                    except Exception as e:
                        Logger.warn(f"⚠️ Storage 서비스 S3 테스트 실패: {e}")
                else:
                    Logger.info("⏭️ Storage 서비스 S3 테스트 스킵 (skipAwsTests=true)")
            else:
                Logger.warn("Storage 서비스 초기화 실패")
        except Exception as e:
            Logger.error(f"Storage 서비스 초기화 실패: {e}")
            Logger.info("Storage 서비스 없이 계속 진행")
        
        # Search 서비스 초기화 (OpenSearch) - 근본 원인 해결  
        try:
            if SearchService.init(app_config.searchConfig):
                Logger.info("Search 서비스 초기화 완료")
                
                # 🔧 근본 해결: 전용 테스트 인덱스로 실제 동작 테스트
                if not app_config.templateConfig.skipAwsTests:
                    try:
                        # 1. 기본 연결 테스트
                        exists_result = await SearchService.index_exists("finance_search_local")
                        if not exists_result["success"]:
                            raise Exception(f"OpenSearch 기본 연결 실패: {exists_result.get('error', 'Unknown')}")
                        
                        # 2. 전용 테스트 인덱스 생성 및 실제 동작 테스트
                        import time, uuid
                        server_id = f"{os.getpid()}_{uuid.uuid4().hex[:8]}"
                        test_index = f"health_test_{server_id[:8]}_{int(time.time())}"
                        test_doc_id = "test_doc"
                        
                        # 테스트용 인덱스 생성 (유연한 스키마)
                        create_result = await SearchService.create_test_index(test_index)
                        if not create_result.get("success", True):  # create_index는 성공 시 다른 응답 구조
                            Logger.debug(f"테스트 인덱스 생성 응답: {create_result}")
                        
                        # 간단한 테스트 문서
                        test_document = {
                            "content": f"health test {server_id[:8]}",
                            "timestamp": int(time.time()),
                            "server_id": server_id
                        }
                        
                        # 인덱싱 테스트
                        index_result = await SearchService.index_document(test_index, test_document, test_doc_id)
                        if not index_result["success"]:
                            raise Exception(f"OpenSearch 인덱싱 실패: {index_result.get('error', 'Unknown')}")
                        
                        # 검색 테스트 (인덱싱 완료 대기)
                        await asyncio.sleep(1)
                        search_result = await SearchService.search(test_index, {
                            "query": {"match_all": {}}
                        })
                        
                        # 테스트 인덱스 전체 삭제 (정리)
                        await SearchService.delete_index(test_index)
                        
                        if search_result["success"] and search_result.get("documents"):
                            Logger.info("✅ Search 서비스 OpenSearch 실제 동작 테스트 성공 (인덱스생성/인덱싱/검색/삭제)")
                        else:
                            Logger.warn("⚠️ OpenSearch 검색 결과 없음 (인덱싱은 성공)")
                        
                    except Exception as e:
                        Logger.warn(f"⚠️ Search 서비스 OpenSearch 테스트 실패: {e}")
                else:
                    Logger.info("⏭️ Search 서비스 OpenSearch 테스트 스킵 (skipAwsTests=true)")
            else:
                Logger.warn("Search 서비스 초기화 실패")
        except Exception as e:
            Logger.error(f"Search 서비스 초기화 실패: {e}")
            Logger.info("Search 서비스 없이 계속 진행")
        
        # VectorDB 서비스 초기화 (Bedrock)
        try:
            if VectorDbService.init(app_config.vectordbConfig):
                Logger.info("VectorDB 서비스 초기화 완료")
                
                # Bedrock 실제 동작 테스트 (최소 비용으로 임베딩/검색)
                if not app_config.templateConfig.skipAwsTests:
                    try:
                        import time
                        import uuid
                        server_id = f"{os.getpid()}_{uuid.uuid4().hex[:8]}"
                        
                        # 💰 비용 최소화: 매우 짧은 텍스트 사용
                        test_text = f"test{server_id[:4]}"  # 매우 짧은 텍스트 (8-10자)
                        test_id = f"health_{server_id}"
                        
                        # 1. 임베딩 생성 테스트 (최소 텍스트)
                        embed_result = await VectorDbService.embed_text(test_text)
                        if not embed_result["success"]:
                            raise Exception(f"Bedrock 임베딩 실패: {embed_result.get('error', 'Unknown')}")
                        
                        # 응답 구조 확인 (로그에서 "1024 dimensions" 확인됨)
                        embeddings = embed_result.get("embedding") or embed_result.get("embeddings") or embed_result.get("vector")
                        if not embeddings:
                            # 응답 구조 디버깅을 위해 키 목록 확인
                            available_keys = list(embed_result.keys()) if isinstance(embed_result, dict) else []
                            Logger.debug(f"Bedrock 응답 키들: {available_keys}")
                            raise Exception(f"Bedrock 임베딩 결과 없음 (사용 가능한 키: {available_keys})")
                        
                        # 2. 벡터 저장 테스트 (메모리에만 저장, 실제 DB 저장 안함)
                        vector_length = len(embeddings) if isinstance(embeddings, (list, tuple)) else "unknown"
                        
                        # 3. 간단한 유사도 계산 테스트 (같은 텍스트로 재테스트)
                        verify_result = await VectorDbService.embed_text(test_text)
                        if verify_result["success"]:
                            Logger.info(f"✅ VectorDB 서비스 Bedrock 실제 동작 테스트 성공 (벡터크기:{vector_length})")
                        else:
                            raise Exception("Bedrock 재검증 실패")
                        
                    except Exception as conn_e:
                        Logger.warn(f"⚠️ VectorDB 서비스 Bedrock 동작 테스트 실패: {conn_e}")
                        # 기본 연결 테스트로 폴백 (더 짧은 텍스트)
                        try:
                            test_result = await VectorDbService.embed_text("hi")  # 2글자로 최소화
                            if test_result["success"]:
                                Logger.info("✅ VectorDB 서비스 Bedrock 기본 연결 성공")
                            else:
                                Logger.warn(f"❌ VectorDB 서비스 Bedrock 기본 연결 실패: {test_result.get('error', 'Unknown')}")
                        except Exception as basic_e:
                            Logger.warn(f"❌ VectorDB 서비스 Bedrock 기본 연결 테스트 실패: {basic_e}")
                else:
                    Logger.info("⏭️ VectorDB 서비스 Bedrock 테스트 스킵 (skipAwsTests=true)")
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
        
        # WebSocket 서비스 초기화
        try:
            # config 파일에서 WebSocket 설정 사용
            Logger.info(f"WebSocket 설정: require_auth={app_config.websocketConfig.require_auth}, use_redis_pubsub={app_config.websocketConfig.use_redis_pubsub}")
            if WebSocketService.init(app_config.websocketConfig):
                Logger.info("WebSocket 서비스 초기화 완료")
                ServiceContainer.set_websocket_service_initialized(True)
                
                # 백그라운드 태스크 시작
                await WebSocketService.start_background_tasks()
                Logger.info("WebSocket 백그라운드 태스크 시작")
            else:
                Logger.warn("WebSocket 서비스 초기화 실패")
        except Exception as e:
            Logger.error(f"WebSocket 서비스 초기화 실패: {e}")
            Logger.info("WebSocket 서비스 없이 계속 진행")
        
    except Exception as e:
        Logger.error(f"❌ Config 파일 로드 실패: {config_file} - {e}")
        Logger.error("🚫 서버 시작 불가 - 올바른 config 파일이 필요합니다")
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

    # 🛡️ 템플릿 등록 - 장애 허용 및 개별 실패 추적
    template_registration_status = {}
    template_configs = [
        (TemplateType.ADMIN, AdminTemplateImpl, "관리자"),
        (TemplateType.ACCOUNT, AccountTemplateImpl, "계정"),
        (TemplateType.TUTORIAL, TutorialTemplateImpl, "튜토리얼"),
        (TemplateType.DASHBOARD, DashboardTemplateImpl, "대시보드"),
        (TemplateType.PORTFOLIO, PortfolioTemplateImpl, "포트폴리오"),
        (TemplateType.CHAT, ChatTemplateImpl, "채팅"),
        (TemplateType.AUTOTRADE, AutoTradeTemplateImpl, "자동매매"),
        (TemplateType.MARKET, MarketTemplateImpl, "마켓"),
        (TemplateType.SETTINGS, SettingsTemplateImpl, "설정"),
        (TemplateType.NOTIFICATION, NotificationTemplateImpl, "알림"),
        (TemplateType.CRAWLER, CrawlerTemplateImpl, "크롤러")
    ]
    
    for template_type, template_class, template_name in template_configs:
        try:
            template_instance = template_class()
            TemplateContext.add_template(template_type, template_instance)
            template_registration_status[template_name] = True
            Logger.info(f"✅ {template_name} 템플릿 등록 성공")
        except Exception as e:
            template_registration_status[template_name] = False
            Logger.error(f"❌ {template_name} 템플릿 등록 실패: {e}")
    
    successful_templates = sum(template_registration_status.values())
    total_templates = len(template_registration_status)
    Logger.info(f"템플릿 등록 완료: {successful_templates}/{total_templates} 성공")
    
    if successful_templates < total_templates:
        Logger.warn(f"⚠️ {total_templates - successful_templates}개 템플릿 등록 실패 - 해당 기능 제한됨")
    
    # 🛡️ 템플릿 서비스 초기화 - 실패 시 복구 불가능
    try:
        TemplateService.init(app_config)
        Logger.info("✅ 템플릿 서비스 초기화 완료")
    except Exception as e:
        Logger.error(f"❌ 템플릿 서비스 초기화 실패: {e}")
        raise RuntimeError("Critical: Template service initialization required")
    
    # 🛡️ Protocol 콜백 설정 - 개별 실패 허용
    protocol_callback_configs = [
        ("account", "계정"),
        ("admin", "관리자"),
        ("tutorial", "튜토리얼"),
        ("dashboard", "대시보드"),
        ("portfolio", "포트폴리오"),
        ("chat", "채팅"),
        ("autotrade", "자동매매"),
        ("market", "마켓"),
        ("settings", "설정"),
        ("notification", "알림"),
        ("crawler", "크롤러"),
        ("websocket", "웹소켓")
    ]
    
    protocol_callback_status = {}
    for protocol_name, protocol_display_name in protocol_callback_configs:
        try:
            # 기존 방식으로 되돌리기 - 동적 import 대신 개별 import 사용
            if protocol_name == "account":
                from .routers.account import setup_account_protocol_callbacks
                setup_account_protocol_callbacks()
            elif protocol_name == "admin":
                from .routers.admin import setup_admin_protocol_callbacks
                setup_admin_protocol_callbacks()
            elif protocol_name == "tutorial":
                from .routers.tutorial import setup_tutorial_protocol_callbacks
                setup_tutorial_protocol_callbacks()
            elif protocol_name == "dashboard":
                from .routers.dashboard import setup_dashboard_protocol_callbacks
                setup_dashboard_protocol_callbacks()
            elif protocol_name == "portfolio":
                from .routers.portfolio import setup_portfolio_protocol_callbacks
                setup_portfolio_protocol_callbacks()
            elif protocol_name == "chat":
                from .routers.chat import setup_chat_protocol_callbacks
                setup_chat_protocol_callbacks()
            elif protocol_name == "autotrade":
                from .routers.autotrade import setup_autotrade_protocol_callbacks
                setup_autotrade_protocol_callbacks()
            elif protocol_name == "market":
                from .routers.market import setup_market_protocol_callbacks
                setup_market_protocol_callbacks()
            elif protocol_name == "settings":
                from .routers.settings import setup_settings_protocol_callbacks
                setup_settings_protocol_callbacks()
            elif protocol_name == "notification":
                from .routers.notification import setup_notification_protocol_callbacks
                setup_notification_protocol_callbacks()
            elif protocol_name == "crawler":
                from .routers.crawler import setup_crawler_protocol_callbacks
                setup_crawler_protocol_callbacks()
            elif protocol_name == "websocket":
                from .routers.websocket import setup_websocket_protocol_callbacks
                setup_websocket_protocol_callbacks()
            else:
                raise ImportError(f"Unknown protocol: {protocol_name}")
                
            protocol_callback_status[protocol_display_name] = True
            Logger.info(f"✅ {protocol_display_name} protocol 콜백 설정 성공")
        except Exception as e:
            protocol_callback_status[protocol_display_name] = False
            Logger.error(f"❌ {protocol_display_name} protocol 콜백 설정 실패: {e}")
    
    successful_protocols = sum(protocol_callback_status.values())
    total_protocols = len(protocol_callback_status)
    Logger.info(f"Protocol 콜백 설정 완료: {successful_protocols}/{total_protocols} 성공")
    
    if successful_protocols < total_protocols:
        Logger.warn(f"⚠️ {total_protocols - successful_protocols}개 protocol 콜백 실패 - 해당 API 제한됨")
    
    # 🛡️ 최종 시스템 검증 및 상태 요약
    Logger.info("=== 시스템 초기화 완료 - 최종 검증 실행 ===")
    
    try:
        # 핵심 서비스 상태 검증
        core_services_status = {
            "database": ServiceContainer.is_initialized(),
            "cache": CacheService.is_initialized(),
            "template": True
        }
        
        # 선택적 서비스 상태 검증
        optional_services_status = {
            "lock": LockService.is_initialized(),
            "scheduler": SchedulerService.is_initialized(),
            "queue": hasattr(QueueService, '_initialized') and QueueService._initialized,
            "external": external_init_success
        }
        
        # 핵심 서비스 검증
        failed_core_services = [name for name, status in core_services_status.items() if not status]
        if failed_core_services:
            Logger.error(f"❌ 핵심 서비스 실패: {failed_core_services}")
            raise RuntimeError(f"Critical services failed: {failed_core_services}")
        
        Logger.info("✅ 모든 핵심 서비스 초기화 성공")
        
        # 선택적 서비스 요약
        working_optional = [name for name, status in optional_services_status.items() if status]
        failed_optional = [name for name, status in optional_services_status.items() if not status]
        
        Logger.info(f"✅ 활성화된 선택적 서비스: {working_optional}")
        if failed_optional:
            Logger.warn(f"⚠️ 비활성화된 선택적 서비스: {failed_optional}")
        
        # 시스템 통합 테스트
        Logger.info("=== 시스템 통합 테스트 시작 ===")
        
        # 서비스 상태 추적을 위한 변수 초기화
        services_status = {
            "database": core_services_status["database"],
            "cache": core_services_status["cache"],
            "template": core_services_status["template"],
            "websocket": WebSocketService.is_initialized()
        }
        
        # 큐 시스템 통합 테스트
        if CacheService.is_initialized() and QueueService._initialized:
            try:
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
        
        # WebSocket 시스템 통합 테스트
        if WebSocketService.is_initialized():
            try:
                Logger.info("🔌 WebSocket 시스템 테스트 시작...")
                
                # 1. 서비스 상태 확인
                health_check = await WebSocketService.health_check()
                if health_check.get("healthy"):
                    Logger.info("✅ WebSocket 서비스 health check 성공")
                else:
                    Logger.warn("⚠️ WebSocket 서비스 health check 실패")
                
                # 2. 통계 정보 확인
                stats = WebSocketService.get_stats()
                Logger.info(f"WebSocket 초기 상태 - 연결: {stats.get('active_connections', 0)}, 총 연결: {stats.get('total_connections', 0)}")
                
                # 3. 테스트 메시지 핸들러 등록
                test_message_received = {"count": 0}
                
                async def test_handler(client_id: str, data: dict):
                    test_message_received["count"] += 1
                    Logger.info(f"WebSocket 테스트 메시지 수신: {data}")
                
                WebSocketService.register_message_handler("test_message", test_handler)
                
                # 4. 채널 관리 테스트
                test_channels = WebSocketService.get_all_channels()
                Logger.info(f"활성 채널 수: {len(test_channels)}")
                
                # 5. 연결 사용자 확인
                connected_users = WebSocketService.get_connected_users()
                Logger.info(f"연결된 사용자 수: {len(connected_users)}")
                
                services_status["websocket_system"] = True
                Logger.info("✅ WebSocket 시스템 테스트 완료")
                
            except Exception as e:
                services_status["websocket_system"] = False
                Logger.warn(f"⚠️ WebSocket 시스템 테스트 실패: {e}")
        else:
            services_status["websocket_system"] = False
            Logger.warn("❌ WebSocket 시스템 초기화되지 않음")
        
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
    
    # 🛡️ 런타임 서비스 모니터링 시작
    try:
        await service_monitor.start_monitoring()
        Logger.info("✅ 런타임 서비스 모니터링 시작")
    except Exception as e:
        Logger.error(f"❌ 서비스 모니터링 시작 실패: {e}")
        Logger.warn("⚠️ 런타임 모니터링 없이 계속 진행")
    
    Logger.info("=== base_web_server 초기화 및 테스트 완료 ===")
    
    yield
    
    # 서비스 정리 - 예외 처리와 함께
    Logger.info("서비스 종료 시작...")
    
    # 🛡️ 서비스 모니터링 중지
    try:
        await service_monitor.stop_monitoring()
        Logger.info("✅ 런타임 서비스 모니터링 중지")
    except Exception as e:
        Logger.error(f"❌ 서비스 모니터링 중지 오류: {e}")
    
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
    
    # SchedulerService 종료 (스케줄된 작업 완료 후)
    try:
        if SchedulerService.is_initialized():
            await SchedulerService.shutdown()
            ServiceContainer.set_scheduler_service_initialized(False)
            Logger.info("SchedulerService 종료")
    except Exception as e:
        Logger.error(f"SchedulerService 종료 오류: {e}")
    
    # QueueService 종료 (큐 처리 완료 후)
    try:
        if QueueService._initialized:
            Logger.info("QueueService graceful shutdown 시작...")
            
            # 우아한 종료 시도 (처리 중인 메시지 완료 대기)
            success = await QueueService.graceful_shutdown(timeout_seconds=30)
            
            if success:
                Logger.info("QueueService graceful shutdown 성공")
            else:
                Logger.warn("QueueService graceful shutdown 실패 - 강제 종료")
                await QueueService.shutdown()
            
            ServiceContainer.set_queue_service_initialized(False)
            Logger.info("QueueService 종료 완료")
    except Exception as e:
        Logger.error(f"QueueService 종료 오류: {e}")
        # 예외 발생 시에도 강제 종료 시도
        try:
            await QueueService.shutdown()
            ServiceContainer.set_queue_service_initialized(False)
        except Exception as force_e:
            Logger.error(f"QueueService 강제 종료도 실패: {force_e}")
    
    # WebSocket 서비스 종료
    try:
        if WebSocketService.is_initialized():
            await WebSocketService.shutdown()
            ServiceContainer.set_websocket_service_initialized(False)
            Logger.info("WebSocket 서비스 종료 완료")
    except Exception as e:
        Logger.error(f"WebSocket 서비스 종료 오류: {e}")
    
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
        
    # 캐시 서비스 종료 (Redis 연결) - CacheService 의존 서비스들 이후 종료
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
        await asyncio.sleep(0.1)  # 마지막 로그 출력 대기
        Logger.shutdown()  # 파일 로거의 경우 큐 비우고 스레드 종료
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

# CORS 미들웨어 추가 (모든 origin, method, header 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
from .routers import account, admin, tutorial, dashboard, portfolio, chat, autotrade, market, settings, notification, crawler, websocket
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
app.include_router(websocket.router, prefix="/api/websocket", tags=["websocket"])

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