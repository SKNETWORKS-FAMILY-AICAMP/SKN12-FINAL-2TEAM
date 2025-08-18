# AI Trading Platform — Outbox Service

> **개요**: SKN12-FINAL-2TEAM의 AI 트레이딩 플랫폼 백엔드 Outbox 서비스입니다. 트랜잭션 일관성을 보장하는 이벤트 발행 시스템으로, 샤딩된 데이터베이스 환경에서 안전한 이벤트 처리를 담당합니다. Outbox 패턴을 통해 비즈니스 로직과 이벤트 발행의 원자성을 보장합니다.

---

## 🏗️ 프로젝트 구조

### 디렉토리 구조
```
outbox/
├── __init__.py                        # 패키지 초기화
├── outbox_pattern.py                  # 핵심 Outbox 패턴 구현
└── universal_outbox_consumer.py       # Universal Outbox 컨슈머
```

---

## 🔧 핵심 기능

### 1. **Outbox 패턴 (OutboxPattern)**
- **트랜잭션 일관성**: 비즈니스 로직과 이벤트 발행의 원자성 보장
- **샤딩 지원**: 분산 데이터베이스 환경에서 이벤트 저장 및 조회
- **이벤트 상태 관리**: PENDING, PUBLISHED, FAILED, RETRY 상태 추적
- **재시도 메커니즘**: 최대 재시도 횟수 설정 및 자동 재시도

### 2. **이벤트 발행 시스템**
- **이벤트 저장소**: `OutboxRepository`를 통한 샤드별 이벤트 관리
- **이벤트 발행자**: `OutboxEventPublisher`를 통한 핸들러 기반 이벤트 처리
- **트랜잭션 통합**: `OutboxService`를 통한 비즈니스 로직과 이벤트 발행 통합

### 3. **Universal Outbox 컨슈머**
- **도메인별 처리**: CHAT, PORTFOLIO, MARKET, NOTIFICATION, SIGNAL 도메인 지원
- **분산락 기반**: `LockService`를 통한 중복 처리 방지
- **배치 처리**: 샤드별 배치 단위로 이벤트 처리
- **자동 정리**: 오래된 이벤트 자동 정리 및 스케줄링

---

## 📚 사용된 라이브러리

### **백엔드 & 인프라**
- **asyncio**: 비동기 프로그래밍 및 태스크 관리
- **uuid**: 고유 식별자 생성
- **json**: 이벤트 데이터 직렬화/역직렬화
- **dataclasses**: 데이터 클래스 정의

### **개발 도구**
- **typing**: 타입 힌트 및 타입 안전성
- **enum**: 이벤트 상태 및 도메인 열거형
- **service.core.logger.Logger**: 구조화된 로깅 시스템

### **외부 의존성**
- **service.service_container.ServiceContainer**: 서비스 컨테이너
- **service.lock.LockService**: 분산락 서비스
- **service.scheduler.SchedulerService**: 스케줄러 서비스
- **service.queue.QueueService**: 큐 서비스

---

## 🪝 핵심 클래스 및 메서드

### **OutboxEvent - 이벤트 데이터 클래스**

```python
@dataclass
class OutboxEvent:
    """아웃박스 이벤트"""
    id: str                              # 고유 식별자
    event_type: str                      # 이벤트 타입
    aggregate_id: str                    # 집계 ID
    aggregate_type: str                  # 집계 타입
    event_data: Dict[str, Any]           # 이벤트 데이터
    status: OutboxEventStatus            # 이벤트 상태
    retry_count: int = 0                 # 재시도 횟수
    max_retries: int = 3                 # 최대 재시도
    created_at: Optional[datetime]       # 생성 시간
    updated_at: Optional[datetime]       # 수정 시간
    published_at: Optional[datetime]     # 발행 시간
```

**동작 방식**:
- 이벤트의 모든 메타데이터와 상태를 포함
- 재시도 로직을 위한 카운터 관리
- 생성/수정/발행 시간 추적

### **OutboxRepository - 이벤트 저장소**

