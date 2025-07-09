from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class Portfolio(BaseModel):
    """포트폴리오 정보"""
    portfolio_id: str = ""
    name: str = "메인 포트폴리오"
    total_value: float = 0.0
    cash_balance: float = 0.0
    invested_amount: float = 0.0
    total_return: float = 0.0
    return_rate: float = 0.0
    created_at: str = ""

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
    weight: float = 0.0  # 포트폴리오 내 비중

class StockOrder(BaseModel):
    """주식 주문"""
    order_id: str = ""
    symbol: str = ""
    order_type: str = ""  # BUY, SELL
    price_type: str = "MARKET"  # MARKET, LIMIT, STOP
    quantity: int = 0
    price: float = 0.0
    stop_price: float = 0.0
    filled_quantity: int = 0
    avg_fill_price: float = 0.0
    order_status: str = ""  # PENDING, PARTIAL, FILLED, CANCELLED, REJECTED
    order_source: str = "MANUAL"  # MANUAL, AUTO_STRATEGY, REBALANCE
    commission: float = 0.0
    order_time: str = ""
    fill_time: str = ""

class PerformanceMetrics(BaseModel):
    """성과 지표"""
    total_return: float = 0.0
    annualized_return: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    volatility: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    benchmark_return: float = 0.0

class RebalanceReport(BaseModel):
    """리밸런싱 리포트"""
    report_id: str = ""
    trigger_reason: str = ""
    recommendations: List[Dict[str, Any]] = []
    expected_improvement: float = 0.0
    target_allocation: Dict[str, float] = {}  # 목표 배분
    trades_required: List[Dict[str, Any]] = []  # 필요한 거래
    estimated_cost: float = 0.0
    status: str = "PENDING"  # PENDING, APPLIED, REJECTED
    generated_at: str = ""
    applied_at: str = ""

class AllocationHistory(BaseModel):
    """자산 배분 히스토리"""
    symbol: str = ""
    allocation_date: str = ""
    target_weight: float = 0.0
    actual_weight: float = 0.0
    target_value: float = 0.0
    actual_value: float = 0.0
    deviation: float = 0.0

class TransactionHistory(BaseModel):
    """거래 내역"""
    transaction_id: str = ""
    symbol: str = ""
    transaction_type: str = ""  # BUY, SELL, DIVIDEND, FEE
    quantity: int = 0
    price: float = 0.0
    amount: float = 0.0
    commission: float = 0.0
    net_amount: float = 0.0
    transaction_date: str = ""
    description: str = ""

class DividendInfo(BaseModel):
    """배당 정보"""
    symbol: str = ""
    dividend_date: str = ""
    amount_per_share: float = 0.0
    total_amount: float = 0.0
    currency: str = "KRW"
    dividend_type: str = "CASH"  # CASH, STOCK