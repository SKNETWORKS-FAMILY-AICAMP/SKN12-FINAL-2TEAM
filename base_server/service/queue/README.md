# AI Trading Platform — Queue Service

> **개요**: SKN12-FINAL-2TEAM의 AI 트레이딩 플랫폼 백엔드 Queue 서비스입니다. 메시지큐와 이벤트큐를 통합 관리하는 시스템으로, 아웃박스 패턴과 연계하여 트랜잭션 일관성을 보장하는 비동기 메시지 처리 시스템입니다.

---

## 🏗️ 프로젝트 구조

### 디렉토리 구조
```
queue/
├── __init__.py                    # 패키지 초기화
├── queue_service.py               # 통합 큐 서비스 (싱글톤 패턴)
├── message_queue.py               # 메시지큐 시스템 (Redis 기반)
├── event_queue.py                 # 이벤트큐 시스템 (Pub/Sub 패턴)
└── queue_examples.py              # 사용 예제 및 테스트 코드
```

---

## 🔧 핵심 기능

### 1. **통합 큐 서비스 (QueueService)**
- **싱글톤 패턴**: `get_instance()` 메서드로 단일 인스턴스 관리
- **통합 관리**: 메시지큐, 이벤트큐, 아웃박스 패턴을 하나의 서비스로 통합
- **초기화 관리**: `initialize()`, `graceful_shutdown()` 메서드로 서비스 생명주기 관리
- **통계 추적**: 메시지 처리, 이벤트 발행, 오류 등의 통계 수집

### 2. **메시지큐 시스템 (MessageQueue)**
- **우선순위 기반**: LOW(1), NORMAL(2), HIGH(3), CRITICAL(4) 우선순위 지원
- **지연 실행**: `scheduled_at` 필드로 미래 시점 메시지 예약
- **재시도 로직**: 실패한 메시지의 자동 재시도 (최대 3회)
- **Dead Letter Queue**: 최대 재시도 초과 시 DLQ로 이동
- **순서 보장**: `partition_key`를 통한 메시지 순서 보장

### 3. **이벤트큐 시스템 (EventQueue)**
- **Pub/Sub 패턴**: 이벤트 발행자와 구독자 간의 느슨한 결합
- **이벤트 타입**: 계정, 포트폴리오, 시장 데이터, 알림, 예측 등 다양한 도메인
- **필터링**: 구독 시 이벤트 타입과 조건 기반 필터링
- **구독 관리**: 동적 구독/해제 및 활성 상태 관리

### 4. **아웃박스 패턴 연동**
- **트랜잭션 일관성**: 비즈니스 로직과 이벤트 발행의 원자성 보장
- **이벤트 영속성**: MySQL을 통한 이벤트 저장 및 복구
- **자동 처리**: 백그라운드에서 pending 이벤트 자동 처리

---

## 📚 사용된 라이브러리

### **백엔드 & 인프라**
- **asyncio**: 비동기 프로그래밍 및 태스크 관리
- **uuid**: 고유 식별자 생성
- **json**: 메시지/이벤트 데이터 직렬화/역직렬화
- **dataclasses**: 데이터 클래스 정의
- **datetime**: 시간 기반 메시지 스케줄링

### **개발 도구**
- **typing**: 타입 힌트 및 타입 안전성
- **enum**: 메시지 상태, 우선순위, 이벤트 타입 열거형
- **abc**: 추상 클래스 및 인터페이스 정의
- **service.core.logger.Logger**: 구조화된 로깅 시스템

### **외부 의존성**
- **service.cache.CacheService**: Redis 캐시 서비스
- **service.outbox.OutboxService**: 아웃박스 패턴 서비스
- **service.scheduler.SchedulerService**: 스케줄러 서비스

---

## 🪝 핵심 클래스 및 메서드

### **QueueService - 통합 큐 서비스**

