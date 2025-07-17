from datetime import datetime
from template.base.base_template import BaseTemplate
from template.dashboard.common.dashboard_serialize import (
    DashboardMainRequest, DashboardMainResponse,
    DashboardAlertsRequest, DashboardAlertsResponse,
    DashboardPerformanceRequest, DashboardPerformanceResponse
)
from template.dashboard.common.dashboard_model import AssetSummary, StockHolding, MarketAlert, MarketOverview
from service.service_container import ServiceContainer
from service.core.logger import Logger

class DashboardTemplateImpl(BaseTemplate):
    def __init__(self):
        super().__init__()

    async def on_dashboard_main_req(self, client_session, request: DashboardMainRequest):
        """대시보드 메인 데이터 요청 처리"""
        response = DashboardMainResponse()
        response.sequence = request.sequence
        
        Logger.info(f"Dashboard main request: period={request.chart_period}")
        
        try:
            # 세션에서 사용자 정보 가져오기 (세션 검증은 template_service에서 이미 완료)
            account_db_key = getattr(client_session.session, 'account_db_key', 0)
            shard_id = getattr(client_session.session, 'shard_id', 1)
            
            db_service = ServiceContainer.get_database_service()
            
            # 1. 대시보드 메인 데이터 조회 DB 프로시저 호출
            dashboard_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_get_dashboard_main",
                (account_db_key, True, request.chart_period)  # include_chart=True
            )
            
            if not dashboard_result or len(dashboard_result) < 4:
                response.errorCode = 2002
                Logger.info("Dashboard main data not found")
                return response
            
            # 2. DB 결과 처리
            asset_data = dashboard_result[0][0] if dashboard_result[0] else {}
            holdings_data = dashboard_result[1] if len(dashboard_result) > 1 else []
            alerts_data = dashboard_result[2] if len(dashboard_result) > 2 else []
            market_data = dashboard_result[3] if len(dashboard_result) > 3 else []
            chart_data = dashboard_result[4] if len(dashboard_result) > 4 else []
            
            # 3. 자산 요약 정보 생성
            asset_summary = AssetSummary(
                total_assets=float(asset_data.get('total_assets', 0.0)),
                cash_balance=float(asset_data.get('cash_balance', 0.0)),
                stock_value=float(asset_data.get('stock_value', 0.0)),
                total_return=float(asset_data.get('total_return', 0.0)),
                return_rate=float(asset_data.get('return_rate', 0.0)),
                currency=asset_data.get('currency', 'KRW')
            )
            
            # 4. 보유 종목 정보 생성
            holdings = []
            for holding in holdings_data:
                holdings.append(StockHolding(
                    symbol=holding.get('symbol'),
                    name=holding.get('name'),
                    quantity=int(holding.get('quantity', 0)),
                    avg_price=float(holding.get('avg_price', 0.0)),
                    current_price=float(holding.get('current_price', 0.0)),
                    market_value=float(holding.get('market_value', 0.0)),
                    unrealized_pnl=float(holding.get('unrealized_pnl', 0.0)),
                    return_rate=round(float(holding.get('return_rate', 0.0)), 2)
                ))
            
            # 5. 최근 알림 정보 생성
            recent_alerts = []
            for alert in alerts_data:
                recent_alerts.append(MarketAlert(
                    alert_id=alert.get('alert_id'),
                    type=alert.get('type'),
                    title=alert.get('title'),
                    message=alert.get('message'),
                    severity=alert.get('severity', 'INFO'),
                    created_at=str(alert.get('created_at')),
                    symbol=alert.get('symbol', '')
                ))
            
            # 6. 시장 개요 정보 생성
            market_overview = []
            for market in market_data:
                market_overview.append(MarketOverview(
                    symbol=market.get('symbol'),
                    name=market.get('name'),
                    current_price=float(market.get('current_price', 0.0)),
                    change_amount=float(market.get('change_amount', 0.0)),
                    change_rate=float(market.get('change_rate', 0.0)),
                    volume=int(market.get('volume', 0))
                ))
            
            # 7. 포트폴리오 차트 데이터 처리
            portfolio_chart = []
            if chart_data:
                for chart_point in chart_data:
                    portfolio_chart.append({
                        "date": str(chart_point.get('date')),
                        "value": float(chart_point.get('total_value', 0.0)),
                        "return_rate": float(chart_point.get('return_rate', 0.0))
                    })
            
            # 8. 자산 배분 차트 데이터 생성
            allocation_chart = []
            total_stock_value = sum(float(h.get('market_value', 0)) for h in holdings_data)
            if total_stock_value > 0:
                for holding in holdings_data[:5]:  # 상위 5개만
                    allocation_chart.append({
                        "symbol": holding.get('symbol'),
                        "name": holding.get('name'),
                        "value": float(holding.get('market_value', 0.0)),
                        "percentage": round(float(holding.get('market_value', 0.0)) / total_stock_value * 100, 1)
                    })
            
            response.errorCode = 0
            response.asset_summary = asset_summary
            response.holdings = holdings
            response.portfolio_chart = []
            response.allocation_chart = []
            response.recent_alerts = recent_alerts
            response.market_overview = market_overview
            
            Logger.info(f"Dashboard main data retrieved for account_db_key={account_db_key}")
            
        except Exception as e:
            response.errorCode = 1000
            Logger.error(f"Dashboard main error: {e}")
        
        return response

    async def on_dashboard_alerts_req(self, client_session, request: DashboardAlertsRequest):
        """알림 목록 요청 처리"""
        response = DashboardAlertsResponse()
        response.sequence = request.sequence
        
        Logger.info(f"Dashboard alerts request: page={request.page}, type={request.alert_type}")
        
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            db_service = ServiceContainer.get_database_service()
            
            # 1. 알림 목록 조회 (대시보드 알림 테이블에서)
            # 실제로는 별도의 fp_get_dashboard_alerts 프로시저가 필요하지만
            # 여기서는 기존 대시보드 메인 데이터에서 알림 정보를 활용
            
            dashboard_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_get_dashboard_main",
                (account_db_key, False, "1D")  # chart 데이터는 불필요
            )
            
            alerts = []
            if dashboard_result and len(dashboard_result) > 2:
                alerts_data = dashboard_result[2]  # 알림 데이터는 3번째 결과셋
                
                for alert_data in alerts_data:
                    # 타입 필터링 적용
                    if request.alert_type and request.alert_type != "ALL":
                        if alert_data.get('type') != request.alert_type:
                            continue
                    
                    alerts.append(MarketAlert(
                        alert_id=alert_data.get('alert_id'),
                        type=alert_data.get('type'),
                        title=alert_data.get('title'),
                        message=alert_data.get('message'),
                        severity=alert_data.get('severity', 'INFO'),
                        created_at=str(alert_data.get('created_at')),
                        symbol=alert_data.get('symbol', '')
                    ))
            
            # 페이지네이션 적용
            start_idx = (request.page - 1) * request.limit
            end_idx = start_idx + request.limit
            paginated_alerts = alerts[start_idx:end_idx]
            
            # 안읽음 알림 수 계산 (간단한 예시)
            unread_count = len([a for a in alerts if a.severity in ['WARNING', 'ERROR']])
            
            response.errorCode = 0
            response.alerts = paginated_alerts
            response.total_count = len(alerts)
            response.unread_count = unread_count
            
        except Exception as e:
            response.errorCode = 1000
            Logger.error(f"Dashboard alerts error: {e}")
        
        return response

    async def on_dashboard_performance_req(self, client_session, request: DashboardPerformanceRequest):
        """성과 분석 요청 처리"""
        response = DashboardPerformanceResponse()
        response.sequence = request.sequence
        
        Logger.info(f"Dashboard performance request: period={request.period}")
        
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            db_service = ServiceContainer.get_database_service()
            
            # 1. 성과 분석 데이터 조회 (포트폴리오 성과 테이블에서)
            # 실제로는 fp_get_performance_analysis 프로시저가 필요하지만
            # 여기서는 기존 데이터를 활용
            
            # 포트폴리오 성과 데이터 조회
            performance_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_get_portfolio_performance",
                (account_db_key, request.period)
            )
            
            if not performance_result:
                # 기본값으로 설정
                response.portfolio_return = 0.0
                response.benchmark_return = 0.0
                response.sharpe_ratio = 0.0
                response.max_drawdown = 0.0
                response.volatility = 0.0
                response.performance_chart = []
                response.errorCode = 0
                return response
            
            # 2. 성과 지표 계산
            perf_data = performance_result[0] if performance_result else {}
            
            portfolio_return = float(perf_data.get('return_rate', 0.0))
            benchmark_return = float(perf_data.get('benchmark_return', 0.0))
            sharpe_ratio = float(perf_data.get('sharpe_ratio', 0.0))
            max_drawdown = float(perf_data.get('max_drawdown', 0.0))
            volatility = float(perf_data.get('volatility', 0.0))
            
            # 3. 성과 차트 데이터 생성
            performance_chart = []
            if len(performance_result) > 1:
                chart_data = performance_result[1:]
                for chart_point in chart_data:
                    performance_chart.append({
                        "date": str(chart_point.get('date')),
                        "portfolio_value": float(chart_point.get('total_value', 0.0)),
                        "return_rate": float(chart_point.get('return_rate', 0.0)),
                        "benchmark_value": float(chart_point.get('total_value', 0.0)) * (1 + benchmark_return / 100)
                    })
            
            response.portfolio_return = round(portfolio_return, 2)
            response.benchmark_return = round(benchmark_return, 2)
            response.sharpe_ratio = round(sharpe_ratio, 2)
            response.max_drawdown = round(max_drawdown, 2)
            response.volatility = round(volatility, 2)
            response.performance_chart = performance_chart
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            Logger.error(f"Dashboard performance error: {e}")
        
        return response