```python
class OutboxRepository:
    """아웃박스 이벤트 저장소 (샤딩 지원)"""
    
    async def save_event(self, event: OutboxEvent, shard_id: Optional[int] = None) -> bool:
        """이벤트 저장 (적절한 샤드에)"""
        # 샤드 ID가 지정되면 해당 샤드에, 없으면 글로벌 DB에 저장
    
    async def get_pending_events_from_shard(self, shard_id: int, limit: int = 100) -> List[OutboxEvent]:
        """특정 샤드에서 발행 대기 중인 이벤트 조회"""
    
    async def get_all_pending_events(self, limit_per_shard: int = 100) -> Dict[int, List[OutboxEvent]]:
        """모든 샤드에서 대기 중인 이벤트 조회"""
    
    async def update_event_status(self, event_id: str, status: OutboxEventStatus, 
                                retry_count: Optional[int] = None) -> bool:
        """이벤트 상태 업데이트"""
    
    async def cleanup_old_events(self, days: int = 7) -> int:
        """오래된 이벤트 정리"""
```

**동작 방식**:
- 샤딩된 데이터베이스 환경에서 이벤트 저장 및 조회
- 샤드별 이벤트 관리 및 글로벌 이벤트 통합
- 자동 정리 및 상태 업데이트

### **OutboxEventPublisher - 이벤트 발행자**

```python
class OutboxEventPublisher:
    """아웃박스 이벤트 발행자"""
    
    def register_handler(self, event_type: str, handler):
        """이벤트 핸들러 등록"""
    
    async def publish_pending_events(self) -> Dict[str, int]:
        """대기 중인 이벤트 발행"""
        # 통계 반환: processed, published, failed, retried
    
    async def _publish_single_event(self, event: OutboxEvent) -> bool:
        """단일 이벤트 발행"""
    
    async def _handle_publish_failure(self, event: OutboxEvent, stats: Dict[str, int]):
        """발행 실패 처리"""
```

**동작 방식**:
- 등록된 핸들러를 통한 이벤트 타입별 처리
- 비동기/동기 핸들러 모두 지원
- 실패 시 재시도 로직 및 통계 관리

### **OutboxService - 통합 서비스**

```python
class OutboxService:
    """아웃박스 패턴 서비스 (트랜잭션 일관성 보장)"""
    
    async def publish_event_in_transaction(self, event_type: str, aggregate_id: str, 
                                         aggregate_type: str, event_data: Dict[str, Any],
                                         business_operation=None) -> bool:
        """비즈니스 로직과 이벤트 발행을 원자적으로 처리"""
    
    def register_event_handler(self, event_type: str, handler):
        """이벤트 핸들러 등록"""
    
    async def process_outbox_events(self) -> Dict[str, int]:
        """아웃박스 이벤트 처리"""
    
    async def cleanup_old_events(self, days: int = 7) -> int:
        """오래된 이벤트 정리"""
```

**동작 방식**:
- 트랜잭션 내에서 비즈니스 로직과 이벤트 발행 통합
- 원자성 보장을 위한 트랜잭션 관리
- 이벤트 핸들러 등록 및 처리

### **UniversalOutboxConsumer - 범용 컨슈머**

```python
class UniversalOutboxConsumer:
    """Universal Outbox 컨슈머 - 분산 환경용"""
    
    @classmethod
    async def init(cls):
        """컨슈머 초기화"""
        # 기본 이벤트 핸들러 등록
        # 각 도메인별 컨슈머 태스크 시작
        # 정리 작업 스케줄러 등록
    
    @classmethod
    def register_handler(cls, domain: EventDomain, event_type: str, handler: Callable):
        """이벤트 핸들러 등록"""
    
    @classmethod
    async def _consume_domain_events(cls, domain: EventDomain):
        """도메인별 이벤트 컨슘"""
        # 분산 락으로 중복 처리 방지
        # 활성 샤드에서 pending 이벤트 조회 및 처리
    
    @classmethod
    async def _process_pending_events(cls, domain: str) -> int:
        """도메인별 pending 이벤트 처리"""
        # SQL 프로시저를 통한 샤드별 이벤트 조회
        # 배치 단위로 이벤트 처리
```

**동작 방식**:
- 도메인별 독립적인 이벤트 컨슈머 태스크
- 분산락을 통한 중복 처리 방지
- SQL 프로시저 기반의 효율적인 이벤트 조회

---

## 🌐 API 연동 방식

### **Outbox 서비스 초기화**

```python
# main.py에서 DatabaseService 이후 초기화
from service.outbox.outbox_pattern import OutboxService

# DatabaseService 초기화 후
outbox_service = OutboxService(db_service)

# 이벤트 핸들러 등록
outbox_service.register_event_handler("user_registered", handle_user_registered)
outbox_service.register_event_handler("order_created", handle_order_created)
```

### **Universal Outbox 컨슈머 초기화**