```python
class QueueService:
    """통합 큐 서비스 - 메시지큐/이벤트큐/아웃박스 패턴 통합 관리"""
    
    _instance: Optional['QueueService'] = None
    _initialized: bool = False
    
    @classmethod
    def get_instance(cls) -> 'QueueService':
        """싱글톤 인스턴스 반환"""
    
    @classmethod
    async def initialize(cls, db_service) -> bool:
        """큐 서비스 초기화"""
    
    async def send_message(self, queue_name: str, payload: Dict[str, Any], 
                          message_type: str, priority: MessagePriority = MessagePriority.NORMAL,
                          scheduled_at: Optional[datetime] = None, 
                          partition_key: Optional[str] = None) -> bool:
        """메시지 전송"""
    
    async def register_message_consumer(self, queue_name: str, consumer_id: str, 
                                      handler: Callable[[QueueMessage], bool]) -> bool:
        """메시지 소비자 등록"""
    
    async def publish_event(self, event_type: EventType, source: str, 
                           data: Dict[str, Any], correlation_id: Optional[str] = None) -> bool:
        """이벤트 발행"""
    
    async def subscribe_events(self, subscriber_id: str, event_types: List[EventType],
                              callback: Callable[[Event], bool]) -> Optional[str]:
        """이벤트 구독"""
```

### **MessageQueueManager - 메시지큐 관리자**

```python
class MessageQueueManager:
    """메시지큐 매니저 - Redis 기반 메시지큐 관리"""
    
    def __init__(self, cache_service):
        self.cache_service = cache_service
    
    async def enqueue_message(self, message: QueueMessage) -> bool:
        """메시지 큐에 추가"""
    
    async def dequeue_message(self, queue_name: str, consumer_id: str) -> Optional[QueueMessage]:
        """메시지 큐에서 가져오기"""
    
    async def ack_message(self, message_id: str, consumer_id: str) -> bool:
        """메시지 처리 완료 확인"""
    
    async def nack_message(self, message_id: str, consumer_id: str, retry: bool = True) -> bool:
        """메시지 처리 실패 처리"""
    
    async def process_delayed_messages(self):
        """지연 메시지 처리"""
```

### **EventQueueManager - 이벤트큐 관리자**

```python
class EventQueueManager:
    """이벤트큐 매니저 - Redis 기반 이벤트큐 관리"""
    
    def __init__(self, cache_service):
        self.cache_service = cache_service
    
    async def initialize(self):
        """이벤트큐 초기화"""
    
    async def publish_event(self, event: Event) -> bool:
        """이벤트 발행"""
    
    async def subscribe_events(self, subscriber_id: str, event_types: List[EventType],
                              callback: Callable[[Event], bool]) -> Optional[str]:
        """이벤트 구독"""
    
    async def unsubscribe_from_events(self, subscription_id: str) -> bool:
        """구독 해제"""
    
    async def process_published_events(self):
        """발행된 이벤트 처리"""
```

---

## 🌐 API 연동 방식

### **큐 서비스 초기화**

```python
# main.py에서 DatabaseService 이후 초기화
from service.queue.queue_service import initialize_queue_service

# DatabaseService 초기화 후
success = await initialize_queue_service(db_service)
if success:
    Logger.info("QueueService 초기화 완료")
else:
    Logger.error("QueueService 초기화 실패")
```

### **메시지 전송 및 소비**

```python
from service.queue.queue_service import get_queue_service
from service.queue.message_queue import MessagePriority

queue_service = get_queue_service()

# 메시지 전송
await queue_service.send_message(
    queue_name="user_notifications",
    payload={"user_id": "user123", "message": "포트폴리오 업데이트"},
    message_type="notification",
    priority=MessagePriority.HIGH
)

# 메시지 소비자 등록
async def notification_handler(message: QueueMessage) -> bool:
    try:
        # 메시지 처리 로직
        Logger.info(f"알림 처리: {message.payload}")
        return True
    except Exception as e:
        Logger.error(f"알림 처리 실패: {e}")
        return False

await queue_service.register_message_consumer(
    "user_notifications",
    "notification_worker_1",
    notification_handler
)
```

