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
    def is_initialized(cls) -> bool:
        """서비스 컨테이너가 초기화되었는지 확인"""
        container = cls()
        return container._database_service is not None