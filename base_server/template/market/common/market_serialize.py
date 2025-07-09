from service.net.protocol_base import BaseRequest, BaseResponse
from .market_model import SecurityInfo, PriceData, TechnicalIndicators, NewsItem
from typing import Optional, List, Dict, Any

# ============================================================================
# REQ-MKT-001: 종목 검색
# 의거: 화면 015 (시장 현황), REQ-MKT-001
# ============================================================================

class MarketSearchSecuritiesRequest(BaseRequest):
    """종목 검색 요청"""
    query: str
    exchange: str = ""  # KRX, NASDAQ, NYSE 등
    sector: str = ""
    limit: int = 20

class MarketSearchSecuritiesResponse(BaseResponse):
    """종목 검색 응답"""
    securities: List[SecurityInfo] = []
    total_count: int = 0

# ============================================================================
# REQ-MKT-002: 가격 데이터 조회
# 의거: 화면 015 (차트 데이터), REQ-MKT-002
# ============================================================================

class MarketGetPriceDataRequest(BaseRequest):
    """가격 데이터 조회 요청"""
    symbols: List[str]
    period: str = "1D"  # 1D, 1W, 1M, 3M, 1Y
    interval: str = "1d"  # 1m, 5m, 1h, 1d

class MarketGetPriceDataResponse(BaseResponse):
    """가격 데이터 조회 응답"""
    price_data: List[PriceData] = []
    total_count: int = 0

# ============================================================================
# REQ-MKT-003: 실시간 가격 조회
# 의거: 화면 003 (대시보드), REQ-MKT-003
# ============================================================================

class MarketGetRealtimePriceRequest(BaseRequest):
    """실시간 가격 조회 요청"""
    symbols: List[str]

class MarketGetRealtimePriceResponse(BaseResponse):
    """실시간 가격 조회 응답"""
    prices: List[PriceData] = []
    timestamp: str = ""

# ============================================================================
# REQ-MKT-004: 기술적 지표 조회
# 의거: 화면 015 (기술적 분석), REQ-MKT-004
# ============================================================================

class MarketGetTechnicalIndicatorsRequest(BaseRequest):
    """기술적 지표 조회 요청"""
    symbols: List[str]

class MarketGetTechnicalIndicatorsResponse(BaseResponse):
    """기술적 지표 조회 응답"""
    indicators: List[TechnicalIndicators] = []

# ============================================================================
# REQ-MKT-005: 시장 개요 조회
# 의거: 화면 003 (대시보드 시장 현황), REQ-MKT-005
# ============================================================================

class MarketGetOverviewRequest(BaseRequest):
    """시장 개요 조회 요청"""
    markets: List[str] = ["KOSPI", "KOSDAQ", "S&P500", "NASDAQ"]

class MarketGetOverviewResponse(BaseResponse):
    """시장 개요 조회 응답"""
    market_data: List[Dict[str, Any]] = []
    summary: Dict[str, Any] = {}  # 전체 시장 요약

# ============================================================================
# REQ-MKT-006: 뉴스 조회
# 의거: 화면 016 (뉴스), REQ-MKT-006
# ============================================================================

class MarketGetNewsRequest(BaseRequest):
    """뉴스 조회 요청"""
    symbols: List[str] = []  # 특정 종목 뉴스, 빈 배열이면 전체 뉴스
    category: str = "ALL"  # MARKET, ECONOMY, TECH, POLITICS, CORPORATE, EARNINGS
    page: int = 1
    limit: int = 20

class MarketGetNewsResponse(BaseResponse):
    """뉴스 조회 응답"""
    news: List[NewsItem] = []
    total_count: int = 0
    page: int = 1
    total_pages: int = 1
    sentiment_summary: Dict[str, Any] = {}  # 감정 분석 요약 (긍정/부정/중립 비율)

# ============================================================================
# REQ-MKT-007: 인기 종목 조회
# 의거: 화면 015 (인기 종목), REQ-MKT-007
# ============================================================================

class MarketGetTrendingRequest(BaseRequest):
    """인기 종목 조회 요청"""
    category: str = "VOLUME"  # VOLUME, PRICE_CHANGE, MARKET_CAP
    exchange: str = ""
    limit: int = 10

