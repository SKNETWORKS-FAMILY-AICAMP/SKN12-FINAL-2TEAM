"""
이벤트큐 시스템 - 발생한 이벤트를 구독자에게 퍼블리싱하는 Pub/Sub 역할
"""

import json
import uuid
import asyncio
from typing import Dict, Any, List, Optional, Callable, Set
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod

from service.core.logger import Logger
from service.cache.redis_cache_client import RedisCacheClient
from service.lock.distributed_lock import DistributedLockManager


class EventType(Enum):
    """이벤트 타입"""
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


@dataclass
class Event:
    """이벤트 객체"""
    id: str
    event_type: EventType
    source: str  # 이벤트 발생 소스
    data: Dict[str, Any]
    timestamp: datetime
    correlation_id: Optional[str] = None  # 추적용
    version: str = "1.0"
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Subscription:
    """구독 정보"""
    id: str
    subscriber_id: str
    event_types: Set[EventType]
    callback: Callable[[Event], bool]
    filter_conditions: Optional[Dict[str, Any]] = None
    active: bool = True


class IEventQueue(ABC):
    """이벤트큐 인터페이스"""
    
    @abstractmethod
    async def publish(self, event: Event) -> bool:
        """이벤트 발행"""
        pass
    
    @abstractmethod
    async def subscribe(self, subscription: Subscription) -> bool:
        """이벤트 구독"""
        pass
    
    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> bool:
        """구독 해제"""
        pass


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
        
        # 이벤트 처리 통계
        self.event_stats = {
            "published": 0,
            "delivered": 0,
            "failed": 0
        }
    
    async def _execute_redis_operation(self, operation_name: str, operation_func, *args, **kwargs):
        """Redis 작업을 CacheService를 통해 안전하게 실행"""
        try:
            # CacheService 초기화 상태 확인
            if not self.cache_service.is_initialized():
                Logger.warn(f"Redis operation {operation_name} failed: CacheService is not initialized")
                return None
            
            async with self.cache_service.get_client() as client:
                return await operation_func(client, *args, **kwargs)
        except Exception as e:
            # Error인 경우는 무조건 출력
            Logger.error(f"Redis operation {operation_name} failed: {e}")
            return None
    
    async def publish(self, event: Event) -> bool:
        """이벤트 발행"""
        async def _publish_operation(client, evt):
            # 이벤트를 JSON으로 직렬화
            event_payload = {
                "event": {
                    "id": evt.id,
                    "event_type": evt.event_type.value,
                    "source": evt.source,
                    "data": evt.data,
                    "timestamp": evt.timestamp.isoformat(),
                    "correlation_id": evt.correlation_id,
                    "version": evt.version,
                    "metadata": evt.metadata
                }
            }
            
            event_json = json.dumps(event_payload)
            
            # 이벤트 히스토리에 저장
            history_key = self.event_history_pattern.format(event_type=evt.event_type.value)
            await client.list_push_right(history_key, event_json)
            await client.expire(history_key, 86400)  # 24시간 후 만료
            
            # 관련 구독자들에게 이벤트 전달
            for subscription in self.subscriptions.values():
                if evt.event_type in subscription.event_types and subscription.active:
                    subscriber_queue_key = self.subscriber_key_pattern.format(
                        subscriber_id=subscription.subscriber_id
                    )
                    await client.list_push_right(subscriber_queue_key, event_json)
            
            self.event_stats["published"] += 1
            return True
        
        return await self._execute_redis_operation("publish", _publish_operation, event)
    
    async def subscribe(self, subscription: Subscription) -> bool:
        """이벤트 구독"""
        try:
            self.subscriptions[subscription.id] = subscription
            self.active_subscribers.add(subscription.subscriber_id)
            
            # 구독자 이벤트 처리 태스크 시작
            asyncio.create_task(self._process_subscriber_events(subscription))
            
            Logger.info(f"이벤트 구독 등록: {subscription.subscriber_id} ({len(subscription.event_types)}개 타입)")
            return True
            
        except Exception as e:
            Logger.error(f"이벤트 구독 실패: {subscription.subscriber_id} - {e}")
            return False
    
    async def unsubscribe(self, subscription_id: str) -> bool:
        """구독 해제"""
        try:
            if subscription_id in self.subscriptions:
                subscription = self.subscriptions[subscription_id]
                subscription.active = False
                
                # 구독자의 다른 구독이 없으면 active_subscribers에서 제거
                has_other_subscriptions = any(
                    sub.subscriber_id == subscription.subscriber_id and sub.active 
                    for sub_id, sub in self.subscriptions.items() 
                    if sub_id != subscription_id
                )
                
                if not has_other_subscriptions:
                    self.active_subscribers.discard(subscription.subscriber_id)
                
                del self.subscriptions[subscription_id]
                Logger.info(f"이벤트 구독 해제: {subscription.subscriber_id}")
                return True
            
            return False
            
        except Exception as e:
            Logger.error(f"이벤트 구독 해제 실패: {subscription_id} - {e}")
            return False
    
    async def unsubscribe_all(self):
        """모든 구독 해제"""
        try:
            # 모든 구독을 비활성화
            for subscription in self.subscriptions.values():
                subscription.active = False
            
            # 구독 정보 모두 제거
            subscription_ids = list(self.subscriptions.keys())
            for subscription_id in subscription_ids:
                await self.unsubscribe(subscription_id)
            
            # 활성 구독자 목록 초기화
            self.active_subscribers.clear()
            
            Logger.info("모든 구독 해제 완료")
            
        except Exception as e:
            Logger.error(f"모든 구독 해제 중 오류: {e}")
    
    async def _process_subscriber_events(self, subscription: Subscription):
        """구독자별 이벤트 처리"""
        subscriber_queue_key = self.subscriber_key_pattern.format(
            subscriber_id=subscription.subscriber_id
        )
        
        while subscription.active and subscription.id in self.subscriptions:
            try:
                
                # 큐에서 이벤트 가져오기
                async def _get_event_operation(client):
                    return await client.list_pop_left(subscriber_queue_key)
                
                event_data = await self._execute_redis_operation("list_pop_left", _get_event_operation)
                
                if not event_data:
                    # 메시지가 없으면 짧은 시간 대기
                    await asyncio.sleep(1)
                    continue
                
                event_payload = json.loads(event_data)
                event_info = event_payload["event"]
                
                # Event 객체 재구성
                event = Event(
                    id=event_info["id"],
                    event_type=EventType(event_info["event_type"]),
                    source=event_info["source"],
                    data=event_info["data"],
                    timestamp=datetime.fromisoformat(event_info["timestamp"]),
                    correlation_id=event_info.get("correlation_id"),
                    version=event_info.get("version", "1.0"),
                    metadata=event_info.get("metadata")
                )
                
                # 콜백 실행
                try:
                    success = False
                    if asyncio.iscoroutinefunction(subscription.callback):
                        success = await subscription.callback(event)
                    else:
                        success = subscription.callback(event)
                    
                    if success:
                        self.event_stats["delivered"] += 1
                    else:
                        self.event_stats["failed"] += 1
                        
                except Exception as e:
                    Logger.error(f"구독자 이벤트 처리 오류: {subscription.subscriber_id} - {e}")
                    self.event_stats["failed"] += 1
                
            except Exception as e:
                Logger.error(f"구독자 이벤트 처리 오류: {subscription.subscriber_id} - {e}")
                await asyncio.sleep(5)
    
    async def get_event_history(self, event_type: EventType, limit: int = 100) -> List[Event]:
        """이벤트 히스토리 조회"""
        async def _get_history_operation(client, et, lmt):
            history_key = self.event_history_pattern.format(event_type=et.value)
            event_data_list = await client.list_range(history_key, -lmt, -1)
            
            events = []
            for event_data in reversed(event_data_list):
                try:
                    event_payload = json.loads(event_data)
                    event_info = event_payload["event"]
                    
                    event = Event(
                        id=event_info["id"],
                        event_type=EventType(event_info["event_type"]),
                        source=event_info["source"],
                        data=event_info["data"],
                        timestamp=datetime.fromisoformat(event_info["timestamp"]),
                        correlation_id=event_info.get("correlation_id"),
                        version=event_info.get("version", "1.0"),
                        metadata=event_info.get("metadata")
                    )
                    events.append(event)
                except Exception as e:
                    Logger.error(f"이벤트 히스토리 파싱 오류: {e}")
            
            return events
        
        result = await self._execute_redis_operation("get_event_history", _get_history_operation, event_type, limit)
        return result if result is not None else []
    
    async def get_subscription_stats(self) -> Dict[str, Any]:
        """구독 통계 조회"""
        try:
            stats = {
                "total_subscriptions": len(self.subscriptions),
                "active_subscribers": len(self.active_subscribers),
                "event_stats": self.event_stats.copy(),
                "subscriptions_by_type": {}
            }
            
            # 이벤트 타입별 구독 수 계산
            for subscription in self.subscriptions.values():
                for event_type in subscription.event_types:
                    type_name = event_type.value
                    if type_name not in stats["subscriptions_by_type"]:
                        stats["subscriptions_by_type"][type_name] = 0
                    stats["subscriptions_by_type"][type_name] += 1
            
            return stats
            
        except Exception as e:
            Logger.error(f"구독 통계 조회 실패: {e}")
            return {}