### **이벤트 발행 및 구독**

```python
from service.queue.event_queue import EventType

# 이벤트 발행
await queue_service.publish_event(
    event_type=EventType.PORTFOLIO_UPDATED,
    source="portfolio_service",
    data={"portfolio_id": "portfolio123", "changes": ["AAPL", "GOOGL"]}
)

# 이벤트 구독
async def portfolio_event_handler(event: Event) -> bool:
    try:
        Logger.info(f"포트폴리오 이벤트 처리: {event.data}")
        return True
    except Exception as e:
        Logger.error(f"이벤트 처리 실패: {e}")
        return False

await queue_service.subscribe_events(
    "portfolio_monitor",
    [EventType.PORTFOLIO_UPDATED, EventType.TRADE_EXECUTED],
    portfolio_event_handler
)
```

---

## 🔄 큐 서비스 전체 흐름

### **1. 메시지큐 처리 플로우**
```
1. 메시지 전송 (send_message)
2. Redis 우선순위 큐에 저장
3. 소비자가 직접 메시지 가져오기 (dequeue)
4. 메시지 처리 및 ACK/NACK
5. 실패 시 재시도 또는 DLQ 이동
```

### **2. 이벤트큐 처리 플로우**
```
1. 이벤트 발행 (publish_event)
2. 구독자 큐에 이벤트 직접 추가
3. 구독자가 이벤트 가져오기
4. 콜백 함수 실행
5. 처리 결과 로깅
```

### **3. 지연 메시지 처리 플로우**
```
1. 지연 메시지 예약 (scheduled_at)
2. Redis Sorted Set에 저장
3. 백그라운드 프로세서가 10초마다 확인
4. 실행 시간 도달 시 일반 큐로 이동
5. 정상적인 메시지 처리 흐름
```

---

## 🔌 큐 시스템 구현 상세

### **Redis 기반 메시지큐**

```python
class RedisCacheMessageQueue(IMessageQueue):
    """CacheService를 사용하는 Redis 메시지큐"""
    
    def __init__(self, cache_service):
        self.cache_service = cache_service
        
        # Redis 키 패턴들
        self.message_key_pattern = "mq:message:{message_id}"
        self.priority_queue_pattern = "mq:priority:{queue_name}:{priority}"
        self.delayed_key_pattern = "mq:delayed:messages"
        self.processing_key_pattern = "mq:processing:{queue_name}"
        self.dlq_key_pattern = "mq:dlq:{queue_name}"
    
    async def enqueue(self, message: QueueMessage) -> bool:
        """메시지 큐에 추가"""
        try:
            # 메시지 데이터 저장
            message_key = self.message_key_pattern.format(message_id=message.id)
            message_data = {
                "id": message.id,
                "queue_name": message.queue_name,
                "payload": json.dumps(message.payload),
                "message_type": message.message_type,
                "priority": message.priority.value,
                "status": message.status.value,
                "retry_count": message.retry_count,
                "max_retries": message.max_retries,
                "created_at": message.created_at.isoformat() if message.created_at else None,
                "scheduled_at": message.scheduled_at.isoformat() if message.scheduled_at else None,
                "partition_key": message.partition_key
            }
            
            # 우선순위 큐에 추가
            priority_queue_key = self.priority_queue_pattern.format(
                queue_name=message.queue_name, 
                priority=message.priority.value
            )
            
            await self.cache_service.set_hash(message_key, message_data)
            await self.cache_service.lpush(priority_queue_key, message.id)
            
            # 지연 메시지인 경우 Sorted Set에 추가
            if message.scheduled_at:
                score = message.scheduled_at.timestamp()
                await self.cache_service.zadd(self.delayed_key_pattern, {message.id: score})
            
            Logger.info(f"메시지 큐에 추가: {message.id} (우선순위: {message.priority.value})")
            return True
            
        except Exception as e:
            Logger.error(f"메시지 큐 추가 실패: {message.id} - {e}")
            return False
```

### **이벤트큐 Pub/Sub 구현**

