import json
from enum import IntEnum
from typing import Optional, Dict, Any
from service.core.logger import Logger
from .redis_cache_client_pool import RedisCacheClientPool
from .cache_config import CacheConfig, ECacheType

class CacheService:
    """
    캐시 서비스 싱글턴
    - Init()으로 풀을 주입받아야 함
    - 세션 관리 메서드 직접 제공
    - UserHash, Ranking 등 캐시 객체 제공
    """
    _client_pool: Optional[RedisCacheClientPool] = None
    UserHash = None
    Ranking = None

    @classmethod
    def Init(cls, client_pool: RedisCacheClientPool) -> bool:
        """초기화 메서드"""
        cls._client_pool = client_pool
        
        # lazy import로 순환 import 방지
        from .cache_hash import CacheHash
        from .cache_rank import CacheRank
        
        # 유저 캐시
        cls.UserHash = CacheHash("user:hash")
        # 랭크 캐시
        cls.Ranking = CacheRank("rank:score")
        return True

    @classmethod
    def get_client(cls):
        if cls._client_pool is None:
            raise RuntimeError("CacheService is not initialized. Call Init() first.")
        return cls._client_pool.new()
    
    @classmethod
    def is_initialized(cls) -> bool:
        """초기화 여부 확인"""
        return cls._client_pool is not None
    
    @classmethod
    async def shutdown(cls):
        """서비스 종료"""
        # Redis 클라이언트는 컨텍스트 매니저로 관리되므로 별도 종료 불필요
        cls._client_pool = None
        cls.UserHash = None
        cls.Ranking = None
        Logger.info("Cache service shutdown")
    
    # === 세션 관리 메서드들 ===
    
    @classmethod
    async def SetSessionInfo(cls, access_token: str, session_info: Dict[str, Any]) -> bool:
        """세션 정보를 Redis에 저장"""
        try:
            async with cls.get_client() as client:
                session_key = f"session:{access_token}"
                session_json = json.dumps(session_info)
                return await client.set_string(session_key, session_json, expire=client.session_expire_time)
        except Exception as e:
            Logger.error(f"SetSessionInfo error: {e}")
            return False
    
    @classmethod
    async def GetSessionInfo(cls, access_token: str) -> Optional[Dict[str, Any]]:
        """세션 정보를 Redis에서 가져오기"""
        try:
            async with cls.get_client() as client:
                session_key = f"session:{access_token}"
                session_json = await client.get_string(session_key)
                if session_json:
                    return json.loads(session_json)
                return None
        except Exception as e:
            Logger.error(f"GetSessionInfo error: {e}")
            return None
    
    @classmethod
    async def RemoveSessionInfo(cls, access_token: str) -> bool:
        """세션 정보를 Redis에서 삭제"""
        try:
            async with cls.get_client() as client:
                session_key = f"session:{access_token}"
                return await client.delete(session_key)
        except Exception as e:
            Logger.error(f"RemoveSessionInfo error: {e}")
            return False
    
    @classmethod
    async def CheckSessionInfo(cls, access_token: str) -> bool:
        """세션 존재 여부 확인"""
        try:
            async with cls.get_client() as client:
                session_key = f"session:{access_token}"
                return await client.exists(session_key)
        except Exception as e:
            Logger.error(f"CheckSessionInfo error: {e}")
            return False
    
    # === 모니터링 및 관리 메서드 ===
    @classmethod
    async def health_check(cls) -> Dict[str, Any]:
        """Cache 서비스 Health Check"""
        if cls._client_pool is None:
            return {"healthy": False, "error": "Service not initialized"}
        
        try:
            client = cls.get_client()
            async with client as cache_client:
                return await cache_client.health_check()
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    @classmethod
    def get_metrics(cls) -> Dict[str, Any]:
        """Cache 서비스 메트릭 조회"""
        if cls._client_pool is None:
            return {"error": "Service not initialized"}
        
        try:
            client = cls.get_client()
            # 클라이언트 메트릭 바로 가져오기 (비동기 context manager 없이)
            client_metrics = client.get_metrics()
            
            return {
                "service_initialized": True,
                "client_pool_info": {
                    "host": client._host,
                    "port": client._port,
                    "db": client._db,
                    "cache_key": client.cache_key,
                    "session_expire_time": client.session_expire_time
                },
                "client_metrics": client_metrics
            }
        except Exception as e:
            return {"error": str(e)}
    
    @classmethod
    def reset_metrics(cls):
        """Cache 서비스 메트릭 리셋"""
        if cls._client_pool is None:
            Logger.warn("Cannot reset metrics: Service not initialized")
            return
        
        try:
            client = cls.get_client()
            client.reset_metrics()
            Logger.info("Cache service metrics reset")
        except Exception as e:
            Logger.error(f"Failed to reset cache metrics: {e}")
    
    @classmethod
    async def cache_info(cls) -> Dict[str, Any]:
        """Cache 서비스 정보 조회"""
        if cls._client_pool is None:
            return {"error": "Service not initialized"}
        
        try:
            # 세션 테스트
            test_token = "test_session_token"
            test_data = {"user_id": "test_user", "test": True}
            
            # 세션 설정 테스트
            set_result = await cls.SetSessionInfo(test_token, test_data)
            
            # 세션 조회 테스트
            get_result = await cls.GetSessionInfo(test_token)
            
            # 세션 삭제 (테스트 데이터 정리)
            await cls.RemoveSessionInfo(test_token)
            
            return {
                "service_status": "initialized",
                "client_pool_initialized": cls._client_pool is not None,
                "user_hash_available": cls.UserHash is not None,
                "ranking_available": cls.Ranking is not None,
                "session_test": {
                    "set_success": set_result,
                    "get_success": get_result == test_data,
                    "data_integrity": get_result == test_data if get_result else False
                },
                "health_check": await cls.health_check()
            }
        except Exception as e:
            return {"error": str(e)}
