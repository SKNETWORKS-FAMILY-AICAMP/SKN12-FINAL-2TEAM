from typing import Optional, List, Dict, Any
from service.net.protocol_base import BaseRequest, BaseResponse
from .portfolio_model import Portfolio, StockOrder, PerformanceMetrics, RebalanceReport
from template.dashboard.common.dashboard_model import StockHolding

# ============================================================================
# 포트폴리오 조회 (REQ-PORT-001~007)
# 의거: 화면 006 (포트폴리오), REQ-PORT-001~007
# ============================================================================

class PortfolioGetRequest(BaseRequest):
    """포트폴리오 조회 요청"""
    include_performance: bool = True
    include_holdings: bool = True

class PortfolioGetResponse(BaseResponse):
    """포트폴리오 조회 응답"""
    portfolio: Optional[Portfolio] = None
    holdings: List[StockHolding] = []
    performance: Optional[PerformanceMetrics] = None
    chart_data: List[Dict[str, Any]] = []

class PortfolioAddStockRequest(BaseRequest):
    """종목 추가 요청"""
    symbol: str
    quantity: int
    price: float
    order_type: str = "MARKET"  # MARKET, LIMIT

class PortfolioAddStockResponse(BaseResponse):
    """종목 추가 응답"""
    order: Optional[StockOrder] = None
    updated_portfolio: Optional[Portfolio] = None
    message: str = ""

class PortfolioRemoveStockRequest(BaseRequest):
    """종목 삭제 요청"""
    symbol: str
    quantity: int
    price: Optional[float] = None

class PortfolioRemoveStockResponse(BaseResponse):
    """종목 삭제 응답"""
    order: Optional[StockOrder] = None
    updated_portfolio: Optional[Portfolio] = None
    message: str = ""

class PortfolioRebalanceRequest(BaseRequest):
    """리밸런싱 분석 요청"""
    target_allocation: Dict[str, float] = {}  # symbol: weight
    min_trade_amount: float = 10000.0

class PortfolioRebalanceResponse(BaseResponse):
    """리밸런싱 분석 응답"""
    report: Optional[RebalanceReport] = None
    trades_required: List[Dict[str, Any]] = []
    estimated_cost: float = 0.0

class PortfolioPerformanceRequest(BaseRequest):
    """성과 분석 요청"""
    period: str = "1Y"
    benchmark: str = "KOSPI"
    include_chart: bool = True

class PortfolioPerformanceResponse(BaseResponse):
    """성과 분석 응답"""
    performance: Optional[PerformanceMetrics] = None
    benchmark_comparison: Dict[str, float] = {}
    monthly_returns: List[Dict[str, Any]] = []
    risk_metrics: Dict[str, float] = {}