```python
class RedisCacheEventQueue(IEventQueue):
    """CacheService를 사용하는 Redis 이벤트큐"""
    
    def __init__(self, cache_service):
        self.cache_service = cache_service
        
        # Redis 키 패턴
        self.event_stream_pattern = "eq:stream:{event_type}"
        self.subscription_key = "eq:subscriptions"
        self.subscriber_key_pattern = "eq:subscriber:{subscriber_id}"
        self.event_history_pattern = "eq:history:{event_type}"
        
        # 구독자 정보
        self.subscriptions: Dict[str, Subscription] = {}
        self.active_subscribers: Set[str] = set()
    
    async def publish(self, event: Event) -> bool:
        """이벤트 발행"""
        try:
            # 이벤트를 JSON으로 직렬화
            event_payload = {
                "event": {
                    "id": event.id,
                    "event_type": event.event_type.value,
                    "source": event.source,
                    "data": event.data,
                    "timestamp": event.timestamp.isoformat(),
                    "correlation_id": event.correlation_id,
                    "version": event.version,
                    "metadata": event.metadata
                }
            }
            
            event_json = json.dumps(event_payload)
            
            # 이벤트 히스토리에 저장
            history_key = self.event_history_pattern.format(event_type=event.event_type.value)
            await self.cache_service.list_push_right(history_key, event_json)
            await self.cache_service.expire(history_key, 86400)  # 24시간 후 만료
            
            # 관련 구독자들에게 이벤트 전달
            for subscription in self.subscriptions.values():
                if event.event_type in subscription.event_types and subscription.active:
                    subscriber_queue_key = self.subscriber_key_pattern.format(
                        subscriber_id=subscription.subscriber_id
                    )
                    await self.cache_service.list_push_right(subscriber_queue_key, event_json)
            
            Logger.info(f"이벤트 발행 완료: {event.id} ({event.event_type.value})")
            return True
            
        except Exception as e:
            Logger.error(f"이벤트 발행 실패: {event.id} - {e}")
            return False
```

---

## 🔬 고급 기능 심층 분석: 큐 시스템 아키텍처

큐 서비스의 핵심은 **메시지큐와 이벤트큐의 통합 관리**와 **아웃박스 패턴과의 연동**입니다.

### **1. 개요**
이 시스템은 **Redis를 기반으로 한 고성능 메시지 처리**와 **이벤트 기반 아키텍처**를 제공합니다. 전통적인 동기식 처리의 한계를 극복하고, **비동기 메시지 처리**와 **이벤트 주도 설계**를 통해 시스템의 확장성과 안정성을 향상시킵니다.

### **2. 핵심 아키텍처 및 데이터 플로우**

#### **2.1 메시지큐 우선순위 처리**
```python
async def dequeue_message(self, queue_name: str, consumer_id: str) -> Optional[QueueMessage]:
    """메시지 큐에서 가져오기 (우선순위 기반)"""
    try:
        # 우선순위 순서로 큐 확인 (CRITICAL → HIGH → NORMAL → LOW)
        for priority in [MessagePriority.CRITICAL, MessagePriority.HIGH, 
                        MessagePriority.NORMAL, MessagePriority.LOW]:
            
            priority_queue_key = self.priority_queue_pattern.format(
                queue_name=queue_name, 
                priority=priority.value
            )
            
            # 원자적 메시지 가져오기
            message_id = await self.cache_service.rpop(priority_queue_key)
            if message_id:
                # 메시지 데이터 조회
                message_key = self.message_key_pattern.format(message_id=message_id)
                message_data = await self.cache_service.get_hash(message_key)
                
                if message_data:
                    # 처리 중 상태로 변경
                    processing_key = self.processing_key_pattern.format(queue_name=queue_name)
                    await self.cache_service.hset(processing_key, message_id, consumer_id)
                    
                    # QueueMessage 객체 생성
                    message = QueueMessage(
                        id=message_id,
                        queue_name=queue_name,
                        payload=json.loads(message_data["payload"]),
                        message_type=message_data["message_type"],
                        priority=MessagePriority(int(message_data["priority"])),
                        status=MessageStatus(message_data["status"]),
                        retry_count=int(message_data["retry_count"]),
                        max_retries=int(message_data["max_retries"]),
                        created_at=datetime.fromisoformat(message_data["created_at"]) if message_data["created_at"] else None,
                        scheduled_at=datetime.fromisoformat(message_data["scheduled_at"]) if message_data["scheduled_at"] else None,
                        partition_key=message_data.get("partition_key")
                    )
                    
                    Logger.info(f"메시지 가져오기: {message_id} (우선순위: {priority.value})")
                    return message
        
        return None
        
    except Exception as e:
        Logger.error(f"메시지 가져오기 실패: {e}")
        return None
```