class RedisEventQueue(IEventQueue):
    """Redis 기반 이벤트큐 구현 (Pub/Sub + Stream)"""
    
    def __init__(self, redis_client: RedisCacheClient, lock_manager: DistributedLockManager):
        self.redis_client = redis_client
        self.lock_manager = lock_manager
        
        # Redis 키 패턴
        self.event_stream_pattern = "eq:stream:{event_type}"
        self.subscription_key = "eq:subscriptions"
        self.subscriber_key_pattern = "eq:subscriber:{subscriber_id}"
        self.event_history_pattern = "eq:history:{event_type}"
        
        # 구독자 정보
        self.subscriptions: Dict[str, Subscription] = {}
        self.active_subscribers: Set[str] = set()
        
        # 이벤트 처리 통계
        self.event_stats = {
            "published": 0,
            "delivered": 0,
            "failed": 0
        }
    
    async def publish(self, event: Event) -> bool:
        """이벤트 발행 (Redis Stream + Pub/Sub)"""
        try:
            event.id = event.id or str(uuid.uuid4())
            event.timestamp = event.timestamp or datetime.now()
            
            # 이벤트 데이터 직렬화
            event_data = {
                "id": event.id,
                "event_type": event.event_type.value,
                "source": event.source,
                "data": json.dumps(event.data),
                "timestamp": event.timestamp.isoformat(),
                "correlation_id": event.correlation_id or "",
                "version": event.version,
                "metadata": json.dumps(event.metadata or {})
            }
            
            # 1. Redis Stream에 이벤트 저장 (이력 관리) - 추후 구현
            # stream_key = self.event_stream_pattern.format(event_type=event.event_type.value)
            # await self.redis_client.stream_add(stream_key, event_data)
            
            # 2. 이벤트 히스토리 저장 (최근 1000개만 유지)
            history_key = self.event_history_pattern.format(event_type=event.event_type.value)
            await self.redis_client.list_push_left(history_key, json.dumps(event_data))
            await self.redis_client.list_trim(history_key, 0, 999)  # 최근 1000개만 유지
            
            # 3. 실시간 구독자들에게 Pub/Sub으로 즉시 전달 - 추후 구현
            # channel = f"events:{event.event_type.value}"
            # await self.redis_client.publish(channel, json.dumps(event_data))
            
            # 4. 구독자별 개별 큐에도 전달 (보장된 전달)
            await self._deliver_to_subscribers(event)
            
            self.event_stats["published"] += 1
            Logger.info(f"이벤트 발행 완료: {event.id} ({event.event_type.value})")
            
            return True
            
        except Exception as e:
            Logger.error(f"이벤트 발행 실패: {event.id} - {e}")
            self.event_stats["failed"] += 1
            return False
    
    async def subscribe(self, subscription: Subscription) -> bool:
        """이벤트 구독 (Redis Stream Consumer Group 활용)"""
        try:
            subscription.id = subscription.id or str(uuid.uuid4())
            
            # 구독 정보 저장
            self.subscriptions[subscription.id] = subscription
            self.active_subscribers.add(subscription.subscriber_id)
            
            # Redis에 구독 정보 저장
            subscription_data = {
                "id": subscription.id,
                "subscriber_id": subscription.subscriber_id,
                "event_types": json.dumps([et.value for et in subscription.event_types]),
                "filter_conditions": json.dumps(subscription.filter_conditions or {}),
                "active": str(subscription.active),
                "created_at": datetime.now().isoformat()
            }
            
            await self.redis_client.set_hash_field(
                self.subscription_key,
                subscription.id,
                json.dumps(subscription_data)
            )
            
            # 각 이벤트 타입별로 Consumer Group 생성
            for event_type in subscription.event_types:
                stream_key = self.event_stream_pattern.format(event_type=event_type.value)
                consumer_group = f"group:{subscription.subscriber_id}"
                
                try:
                    # Consumer Group 생성 (이미 존재하면 무시)
                    # Redis Stream의 경우 별도 구현이 필요하므로 우선 패스
                    pass
                except:
                    # Group이 이미 존재하는 경우 무시
                    pass
            
            # 구독자별 전용 큐 생성
            subscriber_queue_key = self.subscriber_key_pattern.format(
                subscriber_id=subscription.subscriber_id
            )
            
            # 구독자 처리 태스크 시작
            asyncio.create_task(self._process_subscriber_events(subscription))
            
            Logger.info(f"이벤트 구독 등록: {subscription.subscriber_id} ({len(subscription.event_types)}개 타입)")
            return True
            
        except Exception as e:
            Logger.error(f"이벤트 구독 실패: {subscription.subscriber_id} - {e}")
            return False
    
    async def unsubscribe(self, subscription_id: str) -> bool:
        """구독 해제"""
        try:
            if subscription_id not in self.subscriptions:
                Logger.warn(f"구독을 찾을 수 없음: {subscription_id}")
                return False
            
            subscription = self.subscriptions[subscription_id]
            
            # 구독 정보 제거
            del self.subscriptions[subscription_id]
            if subscription.subscriber_id in self.active_subscribers:
                self.active_subscribers.remove(subscription.subscriber_id)
            
            # Redis에서 구독 정보 제거
            await self.redis_client.hash_delete(self.subscription_key, subscription_id)
            
            # 구독자 큐 정리
            subscriber_queue_key = self.subscriber_key_pattern.format(
                subscriber_id=subscription.subscriber_id
            )
            await self.redis_client.delete_key(subscriber_queue_key)
            
            Logger.info(f"이벤트 구독 해제: {subscription.subscriber_id}")
            return True
            
        except Exception as e:
            Logger.error(f"구독 해제 실패: {subscription_id} - {e}")
            return False
    
    async def unsubscribe_all(self):
        """모든 구독 해제"""
        try:
            # 모든 구독을 비활성화
            for subscription in self.subscriptions.values():
                subscription.active = False
            
            # 구독 정보 모두 제거
            subscription_ids = list(self.subscriptions.keys())
            for subscription_id in subscription_ids:
                await self.unsubscribe(subscription_id)
            
            Logger.info("모든 구독 해제 완료")
            
        except Exception as e:
            Logger.error(f"모든 구독 해제 중 오류: {e}")
    
    async def _deliver_to_subscribers(self, event: Event):
        """구독자들에게 이벤트 전달"""
        try:
            for subscription in self.subscriptions.values():
                if not subscription.active:
                    continue
                
                # 이벤트 타입 필터링
                if event.event_type not in subscription.event_types:
                    continue
                
                # 조건 필터링
                if subscription.filter_conditions:
                    if not self._match_filter_conditions(event, subscription.filter_conditions):
                        continue
                
                # 구독자 큐에 이벤트 추가
                subscriber_queue_key = self.subscriber_key_pattern.format(
                    subscriber_id=subscription.subscriber_id
                )
                
                event_payload = {
                    "subscription_id": subscription.id,
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
                
                await self.redis_client.list_push_right(
                    subscriber_queue_key,
                    json.dumps(event_payload)
                )
                
                # 큐 크기 제한 (최대 10000개)
                await self.redis_client.list_trim(subscriber_queue_key, -10000, -1)
                
        except Exception as e:
            Logger.error(f"구독자 이벤트 전달 실패: {e}")
    
    async def _process_subscriber_events(self, subscription: Subscription):
        """구독자별 이벤트 처리"""
        subscriber_queue_key = self.subscriber_key_pattern.format(
            subscriber_id=subscription.subscriber_id
        )
        
        while subscription.active and subscription.id in self.subscriptions:
            try:
                # Redis 클라이언트 연결 확인
                if not hasattr(self.redis_client, '_client') or self.redis_client._client is None:
                    Logger.warn(f"Redis client connection lost for subscriber {subscription.subscriber_id}, reconnecting...")
                    await asyncio.sleep(5)
                    continue
                
                # 큐에서 이벤트 가져오기 (blocking pop은 추후 구현)
                event_data = await self.redis_client.list_pop_left(subscriber_queue_key)
                
                if not event_data:
                    # 메시지가 없으면 짧은 시간 대기
                    await asyncio.sleep(1)
                    continue
                
                event_payload = json.loads(event_data)
                event_info = event_payload["event"]
                
                # Event 객체 재구성
                event = Event(
                    id=event_info["id"],
                    event_type=EventType(event_info["event_type"]),
                    source=event_info["source"],
                    data=event_info["data"],
                    timestamp=datetime.fromisoformat(event_info["timestamp"]),
                    correlation_id=event_info.get("correlation_id"),
                    version=event_info.get("version", "1.0"),
                    metadata=event_info.get("metadata")
                )
                
                # 콜백 실행
                try:
                    success = False
                    if asyncio.iscoroutinefunction(subscription.callback):
                        success = await subscription.callback(event)
                    else:
                        success = subscription.callback(event)
                    
                    if success:
                        self.event_stats["delivered"] += 1
                        Logger.debug(f"이벤트 처리 완료: {event.id} -> {subscription.subscriber_id}")
                    else:
                        Logger.warn(f"이벤트 처리 실패: {event.id} -> {subscription.subscriber_id}")
                        
                except Exception as e:
                    Logger.error(f"이벤트 콜백 실행 실패: {event.id} - {e}")
                    
            except Exception as e:
                Logger.error(f"구독자 이벤트 처리 오류: {subscription.subscriber_id} - {e}")
                await asyncio.sleep(1)
    
    def _match_filter_conditions(self, event: Event, conditions: Dict[str, Any]) -> bool:
        """필터 조건 매칭"""
        try:
            for key, expected_value in conditions.items():
                if key == "source":
                    if event.source != expected_value:
                        return False
                elif key == "data":
                    # 데이터 필드별 조건 확인
                    for data_key, data_value in expected_value.items():
                        if event.data.get(data_key) != data_value:
                            return False
                elif key == "correlation_id":
                    if event.correlation_id != expected_value:
                        return False
            
            return True
            
        except Exception as e:
            Logger.error(f"필터 조건 매칭 실패: {e}")
            return False
    
    async def get_event_history(self, event_type: EventType, limit: int = 100) -> List[Event]:
        """이벤트 히스토리 조회"""
        try:
            history_key = self.event_history_pattern.format(event_type=event_type.value)
            event_data_list = await self.redis_client.list_range(history_key, 0, limit - 1)
            
            events = []
            for event_data_str in event_data_list:
                event_data = json.loads(event_data_str)
                event = Event(
                    id=event_data["id"],
                    event_type=EventType(event_data["event_type"]),
                    source=event_data["source"],
                    data=json.loads(event_data["data"]),
                    timestamp=datetime.fromisoformat(event_data["timestamp"]),
                    correlation_id=event_data.get("correlation_id"),
                    version=event_data.get("version", "1.0"),
                    metadata=json.loads(event_data.get("metadata", "{}"))
                )
                events.append(event)
            
            return events
            
        except Exception as e:
            Logger.error(f"이벤트 히스토리 조회 실패: {event_type.value} - {e}")
            return []
    
    async def get_subscription_stats(self) -> Dict[str, Any]:
        """구독 통계 조회"""
        try:
            stats = {
                "total_subscriptions": len(self.subscriptions),
                "active_subscribers": len(self.active_subscribers),
                "event_stats": self.event_stats.copy(),
                "subscribers": {}
            }
            
            for subscription in self.subscriptions.values():
                subscriber_queue_key = self.subscriber_key_pattern.format(
                    subscriber_id=subscription.subscriber_id
                )
                queue_length = await self.redis_client.list_length(subscriber_queue_key)
                
                stats["subscribers"][subscription.subscriber_id] = {
                    "event_types": [et.value for et in subscription.event_types],
                    "pending_events": queue_length,
                    "active": subscription.active
                }
            
            return stats
            
        except Exception as e:
            Logger.error(f"구독 통계 조회 실패: {e}")
            return {}


class EventQueueManager:
    """이벤트큐 매니저"""
    
    def __init__(self, cache_service):
        self.cache_service = cache_service
        self.event_queue = RedisCacheEventQueue(cache_service)
        
        # 이벤트 핸들러 레지스트리
        self.event_handlers: Dict[EventType, List[Callable[[Event], bool]]] = {}
        
        # 시스템 구독 ID
        self.system_subscription_id: Optional[str] = None
    
    async def initialize(self):
        """이벤트큐 매니저 초기화"""
        try:
            # 시스템 내부 이벤트 처리를 위한 구독 생성
            system_subscription = Subscription(
                id="system_internal",
                subscriber_id="system",
                event_types=set(EventType),  # 모든 이벤트 타입 구독
                callback=self._handle_system_event
            )
            
            await self.event_queue.subscribe(system_subscription)
            self.system_subscription_id = system_subscription.id
            
            Logger.info("EventQueueManager 초기화 완료")
            
        except Exception as e:
            Logger.error(f"EventQueueManager 초기화 실패: {e}")
    
    async def publish_event(self, event_type: EventType, source: str, 
                          data: Dict[str, Any], correlation_id: Optional[str] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> bool:
        """이벤트 발행"""
        event = Event(
            id=str(uuid.uuid4()),
            event_type=event_type,
            source=source,
            data=data,
            timestamp=datetime.now(),
            correlation_id=correlation_id,
            metadata=metadata
        )
        
        return await self.event_queue.publish(event)
    
    async def subscribe_events(self, subscriber_id: str, event_types: List[EventType],
                             callback: Callable[[Event], bool],
                             filter_conditions: Optional[Dict[str, Any]] = None) -> str:
        """이벤트 구독"""
        subscription = Subscription(
            id=str(uuid.uuid4()),
            subscriber_id=subscriber_id,
            event_types=set(event_types),
            callback=callback,
            filter_conditions=filter_conditions
        )
        
        success = await self.event_queue.subscribe(subscription)
        if success:
            return subscription.id
        else:
            raise RuntimeError(f"이벤트 구독 실패: {subscriber_id}")
    
    def register_event_handler(self, event_type: EventType, handler: Callable[[Event], bool]):
        """이벤트 핸들러 등록 (시스템 내부용)"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
        Logger.info(f"이벤트 핸들러 등록: {event_type.value}")
    
    async def _handle_system_event(self, event: Event) -> bool:
        """시스템 이벤트 처리"""
        try:
            handlers = self.event_handlers.get(event.event_type, [])
            
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    Logger.error(f"시스템 이벤트 핸들러 실행 실패: {event.id} - {e}")
            
            return True
            
        except Exception as e:
            Logger.error(f"시스템 이벤트 처리 실패: {event.id} - {e}")
            return False
    
    async def get_event_history(self, event_type: EventType, limit: int = 100) -> List[Event]:
        """이벤트 히스토리 조회"""
        return await self.event_queue.get_event_history(event_type, limit)
    
    async def get_stats(self) -> Dict[str, Any]:
        """통계 조회"""
        return await self.event_queue.get_subscription_stats()
    
    async def stop_all_subscribers(self):
        """모든 구독자 중지"""
        try:
            # 모든 구독을 중지
            await self.event_queue.unsubscribe_all()
            Logger.info("모든 이벤트 구독자 중지 완료")
            
        except Exception as e:
            Logger.error(f"이벤트 구독자 중지 중 오류: {e}")
    
    async def shutdown(self):
        """EventQueueManager 종료"""
        try:
            Logger.info("EventQueueManager 정리 시작")
            await self.stop_all_subscribers()
            Logger.info("EventQueueManager 정리 완료")
            
        except Exception as e:
            Logger.error(f"EventQueueManager 종료 중 오류: {e}")


# 전역 이벤트큐 매니저 인스턴스
_event_queue_manager: Optional[EventQueueManager] = None

def get_event_queue_manager() -> EventQueueManager:
    """전역 이벤트큐 매니저 인스턴스 반환"""
    global _event_queue_manager
    if _event_queue_manager is None:
        raise RuntimeError("EventQueueManager가 초기화되지 않았습니다")
    return _event_queue_manager

async def initialize_event_queue_manager(redis_client: RedisCacheClient):
    """전역 이벤트큐 매니저 초기화"""
    global _event_queue_manager
    _event_queue_manager = EventQueueManager(redis_client)
    await _event_queue_manager.initialize()