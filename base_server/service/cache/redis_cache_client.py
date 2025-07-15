import aioredis
import asyncio
import time
import random
import json
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
from service.core.logger import Logger
from .cache_client import AbstractCacheClient

class ConnectionState(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"

@dataclass
class CacheMetrics:
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    total_response_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    last_operation_time: Optional[float] = None
    connection_failures: int = 0
    timeout_errors: int = 0
    redis_errors: int = 0

class RedisCacheClient(AbstractCacheClient):
    """
    비동기 Redis 캐시 클라이언트 - 연결 관리, 재시도, 메트릭 포함
    - aioredis를 사용하여 비동기 Redis 연동
    - context manager 지원 (async with)
    - app_id, env 기반 네임스페이스 키 사용
    - 향상된 연결 관리 및 모니터링
    """
    def __init__(self, host: str, port: int, session_expire_time: int, app_id: str, env: str, db: int = 0, password: str = "", max_retries: int = 3, connection_timeout: int = 5):
        self._host = host
        self._port = port
        self._db = db
        self._password = password
        self.session_expire_time = session_expire_time
        self.cache_key = f"{app_id}:{env}"
        self._client: Optional[aioredis.Redis] = None
        self.metrics = CacheMetrics()
        self.connection_state = ConnectionState.HEALTHY
        self._last_health_check = 0
        self._max_retries = max_retries
        self._retry_delay_base = 0.5
        self._connection_timeout = connection_timeout
        self._socket_timeout = 30

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def connect(self):
        """Redis 연결 생성 (Enhanced connection management with retry)"""
        for attempt in range(self._max_retries):
            try:
                if self._client is None:
                    # Redis URL 구성
                    if self._password:
                        url = f"redis://:{self._password}@{self._host}:{self._port}/{self._db}"
                    else:
                        url = f"redis://{self._host}:{self._port}/{self._db}"
                    
                    # 향상된 연결 설정
                    self._client = await aioredis.from_url(
                        url, 
                        decode_responses=True,
                        socket_connect_timeout=self._connection_timeout,
                        socket_timeout=self._socket_timeout,
                        retry_on_timeout=True,
                        health_check_interval=30,
                        max_connections=20
                    )
                    
                    # 연결 테스트
                    await self._test_connection()
                    self.connection_state = ConnectionState.HEALTHY
                    # 임시로 주석 처리 - Redis 연결 로그 제거
                    # Logger.debug(f"Redis cache client connected to {self._host}:{self._port}/{self._db}")
                
                return
                
            except aioredis.ConnectionError as e:
                self.metrics.connection_failures += 1
                self.connection_state = ConnectionState.FAILED
                Logger.warn(f"Redis connection failed (attempt {attempt + 1}/{self._max_retries}): {e}")
                
            except Exception as e:
                self.metrics.connection_failures += 1
                self.connection_state = ConnectionState.DEGRADED
                Logger.warn(f"Redis client initialization failed (attempt {attempt + 1}/{self._max_retries}): {e}")
            
            # 재시도 대기
            if attempt < self._max_retries - 1:
                delay = self._retry_delay_base * (2 ** attempt) + random.uniform(0, 0.5)
                await asyncio.sleep(delay)
        
        # 모든 재시도 실패
        self.connection_state = ConnectionState.FAILED
        raise aioredis.ConnectionError(f"Failed to connect to Redis after {self._max_retries} attempts")

    def _get_key(self, key: str) -> str:
        return f"{self.cache_key}:{key}"

    async def _test_connection(self):
        """Redis 연결 테스트"""
        if self._client:
            await self._client.ping()
    
    async def _execute_with_retry(self, operation_name: str, operation_func, *args, **kwargs):
        """재시도 로직을 포함한 Redis 작업 실행"""
        start_time = time.time()
        self.metrics.total_operations += 1
        self.metrics.last_operation_time = start_time
        
        for attempt in range(self._max_retries):
            try:
                if self._client is None:
                    await self.connect()
                    if self._client is None:
                        raise aioredis.ConnectionError("Failed to establish Redis connection")
                
                result = await operation_func(*args, **kwargs)
                
                # 성공 메트릭
                operation_time = time.time() - start_time
                self.metrics.successful_operations += 1
                self.metrics.total_response_time += operation_time
                
                # Cache hit/miss 추적 (get 계열 작업)
                if 'get' in operation_name.lower() and result is not None:
                    self.metrics.cache_hits += 1
                elif 'get' in operation_name.lower() and result is None:
                    self.metrics.cache_misses += 1
                
                return result
                
            except aioredis.ConnectionError as e:
                self.metrics.connection_failures += 1
                self.connection_state = ConnectionState.FAILED
                Logger.warn(f"Redis {operation_name} connection error (attempt {attempt + 1}/{self._max_retries}): {e}")
                
                # 연결 재설정
                await self.close()
                
            except asyncio.TimeoutError as e:
                self.metrics.timeout_errors += 1
                Logger.warn(f"Redis {operation_name} timeout error (attempt {attempt + 1}/{self._max_retries}): {e}")
                
            except aioredis.RedisError as e:
                self.metrics.redis_errors += 1
                Logger.warn(f"Redis {operation_name} error (attempt {attempt + 1}/{self._max_retries}): {e}")
                
            except Exception as e:
                Logger.warn(f"Redis {operation_name} unexpected error (attempt {attempt + 1}/{self._max_retries}): {e}")
            
            # 재시도 대기
            if attempt < self._max_retries - 1:
                delay = self._retry_delay_base * (2 ** attempt) + random.uniform(0, 0.5)
                await asyncio.sleep(delay)
        
        # 모든 재시도 실패
        self.metrics.failed_operations += 1
        total_time = time.time() - start_time
        Logger.error(f"Redis {operation_name} failed after {self._max_retries} attempts (total: {total_time:.3f}s)")
        raise aioredis.ConnectionError(f"Redis {operation_name} failed after {self._max_retries} attempts")
    
    async def close(self):
        if self._client:
            try:
                await self._client.close()
            except:
                pass
            self._client = None
            # 임시로 주석 처리 - Redis 로그 출력 제거
            # Logger.debug("Redis cache client closed")
            
            # 임시로 주석 처리 - 최종 메트릭 로깅 제거
            # final_metrics = self.get_metrics()
            # Logger.debug(f"Final Redis cache metrics: {final_metrics}")

    async def scan_keys(self, pattern: str) -> List[str]:
        async def _scan_operation():
            keys = []
            cursor = 0
            while True:
                cursor, found = await self._client.scan(cursor=cursor, match=pattern)
                keys.extend(found)
                if cursor == 0:
                    break
            return keys
        
        return await self._execute_with_retry("scan_keys", _scan_operation)

    async def delete_keys(self, pattern: str) -> int:
        keys = await self.scan_keys(pattern)
        if keys:
            return await self._client.delete(*keys)
        return 0

    async def get_key_count(self, pattern: str) -> int:
        keys = await self.scan_keys(pattern)
        return len(keys)

    async def set_string(self, key: str, val: str, expire: Optional[int] = None, nx: bool = False) -> bool:
        k = self._get_key(key)
        kwargs = {}
        if expire:
            kwargs['ex'] = expire
        if nx:
            kwargs['nx'] = True
        
        result = await self._execute_with_retry("set_string", self._client.set, k, val, **kwargs)
        return result is not None if nx else bool(result)

    async def get_string(self, key: str) -> Optional[str]:
        k = self._get_key(key)
        return await self._execute_with_retry("get_string", self._client.get, k)

    async def set_add(self, key: str, val: str) -> bool:
        k = self._get_key(key)
        return await self._client.sadd(k, val) > 0

    async def set_remove(self, key: str, val: str) -> bool:
        k = self._get_key(key)
        return await self._client.srem(k, val) > 0

    async def exists(self, key: str) -> bool:
        k = self._get_key(key)
        result = await self._execute_with_retry("exists", self._client.exists, k)
        return result != 0

    async def expire(self, key: str, seconds: int) -> bool:
        k = self._get_key(key)
        return await self._client.expire(k, seconds)

    async def delete(self, key: str) -> bool:
        k = self._get_key(key)
        result = await self._execute_with_retry("delete", self._client.delete, k)
        return result > 0

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
        if not pairs:  # 빈 리스트 체크 추가
            return
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
        return await self._execute_with_retry("set_random_members", self._client.srandmember, k, count)
    
    # === 모니터링 및 관리 메소드들 ===
    
    async def health_check(self) -> Dict[str, Any]:
        """Redis 연결 상태 확인"""
        start_time = time.time()
        
        try:
            if self._client is None:
                await self.connect()
            
            # PING 테스트
            await self._client.ping()
            
            # INFO 명령으로 서버 정보 가져오기
            info = await self._client.info()
            
            response_time = time.time() - start_time
            self.connection_state = ConnectionState.HEALTHY
            self._last_health_check = time.time()
            
            return {
                "healthy": True,
                "response_time": response_time,
                "connection_state": self.connection_state.value,
                "host": self._host,
                "port": self._port,
                "db": self._db,
                "redis_version": info.get('redis_version', 'unknown'),
                "connected_clients": info.get('connected_clients', 0),
                "used_memory_human": info.get('used_memory_human', 'unknown'),
                "keyspace": info.get(f'db{self._db}', {}),
                "metrics": self.get_metrics()
            }
            
        except aioredis.ConnectionError as e:
            self.connection_state = ConnectionState.FAILED
            return {
                "healthy": False,
                "error": f"Connection error: {e}",
                "error_type": "connection",
                "connection_state": self.connection_state.value,
                "host": self._host,
                "port": self._port,
                "metrics": self.get_metrics()
            }
        except Exception as e:
            self.connection_state = ConnectionState.DEGRADED
            return {
                "healthy": False,
                "error": str(e),
                "error_type": "unknown",
                "connection_state": self.connection_state.value,
                "host": self._host,
                "port": self._port,
                "metrics": self.get_metrics()
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Redis 캐시 클라이언트 메트릭 조회"""
        avg_response_time = 0.0
        success_rate = 0.0
        cache_hit_rate = 0.0
        
        if self.metrics.successful_operations > 0:
            avg_response_time = self.metrics.total_response_time / self.metrics.successful_operations
        
        if self.metrics.total_operations > 0:
            success_rate = self.metrics.successful_operations / self.metrics.total_operations
        
        total_cache_operations = self.metrics.cache_hits + self.metrics.cache_misses
        if total_cache_operations > 0:
            cache_hit_rate = self.metrics.cache_hits / total_cache_operations
        
        return {
            "total_operations": self.metrics.total_operations,
            "successful_operations": self.metrics.successful_operations,
            "failed_operations": self.metrics.failed_operations,
            "success_rate": success_rate,
            "average_response_time": avg_response_time,
            "cache_hits": self.metrics.cache_hits,
            "cache_misses": self.metrics.cache_misses,
            "cache_hit_rate": cache_hit_rate,
            "connection_failures": self.metrics.connection_failures,
            "timeout_errors": self.metrics.timeout_errors,
            "redis_errors": self.metrics.redis_errors,
            "last_operation_time": self.metrics.last_operation_time,
            "connection_state": self.connection_state.value,
            "last_health_check": self._last_health_check
        }
    
    def reset_metrics(self):
        """메트릭 초기화"""
        self.metrics = CacheMetrics()
        Logger.info("Redis cache client metrics reset")
    
    # === 메시지큐/이벤트큐용 추가 메서드들 ===
    
    async def set_hash_all(self, key: str, mapping: Dict[str, str]) -> bool:
        """해시에 여러 필드를 한번에 설정"""
        k = self._get_key(key)
        try:
            # 디버깅: 원본 mapping 로그 (임시로 주석 처리)
            # Logger.debug(f"set_hash_all mapping types: {[(k, type(v).__name__) for k, v in mapping.items()]}")
            
            # 모든 값을 문자열로 변환하여 Redis 호환성 보장
            string_mapping = {}
            for field, value in mapping.items():
                if isinstance(value, (dict, list)):
                    string_mapping[str(field)] = json.dumps(value)
                else:
                    string_mapping[str(field)] = str(value)
            
            # aioredis hset 호출 - 하나씩 설정하는 안전한 방식
            # mapping이 비어있지 않은 경우만 실행
            if string_mapping:
                async def _hset_operation():
                    # Redis 호환성을 위해 하나씩 설정
                    for field, value in string_mapping.items():
                        await self._client.hset(k, field, value)
                    return True
                result = await self._execute_with_retry("set_hash_all", _hset_operation)
                return result is not None
            return True
        except Exception:
            return False
    
    async def set_hash_field(self, key: str, field: str, value: str) -> bool:
        """해시의 특정 필드 설정"""
        k = self._get_key(key)
        try:
            await self._execute_with_retry("set_hash_field", self._client.hset, k, field, value)
            return True
        except Exception:
            return False
    
    async def get_hash_all(self, key: str) -> Dict[str, str]:
        """해시의 모든 필드 조회"""
        k = self._get_key(key)
        return await self._execute_with_retry("get_hash_all", self._client.hgetall, k) or {}
    
    async def hash_delete(self, key: str, field: str) -> bool:
        """해시의 특정 필드 삭제"""
        k = self._get_key(key)
        try:
            result = await self._execute_with_retry("hash_delete", self._client.hdel, k, field)
            return result > 0
        except Exception:
            return False
    
    async def delete_key(self, key: str) -> bool:
        """키 삭제"""
        k = self._get_key(key)
        try:
            result = await self._execute_with_retry("delete_key", self._client.delete, k)
            return result > 0
        except Exception:
            return False
    
    async def set_expire(self, key: str, seconds: int) -> bool:
        """키에 만료시간 설정"""
        k = self._get_key(key)
        try:
            return await self._execute_with_retry("set_expire", self._client.expire, k, seconds)
        except Exception:
            return False
    
    async def list_push_right(self, key: str, value: str) -> int:
        """리스트 오른쪽에 값 추가"""
        k = self._get_key(key)
        return await self._execute_with_retry("list_push_right", self._client.rpush, k, value)
    
    async def list_push_left(self, key: str, value: str) -> int:
        """리스트 왼쪽에 값 추가"""
        k = self._get_key(key)
        return await self._execute_with_retry("list_push_left", self._client.lpush, k, value)
    
    async def list_pop_left(self, key: str) -> Optional[str]:
        """리스트 왼쪽에서 값 제거 및 반환"""
        k = self._get_key(key)
        return await self._execute_with_retry("list_pop_left", self._client.lpop, k)
    
    async def list_pop_right(self, key: str) -> Optional[str]:
        """리스트 오른쪽에서 값 제거 및 반환"""
        k = self._get_key(key)
        return await self._execute_with_retry("list_pop_right", self._client.rpop, k)
    
    async def list_length(self, key: str) -> int:
        """리스트 길이 조회"""
        k = self._get_key(key)
        return await self._execute_with_retry("list_length", self._client.llen, k) or 0
    
    async def list_range(self, key: str, start: int, end: int) -> List[str]:
        """리스트 범위 조회"""
        k = self._get_key(key)
        return await self._execute_with_retry("list_range", self._client.lrange, k, start, end) or []
    
    async def list_trim(self, key: str, start: int, end: int) -> bool:
        """리스트 트림 (지정 범위만 유지)"""
        k = self._get_key(key)
        try:
            await self._execute_with_retry("list_trim", self._client.ltrim, k, start, end)
            return True
        except Exception:
            return False
    
    async def list_index(self, key: str, index: int) -> Optional[str]:
        """리스트 특정 인덱스 값 조회"""
        k = self._get_key(key)
        return await self._execute_with_retry("list_index", self._client.lindex, k, index)
    
    async def list_remove(self, key: str, value: str, count: int = 1) -> int:
        """리스트에서 값 제거"""
        k = self._get_key(key)
        return await self._execute_with_retry("list_remove", self._client.lrem, k, count, value) or 0
    
    # Sorted Set 메서드들 (지연 메시지용)
    async def sorted_set_add(self, key: str, score: float, member: str) -> int:
        """Sorted Set에 멤버 추가"""
        k = self._get_key(key)
        return await self._execute_with_retry("sorted_set_add", self._client.zadd, k, {member: score}) or 0
    
    async def sorted_set_remove(self, key: str, member: str) -> int:
        """Sorted Set에서 멤버 제거"""
        k = self._get_key(key)
        return await self._execute_with_retry("sorted_set_remove", self._client.zrem, k, member) or 0
    
    async def sorted_set_range_by_score(self, key: str, min_score: float, max_score: float, 
                                      offset: int = 0, count: int = 100) -> List[str]:
        """Sorted Set에서 점수 범위로 조회"""
        k = self._get_key(key)
        return await self._execute_with_retry(
            "sorted_set_range_by_score", 
            self._client.zrangebyscore, 
            k, min_score, max_score, start=offset, num=count
        ) or []
    
    async def sorted_set_count(self, key: str) -> int:
        """Sorted Set 멤버 수 조회"""
        k = self._get_key(key)
        return await self._execute_with_retry("sorted_set_count", self._client.zcard, k) or 0
    
    async def sorted_set_length(self, key: str) -> int:
        """Sorted Set 길이 조회 (sorted_set_count와 동일)"""
        return await self.sorted_set_count(key)
    
    # Redis Stream 메서드들 (이벤트큐용) - 기본 구현
    async def stream_add(self, key: str, fields: Dict[str, str], message_id: str = "*") -> str:
        """Redis Stream에 메시지 추가 (향후 구현)"""
        # 현재는 리스트로 대체
        k = self._get_key(f"stream:{key}")
        message_data = json.dumps({"id": message_id, "fields": fields, "timestamp": time.time()})
        await self.list_push_right(k, message_data)
        return f"{int(time.time() * 1000)}-0"  # 임시 메시지 ID
    
    async def stream_create_group(self, key: str, group_name: str, start_id: str = "$", mkstream: bool = False):
        """Redis Stream Consumer Group 생성 (향후 구현)"""
        # 현재는 패스
        pass
    
    # Pub/Sub 메서드들 (이벤트큐용) - 기본 구현
    async def publish(self, channel: str, message: str) -> int:
        """채널에 메시지 발행 (향후 구현)"""
        # 현재는 리스트로 대체
        k = self._get_key(f"pubsub:{channel}")
        await self.list_push_right(k, message)
        return 1
    
    # Lua 스크립트 실행 (분산락용)
    async def eval_script(self, script: str, keys: List[str], args: List[str]) -> Any:
        """Lua 스크립트 실행"""
        # 키에 네임스페이스 적용
        namespaced_keys = [self._get_key(key) for key in keys]
        return await self._execute_with_retry("eval_script", self._client.eval, script, len(namespaced_keys), *namespaced_keys, *args)
    
    async def eval(self, script: str, numkeys: int, *args) -> Any:
        """Lua 스크립트 실행 (호환성)"""
        return await self._execute_with_retry("eval", self._client.eval, script, numkeys, *args)
