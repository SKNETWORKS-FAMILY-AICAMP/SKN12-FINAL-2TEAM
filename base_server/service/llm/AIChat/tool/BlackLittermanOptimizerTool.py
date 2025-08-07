"""
black_litterman_optimizer.py
============================
BlackLittermanOptimizer  ➡  BaseFinanceTool 상속 + `get_data()` 통일 버전

● 입력
    market_data     : dict
        └ 'assets'   : List[str]       # 자산 심볼
        └ 'cov'      : np.ndarray(N,N) # 시장 공분산
        └ 'mu_prior' : np.ndarray(N,)  # 시장 균형 기대수익(CAPM)
    specialist_data : dict
        └ macro / technical / fundamental / news 등
    risk_free       : float  (기본 0.02)

● 출력(dict)
    {
        'assets'  : List[str],
        'weights' : np.ndarray(N,),   # 최적 비중(합=1)
        'mu_new'  : np.ndarray(N,),   # 뷰 반영 기대수익
        'cov_new' : np.ndarray(N,N),  # 뷰 반영 공분산
        'views'   : List[dict],       # 생성된 투자자 관점
        'elapsed' : float             # 처리 시간(초)
    }
"""

from __future__ import annotations

import time
from typing import Dict, List

import numpy as np

from BaseFinanceTool import BaseFinanceTool

__all__ = ["BlackLittermanOptimizer"]


