from datetime import datetime
from template.dashboard.common.dashboard_serialize import (
    DashboardMainRequest, DashboardMainResponse,
    DashboardAlertsRequest, DashboardAlertsResponse,
    DashboardPerformanceRequest, DashboardPerformanceResponse
)
from template.dashboard.common.dashboard_model import AssetSummary, StockHolding, MarketAlert, MarketOverview
from service.service_container import ServiceContainer
from service.core.logger import Logger

class DashboardTemplateImpl:
    def __init__(self):
        pass

    async def on_dashboard_main_req(self, client_session, request: DashboardMainRequest):
        """대시보드 메인 데이터 요청 처리"""
        response = DashboardMainResponse()
        response.sequence = request.sequence
        
        Logger.info(f"Dashboard main request: period={request.chart_period}")
        
        try:
            if not client_session or not client_session.session:
                response.errorCode = 2001
                Logger.info("Dashboard main failed: no session")
                return response
            
            account_db_key = getattr(client_session.session, 'account_db_key', 0)
            shard_id = getattr(client_session.session, 'shard_id', 1)
            
            # 자산 요약 정보
            asset_summary = AssetSummary(
                total_assets=1000000.0,
                cash_balance=200000.0,
                stock_value=800000.0,
                total_return=50000.0,
                return_rate=5.0,
                currency="KRW"
            )
            
            # 보유 종목 정보
            holdings = [
                StockHolding(
                    symbol="005930",
                    name="삼성전자",
                    quantity=10,
                    avg_price=65000.0,
                    current_price=68000.0,
                    market_value=680000.0,
                    unrealized_pnl=30000.0,
                    return_rate=4.6
                ),
                StockHolding(
                    symbol="035420",
                    name="NAVER",
                    quantity=5,
                    avg_price=180000.0,
                    current_price=185000.0,
                    market_value=925000.0,
                    unrealized_pnl=25000.0,
                    return_rate=2.8
                )
            ]
            
            # 최근 알림
            recent_alerts = [
                MarketAlert(
                    alert_id="alert_1",
                    type="PRICE_CHANGE",
                    title="삼성전자 급등",
                    message="삼성전자가 3% 이상 상승했습니다",
                    severity="INFO",
                    created_at=str(datetime.now()),
                    symbol="005930"
                )
            ]
            
            # 시장 개요
            market_overview = [
                MarketOverview(
                    symbol="KOSPI",
                    name="코스피",
                    current_price=2580.0,
                    change_amount=12.5,
                    change_rate=0.48,
                    volume=500000
                )
            ]
            
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
            # 샘플 알림 데이터
            alerts = [
                MarketAlert(
                    alert_id="alert_1",
                    type="PRICE_CHANGE",
                    title="삼성전자 급등",
                    message="삼성전자가 3% 이상 상승했습니다",
                    severity="INFO",
                    created_at=str(datetime.now()),
                    symbol="005930"
                ),
                MarketAlert(
                    alert_id="alert_2",
                    type="NEWS",
                    title="시장 뉴스",
                    message="주요 IT 기업들의 실적 발표가 예정되어 있습니다",
                    severity="INFO",
                    created_at=str(datetime.now()),
                    symbol=""
                )
            ]
            
            response.errorCode = 0
            response.alerts = alerts
            response.total_count = len(alerts)
            response.unread_count = 1
            
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
            response.errorCode = 0
            response.portfolio_return = 5.2
            response.benchmark_return = 3.8
            response.sharpe_ratio = 1.2
            response.max_drawdown = -8.5
            response.volatility = 12.3
            response.performance_chart = []
            
        except Exception as e:
            response.errorCode = 1000
            Logger.error(f"Dashboard performance error: {e}")
        
        return response