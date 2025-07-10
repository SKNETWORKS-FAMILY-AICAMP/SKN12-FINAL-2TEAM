from typing import Optional, List, Dict, Any
from service.net.protocol_base import BaseRequest, BaseResponse
from .autotrade_model import TradingStrategy, StrategyPerformance, TradeExecution, StrategyBacktest

# ============================================================================
# 자동매매 관리 (REQ-AUTO-001~003)
# 의거: 화면 008-1,2 (자동매매), REQ-AUTO-001~003
# ============================================================================

class AutoTradeStrategyListRequest(BaseRequest):
    """매매 전략 목록 요청"""
    include_performance: bool = True
    status_filter: str = "ALL"  # ALL, ACTIVE, INACTIVE

class AutoTradeStrategyListResponse(BaseResponse):
    """매매 전략 목록 응답"""
    strategies: List[TradingStrategy] = []
    performances: Dict[str, StrategyPerformance] = {}

class AutoTradeStrategyCreateRequest(BaseRequest):
    """새 매매 전략 생성"""
    name: str
    description: str
    algorithm_type: str
    parameters: Dict[str, Any]
    target_symbols: List[str] = []
    max_position_size: float = 0.1
    stop_loss: float = -0.05
    take_profit: float = 0.15

class AutoTradeStrategyCreateResponse(BaseResponse):
    """매매 전략 생성 응답"""
    strategy: Optional[TradingStrategy] = None
    backtest_result: Optional[StrategyBacktest] = None

class AutoTradeStrategyUpdateRequest(BaseRequest):
    """매매 전략 수정"""
    strategy_id: str
    name: Optional[str] = None
    is_active: Optional[bool] = None
    parameters: Optional[Dict[str, Any]] = None
    max_position_size: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

class AutoTradeStrategyUpdateResponse(BaseResponse):
    """매매 전략 수정 응답"""
    strategy: Optional[TradingStrategy] = None
    message: str = ""

class AutoTradeExecutionListRequest(BaseRequest):
    """거래 실행 내역 조회"""
    strategy_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    page: int = 1
    limit: int = 50

class AutoTradeExecutionListResponse(BaseResponse):
    """거래 실행 내역 응답"""
    executions: List[TradeExecution] = []
    total_count: int = 0
    summary: Dict[str, Any] = {}

class AutoTradeBacktestRequest(BaseRequest):
    """백테스트 실행 요청"""
    strategy_id: str
    start_date: str
    end_date: str
    initial_capital: float = 1000000.0
    benchmark: str = "KOSPI"

class AutoTradeBacktestResponse(BaseResponse):
    """백테스트 결과 응답"""
    backtest: Optional[StrategyBacktest] = None
    daily_returns: List[Dict[str, Any]] = []
    trade_history: List[Dict[str, Any]] = []

# ============================================================================
# AI 전략 생성 (화면 008-2 모달)
# ============================================================================

class AutoTradeAIStrategyRequest(BaseRequest):
    """AI 전략 생성 요청"""
    investment_goal: str
    risk_tolerance: str
    preferred_sectors: List[str] = []
    investment_amount: float
    time_horizon: str

class AutoTradeAIStrategyResponse(BaseResponse):
    """AI 전략 생성 응답"""
    strategy_suggestions: List[TradingStrategy] = []
    expected_performance: Dict[str, float] = {}
    risk_analysis: Dict[str, Any] = {}

