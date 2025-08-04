from __future__ import annotations

import time
from datetime import datetime
from typing import Dict, Any, List
import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, Field

# --- 외부 툴 의존부 ---
from service.llm.AIChat.BaseFinanceTool import BaseFinanceTool
from service.llm.AIChat.BasicTools.MacroEconomicTool import MacroEconomicTool
from service.llm.AIChat.BasicTools.TechnicalAnalysisTool import TechnicalAnalysisTool
from service.llm.AIChat.BasicTools.MarketDataTool import MarketDataTool, MarketDataInput

__all__ = ["KalmanRegimeFilterTool"]

# ───────────────────────── Input / Output ───────────────────────── #

class KalmanRegimeFilterInput(BaseModel):
    tickers: List[str] = Field(..., description="분석할 종목 리스트")
    start_date: str    = Field(..., description="데이터 시작일(YYYY-MM-DD)")
    end_date: str      = Field(..., description="데이터 종료일(YYYY-MM-DD)")

    # ▶️ 실전 운용 파라미터
    account_value: float = Field(... ,description="계좌 가치")
    exchange_rate: str = Field("KWR", description="화폐 단위(예시: KWR, USD)" )
    risk_pct: float      = Field(0.02,      description="한 트레이드당 위험 비율(0~1)")
    max_leverage: float  = Field(10.0,      description="허용 최대 레버리지")


class KalmanRegimeFilterActionOutput(BaseModel):
    summary: str
    recommendations: Dict[str, Any]
    start_time: str
    end_time: str

# ─────────────────────────── Kalman Filter Core ───────────────────────── #

class KalmanRegimeFilterCore:
    def __init__(self) -> None:
        # 상태 벡터: [trend, momentum, volatility]
        self.x = np.array([0.0, 0.0, 0.5])
        
        # 공분산 행렬
        self.P = np.eye(3) * 0.1
        
        # 시스템 노이즈
        self.Q = np.eye(3) * 0.01
        
        # 측정 노이즈
        self.R = np.eye(7) * 0.1  # 7개 피처
        
        # 상태 전이 행렬
        self.F = np.eye(3)
        self.F[0, 1] = 0.1  # trend ← momentum
        
        # 측정 행렬 (7개 피처 → 3개 상태)
        self.H = np.array([
            [1, 0, 0, 0.5, 0, 0, 0],  # trend
            [0, 0, 0, 0, 0, 1, 0],    # momentum
            [0, 0, 1, 0, 0.3, 0, 0]   # volatility
        ])

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

# ─────────────────────────── Tool Wrapper ───────────────────────── #

