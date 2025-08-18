# AI Trading Platform — Lock Service

> **개요**: SKN12-FINAL-2TEAM의 AI 트레이딩 플랫폼 백엔드 Lock 서비스입니다. Redis 기반 분산락 서비스로, 111 gameserver 패턴을 따르는 정적 클래스 시스템입니다. 분산 환경에서 동시 작업 실행을 제어하고 중복 처리를 방지합니다.

---

## 🏗️ 프로젝트 구조

### 디렉토리 구조
```
lock/
├── __init__.py                    # 패키지 초기화
├── lock_service.py                # 메인 Lock 서비스 (정적 클래스)
└── distributed_lock.py            # 분산락 구현체 및 매니저
```

---

## 🔧 핵심 기능

### 1. **Lock 서비스 (LockService)**
- **111 gameserver 패턴**: 정적 클래스로 서비스 인스턴스 관리
- **초기화 관리**: `init()`, `shutdown()`, `is_initialized()` 메서드
- **분산락 지원**: Redis 기반 분산 환경에서 동시성 제어
- **자동 정리**: 서비스 종료 시 모든 활성 락 자동 해제

### 2. **분산락 관리**
- **락 획득**: `acquire()` 메서드로 TTL과 타임아웃 설정
- **락 해제**: `release()` 메서드로 토큰 기반 안전한 해제
- **락 연장**: `extend()` 메서드로 만료시간 연장
- **상태 확인**: `is_locked()` 메서드로 락 상태 조회

### 3. **고급 기능**
- **컨텍스트 매니저**: `async with` 구문으로 자동 락 관리
- **토큰 기반 보안**: UUID 토큰으로 락 소유권 검증
- **Lua 스크립트**: Redis에서 원자적 작업 수행
- **강제 해제**: 서버 종료 시 모든 락 자동 정리

---

## 📚 사용된 라이브러리

### **백엔드 & 인프라**
- **contextlib.asynccontextmanager**: 비동기 컨텍스트 매니저
- **abc**: 추상 클래스 및 인터페이스 정의

### **개발 도구**
- **typing**: 타입 힌트 및 타입 안전성
- **service.core.logger.Logger**: 구조화된 로깅 시스템

---

## 🪝 핵심 클래스 및 메서드

### **LockService - 메인 서비스 클래스**

```python
class LockService:
    """111 gameserver 패턴을 따르는 분산락 서비스"""
    
    _lock_impl: Optional[IDistributedLock] = None
    _lock_manager: Optional[DistributedLockManager] = None
    _initialized: bool = False
    
    @classmethod
    def init(cls, cache_service) -> bool:
        """분산락 서비스 초기화"""
        # CacheService를 통한 Redis 분산락 구현체 생성
    
    @classmethod
    async def shutdown(cls):
        """서비스 종료 및 정리"""
        # 모든 활성 락 강제 해제
    
    @classmethod
    def get_manager(cls) -> DistributedLockManager:
        """락 매니저 인스턴스 반환"""
        # 컨텍스트 매니저 지원 락 매니저 반환
```

**동작 방식**:
- 111 gameserver 패턴으로 서비스 인스턴스 관리
- CacheService를 통한 Redis 분산락 구현
- 정적 클래스로 전역 락 서비스 제공

### **DistributedLockManager - 락 매니저**

```python
class DistributedLockManager:
    """분산락 매니저 (컨텍스트 매니저 지원)"""
    
    def __init__(self, lock_impl: IDistributedLock):
        self.lock_impl = lock_impl
        self.active_locks: Dict[str, str] = {}  # key -> token
    
    @asynccontextmanager
    async def acquire_lock(self, key: str, ttl: int = 30, timeout: int = 10):
        """컨텍스트 매니저로 분산락 사용"""
        # 자동 락 획득 및 해제
```

**동작 방식**:
- 컨텍스트 매니저로 자동 락 관리
- 활성 락 추적 및 자동 정리
- 예외 발생 시에도 락 해제 보장

### **CacheServiceDistributedLock - Redis 분산락 구현**

```python
class CacheServiceDistributedLock(IDistributedLock):
    """CacheService를 사용하는 Redis 분산락"""
    
    def __init__(self, cache_service):
        self.cache_service = cache_service
        self.lock_prefix = "lock:"
    
    async def acquire(self, key: str, ttl: int = 30, timeout: int = 10) -> Optional[str]:
        """락 획득 (SET key value EX ttl NX)"""
        # Redis SET 명령어로 원자적 락 획득
    
    async def release(self, key: str, token: str) -> bool:
        """락 해제 (Lua 스크립트로 토큰 검증)"""
        # 토큰 일치 시에만 락 해제
```

**동작 방식**:
- Redis SET 명령어로 원자적 락 획득
- Lua 스크립트로 토큰 기반 안전한 해제
- TTL 기반 자동 만료 처리