#### **2.2 지연 메시지 처리 시스템**
```python
async def process_delayed_messages(self):
    """지연 메시지 처리"""
    try:
        current_time = datetime.now().timestamp()
        
        # 실행 시간이 도달한 지연 메시지 조회
        ready_messages = await self.cache_service.zrangebyscore(
            self.delayed_key_pattern,
            min_score=0,
            max_score=current_time
        )
        
        for message_id in ready_messages:
            try:
                # 메시지 데이터 조회
                message_key = self.message_key_pattern.format(message_id=message_id)
                message_data = await self.cache_service.get_hash(message_key)
                
                if message_data:
                    # 지연 메시지에서 제거
                    await self.cache_service.zrem(self.delayed_key_pattern, message_id)
                    
                    # 일반 우선순위 큐로 이동
                    priority = int(message_data["priority"])
                    priority_queue_key = self.priority_queue_pattern.format(
                        queue_name=message_data["queue_name"], 
                        priority=priority
                    )
                    
                    await self.cache_service.lpush(priority_queue_key, message_id)
                    
                    Logger.info(f"지연 메시지 활성화: {message_id}")
                
            except Exception as e:
                Logger.error(f"지연 메시지 처리 실패: {message_id} - {e}")
        
    except Exception as e:
        Logger.error(f"지연 메시지 처리 오류: {e}")
```

### **3. 실제 구현된 동작 과정**

#### **3.1 메시지 처리 과정**
```
1. 메시지 전송 (우선순위, 지연시간 설정 가능)
2. Redis 우선순위 큐에 저장
3. 소비자가 직접 메시지 가져오기 (dequeue)
4. 우선순위 순서로 메시지 가져오기
5. 메시지 처리 및 ACK/NACK
6. 실패 시 재시도 또는 DLQ 이동
```

#### **3.2 이벤트 처리 과정**
```
1. 이벤트 발행 (도메인별 이벤트 타입)
2. 구독자 큐에 이벤트 직접 추가
3. 구독자가 이벤트 가져오기
4. 이벤트 처리 및 콜백 함수 실행
5. 처리 결과 로깅
```

### **4. 성능 최적화 효과**

#### **4.1 우선순위 기반 처리**
```
우선순위별 독립 큐:
- CRITICAL: 즉시 처리 (시스템 알림, 오류 등)
- HIGH: 높은 우선순위 (사용자 알림, 거래 실행 등)
- NORMAL: 일반 우선순위 (일반 작업)
- LOW: 낮은 우선순위 (백그라운드 작업)
```

#### **4.2 지연 메시지 최적화**
```
Redis Sorted Set 활용:
- 실행 시간을 score로 사용
- O(log N) 시간 복잡도로 효율적 조회
- 배치 처리로 성능 향상
```

### **5. 에러 처리 및 복구**

