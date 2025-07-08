# cache_rank.py

from typing import List, Dict, Tuple
from .cache_service import CacheService

class CacheRank:
    def __init__(self, redis_key: str):
        self._rank_key = redis_key

    async def clear_rank(self, id: int):
        async with CacheService.get_client() as client:
            redis_key = f"{self._rank_key}:{id}"
            await client.delete(redis_key)

    async def get_count(self, id: int) -> int:
        async with CacheService.get_client() as client:
            redis_key = f"{self._rank_key}:{id}"
            return await client.get_sorted_value_count(redis_key)

    async def set_score(self, id: int, value: str, score: float):
        async with CacheService.get_client() as client:
            redis_key = f"{self._rank_key}:{id}"
            await client.set_sorted_value(redis_key, score, value)

    async def set_score_bulk(self, id: int, pairs: List[Tuple[str, float]]):
        """
        pairs: List of (value, score)
        """
        async with CacheService.get_client() as client:
            redis_key = f"{self._rank_key}:{id}"
            await client.set_sorted_value_bulk(redis_key, pairs)

    async def get_rank(self, id: int, value: str) -> Tuple[int, float]:
        async with CacheService.get_client() as client:
            redis_key = f"{self._rank_key}:{id}"
            rank = await client.get_sorted_value_rank_desc(redis_key, value)
            if rank != -1:
                rank = rank + 1  # 랭크 1부터 시작
            score = await client.get_sorted_value_score(redis_key, value)
            return (rank, score)

    async def get_rank_range(self, id: int, start: int, end: int) -> Dict[str, float]:
        async with CacheService.get_client() as client:
            redis_key = f"{self._rank_key}:{id}"
            return await client.get_sorted_value_with_scores_desc(redis_key, start, end)

    async def remove_rank(self, id: int, value: str) -> bool:
        async with CacheService.get_client() as client:
            redis_key = f"{self._rank_key}:{id}"
            return await client.remove_sorted_value(redis_key, value)
