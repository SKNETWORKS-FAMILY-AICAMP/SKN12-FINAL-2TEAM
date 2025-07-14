"""
메시지큐/이벤트큐 사용 예제 및 테스트 코드
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

from service.core.logger import Logger
from .queue_service import QueueService, get_queue_service
from .message_queue import QueueMessage, MessagePriority
from .event_queue import EventType, Event


class QueueExamples:
    """큐 시스템 사용 예제"""
    
    def __init__(self):
        self.queue_service = get_queue_service()
    
    async def example_basic_message_queue(self):
        """기본 메시지큐 사용 예제"""
        Logger.info("=== 기본 메시지큐 예제 시작 ===")
        
        # 메시지 전송
        await self.queue_service.send_message(
            queue_name="user_notifications",
            payload={
                "user_id": "user123",
                "message": "포트폴리오가 업데이트되었습니다.",
                "notification_type": "portfolio_update"
            },
            message_type="notification",
            priority=MessagePriority.HIGH
        )
        
        # 메시지 소비자 등록
        async def notification_handler(message: QueueMessage) -> bool:
            try:
                payload = message.payload
                Logger.info(f"알림 처리: {payload['user_id']} - {payload['message']}")
                
                # 실제 알림 발송 로직
                # await send_push_notification(payload)
                
                return True
            except Exception as e:
                Logger.error(f"알림 처리 실패: {e}")
                return False
        
        await self.queue_service.register_message_consumer(
            "user_notifications",
            "notification_worker_1",
            notification_handler
        )
        
        Logger.info("=== 기본 메시지큐 예제 완료 ===")
    
    async def example_delayed_message_queue(self):
        """지연 메시지큐 사용 예제"""
        Logger.info("=== 지연 메시지큐 예제 시작 ===")
        
        # 10초 후 실행될 메시지
        delayed_time = datetime.now() + timedelta(seconds=10)
        
        await self.queue_service.send_message(
            queue_name="scheduled_tasks",
            payload={
                "task_type": "portfolio_rebalancing",
                "portfolio_id": "portfolio123",
                "target_allocation": {
                    "stocks": 0.6,
                    "bonds": 0.3,
                    "cash": 0.1
                }
            },
            message_type="scheduled_task",
            priority=MessagePriority.NORMAL,
            scheduled_at=delayed_time
        )
        
        Logger.info(f"지연 메시지 예약: {delayed_time}")
        
        # 지연 메시지 처리자
        async def scheduled_task_handler(message: QueueMessage) -> bool:
            try:
                payload = message.payload
                Logger.info(f"예약 작업 실행: {payload['task_type']} - {payload['portfolio_id']}")
                
                # 포트폴리오 리밸런싱 로직
                # await rebalance_portfolio(payload['portfolio_id'], payload['target_allocation'])
                
                return True
            except Exception as e:
                Logger.error(f"예약 작업 실패: {e}")
                return False
        
        await self.queue_service.register_message_consumer(
            "scheduled_tasks",
            "scheduler_worker_1",
            scheduled_task_handler
        )
        
        Logger.info("=== 지연 메시지큐 예제 완료 ===")
    
    async def example_partition_message_queue(self):
        """파티션 메시지큐 사용 예제 (순서 보장)"""
        Logger.info("=== 파티션 메시지큐 예제 시작 ===")
        
        # 동일한 사용자의 거래는 순서가 보장되어야 함
        user_id = "user123"
        
        # 첫 번째 거래
        await self.queue_service.send_message(
            queue_name="trade_processing",
            payload={
                "user_id": user_id,
                "action": "buy",
                "symbol": "AAPL",
                "quantity": 100,
                "order_id": "order001"
            },
            message_type="trade_order",
            priority=MessagePriority.HIGH,
            partition_key=user_id  # 동일한 사용자 = 동일한 파티션
        )
        
        # 두 번째 거래
        await self.queue_service.send_message(
            queue_name="trade_processing",
            payload={
                "user_id": user_id,
                "action": "sell",
                "symbol": "AAPL",
                "quantity": 50,
                "order_id": "order002"
            },
            message_type="trade_order",
            priority=MessagePriority.HIGH,
            partition_key=user_id  # 순서 보장됨
        )
        
        # 거래 처리자
        async def trade_handler(message: QueueMessage) -> bool:
            try:
                payload = message.payload
                Logger.info(f"거래 처리: {payload['user_id']} - {payload['action']} {payload['symbol']} {payload['quantity']}")
                
                # 거래 실행 로직
                # await execute_trade(payload)
                
                return True
            except Exception as e:
                Logger.error(f"거래 처리 실패: {e}")
                return False
        
        await self.queue_service.register_message_consumer(
            "trade_processing",
            "trade_worker_1",
            trade_handler
        )
        
        Logger.info("=== 파티션 메시지큐 예제 완료 ===")
    
    async def example_event_publishing(self):
        """이벤트 발행 예제"""
        Logger.info("=== 이벤트 발행 예제 시작 ===")
        
        # 계정 생성 이벤트 발행
        await self.queue_service.publish_event(
            event_type=EventType.ACCOUNT_CREATED,
            source="account_service",
            data={
                "account_id": "acc123",
                "user_id": "user123",
                "account_type": "investment",
                "created_at": datetime.now().isoformat()
            },
            correlation_id="req123"
        )
        
        # 거래 실행 이벤트 발행
        await self.queue_service.publish_event(
            event_type=EventType.TRADE_EXECUTED,
            source="trading_service",
            data={
                "trade_id": "trade123",
                "account_id": "acc123",
                "symbol": "AAPL",
                "action": "buy",
                "quantity": 100,
                "price": 150.50,
                "executed_at": datetime.now().isoformat()
            }
        )
        
        Logger.info("=== 이벤트 발행 예제 완료 ===")
    
    async def example_event_subscription(self):
        """이벤트 구독 예제"""
        Logger.info("=== 이벤트 구독 예제 시작 ===")
        
        # 계정 관련 이벤트 구독
        async def account_event_handler(event: Event) -> bool:
            try:
                Logger.info(f"계정 이벤트 수신: {event.event_type.value} - {event.data}")
                
                # 계정 이벤트 처리 로직
                if event.event_type == EventType.ACCOUNT_CREATED:
                    # 환영 이메일 발송
                    pass
                elif event.event_type == EventType.ACCOUNT_UPDATED:
                    # 프로필 업데이트 알림
                    pass
                
                return True
            except Exception as e:
                Logger.error(f"계정 이벤트 처리 실패: {e}")
                return False
        
        await self.queue_service.subscribe_events(
            subscriber_id="account_subscriber",
            event_types=[EventType.ACCOUNT_CREATED, EventType.ACCOUNT_UPDATED],
            callback=account_event_handler
        )
        
        # 거래 관련 이벤트 구독
        async def trade_event_handler(event: Event) -> bool:
            try:
                Logger.info(f"거래 이벤트 수신: {event.event_type.value} - {event.data}")
                
                # 거래 이벤트 처리 로직
                if event.event_type == EventType.TRADE_EXECUTED:
                    # 거래 확인 알림
                    # 포트폴리오 업데이트
                    pass
                
                return True
            except Exception as e:
                Logger.error(f"거래 이벤트 처리 실패: {e}")
                return False
        
        await self.queue_service.subscribe_events(
            subscriber_id="trade_subscriber",
            event_types=[EventType.TRADE_EXECUTED],
            callback=trade_event_handler
        )
        
        Logger.info("=== 이벤트 구독 예제 완료 ===")
    
    async def example_outbox_pattern(self):
        """아웃박스 패턴 사용 예제"""
        Logger.info("=== 아웃박스 패턴 예제 시작 ===")
        
        # 비즈니스 로직과 이벤트 발행을 원자적으로 처리
        async def create_account_business_logic(transaction):
            """계정 생성 비즈니스 로직"""
            # 실제 DB 작업은 transaction을 통해 수행
            # 예: await transaction.execute("INSERT INTO accounts ...")
            Logger.info("계정 생성 DB 작업 실행")
        
        # 아웃박스 패턴으로 계정 생성 이벤트 발행
        await self.queue_service.publish_event_with_transaction(
            event_type="account.created",
            aggregate_id="acc123",
            aggregate_type="account",
            event_data={
                "account_id": "acc123",
                "user_id": "user123",
                "account_type": "investment"
            },
            business_operation=create_account_business_logic
        )
        
        Logger.info("=== 아웃박스 패턴 예제 완료 ===")
    
    async def run_all_examples(self):
        """모든 예제 실행"""
        try:
            await self.example_basic_message_queue()
            await asyncio.sleep(1)
            
            await self.example_delayed_message_queue()
            await asyncio.sleep(1)
            
            await self.example_partition_message_queue()
            await asyncio.sleep(1)
            
            await self.example_event_publishing()
            await asyncio.sleep(1)
            
            await self.example_event_subscription()
            await asyncio.sleep(1)
            
            await self.example_outbox_pattern()
            
            Logger.info("=== 모든 예제 실행 완료 ===")
            
        except Exception as e:
            Logger.error(f"예제 실행 중 오류: {e}")


class QueueMonitor:
    """큐 시스템 모니터링"""
    
    def __init__(self):
        self.queue_service = get_queue_service()
    
    async def print_queue_stats(self):
        """큐 통계 출력"""
        try:
            # 서비스 전체 통계
            service_stats = self.queue_service.get_stats()
            Logger.info(f"QueueService 통계: {service_stats}")
            
            # 특정 큐 통계
            queue_names = ["user_notifications", "scheduled_tasks", "trade_processing"]
            for queue_name in queue_names:
                stats = await self.queue_service.get_queue_stats(queue_name)
                if stats:
                    Logger.info(f"큐 통계 [{queue_name}]: {stats}")
            
            # 이벤트큐 통계
            event_stats = await self.queue_service.get_event_stats()
            if event_stats:
                Logger.info(f"이벤트큐 통계: {event_stats}")
            
        except Exception as e:
            Logger.error(f"큐 통계 조회 실패: {e}")
    
    async def start_monitoring(self, interval: int = 30):
        """주기적 모니터링 시작"""
        Logger.info(f"큐 모니터링 시작 (간격: {interval}초)")
        
        while True:
            await self.print_queue_stats()
            await asyncio.sleep(interval)


# 실행 스크립트
async def main():
    """메인 실행 함수"""
    try:
        # QueueService가 초기화되었다고 가정
        # 실제 사용 시에는 아래와 같이 초기화 필요:
        # await QueueService.initialize(db_service)
        
        # 예제 실행
        examples = QueueExamples()
        await examples.run_all_examples()
        
        # 10초 동안 메시지 처리 관찰
        await asyncio.sleep(10)
        
        # 모니터링
        monitor = QueueMonitor()
        await monitor.print_queue_stats()
        
    except Exception as e:
        Logger.error(f"메인 실행 실패: {e}")


if __name__ == "__main__":
    asyncio.run(main())