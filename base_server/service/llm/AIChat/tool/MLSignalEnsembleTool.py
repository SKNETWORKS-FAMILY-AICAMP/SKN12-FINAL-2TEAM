"""
ml_signal_ensemble.py
=====================
MLSignalEnsemble  ➡  BaseFinanceTool 상속 + `get_data()` 표준 인터페이스

● 구성
    ▸ XGBoost 회귀 신호
    ▸ LSTM 시계열 신호
    ▸ 전통(수식·룰) 신호
    ▸ α, β, γ 가중치로 최종 앙상블

● 사전 학습
    - `fit()` : (X, y) 입력으로 두 모델을 모두 학습
    - 학습이 끝나면 `is_trained` 플래그가 켜짐

● 입력 (get_data)
    current_data       : dict → 특성 엔지니어링에 필요한 모든 원시 데이터
    traditional_signal : float (기본 0.0)

● 출력 (dict)
    {
        'xgb_signal'        : float,
        'lstm_signal'       : float,
        'traditional_signal': float,
        'final_signal'      : float,
        'elapsed'           : float   # 예측 소요 시간
    }
"""

from __future__ import annotations

import time
from typing import Dict, Tuple

import numpy as np
from numpy.typing import NDArray

try:
    import xgboost as xgb
except ImportError:  # 런타임에 없다면 더미
    xgb = None

try:
    from tensorflow import keras
    from keras import layers
except ImportError:
    keras = None

from BaseFinanceTool import BaseFinanceTool

__all__ = ["MLSignalEnsemble"]


# --------------------------------------------------------------------- #
#                         헬퍼: 특성 엔지니어링                           #
# --------------------------------------------------------------------- #
def feature_engineering(data: Dict) -> Tuple[NDArray, NDArray]:
    """
    실제 구현에서는 specialist_agents 데이터를 받아
    ▸ 기술·거시·펀더멘털·감정 지표 등을 벡터화
    여기서는 간단히 더미 배열을 반환
    """
    X = np.random.randn(120, 8)  # 120 샘플, 8 특성
    y = np.random.randn(120)
    return X, y


# --------------------------------------------------------------------- #
#                             앙상블 클래스                              #
# --------------------------------------------------------------------- #
class MLSignalEnsemble(BaseFinanceTool):
    """XGBoost + LSTM + 전통신호 통합 앙상블"""

    def __init__(self) -> None:
        super().__init__()  # API-Key 불필요

        # 1) XGBoost
        self.xgb_model = (
            xgb.XGBRegressor(
                n_estimators=150,
                max_depth=4,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                objective="reg:squarederror",
                verbosity=0,
            )
            if xgb
            else None
        )

        # 2) LSTM
        self.lstm_model = self._build_lstm() if keras else None

        # 3) 가중치
        self.weights = np.array([0.4, 0.4, 0.2])  # [XGB, LSTM, Traditional]

        self.is_trained = False

    # ----------------------------- 모델 -------------------------------- #
    @staticmethod
    def _build_lstm():
        model = keras.Sequential(
            [
                layers.LSTM(64, return_sequences=True, input_shape=(60, 8)),
                layers.Dropout(0.3),
                layers.LSTM(32),
                layers.Dense(16, activation="relu"),
                layers.Dense(1),
            ]
        )
        model.compile(optimizer="adam", loss="mse", verbose=0)
        return model

    # ----------------------------- 학습 -------------------------------- #
    def fit(self, training_raw: Dict) -> None:
        """전처리 → X, y → 두 모델 모두 학습"""
        X, y = feature_engineering(training_raw)

        if self.xgb_model:
            self.xgb_model.fit(X, y)

        if self.lstm_model:
            # 최근 60개 샘플로 LSTM 학습 (데모 간소화)
            X_lstm = X[-60:].reshape(1, 60, 8)
            y_lstm = y[-60:]
            self.lstm_model.fit(X_lstm, y_lstm, epochs=2, verbose=0)

        self.is_trained = True

    # ----------------------------- 예측(get_data) ---------------------- #
    def get_data(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str,
        traditional_signal: float = 0.0,
        *,
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
        traditional_signal : float
            수식 기반(모멘텀, 밸류 등) 전통 신호

        Returns
        -------
        dict : xgb_signal, lstm_signal, traditional_signal, final_signal, elapsed
        """
        if not self.is_trained:
            raise RuntimeError("MLSignalEnsemble must be trained with `.fit()` first.")

        t0 = time.time()

        # FeaturePipelineTool을 사용하여 필요한 피처 추출
        from service.llm.AIChat.tool.FeaturePipelineTool import FeaturePipelineTool
        features = FeaturePipelineTool(self.ai_chat_service).transform(
            tickers=tickers,
            start_date=start_date,
            end_date=end_date,
            feature_set=["RSI", "MACD", "PRICE_HISTORY", "GDP", "CPIAUCSL", "DEXKOUS"]
        )

        # feature_engineering 함수를 features 딕셔너리를 직접 사용하도록 수정
        X, _ = self._feature_engineering_from_features(features)

        xgb_sig = (
            float(self.xgb_model.predict(X[:1])[0]) if self.xgb_model else 0.0
        )
        lstm_sig = (
            float(self.lstm_model.predict(X[:1].reshape(1, 1, 8))[0, 0])
            if self.lstm_model
            else 0.0
        )

        final = (
            self.weights[0] * xgb_sig
            + self.weights[1] * lstm_sig
            + self.weights[2] * traditional_signal
        )

        elapsed = time.time() - t0
        if elapsed > max_latency:
            raise RuntimeError(f"Latency {elapsed:.3f}s > {max_latency}s")

        return {
            "xgb_signal": xgb_sig,
            "lstm_signal": lstm_sig,
            "traditional_signal": traditional_signal,
            "final_signal": final,
            "elapsed": elapsed,
        }

    def _feature_engineering_from_features(self, features: Dict) -> Tuple[NDArray, NDArray]:
        """
        FeaturePipelineTool에서 얻은 features 딕셔너리를 사용하여
        ML 모델의 입력 X, y를 생성합니다.
        실제 구현에서는 features 딕셔너리의 값들을 적절히 가공하여 X를 구성해야 합니다.
        """
        # 예시: features 딕셔너리에서 몇 가지 값을 가져와 더미 X를 생성
        # 실제로는 더 복잡한 로직이 필요합니다.
        gdp = features.get("GDP", 0.0)
        cpi = features.get("CPIAUCSL", 0.0)
        rsi = features.get("RSI", 0.0)
        macd = features.get("MACD", 0.0)
        price_history = features.get("PRICE_HISTORY", pd.DataFrame())

        # 간단한 더미 X 생성 (실제 모델에 맞게 수정 필요)
        X = np.array([[gdp, cpi, rsi, macd, price_history.iloc[-1].get("Adj Close", 0.0) if not price_history.empty else 0.0, 0, 0, 0]])
        y = np.array([0.0]) # 예측 대상 y는 여기서는 사용되지 않으므로 더미 값
        return X, y


# --------------------------------------------------------------------- #
# 데모 실행
# --------------------------------------------------------------------- #
if __name__ == "__main__":
    ens = MLSignalEnsemble()
    # 1) 학습
    ens.fit(training_raw={})
    # 2) 예측
    out = ens.get_data(current_raw={}, traditional_signal=0.1)
    print(out)
