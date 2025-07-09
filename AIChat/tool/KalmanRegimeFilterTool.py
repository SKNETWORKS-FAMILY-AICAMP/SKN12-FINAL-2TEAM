"""
kalman_filter.py
================
KalmanRegimeFilter   ➡   **BaseFinanceTool** 상속 + `get_data()` 통일 인터페이스

● 상태 벡터
      x_t = [market_momentum, volatility_regime, liquidity_state]ᵀ

● 관측 벡터
      z_t = [momentum, volatility, liquidity,
              0.5·(mom + vol), 0.7·vol + 0.3·liq + noise]

● 알고리즘 단계
      1) predict : x̂ₜ|ₜ₋₁ = F·x̂ₜ₋₁|ₜ₋₁
                   Pₜ|ₜ₋₁ = F·Pₜ₋₁|ₜ₋₁·Fᵀ + Q
      2) update  : Kₜ      = Pₜ|ₜ₋₁·Hᵀ·(H·Pₜ|ₜ₋₁·Hᵀ + R)⁻¹
                   x̂ₜ|ₜ   = x̂ₜ|ₜ₋₁ + Kₜ·(zₜ − H·x̂ₜ|ₜ₋₁)
                   Pₜ|ₜ   = (I − Kₜ·H)·Pₜ|ₜ₋₁

● 입력
      obs_vector : np.ndarray(shape=(5,))  → 관측 zₜ

● 출력 (dict)
      {
          'state'    : np.ndarray(shape=(3,))   # x̂ₜ|ₜ
          'cov'      : np.ndarray(shape=(3,3))  # Pₜ|ₜ
          'elapsed'  : float                    # seconds
      }
"""

from __future__ import annotations

import time
from typing import Dict

import numpy as np
from numpy.typing import NDArray

from BaseFinanceTool import BaseFinanceTool

__all__ = ["KalmanRegimeFilter"]


class KalmanRegimeFilter(BaseFinanceTool):
    """시장 모멘텀·변동성·유동성 상태를 추적하는 칼만 필터"""

    def __init__(self) -> None:
        super().__init__()  # (API-Key 사용 안 함—인터페이스 통일용)

        # ---- 모델 행렬 정의 ------------------------------------ #
        #   x_t = F·x_{t-1} + w_t
        self.F: NDArray = np.array(
            [[0.9, 0.1, 0.0],
             [0.0, 0.8, 0.2],
             [0.1, 0.0, 0.9]]
        )

        #   z_t = H·x_t + v_t
        self.H: NDArray = np.array(
            [[1.0, 0.0, 0.0],
             [0.0, 1.0, 0.0],
             [0.0, 0.0, 1.0],
             [0.5, 0.5, 0.0],
             [0.0, 0.7, 0.3]]
        )

        # 공분산 매개변수
        self.Q: NDArray = np.eye(3) * 0.01   # 프로세스 노이즈
        self.R: NDArray = np.eye(5) * 0.10   # 관측 노이즈

        # 초기 추정
        self.x: NDArray = np.array([0.0, 1.0, 0.5])
        self.P: NDArray = np.eye(3)

    # ------------------- 칼만 필터 단계 ------------------------- #
    def _predict(self) -> None:
        """a priori 예측"""
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q

    def _update(self, z: NDArray) -> None:
        """관측 반영(a posteriori)"""
        y = z - self.H @ self.x                       # 잔차
        S = self.H @ self.P @ self.H.T + self.R       # 잔차 공분산
        K = self.P @ self.H.T @ np.linalg.inv(S)      # 칼만 이득
        self.x = self.x + K @ y
        self.P = (np.eye(3) - K @ self.H) @ self.P

    def step(self, z: NDArray) -> None:
        """1-스텝 예측+업데이트 (내부 상태 갱신)"""
        self._predict()
        self._update(z)

    # ------------------- 공개 API: get_data -------------------- #
    def get_data(self, obs_vector: NDArray, *, max_latency: float = 1.0) -> Dict[str, NDArray | float]:
        """
        Parameters
        ----------
        obs_vector : np.ndarray shape=(5,)
            [momentum, volatility, liquidity,
             0.5·(mom+vol), 0.7·vol + 0.3·liq + noise]

        Returns
        -------
        dict
            'state'   : 필터링된 상태 추정 x̂ₜ|ₜ
            'cov'     : 추정 공분산 Pₜ|ₜ
            'elapsed' : 소요 시간(초)
        """
        t0 = time.time()
        self.step(obs_vector)
        elapsed = time.time() - t0
        if elapsed > max_latency:
            raise RuntimeError(f"Latency {elapsed:.3f}s > {max_latency}s")

        return {"state": self.x.copy(), "cov": self.P.copy(), "elapsed": elapsed}


# ---------------------------------------------------------------------- #
# 간단 데모 (python kalman_filter.py 로 실행)                            #
# ---------------------------------------------------------------------- #
if __name__ == "__main__":
    kf = KalmanRegimeFilter()

    # 임의 관측 6개 스텁
    obs_list = [
        np.array([-1.0, 22, 0.3, 10.5, 16.0]),
        np.array([ 0.2, 25, 0.4, 12.6, 18.2]),
        np.array([ 2.5, 18, 0.5, 10.2, 14.3]),
    ]

    for i, z in enumerate(obs_list):
        out = kf.get_data(z)
        print(f"t={i}  state={out['state'].round(3)}  elapsed={out['elapsed']*1e3:.1f} ms")