class MarketGetTrendingResponse(BaseResponse):
    """인기 종목 조회 응답"""
    trending_securities: List[SecurityInfo] = []
    price_info: List[PriceData] = []

# ============================================================================
# REQ-MKT-008: 섹터별 현황 조회
# 의거: 화면 015 (섹터 분석), REQ-MKT-008
# ============================================================================

class MarketGetSectorPerformanceRequest(BaseRequest):
    """섹터별 현황 조회 요청"""
    period: str = "1D"  # 1D, 1W, 1M, 3M, 1Y

class MarketGetSectorPerformanceResponse(BaseResponse):
    """섹터별 현황 조회 응답"""
    sector_data: List[Dict[str, Any]] = []
    top_performers: List[Dict[str, Any]] = []  # 상승률 상위 섹터
    worst_performers: List[Dict[str, Any]] = []  # 하락률 상위 섹터

# ============================================================================
# REQ-MKT-009: 경제 지표 조회
# 의거: 화면 015 (경제 지표), REQ-MKT-009
# ============================================================================

class MarketGetEconomicIndicatorsRequest(BaseRequest):
    """경제 지표 조회 요청"""
    indicators: List[str] = ["GDP", "INFLATION", "INTEREST_RATE"]
    period: str = "1Y"

class MarketGetEconomicIndicatorsResponse(BaseResponse):
    """경제 지표 조회 응답"""
    indicators: List[Dict[str, Any]] = []
    forecast: Dict[str, Any] = {}  # 예측 데이터

# ============================================================================
# REQ-MKT-010: 종목 상세 정보 조회
# 의거: 화면 015 (종목 상세), REQ-MKT-010
# ============================================================================

class MarketGetSecurityDetailRequest(BaseRequest):
    """종목 상세 정보 조회 요청"""
    symbol: str

class MarketGetSecurityDetailResponse(BaseResponse):
    """종목 상세 정보 조회 응답"""
    security: Optional[SecurityInfo] = None
    current_price: Optional[PriceData] = None
    technical_indicators: Optional[TechnicalIndicators] = None
    financial_metrics: Dict[str, Any] = {}  # PE, PBR, ROE, EPS 등
    analyst_ratings: Dict[str, Any] = {}  # 애널리스트 평가 (BUY/HOLD/SELL 비율)

# ============================================================================
# REQ-MKT-011: 가격 알림 설정
# 의거: 화면 018 (알림 설정), REQ-MKT-011
# ============================================================================

class MarketCreatePriceAlertRequest(BaseRequest):
    """가격 알림 설정 요청"""
    symbol: str
    alert_type: str  # PRICE_ABOVE, PRICE_BELOW, CHANGE_RATE_ABOVE, CHANGE_RATE_BELOW
    target_value: float
    message: str = ""

class MarketCreatePriceAlertResponse(BaseResponse):
    """가격 알림 설정 응답"""
    alert_id: str = ""
    message: str = ""

# ============================================================================
# REQ-MKT-012: 관심 종목 관리
# 의거: 화면 004 (관심 종목), REQ-MKT-012
# ============================================================================

class MarketManageWatchlistRequest(BaseRequest):
    """관심 종목 관리 요청"""
    action: str  # ADD, REMOVE, REORDER
    symbol: str = ""
    watchlist_data: List[str] = []  # 순서 변경시 전체 목록

class MarketManageWatchlistResponse(BaseResponse):
    """관심 종목 관리 응답"""
    watchlist: List[str] = []
    message: str = ""

# ============================================================================
# REQ-MKT-013: 시장 달력 조회
# 의거: 화면 016 (경제 달력), REQ-MKT-013
# ============================================================================

class MarketGetCalendarRequest(BaseRequest):
    """시장 달력 조회 요청"""
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD
    importance: str = "ALL"  # LOW, MEDIUM, HIGH, ALL

class MarketGetCalendarResponse(BaseResponse):
    """시장 달력 조회 응답"""
    events: List[Dict[str, Any]] = []
    total_count: int = 0