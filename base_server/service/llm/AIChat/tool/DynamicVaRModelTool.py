"""
dynamic_var.py
==============
DynamicVaRModel  ➡  BaseFinanceTool 상속 + `get_data()` 인터페이스

● 모델
      • GARCH(1,1) 조건부 분산 σ²_t
      • Student-t 분포 누적확률 역함수(ppf)로 VaR 산출
      • 옵션: agent_forecasts(μ_t) 입력 → 구조적 전망 반영
      • 백테스트(Basel 방식, 초과 횟수) 지원

● 입력 (get_data)
      returns          : np.ndarray(shape=(T,))   # 최근 수익률 시계열
      agent_forecasts  : dict | None              # {'mu': float}
      backtest         : bool = False             # True면 백테스트 포함
      confidence_lvls  : List[float] = [0.01, 0.05, 0.1]

● 출력(dict)
      {
        'var'      : {α: np.ndarray(T,)}   # α별 VaR 시퀀스
        'latest'   : {α: float}            # 가장 최근 VaR
        'backtest' : {α: {'breaches', 'total', 'rate'}} | None
        'elapsed'  : float
      }
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional

import numpy as np
from numpy.typing import NDArray
from scipy.stats import t as student_t

from BaseFinanceTool import BaseFinanceTool

__all__ = ["DynamicVaRModel"]


class DynamicVaRModel(BaseFinanceTool):
    """GARCH 기반 동적 VaR + 백테스트"""

    # ------------------------ 초기화 ------------------------------ #
    def __init__(
        self,
        garch_params: Optional[Dict[str, float]] = None,
        nu: int = 6,
    ) -> None:
        """
        Parameters
        ----------
        garch_params : dict
            {'omega': 1e-5, 'alpha': 0.05, 'beta': 0.9}
        nu : int
            Student-t 자유도 (꼬리 두께)
        """
        super().__init__()
        self.gp = garch_params or {"omega": 1.0e-5, "alpha": 0.05, "beta": 0.90}
        self.nu = nu

    # -------------------- GARCH 조건부 분산 ----------------------- #
    def _garch_variance(self, returns: NDArray) -> NDArray:
        omega, alpha, beta = self.gp["omega"], self.gp["alpha"], self.gp["beta"]
        T = returns.size
        var = np.empty(T)
        var[0] = np.var(returns[:20])  # 초기값
        for t in range(1, T):
            var[t] = omega + alpha * returns[t - 1] ** 2 + beta * var[t - 1]
        return var

    # ----------------------- VaR 계산 ----------------------------- #
    def _calc_var_series(
        self,
        returns: NDArray,
        mu_t: float,
        conf_lvls: List[float],
    ) -> Dict[float, NDArray]:
        sigma = np.sqrt(self._garch_variance(returns))
        var_dict = {}
        for cl in conf_lvls:
            q = student_t.ppf(cl, self.nu)
            var_dict[cl] = mu_t + sigma * q
        return var_dict

    # ----------------------- 백테스트 ----------------------------- #
    @staticmethod
    def _backtest(var: Dict[float, NDArray], returns: NDArray):
        results = {}
        for cl, series in var.items():
            breaches = int((returns < series).sum())
            T = returns.size
            results[cl] = {
                "breaches": breaches,
                "total": T,
                "rate": breaches / T,
            }
        return results

    # ------------------------- get_data -------------------------- #
    def get_data(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str,
        *,
        agent_forecasts: Optional[Dict[str, float]] = None,
        backtest: bool = False,
        confidence_lvls: List[float] | None = None,
        max_latency: float = 1.0,
    ) -> Dict:
        """
        tickers : 분석할 종목 리스트
        start_date : 데이터 시작일(YYYY-MM-DD)
        end_date : 데이터 종료일(YYYY-MM-DD)
        agent_forecasts : 구조적 μ_t 전망 (선택)
        """
        t0 = time.time()

        conf_lvls = confidence_lvls or [0.01, 0.05, 0.10]

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

        # 단일 종목인 경우 1차원 배열로 변환
        if returns.ndim > 1 and returns.shape[1] == 1:
            returns = returns.flatten()

        mu_t = (
            agent_forecasts.get("mu", 0.0)
            if agent_forecasts is not None
            else returns[-20:].mean()
        )
        var_series = self._calc_var_series(returns, mu_t, conf_lvls)
        latest = {cl: float(series[-1]) for cl, series in var_series.items()}

        out = {
            "var": var_series,
            "latest": latest,
            "backtest": None,
            "elapsed": time.time() - t0,
        }

        if backtest:
            out["backtest"] = self._backtest(var_series, returns)

        if out["elapsed"] > max_latency:
            raise RuntimeError(
                f"Latency {out['elapsed']:.3f}s exceeds {max_latency}s"
            )
        return out


# --------------------------------------------------------------------- #
# 간단 데모
# --------------------------------------------------------------------- #
if __name__ == "__main__":
    np.random.seed(0)
    demo_returns = np.random.randn(250) * 0.01  # 1년(250d) 수익률
    dvar = DynamicVaRModel()
    result = dvar.get_data(
        demo_returns, agent_forecasts={"mu": 0.0004}, backtest=True
    )
    print("Latest VaR:", result["latest"])
    print("Backtest  :", result["backtest"])
