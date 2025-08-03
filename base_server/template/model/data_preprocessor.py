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

class StockDataPreprocessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scaler = MinMaxScaler()
    
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
        
        self.logger.info(f"Added technical indicators for {len(df_copy)} records")
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
    
    def create_sequences(self, df: pd.DataFrame, sequence_length: int = 60, prediction_length: int = 5) -> Tuple[np.ndarray, np.ndarray]:
        """
        LSTM 학습용 시퀀스 데이터 생성
        
        Args:
            df: 전처리된 데이터프레임
            sequence_length: 입력 시퀀스 길이 (60일)
            prediction_length: 예측 길이 (5일)
            
        Returns:
            (X, y) - 입력 시퀀스와 타겟 시퀀스
        """
        # 학습에 사용할 피처 선택
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
        
        # 정규화
        feature_data_scaled = self.scaler.fit_transform(feature_data)
        
        X, y = [], []
        
        for i in range(len(feature_data_scaled) - sequence_length - prediction_length + 1):
            # 입력: 과거 60일의 모든 피처
            X.append(feature_data_scaled[i:(i + sequence_length)])
            
            # 타겟: 다음 5일의 Close, BB_Upper, BB_Lower
            y.append(target_data[(i + sequence_length):(i + sequence_length + prediction_length)])
        
        X = np.array(X)
        y = np.array(y)
        
        self.logger.info(f"Created sequences - X shape: {X.shape}, y shape: {y.shape}")
        return X, y
    
    def preprocess_for_inference(self, df: pd.DataFrame) -> np.ndarray:
        """
        추론용 데이터 전처리
        
        Args:
            df: 최근 60일 OHLCV 데이터
            
        Returns:
            정규화된 시퀀스 데이터
        """
        # 전처리 파이프라인 적용
        df_processed = self.preprocess_data(df)
        
        # 피처 선택
        feature_columns = [
            'Open', 'High', 'Low', 'Close', 'Volume',
            'MA_5', 'MA_20', 'MA_60',
            'BB_Upper', 'BB_Middle', 'BB_Lower', 'BB_Percent', 'BB_Width',
            'RSI', 'MACD', 'MACD_Signal', 'Price_Change', 'Volatility'
        ]
        
        feature_data = df_processed[feature_columns].values
        
        # 정규화 (학습 시 사용한 scaler 사용)
        feature_data_scaled = self.scaler.transform(feature_data)
        
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