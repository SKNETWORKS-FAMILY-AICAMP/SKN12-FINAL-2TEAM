from service.net.protocol_base import BaseRequest, BaseResponse
from .autotrade_model import TradingStrategy, StrategyPerformance, TradeExecution, StrategyBacktest
from typing import Optional, List, Dict, Any

# ============================================================================
# REQ-AUTO-001: 매매 전략 생성
# 의거: 화면 012 (자동매매 설정), REQ-AUTO-001
# ============================================================================

class AutoTradeCreateStrategyRequest(BaseRequest):
    """매매 전략 생성 요청"""
    name: str
    description: str = ""
    algorithm_type: str = "AI_GENERATED"  # MOMENTUM, MEAN_REVERSION, AI_GENERATED, RSI, MACD, BOLLINGER
    parameters: Dict[str, Any] = {}
    target_symbols: List[str] = []
    max_position_size: float = 0.1  # 최대 포지션 비율 (10%)
    stop_loss: float = -0.05  # -5%
    take_profit: float = 0.15  # +15%

class AutoTradeCreateStrategyResponse(BaseResponse):
    """매매 전략 생성 응답"""
    strategy: Optional[TradingStrategy] = None
    message: str = ""

# ============================================================================
# REQ-AUTO-002: 매매 전략 목록 조회
# 의거: 화면 012 (자동매매 관리), REQ-AUTO-002
# ============================================================================

class AutoTradeGetStrategiesRequest(BaseRequest):
    """매매 전략 목록 조회 요청"""
    include_performance: bool = False
    status_filter: str = "ALL"  # ALL, ACTIVE, INACTIVE

class AutoTradeGetStrategiesResponse(BaseResponse):
    """매매 전략 목록 조회 응답"""
    strategies: List[TradingStrategy] = []
    performances: List[StrategyPerformance] = []
    total_count: int = 0

# ============================================================================
# REQ-AUTO-003: 매매 전략 시작/중지
# 의거: 화면 012 (자동매매 제어), REQ-AUTO-003
# ============================================================================

class AutoTradeControlStrategyRequest(BaseRequest):
    """매매 전략 제어 요청"""
    strategy_id: str
    action: str  # START, STOP, DELETE

class AutoTradeControlStrategyResponse(BaseResponse):
    """매매 전략 제어 응답"""
    strategy_id: str = ""
    new_status: str = ""
    message: str = ""

# ============================================================================
# REQ-AUTO-004: 백테스트 실행
# 의거: 화면 013 (백테스트), REQ-AUTO-004
# ============================================================================

class AutoTradeBacktestRequest(BaseRequest):
    """백테스트 실행 요청"""
    strategy_id: str
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD
    initial_capital: float = 1000000.0
    benchmark: str = "KOSPI"

class AutoTradeBacktestResponse(BaseResponse):
    """백테스트 실행 응답"""
    backtest_id: str = ""
    status: str = "RUNNING"  # RUNNING, COMPLETED, FAILED
    estimated_time: int = 300  # 예상 소요 시간(초)

# ============================================================================
# REQ-AUTO-005: 백테스트 결과 조회
# 의거: 화면 013 (백테스트 결과), REQ-AUTO-005
# ============================================================================

class AutoTradeGetBacktestRequest(BaseRequest):
    """백테스트 결과 조회 요청"""
    backtest_id: str = ""
    strategy_id: str = ""  # strategy_id로 최신 백테스트 조회

class AutoTradeGetBacktestResponse(BaseResponse):
    """백테스트 결과 조회 응답"""
    backtest: Optional[StrategyBacktest] = None
    daily_returns: List[Dict[str, Any]] = []  # 일별 수익률 차트 데이터
    trade_history: List[TradeExecution] = []  # 거래 내역
    risk_metrics: Dict[str, float] = {}  # 리스크 지표

# ============================================================================
# REQ-AUTO-006: 거래 실행 내역 조회
# 의거: 화면 014 (거래 내역), REQ-AUTO-006
# ============================================================================

class AutoTradeGetExecutionsRequest(BaseRequest):
    """거래 실행 내역 조회 요청"""
    strategy_id: str = ""
    symbol: str = ""
    start_date: str = ""
    end_date: str = ""
    page: int = 1
    limit: int = 20

class AutoTradeGetExecutionsResponse(BaseResponse):
    """거래 실행 내역 조회 응답"""
    executions: List[TradeExecution] = []
    total_count: int = 0
    page: int = 1
    total_pages: int = 1

# ============================================================================
# REQ-AUTO-007: AI 전략 추천
# 의거: 화면 012 (전략 추천), REQ-AUTO-007
# ============================================================================

class AutoTradeGetRecommendationsRequest(BaseRequest):
    """AI 전략 추천 요청"""
    investment_goal: str = "GROWTH"  # GROWTH, INCOME, PRESERVATION
    risk_tolerance: str = "MODERATE"  # CONSERVATIVE, MODERATE, AGGRESSIVE
    investment_amount: float = 0.0
    time_horizon: str = "MEDIUM"  # SHORT, MEDIUM, LONG

class AutoTradeGetRecommendationsResponse(BaseResponse):
    """AI 전략 추천 응답"""
    recommendations: List[Dict[str, Any]] = []
    total_count: int = 0

# ============================================================================
# REQ-AUTO-008: 전략 성과 분석
# 의거: 화면 014 (성과 분석), REQ-AUTO-008
# ============================================================================

class AutoTradeGetPerformanceRequest(BaseRequest):
    """전략 성과 분석 요청"""
    strategy_id: str
    period: str = "1M"  # 1D, 1W, 1M, 3M, 1Y

class AutoTradeGetPerformanceResponse(BaseResponse):
    """전략 성과 분석 응답"""
    performance: Optional[StrategyPerformance] = None
    chart_data: List[Dict[str, Any]] = []  # 성과 차트 데이터
    comparison: Dict[str, Any] = {}  # 벤치마크 대비 성과

# ============================================================================
# REQ-AUTO-009: 전략 복사/공유
# 의거: 화면 012 (전략 공유), REQ-AUTO-009
# ============================================================================

class AutoTradeCopyStrategyRequest(BaseRequest):
    """전략 복사 요청"""
    source_strategy_id: str
    new_name: str = ""
    customize_parameters: Dict[str, Any] = {}

class AutoTradeCopyStrategyResponse(BaseResponse):
    """전략 복사 응답"""
    new_strategy: Optional[TradingStrategy] = None
    message: str = ""