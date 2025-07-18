"""
메시지큐 시스템 - 메시지의 안전한 저장과 전달 담당
"""

import json
import uuid
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod

from service.core.logger import Logger
from service.cache.redis_cache_client import RedisCacheClient
from service.lock.distributed_lock import DistributedLockManager


class MessageStatus(Enum):
    """메시지 상태"""
    PENDING = "pending"      # 처리 대기
    PROCESSING = "processing"  # 처리 중
    COMPLETED = "completed"    # 처리 완료
    FAILED = "failed"         # 처리 실패
    RETRY = "retry"           # 재시도 대기


class MessagePriority(Enum):
    """메시지 우선순위"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class QueueMessage:
    """큐 메시지"""
    id: str
    queue_name: str
    payload: Dict[str, Any]
    message_type: str
    priority: MessagePriority = MessagePriority.NORMAL
    status: MessageStatus = MessageStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    created_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None  # 지연 실행
    processed_at: Optional[datetime] = None
    partition_key: Optional[str] = None  # 순서 보장용


class IMessageQueue(ABC):
    """메시지큐 인터페이스"""
    
    @abstractmethod
    async def enqueue(self, message: QueueMessage) -> bool:
        """메시지 큐에 추가"""
        pass
    
    @abstractmethod
    async def dequeue(self, queue_name: str, consumer_id: str) -> Optional[QueueMessage]:
        """메시지 큐에서 가져오기"""
        pass
    
    @abstractmethod
    async def ack(self, message_id: str, consumer_id: str) -> bool:
        """메시지 처리 완료 확인"""
        pass
    
    @abstractmethod
    async def nack(self, message_id: str, consumer_id: str, retry: bool = True) -> bool:
        """메시지 처리 실패 처리"""
        pass


class RedisCacheMessageQueue(IMessageQueue):
    """CacheService를 사용하는 Redis 메시지큐"""
    
    def __init__(self, cache_service):
        self.cache_service = cache_service
        
        # Redis 키 패턴들
        self.message_key_pattern = "mq:message:{message_id}"
        self.queue_key_pattern = "mq:queue:{queue_name}"
        self.priority_queue_pattern = "mq:priority:{queue_name}:{priority}"
        self.delayed_key_pattern = "mq:delayed:messages"
        self.processing_key_pattern = "mq:processing:{queue_name}"
        self.dlq_key_pattern = "mq:dlq:{queue_name}"
    
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
    
    async def enqueue(self, message: QueueMessage) -> bool:
        """메시지 큐에 추가"""
        async def _enqueue_operation(client, msg):
            # 메시지 ID 생성 (아직 없는 경우)
            if not msg.id:
                msg.id = str(uuid.uuid4())
            
            # 메시지 직렬화 및 저장 (모든 값을 문자열로 변환)
            message_data = {
                "id": str(msg.id),
                "queue_name": str(msg.queue_name),
                "payload": json.dumps(msg.payload),
                "message_type": str(msg.message_type),
                "priority": str(msg.priority.value),
                "created_at": str(msg.created_at.isoformat() if msg.created_at else datetime.now().isoformat()),
                "retry_count": str(msg.retry_count),
                "max_retries": str(msg.max_retries),
                "partition_key": str(msg.partition_key or "")
            }
            
            message_key = self.message_key_pattern.format(message_id=msg.id)
            if message_data:  # 빈 딕셔너리가 아닌지 확인
                await client.set_hash_all(message_key, message_data)
            
            # 지연 실행 메시지인 경우
            if msg.scheduled_at and msg.scheduled_at > datetime.now():
                timestamp = msg.scheduled_at.timestamp()
                await client.sorted_set_add(self.delayed_key_pattern, timestamp, msg.id)
                return True
            
            # 파티션별 큐에 추가
            if msg.partition_key:
                partition_queue_key = f"mq:partition:{msg.queue_name}:{hash(msg.partition_key) % 16}"
                await client.list_push_right(partition_queue_key, msg.id)
            else:
                # 우선순위별 큐에 추가
                priority_queue_key = self.priority_queue_pattern.format(
                    queue_name=msg.queue_name,
                    priority=msg.priority.value
                )
                await client.list_push_right(priority_queue_key, msg.id)
            
            return True
        
        result = await self._execute_redis_operation("enqueue", _enqueue_operation, message)
        return result if result is not None else False
    
    async def dequeue(self, queue_name: str, consumer_id: str, 
                     visibility_timeout: int = 300) -> Optional[QueueMessage]:
        """메시지 큐에서 제거하여 반환"""
        async def _dequeue_operation(client, q_name, c_id, timeout):
            # 우선순위 순서대로 확인 (CRITICAL=4, HIGH=3, NORMAL=2, LOW=1)
            for priority in [4, 3, 2, 1]:
                priority_queue_key = self.priority_queue_pattern.format(
                    queue_name=q_name, priority=priority
                )
                
                message_id = await client.list_pop_left(priority_queue_key)
                if message_id:
                    # 메시지 상세 정보 가져오기
                    message_key = self.message_key_pattern.format(message_id=message_id)
                    message_data = await client.get_hash_all(message_key)
                    
                    if not message_data:
                        continue
                    
                    # 처리 중 상태로 이동
                    processing_key = self.processing_key_pattern.format(queue_name=q_name)
                    processing_info = {
                        "message_id": str(message_id),
                        "consumer_id": str(c_id),
                        "started_at": datetime.now().isoformat(),
                        "visibility_timeout": str(timeout)
                    }
                    if processing_info:  # 빈 딕셔너리가 아닌지 확인
                        await client.set_hash_all(f"{processing_key}:{message_id}", processing_info)
                    
                    # QueueMessage 객체로 변환
                    return QueueMessage(
                        id=message_data["id"],
                        queue_name=message_data["queue_name"],
                        payload=json.loads(message_data["payload"]),
                        message_type=message_data["message_type"],
                        priority=MessagePriority(int(message_data["priority"])),
                        created_at=datetime.fromisoformat(message_data["created_at"]),
                        retry_count=int(message_data.get("retry_count", 0)),
                        max_retries=int(message_data.get("max_retries", 3)),
                        partition_key=message_data.get("partition_key") or None
                    )
            
            return None
        
        return await self._execute_redis_operation("dequeue", _dequeue_operation, queue_name, consumer_id, visibility_timeout)
    
    async def ack(self, message: QueueMessage, consumer_id: str) -> bool:
        """메시지 처리 완료 확인"""
        async def _ack_operation(client, msg, c_id):
            # 처리 중 상태에서 제거
            processing_key = self.processing_key_pattern.format(queue_name=msg.queue_name)
            await client.delete(f"{processing_key}:{msg.id}")
            
            # 메시지 데이터 삭제
            message_key = self.message_key_pattern.format(message_id=msg.id)
            await client.delete(message_key)
            
            return True
        
        return await self._execute_redis_operation("ack", _ack_operation, message, consumer_id)
    
    async def nack(self, message: QueueMessage, consumer_id: str, 
                  requeue: bool = True) -> bool:
        """메시지 처리 실패 처리"""
        async def _nack_operation(client, msg, c_id, should_requeue):
            # 처리 중 상태에서 제거
            processing_key = self.processing_key_pattern.format(queue_name=msg.queue_name)
            await client.delete(f"{processing_key}:{msg.id}")
            
            if should_requeue and msg.retry_count < msg.max_retries:
                # 재시도 카운트 증가 후 재큐잉
                msg.retry_count += 1
                message_key = self.message_key_pattern.format(message_id=msg.id)
                await client.set_hash_field(message_key, "retry_count", str(msg.retry_count))
                
                # 우선순위 큐에 다시 추가
                priority_queue_key = self.priority_queue_pattern.format(
                    queue_name=msg.queue_name,
                    priority=msg.priority.value
                )
                await client.list_push_right(priority_queue_key, msg.id)
            else:
                # DLQ로 이동
                dlq_key = self.dlq_key_pattern.format(queue_name=msg.queue_name)
                dlq_message = {
                    "message_id": msg.id,
                    "original_queue": msg.queue_name,
                    "failed_at": datetime.now().isoformat(),
                    "consumer_id": c_id,
                    "retry_count": str(msg.retry_count)
                }
                await client.list_push_right(dlq_key, json.dumps(dlq_message))
                
                # 원본 메시지 삭제
                message_key = self.message_key_pattern.format(message_id=msg.id)
                await client.delete(message_key)
            
            return True
        
        return await self._execute_redis_operation("nack", _nack_operation, message, consumer_id, requeue)
    
    async def process_delayed_messages(self) -> int:
        """지연 실행 시간이 된 메시지들을 큐로 이동"""
        async def _process_delayed_operation(client):
            now_timestamp = datetime.now().timestamp()
            
            # 현재 시간 이전의 메시지들 조회
            delayed_messages = await client.sorted_set_range_by_score(
                self.delayed_key_pattern, 0, now_timestamp, 0, 100
            )
            
            processed_count = 0
            
            for message_id in delayed_messages:
                try:
                    # 메시지 상세 정보 조회
                    message_key = self.message_key_pattern.format(message_id=message_id)
                    message_data = await client.get_hash_all(message_key)
                    
                    if not message_data:
                        # 메시지가 없으면 delayed set에서 제거
                        await client.sorted_set_remove(self.delayed_key_pattern, message_id)
                        continue
                    
                    # 메시지를 적절한 큐로 이동
                    message = QueueMessage(
                        id=message_data["id"],
                        queue_name=message_data["queue_name"],
                        payload=json.loads(message_data["payload"]),
                        message_type=message_data["message_type"],
                        priority=MessagePriority(int(message_data["priority"])),
                        retry_count=int(message_data.get("retry_count", 0)),
                        max_retries=int(message_data.get("max_retries", 3)),
                        partition_key=message_data.get("partition_key")
                    )
                    
                    # 우선순위/파티션 큐에 추가
                    if message.partition_key:
                        partition_queue_key = f"mq:partition:{message.queue_name}:{hash(message.partition_key) % 16}"
                        await client.list_push_right(partition_queue_key, message.id)
                    else:
                        priority_queue_key = self.priority_queue_pattern.format(
                            queue_name=message.queue_name,
                            priority=message.priority.value
                        )
                        await client.list_push_right(priority_queue_key, message.id)
                    
                    # delayed sorted set에서 제거
                    await client.sorted_set_remove(self.delayed_key_pattern, message_id)
                    processed_count += 1
                    
                except Exception as e:
                    Logger.error(f"지연 메시지 처리 실패: {message_id} - {e}")
            
            return processed_count
        
        result = await self._execute_redis_operation("process_delayed_messages", _process_delayed_operation)
        return result if result is not None else 0
    
    async def get_queue_stats(self, queue_name: str) -> Dict[str, Any]:
        """큐 통계 조회"""
        async def _get_stats_operation(client, q_name):
            stats = {"queue_name": q_name}
            
            # 우선순위별 큐 길이
            for priority in [1, 2, 3, 4]:
                priority_queue_key = self.priority_queue_pattern.format(
                    queue_name=q_name, priority=priority
                )
                length = await client.list_length(priority_queue_key)
                stats[f"priority_{priority}_count"] = length
            
            # 처리 중인 메시지 수
            processing_key = self.processing_key_pattern.format(queue_name=q_name)
            processing_keys = await client.scan_keys(f"{processing_key}:*")
            stats["processing_count"] = len(processing_keys)
            
            # DLQ 메시지 수
            dlq_key = self.dlq_key_pattern.format(queue_name=q_name)
            stats["dlq_count"] = await client.list_length(dlq_key)
            
            # 지연 메시지 수
            delayed_count = await client.sorted_set_length(self.delayed_key_pattern)
            stats["delayed_count"] = delayed_count
            
            return stats
        
        result = await self._execute_redis_operation("get_queue_stats", _get_stats_operation, queue_name)
        return result if result is not None else {}


class MessageQueueManager:
    """메시지큐 매니저"""
    
    def __init__(self, cache_service):
        self.cache_service = cache_service
        # MessageQueue를 CacheService 사용하도록 수정
        self.message_queue = RedisCacheMessageQueue(cache_service)
        self.consumers: Dict[str, 'MessageConsumer'] = {}
    
    async def create_queue(self, queue_name: str, config: Optional[Dict[str, Any]] = None):
        """큐 생성 및 설정"""
        try:
            default_config = {
                "max_consumers": 10,
                "visibility_timeout": 300,  # 5분
                "message_retention": 86400   # 24시간
            }
            
            if config:
                default_config.update(config)
            
            # 큐 설정 저장
            config_key = f"mq:config:{queue_name}"
            async with self.cache_service.get_client() as client:
                await client.set_hash_all(config_key, default_config)
            
            Logger.info(f"메시지큐 생성: {queue_name}")
            
        except Exception as e:
            Logger.error(f"메시지큐 생성 실패: {queue_name} - {e}")
    
    async def register_consumer(self, queue_name: str, consumer_id: str, 
                             handler: Callable[[QueueMessage], bool]) -> 'MessageConsumer':
        """소비자 등록"""
        consumer = MessageConsumer(
            queue_name=queue_name,
            consumer_id=consumer_id,
            message_queue=self.message_queue,
            handler=handler
        )
        
        self.consumers[f"{queue_name}:{consumer_id}"] = consumer
        Logger.info(f"메시지 소비자 등록: {queue_name}:{consumer_id}")
        
        return consumer
    
    async def stop_all_consumers(self):
        """모든 소비자 중지"""
        try:
            for consumer_key, consumer in self.consumers.items():
                try:
                    await consumer.stop()
                    Logger.info(f"소비자 중지 완료: {consumer_key}")
                except Exception as e:
                    Logger.error(f"소비자 중지 중 오류: {consumer_key} - {e}")
            
            self.consumers.clear()
            Logger.info("모든 소비자 중지 완료")
            
        except Exception as e:
            Logger.error(f"소비자 중지 중 오류: {e}")
    
    async def start_delayed_message_processor(self):
        """지연 메시지 처리기 시작"""
        async def process_delayed():
            while True:
                try:
                    await self.message_queue.process_delayed_messages()
                    await asyncio.sleep(10)  # 10초마다 확인
                except Exception as e:
                    Logger.error(f"지연 메시지 처리기 오류: {e}")
                    await asyncio.sleep(30)
        
        asyncio.create_task(process_delayed())
        Logger.info("지연 메시지 처리기 시작")


class MessageConsumer:
    """메시지 소비자"""
    
    def __init__(self, queue_name: str, consumer_id: str, 
                 message_queue: IMessageQueue, handler: Callable[[QueueMessage], bool]):
        self.queue_name = queue_name
        self.consumer_id = consumer_id
        self.message_queue = message_queue
        self.handler = handler
        self.running = False
        self.task: Optional[asyncio.Task] = None
    
    async def start(self):
        """소비자 시작"""
        if self.running:
            return
        
        self.running = True
        self.task = asyncio.create_task(self._consume_loop())
        Logger.info(f"메시지 소비자 시작: {self.queue_name}:{self.consumer_id}")
    
    async def stop(self):
        """소비자 중지"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        Logger.info(f"메시지 소비자 중지: {self.queue_name}:{self.consumer_id}")
    
    async def _consume_loop(self):
        """메시지 소비 루프"""
        while self.running:
            try:
                message = await self.message_queue.dequeue(self.queue_name, self.consumer_id)
                
                if message:
                    success = False
                    try:
                        # 핸들러 실행
                        if asyncio.iscoroutinefunction(self.handler):
                            success = await self.handler(message)
                        else:
                            success = self.handler(message)
                        
                        if success:
                            await self.message_queue.ack(message, self.consumer_id)
                        else:
                            await self.message_queue.nack(message, self.consumer_id)
                            
                    except Exception as e:
                        Logger.error(f"메시지 처리 중 오류: {message.id} - {e}")
                        await self.message_queue.nack(message, self.consumer_id)
                else:
                    # 메시지가 없으면 짧은 시간 대기
                    await asyncio.sleep(1)
                    
            except Exception as e:
                Logger.error(f"메시지 소비 루프 오류: {e}")
                await asyncio.sleep(5)