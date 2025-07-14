"""
서비스 컨테이너 - 전역 서비스 인스턴스 관리
"""

from typing import Optional
from service.db.database_service import DatabaseService
from service.cache.cache_service import CacheService

class ServiceContainer:
    """전역 서비스 인스턴스를 관리하는 컨테이너"""
    
    _instance: Optional['ServiceContainer'] = None
    _database_service: Optional[DatabaseService] = None
    _cache_service: Optional[CacheService] = None
    _lock_service_initialized: bool = False
    _scheduler_service_initialized: bool = False
    _queue_service_initialized: bool = False
    
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