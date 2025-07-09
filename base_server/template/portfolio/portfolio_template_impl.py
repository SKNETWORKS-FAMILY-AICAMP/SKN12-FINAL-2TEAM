from template.base.base_template import BaseTemplate
from template.portfolio.common.portfolio_serialize import (
    PortfolioGetRequest, PortfolioGetResponse,
    PortfolioAddStockRequest, PortfolioAddStockResponse,
    PortfolioRemoveStockRequest, PortfolioRemoveStockResponse,
    PortfolioRebalanceRequest, PortfolioRebalanceResponse,
    PortfolioPerformanceRequest, PortfolioPerformanceResponse
)
from template.portfolio.common.portfolio_model import Portfolio, StockOrder, PerformanceMetrics, RebalanceReport
from service.core.logger import Logger
from service.service_container import ServiceContainer
import json
import uuid
from datetime import datetime, timedelta

class PortfolioTemplateImpl(BaseTemplate):
    def __init__(self):
        super().__init__()
    
    async def on_portfolio_get_req(self, client_session, request: PortfolioGetRequest):
        """포트폴리오 조회 요청 처리"""
        response = PortfolioGetResponse()
        
        Logger.info("Portfolio get request received")
        
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            db_service = ServiceContainer.get_database_service()
            
            # 1. 계좌 정보 조회
            account_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_get_account_info",
                (account_db_key,)
            )
            
            # 2. 포트폴리오 보유 종목 조회
            holdings_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_get_portfolio_holdings",
                (account_db_key,)
            )
            
            # TODO: 포트폴리오 가치 계산 로직 구현
            # - 보유 종목별 현재가 조회
            # - 총 투자금액 계산
            # - 수익률 계산
            # - 위험 지표 계산
            
            # 계산된 결과를 가데이터로 대체
            total_value = 10000.0
            cash_balance = 5000.0 if account_result else 0.0
            invested_amount = 5000.0
            total_return = 500.0
            return_rate = 5.0
            
            # Portfolio 모델 생성
            portfolio = Portfolio(
                portfolio_id=f"port_{account_db_key}",
                name="메인 포트폴리오",
                total_value=total_value,
                cash_balance=cash_balance,
                invested_amount=invested_amount,
                total_return=total_return,
                return_rate=return_rate,
                created_at=str(datetime.now())
            )
            
            response.portfolio = portfolio
            response.holdings = holdings_result if holdings_result else []
            
            # 성과 지표 조회 (request.include_performance가 True인 경우)
            if request.include_performance:
                # TODO: 성과 지표 계산 로직 구현
                performance = PerformanceMetrics(
                    total_return=500.0,
                    annualized_return=15.0,
                    sharpe_ratio=1.2,
                    max_drawdown=-5.0,
                    win_rate=60.0,
                    profit_factor=1.5
                )
                response.performance = performance
            
            response.errorCode = 0
            Logger.info(f"Portfolio retrieved successfully for account_db_key: {account_db_key}")
            
        except Exception as e:
            response.errorCode = 1000
            Logger.error(f"Portfolio get error: {e}")
        
        return response

    async def on_portfolio_add_stock_req(self, client_session, request: PortfolioAddStockRequest):
        """종목 추가 요청 처리"""
        response = PortfolioAddStockResponse()
        
        Logger.info(f"Portfolio add stock request: {request.symbol}")
        
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            db_service = ServiceContainer.get_database_service()
            
            # 주문 ID 생성
            order_id = f"ord_{uuid.uuid4().hex[:16]}"
            
            # TODO: 주문 검증 로직 구현
            # - 계좌 잔고 확인
            # - 종목 유효성 검사
            # - 주문 가능 수량 확인
            # - 시장 시간 체크
            
            # 주식 주문 생성 (DB 저장)
            order_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_create_stock_order",
                (order_id, account_db_key, request.symbol, "BUY", request.quantity, request.price, request.order_type)
            )
            
            # 가데이터로 성공 처리
            stock_order = StockOrder(
                order_id=order_id,
                symbol=request.symbol,
                order_type="BUY",
                quantity=request.quantity,
                price=request.price,
                order_status="PENDING",
                created_at=str(datetime.now())
            )
            
            response.order = stock_order
            response.message = "종목 추가 주문이 생성되었습니다"
            response.errorCode = 0
            
            Logger.info(f"Stock order created: {order_id}")
            
        except Exception as e:
            response.errorCode = 1000
            response.message = "종목 추가 실패"
            Logger.error(f"Portfolio add stock error: {e}")
        
        return response

    async def on_portfolio_remove_stock_req(self, client_session, request: PortfolioRemoveStockRequest):
        """종목 삭제 요청 처리"""
        response = PortfolioRemoveStockResponse()
        
        Logger.info(f"Portfolio remove stock request: {request.symbol}")
        
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            db_service = ServiceContainer.get_database_service()
            
            # 주문 ID 생성
            order_id = f"ord_{uuid.uuid4().hex[:16]}"
            
            # TODO: 매도 주문 검증 로직 구현
            # - 보유 수량 확인
            # - 매도 가능 수량 체크
            # - 시장 시간 체크
            
            # 매도 주문 생성 (DB 저장)
            order_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_create_stock_order",
                (order_id, account_db_key, request.symbol, "SELL", request.quantity, request.price or 0.0, "MARKET")
            )
            
            # 가데이터로 성공 처리
            stock_order = StockOrder(
                order_id=order_id,
                symbol=request.symbol,
                order_type="SELL",
                quantity=request.quantity,
                price=request.price or 0.0,
                order_status="PENDING",
                created_at=str(datetime.now())
            )
            
            response.order = stock_order
            response.message = "종목 매도 주문이 생성되었습니다"
            response.errorCode = 0
            
            Logger.info(f"Stock sell order created: {order_id}")
            
        except Exception as e:
            response.errorCode = 1000
            response.message = "종목 삭제 실패"
            Logger.error(f"Portfolio remove stock error: {e}")
        
        return response

    async def on_portfolio_rebalance_req(self, client_session, request: PortfolioRebalanceRequest):
        """리밸런싱 분석 요청 처리"""
        response = PortfolioRebalanceResponse()
        
        Logger.info("Portfolio rebalance request received")
        
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            db_service = ServiceContainer.get_database_service()
            
            # 리밸런싱 리포트 ID 생성
            report_id = f"rebal_{uuid.uuid4().hex[:16]}"
            
            # TODO: 리밸런싱 분석 로직 구현
            # - 현재 포트폴리오 구성 조회
            # - 목표 배분과 현재 배분 비교
            # - 필요한 거래 목록 계산
            # - 수수료 및 세금 계산
            # - 예상 개선 효과 계산
            
            # 리밸런싱 리포트 DB 저장
            await db_service.call_shard_procedure(
                shard_id,
                "fp_save_rebalance_report",
                (report_id, account_db_key, json.dumps(request.target_allocation), 
                 json.dumps([]), 100.0, "USER_REQUEST")  # 가데이터
            )
            
            # 가데이터로 응답 생성
            rebalance_report = RebalanceReport(
                report_id=report_id,
                trigger_reason="USER_REQUEST",
                recommendations=[
                    {"action": "SELL", "symbol": "AAPL", "quantity": 5, "current_weight": 60.0, "target_weight": 40.0},
                    {"action": "BUY", "symbol": "GOOGL", "quantity": 3, "current_weight": 20.0, "target_weight": 30.0}
                ],
                expected_improvement=2.5,
                generated_at=str(datetime.now())
            )
            
            response.report = rebalance_report
            response.trades_required = [
                {"symbol": "AAPL", "action": "SELL", "quantity": 5, "estimated_price": 150.0},
                {"symbol": "GOOGL", "action": "BUY", "quantity": 3, "estimated_price": 240.0}
            ]
            response.estimated_cost = 15.0
            response.errorCode = 0
            
            Logger.info(f"Rebalance report generated: {report_id}")
            
        except Exception as e:
            response.errorCode = 1000
            response.estimated_cost = 0.0
            Logger.error(f"Portfolio rebalance error: {e}")
        
        return response

    async def on_portfolio_performance_req(self, client_session, request: PortfolioPerformanceRequest):
        """성과 분석 요청 처리"""
        response = PortfolioPerformanceResponse()
        
        Logger.info(f"Portfolio performance request: period={request.period}")
        
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            db_service = ServiceContainer.get_database_service()
            
            # TODO: 성과 분석 로직 구현
            # - 지정된 기간의 포트폴리오 성과 데이터 조회
            # - 벤치마크 대비 성과 비교 계산
            # - 위험 지표 계산 (샤프 비율, 최대 낙폭, 변동성 등)
            # - 월별/일별 수익률 계산
            # - 차트 데이터 생성
            
            # 성과 데이터 DB 저장
            await db_service.call_shard_procedure(
                shard_id,
                "fp_save_portfolio_performance",
                (account_db_key, str(datetime.now().date()), 10000.0, 15.0, 1.2, -5.0, 12.5)  # 가데이터
            )
            
            # 가데이터로 응답 생성
            performance = PerformanceMetrics(
                total_return=500.0,
                annualized_return=15.0,
                sharpe_ratio=1.2,
                max_drawdown=-5.0,
                win_rate=65.0,
                profit_factor=1.8
            )
            
            response.performance = performance
            response.benchmark_comparison = {
                "portfolio_return": 15.0,
                "benchmark_return": 10.0,
                "outperformance": 5.0,
                "beta": 1.1,
                "alpha": 4.5
            }
            response.monthly_returns = [
                {"month": "2024-01", "return": 2.5},
                {"month": "2024-02", "return": -1.2},
                {"month": "2024-03", "return": 3.8},
                {"month": "2024-04", "return": 1.5}
            ]
            response.risk_metrics = {
                "volatility": 12.5,
                "var_95": -2.1,
                "tracking_error": 3.2,
                "information_ratio": 1.56
            }
            response.errorCode = 0
            
            Logger.info(f"Performance analysis completed for period: {request.period}")
            
        except Exception as e:
            response.errorCode = 1000
            Logger.error(f"Portfolio performance error: {e}")
        
        return response