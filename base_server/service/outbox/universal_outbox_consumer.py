"""
Universal Outbox 컨슈머 - SQL 프로시저 기반
분산 환경에서 이벤트 발행/처리/정리를 담당
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass

from service.core.logger import Logger
from service.service_container import ServiceContainer
from service.lock.lock_service import LockService
from service.scheduler.scheduler_service import SchedulerService
from service.scheduler.base_scheduler import ScheduleJob, ScheduleType
from service.queue.queue_service import QueueService
from service.queue.message_queue import QueueMessage, MessagePriority


class EventDomain(Enum):
    """이벤트 도메인"""
    CHAT = "chat"
    PORTFOLIO = "portfolio"
    MARKET = "market"
    NOTIFICATION = "notification"
    SIGNAL = "signal"


@dataclass 
class OutboxEventHandler:
    """이벤트 핸들러 등록"""
    domain: EventDomain
    event_type: str
    handler: Callable[[Dict[str, Any]], bool]


class UniversalOutboxConsumer:
    """Universal Outbox 컨슈머 - 분산 환경용"""
    
    _initialized: bool = False
    _event_handlers: Dict[str, Dict[str, Callable]] = {}
    _consumer_tasks: List[asyncio.Task] = []
    _scheduler_job_ids: List[str] = []
    
    # 설정값
    BATCH_SIZE = 50
    POLL_INTERVAL = 5  # 5초마다 폴링
    MAX_RETRIES = 3
    CLEANUP_RETENTION_DAYS = 7
    
    @classmethod
    async def init(cls):
        """컨슈머 초기화"""
        if cls._initialized:
            Logger.warn("UniversalOutboxConsumer 이미 초기화됨")
            return
            
        try:
            # 기본 이벤트 핸들러 등록
            await cls._register_default_handlers()
            
            # 각 도메인별 컨슈머 태스크 시작
            for domain in EventDomain:
                task = asyncio.create_task(cls._consume_domain_events(domain))
                cls._consumer_tasks.append(task)
                Logger.info(f"✅ {domain.value} 도메인 컨슈머 시작")
            
            # 정리 작업 스케줄러 등록
            await cls._register_cleanup_jobs()
            
            cls._initialized = True
            Logger.info("✅ UniversalOutboxConsumer 초기화 완료")
            
        except Exception as e:
            Logger.error(f"❌ UniversalOutboxConsumer 초기화 실패: {e}")
            raise
    
    @classmethod
    async def _register_default_handlers(cls):
        """기본 이벤트 핸들러 등록"""
        
        # 채팅 이벤트 핸들러
        cls.register_handler(
            EventDomain.CHAT,
            "room_created",
            cls._handle_chat_room_created
        )
        cls.register_handler(
            EventDomain.CHAT,
            "message_sent", 
            cls._handle_chat_message_sent
        )
        
        # 포트폴리오 이벤트 핸들러
        cls.register_handler(
            EventDomain.PORTFOLIO,
            "portfolio_updated",
            cls._handle_portfolio_updated
        )
        
        # 시그널 이벤트 핸들러
        cls.register_handler(
            EventDomain.SIGNAL,
            "signal_generated",
            cls._handle_signal_generated
        )
        
        # 알림 이벤트 핸들러
        cls.register_handler(
            EventDomain.NOTIFICATION,
            "notification_created",
            cls._handle_notification_created
        )
    
    @classmethod
    def register_handler(cls, domain: EventDomain, event_type: str, handler: Callable):
        """이벤트 핸들러 등록"""
        if domain.value not in cls._event_handlers:
            cls._event_handlers[domain.value] = {}
        
        cls._event_handlers[domain.value][event_type] = handler
        Logger.info(f"이벤트 핸들러 등록: {domain.value}.{event_type}")
    
    @classmethod
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
    
    @classmethod
    async def _process_pending_events(cls, domain: str) -> int:
        """도메인별 pending 이벤트 처리"""
        try:
            db_service = ServiceContainer.get_database_service()
            processed_count = 0
            
            # 활성 샤드 목록 조회
            active_shards = await cls._get_active_shard_ids(db_service)
            if not active_shards:
                return 0
            
            # 각 샤드에서 pending 이벤트 조회 및 처리
            for shard_id in active_shards:
                try:
                    # 샤드별 pending 이벤트 조회 (SQL 프로시저 사용)
                    result = await db_service.call_shard_procedure(
                        shard_id,
                        "fp_universal_outbox_get_pending",
                        (domain, cls.BATCH_SIZE)
                    )
                    
                    if not result:
                        continue
                    
                    # 이벤트 배치 처리
                    for event_row in result:
                        try:
                            await cls._process_single_event(shard_id, event_row)
                            processed_count += 1
                            
                        except Exception as e:
                            Logger.error(f"이벤트 처리 실패: {event_row.get('id')} - {e}")
                            await cls._mark_event_failed(db_service, shard_id, event_row, str(e))
                
                except Exception as e:
                    Logger.error(f"샤드 {shard_id} 이벤트 처리 실패: {e}")
                    continue
            
            return processed_count
            
        except Exception as e:
            Logger.error(f"도메인 {domain} 이벤트 처리 실패: {e}")
            return 0
    
    @classmethod
    async def _process_single_event(cls, shard_id: int, event_row: Dict[str, Any]):
        """개별 이벤트 처리"""
        event_id = event_row.get('id')
        domain = event_row.get('domain')
        event_type = event_row.get('event_type')
        event_data = json.loads(event_row.get('event_data', '{}'))
        
        Logger.info(f"이벤트 처리 시작: {domain}.{event_type} ({event_id})")
        
        try:
            # 등록된 핸들러로 이벤트 처리
            if domain in cls._event_handlers and event_type in cls._event_handlers[domain]:
                handler = cls._event_handlers[domain][event_type]
                
                # 핸들러 실행 (비동기/동기 모두 지원)
                if asyncio.iscoroutinefunction(handler):
                    success = await handler(event_data)
                else:
                    success = handler(event_data)
                
                if success:
                    # 성공 시 published 상태로 변경
                    await cls._mark_event_published(shard_id, event_id)
                    Logger.info(f"✅ 이벤트 처리 성공: {event_id}")
                else:
                    # 실패 시 failed 상태로 변경
                    await cls._mark_event_failed_simple(shard_id, event_id, "Handler returned False")
                    Logger.warn(f"⚠️ 이벤트 처리 실패: {event_id} (핸들러 False 반환)")
            else:
                Logger.warn(f"⚠️ 등록되지 않은 이벤트 타입: {domain}.{event_type}")
                await cls._mark_event_published(shard_id, event_id)  # 스킵하고 published 처리
                
        except Exception as e:
            Logger.error(f"❌ 이벤트 처리 오류: {event_id} - {e}")
            await cls._mark_event_failed_simple(shard_id, event_id, str(e))
            raise
    
    @classmethod
    async def _mark_event_published(cls, shard_id: int, event_id: str):
        """이벤트를 published 상태로 변경"""
        try:
            db_service = ServiceContainer.get_database_service()
            await db_service.call_shard_procedure(
                shard_id,
                "fp_universal_outbox_update_status",
                (event_id, "published", None)
            )
        except Exception as e:
            Logger.error(f"이벤트 published 마킹 실패: {event_id} - {e}")
    
    @classmethod
    async def _mark_event_failed_simple(cls, shard_id: int, event_id: str, error_msg: str):
        """이벤트를 failed 상태로 변경 (간단 버전)"""
        try:
            db_service = ServiceContainer.get_database_service()
            await db_service.call_shard_procedure(
                shard_id,
                "fp_universal_outbox_update_status",
                (event_id, "failed", error_msg)
            )
        except Exception as e:
            Logger.error(f"이벤트 failed 마킹 실패: {event_id} - {e}")
    
    @classmethod
    async def _mark_event_failed(cls, db_service, shard_id: int, event_row: Dict, error_msg: str):
        """이벤트를 failed 상태로 변경 (재시도 고려)"""
        try:
            event_id = event_row.get('id')
            retry_count = int(event_row.get('retry_count', 0))
            max_retries = int(event_row.get('max_retries', cls.MAX_RETRIES))
            
            if retry_count < max_retries:
                # 재시도 가능
                await db_service.call_shard_procedure(
                    shard_id,
                    "fp_universal_outbox_update_status",
                    (event_id, "pending", error_msg)  # pending으로 돌려서 재시도
                )
                Logger.info(f"이벤트 재시도 예약: {event_id} ({retry_count + 1}/{max_retries})")
            else:
                # 최대 재시도 초과 → dead_letter
                await db_service.call_shard_procedure(
                    shard_id,
                    "fp_universal_outbox_update_status",
                    (event_id, "dead_letter", error_msg)
                )
                Logger.error(f"이벤트 dead_letter 처리: {event_id}")
                
        except Exception as e:
            Logger.error(f"이벤트 실패 마킹 실패: {event_row.get('id')} - {e}")
    
    @classmethod
    async def _get_active_shard_ids(cls, db_service) -> List[int]:
        """활성 샤드 ID 목록 조회"""
        try:
            result = await db_service.call_global_procedure(
                "fp_get_active_shard_ids",
                ()
            )
            
            if not result or len(result) < 2:
                return []
            
            # 첫 번째는 상태, 두 번째부터는 샤드 데이터
            proc_result = result[0]
            if proc_result.get('ErrorCode', 1) != 0:
                return []
            
            active_shard_ids = []
            for shard_data in result[1:]:
                shard_id = shard_data.get('shard_id')
                status = shard_data.get('status', '')
                if shard_id and status == 'active':
                    active_shard_ids.append(shard_id)
            
            return active_shard_ids
            
        except Exception as e:
            Logger.error(f"활성 샤드 조회 실패: {e}")
            return []
    
    @classmethod
    async def _register_cleanup_jobs(cls):
        """정리 작업 스케줄러 등록"""
        try:
            # 매일 새벽 2시에 published 이벤트 정리 (7일 후)
            published_cleanup_job = ScheduleJob(
                job_id="outbox_cleanup_published",
                name="Universal Outbox Published 이벤트 정리",
                schedule_type=ScheduleType.DAILY,
                schedule_value="02:00",
                callback=cls._cleanup_published_events,
                use_distributed_lock=True,
                lock_key="outbox:cleanup:published"
            )
            await SchedulerService.add_job(published_cleanup_job)
            cls._scheduler_job_ids.append(published_cleanup_job.job_id)
            
            # 매일 새벽 3시에 failed/dead_letter 이벤트 정리 (30일 후)
            failed_cleanup_job = ScheduleJob(
                job_id="outbox_cleanup_failed",
                name="Universal Outbox Failed 이벤트 정리",
                schedule_type=ScheduleType.DAILY,
                schedule_value="03:00",
                callback=cls._cleanup_failed_events,
                use_distributed_lock=True,
                lock_key="outbox:cleanup:failed"
            )
            await SchedulerService.add_job(failed_cleanup_job)
            cls._scheduler_job_ids.append(failed_cleanup_job.job_id)
            
            # 매주 일요일 새벽 4시에 시퀀스 정리
            sequence_cleanup_job = ScheduleJob(
                job_id="outbox_cleanup_sequences",
                name="Universal Outbox 시퀀스 정리",
                schedule_type=ScheduleType.WEEKLY,
                schedule_value="SUN:04:00",
                callback=cls._cleanup_sequences,
                use_distributed_lock=True,
                lock_key="outbox:cleanup:sequences"
            )
            await SchedulerService.add_job(sequence_cleanup_job)
            cls._scheduler_job_ids.append(sequence_cleanup_job.job_id)
            
            Logger.info("✅ Universal Outbox 정리 작업 스케줄러 등록 완료")
            
        except Exception as e:
            Logger.error(f"❌ Universal Outbox 정리 작업 등록 실패: {e}")
    
    @classmethod
    async def _cleanup_published_events(cls):
        """Published 이벤트 정리"""
        try:
            db_service = ServiceContainer.get_database_service()
            active_shards = await cls._get_active_shard_ids(db_service)
            
            total_deleted = 0
            for shard_id in active_shards:
                try:
                    result = await db_service.call_shard_procedure(
                        shard_id,
                        "fp_universal_outbox_cleanup_published",
                        (cls.CLEANUP_RETENTION_DAYS,)
                    )
                    
                    if result and result[0].get('result') == 'SUCCESS':
                        deleted_count = result[0].get('deleted_count', 0)
                        total_deleted += deleted_count
                        
                except Exception as e:
                    Logger.error(f"샤드 {shard_id} published 정리 실패: {e}")
            
            Logger.info(f"✅ Published 이벤트 정리 완료: {total_deleted}개 삭제")
            
        except Exception as e:
            Logger.error(f"Published 이벤트 정리 실패: {e}")
    
    @classmethod  
    async def _cleanup_failed_events(cls):
        """Failed/Dead Letter 이벤트 정리"""
        try:
            db_service = ServiceContainer.get_database_service()
            active_shards = await cls._get_active_shard_ids(db_service)
            
            total_deleted = 0
            for shard_id in active_shards:
                try:
                    result = await db_service.call_shard_procedure(
                        shard_id,
                        "fp_universal_outbox_cleanup_failed",
                        (30,)  # 30일 후 정리
                    )
                    
                    if result and result[0].get('result') == 'SUCCESS':
                        deleted_count = result[0].get('deleted_count', 0)
                        total_deleted += deleted_count
                        
                except Exception as e:
                    Logger.error(f"샤드 {shard_id} failed 정리 실패: {e}")
            
            Logger.info(f"✅ Failed 이벤트 정리 완료: {total_deleted}개 삭제")
            
        except Exception as e:
            Logger.error(f"Failed 이벤트 정리 실패: {e}")
    
    @classmethod
    async def _cleanup_sequences(cls):
        """사용되지 않는 시퀀스 정리"""
        try:
            db_service = ServiceContainer.get_database_service()
            active_shards = await cls._get_active_shard_ids(db_service)
            
            total_deleted = 0
            for shard_id in active_shards:
                try:
                    result = await db_service.call_shard_procedure(
                        shard_id,
                        "fp_universal_outbox_cleanup_sequences",
                        (90,)  # 90일 후 정리
                    )
                    
                    if result and result[0].get('result') == 'SUCCESS':
                        deleted_count = result[0].get('deleted_count', 0)
                        total_deleted += deleted_count
                        
                except Exception as e:
                    Logger.error(f"샤드 {shard_id} 시퀀스 정리 실패: {e}")
            
            Logger.info(f"✅ 시퀀스 정리 완료: {total_deleted}개 삭제")
            
        except Exception as e:
            Logger.error(f"시퀀스 정리 실패: {e}")
    
    # ===========================================
    # 기본 이벤트 핸들러들
    # ===========================================
    
    @classmethod
    async def _handle_chat_room_created(cls, event_data: Dict[str, Any]) -> bool:
        """채팅방 생성 이벤트 처리"""
        try:
            room_id = event_data.get('room_id')
            account_db_key = event_data.get('account_db_key')
            
            Logger.info(f"채팅방 생성 이벤트 처리: {room_id} (사용자: {account_db_key})")
            
            # WebSocket으로 실시간 알림 전송 (향후 구현)
            # await WebSocketService.broadcast_to_user(account_db_key, {
            #     "type": "room_created",
            #     "data": event_data
            # })
            
            return True
            
        except Exception as e:
            Logger.error(f"채팅방 생성 이벤트 처리 실패: {e}")
            return False
    
    @classmethod
    async def _handle_chat_message_sent(cls, event_data: Dict[str, Any]) -> bool:
        """채팅 메시지 전송 이벤트 처리"""
        try:
            message_id = event_data.get('message_id')
            room_id = event_data.get('room_id')
            
            Logger.info(f"채팅 메시지 전송 이벤트 처리: {message_id} (방: {room_id})")
            
            # 실시간 알림, 푸시 알림 등 (향후 구현)
            return True
            
        except Exception as e:
            Logger.error(f"채팅 메시지 전송 이벤트 처리 실패: {e}")
            return False
    
    @classmethod
    async def _handle_portfolio_updated(cls, event_data: Dict[str, Any]) -> bool:
        """포트폴리오 업데이트 이벤트 처리"""
        try:
            account_db_key = event_data.get('account_db_key')
            portfolio_data = event_data.get('portfolio_data', {})
            
            Logger.info(f"포트폴리오 업데이트 이벤트 처리: 사용자 {account_db_key}")
            
            # 캐시 무효화, 실시간 업데이트 등
            return True
            
        except Exception as e:
            Logger.error(f"포트폴리오 업데이트 이벤트 처리 실패: {e}")
            return False
    
    @classmethod
    async def _handle_signal_generated(cls, event_data: Dict[str, Any]) -> bool:
        """시그널 생성 이벤트 처리"""
        try:
            signal_id = event_data.get('signal_id')
            symbol = event_data.get('symbol')
            signal_type = event_data.get('signal_type')
            
            Logger.info(f"시그널 생성 이벤트 처리: {signal_id} ({symbol} {signal_type})")
            
            # 알림 발송, 캐시 업데이트 등
            return True
            
        except Exception as e:
            Logger.error(f"시그널 생성 이벤트 처리 실패: {e}")
            return False
    
    @classmethod
    async def _handle_notification_created(cls, event_data: Dict[str, Any]) -> bool:
        """알림 생성 이벤트 처리"""
        try:
            notification_id = event_data.get('notification_id')
            account_db_key = event_data.get('account_db_key')
            
            Logger.info(f"알림 생성 이벤트 처리: {notification_id} (사용자: {account_db_key})")
            
            # 실시간 알림 전송 등
            return True
            
        except Exception as e:
            Logger.error(f"알림 생성 이벤트 처리 실패: {e}")
            return False
    
    @classmethod
    async def shutdown(cls):
        """컨슈머 종료"""
        try:
            cls._initialized = False
            
            # 컨슈머 태스크 종료
            for task in cls._consumer_tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            cls._consumer_tasks.clear()
            
            # 스케줄러 작업 제거
            for job_id in cls._scheduler_job_ids:
                try:
                    await SchedulerService.remove_job(job_id)
                except:
                    pass
            cls._scheduler_job_ids.clear()
            
            Logger.info("✅ UniversalOutboxConsumer 종료 완료")
            
        except Exception as e:
            Logger.error(f"❌ UniversalOutboxConsumer 종료 실패: {e}")
    
    @classmethod
    def is_initialized(cls) -> bool:
        """초기화 상태 확인"""
        return cls._initialized


# 편의 함수들
async def publish_outbox_event(
    domain: EventDomain,
    event_type: str,
    aggregate_id: str,
    event_data: Dict[str, Any],
    partition_key: str = None,
    shard_id: int = None
) -> bool:
    """Outbox 이벤트 발행 (편의 함수)"""
    try:
        db_service = ServiceContainer.get_database_service()
        
        # partition_key 기본값 설정
        if not partition_key:
            partition_key = aggregate_id
        
        # 샤드 결정
        if shard_id is None:
            # aggregate_id에서 사용자 정보 추출하여 샤드 결정 (간단 구현)
            shard_id = hash(aggregate_id) % 2 + 1  # 1 또는 2
        
        # SQL 프로시저로 이벤트 발행
        result = await db_service.call_shard_procedure(
            shard_id,
            "fp_universal_outbox_publish",
            (domain.value, partition_key, event_type, aggregate_id, json.dumps(event_data))
        )
        
        if result and result[0].get('result') == 'SUCCESS':
            event_id = result[0].get('event_id')
            Logger.info(f"✅ Outbox 이벤트 발행: {event_id} ({domain.value}.{event_type})")
            return True
        else:
            Logger.error(f"❌ Outbox 이벤트 발행 실패: {result}")
            return False
            
    except Exception as e:
        Logger.error(f"❌ Outbox 이벤트 발행 오류: {e}")
        return False