#### **5.1 재시도 로직**
```python
async def nack_message(self, message_id: str, consumer_id: str, retry: bool = True) -> bool:
    """메시지 처리 실패 처리"""
    try:
        # 메시지 데이터 조회
        message_key = self.message_key_pattern.format(message_id=message_id)
        message_data = await self.cache_service.get_hash(message_key)
        
        if message_data:
            retry_count = int(message_data["retry_count"])
            max_retries = int(message_data["max_retries"])
            
            if retry and retry_count < max_retries:
                # 재시도 횟수 증가
                new_retry_count = retry_count + 1
                await self.cache_service.hset(message_key, "retry_count", new_retry_count)
                
                # 재시도 대기 상태로 변경
                await self.cache_service.hset(message_key, "status", MessageStatus.RETRY.value)
                
                # 원래 우선순위 큐에 다시 추가
                priority = int(message_data["priority"])
                priority_queue_key = self.priority_queue_pattern.format(
                    queue_name=message_data["queue_name"], 
                    priority=priority
                )
                
                await self.cache_service.lpush(priority_queue_key, message_id)
                
                Logger.warning(f"메시지 재시도 예약: {message_id} ({new_retry_count}/{max_retries})")
                
            else:
                # 최대 재시도 횟수 초과 시 DLQ로 이동
                await self.cache_service.hset(message_key, "status", MessageStatus.FAILED.value)
                
                dlq_key = self.dlq_key_pattern.format(queue_name=message_data["queue_name"])
                await self.cache_service.lpush(dlq_key, message_id)
                
                Logger.error(f"메시지 최종 실패 - DLQ 이동: {message_id}")
            
            # 처리 중 상태에서 제거
            processing_key = self.processing_key_pattern.format(queue_name=message_data["queue_name"])
            await self.cache_service.hdel(processing_key, message_id)
            
            return True
            
    except Exception as e:
        Logger.error(f"메시지 NACK 처리 실패: {message_id} - {e}")
        return False
```

#### **5.2 자동 복구 메커니즘**
```python
async def _start_delayed_message_processor_with_check(self):
    """CacheService 연결 체크를 포함한 지연 메시지 처리기 시작"""
    async def process_delayed_with_cache_check():
        while self.__class__._initialized:  # 서비스 초기화 상태 확인
            try:
                # CacheService 연결 상태 확인
                cache_service = CacheService.get_instance()
                if not cache_service.is_initialized():
                    Logger.debug("CacheService가 초기화되지 않음. 지연 메시지 처리 건너뜀")
                    await asyncio.sleep(30)
                    continue
                
                # 연결 상태 테스트
                health_check = await cache_service.health_check()
                if not health_check.get("healthy", False):
                    Logger.debug(f"Redis 연결 불안정: {health_check.get('error', 'Unknown')}. 지연 메시지 처리 건너뜀")
                    await asyncio.sleep(30)
                    continue
                
                # 정상 처리
                await self.message_queue_manager.message_queue.process_delayed_messages()
                await asyncio.sleep(10)  # 10초마다 확인
                
            except Exception as e:
                Logger.error(f"지연 메시지 처리기 오류: {e}")
                await asyncio.sleep(30)
        
        Logger.debug("지연 메시지 처리기 종료")
    
    asyncio.create_task(process_delayed_with_cache_check())
```

### **6. 실제 사용 사례**

#### **6.1 사용자 알림 시스템**
```python
# 고우선순위 알림 메시지
await queue_service.send_message(
    queue_name="user_notifications",
    payload={
        "user_id": "user123",
        "message": "주가 알림: AAPL이 $150.00에 도달했습니다",
        "notification_type": "price_alert",
        "stock_symbol": "AAPL",
        "target_price": 150.00
    },
    message_type="price_alert",
    priority=MessagePriority.HIGH
)

# 알림 소비자 등록
async def price_alert_handler(message: QueueMessage) -> bool:
    try:
        payload = message.payload
        user_id = payload["user_id"]
        message_text = payload["message"]
        
        # 푸시 알림 발송 
        await send_push_notification(user_id, message_text)
        
        # 알림 로그 저장 
        await save_notification_log(user_id, "price_alert", message_text)
        
        Logger.info(f"가격 알림 처리 완료: {user_id}")
        return True
        
    except Exception as e:
        Logger.error(f"가격 알림 처리 실패: {e}")
        return False

await queue_service.register_message_consumer(
    "user_notifications",
    "price_alert_worker",
    price_alert_handler
)
```

