"""
주식 데이터 전처리 모듈
OHLCV 데이터에서 MA(5,20,60)와 Bollinger Band 계산
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from sklearn.preprocessing import MinMaxScaler
import warnings
warnings.filterwarnings('ignore')

# 🚀 고급 피처 엔지니어링 import
from advanced_features import AdvancedFeatureEngineering

class StockDataPreprocessor:
    def __init__(self, use_log_transform: bool = True):
        self.logger = logging.getLogger(__name__)
        
        # 🔧 로그 변환 설정 (2단계 해결책)
        self.use_log_transform = use_log_transform
        self.price_columns = ['Open', 'High', 'Low', 'Close']  # 로그 변환 대상 컬럼
        self.ma_columns = ['MA_5', 'MA_20', 'MA_60']  # 이동평균도 로그 변환 대상
        self.bb_price_columns = ['BB_Upper', 'BB_Middle', 'BB_Lower']  # 볼린저 밴드도 로그 변환 대상
        
        # 하이브리드 스케일러 시스템
        self.global_scaler = MinMaxScaler()      # 전역 피처 스케일러 (fallback용)
        self.global_target_scaler = MinMaxScaler()  # 전역 타겟 스케일러 (fallback용)
        self.symbol_scalers = {}  # 종목별 개별 피처 스케일러 (우선 사용)
        self.target_scalers = {}  # 종목별 개별 타겟 스케일러 (우선 사용)
        
        # 하위 호환성을 위한 기존 스케일러 (사용 안함)
        self.scaler = MinMaxScaler()
        
        # 🚀 고급 피처 엔지니어링 초기화
        self.advanced_features = AdvancedFeatureEngineering()
        self.advanced_features_enabled = False  # 기본값: 비활성화 (호환성)
        
        if self.use_log_transform:
            self.logger.info("Log transformation enabled for price scaling")
    
    # ============================================================================
    # 로그 변환 함수들 (2단계 해결책)
    # ============================================================================
    
    def apply_log_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        가격 관련 컬럼에 로그 변환 적용
        
        Args:
            df: 원본 데이터프레임
            
        Returns:
            로그 변환된 데이터프레임
        """
        if not self.use_log_transform:
            return df
        
        df_transformed = df.copy()
        
        # 가격 컬럼들에 로그 변환 적용 (작은 값 처리를 위해 +1)
        for col in self.price_columns:
            if col in df_transformed.columns:
                df_transformed[col] = np.log(df_transformed[col] + 1)
        
        # 이동평균 컬럼들에도 로그 변환 적용
        for col in self.ma_columns:
            if col in df_transformed.columns:
                df_transformed[col] = np.log(df_transformed[col] + 1)
        
        # 볼린저 밴드 컬럼들에도 로그 변환 적용
        for col in self.bb_price_columns:
            if col in df_transformed.columns:
                df_transformed[col] = np.log(df_transformed[col] + 1)
        
        self.logger.info(f"Applied log transformation to price columns")
        return df_transformed
    
    def apply_inverse_log_transform(self, values: np.ndarray, is_price_data: bool = True) -> np.ndarray:
        """
        로그 변환된 데이터를 원래 스케일로 역변환
        
        Args:
            values: 로그 변환된 값들
            is_price_data: 가격 데이터 여부 (가격이 아닌 데이터는 역변환하지 않음)
            
        Returns:
            원래 스케일로 복원된 값들
        """
        if not self.use_log_transform or not is_price_data:
            return values
        
        # exp 변환 후 -1 (log(x+1)의 역변환)
        restored_values = np.exp(values) - 1
        
        # 음수값 보정 (가격은 항상 양수여야 함)
        restored_values = np.maximum(restored_values, 0.01)
        
        self.logger.debug(f"Applied inverse log transformation")
        return restored_values
    
    def log_transform_single_value(self, value: float) -> float:
        """단일 값에 로그 변환 적용"""
        if not self.use_log_transform:
            return value
        return np.log(value + 1)
    
    def inverse_log_transform_single_value(self, value: float) -> float:
        """단일 값에 로그 역변환 적용"""
        if not self.use_log_transform:
            return value
        return max(np.exp(value) - 1, 0.01)
    
    def calculate_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        이동평균선 계산 (MA 5, 20, 60)
        
        Args:
            df: OHLCV 데이터프레임
            
        Returns:
            MA가 추가된 데이터프레임
        """
        df_copy = df.copy()
        
        # 이동평균선 계산
        df_copy['MA_5'] = df_copy['Close'].rolling(window=5).mean()
        df_copy['MA_20'] = df_copy['Close'].rolling(window=20).mean()
        df_copy['MA_60'] = df_copy['Close'].rolling(window=60).mean()
        
        # 초기 NaN 값 제거를 위해 forward fill 사용
        df_copy['MA_5'] = df_copy['MA_5'].fillna(method='bfill')
        df_copy['MA_20'] = df_copy['MA_20'].fillna(method='bfill')
        df_copy['MA_60'] = df_copy['MA_60'].fillna(method='bfill')
        
        self.logger.info(f"Calculated moving averages for {len(df_copy)} records")
        return df_copy
    
    def calculate_bollinger_bands(self, df: pd.DataFrame, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
        """
        볼린저 밴드 계산
        
        Args:
            df: OHLCV 데이터프레임
            window: 이동평균 윈도우 (기본 20일)
            num_std: 표준편차 배수 (기본 2.0)
            
        Returns:
            볼린저 밴드가 추가된 데이터프레임
        """
        df_copy = df.copy()
        
        # 20일 이동평균 (중심선)
        df_copy['BB_Middle'] = df_copy['Close'].rolling(window=window).mean()
        
        # 20일 이동표준편차
        rolling_std = df_copy['Close'].rolling(window=window).std()
        
        # 상한선과 하한선
        df_copy['BB_Upper'] = df_copy['BB_Middle'] + (rolling_std * num_std)
        df_copy['BB_Lower'] = df_copy['BB_Middle'] - (rolling_std * num_std)
        
        # %B 계산 (현재 가격이 밴드 내에서 어디에 위치하는지)
        df_copy['BB_Width'] = df_copy['BB_Upper'] - df_copy['BB_Lower']
        df_copy['BB_Percent'] = (df_copy['Close'] - df_copy['BB_Lower']) / (df_copy['BB_Upper'] - df_copy['BB_Lower'])
        
        # 초기 NaN 값 처리
        bb_columns = ['BB_Middle', 'BB_Upper', 'BB_Lower', 'BB_Width', 'BB_Percent']
        for col in bb_columns:
            df_copy[col] = df_copy[col].fillna(method='bfill')
        
        self.logger.info(f"Calculated Bollinger Bands for {len(df_copy)} records")
        return df_copy
    
    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        기술적 지표 추가 (RSI, MACD 등)
        
        Args:
            df: OHLCV 데이터프레임
            
        Returns:
            기술적 지표가 추가된 데이터프레임
        """
        df_copy = df.copy()
        
        # RSI 계산
        df_copy['RSI'] = self.calculate_rsi(df_copy['Close'])
        
        # MACD 계산
        macd_data = self.calculate_macd(df_copy['Close'])
        df_copy['MACD'] = macd_data['MACD']
        df_copy['MACD_Signal'] = macd_data['Signal']
        df_copy['MACD_Histogram'] = macd_data['Histogram']
        
        # 가격 변화율
        df_copy['Price_Change'] = df_copy['Close'].pct_change()
        df_copy['Volume_Change'] = df_copy['Volume'].pct_change()
        
        # 변동성 지표
        df_copy['Volatility'] = df_copy['Price_Change'].rolling(window=20).std()
        
        # NaN 값 처리
        numeric_cols = df_copy.select_dtypes(include=[np.number]).columns
        df_copy[numeric_cols] = df_copy[numeric_cols].fillna(method='bfill').fillna(method='ffill')
        
        # 🚀 고급 피처 엔지니어링 (선택적 활성화)
        if self.advanced_features_enabled:
            df_copy = self.advanced_features.add_all_advanced_features(df_copy)
            self.logger.info("고급 피처 엔지니어링 적용됨 (42개 피처 모드)")
        else:
            self.logger.info("기본 피처만 사용 (18개 피처 모드 - 호환성)")
        
        # 🔧 로그 변환 적용 (2단계 해결책)
        df_copy = self.apply_log_transform(df_copy)
        
        feature_count = len(df_copy.columns)
        self.logger.info(f"✅ Added technical indicators + advanced features: {feature_count} total features for {len(df_copy)} records")
        return df_copy
    
    def calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """RSI 계산"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """MACD 계산"""
        exp_fast = prices.ewm(span=fast).mean()
        exp_slow = prices.ewm(span=slow).mean()
        macd = exp_fast - exp_slow
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        
        return {
            'MACD': macd,
            'Signal': signal_line,
            'Histogram': histogram
        }
    
    def preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        전체 전처리 파이프라인 실행
        
        Args:
            df: 원본 OHLCV 데이터프레임
            
        Returns:
            전처리된 데이터프레임
        """
        self.logger.info(f"Starting preprocessing for {len(df)} records")
        
        # 1. 이동평균선 계산
        df_processed = self.calculate_moving_averages(df)
        
        # 2. 볼린저 밴드 계산
        df_processed = self.calculate_bollinger_bands(df_processed)
        
        # 3. 기술적 지표 추가
        df_processed = self.add_technical_indicators(df_processed)
        
        # 4. 데이터 정렬 (날짜순)
        if 'Date' in df_processed.columns:
            df_processed = df_processed.sort_values('Date').reset_index(drop=True)
        
        self.logger.info(f"Preprocessing completed. Final shape: {df_processed.shape}")
        return df_processed
    
    def create_sequences(self, df: pd.DataFrame, symbol: str, sequence_length: int = 60, prediction_length: int = 5) -> Tuple[np.ndarray, np.ndarray]:
        """
        LSTM 학습용 시퀀스 데이터 생성 (종목별 개별 정규화)
        
        Args:
            df: 전처리된 데이터프레임
            symbol: 종목 심볼 (개별 정규화용)
            sequence_length: 입력 시퀀스 길이 (60일)
            prediction_length: 예측 길이 (5일)
            
        Returns:
            (X, y) - 입력 시퀀스와 타겟 시퀀스
        """
        # 🚀 피처 선택 (고급 피처 활성화 여부에 따라)
        if self.advanced_features_enabled:
            # 고급 피처 포함 (42개)
            feature_columns = [
                # 기본 OHLCV (5개)
                'Open', 'High', 'Low', 'Close', 'Volume',
                
                # 이동평균 및 추세 (8개)
                'MA_5', 'MA_20', 'MA_60', 'ADX', 'DI_Plus', 'DI_Minus', 'PSAR', 'PSAR_Trend',
                
                # 볼린저 밴드 및 변동성 (7개)
                'BB_Upper', 'BB_Middle', 'BB_Lower', 'BB_Percent', 'BB_Width', 'ATR', 'ATR_Ratio',
                
                # 모멘텀 지표 (8개)
                'RSI', 'Stoch_K', 'Stoch_D', 'Williams_R', 'CCI', 'MFI', 'ROC_10', 'Price_Momentum',
                
                # 거래량 지표 (4개)
                'OBV_Ratio', 'CMF', 'Volume_Profile', 'Volume_Momentum',
                
                # 시장 체제 및 미시구조 (6개)
                'Vol_Regime', 'Trend_Strength', 'VWAP', 'PV_Corr', 'Intraday_Range', 'Price_ZScore',
                
                # 기존 기술지표 (4개)
                'MACD', 'MACD_Signal', 'Price_Change', 'Volatility'
            ]
        else:
            # 기본 피처만 (18개 - 호환성)
            feature_columns = [
                'Open', 'High', 'Low', 'Close', 'Volume',
                'MA_5', 'MA_20', 'MA_60',
                'BB_Upper', 'BB_Middle', 'BB_Lower', 'BB_Percent', 'BB_Width',
                'RSI', 'MACD', 'MACD_Signal', 'Price_Change', 'Volatility'
            ]
        
        # 타겟은 다음 5일의 Close, BB_Upper, BB_Lower
        target_columns = ['Close', 'BB_Upper', 'BB_Lower']
        
        # 피처 데이터 준비
        feature_data = df[feature_columns].values
        target_data = df[target_columns].values
        
        # 종목별 개별 스케일러 생성 및 피처 정규화
        if symbol not in self.symbol_scalers:
            self.symbol_scalers[symbol] = MinMaxScaler()
        
        feature_data_scaled = self.symbol_scalers[symbol].fit_transform(feature_data)
        
        # 종목별 개별 타겟 스케일러 생성 및 타겟 정규화
        if symbol not in self.target_scalers:
            self.target_scalers[symbol] = MinMaxScaler()
        
        target_data_scaled = self.target_scalers[symbol].fit_transform(target_data)
        
        X, y = [], []
        
        for i in range(len(feature_data_scaled) - sequence_length - prediction_length + 1):
            # 입력: 과거 60일의 모든 피처 (정규화됨)
            X.append(feature_data_scaled[i:(i + sequence_length)])
            
            # 타겟: 다음 5일의 Close, BB_Upper, BB_Lower (정규화됨)
            y.append(target_data_scaled[(i + sequence_length):(i + sequence_length + prediction_length)])
        
        X = np.array(X)
        y = np.array(y)
        
        self.logger.info(f"Created sequences for {symbol} - X shape: {X.shape}, y shape: {y.shape}")
        self.logger.info(f"  Feature range: [{feature_data_scaled.min():.3f}, {feature_data_scaled.max():.3f}]")
        self.logger.info(f"  Target range: [{target_data_scaled.min():.3f}, {target_data_scaled.max():.3f}]")
        
        return X, y
    
    def inverse_transform_predictions(self, predictions: np.ndarray, symbol: str) -> np.ndarray:
        """
        정규화된 예측값을 원래 스케일로 역변환 (하이브리드 방식)
        
        Args:
            predictions: 정규화된 예측값 (batch_size, prediction_length, num_targets)
            symbol: 종목 심볼
            
        Returns:
            역변환된 예측값
        """
        # 3D → 2D 변환
        original_shape = predictions.shape
        predictions_2d = predictions.reshape(-1, predictions.shape[-1])
        
        # 하이브리드 역변환: 종목별 → 전역 타겟 스케일러 순서로 시도
        if symbol in self.target_scalers:
            # 우선순위 1: 종목별 타겟 스케일러 사용
            predictions_scaled_back = self.target_scalers[symbol].inverse_transform(predictions_2d)
            self.logger.info(f"Using symbol-specific target scaler for {symbol}")
        else:
            # 우선순위 2: 전역 타겟 스케일러 사용
            try:
                predictions_scaled_back = self.global_target_scaler.inverse_transform(predictions_2d)
                self.logger.info(f"Using global target scaler for {symbol}")
            except Exception as e:
                # 최후의 수단: 역변환 없이 그대로 반환
                self.logger.warning(f"No suitable target scaler for {symbol}, returning normalized predictions: {e}")
                predictions_scaled_back = predictions_2d
        
        # 🔧 로그 역변환 적용 (2단계 해결책)
        predictions_original = self.apply_inverse_log_transform(predictions_scaled_back, is_price_data=True)
        
        # 원래 shape로 복원
        predictions_original = predictions_original.reshape(original_shape)
        
        self.logger.info(f"Applied log inverse transform for {symbol}")
        return predictions_original
    
    def preprocess_for_inference(self, df: pd.DataFrame, symbol: str = "DEFAULT") -> np.ndarray:
        """
        추론용 데이터 전처리
        
        Args:
            df: 최근 60일 OHLCV 데이터
            symbol: 주식 심볼 (종목별 스케일러 사용)
            
        Returns:
            정규화된 시퀀스 데이터
        """
        # 전처리 파이프라인 적용
        df_processed = self.preprocess_data(df)
        
        # 🚀 피처 선택 (고급 피처 활성화 여부에 따라)
        if self.advanced_features_enabled:
            # 고급 피처 포함 (42개)
            feature_columns = [
                # 기본 OHLCV (5개)
                'Open', 'High', 'Low', 'Close', 'Volume',
                
                # 이동평균 및 추세 (8개)
                'MA_5', 'MA_20', 'MA_60', 'ADX', 'DI_Plus', 'DI_Minus', 'PSAR', 'PSAR_Trend',
                
                # 볼린저 밴드 및 변동성 (7개)
                'BB_Upper', 'BB_Middle', 'BB_Lower', 'BB_Percent', 'BB_Width', 'ATR', 'ATR_Ratio',
                
                # 모멘텀 지표 (8개)
                'RSI', 'Stoch_K', 'Stoch_D', 'Williams_R', 'CCI', 'MFI', 'ROC_10', 'Price_Momentum',
                
                # 거래량 지표 (4개)
                'OBV_Ratio', 'CMF', 'Volume_Profile', 'Volume_Momentum',
                
                # 시장 체제 및 미시구조 (6개)
                'Vol_Regime', 'Trend_Strength', 'VWAP', 'PV_Corr', 'Intraday_Range', 'Price_ZScore',
                
                # 기존 기술지표 (4개)
                'MACD', 'MACD_Signal', 'Price_Change', 'Volatility'
            ]
        else:
            # 기본 피처만 (18개 - 호환성)
            feature_columns = [
                'Open', 'High', 'Low', 'Close', 'Volume',
                'MA_5', 'MA_20', 'MA_60',
                'BB_Upper', 'BB_Middle', 'BB_Lower', 'BB_Percent', 'BB_Width',
                'RSI', 'MACD', 'MACD_Signal', 'Price_Change', 'Volatility'
            ]
        
        feature_data = df_processed[feature_columns].values
        
        # 하이브리드 스케일링: 종목별 → 전역 스케일러 순서로 시도
        if symbol in self.symbol_scalers:
            # 우선순위 1: 종목별 스케일러 사용 (학습된 종목)
            feature_data_scaled = self.symbol_scalers[symbol].transform(feature_data)
            self.logger.info(f"Using symbol-specific scaler for {symbol}")
        else:
            # 우선순위 2: 전역 스케일러 사용 (새로운 종목)
            try:
                feature_data_scaled = self.global_scaler.transform(feature_data)
                self.logger.info(f"Using global scaler for new symbol: {symbol}")
            except Exception as e:
                # 최후의 수단: 현재 데이터로 임시 스케일러 생성
                self.logger.warning(f"Global scaler failed for {symbol}, creating temporary scaler: {e}")
                temp_scaler = MinMaxScaler()
                feature_data_scaled = temp_scaler.fit_transform(feature_data)
        
        # 마지막 60일만 사용
        if len(feature_data_scaled) >= 60:
            sequence = feature_data_scaled[-60:]
        else:
            # 60일 미만인 경우 패딩
            sequence = np.pad(feature_data_scaled, 
                            ((60 - len(feature_data_scaled), 0), (0, 0)), 
                            mode='edge')
        
        # 배치 차원 추가
        sequence = sequence.reshape(1, 60, -1)
        
        self.logger.info(f"Preprocessed inference data shape: {sequence.shape}")
        return sequence


if __name__ == "__main__":
    # 테스트 코드
    logging.basicConfig(level=logging.INFO)
    
    # 샘플 데이터로 테스트
    dates = pd.date_range('2021-01-01', periods=200, freq='D')
    sample_data = pd.DataFrame({
        'Date': dates,
        'Open': np.random.randn(200).cumsum() + 100,
        'High': np.random.randn(200).cumsum() + 105,
        'Low': np.random.randn(200).cumsum() + 95,
        'Close': np.random.randn(200).cumsum() + 100,
        'Volume': np.random.randint(1000000, 10000000, 200),
        'Symbol': 'TEST'
    })
    
    preprocessor = StockDataPreprocessor()
    processed_data = preprocessor.preprocess_data(sample_data)
    X, y = preprocessor.create_sequences(processed_data)
    
    print(f"Processed data shape: {processed_data.shape}")
    print(f"Sequence data - X: {X.shape}, y: {y.shape}")
    print("Preprocessing test completed successfully!")