```python
# main.py에서 서비스 초기화 후
from service.outbox.universal_outbox_consumer import UniversalOutboxConsumer

# 모든 서비스 초기화 완료 후
await UniversalOutboxConsumer.init()
```

### **이벤트 발행 및 처리 통합**

```python
# 비즈니스 로직과 이벤트 발행을 원자적으로 처리
success = await outbox_service.publish_event_in_transaction(
    event_type="user_registered",
    aggregate_id=user_id,
    aggregate_type="user",
    event_data={"email": "user@example.com", "name": "John Doe"},
    business_operation=create_user_account  # 코루틴 함수
)

if success:
    Logger.info("사용자 계정 생성 및 이벤트 발행 완료")
else:
    Logger.error("사용자 계정 생성 또는 이벤트 발행 실패")
```

---

## 🔄 Outbox 서비스 전체 흐름

### **1. 이벤트 발행 플로우**
```
1. 비즈니스 로직 실행 (트랜잭션 내)
2. OutboxEvent 생성 및 메타데이터 설정
3. 적절한 샤드에 이벤트 저장
4. 트랜잭션 커밋 (자동)
5. 이벤트 발행 대기 상태
```

### **2. 이벤트 처리 플로우**
```
1. UniversalOutboxConsumer가 각 도메인별로 폴링
2. 분산락으로 중복 처리 방지
3. SQL 프로시저를 통한 샤드별 pending 이벤트 조회
4. 등록된 핸들러로 이벤트 처리
5. 성공 시 PUBLISHED, 실패 시 RETRY/FAILED 상태 업데이트
```

### **3. 재시도 및 정리 플로우**
```
1. 실패한 이벤트는 retry_count 증가
2. max_retries 도달 시 FAILED 상태로 변경
3. 스케줄러를 통한 주기적 정리 작업
4. 오래된 published 이벤트 자동 삭제
```

---

## 🔌 Outbox 패턴 구현 상세

### **트랜잭션 일관성 보장**

```python
async def publish_event_in_transaction(self, event_type: str, aggregate_id: str, 
                                     aggregate_type: str, event_data: Dict[str, Any],
                                     business_operation=None) -> bool:
    """비즈니스 로직과 이벤트 발행을 원자적으로 처리"""
    try:
        # 트랜잭션 시작
        async with self.db_service.get_transaction() as transaction:
            
            # 1. 비즈니스 로직 실행 (있는 경우)
            if business_operation:
                if asyncio.iscoroutinefunction(business_operation):
                    await business_operation(transaction)
                else:
                    business_operation(transaction)
            
            # 2. 아웃박스 이벤트 저장
            event = OutboxEvent(
                id=str(uuid.uuid4()),
                event_type=event_type,
                aggregate_id=aggregate_id,
                aggregate_type=aggregate_type,
                event_data=event_data,
                created_at=datetime.now()
            )
            
            success = await self.repository.save_event(event)
            
            if not success:
                raise Exception("아웃박스 이벤트 저장 실패")
            
            # 트랜잭션 커밋 (자동)
            Logger.info(f"트랜잭션 완료 - 이벤트 저장: {event.id}")
            return True
            
    except Exception as e:
        Logger.error(f"트랜잭션 실패: {e}")
        return False
```

### **샤딩 지원 이벤트 저장**

```python
async def save_event(self, event: OutboxEvent, shard_id: Optional[int] = None) -> bool:
    """이벤트 저장 (적절한 샤드에)"""
    try:
        query = """
            INSERT INTO outbox_events 
            (id, event_type, aggregate_id, aggregate_type, event_data, status, retry_count, max_retries, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        values = (
            event.id,
            event.event_type,
            event.aggregate_id,
            event.aggregate_type,
            json.dumps(event.event_data),
            event.status.value,
            event.retry_count,
            event.max_retries,
            event.created_at or datetime.now()
        )
        
        # 샤드 ID가 지정되면 해당 샤드에, 없으면 글로벌 DB에 저장
        if shard_id:
            await self.db_service.call_shard_procedure_update(shard_id, query, values)
        else:
            await self.db_service.call_global_procedure_update(query, values)
            
        Logger.info(f"아웃박스 이벤트 저장: {event.id} (shard: {shard_id})")
        return True
        
    except Exception as e:
        Logger.error(f"아웃박스 이벤트 저장 실패: {event.id} - {e}")
        return False
```

### **분산락 기반 중복 처리 방지**