---

## 🌐 API 연동 방식

### **Lock 서비스 초기화**

```python
# main.py에서 CacheService 이후 초기화
if LockService.init(cache_service):
    Logger.info("LockService 초기화 완료")
    
    # 분산락 테스트
    test_token = await LockService.acquire("test_lock", ttl=5, timeout=3)
    if test_token:
        await LockService.release("test_lock", test_token)
```

### **CacheService 의존성**

```python
# lock_service.py
@classmethod
def init(cls, cache_service) -> bool:
    """분산락 서비스 초기화"""
    try:
        # Redis 분산락 구현체 생성 (CacheService 사용)
        cls._lock_impl = CacheServiceDistributedLock(cache_service)
        cls._lock_manager = DistributedLockManager(cls._lock_impl)
        cls._initialized = True
        return True
    except Exception as e:
        Logger.error(f"LockService 초기화 실패: {e}")
        return False
```

### **CacheService 설정 예시**

```json
{
  "cacheConfig": {
    "redis_host": "your_redis_host",
    "redis_port": 6379,
    "redis_db": 0,
    "max_connections": 10,
    "connection_timeout": 5
  }
}
```

**참고**: Lock 서비스는 CacheService를 통해 Redis에 접근하므로, Redis 설정은 CacheService 설정에 포함됩니다.

---

## 🔄 Lock 서비스 전체 흐름

### **1. 서비스 초기화**
```
1. LockService.init(cache_service) 호출
2. CacheService 인스턴스 검증
3. CacheServiceDistributedLock 생성
4. DistributedLockManager 생성
5. 초기화 완료 상태 설정
```

### **2. 락 획득 플로우**
```
1. LockService.acquire(key, ttl, timeout) 호출
2. Redis SET key value EX ttl NX 명령어 실행
3. 성공 시 UUID 토큰 반환, 실패 시 None 반환
4. 타임아웃까지 재시도 (0.1초 간격)
```

### **3. 락 해제 플로우**
```
1. LockService.release(key, token) 호출
2. Lua 스크립트로 토큰 일치 확인
3. 토큰 일치 시 락 삭제, 불일치 시 실패
4. 결과 반환 (성공/실패)
```

### **4. 컨텍스트 매니저 플로우**
```
1. async with lock_manager.acquire_lock(key) 진입
2. 자동으로 락 획득 시도
3. 락 획득 성공 시 코드 블록 실행
4. finally 블록에서 자동 락 해제
```

---

## 🔌 분산락 구현 상세

### **Redis 기반 락 획득**

```python
# SET key value EX ttl NX (존재하지 않을 때만 설정)
result = await client.set_string(
    lock_key, 
    token, 
    expire=ttl,
    nx=True  # Not eXists
)

if result:
    Logger.info(f"분산락 획득 성공: {key}, token: {token[:8]}...")
    return token
```

### **Lua 스크립트 기반 락 해제**

```python
# 토큰 확인 후 원자적 삭제
lua_script = """
if redis.call("GET", KEYS[1]) == ARGV[1] then
    return redis.call("DEL", KEYS[1])
else
    return 0
end
"""

result = await client.eval(lua_script, 1, full_key, token)
```

### **컨텍스트 매니저 사용법**

```python
# 자동 락 관리
async with LockService.get_manager().acquire_lock("scheduler:create_table", ttl=60):
    # 락이 보장된 코드 블록
    await create_daily_table()
    # 자동으로 락 해제
```

---

## 🔬 고급 기능 심층 분석: 분산락 패턴

LockService의 핵심은 **Redis 기반 분산락 패턴**을 통한 동시성 제어입니다.

### **1. 개요**
이 패턴은 **Redis의 SET 명령어**와 **Lua 스크립트**를 결합하여 분산 환경에서 안전한 락을 구현합니다. 전통적인 방식에서는 단일 서버의 메모리 기반 락을 사용하지만, 이 패턴은 **Redis의 원자성**과 **TTL 기반 자동 만료**를 활용합니다.

### **2. 핵심 아키텍처 및 데이터 플로우**

#### **2.1 Redis 기반 락 획득**
```python
async def acquire(self, key: str, ttl: int = 30, timeout: int = 10) -> Optional[str]:
    """락 획득"""
    lock_key = f"{self.lock_prefix}{key}"
    token = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        while time.time() - start_time < timeout:
            async with self.cache_service.get_client() as client:
                # SET key value EX ttl NX (존재하지 않을 때만 설정)
                result = await client.set_string(
                    lock_key, 
                    token, 
                    expire=ttl,
                    nx=True  # Not eXists
                )
                
                if result:
                    return token
            
            # 짧은 시간 대기 후 재시도
            await self._sleep(0.1)
        
        return None
```

