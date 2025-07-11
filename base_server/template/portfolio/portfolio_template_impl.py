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
            
            # 2. 포트폴리오 확장 정보 조회 (DB 프로시저 활용)
            portfolio_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_get_portfolio_extended",
                (account_db_key, request.include_performance, True)
            )
            
            if not portfolio_result:
                response.errorCode = 2003
                Logger.info("No portfolio found")
                return response
            
            # DB에서 조회된 실제 포트폴리오 데이터 사용
            portfolio_data = portfolio_result[0] if portfolio_result else {}
            
            # Portfolio 모델 생성
            portfolio = Portfolio(
                portfolio_id=portfolio_data.get('portfolio_id', f"portfolio_{account_db_key}"),
                name=portfolio_data.get('name', '메인 포트폴리오'),
                total_value=float(portfolio_data.get('total_value', 0.0)),
                cash_balance=float(portfolio_data.get('cash_balance', 0.0)),
                invested_amount=float(portfolio_data.get('invested_amount', 0.0)),
                total_return=float(portfolio_data.get('total_return', 0.0)),
                return_rate=float(portfolio_data.get('return_rate', 0.0)),
                created_at=str(portfolio_data.get('created_at', datetime.now()))
            )
            
            response.portfolio = portfolio
            
            # 보유 종목 정보도 DB 프로시저 결과에서 가져오기
            if len(portfolio_result) > 1:
                response.holdings = portfolio_result[1:]  # 첫 번째는 포트폴리오 정보, 나머지는 보유종목
            else:
                response.holdings = []
            
            # 성과 지표 조회 (request.include_performance가 True인 경우)
            if request.include_performance:
                # DB에서 성과 데이터 조회
                performance_result = await db_service.call_shard_procedure(
                    shard_id,
                    "fp_get_portfolio_performance",
                    (account_db_key, request.period or '1Y')
                )
                
                if performance_result and len(performance_result) > 2:  # 포트폴리오, 보유종목, 성과순
                    perf_data = performance_result[2]
                    performance = PerformanceMetrics(
                        total_return=float(perf_data.get('total_return', 0.0)),
                        annualized_return=float(perf_data.get('annualized_return', 0.0)),
                        sharpe_ratio=float(perf_data.get('sharpe_ratio', 0.0)),
                        max_drawdown=float(perf_data.get('max_drawdown', 0.0)),
                        win_rate=float(perf_data.get('win_rate', 0.0)),
                        profit_factor=float(perf_data.get('profit_factor', 0.0))
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
            
            # 1. 계좌 잔고 확인
            account_info = await db_service.call_shard_procedure(
                shard_id,
                "fp_get_account_info",
                (account_db_key,)
            )
            
            if not account_info or len(account_info) == 0:
                response.errorCode = 3001
                response.message = "계좌 정보를 찾을 수 없습니다"
                return response
            
            account_balance = float(account_info[0].get('balance', 0.0))
            required_amount = request.quantity * request.price
            
            if account_balance < required_amount:
                response.errorCode = 3002
                response.message = f"잔고 부족: 필요 {required_amount:,.0f}원, 보유 {account_balance:,.0f}원"
                return response
            
            # 2. 주식 주문 생성 (DB 저장) - 수정된 프로시저 호출
            order_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_create_stock_order",
                (order_id, account_db_key, request.symbol, "BUY", 
                 request.order_type or "MARKET", request.quantity, request.price, 
                 None, 0.0)  # stop_price, commission
            )
            
            if not order_result or order_result[0].get('result') != 'SUCCESS':
                response.errorCode = 3003
                response.message = "주문 생성 실패"
                return response
            
            # DB 결과를 바탕으로 주문 정보 생성
            order_data = order_result[0]
            stock_order = StockOrder(
                order_id=order_data.get('order_id', order_id),
                symbol=request.symbol,
                order_type="BUY",
                quantity=request.quantity,
                price=request.price,
                order_status=order_data.get('order_status', 'PENDING'),
                created_at=str(order_data.get('order_time', datetime.now()))
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
            
            # 1. 보유 수량 확인
            portfolio_holdings = await db_service.call_shard_procedure(
                shard_id,
                "fp_get_portfolio_extended",
                (account_db_key, False, True)
            )
            
            if not portfolio_holdings or len(portfolio_holdings) < 2:
                response.errorCode = 3004
                response.message = "보유 종목이 없습니다"
                return response
            
            # 보유 수량 확인
            holdings = portfolio_holdings[1:]  # 첫 번째는 포트폴리오 정보
            target_holding = None
            for holding in holdings:
                if holding.get('symbol') == request.symbol:
                    target_holding = holding
                    break
            
            if not target_holding:
                response.errorCode = 3005
                response.message = f"{request.symbol} 종목을 보유하고 있지 않습니다"
                return response
            
            holding_quantity = int(target_holding.get('quantity', 0))
            if holding_quantity < request.quantity:
                response.errorCode = 3006
                response.message = f"보유 수량 부족: 필요 {request.quantity}주, 보유 {holding_quantity}주"
                return response
            
            # 2. 매도 주문 생성 (DB 저장)
            order_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_create_stock_order",
                (order_id, account_db_key, request.symbol, "SELL", 
                 "MARKET", request.quantity, request.price or 0.0, 
                 None, 0.0)  # stop_price, commission
            )
            
            if not order_result or order_result[0].get('result') != 'SUCCESS':
                response.errorCode = 3007
                response.message = "매도 주문 생성 실패"
                return response
            
            # DB 결과를 바탕으로 주문 정보 생성
            order_data = order_result[0]
            stock_order = StockOrder(
                order_id=order_data.get('order_id', order_id),
                symbol=request.symbol,
                order_type="SELL",
                quantity=request.quantity,
                price=request.price or 0.0,
                order_status=order_data.get('order_status', 'PENDING'),
                created_at=str(order_data.get('order_time', datetime.now()))
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
            
            # 1. 현재 포트폴리오 구성 조회
            current_portfolio = await db_service.call_shard_procedure(
                shard_id,
                "fp_get_portfolio_extended",
                (account_db_key, False, True)
            )
            
            if not current_portfolio:
                response.errorCode = 4001
                response.estimated_cost = 0.0
                Logger.info("No portfolio found for rebalancing")
                return response
            
            # 2. 리밸런싱 리포트 생성 (DB 프로시저 활용)
            rebalance_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_create_rebalance_report",
                (account_db_key, "USER_REQUEST", json.dumps(request.target_allocation), 10000.0)  # min_trade_amount
            )
            
            if not rebalance_result or rebalance_result[0].get('result') != 'SUCCESS':
                response.errorCode = 4002
                response.estimated_cost = 0.0
                Logger.error("Failed to create rebalance report")
                return response
            
            # DB에서 리밸런싱 리포트 조회
            report_data = rebalance_result[0]
            report_id = report_data.get('report_id')
            current_value = float(report_data.get('current_value', 0.0))
            
            # 리밸런싱 권장사항 계산 (간단한 예시)
            recommendations = []
            trades_required = []
            estimated_cost = 0.0
            
            # 예시: 기존 보유 종목에 대한 리밸런싱 처리
            if len(current_portfolio) > 1:  # 보유 종목이 있는 경우
                holdings = current_portfolio[1:]
                total_value = sum(float(h.get('market_value', 0)) for h in holdings)
                
                for holding in holdings:
                    symbol = holding.get('symbol')
                    current_value_amt = float(holding.get('market_value', 0))
                    current_weight = (current_value_amt / total_value * 100) if total_value > 0 else 0
                    
                    # 목표 비중 찾기
                    target_weight = 0
                    for allocation in request.target_allocation:
                        if allocation.get('symbol') == symbol:
                            target_weight = float(allocation.get('weight', 0))
                            break
                    
                    weight_diff = target_weight - current_weight
                    if abs(weight_diff) > 1.0:  # 1% 이상 차이
                        action = "BUY" if weight_diff > 0 else "SELL"
                        quantity = int(abs(weight_diff) * total_value / 100 / float(holding.get('current_price', 1)))
                        
                        recommendations.append({
                            "action": action,
                            "symbol": symbol,
                            "quantity": quantity,
                            "current_weight": round(current_weight, 2),
                            "target_weight": target_weight
                        })
                        
                        trades_required.append({
                            "symbol": symbol,
                            "action": action,
                            "quantity": quantity,
                            "estimated_price": float(holding.get('current_price', 0))
                        })
                        
                        estimated_cost += quantity * 0.0025  # 0.25% 수수료 가정
            
            # 리밸런싱 리포트 모델 생성
            rebalance_report = RebalanceReport(
                report_id=report_id,
                trigger_reason="USER_REQUEST",
                recommendations=recommendations,
                expected_improvement=min(len(recommendations) * 0.5, 5.0),  # 간단한 계산
                generated_at=str(datetime.now())
            )
            
            response.report = rebalance_report
            response.trades_required = trades_required
            response.estimated_cost = round(estimated_cost, 2)
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
            
            # 1. 현재 포트폴리오 가치 계산 및 성과 기록
            current_portfolio = await db_service.call_shard_procedure(
                shard_id,
                "fp_get_portfolio_extended",
                (account_db_key, True, True)  # 성과 데이터 포함
            )
            
            if not current_portfolio:
                response.errorCode = 5001
                Logger.info("No portfolio found for performance analysis")
                return response
            
            # 포트폴리오 데이터 추출
            portfolio_data = current_portfolio[0]
            total_value = float(portfolio_data.get('total_value', 0.0))
            cash_balance = float(portfolio_data.get('cash_balance', 0.0))
            invested_amount = float(portfolio_data.get('invested_amount', 0.0))
            
            # 2. 성과 데이터 DB 저장
            performance_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_record_portfolio_performance",
                (account_db_key, str(datetime.now().date()), total_value, cash_balance, invested_amount)
            )
            
            if not performance_result:
                response.errorCode = 5002
                Logger.error("Failed to record portfolio performance")
                return response
            
            # 3. 기간별 성과 데이터 조회 (예: 최근 1년)
            period_days = {
                '1D': 1, '1W': 7, '1M': 30, '3M': 90, '6M': 180, '1Y': 365
            }.get(request.period, 365)
            
            # 기간별 성과 데이터 예시 (실제로는 일별 데이터를 집계)
            return_rate = float(performance_result[0].get('return_rate', 0.0))
            annualized_return = return_rate * (365 / period_days) if period_days > 0 else 0.0
            
            # 성과 지표 계산
            performance = PerformanceMetrics(
                total_return=total_value - invested_amount if invested_amount > 0 else 0.0,
                annualized_return=round(annualized_return, 2),
                sharpe_ratio=max(0.5, min(2.0, abs(return_rate) / 10.0)),  # 간단한 계산
                max_drawdown=min(-1.0, return_rate * -0.3) if return_rate < 0 else -1.0,
                win_rate=60.0 + (return_rate * 2) if return_rate > 0 else 40.0,
                profit_factor=max(1.0, 1.0 + (return_rate / 20.0)) if return_rate > 0 else 0.8
            )
            
            response.performance = performance
            
            # 벤치마크 비교 (간단한 예시 - 실제로는 시장 지수 데이터 필요)
            benchmark_return = 8.0  # KOSPI 예시 수익률
            response.benchmark_comparison = {
                "portfolio_return": round(annualized_return, 2),
                "benchmark_return": benchmark_return,
                "outperformance": round(annualized_return - benchmark_return, 2),
                "beta": round(1.0 + (return_rate / 50.0), 2),
                "alpha": round(annualized_return - benchmark_return * 1.1, 2)
            }
            
            # 월별 수익률 (예시 데이터 - 실제로는 일별 데이터에서 집계)
            current_date = datetime.now()
            monthly_returns = []
            for i in range(min(12, period_days // 30)):
                month_date = current_date - timedelta(days=30 * i)
                month_return = return_rate * (0.8 + 0.4 * (i % 3)) / 12  # 예시 계산
                monthly_returns.append({
                    "month": month_date.strftime("%Y-%m"),
                    "return": round(month_return, 2)
                })
            response.monthly_returns = monthly_returns[::-1]  # 오래된 순서로
            
            # 위험 지표
            volatility = abs(return_rate) * 2.5  # 간단한 추정
            response.risk_metrics = {
                "volatility": round(volatility, 2),
                "var_95": round(return_rate * -0.4, 2),
                "tracking_error": round(volatility * 0.3, 2),
                "information_ratio": round((annualized_return - benchmark_return) / max(1.0, volatility * 0.3), 2)
            }
            response.errorCode = 0
            
            Logger.info(f"Performance analysis completed for period: {request.period}")
            
        except Exception as e:
            response.errorCode = 1000
            Logger.error(f"Portfolio performance error: {e}")
        
        return response