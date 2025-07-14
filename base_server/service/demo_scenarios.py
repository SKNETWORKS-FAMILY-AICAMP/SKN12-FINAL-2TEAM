"""
실제 비즈니스 시나리오 데모 및 테스트
각 서비스가 실제 동작하는 모습을 보여주는 시나리오들
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

from service.core.logger import Logger
from service.queue.queue_service import QueueService
from service.queue.message_queue import MessagePriority, QueueMessage
from service.queue.event_queue import EventType, Event
from service.lock.lock_service import LockService
from service.scheduler.scheduler_service import SchedulerService
from service.scheduler.base_scheduler import ScheduleJob


class FinanceServiceDemo:
    """금융 서비스 시나리오 데모"""
    
    def __init__(self):
        self.demo_results = []
        self.demo_data = {
            "users": {},
            "portfolios": {},
            "trades": {},
            "market_data": {}
        }
    
    async def run_complete_demo(self) -> Dict[str, Any]:
        """완전한 금융 서비스 시나리오 실행"""
        Logger.info("🎬 === 금융 서비스 완전 시나리오 데모 시작 ===")
        
        try:
            # 1. 사용자 계정 생성 시나리오
            await self.demo_account_creation()
            
            # 2. 포트폴리오 생성 및 관리 시나리오
            await self.demo_portfolio_management()
            
            # 3. 거래 실행 시나리오
            await self.demo_trade_execution()
            
            # 4. 시장 데이터 업데이트 시나리오
            await self.demo_market_data_update()
            
            # 5. 리스크 분석 시나리오
            await self.demo_risk_analysis()
            
            # 6. 알림 및 보고서 시나리오
            await self.demo_notification_system()
            
            Logger.info("🎉 === 금융 서비스 완전 시나리오 데모 완료 ===")
            
            return {
                "demo_type": "complete_finance_scenario",
                "total_steps": len(self.demo_results),
                "results": self.demo_results,
                "demo_data": self.demo_data,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            Logger.error(f"데모 실행 중 오류: {e}")
            return {
                "error": str(e),
                "completed_steps": len(self.demo_results),
                "results": self.demo_results,
                "timestamp": datetime.now().isoformat()
            }
    
    async def demo_account_creation(self):
        """1. 계정 생성 시나리오"""
        Logger.info("📋 1. 계정 생성 시나리오 시작")
        
        try:
            queue_service = QueueService.get_instance()
            
            # 새 사용자 정보
            user_data = {
                "user_id": "user_demo_001",
                "username": "김투자",
                "email": "kim.investor@example.com",
                "phone": "010-1234-5678",
                "investment_type": "aggressive",
                "initial_capital": 10000000,  # 1천만원
                "created_at": datetime.now().isoformat()
            }
            
            self.demo_data["users"][user_data["user_id"]] = user_data
            
            # 계정 생성 이벤트 발행
            account_created = await queue_service.publish_event(
                event_type=EventType.ACCOUNT_CREATED,
                source="account_service",
                data=user_data,
                correlation_id=f"account_creation_{user_data['user_id']}"
            )
            
            if account_created:
                self._log_demo_step("계정 생성 이벤트 발행 성공", user_data)
                
                # 계정 생성 후 처리 작업들을 메시지큐로 전송
                welcome_tasks = [
                    {
                        "queue": "user_notifications",
                        "task": "send_welcome_email",
                        "priority": MessagePriority.HIGH,
                        "data": {
                            "user_id": user_data["user_id"],
                            "email": user_data["email"],
                            "username": user_data["username"]
                        }
                    },
                    {
                        "queue": "account_setup",
                        "task": "create_default_portfolio",
                        "priority": MessagePriority.NORMAL,
                        "data": {
                            "user_id": user_data["user_id"],
                            "initial_capital": user_data["initial_capital"]
                        }
                    },
                    {
                        "queue": "kyc_verification", 
                        "task": "start_kyc_process",
                        "priority": MessagePriority.HIGH,
                        "data": {
                            "user_id": user_data["user_id"],
                            "phone": user_data["phone"]
                        }
                    }
                ]
                
                # 각 작업을 메시지큐에 전송
                for task in welcome_tasks:
                    await queue_service.send_message(
                        queue_name=task["queue"],
                        payload=task["data"],
                        message_type=task["task"],
                        priority=task["priority"]
                    )
                
                self._log_demo_step("계정 생성 후 처리 작업 큐 전송 완료", {"task_count": len(welcome_tasks)})
            
        except Exception as e:
            self._log_demo_step("계정 생성 시나리오 실패", {"error": str(e)})
    
    async def demo_portfolio_management(self):
        """2. 포트폴리오 생성 및 관리 시나리오"""
        Logger.info("💼 2. 포트폴리오 관리 시나리오 시작")
        
        try:
            queue_service = QueueService.get_instance()
            
            # 포트폴리오 생성
            portfolio_data = {
                "portfolio_id": "portfolio_demo_001",
                "user_id": "user_demo_001",
                "name": "김투자의 성장형 포트폴리오",
                "strategy": "growth",
                "target_allocation": {
                    "stocks": 0.7,     # 70% 주식
                    "bonds": 0.2,      # 20% 채권
                    "cash": 0.1        # 10% 현금
                },
                "current_value": 10000000,
                "created_at": datetime.now().isoformat()
            }
            
            self.demo_data["portfolios"][portfolio_data["portfolio_id"]] = portfolio_data
            
            # 포트폴리오 생성 이벤트
            portfolio_created = await queue_service.publish_event(
                event_type=EventType.PORTFOLIO_CREATED,
                source="portfolio_service",
                data=portfolio_data
            )
            
            if portfolio_created:
                self._log_demo_step("포트폴리오 생성 이벤트 발행", portfolio_data)
                
                # 포트폴리오 리밸런싱 작업 스케줄링 (매주 월요일 9시)
                rebalancing_job = ScheduleJob(
                    job_id=f"rebalance_{portfolio_data['portfolio_id']}",
                    name=f"포트폴리오 리밸런싱: {portfolio_data['name']}",
                    schedule_type="cron",
                    cron_expression="0 9 * * 1",  # 매주 월요일 9시
                    job_function=self._create_rebalancing_function(portfolio_data),
                    use_distributed_lock=True,
                    lock_key=f"rebalance:{portfolio_data['portfolio_id']}"
                )
                
                await SchedulerService.add_job(rebalancing_job)
                self._log_demo_step("포트폴리오 리밸런싱 스케줄 등록", {
                    "job_id": rebalancing_job.job_id,
                    "schedule": "매주 월요일 9시"
                })
        
        except Exception as e:
            self._log_demo_step("포트폴리오 관리 시나리오 실패", {"error": str(e)})
    
    async def demo_trade_execution(self):
        """3. 거래 실행 시나리오"""
        Logger.info("💰 3. 거래 실행 시나리오 시작")
        
        try:
            queue_service = QueueService.get_instance()
            
            # 분산락을 사용한 동시 거래 방지
            async with LockService.get_manager().acquire_lock(
                "trade:user_demo_001", ttl=30, timeout=10
            ):
                # 매수 주문
                buy_order = {
                    "trade_id": "trade_demo_001",
                    "user_id": "user_demo_001",
                    "portfolio_id": "portfolio_demo_001",
                    "symbol": "AAPL",
                    "company_name": "Apple Inc.",
                    "action": "buy",
                    "quantity": 50,
                    "price": 150.25,
                    "total_amount": 7512.50,
                    "order_type": "market",
                    "executed_at": datetime.now().isoformat()
                }
                
                self.demo_data["trades"][buy_order["trade_id"]] = buy_order
                
                # 거래 실행 이벤트 발행
                trade_executed = await queue_service.publish_event(
                    event_type=EventType.TRADE_EXECUTED,
                    source="trading_service",
                    data=buy_order
                )
                
                if trade_executed:
                    self._log_demo_step("거래 실행 이벤트 발행", buy_order)
                    
                    # 거래 후 처리 작업들
                    post_trade_tasks = [
                        {
                            "queue": "trade_settlement",
                            "task": "settle_trade",
                            "priority": MessagePriority.CRITICAL,
                            "data": buy_order
                        },
                        {
                            "queue": "portfolio_update",
                            "task": "update_portfolio_holdings",
                            "priority": MessagePriority.HIGH,
                            "data": {
                                "portfolio_id": buy_order["portfolio_id"],
                                "trade_data": buy_order
                            }
                        },
                        {
                            "queue": "risk_analysis",
                            "task": "analyze_portfolio_risk",
                            "priority": MessagePriority.NORMAL,
                            "data": {
                                "portfolio_id": buy_order["portfolio_id"],
                                "trigger": "new_trade"
                            }
                        },
                        {
                            "queue": "user_notifications",
                            "task": "send_trade_confirmation",
                            "priority": MessagePriority.HIGH,
                            "data": {
                                "user_id": buy_order["user_id"],
                                "trade_summary": f"{buy_order['action'].upper()} {buy_order['quantity']} {buy_order['symbol']} @ ${buy_order['price']}"
                            }
                        }
                    ]
                    
                    # 각 작업을 순서대로 큐에 전송 (파티션 키로 순서 보장)
                    for task in post_trade_tasks:
                        await queue_service.send_message(
                            queue_name=task["queue"],
                            payload=task["data"],
                            message_type=task["task"],
                            priority=task["priority"],
                            partition_key=buy_order["user_id"]  # 사용자별 순서 보장
                        )
                    
                    self._log_demo_step("거래 후 처리 작업 큐 전송 완료", {
                        "trade_id": buy_order["trade_id"],
                        "task_count": len(post_trade_tasks)
                    })
        
        except Exception as e:
            self._log_demo_step("거래 실행 시나리오 실패", {"error": str(e)})
    
    async def demo_market_data_update(self):
        """4. 시장 데이터 업데이트 시나리오"""
        Logger.info("📊 4. 시장 데이터 업데이트 시나리오 시작")
        
        try:
            queue_service = QueueService.get_instance()
            
            # 실시간 시장 데이터 업데이트
            market_update = {
                "symbol": "AAPL",
                "price": 152.80,
                "change": 2.55,
                "change_percent": 1.70,
                "volume": 45678900,
                "market_cap": 2456000000000,
                "timestamp": datetime.now().isoformat()
            }
            
            self.demo_data["market_data"]["AAPL"] = market_update
            
            # 시장 데이터 업데이트 이벤트 발행
            market_updated = await queue_service.publish_event(
                event_type=EventType.MARKET_DATA_UPDATED,
                source="market_data_service",
                data=market_update
            )
            
            if market_updated:
                self._log_demo_step("시장 데이터 업데이트 이벤트 발행", market_update)
                
                # 가격 알림 체크 작업
                await queue_service.send_message(
                    queue_name="price_alerts",
                    payload={
                        "symbol": market_update["symbol"],
                        "current_price": market_update["price"],
                        "change_percent": market_update["change_percent"]
                    },
                    message_type="price_alert_check",
                    priority=MessagePriority.NORMAL
                )
                
                # 포트폴리오 평가 업데이트 (지연 실행 - 1분 후)
                delayed_time = datetime.now() + timedelta(minutes=1)
                await queue_service.send_message(
                    queue_name="portfolio_valuation",
                    payload={
                        "symbol": market_update["symbol"],
                        "new_price": market_update["price"],
                        "update_reason": "market_data_change"
                    },
                    message_type="update_portfolio_valuation",
                    priority=MessagePriority.NORMAL,
                    scheduled_at=delayed_time
                )
                
                self._log_demo_step("시장 데이터 후속 작업 스케줄링 완료", {
                    "immediate_tasks": 1,
                    "delayed_tasks": 1,
                    "delayed_execution_time": delayed_time.isoformat()
                })
        
        except Exception as e:
            self._log_demo_step("시장 데이터 업데이트 시나리오 실패", {"error": str(e)})
    
    async def demo_risk_analysis(self):
        """5. 리스크 분석 시나리오"""
        Logger.info("⚠️ 5. 리스크 분석 시나리오 시작")
        
        try:
            queue_service = QueueService.get_instance()
            
            # 포트폴리오 리스크 분석 시뮬레이션
            risk_analysis = {
                "portfolio_id": "portfolio_demo_001",
                "analysis_type": "comprehensive",
                "var_95": -150000,  # 95% VaR: 15만원 손실 가능
                "var_99": -300000,  # 99% VaR: 30만원 손실 가능
                "beta": 1.15,       # 시장 대비 변동성
                "sharpe_ratio": 1.85,
                "risk_level": "moderate_high",
                "recommendations": [
                    "현금 비중을 15%로 증가 권장",
                    "방어주 비중 확대 고려",
                    "섹터 분산 재검토 필요"
                ],
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            # 리스크 임계값 초과 시 즉시 알림
            if abs(risk_analysis["var_95"]) > 100000:  # 10만원 초과 손실 가능성
                await queue_service.send_message(
                    queue_name="risk_alerts",
                    payload={
                        "alert_type": "high_risk_detected",
                        "portfolio_id": risk_analysis["portfolio_id"],
                        "risk_metrics": risk_analysis,
                        "severity": "high"
                    },
                    message_type="risk_alert",
                    priority=MessagePriority.CRITICAL
                )
                
                self._log_demo_step("고위험 포트폴리오 긴급 알림 발송", {
                    "var_95": risk_analysis["var_95"],
                    "alert_severity": "high"
                })
            
            # 리스크 분석 보고서 생성 작업
            await queue_service.send_message(
                queue_name="report_generation",
                payload={
                    "report_type": "risk_analysis",
                    "portfolio_id": risk_analysis["portfolio_id"],
                    "analysis_data": risk_analysis,
                    "delivery_method": ["email", "app_notification"]
                },
                message_type="generate_risk_report",
                priority=MessagePriority.NORMAL
            )
            
            self._log_demo_step("리스크 분석 완료 및 보고서 생성 요청", risk_analysis)
            
        except Exception as e:
            self._log_demo_step("리스크 분석 시나리오 실패", {"error": str(e)})
    
    async def demo_notification_system(self):
        """6. 알림 및 보고서 시나리오"""
        Logger.info("📧 6. 알림 및 보고서 시나리오 시작")
        
        try:
            queue_service = QueueService.get_instance()
            
            # 일일 포트폴리오 요약 스케줄 (매일 오후 6시)
            daily_summary_job = ScheduleJob(
                job_id="daily_portfolio_summary",
                name="일일 포트폴리오 요약 발송",
                schedule_type="cron",
                cron_expression="0 18 * * *",  # 매일 오후 6시
                job_function=self._create_daily_summary_function(),
                use_distributed_lock=True,
                lock_key="daily_summary_generation"
            )
            
            await SchedulerService.add_job(daily_summary_job)
            
            # 월간 투자 성과 보고서 스케줄 (매월 1일 오전 9시)
            monthly_report_job = ScheduleJob(
                job_id="monthly_performance_report",
                name="월간 투자 성과 보고서",
                schedule_type="cron", 
                cron_expression="0 9 1 * *",  # 매월 1일 오전 9시
                job_function=self._create_monthly_report_function(),
                use_distributed_lock=True,
                lock_key="monthly_report_generation"
            )
            
            await SchedulerService.add_job(monthly_report_job)
            
            # 즉시 테스트 알림 발송
            test_notifications = [
                {
                    "type": "portfolio_performance",
                    "title": "포트폴리오 성과 업데이트",
                    "message": "오늘 포트폴리오가 +2.5% 상승했습니다.",
                    "priority": "normal"
                },
                {
                    "type": "market_alert",
                    "title": "시장 급등 알림",
                    "message": "AAPL이 +5% 급등하여 목표가에 도달했습니다.",
                    "priority": "high"
                },
                {
                    "type": "system_maintenance",
                    "title": "시스템 정기 점검 안내",
                    "message": "내일 새벽 2시-4시 시스템 점검이 예정되어 있습니다.",
                    "priority": "low"
                }
            ]
            
            for notification in test_notifications:
                await queue_service.send_message(
                    queue_name="user_notifications",
                    payload={
                        "user_id": "user_demo_001",
                        "notification": notification
                    },
                    message_type="send_notification",
                    priority=getattr(MessagePriority, notification["priority"].upper())
                )
            
            self._log_demo_step("정기 보고서 스케줄 등록 및 테스트 알림 발송", {
                "scheduled_jobs": ["daily_summary", "monthly_report"],
                "test_notifications": len(test_notifications)
            })
            
        except Exception as e:
            self._log_demo_step("알림 및 보고서 시나리오 실패", {"error": str(e)})
    
    def _create_rebalancing_function(self, portfolio_data):
        """포트폴리오 리밸런싱 함수 생성"""
        async def rebalance_portfolio():
            Logger.info(f"🔄 포트폴리오 리밸런싱 실행: {portfolio_data['name']}")
            
            # 실제 리밸런싱 로직 시뮬레이션
            current_allocation = {
                "stocks": 0.75,  # 목표: 70%
                "bonds": 0.15,   # 목표: 20%
                "cash": 0.10     # 목표: 10%
            }
            
            target_allocation = portfolio_data["target_allocation"]
            
            # 리밸런싱 필요 여부 확인
            needs_rebalancing = any(
                abs(current_allocation[asset] - target_allocation[asset]) > 0.05
                for asset in target_allocation
            )
            
            if needs_rebalancing:
                Logger.info(f"리밸런싱 필요: {portfolio_data['portfolio_id']}")
                
                # 리밸런싱 작업을 큐에 추가
                queue_service = QueueService.get_instance()
                await queue_service.send_message(
                    queue_name="portfolio_rebalancing",
                    payload={
                        "portfolio_id": portfolio_data["portfolio_id"],
                        "current_allocation": current_allocation,
                        "target_allocation": target_allocation,
                        "rebalancing_reason": "scheduled_weekly_rebalancing"
                    },
                    message_type="execute_rebalancing",
                    priority=MessagePriority.HIGH
                )
            
            return True
        
        return rebalance_portfolio
    
    def _create_daily_summary_function(self):
        """일일 요약 생성 함수"""
        async def generate_daily_summary():
            Logger.info("📊 일일 포트폴리오 요약 생성 시작")
            
            queue_service = QueueService.get_instance()
            
            # 모든 사용자의 일일 요약 생성
            for user_id in self.demo_data["users"]:
                await queue_service.send_message(
                    queue_name="report_generation",
                    payload={
                        "report_type": "daily_summary",
                        "user_id": user_id,
                        "date": datetime.now().strftime("%Y-%m-%d")
                    },
                    message_type="generate_daily_summary",
                    priority=MessagePriority.NORMAL
                )
            
            return True
        
        return generate_daily_summary
    
    def _create_monthly_report_function(self):
        """월간 보고서 생성 함수"""
        async def generate_monthly_report():
            Logger.info("📈 월간 투자 성과 보고서 생성 시작")
            
            queue_service = QueueService.get_instance()
            
            # 모든 사용자의 월간 보고서 생성
            for user_id in self.demo_data["users"]:
                await queue_service.send_message(
                    queue_name="report_generation",
                    payload={
                        "report_type": "monthly_performance",
                        "user_id": user_id,
                        "month": datetime.now().strftime("%Y-%m")
                    },
                    message_type="generate_monthly_report",
                    priority=MessagePriority.HIGH
                )
            
            return True
        
        return generate_monthly_report
    
    def _log_demo_step(self, step_name: str, data: Dict[str, Any]):
        """데모 단계 로깅"""
        step_info = {
            "step": step_name,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        self.demo_results.append(step_info)
        Logger.info(f"✅ {step_name}: {data}")


# 빠른 데모 함수들
async def run_quick_finance_demo() -> Dict[str, Any]:
    """빠른 금융 서비스 데모"""
    demo = FinanceServiceDemo()
    
    Logger.info("⚡ 빠른 금융 서비스 데모 시작")
    
    try:
        queue_service = QueueService.get_instance()
        
        # 간단한 거래 시나리오
        quick_trade = {
            "trade_id": f"quick_trade_{datetime.now().timestamp()}",
            "user_id": "quick_demo_user",
            "symbol": "TSLA",
            "action": "buy",
            "quantity": 10,
            "price": 250.50
        }
        
        # 거래 이벤트 발행
        trade_event = await queue_service.publish_event(
            event_type=EventType.TRADE_EXECUTED,
            source="quick_demo",
            data=quick_trade
        )
        
        # 알림 메시지 전송
        notification_sent = await queue_service.send_message(
            queue_name="quick_notifications",
            payload={
                "message": f"거래 완료: {quick_trade['action']} {quick_trade['quantity']} {quick_trade['symbol']}",
                "user_id": quick_trade["user_id"]
            },
            message_type="trade_notification",
            priority=MessagePriority.HIGH
        )
        
        return {
            "demo_type": "quick_finance",
            "trade_event_published": trade_event,
            "notification_sent": notification_sent,
            "trade_data": quick_trade,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "demo_type": "quick_finance",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


async def run_scheduler_demo() -> Dict[str, Any]:
    """스케줄러 데모"""
    Logger.info("⏰ 스케줄러 데모 시작")
    
    try:
        # 간단한 테스트 작업
        execution_log = {"count": 0}
        
        async def test_scheduled_task():
            execution_log["count"] += 1
            Logger.info(f"📅 예약 작업 실행: {execution_log['count']}번째")
            return True
        
        # 5초마다 실행되는 작업 등록
        demo_job = ScheduleJob(
            job_id="scheduler_demo_job",
            name="스케줄러 데모 작업",
            schedule_type="interval",
            interval_seconds=5,
            job_function=test_scheduled_task,
            use_distributed_lock=False
        )
        
        await SchedulerService.add_job(demo_job)
        
        # 10초 대기 (최소 2회 실행 예상)
        await asyncio.sleep(10)
        
        # 작업 제거
        await SchedulerService.remove_job("scheduler_demo_job")
        
        return {
            "demo_type": "scheduler",
            "job_added": True,
            "execution_count": execution_log["count"],
            "job_removed": True,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "demo_type": "scheduler",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# 전역 데모 실행 함수
async def run_complete_service_demo() -> Dict[str, Any]:
    """완전한 서비스 데모 실행"""
    demo = FinanceServiceDemo()
    return await demo.run_complete_demo()