class BlackLittermanOptimizer(BaseFinanceTool):
    """시장 균형 + 투자자 뷰 통합 포트폴리오 최적화"""

    def __init__(self) -> None:
        super().__init__()  # API-Key 필요 없음

        # 하이퍼파라미터
        self.tau: float = 0.025  # 추정 불확실성 스케일
        self.confidence_scaling = {
            "macro": 0.8,
            "technical": 0.6,
            "fundamental": 0.7,
            "news": 0.4,
        }

    # ----------------------------------------------------------------- #
    #                     1) 투자자 View 생성                           #
    # ----------------------------------------------------------------- #
    def _generate_views(
        self, features: Dict, assets: List[str]
    ) -> List[Dict]:
        """거시·기술·펀더멘털 정보를 바탕으로 투자자 관점 생성"""
        views = []

        # ※ 예시는 간단 로직 — 실제 서비스에서는 복잡한 룰/ML 활용
        # ① 거시: GDP 성장률이 높으면 주식 ETF relative view
        if features.get("GDP", 0.0) > 2.5:
            views.append(
                {
                    "assets": ["SPY", "QQQ"],
                    "relative_return": 0.05,
                    "confidence": self.confidence_scaling["macro"],
                }
            )

        # ② 기술: RSI<30 자산은 mean-reversion long view
        # features 딕셔너리에서 각 티커별 RSI를 직접 가져오는 방식으로 변경
        for ast in assets:
            # 예시: features["RSI_AAPL"], features["RSI_MSFT"] 와 같이 저장된다고 가정
            # FeaturePipelineTool에서 각 티커별 RSI를 반환하도록 수정 필요
            # 현재 FeaturePipelineTool은 단일 RSI만 반환하므로, 이 부분은 더 정교한 설계가 필요함
            # 여기서는 간단히 첫 번째 티커의 RSI를 사용한다고 가정
            if ast == assets[0] and features.get("RSI", 0.0) < 30:
                views.append(
                    {
                        "assets": [ast],
                        "absolute_return": 0.03,
                        "confidence": self.confidence_scaling["technical"],
                    }
                )

        # (③ 펀더멘털 / ④ 뉴스 등 추가 가능)
        return views

    # ----------------------------------------------------------------- #
    #                     2) BL 행렬(P, Q, Ω)                           #
    # ----------------------------------------------------------------- #
    @staticmethod
    def _construct_p(views: List[Dict], assets: List[str]) -> np.ndarray:
        """P 행렬: (num_views × num_assets)"""
        P = np.zeros((len(views), len(assets)))
        for i, v in enumerate(views):
            if "relative_return" in v:  # 2-asset relative view (a − b)
                a1, a2 = v["assets"]
                P[i, assets.index(a1)] = 1.0
                P[i, assets.index(a2)] = -1.0
            else:  # single-asset absolute view
                P[i, assets.index(v["assets"][0])] = 1.0
        return P

    @staticmethod
    def _omega(views: List[Dict]) -> np.ndarray:
        """Ω : 관점별 불확실성(대각)"""
        return np.diag([1.0 / (v["confidence"] + 1e-6) for v in views])

    # ----------------------------------------------------------------- #
    #                     3) BL Closed-Form 업데이트                      #
    # ----------------------------------------------------------------- #
    def _black_litterman(
        self,
        mu_prior: np.ndarray,
        cov: np.ndarray,
        P: np.ndarray,
        Q: np.ndarray,
        omega: np.ndarray,
    ):
        tau_sig_inv = np.linalg.inv(self.tau * cov)
        mid = tau_sig_inv + P.T @ np.linalg.inv(omega) @ P
        mu_new = np.linalg.inv(mid) @ (tau_sig_inv @ mu_prior + P.T @ np.linalg.inv(omega) @ Q)
        cov_new = np.linalg.inv(mid)
        return mu_new, cov_new

    # ----------------------------------------------------------------- #
    #                     4) 위험조정 비중 산출                           #
    # ----------------------------------------------------------------- #
    @staticmethod
    def _max_sharpe_weights(mu: np.ndarray, cov: np.ndarray, rf: float) -> np.ndarray:
        excess = mu - rf
        w = np.linalg.solve(cov, excess)
        w = np.clip(w, 0, None)      # short 금지
        w /= w.sum()
        return w

    # ----------------------------------------------------------------- #
    #                     5) 공개 API : get_data                         #
    # ----------------------------------------------------------------- #
    def get_data(
        self,
        market_data: Dict,
        tickers: List[str],
        start_date: str,
        end_date: str,
        risk_free: float = 0.02,
        *,
        max_latency: float = 1.0,
    ) -> Dict:
        """
        시장 데이터 + 투자자 뷰 → BL 업데이트 → 위험조정 최적화
        """
        t0 = time.time()

        assets = market_data["assets"]
        cov = market_data["cov"]
        mu_prior = market_data["mu_prior"]

        # FeaturePipelineTool을 사용하여 필요한 피처 추출
        from service.llm.AIChat.tool.FeaturePipelineTool import FeaturePipelineTool
        features = FeaturePipelineTool(self.ai_chat_service).transform(
            tickers=tickers,
            start_date=start_date,
            end_date=end_date,
            feature_set=["GDP", "RSI"]
        )

        # ① View 생성
        views = self._generate_views(features, assets)
        if not views:  # 관점 없으면 균형 포트폴리오 사용
            weights = self._max_sharpe_weights(mu_prior, cov, risk_free)
            elapsed = time.time() - t0
            return {
                "assets": assets,
                "weights": weights,
                "mu_new": mu_prior,
                "cov_new": cov,
                "views": [],
                "elapsed": elapsed,
            }

        # ② BL 행렬
        P = self._construct_p(views, assets)
        Q = np.array(
            [v.get("relative_return", v.get("absolute_return", 0.0)) for v in views]
        )
        Ω = self._omega(views)

        # ③ BL 업데이트 → μ_new, Σ_new
        mu_new, cov_new = self._black_litterman(mu_prior, cov, P, Q, Ω)

        # ④ 위험조정(최대 샤프) 비중
        weights = self._max_sharpe_weights(mu_new, cov_new, risk_free)

        elapsed = time.time() - t0
        if elapsed > max_latency:
            raise RuntimeError(f"Latency {elapsed:.3f}s > {max_latency}s")

        return {
            "assets": assets,
            "weights": weights,
            "mu_new": mu_new,
            "cov_new": cov_new,
            "views": views,
            "elapsed": elapsed,
        }


# --------------------------------------------------------------------- #
# 간단 데모: python black_litterman_optimizer.py 로 실행
# --------------------------------------------------------------------- #
if __name__ == "__main__":
    assets = ["SPY", "QQQ", "AAPL", "MSFT"]
    market_data_demo = {
        "assets": assets,
        "cov": np.array(
            [
                [0.04, 0.01, 0.01, 0.01],
                [0.01, 0.05, 0.01, 0.01],
                [0.01, 0.01, 0.06, 0.01],
                [0.01, 0.01, 0.01, 0.07],
            ]
        ),
        "mu_prior": np.array([0.07, 0.08, 0.10, 0.09]),
    }

    spec_data_demo = {
        "macro": {"gdp_growth": 3.0},
        "technical": {"AAPL": {"rsi": 28}, "MSFT": {"rsi": 45}},
    }

    bl = BlackLittermanOptimizer()
    result = bl.get_data(market_data_demo, spec_data_demo)
    print(result)
