import time
import uuid
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from service.core.logger import Logger

class IDistributedLock(ABC):
    """분산락 인터페이스"""
    
    @abstractmethod
    async def acquire(self, key: str, ttl: int = 30, timeout: int = 10) -> Optional[str]:
        """락 획득"""
        pass
    
    @abstractmethod
    async def release(self, key: str, token: str) -> bool:
        """락 해제"""
        pass
    
    @abstractmethod
    async def extend(self, key: str, token: str, ttl: int = 30) -> bool:
        """락 만료시간 연장"""
        pass
    
    @abstractmethod
    async def is_locked(self, key: str) -> bool:
        """락 상태 확인"""
        pass

class CacheServiceDistributedLock(IDistributedLock):
    """CacheService를 사용하는 Redis 분산락"""
    
    def __init__(self, cache_service):
        self.cache_service = cache_service
        self.lock_prefix = "lock:"
    
    async def _sleep(self, seconds: float):
        """비동기 sleep"""
        import asyncio
        await asyncio.sleep(seconds)
    
    async def acquire(self, key: str, ttl: int = 30, timeout: int = 10) -> Optional[str]:
        """락 획득"""
        import uuid
        import time
        
        lock_key = f"{self.lock_prefix}{key}"
        token = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            while time.time() - start_time < timeout:
                # CacheService를 통한 안전한 Redis 작업
                async with self.cache_service.get_client() as client:
                    # SET key value EX ttl NX (존재하지 않을 때만 설정)
                    # set_string은 자동으로 _get_key()를 적용하므로 lock_key를 그대로 사용
                    result = await client.set_string(
                        lock_key, 
                        token, 
                        expire=ttl,
                        nx=True  # Not eXists
                    )
                    
                    if result:
                        Logger.info(f"분산락 획득 성공: {key}, token: {token[:8]}...")
                        return token
                
                # 짧은 시간 대기 후 재시도
                await self._sleep(0.1)
            
            Logger.warn(f"분산락 획득 타임아웃: {key}")
            return None
            
        except Exception as e:
            Logger.error(f"분산락 획득 실패: {key} - {e}")
            return None
    
    async def release(self, key: str, token: str) -> bool:
        """락 해제"""
        lock_key = f"{self.lock_prefix}{key}"
        
        try:
            async with self.cache_service.get_client() as client:
                # Lua 스크립트로 원자적 해제 (토큰 확인 후 삭제)
                lua_script = """
                if redis.call("GET", KEYS[1]) == ARGV[1] then
                    return redis.call("DEL", KEYS[1])
                else
                    return 0
                end
                """
                
                # eval()은 _get_key()를 자동 적용하지 않으므로 수동으로 full key 구성
                full_key = client._get_key(lock_key)
                result = await client.eval(lua_script, 1, full_key, token)
                
                if result == 1:
                    Logger.info(f"분산락 해제 성공: {key}")
                    return True
                else:
                    Logger.warn(f"분산락 해제 실패: {key} (토큰 불일치 또는 이미 해제됨)")
                    return False
                    
        except Exception as e:
            Logger.error(f"분산락 해제 실패: {key} - {e}")
            return False
    
    async def extend(self, key: str, token: str, ttl: int = 30) -> bool:
        """락 연장"""
        lock_key = f"{self.lock_prefix}{key}"
        
        try:
            async with self.cache_service.get_client() as client:
                # Lua 스크립트로 원자적 연장 (토큰 확인 후 TTL 연장)
                lua_script = """
                if redis.call("GET", KEYS[1]) == ARGV[1] then
                    return redis.call("EXPIRE", KEYS[1], ARGV[2])
                else
                    return 0
                end
                """
                
                # eval()은 _get_key()를 자동 적용하지 않으므로 수동으로 full key 구성
                full_key = client._get_key(lock_key)
                result = await client.eval(lua_script, 1, full_key, token, ttl)
                
                if result == 1:
                    Logger.info(f"분산락 연장 성공: {key}")
                    return True
                else:
                    Logger.warn(f"분산락 연장 실패: {key} (토큰 불일치)")
                    return False
                    
        except Exception as e:
            Logger.error(f"분산락 연장 실패: {key} - {e}")
            return False
    
    async def is_locked(self, key: str) -> bool:
        """락 상태 확인"""
        lock_key = f"{self.lock_prefix}{key}"
        
        try:
            async with self.cache_service.get_client() as client:
                result = await client.get_string(lock_key)
                return result is not None
                
        except Exception as e:
            Logger.error(f"분산락 상태 확인 실패: {key} - {e}")
            return False


class DistributedLockManager:
    """분산락 매니저 (컨텍스트 매니저 지원)"""
    
    def __init__(self, lock_impl: IDistributedLock):
        self.lock_impl = lock_impl
        self.active_locks: Dict[str, str] = {}  # key -> token
    
    @asynccontextmanager
    async def acquire_lock(self, key: str, ttl: int = 30, timeout: int = 10):
        """
        컨텍스트 매니저로 분산락 사용
        
        Usage:
            async with lock_manager.acquire_lock("scheduler:create_table"):
                # 락이 보장된 코드 블록
                await create_daily_table()
        """
        token = None
        try:
            token = await self.lock_impl.acquire(key, ttl, timeout)
            
            if token is None:
                raise RuntimeError(f"분산락 획득 실패: {key}")
            
            self.active_locks[key] = token
            yield token
            
        finally:
            if token and key in self.active_locks:
                await self.lock_impl.release(key, token)
                del self.active_locks[key]
    
    async def force_release_all(self):
        """모든 활성 락 강제 해제 (종료 시 정리)"""
        for key, token in list(self.active_locks.items()):
            try:
                await self.lock_impl.release(key, token)
                Logger.info(f"강제 해제된 락: {key}")
            except Exception as e:
                Logger.error(f"락 강제 해제 실패: {key} - {e}")
        
        self.active_locks.clear()