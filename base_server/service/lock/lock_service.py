from typing import Optional
from .distributed_lock import DistributedLockManager, IDistributedLock, CacheServiceDistributedLock
from service.core.logger import Logger

class LockService:
    """111 gameserver 패턴을 따르는 분산락 서비스"""
    
    _lock_impl: Optional[IDistributedLock] = None
    _lock_manager: Optional[DistributedLockManager] = None
    _initialized: bool = False
    
    @classmethod
    def init(cls, cache_service) -> bool:
        """
        분산락 서비스 초기화
        
        Args:
            cache_service: CacheService 인스턴스 (Redis 클라이언트 제공)
        """
        try:
            if cls._initialized:
                Logger.warn("LockService가 이미 초기화되었습니다")
                return True
            
            # Redis 분산락 구현체 생성 (CacheService 사용)
            cls._lock_impl = CacheServiceDistributedLock(cache_service)
            cls._lock_manager = DistributedLockManager(cls._lock_impl)
            cls._initialized = True
            
            Logger.info("LockService 초기화 완료")
            return True
            
        except Exception as e:
            Logger.error(f"LockService 초기화 실패: {e}")
            return False
    
    @classmethod
    async def shutdown(cls):
        """서비스 종료 및 정리"""
        try:
            if cls._lock_manager:
                await cls._lock_manager.force_release_all()
            
            cls._lock_impl = None
            cls._lock_manager = None
            cls._initialized = False
            
            Logger.info("LockService 종료 완료")
            
        except Exception as e:
            Logger.error(f"LockService 종료 중 오류: {e}")
    
    @classmethod
    def is_initialized(cls) -> bool:
        """초기화 상태 확인"""
        return cls._initialized
    
    @classmethod
    def get_manager(cls) -> DistributedLockManager:
        """락 매니저 인스턴스 반환"""
        if not cls._initialized or cls._lock_manager is None:
            raise RuntimeError("LockService가 초기화되지 않았습니다")
        
        return cls._lock_manager
    
    @classmethod
    async def acquire(cls, key: str, ttl: int = 30, timeout: int = 10) -> Optional[str]:
        """락 획득 (직접 호출)"""
        if not cls._initialized or cls._lock_impl is None:
            raise RuntimeError("LockService가 초기화되지 않았습니다")
        
        return await cls._lock_impl.acquire(key, ttl, timeout)
    
    @classmethod
    async def release(cls, key: str, token: str) -> bool:
        """락 해제 (직접 호출)"""
        if not cls._initialized or cls._lock_impl is None:
            raise RuntimeError("LockService가 초기화되지 않았습니다")
        
        return await cls._lock_impl.release(key, token)
    
    @classmethod
    async def extend(cls, key: str, token: str, ttl: int = 30) -> bool:
        """락 만료시간 연장"""
        if not cls._initialized or cls._lock_impl is None:
            raise RuntimeError("LockService가 초기화되지 않았습니다")
        
        return await cls._lock_impl.extend(key, token, ttl)
    
    @classmethod
    async def is_locked(cls, key: str) -> bool:
        """락 상태 확인"""
        if not cls._initialized or cls._lock_impl is None:
            raise RuntimeError("LockService가 초기화되지 않았습니다")
        
        return await cls._lock_impl.is_locked(key)