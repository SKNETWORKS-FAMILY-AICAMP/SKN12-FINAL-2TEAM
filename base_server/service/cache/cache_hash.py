from typing import List, Dict, Tuple, Optional
from .cache_service import CacheService

class CacheHash:
    def __init__(self, hash_key: str):
        self._hash_key = hash_key

    async def set(self, user_guid: str, field: str, value: str):
        async with CacheService.get_client() as client:
            redis_key = f"{self._hash_key}:{user_guid}"
            await client.hash_set(redis_key, field, value)

    async def set_bulk(self, user_guid: str, value_pairs: List[Tuple[str, str]]):
        """
        value_pairs: List of (field, value)
        """
        if not value_pairs:  # 빈 리스트 체크 추가
            return
        async with CacheService.get_client() as client:
            redis_key = f"{self._hash_key}:{user_guid}"
            await client.hash_mset(redis_key, value_pairs)

    async def get(self, user_guid: str, field: str) -> Optional[str]:
        async with CacheService.get_client() as client:
            redis_key = f"{self._hash_key}:{user_guid}"
            return await client.hash_get(redis_key, field)

    async def get_bulk(self, user_guid: str, fields: List[str]) -> Dict[str, str]:
        async with CacheService.get_client() as client:
            redis_key = f"{self._hash_key}:{user_guid}"
            return await client.hash_mget(redis_key, fields)

    async def get_all(self, user_guid: str) -> Dict[str, str]:
        async with CacheService.get_client() as client:
            redis_key = f"{self._hash_key}:{user_guid}"
            return await client.hash_get_all(redis_key)
