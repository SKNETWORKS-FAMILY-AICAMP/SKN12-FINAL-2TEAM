import json
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from service.core.logger import Logger

class OutboxEventStatus(Enum):
    """아웃박스 이벤트 상태"""
    PENDING = "pending"      # 발행 대기
    PUBLISHED = "published"  # 발행 완료
    FAILED = "failed"        # 발행 실패
    RETRY = "retry"          # 재시도 대기

@dataclass
class OutboxEvent:
    """아웃박스 이벤트"""
    id: str
    event_type: str
    aggregate_id: str
    aggregate_type: str
    event_data: Dict[str, Any]
    status: OutboxEventStatus = OutboxEventStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None

class OutboxRepository:
    """아웃박스 이벤트 저장소 (샤딩 지원)"""
    
    def __init__(self, db_service):
        self.db_service = db_service
    
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
    
    async def get_pending_events_from_shard(self, shard_id: int, limit: int = 100) -> List[OutboxEvent]:
        """특정 샤드에서 발행 대기 중인 이벤트 조회"""
        try:
            query = """
                SELECT id, event_type, aggregate_id, aggregate_type, event_data, 
                       status, retry_count, max_retries, created_at, updated_at, published_at
                FROM outbox_events 
                WHERE status IN ('pending', 'retry')
                ORDER BY created_at ASC
                LIMIT %s
            """
            
            result = await self.db_service.call_shard_read_query(shard_id, query, (limit,))
            
            events = []
            for row in result:
                event = OutboxEvent(
                    id=row['id'],
                    event_type=row['event_type'],
                    aggregate_id=row['aggregate_id'],
                    aggregate_type=row['aggregate_type'],
                    event_data=json.loads(row['event_data']),
                    status=OutboxEventStatus(row['status']),
                    retry_count=row['retry_count'],
                    max_retries=row['max_retries'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    published_at=row['published_at']
                )
                events.append(event)
            
            return events
            
        except Exception as e:
            Logger.error(f"샤드 {shard_id} 대기 중인 이벤트 조회 실패: {e}")
            return []
    
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
    
    async def update_event_status(self, event_id: str, status: OutboxEventStatus, 
                                retry_count: Optional[int] = None) -> bool:
        """이벤트 상태 업데이트"""
        try:
            if status == OutboxEventStatus.PUBLISHED:
                query = """
                    UPDATE outbox_events 
                    SET status = %s, published_at = %s, updated_at = %s
                    WHERE id = %s
                """
                values = (status.value, datetime.now(), datetime.now(), event_id)
            else:
                query = """
                    UPDATE outbox_events 
                    SET status = %s, retry_count = %s, updated_at = %s
                    WHERE id = %s
                """
                values = (status.value, retry_count or 0, datetime.now(), event_id)
            
            await self.db_service.call_global_procedure_update(query, values)
            Logger.debug(f"아웃박스 이벤트 상태 업데이트: {event_id} -> {status.value}")
            return True
            
        except Exception as e:
            Logger.error(f"이벤트 상태 업데이트 실패: {event_id} - {e}")
            return False
    
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

class OutboxEventPublisher:
    """아웃박스 이벤트 발행자"""
    
    def __init__(self, repository: OutboxRepository):
        self.repository = repository
        self.event_handlers = {}
    
    def register_handler(self, event_type: str, handler):
        """이벤트 핸들러 등록"""
        self.event_handlers[event_type] = handler
        Logger.info(f"이벤트 핸들러 등록: {event_type}")
    
    async def publish_pending_events(self) -> Dict[str, int]:
        """대기 중인 이벤트 발행"""
        stats = {
            "processed": 0,
            "published": 0,
            "failed": 0,
            "retried": 0
        }
        
        try:
            # 모든 샤드에서 대기 중인 이벤트를 가져와서 플랫 리스트로 변환
            all_pending_dict = await self.repository.get_all_pending_events()
            pending_events = []
            for shard_events in all_pending_dict.values():
                pending_events.extend(shard_events)
            
            for event in pending_events:
                stats["processed"] += 1
                
                try:
                    success = await self._publish_single_event(event)
                    
                    if success:
                        await self.repository.update_event_status(
                            event.id, 
                            OutboxEventStatus.PUBLISHED
                        )
                        stats["published"] += 1
                        Logger.info(f"이벤트 발행 성공: {event.id}")
                    else:
                        await self._handle_publish_failure(event, stats)
                        
                except Exception as e:
                    Logger.error(f"이벤트 발행 중 오류: {event.id} - {e}")
                    await self._handle_publish_failure(event, stats)
            
            if stats["processed"] > 0:
                Logger.info(f"아웃박스 이벤트 발행 완료: {stats}")
            
            return stats
            
        except Exception as e:
            Logger.error(f"아웃박스 이벤트 발행 실패: {e}")
            return stats
    
    async def _publish_single_event(self, event: OutboxEvent) -> bool:
        """단일 이벤트 발행"""
        handler = self.event_handlers.get(event.event_type)
        
        if not handler:
            Logger.warn(f"핸들러를 찾을 수 없음: {event.event_type}")
            return False
        
        try:
            # 핸들러가 코루틴인지 확인
            if hasattr(handler, '__call__'):
                if asyncio.iscoroutinefunction(handler):
                    return await handler(event)
                else:
                    return handler(event)
            
            return False
            
        except Exception as e:
            Logger.error(f"이벤트 핸들러 실행 실패: {event.event_type} - {e}")
            return False
    
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

class OutboxService:
    """아웃박스 패턴 서비스 (트랜잭션 일관성 보장)"""
    
    def __init__(self, db_service):
        self.db_service = db_service
        self.repository = OutboxRepository(db_service)
        self.publisher = OutboxEventPublisher(self.repository)
    
    async def publish_event_in_transaction(self, event_type: str, aggregate_id: str, 
                                         aggregate_type: str, event_data: Dict[str, Any],
                                         business_operation=None) -> bool:
        """
        비즈니스 로직과 이벤트 발행을 원자적으로 처리
        
        Args:
            event_type: 이벤트 타입
            aggregate_id: 집계 ID
            aggregate_type: 집계 타입
            event_data: 이벤트 데이터
            business_operation: 비즈니스 로직 (코루틴 함수)
        """
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
    
    def register_event_handler(self, event_type: str, handler):
        """이벤트 핸들러 등록"""
        self.publisher.register_handler(event_type, handler)
    
    async def process_outbox_events(self) -> Dict[str, int]:
        """아웃박스 이벤트 처리"""
        return await self.publisher.publish_pending_events()
    
    async def cleanup_old_events(self, days: int = 7) -> int:
        """오래된 이벤트 정리"""
        return await self.repository.cleanup_old_events(days)