"""
서비스 컨테이너 - 전역 서비스 인스턴스 관리
AIChatService 인스턴스 등록/조회, 서비스 초기화 상태 플래그 추가
순환 참조 방지를 위해 모듈 내부 임포트 사용
"""
from typing import Optional
from service.db.database_service import DatabaseService
from service.cache.cache_service import CacheService
from service.external.external_service import ExternalService
from service.storage.storage_service import StorageService
from service.search.search_service import SearchService
from service.vectordb.vectordb_service import VectorDbService

class ServiceContainer:
    """전역 서비스 인스턴스를 관리하는 컨테이너"""
    _instance: Optional['ServiceContainer'] = None
    _database_service: Optional[DatabaseService] = None
    _cache_service: Optional[CacheService] = None
    _external_service: Optional[ExternalService] = None
    _storage_service: Optional[StorageService] = None
    _search_service: Optional[SearchService] = None
    _vectordb_service: Optional[VectorDbService] = None

    # AIChatService 인스턴스 (forward reference)
    _ai_chat_service = None  # type: ignore
    
    # Korea Investment 서비스 인스턴스들
    _korea_investment_service = None  # type: ignore
    _korea_investment_websocket = None  # type: ignore

    # 초기화 상태 플래그
    _cache_service_initialized: bool = False
    _lock_service_initialized: bool = False
    _scheduler_service_initialized: bool = False
    _queue_service_initialized: bool = False
    _websocket_service_initialized: bool = False
    _notification_service_initialized: bool = False
    _korea_investment_service_initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def init(cls, database_service: DatabaseService, ai_chat_service) -> None:
        """서비스 컨테이너 초기화: DB와 AIChatService 등록"""
        container = cls()
        container._database_service = database_service
        # AIChatService 내부 임포트로 순환 참조 방지
        from service.llm.AIChat_service import AIChatService
        if not isinstance(ai_chat_service, AIChatService):
            raise TypeError("Expected AIChatService instance")
        container._ai_chat_service = ai_chat_service

    @classmethod
    def get_database_service(cls) -> DatabaseService:
        container = cls()
        if container._database_service is None:
            raise RuntimeError("DatabaseService not initialized in ServiceContainer")
        return container._database_service

    @classmethod
    def get_cache_service(cls) -> CacheService:
        return CacheService

    @classmethod
    def set_ai_chat_service(cls, service) -> None:
        """AIChatService 인스턴스 설정"""
        from service.llm.AIChat_service import AIChatService
        if not isinstance(service, AIChatService):
            raise TypeError("Expected AIChatService instance")
        cls()._ai_chat_service = service

    @classmethod
    def get_ai_chat_service(cls):
        """AIChatService 인스턴스 반환"""
        container = cls()
        if container._ai_chat_service is None:
            raise RuntimeError("AIChatService not initialized in ServiceContainer")
        return container._ai_chat_service

    @classmethod
    def get_lock_service(cls):
        from service.lock.lock_service import LockService
        return LockService

    # 서비스 초기화 플래그 설정/확인 메서드
    @classmethod
    def set_queue_service_initialized(cls, initialized: bool):
        """QueueService 초기화 상태 설정"""
        container = cls()
        container._queue_service_initialized = initialized
    
    @classmethod
    def set_websocket_service_initialized(cls, initialized: bool):
        """WebSocketService 초기화 상태 설정"""
        container = cls()
        container._websocket_service_initialized = initialized
    
    @classmethod
    def set_cache_service_initialized(cls, initialized: bool):
        """CacheService 초기화 상태 설정"""
        cls()._cache_service_initialized = initialized

    @classmethod
    def is_cache_service_initialized(cls) -> bool:
        return getattr(cls(), "_cache_service_initialized", False)

    @classmethod
    def set_lock_service_initialized(cls, initialized: bool) -> None:
        """LockService 초기화 상태 설정"""
        cls()._lock_service_initialized = initialized

    @classmethod
    def is_lock_service_initialized(cls) -> bool:
        return getattr(cls(), "_lock_service_initialized", False)

    @classmethod
    def set_scheduler_service_initialized(cls, initialized: bool) -> None:
        """SchedulerService 초기화 상태 설정"""
        cls()._scheduler_service_initialized = initialized

    @classmethod
    def is_scheduler_service_initialized(cls) -> bool:
        return getattr(cls(), "_scheduler_service_initialized", False)

    @classmethod
    def set_queue_service_initialized(cls, initialized: bool) -> None:
        """QueueService 초기화 상태 설정"""
        cls()._queue_service_initialized = initialized

    @classmethod
    def is_queue_service_initialized(cls) -> bool:
        return getattr(cls(), "_queue_service_initialized", False)

    @classmethod
    def set_notification_service_initialized(cls, initialized: bool) -> None:
        """NotificationService 초기화 상태 설정"""
        cls()._notification_service_initialized = initialized

    @classmethod
    def is_notification_service_initialized(cls) -> bool:
        return getattr(cls(), "_notification_service_initialized", False)

    @classmethod
    def set_korea_investment_service(cls, service, websocket_service) -> None:
        """Korea Investment 서비스 인스턴스 설정"""
        container = cls()
        container._korea_investment_service = service
        container._korea_investment_websocket = websocket_service
        container._korea_investment_service_initialized = True

    @classmethod
    def get_korea_investment_service(cls):
        """Korea Investment 서비스 인스턴스 반환"""
        container = cls()
        if container._korea_investment_service is None:
            raise RuntimeError("Korea Investment Service not initialized in ServiceContainer")
        return container._korea_investment_service

    @classmethod
    def get_korea_investment_websocket(cls):
        """Korea Investment WebSocket 서비스 인스턴스 반환"""
        container = cls()
        if container._korea_investment_websocket is None:
            raise RuntimeError("Korea Investment WebSocket Service not initialized in ServiceContainer")
        return container._korea_investment_websocket

    @classmethod
    def is_korea_investment_service_initialized(cls) -> bool:
        return getattr(cls(), "_korea_investment_service_initialized", False)

    @classmethod
    def get_service_status(cls) -> dict:
        container = cls()
        return {
            "database": container._database_service is not None,
            "cache": container._cache_service_initialized,
            "lock": container._lock_service_initialized,
            "scheduler": container._scheduler_service_initialized,
            "queue": container._queue_service_initialized,
            "external": container._external_service is not None,
            "storage": container._storage_service is not None,
            "search": container._search_service is not None,
            "vectordb": container._vectordb_service is not None,
            "ai_chat": container._ai_chat_service is not None,
            "websocket": container._websocket_service_initialized,
            "notification": container._notification_service_initialized,
            "korea_investment": container._korea_investment_service_initialized
        }

    @classmethod
    def is_initialized(cls) -> bool:
        container = cls()
        return (container._database_service is not None and
                container._ai_chat_service is not None)
