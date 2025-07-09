"""
multi_factor_signal.py
======================
MultiFactorSignalGenerator  ➡  BaseFinanceTool 상속 + `get_data()` 통일 버전

● 입력
    agent_data : dict
        └ 'technical'   : {'prices': np.ndarray, 'rsi': float, 'bollinger': {'mid': float, 'std': float}}
        └ 'fundamental' : {'roe': float, 'pe': float, 'sector': {'roe_sector': float, 'sigma_roe': float, 'pe_sector': float}}
        └ 'macro'       : {'gdp_surprise': float, 'cpi_surprise': float, 'rate_surprise': float}
        └ 'news'        : {'sentiment': float, 'vix': float}
    regime : str   ─ 'Bull' | 'Bear' | 'Sideways'

● 출력(dict)
    {
        'momentum'    : float,
        'reversion'   : float,
        'fundamental' : float,
        'macro'       : float,
        'confidence'  : float,
        'final_signal': float,
        'elapsed'     : float   # 처리 시간(초)
    }
"""

from __future__ import annotations

import time
from typing import Dict

import numpy as np
from numpy.typing import NDArray

from BaseFinanceTool import BaseFinanceTool

__all__ = ["MultiFactorSignalGenerator"]


# --------------------------------------------------------------------- #
#                             헬퍼 함수                                 #
# --------------------------------------------------------------------- #
def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + np.exp(-x))


def tanh(x: float) -> float:
    return np.tanh(x)


# --------------------------------------------------------------------- #
#                       Multi-Factor Signal Class                       #
# --------------------------------------------------------------------- #
class MultiFactorSignalGenerator(BaseFinanceTool):
    """모멘텀·평균회귀·펀더멘털·매크로 요인 통합 신호 생성기"""

    # ------------------------------ 초기화 --------------------------- #
    def __init__(self) -> None:
        super().__init__()  # API-Key 필요 없음

        # Regime별 동적 가중치
        self.factor_weights: Dict[str, Dict[str, float]] = {
            "Bull": {"momentum": 0.4, "reversion": 0.1, "fundamental": 0.3, "macro": 0.2},
            "Bear": {"momentum": 0.1, "reversion": 0.4, "fundamental": 0.2, "macro": 0.3},
            "Sideways": {"momentum": 0.2, "reversion": 0.3, "fundamental": 0.3, "macro": 0.2},
        }

    # --------------------------- 신호 함수 --------------------------- #
    @staticmethod
    def momentum_signal(prices: NDArray, rsi: float) -> float:
        sma = prices.mean()
        return (prices[-1] / sma - 1.0) * (1.0 - 2.0 * rsi / 100.0)

    @staticmethod
    def reversion_signal(prices: NDArray, bollinger: Dict[str, float]) -> float:
        z = (prices[-1] - bollinger["mid"]) / (bollinger["std"] + 1e-8)
        returns = np.diff(prices) / prices[:-1]
        R_t = returns[-1]
        sigma_R = returns.std() + 1e-8
        return -tanh(z) * (1.0 - abs(R_t) / sigma_R)

    @staticmethod
    def fundamental_signal(roe: float, pe: float, sector: Dict[str, float]) -> float:
        roe_sector, sigma_roe, pe_sector = (
            sector["roe_sector"],
            sector["sigma_roe"] + 1e-8,
            sector["pe_sector"] + 1e-6,
        )
        pe_relative = pe / pe_sector
        return ((roe - roe_sector) / sigma_roe) * (1.0 - pe_relative)

    @staticmethod
    def macro_signal(
        gdp_s: float, cpi_s: float, rate_s: float, alpha: float = 0.5, beta: float = 0.3, gamma: float = 0.2
    ) -> float:
        return alpha * gdp_s + beta * cpi_s + gamma * rate_s

    @staticmethod
    def confidence_score(sentiment: float, vix: float) -> float:
        return sigmoid(sentiment) * (1.0 - min(vix / 50.0, 1.0))

    # --------------------------- 공용 API --------------------------- #
    def get_data(
        self,
        agent_data: Dict[str, Dict],
        regime: str,
        *,
        max_latency: float = 1.0,
    ) -> Dict[str, float]:
        """
        다양한 요인·Regime에 기반한 통합 매수/매도 신호 계산

        Notes
        -----
        • 최종 출력이 0 이상이면 Long 방향, 0 이하이면 Short 방향으로 해석 가능.
        """
        t0 = time.time()

        tech = agent_data["technical"]
        prices: NDArray = tech["prices"]
        rsi: float = tech["rsi"]
        boll = tech["bollinger"]

        fund = agent_data["fundamental"]
        macro = agent_data["macro"]
        news = agent_data["news"]

        # ① 개별 인자 신호
        s_mom = self.momentum_signal(prices, rsi)
        s_rev = self.reversion_signal(prices, boll)
        s_fnd = self.fundamental_signal(fund["roe"], fund["pe"], fund["sector"])
        s_mac = self.macro_signal(
            macro["gdp_surprise"], macro["cpi_surprise"], macro["rate_surprise"]
        )
        conf = self.confidence_score(news["sentiment"], news["vix"])

        # ② Regime별 가중합
        w = self.factor_weights[regime]
        final = (
            w["momentum"] * s_mom +
            w["reversion"] * s_rev +
            w["fundamental"] * s_fnd +
            w["macro"] * s_mac
        ) * conf

        elapsed = time.time() - t0
        if elapsed > max_latency:
            raise RuntimeError(f"Latency {elapsed:.3f}s > {max_latency}s")

        return {
            "momentum": s_mom,
            "reversion": s_rev,
            "fundamental": s_fnd,
            "macro": s_mac,
            "confidence": conf,
            "final_signal": final,
            "elapsed": elapsed,
        }


# --------------------------------------------------------------------- #
# 간단 데모
# --------------------------------------------------------------------- #
if __name__ == "__main__":
    # Dummy data for quick check
    prices = np.array([100, 101, 103, 102, 104, 106])
    boll = {"mid": prices.mean(), "std": prices.std()}
    demo_data = {
        "technical": {"prices": prices, "rsi": 55.0, "bollinger": boll},
        "fundamental": {"roe": 0.14, "pe": 17, "sector": {"roe_sector": 0.10, "sigma_roe": 0.02, "pe_sector": 15}},
        "macro": {"gdp_surprise": 0.3, "cpi_surprise": 0.1, "rate_surprise": -0.05},
        "news": {"sentiment": 0.3, "vix": 18},
    }

    gen = MultiFactorSignalGenerator()
    out = gen.get_data(demo_data, regime="Bull")
    print(out)
