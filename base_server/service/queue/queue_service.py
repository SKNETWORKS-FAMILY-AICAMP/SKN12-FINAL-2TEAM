"""
통합 큐 서비스 - 메시지큐와 이벤트큐를 아웃박스 패턴과 연계하여 관리
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

from service.core.logger import Logger
from service.cache.cache_service import CacheService
from service.outbox.outbox_pattern import OutboxService, OutboxEvent
from service.scheduler.scheduler_service import SchedulerService
from service.scheduler.base_scheduler import ScheduleJob, ScheduleType

from .message_queue import MessageQueueManager, QueueMessage, MessagePriority
from .event_queue import EventQueueManager, EventType, Event


class QueueService:
    """통합 큐 서비스 - 메시지큐/이벤트큐/아웃박스 패턴 통합 관리"""
    
    _instance: Optional['QueueService'] = None
    _initialized: bool = False
    
    def __init__(self):
        if QueueService._instance is not None:
            raise RuntimeError("QueueService는 싱글톤입니다. get_instance()를 사용하세요.")
        
        self.message_queue_manager: Optional[MessageQueueManager] = None
        self.event_queue_manager: Optional[EventQueueManager] = None
        self.outbox_service: Optional[OutboxService] = None
        
        # 큐 통계
        self.stats = {
            "messages_processed": 0,
            "events_published": 0,
            "outbox_events_processed": 0,
            "errors": 0
        }
    
    @classmethod
    def get_instance(cls) -> 'QueueService':
        """싱글톤 인스턴스 반환"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    async def initialize(cls, db_service) -> bool:
        """큐 서비스 초기화"""
        try:
            if cls._initialized:
                Logger.warn("QueueService가 이미 초기화되었습니다")
                return True
            
            instance = cls.get_instance()
            
            # CacheService 확인
            cache_service = CacheService.get_instance()
            
            if not cache_service.is_initialized():
                Logger.error("CacheService가 초기화되지 않음. QueueService 초기화 중단")
                return False
            
            # 각 컴포넌트 초기화 (CacheService를 통해 클라이언트 사용)
            instance.message_queue_manager = MessageQueueManager(cache_service)
            instance.event_queue_manager = EventQueueManager(cache_service)
            instance.outbox_service = OutboxService(db_service)
            
            # 이벤트큐 매니저 초기화
            try:
                await instance.event_queue_manager.initialize()
                Logger.info("이벤트큐 매니저 초기화 완료")
            except Exception as e:
                Logger.error(f"이벤트큐 매니저 초기화 실패: {e}")
                return False
            
            # 지연 메시지 처리기 시작 (CacheService 연결 체크 포함)
            try:
                await instance._start_delayed_message_processor_with_check()
                Logger.info("지연 메시지 처리기 시작 완료")
            except Exception as e:
                Logger.error(f"지연 메시지 처리기 시작 실패: {e}")
                return False
            
            # 아웃박스 패턴과 이벤트큐 연동
            try:
                await instance._setup_outbox_event_integration()
                Logger.info("아웃박스 패턴 연동 완료")
            except Exception as e:
                Logger.error(f"아웃박스 패턴 연동 실패: {e}")
                return False
            
            # 스케줄러 작업 등록
            try:
                await instance._setup_scheduler_jobs()
                Logger.info("스케줄러 작업 등록 완료")
            except Exception as e:
                Logger.error(f"스케줄러 작업 등록 실패: {e}")
                return False
            
            cls._initialized = True
            Logger.info("QueueService 초기화 완료")
            return True
            
        except Exception as e:
            Logger.error(f"QueueService 초기화 실패: {e}")
            return False
    
    @classmethod
    async def shutdown(cls):
        """서비스 종료"""
        try:
            if not cls._initialized:
                return
            
            # 각 컴포넌트 정리 로직 필요시 추가
            cls._initialized = False
            cls._instance = None
            
            Logger.info("QueueService 종료 완료")
            
        except Exception as e:
            Logger.error(f"QueueService 종료 중 오류: {e}")
    
    async def _start_delayed_message_processor_with_check(self):
        """CacheService 연결 체크를 포함한 지연 메시지 처리기 시작"""
        async def process_delayed_with_cache_check():
            while True:
                try:
                    # CacheService 연결 상태 확인
                    cache_service = CacheService.get_instance()
                    if not cache_service.is_initialized():
                        Logger.warn("CacheService가 초기화되지 않음. 지연 메시지 처리 건너뜀")
                        await asyncio.sleep(30)
                        continue
                    
                    # 연결 상태 테스트
                    health_check = await cache_service.health_check()
                    if not health_check.get("healthy", False):
                        Logger.warn(f"Redis 연결 불안정: {health_check.get('error', 'Unknown')}. 지연 메시지 처리 건너뜀")
                        await asyncio.sleep(30)
                        continue
                    
                    # 정상 처리
                    await self.message_queue_manager.message_queue.process_delayed_messages()
                    await asyncio.sleep(10)  # 10초마다 확인
                    
                except Exception as e:
                    Logger.error(f"지연 메시지 처리기 오류: {e}")
                    await asyncio.sleep(30)
        
        asyncio.create_task(process_delayed_with_cache_check())
    
    async def _setup_outbox_event_integration(self):
        """아웃박스 패턴과 이벤트큐 통합 설정"""
        try:
            # 아웃박스 이벤트 타입별 핸들러 등록
            outbox_event_handlers = {
                "account.created": self._handle_account_created_outbox,
                "account.updated": self._handle_account_updated_outbox,
                "portfolio.updated": self._handle_portfolio_updated_outbox,
                "trade.executed": self._handle_trade_executed_outbox,
                "market.data.updated": self._handle_market_data_updated_outbox
            }
            
            for event_type, handler in outbox_event_handlers.items():
                self.outbox_service.register_event_handler(event_type, handler)
            
            Logger.info("아웃박스-이벤트큐 통합 설정 완료")
            
        except Exception as e:
            Logger.error(f"아웃박스-이벤트큐 통합 설정 실패: {e}")
    
    async def _setup_scheduler_jobs(self):
        """스케줄러 작업 설정"""
        try:
            # 아웃박스 이벤트 처리 작업 (1분마다)
            outbox_job = ScheduleJob(
                job_id="process_outbox_events",
                name="아웃박스 이벤트 처리",
                schedule_type=ScheduleType.INTERVAL,
                schedule_value=60,
                callback=self._process_outbox_events_job,
                use_distributed_lock=True,
                lock_key="scheduler:outbox_events"
            )
            
            # 메시지큐 상태 모니터링 작업 (5분마다)
            monitoring_job = ScheduleJob(
                job_id="monitor_queues",
                name="큐 상태 모니터링",
                schedule_type=ScheduleType.INTERVAL,
                schedule_value=300,
                callback=self._monitor_queues_job,
                use_distributed_lock=False
            )
            
            # 큐 정리 작업 (1시간마다)
            cleanup_job = ScheduleJob(
                job_id="cleanup_queues",
                name="큐 정리",
                schedule_type=ScheduleType.INTERVAL,
                schedule_value=3600,
                callback=self._cleanup_queues_job,
                use_distributed_lock=True,
                lock_key="scheduler:cleanup_queues"
            )
            
            # 스케줄러에 작업 추가
            await SchedulerService.add_job(outbox_job)
            await SchedulerService.add_job(monitoring_job)
            await SchedulerService.add_job(cleanup_job)
            
            Logger.info("스케줄러 작업 설정 완료")
            
        except Exception as e:
            Logger.error(f"스케줄러 작업 설정 실패: {e}")
    
    # ==================== 메시지큐 관련 메서드 ====================
    
    async def send_message(self, queue_name: str, payload: Dict[str, Any], 
                          message_type: str, priority: MessagePriority = MessagePriority.NORMAL,
                          scheduled_at: Optional[datetime] = None,
                          partition_key: Optional[str] = None) -> bool:
        """메시지 전송"""
        try:
            message = QueueMessage(
                id=None,  # 자동 생성
                queue_name=queue_name,
                payload=payload,
                message_type=message_type,
                priority=priority,
                scheduled_at=scheduled_at,
                partition_key=partition_key
            )
            
            success = await self.message_queue_manager.message_queue.enqueue(message)
            
            if success:
                self.stats["messages_processed"] += 1
                Logger.info(f"메시지 전송 완료: {queue_name} ({message_type})")
            
            return success
            
        except Exception as e:
            Logger.error(f"메시지 전송 실패: {queue_name} - {e}")
            self.stats["errors"] += 1
            return False
    
    async def register_message_consumer(self, queue_name: str, consumer_id: str,
                                       handler: Callable[[QueueMessage], bool]) -> bool:
        """메시지 소비자 등록"""
        try:
            consumer = await self.message_queue_manager.register_consumer(
                queue_name, consumer_id, handler
            )
            
            await consumer.start()
            Logger.info(f"메시지 소비자 등록 및 시작: {queue_name}:{consumer_id}")
            return True
            
        except Exception as e:
            Logger.error(f"메시지 소비자 등록 실패: {queue_name}:{consumer_id} - {e}")
            return False
    
    # ==================== 이벤트큐 관련 메서드 ====================
    
    async def publish_event(self, event_type: EventType, source: str, 
                           data: Dict[str, Any], correlation_id: Optional[str] = None) -> bool:
        """이벤트 발행"""
        try:
            success = await self.event_queue_manager.publish_event(
                event_type, source, data, correlation_id
            )
            
            if success:
                self.stats["events_published"] += 1
            
            return success
            
        except Exception as e:
            Logger.error(f"이벤트 발행 실패: {event_type.value} - {e}")
            self.stats["errors"] += 1
            return False
    
    async def subscribe_events(self, subscriber_id: str, event_types: List[EventType],
                              callback: Callable[[Event], bool]) -> Optional[str]:
        """이벤트 구독"""
        try:
            subscription_id = await self.event_queue_manager.subscribe_events(
                subscriber_id, event_types, callback
            )
            
            Logger.info(f"이벤트 구독 완료: {subscriber_id} ({len(event_types)}개 타입)")
            return subscription_id
            
        except Exception as e:
            Logger.error(f"이벤트 구독 실패: {subscriber_id} - {e}")
            return None
    
    # ==================== 아웃박스 패턴 관련 메서드 ====================
    
    async def publish_event_with_transaction(self, event_type: str, aggregate_id: str,
                                           aggregate_type: str, event_data: Dict[str, Any],
                                           business_operation: Optional[Callable] = None) -> bool:
        """트랜잭션과 함께 이벤트 발행 (아웃박스 패턴)"""
        try:
            success = await self.outbox_service.publish_event_in_transaction(
                event_type, aggregate_id, aggregate_type, event_data, business_operation
            )
            
            if success:
                Logger.info(f"트랜잭션 이벤트 발행: {event_type} ({aggregate_id})")
            
            return success
            
        except Exception as e:
            Logger.error(f"트랜잭션 이벤트 발행 실패: {event_type} - {e}")
            return False
    
    # ==================== 아웃박스 이벤트 핸들러들 ====================
    
    async def _handle_account_created_outbox(self, outbox_event: OutboxEvent) -> bool:
        """계정 생성 아웃박스 이벤트 처리"""
        try:
            # 이벤트큐로 이벤트 발행
            await self.publish_event(
                EventType.ACCOUNT_CREATED,
                "account_service",
                outbox_event.event_data,
                outbox_event.aggregate_id
            )
            
            # 관련 메시지큐 작업들 추가
            await self.send_message(
                "account_notifications",
                {
                    "account_id": outbox_event.aggregate_id,
                    "action": "created",
                    "data": outbox_event.event_data
                },
                "account_notification",
                MessagePriority.HIGH
            )
            
            return True
            
        except Exception as e:
            Logger.error(f"계정 생성 아웃박스 이벤트 처리 실패: {e}")
            return False
    
    async def _handle_account_updated_outbox(self, outbox_event: OutboxEvent) -> bool:
        """계정 업데이트 아웃박스 이벤트 처리"""
        try:
            await self.publish_event(
                EventType.ACCOUNT_UPDATED,
                "account_service",
                outbox_event.event_data,
                outbox_event.aggregate_id
            )
            return True
        except Exception as e:
            Logger.error(f"계정 업데이트 아웃박스 이벤트 처리 실패: {e}")
            return False
    
    async def _handle_portfolio_updated_outbox(self, outbox_event: OutboxEvent) -> bool:
        """포트폴리오 업데이트 아웃박스 이벤트 처리"""
        try:
            await self.publish_event(
                EventType.PORTFOLIO_UPDATED,
                "portfolio_service",
                outbox_event.event_data,
                outbox_event.aggregate_id
            )
            
            # 리스크 분석 작업 큐에 메시지 추가
            await self.send_message(
                "risk_analysis",
                {
                    "portfolio_id": outbox_event.aggregate_id,
                    "changes": outbox_event.event_data
                },
                "portfolio_risk_analysis",
                MessagePriority.NORMAL
            )
            
            return True
        except Exception as e:
            Logger.error(f"포트폴리오 업데이트 아웃박스 이벤트 처리 실패: {e}")
            return False
    
    async def _handle_trade_executed_outbox(self, outbox_event: OutboxEvent) -> bool:
        """거래 실행 아웃박스 이벤트 처리"""
        try:
            await self.publish_event(
                EventType.TRADE_EXECUTED,
                "trading_service",
                outbox_event.event_data,
                outbox_event.aggregate_id
            )
            
            # 거래 후 처리 작업들
            await self.send_message(
                "trade_settlement",
                outbox_event.event_data,
                "trade_settlement",
                MessagePriority.HIGH
            )
            
            await self.send_message(
                "trade_notifications",
                outbox_event.event_data,
                "trade_notification",
                MessagePriority.HIGH
            )
            
            return True
        except Exception as e:
            Logger.error(f"거래 실행 아웃박스 이벤트 처리 실패: {e}")
            return False
    
    async def _handle_market_data_updated_outbox(self, outbox_event: OutboxEvent) -> bool:
        """시장 데이터 업데이트 아웃박스 이벤트 처리"""
        try:
            await self.publish_event(
                EventType.MARKET_DATA_UPDATED,
                "market_data_service",
                outbox_event.event_data,
                outbox_event.aggregate_id
            )
            
            # 가격 알림 체크 작업
            await self.send_message(
                "price_alerts",
                outbox_event.event_data,
                "price_alert_check",
                MessagePriority.NORMAL
            )
            
            return True
        except Exception as e:
            Logger.error(f"시장 데이터 업데이트 아웃박스 이벤트 처리 실패: {e}")
            return False
    
    # ==================== 스케줄러 작업들 ====================
    
    async def _process_outbox_events_job(self):
        """아웃박스 이벤트 처리 작업"""
        try:
            stats = await self.outbox_service.process_outbox_events()
            
            if stats["processed"] > 0:
                self.stats["outbox_events_processed"] += stats["processed"]
                Logger.info(f"아웃박스 이벤트 처리 완료: {stats}")
            
        except Exception as e:
            # 테이블이 없는 경우는 경고로만 처리
            if "doesn't exist" in str(e):
                Logger.warn(f"아웃박스 테이블이 존재하지 않음: {e}")
            else:
                Logger.error(f"아웃박스 이벤트 처리 작업 실패: {e}")
    
    async def _monitor_queues_job(self):
        """큐 상태 모니터링 작업"""
        try:
            # 메시지큐 통계
            if hasattr(self.message_queue_manager, 'message_queue'):
                queue_stats = await self.message_queue_manager.message_queue.get_queue_stats("default")
                if queue_stats:
                    Logger.info(f"메시지큐 상태: {queue_stats}")
            
            # 이벤트큐 통계
            event_stats = await self.event_queue_manager.get_stats()
            if event_stats:
                Logger.info(f"이벤트큐 상태: {event_stats}")
            
            # 전체 서비스 통계
            Logger.info(f"QueueService 통계: {self.stats}")
            
        except Exception as e:
            Logger.error(f"큐 모니터링 작업 실패: {e}")
    
    async def _cleanup_queues_job(self):
        """큐 정리 작업"""
        try:
            # 아웃박스 이벤트 정리 (7일 이전)
            cleaned_events = await self.outbox_service.cleanup_old_events(7)
            
            if cleaned_events > 0:
                Logger.info(f"오래된 아웃박스 이벤트 정리: {cleaned_events}개")
            
        except Exception as e:
            Logger.error(f"큐 정리 작업 실패: {e}")
    
    # ==================== 유틸리티 메서드 ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """서비스 통계 반환"""
        return self.stats.copy()
    
    async def get_queue_stats(self, queue_name: str) -> Dict[str, Any]:
        """특정 큐 통계 조회"""
        try:
            return await self.message_queue_manager.message_queue.get_queue_stats(queue_name)
        except Exception as e:
            Logger.error(f"큐 통계 조회 실패: {queue_name} - {e}")
            return {}
    
    async def get_event_stats(self) -> Dict[str, Any]:
        """이벤트큐 통계 조회"""
        try:
            return await self.event_queue_manager.get_stats()
        except Exception as e:
            Logger.error(f"이벤트큐 통계 조회 실패: {e}")
            return {}


# 전역 함수들
def get_queue_service() -> QueueService:
    """QueueService 인스턴스 반환"""
    return QueueService.get_instance()


async def initialize_queue_service(db_service) -> bool:
    """QueueService 초기화"""
    return await QueueService.initialize(db_service)