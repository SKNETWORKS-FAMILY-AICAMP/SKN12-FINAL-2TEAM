from typing import Optional, List, Dict, Any
from service.net.protocol_base import BaseRequest, BaseResponse
from .dashboard_model import AssetSummary, StockHolding, MarketAlert, MarketOverview

# ============================================================================
# 대시보드 메인 데이터 (REQ-DASH-001~005)
# 의거: 화면 005 (대시보드), REQ-DASH-001~005
# ============================================================================

class DashboardMainRequest(BaseRequest):
    """대시보드 메인 데이터 요청"""
    include_chart: bool = True
    chart_period: str = "1D"  # 1D, 1W, 1M, 3M, 1Y

class DashboardMainResponse(BaseResponse):
    """대시보드 메인 데이터 응답"""
    asset_summary: Optional[AssetSummary] = None
    holdings: List[StockHolding] = []
    portfolio_chart: List[Dict[str, Any]] = []  # 시간별 포트폴리오 가치
    allocation_chart: List[Dict[str, Any]] = []  # 종목별 배분
    recent_alerts: List[MarketAlert] = []
    market_overview: List[MarketOverview] = []

class DashboardAlertsRequest(BaseRequest):
    """알림 목록 요청"""
    page: int = 1
    limit: int = 20
    alert_type: str = "ALL"

class DashboardAlertsResponse(BaseResponse):
    """알림 목록 응답"""
    alerts: List[MarketAlert] = []
    total_count: int = 0
    unread_count: int = 0

class DashboardPerformanceRequest(BaseRequest):
    """성과 분석 요청"""
    period: str = "1M"
    benchmark: str = "KOSPI"

class DashboardPerformanceResponse(BaseResponse):
    """성과 분석 응답"""
    portfolio_return: float = 0.0
    benchmark_return: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    volatility: float = 0.0
    performance_chart: List[Dict[str, Any]] = []