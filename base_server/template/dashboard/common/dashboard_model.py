from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class AssetSummary(BaseModel):
    """자산 요약"""
    total_assets: float = 0.0
    cash_balance: float = 0.0
    stock_value: float = 0.0
    total_return: float = 0.0
    return_rate: float = 0.0
    currency: str = "KRW"

class StockHolding(BaseModel):
    """보유 종목"""
    symbol: str = ""
    name: str = ""
    quantity: int = 0
    avg_price: float = 0.0
    current_price: float = 0.0
    market_value: float = 0.0
    unrealized_pnl: float = 0.0
    return_rate: float = 0.0

class MarketAlert(BaseModel):
    """시장 알림"""
    alert_id: str = ""
    type: str = ""  # PRICE_CHANGE, NEWS, TARGET_REACHED
    title: str = ""
    message: str = ""
    severity: str = "INFO"  # INFO, WARNING, CRITICAL
    created_at: str = ""
    symbol: str = ""

class MarketOverview(BaseModel):
    """주요 종목 현황"""
    symbol: str = ""
    name: str = ""
    current_price: float = 0.0
    change_amount: float = 0.0
    change_rate: float = 0.0
    volume: int = 0