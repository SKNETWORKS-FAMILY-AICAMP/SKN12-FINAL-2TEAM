"""
서비스 컨테이너 - 전역 서비스 인스턴스 관리
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
    _lock_service_initialized: bool = False
    _scheduler_service_initialized: bool = False
    _queue_service_initialized: bool = False
    _websocket_service_initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def init(cls, database_service: DatabaseService):
        """서비스 컨테이너 초기화"""
        container = cls()
        container._database_service = database_service
        
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
    
    @classmethod
    def set_lock_service_initialized(cls, initialized: bool):
        """LockService 초기화 상태 설정"""
        container = cls()
        container._lock_service_initialized = initialized
    
    @classmethod
    def set_scheduler_service_initialized(cls, initialized: bool):
        """SchedulerService 초기화 상태 설정"""
        container = cls()
        container._scheduler_service_initialized = initialized
    
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
        container = cls()
        container._cache_service = CacheService if initialized else None
    
    @classmethod
    def set_external_service(cls, service: Optional[ExternalService]):
        """ExternalService 설정"""
        container = cls()
        container._external_service = service
    
    @classmethod
    def get_external_service(cls) -> Optional[ExternalService]:
        """ExternalService 반환"""
        container = cls()
        return container._external_service
    
    @classmethod
    def set_storage_service(cls, service: Optional[StorageService]):
        """StorageService 설정"""
        container = cls()
        container._storage_service = service
    
    @classmethod
    def get_storage_service(cls) -> Optional[StorageService]:
        """StorageService 반환"""
        container = cls()
        return container._storage_service
    
    @classmethod
    def set_search_service(cls, service: Optional[SearchService]):
        """SearchService 설정"""
        container = cls()
        container._search_service = service
    
    @classmethod
    def get_search_service(cls) -> Optional[SearchService]:
        """SearchService 반환"""
        container = cls()
        return container._search_service
    
    @classmethod
    def set_vectordb_service(cls, service: Optional[VectorDbService]):
        """VectorDbService 설정"""
        container = cls()
        container._vectordb_service = service
    
    @classmethod
    def get_vectordb_service(cls) -> Optional[VectorDbService]:
        """VectorDbService 반환"""
        container = cls()
        return container._vectordb_service
    
    @classmethod
    def get_service_status(cls) -> dict:
        """모든 서비스 상태 반환"""
        container = cls()
        
        # 기존 ServiceContainer 관리 서비스들
        status = {
            "database": container._database_service is not None,
            "cache": container._cache_service is not None,
            "lock": container._lock_service_initialized,
            "scheduler": container._scheduler_service_initialized,
            "queue": container._queue_service_initialized,
            "websocket": container._websocket_service_initialized
        }
        
        # Singleton 패턴 서비스들 (동적 import로 순환 import 방지)
        try:
            from service.external.external_service import ExternalService
            status["external"] = ExternalService.is_initialized()
        except ImportError:
            status["external"] = False
            
        try:
            from service.storage.storage_service import StorageService
            status["storage"] = StorageService.is_initialized()
        except ImportError:
            status["storage"] = False
            
        try:
            from service.search.search_service import SearchService
            status["search"] = SearchService.is_initialized()
        except ImportError:
            status["search"] = False
            
        try:
            from service.vectordb.vectordb_service import VectorDbService
            status["vectordb"] = VectorDbService.is_initialized()
        except ImportError:
            status["vectordb"] = False
            
        return status
    
    @classmethod
    def is_initialized(cls) -> bool:
        """서비스 컨테이너가 초기화되었는지 확인"""
        container = cls()
        return container._database_service is not None