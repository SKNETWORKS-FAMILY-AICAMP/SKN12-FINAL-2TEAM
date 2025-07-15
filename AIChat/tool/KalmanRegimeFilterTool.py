from __future__ import annotations

import time
from typing import Dict, Any, List
import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, Field

# --- 외부 툴 의존부 ---
from AIChat.BaseFinanceTool import BaseFinanceTool
from AIChat.BasicTools.MacroEconomicTool import MacroEconomicTool
from AIChat.BasicTools.TechnicalAnalysisTool import TechnicalAnalysisTool
from AIChat.BasicTools.MarketDataTool import MarketDataTool, MarketDataInput

__all__ = ["KalmanRegimeFilterTool"]

# ───────────────────────── Input / Output ───────────────────────── #

class KalmanRegimeFilterInput(BaseModel):
    tickers: List[str] = Field(..., description="분석할 종목 리스트")
    start_date: str    = Field(..., description="데이터 시작일(YYYY-MM-DD)")
    end_date: str      = Field(..., description="데이터 종료일(YYYY-MM-DD)")

    # ▶️ 실전 운용 파라미터
    account_value: float = Field(100_000.0, description="계좌 가치(USD)")
    risk_pct: float      = Field(0.02,      description="한 트레이드당 위험 비율(0~1)")
    entry_price: float   = Field(100.0,     description="진입 가격(USD)")
    max_leverage: float  = Field(10.0,      description="허용 최대 레버리지")


class KalmanRegimeFilterActionOutput(BaseModel):
    summary: str
    recommendations: Dict[str, Any]
    start_time: str
    end_time: str

# ─────────────────────── Kalman Filter Core ─────────────────────── #

class KalmanRegimeFilterCore:
    """
    상태벡터 x = [trend, macro drift, volatility]
    F, H, Q, R는 예시 상수이며 EM 학습으로 교체 가능
    """
    def __init__(self) -> None:
        self.F: NDArray = np.array([[0.9, 0.1, 0.0],
                                    [0.0, 0.8, 0.2],
                                    [0.1, 0.0, 0.9]])
        self.H: NDArray = np.array([
            [1,   0,   0],   # GDP
            [0,   1,   0],   # CPI
            [0,   0,   1],   # VIX
            [0.5, 0.5, 0],   # GDP+CPI
            [0,  0.7, 0.3],  # CPI&VIX
            [0.2,0.2, 0.6],  # RSI
            [0.4,0.3, 0.3]   # MACD
        ])
        self.Q: NDArray = np.eye(3) * 0.01
        self.R: NDArray = np.eye(7) * 0.10
        self.x: NDArray = np.array([0.0, 1.0, 0.5])
        self.P: NDArray = np.eye(3)

    def _predict(self) -> None:
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q

    def _update(self, z: NDArray) -> None:
        y = z - self.H @ self.x
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)
        self.x += K @ y
        self.P = (np.eye(3) - K @ self.H) @ self.P

    def step(self, z: NDArray) -> None:
        self._predict()
        self._update(z)

# ─────────────────────────── Tool Wrapper ───────────────────────── #