#### **6.2 포트폴리오 리밸런싱 스케줄링**
```python
# 10분 후 실행될 리밸런싱 작업
delayed_time = datetime.now() + timedelta(minutes=10)

await queue_service.send_message(
    queue_name="portfolio_tasks",
    payload={
        "task_type": "portfolio_rebalancing",
        "portfolio_id": "portfolio123",
        "target_allocation": {
            "stocks": 0.6,
            "bonds": 0.3,
            "cash": 0.1
        },
        "rebalance_threshold": 0.05
    },
    message_type="scheduled_task",
    priority=MessagePriority.NORMAL,
    scheduled_at=delayed_time
)

# 리밸런싱 작업 처리자
async def rebalancing_handler(message: QueueMessage) -> bool:
    try:
        payload = message.payload
        portfolio_id = payload["portfolio_id"]
        target_allocation = payload["target_allocation"]
        
        # 현재 포트폴리오 조회
        current_portfolio = await get_portfolio(portfolio_id)
        
        # 리밸런싱 계산
        rebalancing_orders = calculate_rebalancing_orders(
            current_portfolio, target_allocation
        )
        
        # 주문 실행
        for order in rebalancing_orders:
            await execute_trade_order(order)
        
        Logger.info(f"포트폴리오 리밸런싱 완료: {portfolio_id}")
        return True
        
    except Exception as e:
        Logger.error(f"포트폴리오 리밸런싱 실패: {e}")
        return False

await queue_service.register_message_consumer(
    "portfolio_tasks",
    "rebalancing_worker",
    rebalancing_handler
)
```

### **7. 핵심 특징 및 장점**

#### **7.1 성능 및 확장성**
- **Redis 기반**: 고성능 인메모리 데이터 구조
- **우선순위 처리**: 중요도에 따른 메시지 처리 순서
- **지연 실행**: 미래 시점 작업 스케줄링
- **배치 처리**: 효율적인 메시지 처리

#### **7.2 안정성 및 신뢰성**
- **재시도 로직**: 실패한 메시지의 자동 재시도
- **Dead Letter Queue**: 처리 불가능한 메시지 격리
- **분산락**: 중복 처리 방지
- **상태 추적**: 메시지의 전체 생명주기 추적

#### **7.3 유연성 및 확장성**
- **이벤트 기반**: 느슨한 결합의 시스템 설계
- **동적 구독**: 런타임에 이벤트 구독/해제
- **필터링**: 이벤트 타입과 조건 기반 구독
- **아웃박스 연동**: 트랜잭션 일관성 보장

이 시스템은 단순한 메시지 전달을 넘어서 **우선순위 기반 처리**, **지연 실행**, **이벤트 주도 설계**, **트랜잭션 일관성**을 제공하는 고도화된 큐 시스템입니다.

---

## 📊 사용 예제

### **기본 메시지큐 사용**

```python
from service.queue.queue_service import get_queue_service
from service.queue.message_queue import MessagePriority

queue_service = get_queue_service()

# 메시지 전송
await queue_service.send_message(
    queue_name="email_notifications",
    payload={
        "to": "user@example.com",
        "subject": "포트폴리오 업데이트",
        "body": "포트폴리오가 성공적으로 업데이트되었습니다."
    },
    message_type="email",
    priority=MessagePriority.NORMAL
)

# 메시지 소비자 등록
async def email_handler(message: QueueMessage) -> bool:
    try:
        payload = message.payload
        # 이메일 발송 로직
        from service.email.email_service import EmailService
        await EmailService.send_email(
            to_emails=[payload["to"]],
            subject=payload["subject"],
            body=payload["body"]
        )
        return True
    except Exception as e:
        Logger.error(f"이메일 처리 실패: {e}")
        return False

await queue_service.register_message_consumer(
    "email_notifications",
    "email_worker",
    email_handler
)
```

