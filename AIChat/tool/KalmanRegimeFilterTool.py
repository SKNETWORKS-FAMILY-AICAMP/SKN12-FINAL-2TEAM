from __future__ import annotations

import time
from typing import Dict, Any
import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, Field

from AIChat.BaseFinanceTool import BaseFinanceTool
from AIChat.BasicTools.MacroEconomicTool import MacroEconomicTool, MacroEconomicInput
from AIChat.BasicTools.TechnicalAnalysisTool import TechnicalAnalysisTool, TechnicalAnalysisInput
from AIChat.BasicTools.MarketDataTool import MarketDataTool, MarketDataInput

__all__ = ["KalmanRegimeFilterTool"]

# ------------------- 🔷 Input / Output Schema -------------------- #

class KalmanRegimeFilterInput(BaseModel):
    tickers: list[str] = Field(..., description="분석할 ticker 리스트. 예: ['AAPL', 'MSFT']")
    start_date: str = Field(..., description="조회 시작일 (yyyy-mm-dd). 예: '2024-01-01'")
    end_date: str = Field(..., description="조회 종료일 (yyyy-mm-dd). 예: '2024-12-31(최대한 최근 날짜)'")

class KalmanRegimeFilterActionOutput(BaseModel):
    summary: str
    recommendations: Dict[str, Any]

# ------------------- 🔷 Kalman Filter Core (7차원 입력에 맞춰 수정) -------------------- #

class KalmanRegimeFilterCore:
    def __init__(self) -> None:
        # x: 3차원 상태, z: 7차원 관측
        self.F: NDArray = np.array([[0.9, 0.1, 0.0], [0.0, 0.8, 0.2], [0.1, 0.0, 0.9]])
        # H: (7, 3)로 확장. 필요한 만큼 자유롭게 조정해도 됨
        self.H: NDArray = np.array([
            [1.0, 0.0, 0.0],   # gdp
            [0.0, 1.0, 0.0],   # cpi
            [0.0, 0.0, 1.0],   # vix
            [0.5, 0.5, 0.0],   # gdp+cpi
            [0.0, 0.7, 0.3],   # cpi, vix
            [0.2, 0.2, 0.6],   # rsi ("상태"와 rsi의 가상 연결)
            [0.4, 0.3, 0.3],   # macd (동일)
        ])
        self.Q: NDArray = np.eye(3) * 0.01
        self.R: NDArray = np.eye(7) * 0.10   # 관측 잡음행렬 (7x7)
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

    def find_value(data_list, series_id, default=0.0):
        for item in data_list:
            if isinstance(item, dict):
                if item.get('series_id') == series_id:
                    return item.get('latest_value', default)
            # 혹시 MacroEconomicSeries 객체일 경우
            elif hasattr(item, 'series_id'):
                if getattr(item, 'series_id', None) == series_id:
                    return getattr(item, 'latest_value', default)
        return default
    
    def get_data(self, **kwargs) -> KalmanRegimeFilterActionOutput:
        t0 = time.time()
        input_data = KalmanRegimeFilterInput(**kwargs)

        # [1] 데이터 수집
        macro_tool = MacroEconomicTool()
        macro_output = macro_tool.get_data(series_ids=["GDP", "CPIAUCSL"])
        gdp = KalmanRegimeFilterTool.find_value(macro_output.data, 'GDP', 0.0)
        cpi = KalmanRegimeFilterTool.find_value(macro_output.data, 'CPIAUCSL', 0.0)

        ta_tool = TechnicalAnalysisTool()
        ta_output = ta_tool.get_data(tickers=input_data.tickers)  # 리스트 결과
        ta_result = ta_output.results[0]  # 첫 번째 종목만 사용
        rsi, macd = ta_result.rsi, ta_result.macd

        market_data_tool = MarketDataTool()
        market_input = MarketDataInput(tickers=input_data.tickers, start_date=input_data.start_date, end_date=input_data.end_date)
        market_data = market_data_tool.get_data(market_input)
        vix = market_data.get('vix', 0.0)
        print(f"Data collected: GDP={gdp}, CPI={cpi}, VIX={vix}, RSI={rsi}, MACD={macd}")
        # [2] 관측 벡터 (rsi, macd 추가)
        obs_vector = np.array([
            gdp, cpi, vix,
            0.5 * (gdp + cpi),
            0.7 * cpi + 0.3 * vix,
            rsi,  # 추가
            macd  # 추가
        ])

        # [3] 칼만 필터 스텝
        self.filter.step(obs_vector)
        elapsed = time.time() - t0
        print(f"KalmanRegimeFilterTool: Elapsed time: {elapsed:.3f} seconds")
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
        print(f"Position Size: {position_size:.2f}")
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
