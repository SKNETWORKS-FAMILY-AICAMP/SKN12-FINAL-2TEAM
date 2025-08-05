from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from typing import Dict, Any, Tuple
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd

class KalmanInitializerTool:
    """
    Rule-Based Kalman Filter 초기화 툴
    - 기업별 특성 기반 초기화
    - 시장 상황 반영
    - 프리트레인 없이 즉시 사용 가능
    """
    
    def __init__(self):
        self.max_latency = 5.0  # 5초 제한
    
    def initialize_kalman_state(self, ticker: str) -> Tuple[NDArray, NDArray]:
        """
        룰 기반으로 칼만 필터 초기 상태 생성
        
        Args:
            ticker: 종목 심볼 (예: TSLA, NVDA, AAPL)
            
        Returns:
            x: 초기 상태 벡터 [trend, momentum, volatility, macro_signal, tech_signal]
            P: 초기 공분산 행렬 (5x5)
        """
        try:
            # 1. 기업별 특성 분석
            company_profile = self._analyze_company_profile(ticker)
            
            # 2. 최근 가격 데이터 수집
            price_data = self._get_recent_price_data(ticker)
            
            # 3. 기술적 지표 계산
            technical_indicators = self._calculate_technical_indicators(price_data)
            
            # 4. 거시경제 상황 반영
            macro_context = self._get_macro_context()
            
            # 5. 초기 상태 벡터 생성
            x = self._create_initial_state_vector(
                ticker, company_profile, technical_indicators, macro_context
            )
            
            # 6. 초기 공분산 행렬 생성
            P = self._create_initial_covariance_matrix(ticker, company_profile)
            
            print(f"[KalmanInitializer] {ticker} 초기화 완료: x={x.tolist()}")
            
            return x, P
            
        except Exception as e:
            print(f"[KalmanInitializer] {ticker} 초기화 실패: {e}")
            # 기본값 반환
            return self._get_default_initialization()
    
    def _analyze_company_profile(self, ticker: str) -> Dict[str, Any]:
        """기업별 특성 분석"""
        profiles = {
            "TSLA": {
                "sector": "technology",
                "volatility": "high",
                "growth": "high",
                "sensitivity": ["interest_rates", "oil_prices", "tech_sentiment"]
            },
            "NVDA": {
                "sector": "technology", 
                "volatility": "high",
                "growth": "very_high",
                "sensitivity": ["ai_sentiment", "chip_demand", "tech_sentiment"]
            },
            "AAPL": {
                "sector": "consumer_goods",
                "volatility": "medium",
                "growth": "medium",
                "sensitivity": ["consumer_spending", "iphone_sales", "tech_sentiment"]
            },
            "MSFT": {
                "sector": "technology",
                "volatility": "medium",
                "growth": "high", 
                "sensitivity": ["cloud_demand", "enterprise_spending", "tech_sentiment"]
            }
        }
        
        return profiles.get(ticker, {
            "sector": "general",
            "volatility": "medium",
            "growth": "medium",
            "sensitivity": ["market_sentiment", "sector_performance"]
        })
    
    def _get_recent_price_data(self, ticker: str) -> pd.DataFrame:
        """최근 가격 데이터 수집"""
        try:
            # 최근 30일 데이터 수집
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            stock = yf.Ticker(ticker)
            data = stock.history(start=start_date, end=end_date)
            
            if data.empty:
                raise ValueError(f"No data available for {ticker}")
            
            return data
            
        except Exception as e:
            print(f"[KalmanInitializer] 가격 데이터 수집 실패: {e}")
            # 더미 데이터 반환
            return self._create_dummy_price_data()
    
    def _calculate_technical_indicators(self, price_data: pd.DataFrame) -> Dict[str, float]:
        """기술적 지표 계산"""
        try:
            close_prices = price_data['Close']
            
            # 1. EMA 기울기 (트렌드)
            ema20 = close_prices.ewm(span=20).mean()
            trend = (ema20.iloc[-1] - ema20.iloc[-5]) / ema20.iloc[-5] * 100
            
            # 2. ROC (모멘텀)
            roc = (close_prices.iloc[-1] - close_prices.iloc[-5]) / close_prices.iloc[-5] * 100
            
            # 3. 변동성 (표준편차)
            volatility = close_prices.pct_change().rolling(5).std().iloc[-1] * 100
            
            # 4. RSI
            delta = close_prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs.iloc[-1]))
            
            return {
                "trend": trend,
                "momentum": roc,
                "volatility": volatility,
                "rsi": rsi
            }
            
        except Exception as e:
            print(f"[KalmanInitializer] 기술적 지표 계산 실패: {e}")
            return {
                "trend": 0.0,
                "momentum": 0.0,
                "volatility": 20.0,
                "rsi": 50.0
            }
    
    def _get_macro_context(self) -> Dict[str, float]:
        """거시경제 상황 (현재는 기본값)"""
        return {
            "interest_rate_environment": 0.0,  # 중립
            "market_sentiment": 0.0,  # 중립
            "sector_performance": 0.0  # 중립
        }
    
    def _create_initial_state_vector(self, ticker: str, company_profile: Dict, 
                                   technical_indicators: Dict, macro_context: Dict) -> NDArray:
        """초기 상태 벡터 생성"""
        
        # 1. 트렌드 신호
        trend = technical_indicators["trend"]
        trend = np.clip(trend, -50, 50)  # -50% ~ +50% 범위 제한
        
        # 2. 모멘텀 신호
        momentum = technical_indicators["momentum"]
        momentum = np.clip(momentum, -30, 30)  # -30% ~ +30% 범위 제한
        
        # 3. 변동성 신호
        volatility = technical_indicators["volatility"]
        volatility = np.clip(volatility, 5, 50)  # 5% ~ 50% 범위 제한
        
        # 4. 거시경제 신호
        macro_signal = macro_context["interest_rate_environment"] + \
                      macro_context["market_sentiment"] + \
                      macro_context["sector_performance"]
        macro_signal = np.clip(macro_signal, -1, 1)
        
        # 5. 기술적 신호 (RSI 기반)
        rsi = technical_indicators["rsi"]
        if rsi < 30:
            tech_signal = 1.0  # 과매도
        elif rsi > 70:
            tech_signal = -1.0  # 과매수
        else:
            tech_signal = (rsi - 50) / 50  # -1 ~ +1 범위로 정규화
        
        # 기업별 특성 조정
        if company_profile["volatility"] == "high":
            volatility *= 1.5  # 고변동성 기업은 변동성 증가
        elif company_profile["volatility"] == "low":
            volatility *= 0.7  # 저변동성 기업은 변동성 감소
        
        if company_profile["growth"] == "very_high":
            trend *= 1.2  # 고성장 기업은 트렌드 강화
            momentum *= 1.2
        
        return np.array([trend, momentum, volatility, macro_signal, tech_signal])
    
    def _create_initial_covariance_matrix(self, ticker: str, company_profile: Dict) -> NDArray:
        """초기 공분산 행렬 생성"""
        
        # 기본 공분산 행렬 (단위행렬 * 0.1)
        P = np.eye(5) * 0.1
        
        # 기업별 특성에 따른 조정
        if company_profile["volatility"] == "high":
            P[2, 2] = 0.2  # 변동성 불확실성 증가
        elif company_profile["volatility"] == "low":
            P[2, 2] = 0.05  # 변동성 불확실성 감소
        
        # 성장성에 따른 조정
        if company_profile["growth"] == "very_high":
            P[0, 0] = 0.15  # 트렌드 불확실성 증가
            P[1, 1] = 0.15  # 모멘텀 불확실성 증가
        elif company_profile["growth"] == "low":
            P[0, 0] = 0.05  # 트렌드 불확실성 감소
            P[1, 1] = 0.05  # 모멘텀 불확실성 감소
        
        return P
    
    def _create_dummy_price_data(self) -> pd.DataFrame:
        """더미 가격 데이터 생성 (에러 시 사용)"""
        dates = pd.date_range(start=datetime.now() - timedelta(days=30), 
                             end=datetime.now(), freq='D')
        data = pd.DataFrame({
            'Open': [100] * len(dates),
            'High': [105] * len(dates),
            'Low': [95] * len(dates),
            'Close': [100] * len(dates),
            'Volume': [1000000] * len(dates)
        }, index=dates)
        return data
    
    def _get_default_initialization(self) -> Tuple[NDArray, NDArray]:
        """기본 초기화값"""
        x = np.array([0.0, 0.0, 20.0, 0.0, 0.0])  # 중립적 초기값
        P = np.eye(5) * 0.1  # 기본 공분산 행렬
        return x, P 