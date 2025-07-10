from typing import Optional, List, Dict, Any
from service.net.protocol_base import BaseRequest, BaseResponse
from .market_model import SecurityInfo, PriceData, TechnicalIndicators, NewsItem

# ============================================================================
# 시장 데이터 조회
# ============================================================================

class MarketSecuritySearchRequest(BaseRequest):
    """종목 검색 요청"""
    query: str
    exchange: Optional[str] = None
    sector: Optional[str] = None
    limit: int = 20

class MarketSecuritySearchResponse(BaseResponse):
    """종목 검색 응답"""
    securities: List[SecurityInfo] = []
    total_count: int = 0

class MarketPriceRequest(BaseRequest):
    """시세 조회 요청"""
    symbols: List[str]
    period: str = "1D"  # 1D, 1W, 1M, 3M, 1Y
    interval: str = "1h"  # 1m, 5m, 1h, 1d

class MarketPriceResponse(BaseResponse):
    """시세 조회 응답"""
    price_data: Dict[str, List[PriceData]] = {}
    technical_indicators: Dict[str, TechnicalIndicators] = {}

class MarketOverviewRequest(BaseRequest):
    """시장 개요 요청"""
    indices: List[str] = ["KOSPI", "KOSDAQ", "KRX100"]
    include_movers: bool = True

class MarketOverviewResponse(BaseResponse):
    """시장 개요 응답"""
    indices: Dict[str, PriceData] = {}
    top_gainers: List[PriceData] = []
    top_losers: List[PriceData] = []
    most_active: List[PriceData] = []
    market_sentiment: str = "NEUTRAL"

class MarketNewsRequest(BaseRequest):
    """뉴스 조회 요청"""
    symbols: Optional[List[str]] = None
    category: str = "ALL"  # ALL, MARKET, ECONOMY, TECH
    page: int = 1
    limit: int = 20

class MarketNewsResponse(BaseResponse):
    """뉴스 조회 응답"""
    news: List[NewsItem] = []
    total_count: int = 0
    sentiment_summary: Dict[str, float] = {}