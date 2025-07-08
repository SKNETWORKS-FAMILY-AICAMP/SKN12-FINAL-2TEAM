import aioredis
from typing import List, Dict, Tuple, Optional
from .cache_client import AbstractCacheClient

class RedisCacheClient(AbstractCacheClient):
    """
    비동기 Redis 캐시 클라이언트.
    - aioredis를 사용하여 비동기 Redis 연동
    - context manager 지원 (async with)
    - app_id, env 기반 네임스페이스 키 사용
    """
    def __init__(self, host: str, port: int, session_expire_time: int, app_id: str, env: str, db: int = 0, password: str = ""):
        self._host = host
        self._port = port
        self._db = db
        self._password = password
        self.session_expire_time = session_expire_time
        self.cache_key = f"{app_id}:{env}"
        self._client: Optional[aioredis.Redis] = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def connect(self):
        if self._client is None:
            # Redis URL 구성
            if self._password:
                url = f"redis://:{self._password}@{self._host}:{self._port}/{self._db}"
            else:
                url = f"redis://{self._host}:{self._port}/{self._db}"
            self._client = await aioredis.from_url(url, decode_responses=True)

    def _get_key(self, key: str) -> str:
        return f"{self.cache_key}:{key}"

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None

    async def scan_keys(self, pattern: str) -> List[str]:
        keys = []
        cursor = 0
        while True:
            cursor, found = await self._client.scan(cursor=cursor, match=pattern)
            keys.extend(found)
            if cursor == 0:
                break
        return keys

    async def delete_keys(self, pattern: str) -> int:
        keys = await self.scan_keys(pattern)
        if keys:
            return await self._client.delete(*keys)
        return 0

    async def get_key_count(self, pattern: str) -> int:
        keys = await self.scan_keys(pattern)
        return len(keys)

    async def set_string(self, key: str, val: str, expire: Optional[int] = None) -> bool:
        k = self._get_key(key)
        if expire:
            return await self._client.set(k, val, ex=expire)
        return await self._client.set(k, val)

    async def get_string(self, key: str) -> Optional[str]:
        k = self._get_key(key)
        return await self._client.get(k)

    async def set_add(self, key: str, val: str) -> bool:
        k = self._get_key(key)
        return await self._client.sadd(k, val) > 0

    async def set_remove(self, key: str, val: str) -> bool:
        k = self._get_key(key)
        return await self._client.srem(k, val) > 0

    async def exists(self, key: str) -> bool:
        k = self._get_key(key)
        return await self._client.exists(k) != 0

    async def expire(self, key: str, seconds: int) -> bool:
        k = self._get_key(key)
        return await self._client.expire(k, seconds)

    async def delete(self, key: str) -> bool:
        k = self._get_key(key)
        return await self._client.delete(k) > 0

    async def incre(self, key: str) -> int:
        k = self._get_key(key)
        return await self._client.incr(k)

    async def set_sorted_value(self, key: str, score: float, value: str) -> bool:
        k = self._get_key(key)
        return await self._client.zadd(k, {value: score}) > 0

    async def set_sorted_value_bulk(self, key: str, pairs: List[Tuple[str, float]]) -> int:
        k = self._get_key(key)
        mapping = {v: s for v, s in pairs}
        return await self._client.zadd(k, mapping)

    async def remove_sorted_value(self, key: str, value: str) -> bool:
        k = self._get_key(key)
        return await self._client.zrem(k, value) > 0

    async def get_sorted_value_count(self, key: str) -> int:
        k = self._get_key(key)
        return await self._client.zcard(k)

    async def get_sorted_value_rank(self, key: str, value: str) -> int:
        k = self._get_key(key)
        res = await self._client.zrank(k, value)
        return res if res is not None else -1

    async def get_sorted_value_rank_desc(self, key: str, value: str) -> int:
        k = self._get_key(key)
        res = await self._client.zrevrank(k, value)
        return res if res is not None else -1

    async def get_sorted_value_score(self, key: str, value: str) -> float:
        k = self._get_key(key)
        res = await self._client.zscore(k, value)
        return res if res is not None else 0.0

    async def get_sorted_value(self, key: str, from_rank: int, to_rank: int) -> List[str]:
        k = self._get_key(key)
        return await self._client.zrange(k, from_rank, to_rank)

    async def get_sorted_value_desc(self, key: str, from_rank: int, to_rank: int) -> List[str]:
        k = self._get_key(key)
        return await self._client.zrevrange(k, from_rank, to_rank)

    async def get_sorted_value_with_scores(self, key: str, from_rank: int, to_rank: int) -> Dict[str, float]:
        k = self._get_key(key)
        res = await self._client.zrange(k, from_rank, to_rank, withscores=True)
        return {v: s for v, s in res}

    async def get_sorted_value_with_scores_desc(self, key: str, from_rank: int, to_rank: int) -> Dict[str, float]:
        k = self._get_key(key)
        res = await self._client.zrevrange(k, from_rank, to_rank, withscores=True)
        return {v: s for v, s in res}

    async def get_set(self, key: str, value: str) -> Optional[str]:
        k = self._get_key(key)
        return await self._client.getset(k, value)

    async def hash_set(self, key: str, field: str, value: str, expiry_second: int = 0) -> bool:
        k = self._get_key(key)
        return await self._client.hset(k, field, value) > 0

    async def hash_mset(self, key: str, pairs: List[Tuple[str, str]], expiry_second: int = 0) -> None:
        k = self._get_key(key)
        mapping = {f: v for f, v in pairs}
        await self._client.hset(k, mapping=mapping)

    async def hash_get(self, key: str, field: str) -> Optional[str]:
        k = self._get_key(key)
        return await self._client.hget(k, field)

    async def hash_mget(self, key: str, fields: List[str]) -> Dict[str, str]:
        k = self._get_key(key)
        values = await self._client.hmget(k, fields)
        return dict(zip(fields, values))

    async def hash_get_all(self, key: str) -> Dict[str, str]:
        k = self._get_key(key)
        return await self._client.hgetall(k)

    async def hash_scan(self, key: str, pattern: str) -> Dict[str, str]:
        k = self._get_key(key)
        cursor = 0
        result = {}
        while True:
            cursor, data = await self._client.hscan(k, cursor=cursor, match=pattern)
            result.update(data)
            if cursor == 0:
                break
        return result

    async def hash_remove(self, key: str, field: str) -> bool:
        k = self._get_key(key)
        return await self._client.hdel(k, field) > 0

    async def get_sorted_value_by_score(self, key: str, from_score: float, to_score: float) -> List[str]:
        k = self._get_key(key)
        return await self._client.zrangebyscore(k, from_score, to_score)

    async def lpush(self, key: str, value: str) -> None:
        k = self._get_key(key)
        await self._client.lpush(k, value)

    async def get_range_from_list(self, key: str, start_index: int, end_index: int) -> List[str]:
        k = self._get_key(key)
        return await self._client.lrange(k, start_index, end_index)

    async def set_random_members(self, key: str, count: int) -> List[str]:
        k = self._get_key(key)
        return await self._client.srandmember(k, count)