class KalmanRegimeFilterTool(BaseFinanceTool):
    """
    매 호출 시:
      1) 거시·기술·가격 데이터 수집
      2) 칼만 필터 업데이트
      3) 트레이딩 신호·리스크·경고 생성
    """
    def __init__(self) -> None:
        super().__init__()
        self.filter = KalmanRegimeFilterCore()
        self.max_latency = 5.0  # seconds

    # ---------- 유틸 ----------
    @staticmethod
    def _find_value(data_list, series_id, default=0.0):
        for item in data_list:
            if isinstance(item, dict) and item.get('series_id') == series_id:
                return item.get('latest_value', default)
            if hasattr(item, 'series_id') and getattr(item, 'series_id') == series_id:
                return getattr(item, 'latest_value', default)
        return default

    # ---------- main ----------
    def get_data(self, **kwargs) -> KalmanRegimeFilterActionOutput:
        t_start = time.time()
        start_ts = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t_start))
        inp = KalmanRegimeFilterInput(**kwargs)

        # 1️⃣ 데이터 수집
        macro = MacroEconomicTool().get_data(series_ids=["GDP", "CPIAUCSL"])
        gdp = self._find_value(macro.data, 'GDP')
        cpi = self._find_value(macro.data, 'CPIAUCSL')

        ta_res = TechnicalAnalysisTool().get_data(tickers=inp.tickers).results[0]
        rsi, macd = ta_res.rsi, ta_res.macd

        md_inp = MarketDataInput(tickers=inp.tickers,
                                 start_date=inp.start_date,
                                 end_date=inp.end_date)
        vix = MarketDataTool().get_data(**md_inp.dict()).vix

        z = np.array([gdp, cpi, vix,
                      0.5*(gdp+cpi),
                      0.7*cpi + 0.3*vix,
                      rsi, macd])

        # 2️⃣ 칼만 필터
        self.filter.step(z)
        state, cov = self.filter.x.copy(), self.filter.P.copy()
        raw_vol = float(state[2])

        # 3️⃣ 액션 엔진
        rec: Dict[str, Any] = {}
        warnings: List[str] = []

        # ── 변동성 클리핑
        vol = float(np.clip(raw_vol, 0.05, 2.0))
        if vol != raw_vol:
            warnings.append(f"Volatility clipped: {raw_vol:.4f}→{vol:.2f}")

        # ── 신호
        trend = state[0]
        if trend > 0.5:
            signal = "Long"
        elif trend < -0.5:
            signal = "Short"
        else:
            signal = "Neutral"
        rec["trading_signal"] = signal

        # ── 포지션 크기
        risk_dollar = inp.account_value * inp.risk_pct
        pos_size = risk_dollar / (vol * inp.entry_price)
        rec["position_size"] = round(pos_size, 4)

        # ── 레버리지
        target_vol = 0.5
        leverage = min(target_vol / vol, inp.max_leverage)
        if leverage >= inp.max_leverage:
            warnings.append(f"Leverage capped at {inp.max_leverage}×")
        rec["leverage"] = round(leverage, 2)

        # ── 전략
        rec["strategy"] = ("Trend Following" if signal == "Long"
                           else "Mean Reversion" if signal == "Short"
                           else "Market Neutral")

        # ── SL / TP (ATR 기반)
        atr = vol * inp.entry_price
        stop_loss   = inp.entry_price - atr * 1.5
        take_profit = inp.entry_price + atr * 3.0
        rec["stop_loss"]   = round(stop_loss, 2)
        rec["take_profit"] = round(take_profit, 2)

        # ── 리스크 지표
        rec["risk_score"] = round(float(np.trace(cov)), 3)
        rec["market_stability"] = "Stable" if vol < 0.3 else "Unstable"

        # ── 지연
        latency = time.time() - t_start
        if latency > self.max_latency:
            warnings.append(f"Latency {latency:.3f}s > limit {self.max_latency}s")
        rec["latency"] = round(latency, 3)

        if warnings:
            rec["warnings"] = warnings

        # 4️⃣ 요약 문자열
        lines = [
            "📈 [Kalman Regime Filter Action Engine]",
            f"Signal:{signal}  Strategy:{rec['strategy']}",
            f"PosSize:{pos_size:.4f}  Lev:{leverage:.2f}",
            f"SL:{stop_loss:.2f}  TP:{take_profit:.2f}",
            f"Risk:{rec['risk_score']:.3f}  Market:{rec['market_stability']}",
            f"Elapsed:{latency:.3f}s"
        ]
        if warnings:
            lines.append("⚠️ " + " | ".join(warnings))
        summary = "\n".join(lines)

        end_ts = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

        return KalmanRegimeFilterActionOutput(
            summary=summary,
            recommendations=rec,
            start_time=start_ts,
            end_time=end_ts
        )
