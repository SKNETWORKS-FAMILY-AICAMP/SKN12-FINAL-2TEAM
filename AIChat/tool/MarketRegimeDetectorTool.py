"""
market_regime.py
================
MarketRegimeDetector  ➡  **BaseFinanceTool** 상속 + `get_data()` 통일 인터페이스 버전

● 입력
    macro_data : dict  ─ {'gdp_growth': float, 'cpi': float}
    tech_data  : dict  ─ {'rsi': float, 'vix': float, 'macd': float}
    prev_state : str | None  ─ 이전 시점 Regime (‘Bear’/‘Sideways’/‘Bull’)

● 출력 (dict)
    {
        'regime'    : str,              # 가장 확률 높은 상태
        'posteriors': {'Bear': p, ...}, # 상태별 Posterior 확률
        'elapsed'   : float             # 처리 시간(초)
    }
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional

import numpy as np
from scipy.stats import multivariate_normal

from BaseFinanceTool import BaseFinanceTool  # 같은 프로젝트 내 공통 베이스

__all__ = ["MarketRegimeDetector"]


class MarketRegimeDetector(BaseFinanceTool):
    """베이지안·HMM 기반 시장 Regime 탐지기 (Bull/Bear/Sideways)"""

    # ------------------------------------------------------------------ #
    # 1. 초기화
    # ------------------------------------------------------------------ #
    def __init__(self) -> None:
        super().__init__()  # API-Key 필요 없지만 공통 인터페이스 유지

        # 상태 정의
        self.states: List[str] = ["Bear", "Sideways", "Bull"]
        self.state_idx = {s: i for i, s in enumerate(self.states)}

        # Markov 전이 확률
        self.transition_matrix = np.array(
            [[0.85, 0.10, 0.05], [0.25, 0.50, 0.25], [0.05, 0.10, 0.85]]
        )

        # 상태별 관측 분포(다변량 정규) 모수
        self.observation_params: Dict[str, Dict[str, np.ndarray]] = {
            "Bear": {
                "mean": np.array([-0.5, 4.0, 35, 30, -0.5]),
                "cov": np.diag([0.25, 1.0, 100, 25, 0.1]),
            },
            "Sideways": {
                "mean": np.array([1.5, 2.5, 50, 20, 0.0]),
                "cov": np.diag([0.5, 0.5, 64, 16, 0.05]),
            },
            "Bull": {
                "mean": np.array([3.0, 2.0, 65, 15, 0.5]),
                "cov": np.diag([0.75, 0.25, 81, 9, 0.1]),
            },
        }

    # ------------------------------------------------------------------ #
    # 2. 내부 유틸
    # ------------------------------------------------------------------ #
    def _likelihood(self, obs_vec: np.ndarray, state: str) -> float:
        """다변량 정규 pdf = P(X_t | State_t)"""
        param = self.observation_params[state]
        return multivariate_normal.pdf(obs_vec, mean=param["mean"], cov=param["cov"])

    # ------------------------------------------------------------------ #
    # 3. 공용 API (요구사항: get_data)
    # ------------------------------------------------------------------ #
    def get_data(
        self,
        macro_data: Dict[str, float],
        tech_data: Dict[str, float],
        prev_state: Optional[str] = None,
        max_latency: float = 1.0,
    ) -> Dict[str, object]:
        """
        단일 시점 Regime 예측.

        Returns
        -------
        dict
            - regime     : posterior 최대 상태
            - posteriors : 상태별 확률 dict
            - elapsed    : 처리 시간(초)
        """
        t0 = time.time()

        # 관측 벡터
        obs = np.array(
            [
                macro_data["gdp_growth"],
                macro_data["cpi"],
                tech_data["rsi"],
                tech_data["vix"],
                tech_data["macd"],
            ]
        )

        # Prior
        priors = (
            np.full(3, 1 / 3)
            if prev_state is None
            else self.transition_matrix[self.state_idx[prev_state]]
        )

        # Posterior
        likes = np.array([self._likelihood(obs, s) for s in self.states])
        post = likes * priors
        post = post / post.sum()
        posteriors = {s: float(post[i]) for i, s in enumerate(self.states)}

        regime = max(posteriors, key=posteriors.get)
        elapsed = time.time() - t0
        if elapsed > max_latency:
            raise RuntimeError(f"실시간 제약 초과: {elapsed:.3f}s")

        return {"regime": regime, "posteriors": posteriors, "elapsed": elapsed}

    # ------------------------------------------------------------------ #
    # 4. 선택적: Viterbi 경로 추정 & 전이 행렬 재학습
    # ------------------------------------------------------------------ #
    def viterbi_path(
        self,
        macro_seq: List[Dict[str, float]],
        tech_seq: List[Dict[str, float]],
    ) -> List[str]:
        T, S = len(macro_seq), len(self.states)
        log_delta = np.zeros((T, S))
        psi = np.zeros((T, S), dtype=int)

        # 초기
        obs0 = np.array(
            [
                macro_seq[0]["gdp_growth"],
                macro_seq[0]["cpi"],
                tech_seq[0]["rsi"],
                tech_seq[0]["vix"],
                tech_seq[0]["macd"],
            ]
        )
        for s in range(S):
            log_delta[0, s] = np.log(1 / S) + np.log(
                self._likelihood(obs0, self.states[s])
            )

        # 재귀
        for t in range(1, T):
            obs_t = np.array(
                [
                    macro_seq[t]["gdp_growth"],
                    macro_seq[t]["cpi"],
                    tech_seq[t]["rsi"],
                    tech_seq[t]["vix"],
                    tech_seq[t]["macd"],
                ]
            )
            like_vec = np.array([self._likelihood(obs_t, st) for st in self.states])
            for s in range(S):
                trans = log_delta[t - 1] + np.log(self.transition_matrix[:, s])
                psi[t, s] = np.argmax(trans)
                log_delta[t, s] = np.max(trans) + np.log(like_vec[s])

        # 역추적
        idx_seq = np.zeros(T, dtype=int)
        idx_seq[-1] = np.argmax(log_delta[-1])
        for t in range(T - 2, -1, -1):
            idx_seq[t] = psi[t + 1, idx_seq[t + 1]]

        return [self.states[i] for i in idx_seq]

    def fit_transition(self, regime_history: List[str]) -> None:
        S = len(self.states)
        counts = np.zeros((S, S))
        for p, c in zip(regime_history[:-1], regime_history[1:]):
            counts[self.state_idx[p], self.state_idx[c]] += 1
        row_sum = counts.sum(axis=1, keepdims=True)
        with np.errstate(invalid="ignore"):
            self.transition_matrix = np.where(
                row_sum > 0, counts / row_sum, self.transition_matrix
            )


# ---------------------------------------------------------------------- #
# 간단 데모: python market_regime.py 로 실행
# ---------------------------------------------------------------------- #
if __name__ == "__main__":
    # 데모용 스텁 데이터
    macro_seq = [
        {"gdp_growth": -1.0, "cpi": 2.0},
        {"gdp_growth": 0.5, "cpi": 2.5},
        {"gdp_growth": 2.5, "cpi": 3.5},
    ]
    tech_seq = [
        {"rsi": 30, "vix": 25, "macd": -0.2},
        {"rsi": 50, "vix": 20, "macd": 0.1},
        {"rsi": 65, "vix": 15, "macd": 0.5},
    ]

    det = MarketRegimeDetector()
    # Viterbi 경로
    print("Viterbi:", det.viterbi_path(macro_seq, tech_seq))
    # 실시간 예측
    for m, t in zip(macro_seq, tech_seq):
        print(det.get_data(m, t))
