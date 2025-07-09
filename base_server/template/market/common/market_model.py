from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class SecurityInfo(BaseModel):
    """종목 기본 정보"""
    symbol: str = ""
    name: str = ""
    exchange: str = ""
    sector: str = ""
    industry: str = ""
    market_cap: int = 0
    currency: str = "KRW"
    description: str = ""

class PriceData(BaseModel):
    """가격 데이터"""
    symbol: str = ""
    timestamp: str = ""
    open_price: float = 0.0
    high_price: float = 0.0
    low_price: float = 0.0
    close_price: float = 0.0
    volume: int = 0
    change_amount: float = 0.0
    change_rate: float = 0.0

class TechnicalIndicators(BaseModel):
    """기술적 지표"""
    symbol: str = ""
    rsi: float = 0.0
    macd: float = 0.0
    macd_signal: float = 0.0
    bollinger_upper: float = 0.0
    bollinger_lower: float = 0.0
    ma5: float = 0.0
    ma20: float = 0.0
    ma60: float = 0.0

class NewsItem(BaseModel):
    """뉴스 아이템"""
    news_id: str = ""
    title: str = ""
    content: str = ""
    summary: str = ""
    source: str = ""
    published_at: str = ""
    sentiment_score: float = 0.0  # -1.0 ~ 1.0
    related_symbols: List[str] = []
    url: str = ""