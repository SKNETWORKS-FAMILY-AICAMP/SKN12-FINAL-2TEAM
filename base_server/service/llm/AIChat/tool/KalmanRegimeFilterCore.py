from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

class KalmanRegimeFilterCore:
    """
    5차원 실전용 칼만 필터
    상태 벡터: [trend, momentum, volatility, macro_signal, tech_signal]
    """
    def __init__(self) -> None:
        # 상태 벡터: [trend, momentum, volatility, macro_signal, tech_signal]
        self.x = np.array([0.0, 0.0, 0.2, 0.0, 0.0])  # volatility만 0.2로 초기화
        
        # 공분산 행렬 (5x5)
        self.P = np.eye(5) * 1.0
        self.P[2, 2] = 0.1  # volatility는 더 작은 불확실성
        
        # 시스템 노이즈 (5x5)
        self.Q = np.eye(5) * 0.01
        self.Q[0, 0] = 0.005  # trend는 더 안정적
        self.Q[2, 2] = 0.02   # volatility는 더 변동적
        
        # 측정 노이즈 (5x5)
        self.R = np.eye(5) * 0.1
        self.R[3, 3] = 0.5    # macro_signal은 더 노이즈 많음
        self.R[4, 4] = 0.3    # tech_signal은 중간 노이즈
        
        # 상태 전이 행렬 (5x5)
        self.F = np.eye(5)
        self.F[0, 1] = 0.1    # trend ← momentum
        self.F[1, 0] = 0.05   # momentum ← trend
        self.F[3, 0] = 0.1    # macro_signal ← trend
        self.F[4, 1] = 0.1    # tech_signal ← momentum
        
        # 측정 행렬 (5x5) - 단위행렬 (각 상태를 직접 관측)
        self.H = np.eye(5)
        
        # 성능 모니터링
        self.innovation_history = []
        self.state_history = []
        self.step_count = 0

    def _predict(self) -> None:
        """예측 단계"""
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q

    def _update(self, z: NDArray) -> None:
        """업데이트 단계"""
        # Innovation (예측 오차)
        y = z - self.H @ self.x
        
        # Innovation 공분산
        S = self.H @ self.P @ self.H.T + self.R
        
        # Kalman Gain
        K = self.P @ self.H.T @ np.linalg.inv(S)
        
        # 상태 업데이트
        self.x = self.x + K @ y
        self.P = (np.eye(5) - K @ self.H) @ self.P
        
        # 성능 모니터링
        self.innovation_history.append(y)
        self.state_history.append(self.x.copy())
        self.step_count += 1

    def step(self, z: NDArray) -> None:
        """칼만 필터 한 스텝 실행"""
        self._predict()
        self._update(z)
    
    def get_performance_metrics(self) -> dict:
        """성능 지표 반환"""
        if len(self.innovation_history) < 1:
            return {
                "innovation_mean": [0.0] * 5,
                "innovation_std": [0.0] * 5,
                "state_std": [0.0] * 5,
                "max_innovation": [0.0] * 5,
                "is_diverging": False,
                "step_count": self.step_count,
                "status": "initializing"
            }
        
        innovations = np.array(self.innovation_history)
        states = np.array(self.state_history)
        
        # Innovation 통계
        innovation_mean = np.mean(innovations, axis=0)
        innovation_std = np.std(innovations, axis=0) if len(innovations) > 1 else np.zeros_like(innovation_mean)
        
        # 상태 안정성
        state_std = np.std(states, axis=0) if len(states) > 1 else np.zeros_like(states[0])
        
        # Divergence 감지 (innovation이 너무 크면)
        max_innovation = np.max(np.abs(innovations), axis=0)
        is_diverging = np.any(max_innovation > 5.0)  # 임계값
        
        # 상태 결정: 초기화 중이거나 안정적이거나 발산 중
        if self.step_count < 3:
            status = "initializing"
        elif is_diverging:
            status = "diverging"
        else:
            status = "stable"
        
        return {
            "innovation_mean": innovation_mean.tolist(),
            "innovation_std": innovation_std.tolist(),
            "state_std": state_std.tolist(),
            "max_innovation": max_innovation.tolist(),
            "is_diverging": bool(is_diverging),
            "step_count": self.step_count,
            "status": status
        }
    
    def reset(self) -> None:
        """필터 초기화"""
        self.x = np.array([0.0, 0.0, 0.2, 0.0, 0.0])
        self.P = np.eye(5) * 1.0
        self.P[2, 2] = 0.1
        self.innovation_history = []
        self.state_history = []
        self.step_count = 0 