class KalmanRegimeFilterTool(BaseFinanceTool):
    """
    매 호출 시:
      1) 거시·기술·가격 데이터 수집 (raw 값)
      2) 피처 조합 후 정규화
      3) 칼만 필터 업데이트
      4) 트레이딩 신호·리스크·경고 생성
    """
    def __init__(self, ai_chat_service):
        from service.llm.AIChat_service import AIChatService
        if not isinstance(ai_chat_service, AIChatService):
            raise TypeError("Expected AIChatService instance")
        self.ai_chat_service = ai_chat_service
        self.filter = KalmanRegimeFilterCore()
        self.max_latency = 5.0  # seconds

    # ---------- 정규화 유틸리티 함수들 ----------
    # ❌ 중복 정규화 메서드 제거 - FeaturePipelineTool에서 처리
    # _log1p_normalize, _zscore_normalize 메서드 삭제

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
        """
        칼만 필터 기반 시장 체제 감지 + 자동 트레이딩 신호 생성
        
        Returns:
            KalmanRegimeFilterActionOutput: 트레이딩 추천사항
        """
        t_start = time.time()
        
        # 1️⃣ kwargs → input class 파싱
        inp = KalmanRegimeFilterInput(**kwargs)
        
        # 🆕 칼만 필터 전용 Composite 공식 정의
        kalman_composite_formulas = {
            # 거시경제 + 변동성 복합 지표 (칼만 필터의 trend 추정용)
            "kalman_macro_vol": lambda feats: (
                0.4 * feats.get("GDP", 0.0) + 
                0.3 * feats.get("CPIAUCSL", 0.0) + 
                0.3 * feats.get("VIX", 0.0)
            ),
            # 기술적 + 거시경제 복합 지표 (momentum 추정용)
            "kalman_tech_macro": lambda feats: (
                0.5 * feats.get("RSI", 0.0) + 
                0.3 * feats.get("MACD", 0.0) + 
                0.2 * feats.get("CPIAUCSL", 0.0)
            ),
            # 변동성 + 환율 복합 지표 (volatility 추정용)
            "kalman_vol_fx": lambda feats: (
                0.7 * feats.get("VIX", 0.0) + 
                0.3 * feats.get("DEXKOUS", 0.0)
            )
        }

        # 2️⃣ 완전한 피처 파이프라인 활용 (칼만 전용 composite 공식 사용)
        from service.llm.AIChat.tool.FeaturePipelineTool import FeaturePipelineTool
        
        pipeline_result = FeaturePipelineTool(self.ai_chat_service).transform(
            tickers=inp.tickers,
            start_date=inp.start_date,
            end_date=inp.end_date,
            feature_set=["GDP", "CPIAUCSL", "DEXKOUS", "RSI", "MACD", "VIX", "PRICE"],
            normalize=True,  # ✅ 정규화 활성화
            normalize_targets=["GDP", "CPIAUCSL", "VIX", "RSI", "MACD"],  # ✅ Composite 자동 추가됨
            generate_composites=True,  # ✅ 복합 피처 생성
            composite_formula_map=kalman_composite_formulas,  # 🆕 칼만 전용 공식 사용
            return_raw=True,  # 🆕 Raw + Normalized 동시 반환
            debug=False
        )

        # 3️⃣ Raw 값과 Normalized 값 분리
        raw_features = pipeline_result["raw"]      # 계산용 (가격, 환율)
        norm_features = pipeline_result["normalized"]  # 신호용 (모델 입력)
        
        # Raw 값으로 계산용 데이터 추출
        exchange_rate = raw_features.get("DEXKOUS", 0.00072)
        entry_price = raw_features.get("PRICE", 0.0)

        if inp.exchange_rate.upper() == "KWR":
            inp.account_value *= exchange_rate

        if entry_price == 0.0:
            raise RuntimeError(f"{inp.tickers[0]}의 가격 데이터를 찾을 수 없습니다.")

        # 4️⃣ 정규화된 피처들로 관측값 벡터 구성 (칼만 전용 composite 사용)
        z = np.array([
            norm_features.get("GDP"),                    # ✅ log1p 정규화됨
            norm_features.get("CPIAUCSL"),               # ✅ z-score 정규화됨  
            norm_features.get("VIX"),                    # ✅ z-score 정규화됨
            norm_features.get("kalman_macro_vol"),       # 🆕 칼만 전용 composite (자동 정규화됨)
            norm_features.get("kalman_tech_macro"),      # 🆕 칼만 전용 composite (자동 정규화됨)
            norm_features.get("kalman_vol_fx"),          # 🆕 칼만 전용 composite (자동 정규화됨)
            norm_features.get("RSI"),                    # ✅ z-score 정규화됨
            norm_features.get("MACD")                    # ✅ z-score 정규화됨
        ])

        # 5️⃣ 칼만 필터
        self.filter.step(z)
        state, cov = self.filter.x.copy(), self.filter.P.copy()
        raw_vol = float(state[2])

        # 6️⃣ 액션 엔진
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
        pos_size = risk_dollar / (vol * entry_price)
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
        atr = vol * entry_price
        stop_loss   = entry_price - atr * 1.5
        take_profit = entry_price + atr * 3.0
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

        # 7️⃣ 결과 반환
        return KalmanRegimeFilterActionOutput(
            summary=f"칼만 필터 분석 완료 - {signal} 신호, 변동성: {vol:.3f}",
            recommendations=rec,
            start_time=inp.start_date,
            end_time=inp.end_date
        )
