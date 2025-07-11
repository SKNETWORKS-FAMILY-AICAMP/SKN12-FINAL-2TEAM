    """	
    1.	거시경제 데이터 (GDP, CPI) 가져옴
	2.	기술적 지표 (RSI, MACD 등) 가져옴
	3.	시장 데이터 (VIX 등) 가져옴
	4.	이 데이터로 관측 벡터(obs_vector) 구성
	5.	Kalman Filter 실행 → 시장 상태(state) + 공분산(cov) 계산
	6.	계산된 state, cov, elapsed를 기반으로 → 트레이딩 시그널, 전략, 포지션 크기, 레버리지, 손절/익절, 리스크 스코어, 안정성 등 추천안을 산출
	7.	최종적으로 recommendations 딕셔너리 형태로 반환

    
    알수 있는거 :
    시장의 모멘텀, 변동성, 유동성을 실시간 계산해서
    매수/매도 시그널,
    권장 포지션 크기,
    레버리지 배율,
    추천 전략 (추세추종, 역추세, 중립),
    손절/익절 가격,
    시장 리스크 스코어,
    시장 안정성 평가
    """
from __future__ import annotations

import time
from typing import Dict, Any
import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, Field

from AIChat.BaseFinanceTool import BaseFinanceTool
from AIChat.BasicTools.MacroEconomicTool import MacroEconomicTool
from AIChat.BasicTools.TechnicalAnalysisTool import TechnicalAnalysisTool, TechnicalAnalysisInput
from AIChat.BasicTools.MarketDataTool import MarketDataTool, MarketDataInput

__all__ = ["KalmanRegimeFilterTool"]

# ------------------- 🔷 Input / Output Schema -------------------- #

class KalmanRegimeFilterInput(BaseModel):
    tickers: list[str] = Field(..., description="분석할 ticker 리스트. 예: ['AAPL', 'MSFT']")
    start_date: str = Field(..., description="조회 시작일 (yyyy-mm-dd). 예: '2024-01-01'")
    end_date: str = Field(..., description="조회 종료일 (yyyy-mm-dd). 예: '2024-12-31'")

class KalmanRegimeFilterActionOutput(BaseModel):
    summary: str
    recommendations: Dict[str, Any]

# ------------------- 🔷 Kalman Filter Core -------------------- #

class KalmanRegimeFilterCore:
    def __init__(self) -> None:
        self.F: NDArray = np.array([[0.9, 0.1, 0.0], [0.0, 0.8, 0.2], [0.1, 0.0, 0.9]])
        self.H: NDArray = np.array([[1.0,0.0,0.0],[0.0,1.0,0.0],[0.0,0.0,1.0],[0.5,0.5,0.0],[0.0,0.7,0.3]])
        self.Q: NDArray = np.eye(3) * 0.01
        self.R: NDArray = np.eye(5) * 0.10
        self.x: NDArray = np.array([0.0, 1.0, 0.5])
        self.P: NDArray = np.eye(3)

    def _predict(self) -> None:
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q

    def _update(self, z: NDArray) -> None:
        y = z - self.H @ self.x
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)
        self.x = self.x + K @ y
        self.P = (np.eye(3) - K @ self.H) @ self.P

    def step(self, z: NDArray) -> None:
        self._predict()
        self._update(z)

# ------------------- 🔷 BaseFinanceTool Wrapper -------------------- #

class KalmanRegimeFilterTool(BaseFinanceTool):
    def __init__(self):
        super().__init__()
        self.filter = KalmanRegimeFilterCore()
        self.max_latency = 1.0

    def get_data(self, **kwargs) -> KalmanRegimeFilterActionOutput:
        t0 = time.time()
        input_data = KalmanRegimeFilterInput(**kwargs)

        # [1] 데이터 수집
        macro_tool = MacroEconomicTool()
        macro_output = macro_tool.get_data(['GDP', 'CPI'])
        gdp = macro_output.data.get('GDP', 0.0)
        cpi = macro_output.data.get('CPI', 0.0)

        ta_tool = TechnicalAnalysisTool()
        ta_input = TechnicalAnalysisInput(tickers=input_data.tickers)
        ta_output = ta_tool.get_data(ta_input, as_dict=True)
        ticker = input_data.tickers[0]
        ta_result = ta_output.results[ticker]
        rsi, macd = ta_result.rsi, ta_result.macd

        market_data_tool = MarketDataTool()
        market_input = MarketDataInput(tickers=input_data.tickers, start_date=input_data.start_date, end_date=input_data.end_date)
        market_data = market_data_tool.get_data(market_input)
        vix = market_data.get('vix', 0.0)

        # [2] 관측 벡터
        obs_vector = np.array([gdp, cpi, vix, 0.5 * (gdp + cpi), 0.7 * cpi + 0.3 * vix])

        # [3] 칼만 필터 스텝
        self.filter.step(obs_vector)
        elapsed = time.time() - t0

        if elapsed > self.max_latency:
            raise RuntimeError(f"Latency {elapsed:.3f}s > {self.max_latency}s")

        # [4] 결과
        state = self.filter.x.copy()
        cov = self.filter.P.copy()

        # ------------------- 🔥 Action Recommendation Engine -------------------- #

        recommendations = {}

        # 1. Trading Signal
        if state[0] > 0.5:
            signal = "Long"
        elif state[0] < -0.5:
            signal = "Short"
        else:
            signal = "Neutral"
        recommendations["trading_signal"] = signal

        # 2. Position Sizing
        base_size = 1000
        position_size = base_size * abs(state[0]) / (state[1] + 1e-6)
        recommendations["position_size"] = round(position_size, 2)

        # 3. Leverage
        target_volatility = 0.5
        leverage = target_volatility / (state[1] + 1e-6)
        recommendations["leverage"] = round(leverage, 2)

        # 4. Strategy Selection
        if state[0] > 0.5:
            strategy = "Trend Following"
        elif state[0] < -0.5:
            strategy = "Mean Reversion"
        else:
            strategy = "Market Neutral"
        recommendations["strategy"] = strategy

        # 5. Risk Management
        entry_price = 100  # 예시
        stop_multiplier = 2
        tp_multiplier = 3
        stop_loss = entry_price - state[1] * stop_multiplier
        take_profit = entry_price + state[1] * tp_multiplier
        recommendations["stop_loss"] = round(stop_loss, 2)
        recommendations["take_profit"] = round(take_profit, 2)

        # 6. Risk Score
        risk_score = np.trace(cov)
        recommendations["risk_score"] = round(risk_score, 3)

        # 7. Latency Monitoring
        recommendations["latency"] = round(elapsed, 3)

        # 8. Market Stability
        if state[1] < 0.2 and state[2] > 0.5:
            stability = "Stable"
        else:
            stability = "Unstable"
        recommendations["market_stability"] = stability

        summary = (
            f"📈 [Kalman Regime Filter Action Engine]\n"
            f"Signal: {signal}, Strategy: {strategy}, PosSize: {position_size:.2f}, Leverage: {leverage:.2f}\n"
            f"StopLoss: {stop_loss:.2f}, TakeProfit: {take_profit:.2f}, RiskScore: {risk_score:.3f}, Stability: {stability}\n"
            f"Elapsed: {elapsed:.3f} sec"
        )

        return KalmanRegimeFilterActionOutput(summary=summary, recommendations=recommendations)