### **지연 메시지 스케줄링**

```python
from datetime import datetime, timedelta

# 1시간 후 실행될 작업
delayed_time = datetime.now() + timedelta(hours=1)

await queue_service.send_message(
    queue_name="maintenance_tasks",
    payload={
        "task": "database_cleanup",
        "tables": ["user_sessions", "temp_data"],
        "retention_days": 30
    },
    message_type="maintenance",
    priority=MessagePriority.LOW,
    scheduled_at=delayed_time
)
```

### **이벤트 기반 시스템**

```python
from service.queue.event_queue import EventType

# 포트폴리오 업데이트 이벤트 발행
await queue_service.publish_event(
    event_type=EventType.PORTFOLIO_UPDATED,
    source="portfolio_service",
    data={
        "portfolio_id": "portfolio123",
        "user_id": "user456",
        "changes": ["AAPL", "GOOGL"],
        "timestamp": datetime.now().isoformat()
    }
)

# 이벤트 구독
async def portfolio_update_handler(event: Event) -> bool:
    try:
        # 포트폴리오 변경 알림
        Logger.info(f"포트폴리오 변경 이벤트 처리: {event.data}")
        # 실제 포트폴리오 업데이트 로직 구현 필요
        # await update_portfolio(event.data)
        return True
    except Exception as e:
        Logger.error(f"포트폴리오 이벤트 처리 실패: {e}")
        return False

await queue_service.subscribe_events(
    "portfolio_monitor",
    [EventType.PORTFOLIO_UPDATED, EventType.TRADE_EXECUTED],
    portfolio_update_handler
)
```

---

## ⚙️ 설정

### **QueueService 설정**

```python
# main.py에서 초기화
from service.queue.queue_service import initialize_queue_service

# DatabaseService 초기화 후
success = await initialize_queue_service(db_service)
if not success:
    Logger.error("QueueService 초기화 실패")
    exit(1)
```

### **Redis 설정 (CacheService를 통해)**

```json
{
  "cache": {
    "redis": {
      "host": "your_redis_host",
      "port": 6379,
      "db": 0,
      "password": "your_redis_password",
      "max_connections": 10
    }
  }
}
```

### **메시지큐 설정**

```python
# 메시지 우선순위
MessagePriority.LOW = 1      # 낮은 우선순위
MessagePriority.NORMAL = 2   # 일반 우선순위
MessagePriority.HIGH = 3     # 높은 우선순위
MessagePriority.CRITICAL = 4 # 최고 우선순위

# 재시도 설정
max_retries = 3              # 최대 재시도 횟수 (QueueMessage 기본값)
```

---

## 🔗 연관 폴더

### **사용하는 Service**
- **service.cache.CacheService**: Redis 캐시 서비스를 통한 메시지/이벤트 저장
- **service.outbox.OutboxService**: 트랜잭션 일관성을 위한 아웃박스 패턴 연동
- **service.scheduler.SchedulerService**: 백그라운드 작업 스케줄링

### **사용하는 Template**
- **template.chat**: 채팅 영속성 컨슈머를 QueueService에 등록하여 메시지 처리
- **template.notification**: 알림 영속성 컨슈머를 QueueService에 등록하여 알림 처리
- **template.admin**: QueueService 상태 모니터링 및 큐 통계 조회

### **의존성 관계**
- **service.core.logger.Logger**: 구조화된 로깅 시스템
- **service.db.DatabaseService**: 아웃박스 이벤트 영속성 저장
- **application.base_web_server.main**: 서비스 초기화 및 통합

---

## 📚 외부 시스템

### **Redis**
- **메시지큐**: 우선순위 기반 메시지 저장 및 처리
- **이벤트큐**: Pub/Sub 패턴의 이벤트 전파
- **지연 메시지**: Sorted Set을 활용한 스케줄링
- **분산락**: 중복 처리 방지

### **MySQL**
- **아웃박스 이벤트**: OutboxService를 통한 트랜잭션 일관성 보장 (QueueService와 연동)

---