```python
async def _consume_domain_events(cls, domain: EventDomain):
    """도메인별 이벤트 컨슘"""
    domain_name = domain.value
    
    while cls._initialized:
        try:
            # 분산 락으로 중복 처리 방지
            lock_key = f"outbox_consumer:{domain_name}"
            lock_token = await LockService.acquire(lock_key, ttl=30, timeout=1)
            
            if not lock_token:
                # 다른 인스턴스에서 처리 중
                await asyncio.sleep(cls.POLL_INTERVAL)
                continue
            
            try:
                # 활성 샤드에서 pending 이벤트 조회
                processed_count = await cls._process_pending_events(domain_name)
                
                if processed_count > 0:
                    Logger.info(f"✅ {domain_name} 도메인: {processed_count}개 이벤트 처리 완료")
                
            finally:
                await LockService.release(lock_key, lock_token)
            
            # 다음 폴링까지 대기
            await asyncio.sleep(cls.POLL_INTERVAL)
            
        except asyncio.CancelledError:
            Logger.info(f"{domain_name} 도메인 컨슈머 중지")
            break
        except Exception as e:
            Logger.error(f"{domain_name} 도메인 컨슈머 오류: {e}")
            await asyncio.sleep(10)  # 오류 시 10초 대기
```

---

## 🔬 고급 기능 심층 분석: Outbox 패턴 아키텍처

Outbox 서비스의 핵심은 **트랜잭션 일관성을 보장하는 이벤트 발행 패턴**입니다.

### **1. 개요**
이 패턴은 **데이터베이스 트랜잭션 내에서 비즈니스 로직과 이벤트 발행을 원자적으로 처리**합니다. 전통적인 방식에서는 비즈니스 로직과 이벤트 발행이 분리되어 있어 일관성 문제가 발생할 수 있지만, 이 패턴은 **트랜잭션의 원자성**을 활용하여 문제를 해결합니다.

### **2. 핵심 아키텍처 및 데이터 플로우**

#### **2.1 트랜잭션 통합 이벤트 발행**
```python
async def publish_event_in_transaction(self, event_type: str, aggregate_id: str, 
                                     aggregate_type: str, event_data: Dict[str, Any],
                                     business_operation=None) -> bool:
    """비즈니스 로직과 이벤트 발행을 원자적으로 처리"""
    try:
        # 트랜잭션 시작
        async with self.db_service.get_transaction() as transaction:
            
            # 1. 비즈니스 로직 실행 (있는 경우)
            if business_operation:
                if asyncio.iscoroutinefunction(business_operation):
                    await business_operation(transaction)
                else:
                    business_operation(transaction)
            
            # 2. 아웃박스 이벤트 저장
            event = OutboxEvent(
                id=str(uuid.uuid4()),
                event_type=event_type,
                aggregate_id=aggregate_id,
                aggregate_type=aggregate_type,
                event_data=event_data,
                created_at=datetime.now()
            )
            
            success = await self.repository.save_event(event)
            
            if not success:
                raise Exception("아웃박스 이벤트 저장 실패")
            
            # 트랜잭션 커밋 (자동)
            Logger.info(f"트랜잭션 완료 - 이벤트 저장: {event.id}")
            return True
            
    except Exception as e:
        Logger.error(f"트랜잭션 실패: {e}")
        return False
```

#### **2.2 샤딩 지원 이벤트 관리**
```python
async def get_all_pending_events(self, limit_per_shard: int = 100) -> Dict[int, List[OutboxEvent]]:
    """모든 샤드에서 대기 중인 이벤트 조회"""
    all_events = {}
    
    try:
        # 활성 샤드 목록 조회
        active_shards = await self.db_service.get_active_shard_ids()
        
        for shard_id in active_shards:
            events = await self.get_pending_events_from_shard(shard_id, limit_per_shard)
            if events:
                all_events[shard_id] = events
        
        return all_events
        
    except Exception as e:
        Logger.error(f"전체 샤드 이벤트 조회 실패: {e}")
        return {}
```

### **3. 실제 구현된 동작 과정**

#### **3.1 이벤트 발행 과정**
```
1. 비즈니스 로직 실행 (트랜잭션 내)
2. OutboxEvent 객체 생성 및 메타데이터 설정
3. 적절한 샤드에 이벤트 저장
4. 트랜잭션 커밋 (자동)
5. 이벤트 발행 대기 상태로 설정
```

#### **3.2 이벤트 처리 과정**
```
1. UniversalOutboxConsumer가 각 도메인별로 폴링
2. 분산락으로 중복 처리 방지
3. SQL 프로시저를 통한 샤드별 pending 이벤트 조회
4. 등록된 핸들러로 이벤트 처리
5. 성공 시 PUBLISHED, 실패 시 RETRY/FAILED 상태 업데이트
```

