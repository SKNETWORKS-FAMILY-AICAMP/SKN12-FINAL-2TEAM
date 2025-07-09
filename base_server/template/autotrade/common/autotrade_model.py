from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class TradingStrategy(BaseModel):
    """매매 전략"""
    strategy_id: str = ""
    name: str = ""
    description: str = ""
    algorithm_type: str = "AI_GENERATED"  # MOMENTUM, MEAN_REVERSION, AI_GENERATED
    parameters: Dict[str, Any] = {}
    target_symbols: List[str] = []
    is_active: bool = False
    max_position_size: float = 0.1  # 최대 포지션 비율
    stop_loss: float = -0.05  # -5%
    take_profit: float = 0.15  # +15%
    created_at: str = ""

class StrategyPerformance(BaseModel):
    """전략 성과"""
    strategy_id: str = ""
    total_return: float = 0.0
    win_rate: float = 0.0
    total_trades: int = 0
    avg_holding_period: int = 0  # 일
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    last_updated: str = ""

class TradeExecution(BaseModel):
    """거래 실행 내역"""
    execution_id: str = ""
    strategy_id: str = ""
    symbol: str = ""
    action: str = ""  # BUY, SELL
    quantity: int = 0
    price: float = 0.0
    confidence_score: float = 0.0
    reasoning: str = ""
    executed_at: str = ""
    status: str = "EXECUTED"  # PENDING, EXECUTED, FAILED

class StrategyBacktest(BaseModel):
    """백테스트 결과"""
    backtest_id: str = ""
    strategy_id: str = ""
    period: str = ""
    initial_capital: float = 0.0
    final_value: float = 0.0
    total_return: float = 0.0
    benchmark_return: float = 0.0
    max_drawdown: float = 0.0
    trades_count: int = 0
    win_rate: float = 0.0