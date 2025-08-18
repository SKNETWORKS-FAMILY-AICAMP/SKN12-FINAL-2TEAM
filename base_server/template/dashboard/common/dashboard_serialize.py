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

# =========================
# 증권사 API 로그인 요청/응답
# =========================
class SecuritiesLoginRequest(BaseRequest):
    """증권사 API 로그인 요청"""
    accessToken: str = ""  # 사용자 accessToken
    mode: str = "prod"

class SecuritiesLoginResponse(BaseResponse):
    """증권사 API 로그인 응답"""
    result: str = "pending"
    message: str = ""
    app_key: str = ""

class PriceRequest(BaseRequest):
    accessToken: str = ""  # 사용자 accessToken
    appkey: Optional[str] = None         # 한국투자증권 AppKey (옵션)
    ticker: str         # 조회할 종목 코드 (예: "005930")
    kisToken: Optional[str] = None       # KIS 토큰 (옵션)

class PriceResponse(BaseResponse):
    """미국 나스닥 종가 응답"""
    ticker: str = ""
    price: float = 0.0
    change: float = 0.0
    change_pct: float = 0.0
    volume: float = 0.0
    timestamp: str = ""

# =========================
# 주식 종목 추천 요청/응답
# =========================
class StockRecommendationRequest(BaseRequest):
    """주식 종목 추천 요청 (매개변수 2개만 사용)"""
    accessToken: str = ""  # 사용자 accessToken
    market: str = "KOSPI"      # 시장 구분 (KOSPI, KOSDAQ, NASDAQ)
    strategy: str = "MOMENTUM"  # 투자 전략 (MOMENTUM, VALUE, GROWTH)

class StockRecommendationResponse(BaseResponse):
    """주식 종목 추천 응답"""
    result: str = "pending"
    recommendations: List[Dict[str, Any]] = []  # [{date,ticker,reason,report,color?}]
    message: str = ""

# =========================
# 경제 일정 요청/응답
# =========================
class EconomicCalendarRequest(BaseRequest):
    """경제 일정 요청"""
    accessToken: str = ""  # 사용자 accessToken
    days: int = 7          # 조회할 일수 (기본 7일)

class EconomicCalendarResponse(BaseResponse):
    """경제 일정 응답"""
    result: str = "pending"
    events: List[Dict[str, Any]] = []  # [{date,time,country,event,impact,previous,forecast,actual}]
    message: str = ""
    source: str = ""       # 데이터 소스 (FMP API, 더미 데이터 등)
    dateRange: Dict[str, str] = {}  # {from, to}


class MarketRiskPremiumRequest(BaseRequest):
    accessToken: str = ""
    countries: List[str] = ["US", "KR", "JP", "CN", "EU"]  # 기본 국가들


class MarketRiskPremiumResponse(BaseResponse):
    result: str = "pending"
    premiums: List[Dict[str, Any]] = []
    message: str = ""
    source: str = ""
    lastUpdated: str = ""