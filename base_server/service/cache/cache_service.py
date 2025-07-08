import json
from enum import IntEnum
from typing import Optional, Dict, Any
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
            print(f"SetSessionInfo error: {e}")
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
            print(f"GetSessionInfo error: {e}")
            return None
    
    @classmethod
    async def RemoveSessionInfo(cls, access_token: str) -> bool:
        """세션 정보를 Redis에서 삭제"""
        try:
            async with cls.get_client() as client:
                session_key = f"session:{access_token}"
                return await client.delete(session_key)
        except Exception as e:
            print(f"RemoveSessionInfo error: {e}")
            return False
    
    @classmethod
    async def CheckSessionInfo(cls, access_token: str) -> bool:
        """세션 존재 여부 확인"""
        try:
            async with cls.get_client() as client:
                session_key = f"session:{access_token}"
                return await client.exists(session_key)
        except Exception as e:
            print(f"CheckSessionInfo error: {e}")
            return False
