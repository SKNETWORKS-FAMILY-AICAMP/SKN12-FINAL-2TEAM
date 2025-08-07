"""
dynamic_risk_parity.py
======================
DynamicRiskParityOptimizer  ➡  BaseFinanceTool 상속 + `get_data()` 표준화 버전

● 핵심 아이디어
    - EWMA 공분산(λ=0.94 기본)으로 변동성·상관관계 갱신
    - 위험 기여도 균등(Risk Parity) 포트폴리오를
      SLSQP(min Σ_i (RC_i − 1/N)²) 로 최적화
    - 리밸런싱 제한·하한비중(0.01)·거래비용 고려

● 입력
    returns            : np.ndarray(shape=(T, N))   # 최근 T기간 N자산 수익률
    rebalance_threshold: float = 0.05               # 기존 대비 |Δw| > 5%면 리밸런싱
    transaction_cost   : float = 0.001              # 거래비용 비율(옵션)
    lambda_decay       : float = 0.94               # EWMA decay

● 출력(dict)
    {
        'weights'      : np.ndarray(N,),   # 신규 RP 비중(합=1)
        'risk_contrib' : np.ndarray(N,),   # 자산별 위험 기여도
        'cov_matrix'   : np.ndarray(N,N),  # 업데이트된 공분산
        'rebalanced'   : bool,             # 리밸런싱 실행 여부
        'elapsed'      : float             # 처리 시간(초)
    }
"""

from __future__ import annotations

import time
from typing import Dict

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import minimize

from BaseFinanceTool import BaseFinanceTool

__all__ = ["DynamicRiskParityOptimizer"]


class DynamicRiskParityOptimizer(BaseFinanceTool):
    """EWMA 공분산 + 위험 기여도 균등 포트폴리오"""

    # ---------------------------- 초기화 --------------------------- #
    def __init__(self) -> None:
        super().__init__()  # API-Key 필요 없음
        self.prev_weights: NDArray | None = None  # 직전 비중(없으면 1/N)

    # ---------------------- 공분산 업데이트 ------------------------ #
    @staticmethod
    def _ewma_cov(returns: NDArray, lam: float) -> NDArray:
        """EWMA 공분산 행렬"""
        cov = np.cov(returns, rowvar=False)  # 초기값: 표본 공분산
        for r in returns[::-1]:  # 최근 → 과거
            cov = lam * cov + (1 - lam) * np.outer(r, r)
        return cov

    # ----------------- 위험 기여도 & 목적함수 ---------------------- #
    @staticmethod
    def _risk_contrib(weights: NDArray, cov: NDArray) -> NDArray:
        port_vol = np.sqrt(weights @ cov @ weights)
        mrc = cov @ weights  # marginal
        return weights * mrc / (port_vol + 1e-12)

    def _objective(self, w: NDArray, cov: NDArray) -> float:
        rc = self._risk_contrib(w, cov)
        return ((rc - rc.mean()) ** 2).sum()

    # --------------------------- get_data ------------------------- #
    def get_data(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str,
        *,
        rebalance_threshold: float = 0.05,
        transaction_cost: float = 0.001,
        lambda_decay: float = 0.94,
        max_latency: float = 1.0,
    ) -> Dict:
        """
        Parameters
        ----------
        tickers : List[str]
            분석할 종목 리스트
        start_date : str
            데이터 시작일(YYYY-MM-DD)
        end_date : str
            데이터 종료일(YYYY-MM-DD)
        """
        t0 = time.time()

        # FeaturePipelineTool을 사용하여 가격 데이터 추출
        from service.llm.AIChat.tool.FeaturePipelineTool import FeaturePipelineTool
        features = FeaturePipelineTool(self.ai_chat_service).transform(
            tickers=tickers,
            start_date=start_date,
            end_date=end_date,
            feature_set=["PRICE_HISTORY"]
        )

        price_data = features.get("PRICE_HISTORY")
        if not price_data or not isinstance(price_data, pd.DataFrame) or price_data.empty:
            raise RuntimeError("가격 데이터를 가져올 수 없습니다.")

        # 수익률 계산
        returns = price_data.pct_change().dropna().values
        if returns.size == 0:
            raise RuntimeError("수익률 데이터를 계산할 수 없습니다.")

        N = returns.shape[1] if returns.ndim > 1 else 1
        if N == 1: # 단일 종목인 경우 2차원 배열로 변환
            returns = returns.reshape(-1, 1)

        cov = self._ewma_cov(returns, lambda_decay)

        # 초기 weights
        if self.prev_weights is None or self.prev_weights.shape[0] != N:
            self.prev_weights = np.ones(N) / N

        # ----- 최적화 (SLSQP) ------------------------------------ #
        cons = ({"type": "eq", "fun": lambda w: w.sum() - 1.0},)
        bounds = [(0.01, 1.0)] * N
        res = minimize(
            self._objective,
            self.prev_weights,
            args=(cov,),
            bounds=bounds,
            constraints=cons,
            method="SLSQP",
            options={"disp": False},
        )

        w_opt = res.x
        # 거래비용/리밸런싱 제한
        delta = w_opt - self.prev_weights
        delta_clip = np.clip(delta, -0.1, 0.1)
        w_new = self.prev_weights + delta_clip
        w_new = np.maximum(w_new, 0.01)
        w_new /= w_new.sum()

        # 리밸런싱 여부
        rebalanced = np.any(np.abs(delta) > rebalance_threshold)
        # 거래비용 반영 후 가중치 조정(간단 예시)
        if rebalanced:
            w_new *= (1 - transaction_cost)

        # 상태 저장
        self.prev_weights = w_new

        # 위험 기여도
        rc = self._risk_contrib(w_new, cov)

        elapsed = time.time() - t0
        if elapsed > max_latency:
            raise RuntimeError(f"Latency {elapsed:.3f}s > {max_latency}s")

        return {
            "weights": w_new,
            "risk_contrib": rc,
            "cov_matrix": cov,
            "rebalanced": bool(rebalanced),
            "elapsed": elapsed,
        }


# --------------------------------------------------------------------- #
# 간단 데모
# --------------------------------------------------------------------- #
if __name__ == "__main__":
    # 100일×4자산 더미 수익률
    demo_ret = np.random.randn(100, 4) * 0.012

    drp = DynamicRiskParityOptimizer()
    out = drp.get_data(demo_ret)
    print(out)
