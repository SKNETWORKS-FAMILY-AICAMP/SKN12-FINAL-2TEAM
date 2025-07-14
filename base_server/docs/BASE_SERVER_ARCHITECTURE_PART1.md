# Base Server Architecture Documentation - Part 1: Redis 키 시스템 및 캐시

## 목차
1. [개요](#개요)
2. [Redis 키 네임스페이스 구조](#redis-키-네임스페이스-구조)
3. [캐시 시스템](#캐시-시스템)
4. [세션 관리](#세션-관리)
5. [분산락 시스템](#분산락-시스템)

---

## 개요

Base Server는 금융 서비스를 위한 확장 가능한 백엔드 아키텍처입니다. Redis를 중심으로 한 캐시 시스템, 메시지큐, 이벤트큐, 분산락 등의 기능을 제공합니다.

### 주요 특징
- **멀티테넌트 지원**: 앱별, 환경별 완전 격리
- **고가용성**: 자동 재시도, 연결 관리, 헬스체크
- **확장성**: 샤딩, 파티셔닝, 부하 분산 지원
- **모니터링**: 실시간 메트릭 수집 및 성능 추적

---

## Redis 키 네임스페이스 구조

### 기본 네임스페이스 패턴

모든 Redis 키는 다음과 같은 계층 구조를 따릅니다:

```
{app_id}:{env}:{service}:{specific_key}
```

**예시:**
```
finance_app:dev:session:abc123-def456
finance_app:prod:mq:message:uuid-1234
finance_app:test:lock:scheduler:outbox_events
```

### 네임스페이스 계층

| 레벨 | 설명 | 예시 |
|------|------|------|
| `app_id` | 애플리케이션 식별자 | `finance_app` |
| `env` | 환경 (dev/test/prod) | `dev`, `prod` |
| `service` | 서비스 유형 | `session`, `mq`, `eq`, `lock` |
| `specific_key` | 구체적인 키 | `user:123`, `message:uuid` |

### 격리 정책

```python
# CacheService에서 자동 적용
class RedisCacheClient:
    def __init__(self, app_id: str, env: str):
        self.cache_key = f"{app_id}:{env}"
    
    def _get_key(self, key: str) -> str:
        return f"{self.cache_key}:{key}"
```

**장점:**
- ✅ 환경별 완전 격리 (dev/prod 데이터 분리)
- ✅ 다중 애플리케이션 지원
- ✅ 키 충돌 방지
- ✅ 운영/개발 환경 안전성

---

## 캐시 시스템

### CacheService 아키텍처

```python
# 서비스 계층 구조
CacheService (싱글톤)
├── RedisCacheClient (연결 관리)
├── CacheClientPool (연결 풀)
├── CacheHash (해시 캐시)
├── CacheRank (랭킹 캐시)
└── Metrics & Monitoring
```

### 핵심 기능

#### 1. 기본 캐시 연산

```python
# String 타입
await cache_service.set_string("user:profile:123", json.dumps(profile_data))
await cache_service.get_string("user:profile:123")

# Hash 타입  
await cache_service.set_hash_all("user:settings:123", {
    "theme": "dark",
    "language": "ko",
    "notifications": "true"
})

# Sorted Set (랭킹)
await cache_service.set_sorted_value("leaderboard:daily", 95.5, "user:123")
```

#### 2. 연결 관리 및 재시도

```python
class RedisCacheClient:
    async def _execute_with_retry(self, operation_name: str, operation_func, *args, **kwargs):
        for attempt in range(self._max_retries):
            try:
                if self._client is None:
                    await self.connect()
                
                result = await operation_func(*args, **kwargs)
                self.metrics.successful_operations += 1
                return result
                
            except aioredis.ConnectionError:
                await self.close()  # 연결 재설정
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay_base * (2 ** attempt))
```

#### 3. 메트릭 수집

```python
@dataclass
class CacheMetrics:
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    connection_failures: int = 0
    timeout_errors: int = 0
    redis_errors: int = 0
```

### 캐시 키 패턴

#### 사용자 관련 캐시
```
user:profile:{user_id}          # 사용자 프로필
user:settings:{user_id}         # 사용자 설정
user:permissions:{user_id}      # 권한 정보
user:hash:{user_guid}:{field}   # 해시 기반 사용자 데이터
```

#### 애플리케이션 캐시
```
config:app:{feature}            # 앱 설정
config:system:{component}       # 시스템 설정
lookup:{table_name}             # 룩업 테이블 캐시
```

---

## 세션 관리

### 세션 아키텍처

```
Client Request → SessionInfo → Redis Session Store
                           → Database (if needed)
```

### 세션 키 구조

| 키 패턴 | 데이터 타입 | 용도 | TTL |
|---------|-------------|------|-----|
| `accessToken:{token}` | String | 토큰 유효성 검증 | session_expire_time |
| `sessionInfo:{token}` | Hash | 세션 상세 정보 | session_expire_time |

### 세션 데이터 구조

```python
@dataclass
class SessionInfo:
    session_id: str
    user_account_id: str  
    account_db_key: int
    shard_id: int
    login_time: datetime
    last_access_time: datetime
    platform_type: int
    client_version: str
    device_info: Optional[str] = None
```

### 세션 관리 흐름

```python
# 1. 세션 생성
async def create_session(account_id: str, account_db_key: int):
    session_id = str(uuid.uuid4())
    access_token = str(uuid.uuid4())
    
    session_info = SessionInfo(
        session_id=session_id,
        user_account_id=account_id,
        account_db_key=account_db_key,
        shard_id=calculate_shard_id(account_db_key),
        login_time=datetime.now(),
        last_access_time=datetime.now()
    )
    
    # Redis에 저장
    await cache_service.set_string(f"accessToken:{access_token}", "valid", expire=session_expire_time)
    await cache_service.set_hash_all(f"sessionInfo:{access_token}", session_info.to_dict())
    
    return access_token

# 2. 세션 검증
async def validate_session(access_token: str) -> Optional[SessionInfo]:
    # 토큰 유효성 확인
    is_valid = await cache_service.get_string(f"accessToken:{access_token}")
    if not is_valid:
        return None
    
    # 세션 정보 조회
    session_data = await cache_service.get_hash_all(f"sessionInfo:{access_token}")
    if session_data:
        # 마지막 접근 시간 업데이트
        session_data["last_access_time"] = datetime.now().isoformat()
        await cache_service.set_hash_field(f"sessionInfo:{access_token}", "last_access_time", session_data["last_access_time"])
        
        return SessionInfo.from_dict(session_data)
    
    return None

# 3. 세션 삭제
async def delete_session(access_token: str):
    await cache_service.delete(f"accessToken:{access_token}")
    await cache_service.delete(f"sessionInfo:{access_token}")
```

### 세션 보안 기능

#### 1. 자동 만료
```python
# 설정 가능한 만료 시간
session_expire_time = 3600  # 1시간 (기본값)

# 접근 시마다 갱신
await cache_service.expire(f"accessToken:{access_token}", session_expire_time)
await cache_service.expire(f"sessionInfo:{access_token}", session_expire_time)
```

#### 2. 토큰 무효화
```python
# 로그아웃 시 즉시 무효화
async def logout(access_token: str):
    await delete_session(access_token)
    Logger.info(f"Session invalidated: {access_token[:8]}...")
```

#### 3. 동시 세션 제한
```python
# 사용자별 활성 세션 추적
user_sessions_key = f"user:sessions:{user_account_id}"
await cache_service.set_add(user_sessions_key, access_token)
await cache_service.expire(user_sessions_key, session_expire_time)

# 최대 세션 수 제한 체크
active_sessions = await cache_service.set_members(user_sessions_key)
if len(active_sessions) > MAX_CONCURRENT_SESSIONS:
    # 가장 오래된 세션 무효화
    oldest_session = active_sessions[0]
    await delete_session(oldest_session)
```

---

## 분산락 시스템

### 분산락 아키텍처

```
Multiple Servers → DistributedLockManager → Redis (Lua Scripts)
                                        → Automatic Release
```

### 분산락 키 구조

| 키 패턴 | 값 | 용도 | TTL |
|---------|-----|------|-----|
| `lock:{key}` | UUID 토큰 | 락 소유권 증명 | 설정 가능 (기본 30초) |

### 구현 세부사항

#### 1. Lua 스크립트 기반 원자적 연산

```lua
-- 락 획득 (Redis SET NX EX)
SET lock:key token EX 30 NX

-- 락 해제 (원자적 검증 후 삭제)
if redis.call("GET", KEYS[1]) == ARGV[1] then
    return redis.call("DEL", KEYS[1])
else
    return 0
end

-- 락 연장 (원자적 검증 후 TTL 연장)
if redis.call("GET", KEYS[1]) == ARGV[1] then
    return redis.call("EXPIRE", KEYS[1], ARGV[2])
else
    return 0
end
```

#### 2. 분산락 매니저

```python
class DistributedLockManager:
    def __init__(self, lock_impl: IDistributedLock):
        self.lock_impl = lock_impl
        self.active_locks: Dict[str, str] = {}  # key -> token
    
    @asynccontextmanager
    async def acquire_lock(self, key: str, ttl: int = 30, timeout: int = 10):
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
```

#### 3. 사용 예시

```python
# 스케줄러 작업에서 분산락 사용
async def process_outbox_events():
    lock_manager = LockService.get_manager()
    
    async with lock_manager.acquire_lock("scheduler:outbox_events", ttl=300):
        # 한 번에 하나의 서버에서만 실행
        await process_pending_outbox_events()
        Logger.info("아웃박스 이벤트 처리 완료")

# 테이블 생성에서 분산락 사용  
async def create_daily_tables():
    async with lock_manager.acquire_lock("scheduler:create_daily_tables"):
        # 중복 테이블 생성 방지
        for table_name in daily_tables:
            await create_table_if_not_exists(table_name)
```

### 분산락 모니터링

```python
# 활성 락 모니터링
active_locks = lock_manager.active_locks
Logger.info(f"Active locks: {list(active_locks.keys())}")

# 락 상태 확인
is_locked = await LockService.is_locked("scheduler:outbox_events")

# 강제 해제 (서버 종료 시)
await lock_manager.force_release_all()
```

### 분산락 사용 시나리오

| 시나리오 | 락 키 | TTL | 용도 |
|----------|-------|-----|------|
| 아웃박스 이벤트 처리 | `scheduler:outbox_events` | 300초 | 중복 처리 방지 |
| 테이블 생성 | `scheduler:create_table` | 60초 | 동시 생성 방지 |
| 큐 정리 작업 | `scheduler:cleanup_queues` | 3600초 | 중복 정리 방지 |
| 월별 요약 | `scheduler:monthly_summary` | 1800초 | 중복 집계 방지 |

---

## 성능 및 모니터링

### 연결 풀 관리

```python
class CacheClientPool:
    def __init__(self, config: CacheConfig):
        self.max_connections = config.max_connections
        self.connection_timeout = config.connection_timeout
        self.pool = []
        self.active_connections = 0
    
    async def get_client(self) -> RedisCacheClient:
        # 연결 풀에서 사용 가능한 클라이언트 반환
        # 필요 시 새 연결 생성
        pass
```

### 헬스체크

```python
async def health_check() -> Dict[str, Any]:
    try:
        # Redis 연결 테스트
        await cache_client.ping()
        
        # 서버 정보 수집
        info = await cache_client.info()
        
        return {
            "healthy": True,
            "redis_version": info.get('redis_version'),
            "connected_clients": info.get('connected_clients'),
            "used_memory_human": info.get('used_memory_human'),
            "keyspace": info.get(f'db{db_number}', {}),
            "metrics": cache_client.get_metrics()
        }
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e),
            "error_type": type(e).__name__
        }
```

### 메트릭 수집

```python
# 성능 메트릭
metrics = {
    "total_operations": 10000,
    "successful_operations": 9950,
    "failed_operations": 50,
    "success_rate": 0.995,
    "average_response_time": 0.025,
    "cache_hit_rate": 0.85,
    "connection_failures": 2,
    "timeout_errors": 1
}
```

---

이것으로 Part 1이 완료되었습니다. Part 2에서는 메시지큐와 이벤트큐 시스템을, Part 3에서는 데이터베이스와 전체 아키텍처를 다루겠습니다.