### **4. 성능 최적화 효과**

#### **4.1 배치 처리**
```
샤드별 배치 처리:
- 각 샤드에서 limit_per_shard 단위로 이벤트 조회
- 메모리 효율적인 이벤트 처리
- 샤드별 독립적인 처리로 병렬성 향상
```

#### **4.2 분산락 기반 중복 방지**
```
LockService 활용:
- 도메인별 독립적인 락 키 사용
- TTL 기반 자동 락 해제
- 여러 인스턴스에서 동시 실행 시 중복 처리 방지
```

### **5. 에러 처리 및 복구**

#### **5.1 재시도 로직**
```python
async def _handle_publish_failure(self, event: OutboxEvent, stats: Dict[str, int]):
    """발행 실패 처리"""
    event.retry_count += 1
    
    if event.retry_count >= event.max_retries:
        # 최대 재시도 횟수 초과
        await self.repository.update_event_status(
            event.id, 
            OutboxEventStatus.FAILED, 
            event.retry_count
        )
        stats["failed"] += 1
        Logger.error(f"이벤트 발행 최종 실패: {event.id} (재시도 {event.retry_count}회)")
    else:
        # 재시도 대기 상태로 변경
        await self.repository.update_event_status(
            event.id, 
            OutboxEventStatus.RETRY, 
            event.retry_count
        )
        stats["retried"] += 1
        Logger.warn(f"이벤트 발행 실패 - 재시도 예정: {event.id} ({event.retry_count}/{event.max_retries})")
```

#### **5.2 자동 정리 메커니즘**
```python
async def cleanup_old_events(self, days: int = 7) -> int:
    """오래된 이벤트 정리"""
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        query = """
            DELETE FROM outbox_events 
            WHERE status = 'published' AND published_at < %s
        """
        
        result = await self.db_service.call_global_procedure_update(query, (cutoff_date,))
        
        Logger.info(f"오래된 아웃박스 이벤트 정리 완료: {days}일 이전")
        return result if result else 0
        
    except Exception as e:
        Logger.error(f"오래된 이벤트 정리 실패: {e}")
        return 0
```

### **6. 실제 사용 사례**

#### **6.1 사용자 등록 이벤트**
```python
# 사용자 계정 생성과 이벤트 발행을 원자적으로 처리
success = await outbox_service.publish_event_in_transaction(
    event_type="user_registered",
    aggregate_id=user_id,
    aggregate_type="user",
    event_data={
        "email": "user@example.com",
        "name": "John Doe",
        "registration_date": datetime.now().isoformat()
    },
    business_operation=create_user_account
)

if success:
    Logger.info("사용자 계정 생성 및 이벤트 발행 완료")
else:
    Logger.error("사용자 계정 생성 또는 이벤트 발행 실패")
```

#### **6.2 주문 생성 이벤트**
```python
# 주문 생성과 이벤트 발행을 원자적으로 처리
success = await outbox_service.publish_event_in_transaction(
    event_type="order_created",
    aggregate_id=order_id,
    aggregate_type="order",
    event_data={
        "user_id": user_id,
        "amount": 100.00,
        "currency": "USD",
        "items": ["AAPL", "GOOGL"]
    },
    business_operation=create_order
)
```

### **7. 핵심 특징 및 장점**

#### **7.1 트랜잭션 일관성**
- **원자성 보장**: 비즈니스 로직과 이벤트 발행의 동시 성공/실패
- **데이터 무결성**: 트랜잭션 롤백 시 이벤트도 함께 롤백
- **ACID 속성**: 데이터베이스 트랜잭션의 모든 속성 활용

#### **7.2 분산 환경 지원**
- **샤딩 지원**: 샤드별 이벤트 저장 및 조회
- **분산락**: 여러 인스턴스에서의 중복 처리 방지
- **도메인별 분리**: 독립적인 이벤트 처리 도메인

#### **7.3 안정성 및 신뢰성**
- **재시도 로직**: 실패한 이벤트의 자동 재시도
- **상태 추적**: 이벤트의 전체 생명주기 추적
- **자동 정리**: 오래된 이벤트의 자동 정리

이 패턴은 단순한 이벤트 발행을 넘어서 **트랜잭션 일관성**, **분산 환경 지원**, **안정적인 이벤트 처리**를 제공하는 고도화된 이벤트 시스템입니다.

---