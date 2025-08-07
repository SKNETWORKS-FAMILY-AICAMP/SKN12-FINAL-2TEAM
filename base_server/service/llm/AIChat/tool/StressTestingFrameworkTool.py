"""
stress_testing.py
=================
StressTestingFramework  ➡  BaseFinanceTool 상속 + `get_data()` 표준 버전

● 모델
    • 다변량 t-분포(Monte-Carlo) 시뮬레이션
        X = μ + L · Z       (Z ~ t_ν,  L = chol(Σ))
    • 사용자 정의 스트레스 시나리오(역사·가상·역스트레스) 확장 가능
    • 기본 산출물 : VaR / CVaR / 테일 리스크(%)

● 입력 (get_data)
    weights       : np.ndarray(N,)          # 포트폴리오 비중
    mu            : np.ndarray(N,)          # 인자 평균
    cov           : np.ndarray(N,N)         # 인자 공분산
    n_sim         : int = 10_000            # 시뮬레이션 횟수
    nu            : int = 6                 # t 분포 자유도
    conf_lvls     : List[float] = [0.99, 0.95]
    max_latency   : float = 1.0

● 출력(dict)
    {
        'VaR'   : {α: float},
        'CVaR'  : {α: float},
        'tail'  : {α: float},              # 초과 비율
        'elapsed': float
    }
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional

import numpy as np
from numpy.typing import NDArray
from scipy.stats import t as student_t

from BaseFinanceTool import BaseFinanceTool

__all__ = ["StressTestingFramework"]


class StressTestingFramework(BaseFinanceTool):
    """Monte-Carlo 기반 VaR / CVaR 스트레스 테스트"""

    # ---------------------------- 초기화 --------------------------- #
    def __init__(self) -> None:
        super().__init__()  # API-Key 불필요

    # ------------------------ 시나리오 생성 ------------------------ #
    @staticmethod
    def _mc_scenarios(
        mu: NDArray,
        cov: NDArray,
        n_sim: int,
        nu: int,
    ) -> NDArray:
        """
        다변량 Student-t 시뮬레이션
            X = μ + L · Z      (Z ~ t_ν)
        """
        L = np.linalg.cholesky(cov)
        Z = student_t.rvs(df=nu, size=(n_sim, mu.size))
        return mu + Z @ L.T

    # ------------------------- 손익 계산 --------------------------- #
    @staticmethod
    def _pnl(weights: NDArray, scenarios: NDArray) -> NDArray:
        return scenarios @ weights

    # --------------------------- get_data ------------------------- #
    def get_data(
        self,
        weights: NDArray,
        tickers: List[str],
        start_date: str,
        end_date: str,
        *,
        n_sim: int = 10_000,
        nu: int = 6,
        conf_lvls: Optional[List[float]] = None,
        max_latency: float = 1.0,
    ) -> Dict:
        """
        Monte-Carlo 스트레스 테스트 → VaR/CVaR/테일리스크
        """
        t0 = time.time()
        conf_lvls = conf_lvls or [0.99, 0.95]

        # FeaturePipelineTool을 사용하여 가격 데이터 추출
        from service.llm.AIChat.tool.FeaturePipelineTool import FeaturePipelineTool
        from service.llm.AIChat.BasicTools.MarketDataTool import MarketDataTool # MarketDataTool 임포트

        # MarketDataTool을 사용하여 mu와 cov 계산
        market_data_tool = MarketDataTool(self.ai_chat_service)
        # MarketDataTool의 _expected_returns와 _covariance_matrix는 내부 메서드이므로,
        # FeaturePipelineTool에서 이들을 호출하거나, MarketDataTool의 get_data를 통해
        # 필요한 통계량을 얻어야 합니다. 여기서는 MarketDataTool의 get_data를 활용합니다.
        market_output = market_data_tool.get_data(tickers=tickers, start_date=start_date, end_date=end_date)

        mu = np.array([market_output.expected_returns.get(t, 0.0) for t in tickers])
        cov_dict = market_output.covariance_matrix
        if cov_dict is None:
            raise RuntimeError("공분산 행렬을 가져올 수 없습니다.")
        cov = pd.DataFrame(cov_dict).values # dict를 pandas DataFrame으로 변환 후 numpy 배열로

        # ① 시나리오
        scen = self._mc_scenarios(mu, cov, n_sim, nu)
        pnl = self._pnl(weights, scen)

        # ② 지표 계산
        var_out, cvar_out, tail_out = {}, {}, {}
        for cl in conf_lvls:
            perc = 100 * (1 - cl)
            var_val = np.percentile(pnl, perc)
            cvar_val = pnl[pnl <= var_val].mean()
            var_out[cl] = float(var_val)
            cvar_out[cl] = float(cvar_val)
            tail_out[cl] = float((pnl < var_val).mean())

        elapsed = time.time() - t0
        if elapsed > max_latency:
            raise RuntimeError(f"Latency {elapsed:.3f}s > {max_latency}s")

        return {
            "VaR": var_out,
            "CVaR": cvar_out,
            "tail": tail_out,
            "elapsed": elapsed,
        }


# --------------------------------------------------------------------- #
# 간단 데모
# --------------------------------------------------------------------- #
if __name__ == "__main__":
    np.random.seed(42)
    demo_mu = np.array([0.01, 0.005, 0.0])
    demo_cov = np.array([[0.04, 0.01, 0.0], [0.01, 0.03, 0.0], [0.0, 0.0, 0.06]])
    demo_w = np.array([0.5, 0.3, 0.2])

    stf = StressTestingFramework()
    res = stf.get_data(demo_w, demo_mu, demo_cov, n_sim=5_000)
    print(res)
