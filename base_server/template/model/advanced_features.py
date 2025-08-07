"""
고급 피처 엔지니어링 모듈
주식 예측 성능 향상을 위한 고급 기술적 지표들
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class AdvancedFeatureEngineering:
    """
    고급 피처 엔지니어링 클래스
    30+ 고급 기술적 지표 및 시장 체제 인식 피처 생성
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    # ============================================================================
    # 고급 기술적 지표 (Advanced Technical Indicators)
    # ============================================================================
    
    def calculate_stochastic(self, df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
        """
        Stochastic Oscillator (%K, %D) 계산
        모멘텀 지표로 과매수/과매도 상태 식별
        """
        df_copy = df.copy()
        
        # %K 계산
        lowest_low = df_copy['Low'].rolling(window=k_period).min()
        highest_high = df_copy['High'].rolling(window=k_period).max()
        
        df_copy['Stoch_K'] = 100 * (df_copy['Close'] - lowest_low) / (highest_high - lowest_low)
        
        # %D 계산 (K의 이동평균)
        df_copy['Stoch_D'] = df_copy['Stoch_K'].rolling(window=d_period).mean()
        
        # NaN 처리
        df_copy['Stoch_K'] = df_copy['Stoch_K'].fillna(50)
        df_copy['Stoch_D'] = df_copy['Stoch_D'].fillna(50)
        
        return df_copy
    
    def calculate_williams_r(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        Williams %R 계산
        과매수/과매도 식별 지표 (-100 ~ 0 범위)
        """
        df_copy = df.copy()
        
        highest_high = df_copy['High'].rolling(window=period).max()
        lowest_low = df_copy['Low'].rolling(window=period).min()
        
        df_copy['Williams_R'] = -100 * (highest_high - df_copy['Close']) / (highest_high - lowest_low)
        df_copy['Williams_R'] = df_copy['Williams_R'].fillna(-50)
        
        return df_copy
    
    def calculate_cci(self, df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        """
        Commodity Channel Index (CCI) 계산
        사이클 지표로 추세 변화 포착
        """
        df_copy = df.copy()
        
        # Typical Price 계산
        typical_price = (df_copy['High'] + df_copy['Low'] + df_copy['Close']) / 3
        
        # SMA와 Mean Deviation 계산
        sma_tp = typical_price.rolling(window=period).mean()
        mad = typical_price.rolling(window=period).apply(lambda x: np.mean(np.abs(x - x.mean())))
        
        # CCI 계산
        df_copy['CCI'] = (typical_price - sma_tp) / (0.015 * mad)
        df_copy['CCI'] = df_copy['CCI'].fillna(0)
        
        return df_copy
    
    def calculate_mfi(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        Money Flow Index (MFI) 계산
        거래량을 고려한 RSI (0-100 범위)
        """
        df_copy = df.copy()
        
        # Typical Price와 Money Flow 계산
        typical_price = (df_copy['High'] + df_copy['Low'] + df_copy['Close']) / 3
        money_flow = typical_price * df_copy['Volume']
        
        # Positive/Negative Money Flow
        positive_mf = money_flow.where(typical_price > typical_price.shift(1), 0)
        negative_mf = money_flow.where(typical_price < typical_price.shift(1), 0)
        
        # Money Flow Ratio와 MFI
        positive_mf_sum = positive_mf.rolling(window=period).sum()
        negative_mf_sum = negative_mf.rolling(window=period).sum()
        
        mfr = positive_mf_sum / negative_mf_sum
        df_copy['MFI'] = 100 - (100 / (1 + mfr))
        df_copy['MFI'] = df_copy['MFI'].fillna(50)
        
        return df_copy
    
    def calculate_obv(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        On-Balance Volume (OBV) 계산
        가격과 거래량의 관계 분석
        """
        df_copy = df.copy()
        
        # OBV 계산
        obv = [0]
        for i in range(1, len(df_copy)):
            if df_copy['Close'].iloc[i] > df_copy['Close'].iloc[i-1]:
                obv.append(obv[-1] + df_copy['Volume'].iloc[i])
            elif df_copy['Close'].iloc[i] < df_copy['Close'].iloc[i-1]:
                obv.append(obv[-1] - df_copy['Volume'].iloc[i])
            else:
                obv.append(obv[-1])
        
        df_copy['OBV'] = obv
        
        # OBV 정규화 (이동평균 대비 비율)
        obv_ma = pd.Series(obv).rolling(window=20).mean()
        df_copy['OBV_Ratio'] = pd.Series(obv) / obv_ma
        df_copy['OBV_Ratio'] = df_copy['OBV_Ratio'].fillna(1.0)
        
        return df_copy
    
    def calculate_cmf(self, df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        """
        Chaikin Money Flow (CMF) 계산
        매수/매도 압력 측정 (-1 ~ +1 범위)
        """
        df_copy = df.copy()
        
        # Money Flow Multiplier
        mfm = ((df_copy['Close'] - df_copy['Low']) - (df_copy['High'] - df_copy['Close'])) / (df_copy['High'] - df_copy['Low'])
        mfm = mfm.fillna(0)  # 분모가 0인 경우 처리
        
        # Money Flow Volume
        mfv = mfm * df_copy['Volume']
        
        # CMF 계산
        df_copy['CMF'] = mfv.rolling(window=period).sum() / df_copy['Volume'].rolling(window=period).sum()
        df_copy['CMF'] = df_copy['CMF'].fillna(0)
        
        return df_copy
    
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        Average True Range (ATR) 계산
        변동성 측정 지표
        """
        df_copy = df.copy()
        
        # True Range 계산
        high_low = df_copy['High'] - df_copy['Low']
        high_close_prev = np.abs(df_copy['High'] - df_copy['Close'].shift(1))
        low_close_prev = np.abs(df_copy['Low'] - df_copy['Close'].shift(1))
        
        true_range = np.maximum(high_low, np.maximum(high_close_prev, low_close_prev))
        
        # ATR 계산 (지수 이동평균)
        df_copy['ATR'] = pd.Series(true_range).ewm(span=period).mean()
        df_copy['ATR'] = df_copy['ATR'].fillna(df_copy['ATR'].mean())
        
        # ATR 정규화 (Close 대비 비율)
        df_copy['ATR_Ratio'] = df_copy['ATR'] / df_copy['Close']
        
        return df_copy
    
    def calculate_parabolic_sar(self, df: pd.DataFrame, af_start: float = 0.02, af_max: float = 0.2) -> pd.DataFrame:
        """
        Parabolic SAR 계산
        추세 반전 포인트 식별
        """
        df_copy = df.copy()
        
        high = df_copy['High'].values
        low = df_copy['Low'].values
        close = df_copy['Close'].values
        
        # SAR 초기값 설정
        sar = np.zeros(len(df_copy))
        trend = np.ones(len(df_copy))  # 1: 상승, -1: 하락
        af = np.ones(len(df_copy)) * af_start
        ep = np.zeros(len(df_copy))  # Extreme Point
        
        # 초기값
        sar[0] = low[0]
        ep[0] = high[0]
        
        for i in range(1, len(df_copy)):
            # SAR 계산
            sar[i] = sar[i-1] + af[i-1] * (ep[i-1] - sar[i-1])
            
            # 추세 판단
            if trend[i-1] == 1:  # 상승 추세
                if low[i] <= sar[i]:
                    trend[i] = -1
                    sar[i] = ep[i-1]
                    ep[i] = low[i]
                    af[i] = af_start
                else:
                    trend[i] = 1
                    if high[i] > ep[i-1]:
                        ep[i] = high[i]
                        af[i] = min(af[i-1] + af_start, af_max)
                    else:
                        ep[i] = ep[i-1]
                        af[i] = af[i-1]
            else:  # 하락 추세
                if high[i] >= sar[i]:
                    trend[i] = 1
                    sar[i] = ep[i-1]
                    ep[i] = high[i]
                    af[i] = af_start
                else:
                    trend[i] = -1
                    if low[i] < ep[i-1]:
                        ep[i] = low[i]
                        af[i] = min(af[i-1] + af_start, af_max)
                    else:
                        ep[i] = ep[i-1]
                        af[i] = af[i-1]
        
        df_copy['PSAR'] = sar
        df_copy['PSAR_Trend'] = trend
        
        return df_copy
    
    # ============================================================================
    # 시장 체제 인식 피처 (Market Regime Features)
    # ============================================================================
    
    def calculate_volatility_regime(self, df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """
        변동성 체제 인식
        저변동성/고변동성 체제 구분
        """
        df_copy = df.copy()
        
        # 롤링 변동성 계산
        returns = df_copy['Close'].pct_change()
        rolling_vol = returns.rolling(window=window).std() * np.sqrt(252)  # 연환산
        
        # 변동성 분위수 계산
        vol_quantiles = rolling_vol.quantile([0.33, 0.67])
        
        # 변동성 체제 분류
        regime = np.zeros(len(df_copy))
        regime[rolling_vol <= vol_quantiles.iloc[0]] = 0  # 저변동성
        regime[(rolling_vol > vol_quantiles.iloc[0]) & (rolling_vol <= vol_quantiles.iloc[1])] = 1  # 중변동성
        regime[rolling_vol > vol_quantiles.iloc[1]] = 2  # 고변동성
        
        df_copy['Vol_Regime'] = regime
        df_copy['Vol_Level'] = rolling_vol
        
        return df_copy
    
    def calculate_trend_strength(self, df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """
        추세 강도 계산
        ADX(Average Directional Index) 기반
        """
        df_copy = df.copy()
        
        # True Range 계산
        tr = self.calculate_atr(df_copy, period=1)['ATR']
        
        # Directional Movements
        dm_plus = np.maximum(df_copy['High'] - df_copy['High'].shift(1), 0)
        dm_minus = np.maximum(df_copy['Low'].shift(1) - df_copy['Low'], 0)
        
        # 조건부 DM
        dm_plus[dm_plus <= dm_minus] = 0
        dm_minus[dm_minus <= dm_plus] = 0
        
        # Smoothed values
        dm_plus_smooth = dm_plus.ewm(span=window).mean()
        dm_minus_smooth = dm_minus.ewm(span=window).mean()
        tr_smooth = tr.ewm(span=window).mean()
        
        # DI 계산
        di_plus = 100 * dm_plus_smooth / tr_smooth
        di_minus = 100 * dm_minus_smooth / tr_smooth
        
        # ADX 계산
        dx = 100 * np.abs(di_plus - di_minus) / (di_plus + di_minus)
        adx = dx.ewm(span=window).mean()
        
        df_copy['ADX'] = adx.fillna(25)
        df_copy['DI_Plus'] = di_plus.fillna(25)
        df_copy['DI_Minus'] = di_minus.fillna(25)
        
        # 추세 강도 분류
        trend_strength = np.zeros(len(df_copy))
        trend_strength[adx <= 25] = 0  # 약한 추세
        trend_strength[(adx > 25) & (adx <= 50)] = 1  # 중간 추세
        trend_strength[adx > 50] = 2  # 강한 추세
        
        df_copy['Trend_Strength'] = trend_strength
        
        return df_copy
    
    def calculate_market_microstructure(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        시장 미시구조 피처
        가격-거래량 관계, 스프레드 등
        """
        df_copy = df.copy()
        
        # VWAP (Volume Weighted Average Price)
        typical_price = (df_copy['High'] + df_copy['Low'] + df_copy['Close']) / 3
        vwap = (typical_price * df_copy['Volume']).cumsum() / df_copy['Volume'].cumsum()
        df_copy['VWAP'] = vwap
        
        # Price-Volume Correlation
        pv_corr = df_copy['Close'].rolling(window=20).corr(df_copy['Volume'])
        df_copy['PV_Corr'] = pv_corr.fillna(0)
        
        # Intraday Range
        df_copy['Intraday_Range'] = (df_copy['High'] - df_copy['Low']) / df_copy['Close']
        
        # Volume Profile (상대적 거래량)
        vol_ma = df_copy['Volume'].rolling(window=20).mean()
        df_copy['Volume_Profile'] = df_copy['Volume'] / vol_ma
        df_copy['Volume_Profile'] = df_copy['Volume_Profile'].fillna(1.0)
        
        return df_copy
    
    # ============================================================================
    # 통합 피처 생성 함수
    # ============================================================================
    
    def add_all_advanced_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        모든 고급 피처를 데이터프레임에 추가
        
        Args:
            df: 기본 OHLCV 데이터프레임
            
        Returns:
            고급 피처가 추가된 데이터프레임 (30+ 피처)
        """
        self.logger.info("🚀 Starting advanced feature engineering...")
        
        df_enhanced = df.copy()
        
        # 1. 고급 기술적 지표
        df_enhanced = self.calculate_stochastic(df_enhanced)
        df_enhanced = self.calculate_williams_r(df_enhanced)
        df_enhanced = self.calculate_cci(df_enhanced)
        df_enhanced = self.calculate_mfi(df_enhanced)
        df_enhanced = self.calculate_obv(df_enhanced)
        df_enhanced = self.calculate_cmf(df_enhanced)
        df_enhanced = self.calculate_atr(df_enhanced)
        df_enhanced = self.calculate_parabolic_sar(df_enhanced)
        
        # 2. 시장 체제 인식 피처
        df_enhanced = self.calculate_volatility_regime(df_enhanced)
        df_enhanced = self.calculate_trend_strength(df_enhanced)
        df_enhanced = self.calculate_market_microstructure(df_enhanced)
        
        # 3. 추가 파생 피처
        df_enhanced = self._add_momentum_features(df_enhanced)
        df_enhanced = self._add_statistical_features(df_enhanced)
        
        # NaN 처리
        df_enhanced = df_enhanced.fillna(method='bfill').fillna(method='ffill')
        
        feature_count = len(df_enhanced.columns) - len(df.columns)
        self.logger.info(f"✅ Added {feature_count} advanced features")
        
        return df_enhanced
    
    def _add_momentum_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """모멘텀 관련 추가 피처"""
        df_copy = df.copy()
        
        # Rate of Change (ROC)
        for period in [5, 10, 20]:
            df_copy[f'ROC_{period}'] = df_copy['Close'].pct_change(period) * 100
        
        # Price Momentum
        df_copy['Price_Momentum'] = (df_copy['Close'] / df_copy['Close'].shift(10) - 1) * 100
        
        # Volume Momentum  
        df_copy['Volume_Momentum'] = (df_copy['Volume'] / df_copy['Volume'].shift(10) - 1) * 100
        
        return df_copy
    
    def _add_statistical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """통계적 피처 추가"""
        df_copy = df.copy()
        
        # Skewness와 Kurtosis (20일 롤링)
        returns = df_copy['Close'].pct_change()
        df_copy['Returns_Skew'] = returns.rolling(window=20).skew()
        df_copy['Returns_Kurt'] = returns.rolling(window=20).kurt()
        
        # Z-Score (표준화된 가격)
        price_mean = df_copy['Close'].rolling(window=20).mean()
        price_std = df_copy['Close'].rolling(window=20).std()
        df_copy['Price_ZScore'] = (df_copy['Close'] - price_mean) / price_std
        
        return df_copy
    
    def get_feature_importance_ranking(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        피처 중요도 분류
        
        Returns:
            피처별 카테고리 분류 딕셔너리
        """
        feature_categories = {
            # 기본 OHLCV
            'Price_Features': ['Open', 'High', 'Low', 'Close'],
            'Volume_Features': ['Volume', 'OBV', 'OBV_Ratio', 'Volume_Profile', 'Volume_Momentum'],
            
            # 추세 지표
            'Trend_Features': ['MA_5', 'MA_20', 'MA_60', 'PSAR', 'PSAR_Trend', 'ADX', 'DI_Plus', 'DI_Minus'],
            
            # 모멘텀 지표
            'Momentum_Features': ['RSI', 'Stoch_K', 'Stoch_D', 'Williams_R', 'CCI', 'MFI', 'ROC_5', 'ROC_10', 'ROC_20', 'Price_Momentum'],
            
            # 변동성 지표
            'Volatility_Features': ['BB_Upper', 'BB_Lower', 'BB_Percent', 'BB_Width', 'ATR', 'ATR_Ratio', 'Vol_Level', 'Intraday_Range'],
            
            # 시장 체제
            'Regime_Features': ['Vol_Regime', 'Trend_Strength'],
            
            # 시장 미시구조
            'Microstructure_Features': ['VWAP', 'PV_Corr', 'CMF'],
            
            # 통계적 피처
            'Statistical_Features': ['Price_Change', 'Volatility', 'Returns_Skew', 'Returns_Kurt', 'Price_ZScore']
        }
        
        return feature_categories

# 사용 예시 및 테스트
if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    
    # 테스트용 더미 데이터 생성
    dates = pd.date_range('2020-01-01', periods=1000, freq='D')
    np.random.seed(42)
    
    # 가상의 주식 데이터 생성
    price = 100
    prices = [price]
    volumes = []
    
    for _ in range(999):
        change = np.random.normal(0, 0.02)  # 2% 일일 변동성
        price = price * (1 + change)
        prices.append(price)
        volumes.append(np.random.lognormal(15, 0.5))  # 로그정규 분포 거래량
    
    # 고가, 저가 생성
    highs = [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices]
    lows = [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices]
    
    test_df = pd.DataFrame({
        'Date': dates,
        'Open': prices,
        'High': highs,
        'Low': lows,
        'Close': prices,
        'Volume': volumes
    })
    
    # 고급 피처 엔지니어링 적용
    feature_eng = AdvancedFeatureEngineering()
    enhanced_df = feature_eng.add_all_advanced_features(test_df)
    
    print(f"✅ Original features: {len(test_df.columns)}")
    print(f"🚀 Enhanced features: {len(enhanced_df.columns)}")
    print(f"📈 Added features: {len(enhanced_df.columns) - len(test_df.columns)}")
    
    # 피처 카테고리 출력
    categories = feature_eng.get_feature_importance_ranking(enhanced_df)
    print("\n=== Feature Categories ===")
    for category, features in categories.items():
        available_features = [f for f in features if f in enhanced_df.columns]
        print(f"{category}: {len(available_features)} features")
        print(f"  {available_features}")
        print()