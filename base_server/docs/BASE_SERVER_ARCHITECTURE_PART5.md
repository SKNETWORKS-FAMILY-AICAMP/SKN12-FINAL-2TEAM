# Base Server Architecture Documentation - Part 5: 서비스 컨테이너 & 의존성 관리

## 목차
1. [서비스 컨테이너 개요](#서비스-컨테이너-개요)
2. [ServiceContainer 구현](#servicecontainer-구현)
3. [서비스 라이프사이클 관리](#서비스-라이프사이클-관리)
4. [핵심 서비스 분석](#핵심-서비스-분석)
5. [AWS 연동 서비스](#aws-연동-서비스)
6. [모니터링 및 헬스체크](#모니터링-및-헬스체크)
7. [서비스 설정 관리](#서비스-설정-관리)

---

## 서비스 컨테이너 개요

### 아키텍처 패턴

Base Server는 **서비스 컨테이너 패턴**을 채택하여 모든 서비스 인스턴스를 중앙에서 관리합니다.

```
┌─────────────────────────────────────────────────────────────┐
│                   ServiceContainer                          │
│                    (Singleton)                              │
├─────────────────────────────────────────────────────────────┤
│  Core Services           │  AWS Services                    │
│  ┌─────────────────┐    │  ┌──────────────────────────────┐ │
│  │ DatabaseService │    │  │ StorageService (S3)          │ │
│  │ CacheService    │    │  │ VectorDbService (Bedrock)   │ │
│  │ QueueService    │    │  │ SearchService (OpenSearch)   │ │
│  │ LockService     │    │  │ ExternalService (HTTP APIs) │ │
│  │ SchedulerService│    │  └──────────────────────────────┘ │
│  └─────────────────┘    │                                  │
├─────────────────────────────────────────────────────────────┤
│                 Service Lifecycle                           │
│  init() → start() → running → shutdown() → closed           │
└─────────────────────────────────────────────────────────────┘
```

### 설계 원칙

1. **단일 책임**: 각 서비스는 명확한 역할과 책임을 가짐
2. **느슨한 결합**: 서비스 간 인터페이스를 통한 느슨한 결합
3. **생명주기 관리**: 통일된 초기화, 실행, 종료 프로세스
4. **상태 추적**: 각 서비스의 초기화 상태를 중앙에서 관리
5. **오류 격리**: 특정 서비스 오류가 전체 시스템에 영향을 주지 않도록 격리

---

## ServiceContainer 구현

### 싱글톤 패턴 구현

```python
class ServiceContainer:
    """전역 서비스 인스턴스를 관리하는 컨테이너"""
    
    _instance: Optional['ServiceContainer'] = None
    _database_service: Optional[DatabaseService] = None
    _cache_service: Optional[CacheService] = None
    _lock_service_initialized: bool = False
    _scheduler_service_initialized: bool = False
    _queue_service_initialized: bool = False
    
    def __new__(cls):
        """싱글톤 패턴으로 인스턴스 생성"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

**싱글톤 구현 특징:**
- 애플리케이션 전체에서 단일 인스턴스 보장
- 클래스 변수로 서비스 인스턴스 저장
- 초기화 상태를 boolean 플래그로 관리

### 서비스 등록 및 조회

#### 서비스 초기화
```python
@classmethod
def init(cls, database_service: DatabaseService):
    """서비스 컨테이너 초기화"""
    container = cls()
    container._database_service = database_service
```

#### 서비스 조회 메서드
```python
@classmethod
def get_database_service(cls) -> DatabaseService:
    """DatabaseService 인스턴스 반환"""
    container = cls()
    if container._database_service is None:
        raise RuntimeError("DatabaseService not initialized in ServiceContainer")
    return container._database_service

@classmethod
def get_cache_service(cls) -> CacheService:
    """CacheService 인스턴스 반환"""
    # CacheService는 이미 싱글톤으로 구현되어 있음
    return CacheService
```

#### 상태 관리 메서드
```python
@classmethod
def set_lock_service_initialized(cls, initialized: bool):
    """LockService 초기화 상태 설정"""
    container = cls()
    container._lock_service_initialized = initialized

@classmethod
def get_service_status(cls) -> dict:
    """모든 서비스 상태 반환"""
    container = cls()
    return {
        "database": container._database_service is not None,
        "cache": container._cache_service is not None,
        "lock": container._lock_service_initialized,
        "scheduler": container._scheduler_service_initialized,
        "queue": container._queue_service_initialized
    }

@classmethod
def is_initialized(cls) -> bool:
    """서비스 컨테이너가 초기화되었는지 확인"""
    container = cls()
    return container._database_service is not None
```

### 사용 패턴

#### 템플릿에서 서비스 사용
```python
# AccountTemplateImpl.py에서 사용 예시
async def on_account_login_req(self, client_session, request: AccountLoginRequest):
    """로그인 요청 처리"""
    # ServiceContainer를 통해 데이터베이스 서비스 획득
    db_service = ServiceContainer.get_database_service()
    
    # 글로벌 DB에서 계정 인증
    result = await db_service.call_global_procedure(
        "fp_user_login",
        (request.platform_type, request.account_id, hashed_password)
    )
```

---

## 서비스 라이프사이클 관리

### 111 패턴 (One-One-One)

Base Server의 모든 AWS 연동 서비스는 **111 패턴**을 따릅니다:
- **1개의 설정 클래스** (Config)
- **1개의 클라이언트 풀** (ClientPool)  
- **1개의 서비스 클래스** (Service)

### 표준 라이프사이클

#### 1. 초기화 (init)
```python
@classmethod
def init(cls, config: ServiceConfig) -> bool:
    """서비스 초기화"""
    try:
        cls._config = config
        cls._client_pool = ServiceClientPool(config)
        cls._initialized = True
        Logger.info("Service initialized")
        return True
    except Exception as e:
        Logger.error(f"Service init failed: {e}")
        return False
```

#### 2. 종료 (shutdown)
```python
@classmethod
async def shutdown(cls):
    """서비스 종료"""
    if cls._initialized and cls._client_pool:
        await cls._client_pool.close_all()
        cls._client_pool = None
        cls._initialized = False
        Logger.info("Service shutdown")
```

#### 3. 상태 확인
```python
@classmethod
def is_initialized(cls) -> bool:
    """초기화 여부 확인"""
    return cls._initialized

@classmethod
def get_client(cls):
    """클라이언트 가져오기"""
    if not cls._initialized:
        raise RuntimeError("Service not initialized")
    if not cls._client_pool:
        raise RuntimeError("Service client pool not available")
    return cls._client_pool.new()
```

---

## 핵심 서비스 분석

### DatabaseService

**역할**: MySQL 데이터베이스 연결 및 샤딩 관리

```python
class DatabaseService:
    """데이터베이스 서비스 - 글로벌 DB와 샤드 DB 관리"""
    
    def __init__(self, global_config: DatabaseConfig):
        self.global_config = global_config
        self.global_client: Optional[MySQLClient] = None
        self.shard_clients: Dict[int, MySQLClient] = {}
        self.shard_configs: Dict[int, DatabaseConfig] = {}
```

**주요 기능:**
- 글로벌 DB 연결 관리
- 샤드 DB 동적 설정 로드 및 연결
- 세션 기반 자동 라우팅
- 트랜잭션 컨텍스트 제공

**사용 예시:**
```python
# 글로벌 DB 사용
result = await db_service.call_global_procedure("fp_user_login", params)

# 세션 기반 자동 라우팅 (샤드 ID에 따라 자동 선택)
account_info = await db_service.call_procedure_by_session(
    client_session, "fp_get_account_info", (account_db_key,)
)

# 명시적 샤드 호출
result = await db_service.call_shard_procedure(
    shard_id=1, procedure_name="fp_create_account", params=(account_db_key, "checking")
)
```

### CacheService (Redis)

**역할**: Redis 기반 캐싱 및 세션 관리

```python
class CacheService:
    """캐시 서비스 - Redis 연결 및 캐시 관리"""
    
    @classmethod
    async def get_client(cls):
        """비동기 컨텍스트 매니저로 Redis 클라이언트 제공"""
        if cls._instance is None:
            await cls._ensure_instance()
        
        async with cls._instance.client_pool.acquire() as client:
            yield client
```

**주요 기능:**
- Redis 연결 풀 관리
- 세션 정보 저장/조회
- 캐시 작업 (String, Hash, Set, Sorted Set)
- 자동 재연결 및 메트릭 수집

**사용 예시:**
```python
# 세션 정보 저장
async with CacheService.get_client() as client:
    await client.set_string(f"accessToken:{access_token}", access_token, expire=3600)
    await client.set_hash_all(f"sessionInfo:{access_token}", session_dict)

# 캐시 데이터 조회
async with CacheService.get_client() as client:
    user_profile = await client.get_string(f"user:profile:{user_id}")
```

---

## AWS 연동 서비스

### StorageService (S3)

**역할**: AWS S3 기반 파일 스토리지 관리

```python
class StorageService:
    """Storage 서비스 (정적 클래스) - 111 패턴"""
    
    _config: Optional[StorageConfig] = None
    _client_pool: Optional[IStorageClientPool] = None
    _initialized: bool = False
```

**주요 API:**
```python
# 파일 업로드
await StorageService.upload_file(bucket="user-files", key="profile/123.jpg", file_path="/tmp/image.jpg")

# 파일 다운로드
await StorageService.download_file(bucket="user-files", key="profile/123.jpg", file_path="/tmp/download.jpg")

# 사전 서명된 URL 생성 (직접 업로드용)
presigned_url = await StorageService.generate_presigned_url(
    bucket="user-files", key="upload/456.pdf", expiration=3600
)
```

### VectorDbService (AWS Bedrock)

**역할**: AWS Bedrock 기반 AI/LLM 서비스

```python
class VectorDbService:
    """VectorDB 서비스 (정적 클래스) - 111 패턴"""
    
    _config: Optional[VectorDbConfig] = None
    _client_pool: Optional[IVectorDbClientPool] = None
    _initialized: bool = False
```

**주요 API:**
```python
# 텍스트 임베딩
embedding_result = await VectorDbService.embed_text("투자 포트폴리오 분석")

# 유사도 검색
search_results = await VectorDbService.similarity_search(
    query="포트폴리오 최적화 방법", top_k=10
)

# AI 텍스트 생성
response = await VectorDbService.generate_text(
    prompt="주식 투자의 기본 원칙을 설명해주세요"
)

# 채팅 완성
chat_response = await VectorDbService.chat_completion(
    messages=[
        {"role": "user", "content": "오늘 시장 상황을 분석해주세요"}
    ]
)
```

### SearchService (OpenSearch)

**역할**: AWS OpenSearch 기반 검색 엔진

```python
class SearchService:
    """Search 서비스 (정적 클래스) - 111 패턴"""
    
    _config: Optional[SearchConfig] = None
    _client_pool: Optional[ISearchClientPool] = None
    _initialized: bool = False
```

**주요 API:**
```python
# 인덱스 생성
await SearchService.create_index(
    index="financial_documents",
    mappings={"properties": {"title": {"type": "text"}, "content": {"type": "text"}}}
)

# 문서 인덱싱
await SearchService.index_document(
    index="financial_documents",
    document={"title": "투자 가이드", "content": "주식 투자의 기본..."},
    doc_id="guide_001"
)

# 검색 실행
search_results = await SearchService.search(
    index="financial_documents",
    query={
        "match": {"content": "포트폴리오"}
    }
)
```

### ExternalService (HTTP APIs)

**역할**: 외부 API 통합 관리

```python
class ExternalService:
    """External API 서비스 (정적 클래스) - 순수 라이브러리"""
    
    _config: Optional[ExternalConfig] = None
    _client_pool: Optional[IExternalClientPool] = None
    _initialized: bool = False
```

**주요 API:**
```python
# 금융 데이터 API 호출
market_data = await ExternalService.get(
    api_name="yahoo_finance",
    url="/v1/quote",
    params={"symbol": "AAPL"}
)

# 뉴스 API 호출
news_data = await ExternalService.post(
    api_name="news_api",
    url="/v2/everything",
    json={"q": "stock market", "language": "en"}
)

# 환율 API 호출
exchange_rate = await ExternalService.get(
    api_name="currency_api",
    url="/latest",
    params={"base": "USD", "symbols": "KRW,EUR,JPY"}
)
```

---

## 모니터링 및 헬스체크

### 통합 헬스체크 시스템

모든 서비스는 표준 헬스체크 인터페이스를 제공합니다.

#### 개별 서비스 헬스체크
```python
# DatabaseService 헬스체크
db_health = await database_service.health_check()
# {
#   "healthy": True,
#   "global_db": {"connected": True, "latency_ms": 5},
#   "shard_dbs": {
#     "shard_1": {"connected": True, "latency_ms": 3},
#     "shard_2": {"connected": True, "latency_ms": 4}
#   }
# }

# CacheService 헬스체크
cache_health = await CacheService.health_check()
# {
#   "healthy": True,
#   "redis_version": "6.2.7",
#   "connected_clients": 12,
#   "used_memory_human": "2.5M",
#   "metrics": {...}
# }

# StorageService 헬스체크
storage_health = await StorageService.health_check()
# {
#   "healthy": True,
#   "aws_region": "us-east-1",
#   "bucket_accessible": True,
#   "test_operation_success": True
# }
```

#### 전체 시스템 헬스체크
```python
async def system_health_check():
    """전체 시스템 헬스체크"""
    health_status = {
        "timestamp": datetime.now().isoformat(),
        "overall_healthy": True,
        "services": {}
    }
    
    # ServiceContainer 상태
    service_status = ServiceContainer.get_service_status()
    health_status["services"]["container"] = service_status
    
    # 각 서비스 헬스체크
    services_to_check = [
        ("database", DatabaseService),
        ("cache", CacheService),
        ("storage", StorageService),
        ("vectordb", VectorDbService),
        ("search", SearchService),
        ("external", ExternalService)
    ]
    
    for service_name, service_class in services_to_check:
        try:
            if hasattr(service_class, 'health_check'):
                service_health = await service_class.health_check()
                health_status["services"][service_name] = service_health
                
                if not service_health.get("healthy", False):
                    health_status["overall_healthy"] = False
        except Exception as e:
            health_status["services"][service_name] = {
                "healthy": False,
                "error": str(e)
            }
            health_status["overall_healthy"] = False
    
    return health_status
```

### 메트릭 수집

#### 서비스별 메트릭
```python
# ExternalService 메트릭 예시
external_metrics = ExternalService.get_metrics()
# {
#   "overall_metrics": {
#     "total_requests": 1250,
#     "successful_requests": 1180,
#     "failed_requests": 70,
#     "success_rate": 0.944
#   },
#   "api_metrics": {
#     "yahoo_finance": {
#       "total_requests": 450,
#       "successful_requests": 440,
#       "failed_requests": 10,
#       "average_response_time": 0.25
#     },
#     "news_api": {
#       "total_requests": 800,
#       "successful_requests": 740,
#       "failed_requests": 60,
#       "average_response_time": 0.35
#     }
#   },
#   "total_apis": 2
# }

# VectorDbService 메트릭 예시
vectordb_metrics = VectorDbService.get_metrics()
# {
#   "service_initialized": True,
#   "config": {
#     "aws_region": "us-east-1",
#     "embedding_model": "amazon.titan-embed-text-v1",
#     "text_model": "anthropic.claude-v2",
#     "knowledge_base_id": "KB123456"
#   },
#   "client_metrics": {
#     "total_embeddings": 523,
#     "total_text_generations": 89,
#     "average_embedding_time": 0.15,
#     "average_generation_time": 2.3
#   }
# }
```

#### 메트릭 리셋
```python
# 개별 서비스 메트릭 리셋
ExternalService.reset_metrics(api_name="yahoo_finance")  # 특정 API만
ExternalService.reset_metrics()  # 전체 API

# 전체 시스템 메트릭 리셋
def reset_all_service_metrics():
    """모든 서비스 메트릭 리셋"""
    services_with_metrics = [
        CacheService,
        StorageService, 
        VectorDbService,
        SearchService,
        ExternalService
    ]
    
    for service in services_with_metrics:
        try:
            if hasattr(service, 'reset_metrics'):
                service.reset_metrics()
        except Exception as e:
            Logger.error(f"Failed to reset metrics for {service.__name__}: {e}")
```

---

## 서비스 설정 관리

### 설정 클래스 구조

#### DatabaseConfig
```python
@dataclass
class DatabaseConfig:
    """데이터베이스 설정"""
    type: str = "mysql"
    host: str = "localhost"
    port: int = 3306
    database: str = ""
    user: str = ""
    password: str = ""
    charset: str = "utf8mb4"
    pool_size: int = 10
    connect_timeout: int = 30
    read_timeout: int = 30
    write_timeout: int = 30
```

#### CacheConfig  
```python
@dataclass
class CacheConfig:
    """Redis 캐시 설정"""
    host: str = "localhost"
    port: int = 6379
    password: str = ""
    db_number: int = 0
    max_connections: int = 20
    connection_timeout: int = 30
    socket_keepalive: bool = True
    session_expire_time: int = 3600  # 1시간
    app_id: str = "finance_app"
    env: str = "dev"
```

#### StorageConfig
```python
@dataclass
class StorageConfig:
    """S3 스토리지 설정"""
    type: str = "s3"
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    default_bucket: str = ""
    endpoint_url: Optional[str] = None  # LocalStack 등 로컬 테스트용
    max_pool_connections: int = 50
    retry_config: Dict[str, Any] = None
```

#### VectorDbConfig
```python
@dataclass
class VectorDbConfig:
    """AWS Bedrock 설정"""
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    embedding_model: str = "amazon.titan-embed-text-v1"
    text_model: str = "anthropic.claude-v2"
    knowledge_base_id: Optional[str] = None
    max_pool_connections: int = 10
    timeout: int = 30
```

### 환경별 설정 관리

#### 설정 로더
```python
class ConfigLoader:
    """환경별 설정 로더"""
    
    @staticmethod
    def load_database_config(env: str = "dev") -> DatabaseConfig:
        """데이터베이스 설정 로드"""
        if env == "prod":
            return DatabaseConfig(
                host="prod-db.finance.com",
                database="finance_global",
                user="finance_user",
                password=os.getenv("DB_PASSWORD"),
                pool_size=20,
                connect_timeout=10
            )
        elif env == "dev":
            return DatabaseConfig(
                host="localhost",
                database="finance_global", 
                user="root",
                password="Wkdwkrdhkd91!",
                pool_size=5
            )
    
    @staticmethod
    def load_cache_config(env: str = "dev") -> CacheConfig:
        """캐시 설정 로드"""
        return CacheConfig(
            host="localhost" if env == "dev" else "prod-redis.finance.com",
            password=os.getenv("REDIS_PASSWORD", ""),
            app_id="finance_app",
            env=env,
            session_expire_time=3600 if env == "dev" else 1800
        )
```

### 설정 검증

#### 설정 유효성 검사
```python
class ConfigValidator:
    """설정 유효성 검사"""
    
    @staticmethod
    def validate_database_config(config: DatabaseConfig) -> List[str]:
        """데이터베이스 설정 검증"""
        errors = []
        
        if not config.host:
            errors.append("Database host is required")
        if not config.database:
            errors.append("Database name is required")
        if not config.user:
            errors.append("Database user is required")
        if config.pool_size <= 0:
            errors.append("Pool size must be positive")
        if config.port <= 0 or config.port > 65535:
            errors.append("Port must be between 1 and 65535")
            
        return errors
    
    @staticmethod
    def validate_all_configs(**configs) -> Dict[str, List[str]]:
        """모든 설정 검증"""
        validation_results = {}
        
        if "database" in configs:
            validation_results["database"] = ConfigValidator.validate_database_config(configs["database"])
        
        # 다른 설정들도 검증...
        
        return validation_results
```

---

## 서비스 초기화 시퀀스

### 애플리케이션 시작 시퀀스

```python
async def initialize_services(env: str = "dev"):
    """서비스 초기화 시퀀스"""
    
    try:
        # 1. 설정 로드 및 검증
        Logger.info("Loading configurations...")
        db_config = ConfigLoader.load_database_config(env)
        cache_config = ConfigLoader.load_cache_config(env)
        
        validation_errors = ConfigValidator.validate_all_configs(
            database=db_config,
            cache=cache_config
        )
        
        if any(validation_errors.values()):
            raise RuntimeError(f"Configuration validation failed: {validation_errors}")
        
        # 2. 핵심 서비스 초기화 (순서 중요)
        Logger.info("Initializing core services...")
        
        # 2.1 데이터베이스 서비스 (최우선)
        database_service = DatabaseService(db_config)
        await database_service.init_service()
        ServiceContainer.init(database_service)
        
        # 2.2 캐시 서비스 (세션 관리용)
        await CacheService.init(cache_config)
        
        # 2.3 큐 서비스 (데이터베이스 의존)
        if hasattr(queue_service, 'init'):
            await queue_service.init(database_service)
            ServiceContainer.set_queue_service_initialized(True)
        
        # 2.4 분산락 서비스
        if hasattr(lock_service, 'init'):
            await lock_service.init()
            ServiceContainer.set_lock_service_initialized(True)
        
        # 3. AWS 서비스 초기화 (병렬 가능)
        Logger.info("Initializing AWS services...")
        
        aws_services = []
        
        # 3.1 스토리지 서비스
        storage_config = ConfigLoader.load_storage_config(env)
        if StorageService.init(storage_config):
            aws_services.append("StorageService")
        
        # 3.2 벡터DB 서비스
        vectordb_config = ConfigLoader.load_vectordb_config(env)
        if VectorDbService.init(vectordb_config):
            aws_services.append("VectorDbService")
        
        # 3.3 검색 서비스
        search_config = ConfigLoader.load_search_config(env)
        if SearchService.init(search_config):
            aws_services.append("SearchService")
        
        # 3.4 외부 API 서비스
        external_config = ConfigLoader.load_external_config(env)
        await ExternalService.init(external_config)
        aws_services.append("ExternalService")
        
        Logger.info(f"Initialized AWS services: {aws_services}")
        
        # 4. 스케줄러 서비스 (마지막)
        if hasattr(scheduler_service, 'init'):
            await scheduler_service.init()
            ServiceContainer.set_scheduler_service_initialized(True)
        
        # 5. 초기화 완료 확인
        service_status = ServiceContainer.get_service_status()
        Logger.info(f"Service initialization completed: {service_status}")
        
        # 6. 헬스체크 수행
        health_status = await system_health_check()
        if not health_status["overall_healthy"]:
            Logger.warn(f"Some services are unhealthy: {health_status}")
        else:
            Logger.info("All services are healthy")
        
        return True
        
    except Exception as e:
        Logger.error(f"Service initialization failed: {e}")
        # 실패 시 정리
        await shutdown_services()
        raise

async def shutdown_services():
    """서비스 종료 시퀀스"""
    
    Logger.info("Shutting down services...")
    
    try:
        # 역순으로 종료
        services_to_shutdown = [
            ("SchedulerService", getattr(scheduler_service, 'shutdown', None)),
            ("ExternalService", ExternalService.shutdown),
            ("SearchService", SearchService.shutdown),
            ("VectorDbService", VectorDbService.shutdown),
            ("StorageService", StorageService.shutdown),
            ("QueueService", getattr(queue_service, 'shutdown', None)),
            ("CacheService", CacheService.shutdown),
            ("DatabaseService", lambda: ServiceContainer.get_database_service().close_service())
        ]
        
        for service_name, shutdown_func in services_to_shutdown:
            if shutdown_func:
                try:
                    if asyncio.iscoroutinefunction(shutdown_func):
                        await shutdown_func()
                    else:
                        shutdown_func()
                    Logger.info(f"{service_name} shutdown completed")
                except Exception as e:
                    Logger.error(f"{service_name} shutdown failed: {e}")
        
        Logger.info("All services shutdown completed")
        
    except Exception as e:
        Logger.error(f"Service shutdown failed: {e}")
```

---

## 의존성 주입 패턴

### 명시적 의존성 주입

```python
class ServiceDependencies:
    """서비스 의존성 정의"""
    
    def __init__(self):
        self.database_service = None
        self.cache_service = None
        self.queue_service = None
    
    async def inject_dependencies(self):
        """의존성 주입"""
        self.database_service = ServiceContainer.get_database_service()
        self.cache_service = ServiceContainer.get_cache_service()
        
        # 큐 서비스는 데이터베이스에 의존
        if ServiceContainer.get_service_status()["queue"]:
            self.queue_service = queue_service

class BusinessLogicService:
    """비즈니스 로직 서비스 - 의존성 주입 예시"""
    
    def __init__(self, dependencies: ServiceDependencies):
        self.db = dependencies.database_service
        self.cache = dependencies.cache_service
        self.queue = dependencies.queue_service
    
    async def process_user_action(self, user_id: str, action_data: dict):
        """사용자 액션 처리 - 여러 서비스 연동"""
        
        # 1. 캐시에서 사용자 정보 확인
        async with self.cache.get_client() as cache_client:
            user_cache = await cache_client.get_string(f"user:{user_id}")
        
        # 2. 데이터베이스에서 처리
        if user_cache:
            result = await self.db.execute_query(
                "UPDATE user_actions SET last_action = %s WHERE user_id = %s",
                (action_data, user_id)
            )
        
        # 3. 이벤트 큐에 알림 발행
        if self.queue:
            await self.queue.publish_event(
                event_type="user.action.completed",
                data={"user_id": user_id, "action": action_data}
            )
```

---

이것으로 Part 5가 완료되었습니다. Part 6에서는 외부 서비스와 검색 시스템에 대해 상세히 다루겠습니다.

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "Part 3: \ub370\uc774\ud130\ubca0\uc774\uc2a4 \uc2dc\uc2a4\ud15c & \uc0e4\ub529 - \ud604\uc7ac \uad6c\ud604 \ubd84\uc11d", "status": "completed", "priority": "high", "id": "3"}, {"content": "Part 4: \ud15c\ud50c\ub9bf \uc2dc\uc2a4\ud15c & \ub77c\uc6b0\ud305 - \ucf54\ub4dc \ubd84\uc11d", "status": "completed", "priority": "high", "id": "4"}, {"content": "Part 5: \uc11c\ube44\uc2a4 \ucee8\ud14c\uc774\ub108 & \uc758\uc874\uc131 \uad00\ub9ac", "status": "completed", "priority": "high", "id": "5"}, {"content": "Part 6: \uc678\ubd80 \uc11c\ube44\uc2a4 & \uac80\uc0c9 \uc2dc\uc2a4\ud15c", "status": "in_progress", "priority": "high", "id": "6"}, {"content": "Part 7: \uc2a4\ucf00\uc904\ub7ec & \ubc31\uadf8\ub77c\uc6b4\ub4dc \uc791\uc5c5", "status": "pending", "priority": "high", "id": "7"}, {"content": "Part 8: \ubcf4\uc548 & \uc778\uc99d \uc2dc\uc2a4\ud15c", "status": "pending", "priority": "high", "id": "8"}, {"content": "Part 9: \ubaa8\ub2c8\ud130\ub9c1 & \ub85c\uae45", "status": "pending", "priority": "high", "id": "9"}, {"content": "Part 10: \ubc30\ud3ec & \uc6b4\uc601 \uac00\uc774\ub4dc", "status": "pending", "priority": "high", "id": "10"}]