#### **2.2 Lua 스크립트 기반 안전한 해제**
```python
async def release(self, key: str, token: str) -> bool:
    """락 해제"""
    lua_script = """
    if redis.call("GET", KEYS[1]) == ARGV[1] then
        return redis.call("DEL", KEYS[1])
    else
        return 0
    end
    """
    
    result = await client.eval(lua_script, 1, full_key, token)
    return result == 1
```

### **3. 실제 구현된 동작 과정**

#### **3.1 락 획득 과정**
```
1. UUID 토큰 생성
2. Redis SET 명령어로 원자적 락 설정
3. 성공 시 토큰 반환, 실패 시 재시도
4. 타임아웃까지 0.1초 간격으로 재시도
```

#### **3.2 락 해제 과정**
```
1. Lua 스크립트로 토큰 일치 확인
2. 토큰 일치 시에만 락 삭제
3. 토큰 불일치 시 해제 실패
4. 결과 반환 (성공/실패)
```

### **4. 성능 최적화 효과**

#### **4.1 원자성 보장**
```
Redis SET 명령어:
- NX 플래그로 존재하지 않을 때만 설정
- EX 플래그로 TTL 자동 설정
- 단일 명령어로 원자적 실행
```

#### **4.2 자동 만료 처리**
```
TTL 기반 관리:
- 락 획득 시 자동으로 만료시간 설정
- 서버 장애 시에도 자동 락 해제
- 메모리 누수 방지
```

### **5. 에러 처리 및 복구**

#### **5.1 재시도 로직**
```python
# 타임아웃까지 재시도
while time.time() - start_time < timeout:
    result = await client.set_string(lock_key, token, expire=ttl, nx=True)
    if result:
        return token
    
    # 짧은 시간 대기 후 재시도
    await self._sleep(0.1)
```

#### **5.2 강제 해제 메커니즘**
```python
async def force_release_all(self):
    """모든 활성 락 강제 해제 (종료 시 정리)"""
    for key, token in list(self.active_locks.items()):
        try:
            await self.lock_impl.release(key, token)
            Logger.info(f"강제 해제된 락: {key}")
        except Exception as e:
            Logger.error(f"락 강제 해제 실패: {key} - {e}")
    
    self.active_locks.clear()
```

### **6. 실제 사용 사례**

#### **6.1 스케줄러 작업에서의 활용**
```python
# base_server/service/scheduler/table_scheduler.py
async def create_daily_tables():
    # TableScheduler에서 LockService를 통한 중복 실행 방지
    # 실제로는 ScheduleJob 설정에서 lock_key="scheduler:create_daily_tables" 사용
    pass
```

#### **6.2 실제 프로젝트에서의 락 사용**
```python
# LockService를 통한 분산락 사용 예시
lock_key = "scheduler:create_daily_tables"
lock_token = await LockService.acquire(lock_key, ttl=1800, timeout=10)

if lock_token:
    try:
        # 보호된 작업 실행
        await perform_protected_operation()
    finally:
        await LockService.release(lock_key, lock_token)
```

### **7. 핵심 특징 및 장점**

#### **7.1 분산 환경 지원**
- **Redis 기반**: 여러 서버에서 동일한 락 공유
- **TTL 자동 만료**: 서버 장애 시에도 자동 복구
- **토큰 기반 보안**: 락 소유권 검증

#### **7.2 성능 최적화**
- **원자적 작업**: Redis 단일 명령어로 락 획득
- **비동기 처리**: asyncio 기반 동시성 지원
- **자동 정리**: 컨텍스트 매니저로 리소스 관리

#### **7.3 안정성 및 신뢰성**
- **재시도 로직**: 타임아웃까지 자동 재시도
- **강제 해제**: 서버 종료 시 모든 락 정리
- **예외 안전성**: finally 블록으로 락 해제 보장

이 패턴은 단순한 락 메커니즘을 넘어서 **분산 환경에서의 동시성 제어**, **자동 리소스 관리**, **고가용성 보장**을 제공하는 고도화된 분산락 시스템입니다.

---

### **의존성 설치**
```bash
# 프로젝트에 이미 포함된 Redis 클라이언트
# requirements.txt: redis==5.0.0

# Redis 서버는 별도로 설치 및 실행 필요
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Windows
# https://redis.io/docs/getting-started/installation/install-redis-on-windows/
```

### **Redis 서버 설정**
```bash
# Redis 서버 시작 (시스템에 따라 다름)

# Ubuntu/Debian
sudo systemctl start redis-server

# macOS
brew services start redis

# Windows
redis-server.exe

# Redis 연결 테스트
redis-cli ping  # PONG 응답 확인
```

---

## 📚 추가 리소스

- **Redis 문서**: https://redis.io/documentation
- **Redis SET 명령어**: https://redis.io/commands/set
- **Redis Lua 스크립트**: https://redis.io/docs/manual/programmability/

---
