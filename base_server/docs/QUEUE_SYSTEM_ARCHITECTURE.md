# 큐 시스템 아키텍처 가이드

본 문서는 base_server의 메시지큐와 이벤트큐 시스템의 전체 아키텍처를 설명합니다.

## 목차
1. [개요](#1-개요)
2. [시스템 구조](#2-시스템-구조)
3. [메시지큐 시스템](#3-메시지큐-시스템)
4. [이벤트큐 시스템](#4-이벤트큐-시스템)
5. [스케줄러 시스템](#5-스케줄러-시스템)
6. [아웃박스 패턴](#6-아웃박스-패턴)
7. [처리 흐름](#7-처리-흐름)
8. [설정 및 사용법](#8-설정-및-사용법)
9. [모니터링](#9-모니터링)
10. [트러블슈팅](#10-트러블슈팅)

---

## 1. 개요

### 1.1 시스템 목적
- **메시지큐**: 비동기 작업 처리 및 시스템 간 통신
- **이벤트큐**: 이벤트 기반 아키텍처 구현 (Pub/Sub)
- **스케줄러**: 백그라운드 작업 및 시스템 관리
- **아웃박스 패턴**: 데이터 일관성 보장

### 1.2 기술 스택
- **Redis**: 메시지/이벤트 저장소
- **MySQL**: 아웃박스 이벤트 영속성
- **AsyncIO**: 비동기 처리
- **분산 락**: 중복 처리 방지

---

## 2. 시스템 구조

### 2.1 전체 아키텍처
```
┌─────────────────────────────────────────────────────────────────┐
│                        QueueService                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ MessageQueue    │  │   EventQueue    │  │   Scheduler     │ │
│  │   Manager       │  │    Manager      │  │    Service      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Redis                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Message Queues  │  │   Event Pub/Sub │  │ Distributed Lock│ │
│  │ - Priority      │  │ - Subscriptions │  │ - Job Locks     │ │
│  │ - Delayed       │  │ - Event History │  │ - Process Locks │ │
│  │ - DLQ          │  │ - Subscriber Q  │  │                 │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        MySQL                                    │
│  ┌─────────────────┐  ┌─────────────────┐                      │
│  │ Outbox Events   │  │ Business Data   │                      │
│  │ - Transactional │  │ - User Data     │                      │
│  │ - Event Store   │  │ - Portfolio     │                      │
│  └─────────────────┘  └─────────────────┘                      │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 컴포넌트별 역할

| 컴포넌트 | 역할 | 처리 방식 |
|---------|------|----------|
| **MessageConsumer** | 메시지 처리 | 1초 폴링 |
| **EventSubscriber** | 이벤트 처리 | 1초 폴링 |
| **Scheduler** | 백그라운드 작업 | 시간 기반 |
| **OutboxService** | 트랜잭션 이벤트 | DB 연동 |

---

## 3. 메시지큐 시스템

### 3.1 파일 위치
- **메인 구현**: `base_server/service/queue/message_queue.py`
- **인터페이스**: `IMessageQueue`, `RedisCacheMessageQueue`
- **소비자**: `MessageConsumer`
- **관리자**: `MessageQueueManager`

### 3.2 메시지 구조
```python
@dataclass
class QueueMessage:
    id: str                              # 메시지 고유 ID
    queue_name: str                      # 큐 이름
    payload: Dict[str, Any]              # 메시지 내용
    message_type: str                    # 메시지 타입
    priority: MessagePriority            # 우선순위 (LOW=1, NORMAL=2, HIGH=3, CRITICAL=4)
    status: MessageStatus                # 상태 (PENDING, PROCESSING, COMPLETED, FAILED)
    retry_count: int = 0                 # 재시도 횟수
    max_retries: int = 3                 # 최대 재시도
    created_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None  # 지연 실행 시간
    partition_key: Optional[str] = None      # 순서 보장용 파티션 키
```

### 3.3 Redis 저장 구조
```redis
# 메시지 데이터 저장
HSET mq:message:{message_id} id "msg123" payload "{...}" priority "3"

# 우선순위별 큐 (LIST)
LPUSH mq:priority:{queue_name}:4 "msg456"  # CRITICAL
LPUSH mq:priority:{queue_name}:3 "msg123"  # HIGH
LPUSH mq:priority:{queue_name}:2 "msg789"  # NORMAL
LPUSH mq:priority:{queue_name}:1 "msg101"  # LOW

# 지연 메시지 (SORTED SET)
ZADD mq:delayed:messages 1640995200 "msg555"  # timestamp를 score로 사용

# 처리 중인 메시지 (HASH)
HSET mq:processing:{queue_name}:{message_id} consumer_id "worker1" started_at "2024-01-01T12:00:00"

# 실패한 메시지 DLQ (LIST)
LPUSH mq:dlq:{queue_name} "{\"message_id\":\"msg999\",\"failed_at\":\"...\"}"
```

### 3.4 메시지 처리 흐름
```python
# 1. 메시지 소비자 시작
async def start(self):
    self.running = True
    self.task = asyncio.create_task(self._consume_loop())

# 2. 메시지 소비 루프 (1초 폴링)
async def _consume_loop(self):
    while self.running:
        try:
            # 우선순위 순서대로 메시지 가져오기
            message = await self.message_queue.dequeue(self.queue_name, self.consumer_id)
            
            if message:
                success = await self.handler(message)  # 메시지 처리
                if success:
                    await self.message_queue.ack(message, self.consumer_id)
                else:
                    await self.message_queue.nack(message, self.consumer_id)
            else:
                await asyncio.sleep(1)  # 메시지 없으면 1초 대기
                
        except Exception as e:
            Logger.error(f"메시지 소비 루프 오류: {e}")
            await asyncio.sleep(5)

# 3. 메시지 처리 상태 관리
async def dequeue(self, queue_name: str, consumer_id: str) -> Optional[QueueMessage]:
    # 우선순위 순서대로 확인 (CRITICAL=4, HIGH=3, NORMAL=2, LOW=1)
    for priority in [4, 3, 2, 1]:
        priority_queue_key = f"mq:priority:{queue_name}:{priority}"
        message_id = await client.list_pop_left(priority_queue_key)
        
        if message_id:
            # 처리 중 상태로 이동
            processing_key = f"mq:processing:{queue_name}:{message_id}"
            await client.set_hash_all(processing_key, {
                "consumer_id": consumer_id,
                "started_at": datetime.now().isoformat()
            })
            return message
    
    return None
```

### 3.5 메시지 사용 예제
```python
# 메시지 발송
await queue_service.send_message(
    queue_name="user_notifications",
    payload={"user_id": "123", "message": "Welcome!"},
    message_type="notification",
    priority=MessagePriority.HIGH
)

# 지연 메시지 발송
await queue_service.send_message(
    queue_name="scheduled_tasks",
    payload={"task": "cleanup"},
    message_type="maintenance",
    scheduled_at=datetime.now() + timedelta(hours=1)
)

# 메시지 소비자 등록
def message_handler(message: QueueMessage) -> bool:
    try:
        # 메시지 처리 로직
        Logger.info(f"Processing: {message.payload}")
        return True
    except Exception as e:
        Logger.error(f"Handler error: {e}")
        return False

await queue_service.register_message_consumer(
    queue_name="user_notifications",
    consumer_id="notification_worker_1",
    handler=message_handler
)
```

---

## 4. 이벤트큐 시스템

### 4.1 파일 위치
- **메인 구현**: `base_server/service/queue/event_queue.py`
- **인터페이스**: `IEventQueue`, `RedisCacheEventQueue`
- **관리자**: `EventQueueManager`

### 4.2 이벤트 구조
```python
@dataclass
class Event:
    id: str                              # 이벤트 고유 ID
    event_type: EventType                # 이벤트 타입 (enum)
    source: str                          # 이벤트 발생 소스
    data: Dict[str, Any]                 # 이벤트 데이터
    timestamp: datetime                  # 발생 시간
    correlation_id: Optional[str] = None # 추적용 ID
    version: str = "1.0"                # 이벤트 버전
    metadata: Optional[Dict[str, Any]] = None

class EventType(Enum):
    # 계정 관련
    ACCOUNT_CREATED = "account.created"
    ACCOUNT_UPDATED = "account.updated"
    ACCOUNT_DELETED = "account.deleted"
    
    # 포트폴리오 관련
    PORTFOLIO_CREATED = "portfolio.created"
    PORTFOLIO_UPDATED = "portfolio.updated"
    TRADE_EXECUTED = "trade.executed"
    
    # 시장 데이터 관련
    MARKET_DATA_UPDATED = "market.data.updated"
    PRICE_ALERT = "price.alert"
    
    # 시스템 관련
    SYSTEM_MAINTENANCE = "system.maintenance"
    SYSTEM_ERROR = "system.error"
```

### 4.3 구독 구조
```python
@dataclass
class Subscription:
    id: str                              # 구독 고유 ID
    subscriber_id: str                   # 구독자 ID
    event_types: Set[EventType]          # 구독할 이벤트 타입들
    callback: Callable[[Event], bool]   # 이벤트 처리 콜백
    filter_conditions: Optional[Dict[str, Any]] = None
    active: bool = True
```

### 4.4 Redis 저장 구조
```redis
# 이벤트 스트림 (각 이벤트 타입별)
LPUSH eq:stream:account.created "{\"event\": {...}, \"timestamp\": \"...\"}"
LPUSH eq:stream:portfolio.updated "{\"event\": {...}, \"timestamp\": \"...\"}"

# 구독자별 이벤트 큐
LPUSH eq:subscriber:user_service:account.created "{\"event\": {...}}"
LPUSH eq:subscriber:notification_service:account.created "{\"event\": {...}}"

# 이벤트 히스토리 (제한된 개수)
LPUSH eq:history:account.created "{\"event\": {...}}"
LTRIM eq:history:account.created 0 999  # 최근 1000개만 유지

# 구독 정보
HSET eq:subscriptions sub123 "{\"subscriber_id\": \"user_service\", \"event_types\": [...]}"
```

### 4.5 이벤트 처리 흐름
```python
# 1. 이벤트 발행
async def publish(self, event: Event) -> bool:
    # 이벤트 스트림에 추가
    stream_key = f"eq:stream:{event.event_type.value}"
    await client.list_push_right(stream_key, json.dumps(event_payload))
    
    # 구독자별 큐에 복사
    for subscription in self.subscriptions.values():
        if event.event_type in subscription.event_types:
            subscriber_queue_key = f"eq:subscriber:{subscription.subscriber_id}"
            await client.list_push_right(subscriber_queue_key, json.dumps(event_payload))
    
    # 히스토리 저장
    history_key = f"eq:history:{event.event_type.value}"
    await client.list_push_right(history_key, json.dumps(event_payload))
    await client.list_trim(history_key, 0, 999)  # 최근 1000개만 유지

# 2. 이벤트 구독 및 처리 루프
async def _process_subscriber_events(self, subscription: Subscription):
    subscriber_queue_key = f"eq:subscriber:{subscription.subscriber_id}"
    
    while subscription.active:
        try:
            # 구독자 큐에서 이벤트 가져오기
            event_data = await client.list_pop_left(subscriber_queue_key)
            
            if not event_data:
                await asyncio.sleep(1)  # 이벤트 없으면 1초 대기
                continue
            
            # 이벤트 객체 재구성
            event_payload = json.loads(event_data)
            event = Event(...)
            
            # 콜백 실행
            success = await subscription.callback(event)
            
        except Exception as e:
            Logger.error(f"구독자 이벤트 처리 오류: {e}")
            await asyncio.sleep(5)
```

### 4.6 이벤트 사용 예제
```python
# 이벤트 발행
await queue_service.publish_event(
    event_type=EventType.ACCOUNT_CREATED,
    source="account_service",
    data={"user_id": "123", "email": "user@example.com"},
    correlation_id="req-456"
)

# 이벤트 구독
def event_handler(event: Event) -> bool:
    try:
        if event.event_type == EventType.ACCOUNT_CREATED:
            # 계정 생성 이벤트 처리
            user_id = event.data["user_id"]
            Logger.info(f"New account created: {user_id}")
        return True
    except Exception as e:
        Logger.error(f"Event handler error: {e}")
        return False

await queue_service.subscribe_events(
    subscriber_id="notification_service",
    event_types=[EventType.ACCOUNT_CREATED, EventType.ACCOUNT_UPDATED],
    callback=event_handler
)
```

---

## 5. 스케줄러 시스템

### 5.1 파일 위치
- **스케줄러 서비스**: `base_server/service/scheduler/scheduler_service.py`
- **베이스 스케줄러**: `base_server/service/scheduler/base_scheduler.py`
- **큐 스케줄러 작업**: `base_server/service/queue/queue_service.py` (lines 175-218)

### 5.2 스케줄러 역할
스케줄러는 **큐 시스템의 백그라운드 관리 작업**을 담당합니다. 메시지/이벤트 처리와는 완전히 분리된 별도의 시스템입니다.

### 5.3 스케줄러 작업 종류

#### 5.3.1 아웃박스 이벤트 처리 (1분마다)
```python
async def _process_outbox_events_job(self):
    """DB에 저장된 아웃박스 이벤트를 큐로 발행"""
    try:
        # 아웃박스 테이블에서 미처리 이벤트 조회
        stats = await self.outbox_service.process_outbox_events()
        
        if stats["processed"] > 0:
            self.stats["outbox_events_processed"] += stats["processed"]
            Logger.info(f"아웃박스 이벤트 처리 완료: {stats}")
            
    except Exception as e:
        Logger.error(f"아웃박스 이벤트 처리 작업 실패: {e}")
```

#### 5.3.2 큐 상태 모니터링 (5분마다)
```python
async def _monitor_queues_job(self):
    """큐 통계 수집 및 모니터링"""
    try:
        # 메시지큐 통계
        queue_stats = await self.message_queue_manager.message_queue.get_queue_stats("default")
        Logger.info(f"메시지큐 상태: {queue_stats}")
        
        # 이벤트큐 통계
        event_stats = await self.event_queue_manager.get_stats()
        Logger.info(f"이벤트큐 상태: {event_stats}")
        
        # 전체 서비스 통계
        Logger.info(f"QueueService 통계: {self.stats}")
        
    except Exception as e:
        Logger.error(f"큐 모니터링 작업 실패: {e}")
```

#### 5.3.3 큐 정리 작업 (1시간마다)
```python
async def _cleanup_queues_job(self):
    """오래된 메시지/이벤트 정리"""
    try:
        # 아웃박스 이벤트 정리 (7일 이전)
        cleaned_events = await self.outbox_service.cleanup_old_events(7)
        
        if cleaned_events > 0:
            Logger.info(f"오래된 아웃박스 이벤트 정리: {cleaned_events}개")
            
    except Exception as e:
        Logger.error(f"큐 정리 작업 실패: {e}")
```

#### 5.3.4 지연 메시지 처리 (10초마다)
```python
async def _start_delayed_message_processor_with_check(self):
    """scheduled_at 시간이 된 지연 메시지를 큐로 이동"""
    async def process_delayed_with_cache_check():
        while True:
            try:
                # Redis 연결 상태 확인
                cache_service = CacheService.get_instance()
                if not cache_service.is_initialized():
                    await asyncio.sleep(30)
                    continue
                
                # 지연 메시지 처리
                await self.message_queue_manager.message_queue.process_delayed_messages()
                await asyncio.sleep(10)  # 10초마다 확인
                
            except Exception as e:
                Logger.error(f"지연 메시지 처리기 오류: {e}")
                await asyncio.sleep(30)
    
    asyncio.create_task(process_delayed_with_cache_check())
```

### 5.4 스케줄러 작업 등록
```python
async def _setup_scheduler_jobs(self):
    """스케줄러 작업 설정"""
    # 아웃박스 이벤트 처리 작업 (1분마다)
    outbox_job = ScheduleJob(
        job_id="process_outbox_events",
        name="아웃박스 이벤트 처리",
        schedule_type=ScheduleType.INTERVAL,
        schedule_value=60,  # 60초
        callback=self._process_outbox_events_job,
        use_distributed_lock=True,
        lock_key="scheduler:outbox_events"
    )
    
    # 메시지큐 상태 모니터링 작업 (5분마다)
    monitoring_job = ScheduleJob(
        job_id="monitor_queues",
        name="큐 상태 모니터링",
        schedule_type=ScheduleType.INTERVAL,
        schedule_value=300,  # 300초
        callback=self._monitor_queues_job,
        use_distributed_lock=False
    )
    
    # 큐 정리 작업 (1시간마다)
    cleanup_job = ScheduleJob(
        job_id="cleanup_queues",
        name="큐 정리",
        schedule_type=ScheduleType.INTERVAL,
        schedule_value=3600,  # 3600초
        callback=self._cleanup_queues_job,
        use_distributed_lock=True,
        lock_key="scheduler:cleanup_queues"
    )
    
    # 스케줄러에 작업 추가
    await SchedulerService.add_job(outbox_job)
    await SchedulerService.add_job(monitoring_job)
    await SchedulerService.add_job(cleanup_job)
```

---

## 6. 아웃박스 패턴

### 6.1 파일 위치
- **아웃박스 서비스**: `base_server/service/outbox/outbox_pattern.py`

### 6.2 아웃박스 패턴 개념
아웃박스 패턴은 **데이터베이스 트랜잭션과 이벤트 발행의 원자성을 보장**하는 패턴입니다.

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Business Logic  │    │ Database        │    │ Event Queue     │
│                 │    │                 │    │                 │
│ 1. 비즈니스 로직  │───▶│ 2. 데이터 저장   │    │                 │
│                 │    │ 3. 아웃박스 저장  │    │                 │
│                 │    │ (같은 트랜잭션)   │    │                 │
│                 │    │                 │    │                 │
│                 │    │                 │◀───│ 4. 이벤트 발행   │
│                 │    │                 │    │ (스케줄러가 처리) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 6.3 아웃박스 처리 흐름
```python
# 1. 트랜잭션 내에서 아웃박스 이벤트 저장
async def publish_event_in_transaction(self, event_type: str, aggregate_id: str, 
                                     aggregate_type: str, event_data: Dict[str, Any]):
    async with self.db_service.get_transaction() as tx:
        # 비즈니스 로직 처리
        await self.business_operation(tx)
        
        # 아웃박스 이벤트 저장 (같은 트랜잭션)
        outbox_event = OutboxEvent(
            event_type=event_type,
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            event_data=event_data,
            status=OutboxStatus.PENDING
        )
        await self.save_outbox_event(tx, outbox_event)
        
        # 트랜잭션 커밋

# 2. 스케줄러가 아웃박스 이벤트 처리 (1분마다)
async def process_outbox_events(self):
    # 미처리 아웃박스 이벤트 조회
    pending_events = await self.get_pending_outbox_events()
    
    for event in pending_events:
        try:
            # 실제 이벤트큐에 발행
            await self.event_queue_manager.publish_event(
                EventType(event.event_type),
                event.aggregate_type,
                event.event_data,
                event.aggregate_id
            )
            
            # 아웃박스 이벤트 상태 업데이트
            await self.update_outbox_event_status(event.id, OutboxStatus.PROCESSED)
            
        except Exception as e:
            Logger.error(f"아웃박스 이벤트 처리 실패: {event.id} - {e}")
            await self.update_outbox_event_status(event.id, OutboxStatus.FAILED)
```

### 6.4 아웃박스 사용 예제
```python
# 계정 생성 시 아웃박스 패턴 사용
async def create_account(self, user_data: Dict[str, Any]):
    def business_operation(tx):
        # 계정 데이터 저장
        account = Account(**user_data)
        return tx.save(account)
    
    # 아웃박스 패턴으로 이벤트 발행
    await queue_service.publish_event_with_transaction(
        event_type="account.created",
        aggregate_id=user_data["user_id"],
        aggregate_type="account",
        event_data=user_data,
        business_operation=business_operation
    )
```

---

## 7. 처리 흐름

### 7.1 전체 처리 흐름 다이어그램
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Client      │    │   Application   │    │   Queue System  │
│                 │    │                 │    │                 │
│ 1. API 요청     │───▶│ 2. 비즈니스 로직 │───▶│ 3. 메시지/이벤트 │
│                 │    │                 │    │    발행         │
│                 │    │                 │    │                 │
│                 │◀───│ 4. 응답 반환     │    │                 │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                  백그라운드 처리                                  │
│                                                                 │
│ ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│ │ 메시지 소비자    │  │ 이벤트 구독자    │  │   스케줄러      │ │
│ │  (1초 폴링)     │  │  (1초 폴링)     │  │ (시간 기반)     │ │
│ │                 │  │                 │  │                 │ │
│ │ while True:     │  │ while True:     │  │ 1분: 아웃박스    │ │
│ │   message =     │  │   event =       │  │ 5분: 모니터링    │ │
│ │   dequeue()     │  │   pop_event()   │  │ 1시간: 정리      │ │
│ │   process()     │  │   handle()      │  │ 10초: 지연메시지 │ │
│ │   ack/nack()    │  │                 │  │                 │ │
│ │   sleep(1)      │  │   sleep(1)      │  │                 │ │
│ └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 시스템 초기화 순서
```python
# main.py:lifespan() 함수에서 초기화
async def lifespan(app: FastAPI):
    # 1. 기본 서비스 초기화
    await database_service.init_service()
    CacheService.Init(cache_client_pool)
    
    # 2. 큐 서비스 초기화
    await initialize_queue_service(database_service)
    
    # 3. 스케줄러 초기화 및 시작
    await SchedulerService.start()
    
    # 4. 각 라우터의 프로토콜 콜백 설정
    setup_account_protocol_callbacks()
    setup_portfolio_protocol_callbacks()
    # ... 기타 콜백 설정
    
    yield  # 서버 실행
    
    # 5. 종료 시 정리
    await QueueService.shutdown()
    await SchedulerService.shutdown()
```

### 7.3 메시지/이벤트 처리 타이밍
```
시간축: ─────────────────────────────────────────────────────────▶

메시지 소비자:  │─1초─│─1초─│─1초─│─1초─│─1초─│─1초─│
                 poll  poll  poll  poll  poll  poll

이벤트 구독자:  │─1초─│─1초─│─1초─│─1초─│─1초─│─1초─│
                 poll  poll  poll  poll  poll  poll

지연메시지:    │────10초────│────10초────│────10초────│
                check      check      check

아웃박스:      │──────────60초──────────│──────────60초──────────│
                        process             process

모니터링:      │────────────────300초────────────────│
                                monitor

정리작업:      │───────────────────3600초───────────────────│
                                      cleanup
```

---

## 8. 설정 및 사용법

### 8.1 설정 파일
```json
// base_web_server-config_local.json
{
  "cacheConfig": {
    "type": "redis",
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "password": "",
    "session_expire_seconds": 3600,
    "connection_pool": {
      "max_connections": 50,
      "retry_on_timeout": true
    }
  },
  "databaseConfig": {
    "type": "mysql",
    "host": "localhost",
    "port": 3306,
    "database": "finance_global",
    "user": "root",
    "password": "password"
  }
}
```

### 8.2 기본 사용법

#### 8.2.1 메시지 전송
```python
from service.queue.queue_service import get_queue_service
from service.queue.message_queue import MessagePriority

queue_service = get_queue_service()

# 일반 메시지 전송
await queue_service.send_message(
    queue_name="user_tasks",
    payload={"user_id": "123", "action": "process_data"},
    message_type="user_task",
    priority=MessagePriority.NORMAL
)

# 지연 메시지 전송
from datetime import datetime, timedelta
await queue_service.send_message(
    queue_name="scheduled_tasks",
    payload={"task": "daily_report"},
    message_type="report",
    scheduled_at=datetime.now() + timedelta(hours=24)
)
```

#### 8.2.2 메시지 소비자 등록
```python
def process_user_task(message: QueueMessage) -> bool:
    try:
        user_id = message.payload["user_id"]
        action = message.payload["action"]
        
        # 실제 처리 로직
        if action == "process_data":
            result = process_user_data(user_id)
            Logger.info(f"User task completed: {user_id}")
            return True
            
    except Exception as e:
        Logger.error(f"User task failed: {e}")
        return False

# 소비자 등록
await queue_service.register_message_consumer(
    queue_name="user_tasks",
    consumer_id="user_task_worker_1",
    handler=process_user_task
)
```

#### 8.2.3 이벤트 발행
```python
from service.queue.event_queue import EventType

# 이벤트 발행
await queue_service.publish_event(
    event_type=EventType.ACCOUNT_CREATED,
    source="account_service",
    data={
        "user_id": "123",
        "email": "user@example.com",
        "created_at": datetime.now().isoformat()
    },
    correlation_id="req-456"
)
```

#### 8.2.4 이벤트 구독
```python
def handle_account_events(event: Event) -> bool:
    try:
        if event.event_type == EventType.ACCOUNT_CREATED:
            # 계정 생성 처리
            user_id = event.data["user_id"]
            send_welcome_email(user_id)
            
        elif event.event_type == EventType.ACCOUNT_UPDATED:
            # 계정 업데이트 처리
            user_id = event.data["user_id"]
            update_user_cache(user_id)
            
        return True
    except Exception as e:
        Logger.error(f"Event handling failed: {e}")
        return False

# 이벤트 구독
await queue_service.subscribe_events(
    subscriber_id="user_service",
    event_types=[EventType.ACCOUNT_CREATED, EventType.ACCOUNT_UPDATED],
    callback=handle_account_events
)
```

#### 8.2.5 아웃박스 패턴 사용
```python
# 트랜잭션과 함께 이벤트 발행
async def create_user_account(user_data: Dict[str, Any]):
    async def business_operation(tx):
        # 데이터베이스 트랜잭션 내에서 비즈니스 로직 실행
        account = Account(**user_data)
        await tx.save(account)
        return account
    
    # 아웃박스 패턴으로 이벤트 발행
    result = await queue_service.publish_event_with_transaction(
        event_type="account.created",
        aggregate_id=user_data["user_id"],
        aggregate_type="account",
        event_data=user_data,
        business_operation=business_operation
    )
    
    return result
```

---

## 9. 모니터링

### 9.1 큐 상태 모니터링
```python
# 메시지큐 통계 조회
queue_stats = await queue_service.get_queue_stats("user_tasks")
print(f"Queue stats: {queue_stats}")
# 출력 예시:
# {
#   "queue_name": "user_tasks",
#   "priority_4_count": 0,    # CRITICAL 메시지 수
#   "priority_3_count": 5,    # HIGH 메시지 수
#   "priority_2_count": 10,   # NORMAL 메시지 수
#   "priority_1_count": 2,    # LOW 메시지 수
#   "processing_count": 3,    # 처리 중인 메시지 수
#   "dlq_count": 1,          # DLQ 메시지 수
#   "delayed_count": 5       # 지연 메시지 수
# }

# 이벤트큐 통계 조회
event_stats = await queue_service.get_event_stats()
print(f"Event stats: {event_stats}")
# 출력 예시:
# {
#   "total_subscriptions": 5,
#   "active_subscribers": 3,
#   "event_stats": {
#     "published": 150,
#     "delivered": 145,
#     "failed": 5
#   },
#   "subscriptions_by_type": {
#     "account.created": 2,
#     "account.updated": 1,
#     "portfolio.updated": 2
#   }
# }

# 전체 큐 서비스 통계
service_stats = queue_service.get_stats()
print(f"Service stats: {service_stats}")
# 출력 예시:
# {
#   "messages_processed": 1000,
#   "events_published": 500,
#   "outbox_events_processed": 200,
#   "errors": 5
# }
```

### 9.2 로그 모니터링
```python
# 로그 레벨별 모니터링
Logger.info("메시지 처리 완료")      # 정상 처리
Logger.warn("Redis 연결 불안정")    # 경고 상황
Logger.error("메시지 처리 실패")     # 오류 상황

# 메트릭 로그 (5분마다 자동 출력)
# [INFO] 메시지큐 상태: {"queue_name": "user_tasks", "priority_2_count": 10, ...}
# [INFO] 이벤트큐 상태: {"total_subscriptions": 5, "active_subscribers": 3, ...}
# [INFO] QueueService 통계: {"messages_processed": 1000, "events_published": 500, ...}
```

### 9.3 Redis 모니터링
```bash
# Redis 클라이언트로 직접 모니터링
redis-cli

# 큐 상태 확인
127.0.0.1:6379> LLEN mq:priority:user_tasks:2
(integer) 10

# 지연 메시지 확인
127.0.0.1:6379> ZCARD mq:delayed:messages
(integer) 5

# 처리 중인 메시지 확인
127.0.0.1:6379> KEYS mq:processing:user_tasks:*
1) "mq:processing:user_tasks:msg123"
2) "mq:processing:user_tasks:msg456"

# 이벤트 히스토리 확인
127.0.0.1:6379> LLEN eq:history:account.created
(integer) 100
```

---

## 10. 트러블슈팅

### 10.1 일반적인 문제와 해결 방법

#### 10.1.1 메시지가 처리되지 않는 경우
```python
# 문제 진단
queue_stats = await queue_service.get_queue_stats("problem_queue")
print(f"Queue stats: {queue_stats}")

# 가능한 원인들:
# 1. 소비자가 등록되지 않음
# 2. 소비자가 중단됨
# 3. 메시지 처리 핸들러에서 예외 발생
# 4. Redis 연결 문제

# 해결 방법:
# 1. 소비자 재등록
await queue_service.register_message_consumer(
    queue_name="problem_queue",
    consumer_id="backup_consumer",
    handler=backup_handler
)

# 2. DLQ 메시지 확인
dlq_count = queue_stats.get("dlq_count", 0)
if dlq_count > 0:
    Logger.warn(f"DLQ에 {dlq_count}개 메시지가 있습니다")
    # DLQ 메시지 수동 처리 필요
```

#### 10.1.2 이벤트가 전달되지 않는 경우
```python
# 문제 진단
event_stats = await queue_service.get_event_stats()
print(f"Event stats: {event_stats}")

# 가능한 원인들:
# 1. 구독자가 등록되지 않음
# 2. 이벤트 타입 불일치
# 3. 구독자 콜백에서 예외 발생

# 해결 방법:
# 1. 구독 상태 확인
subscriptions = event_stats.get("subscriptions_by_type", {})
if "account.created" not in subscriptions:
    Logger.warn("account.created 이벤트에 구독자가 없습니다")

# 2. 구독자 재등록
await queue_service.subscribe_events(
    subscriber_id="backup_subscriber",
    event_types=[EventType.ACCOUNT_CREATED],
    callback=backup_event_handler
)
```

#### 10.1.3 Redis 연결 문제
```python
# Redis 연결 상태 확인
cache_service = CacheService.get_instance()
health_check = await cache_service.health_check()

if not health_check.get("healthy", False):
    Logger.error(f"Redis 연결 문제: {health_check.get('error', 'Unknown')}")
    
    # 재시도 로직은 자동으로 동작하지만, 수동으로도 가능
    await cache_service.reconnect()
```

#### 10.1.4 스케줄러 작업 문제
```python
# 스케줄러 상태 확인
scheduler_status = SchedulerService.get_all_jobs_status()
print(f"Scheduler status: {scheduler_status}")

# 특정 작업 상태 확인
job_status = SchedulerService.get_job_status("process_outbox_events")
if job_status.get("status") == "failed":
    Logger.error(f"스케줄러 작업 실패: {job_status.get('error')}")
    
    # 작업 재시작
    await SchedulerService.restart_job("process_outbox_events")
```

### 10.2 성능 최적화

#### 10.2.1 메시지 처리 성능 향상
```python
# 1. 소비자 수 증가
for i in range(5):  # 5개 소비자로 증가
    await queue_service.register_message_consumer(
        queue_name="high_volume_queue",
        consumer_id=f"consumer_{i}",
        handler=message_handler
    )

# 2. 배치 처리 (직접 구현 필요)
async def batch_message_handler(messages: List[QueueMessage]) -> List[bool]:
    results = []
    for message in messages:
        try:
            # 배치로 처리
            result = process_batch(message.payload)
            results.append(True)
        except Exception as e:
            Logger.error(f"Batch processing failed: {e}")
            results.append(False)
    return results
```

#### 10.2.2 Redis 성능 최적화
```python
# Redis 연결 풀 설정 조정
cache_config = {
    "max_connections": 100,  # 연결 풀 크기 증가
    "retry_on_timeout": True,
    "connection_timeout": 5
}

# 파이프라인 사용 (직접 구현 필요)
async def bulk_enqueue_messages(messages: List[QueueMessage]):
    async with cache_service.get_client() as client:
        pipeline = client.pipeline()
        for message in messages:
            # 파이프라인에 명령 추가
            pipeline.lpush(f"mq:priority:{message.queue_name}:{message.priority.value}", message.id)
        await pipeline.execute()
```

### 10.3 모니터링 알림 설정
```python
# 임계값 기반 알림
async def check_queue_health():
    stats = await queue_service.get_queue_stats("critical_queue")
    
    # DLQ 메시지 수 확인
    dlq_count = stats.get("dlq_count", 0)
    if dlq_count > 10:
        await send_alert(f"DLQ에 {dlq_count}개 메시지가 누적되었습니다")
    
    # 처리 중인 메시지 수 확인
    processing_count = stats.get("processing_count", 0)
    if processing_count > 50:
        await send_alert(f"처리 중인 메시지가 {processing_count}개로 과다합니다")
    
    # 대기 중인 메시지 수 확인
    total_pending = sum([
        stats.get("priority_4_count", 0),
        stats.get("priority_3_count", 0),
        stats.get("priority_2_count", 0),
        stats.get("priority_1_count", 0)
    ])
    if total_pending > 100:
        await send_alert(f"대기 중인 메시지가 {total_pending}개로 과다합니다")

# 5분마다 헬스체크 실행
schedule.every(5).minutes.do(check_queue_health)
```

---

## 결론

이 문서는 base_server의 큐 시스템에 대한 전체적인 이해를 돕기 위해 작성되었습니다. 각 컴포넌트의 역할과 처리 방식을 명확히 구분하여 설명했으며, 실제 사용 시 참고할 수 있는 예제와 트러블슈팅 가이드를 포함했습니다.

### 핵심 포인트
1. **메시지큐**: 1초 폴링으로 메시지 처리 (우선순위 기반)
2. **이벤트큐**: 1초 폴링으로 이벤트 처리 (구독자별 큐)
3. **스케줄러**: 시간 기반 백그라운드 작업 (시스템 관리)
4. **아웃박스**: 데이터 일관성 보장 (트랜잭션 연계)

각 시스템이 독립적으로 동작하면서도 서로 협력하여 전체 시스템의 안정성과 성능을 보장합니다.