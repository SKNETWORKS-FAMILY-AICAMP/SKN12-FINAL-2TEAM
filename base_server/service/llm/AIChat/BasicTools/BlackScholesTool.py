from __future__ import annotations

import math
import time
from typing import Literal, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, model_validator

from service.llm.AIChat.BaseFinanceTool import BaseFinanceTool

# ───────────────────────── Input / Output Models ───────────────────────── #

class BlackScholesInput(BaseModel):
    mode: Literal["price", "greeks", "iv"] = Field(..., description="계산 모드: price(가격), greeks(그릭스), iv(내재변동성)")
    
    # 기본 파라미터들
    S: float = Field(..., gt=0, description="현재가 (spot price)")
    K: float = Field(..., gt=0, description="행사가 (strike price)")
    T: float = Field(..., gt=0, description="만기까지 남은 시간(년)")
    r: float = Field(0.0, description="무위험이자율 (연, 기본값: 0.0)")
    sigma: Optional[float] = Field(None, gt=0, description="변동성 (연, price/greeks 모드에서 필요)")
    option_type: Literal["call", "put"] = Field("call", description="옵션 타입: call(콜), put(풋)")
    q: float = Field(0.0, description="배당수익률 (연, 기본값: 0.0)")
    
    # IV 계산시에만 필요한 파라미터
    market_price: Optional[float] = Field(None, gt=0, description="시장가 (IV 계산시 필요)")
    init_sigma: Optional[float] = Field(0.2, gt=0, le=5.0, description="IV 계산 초기 추정값 (기본값: 0.2)")

    @model_validator(mode="after")
    def _conditional_requirements(self):
        """모드별 필수 파라미터 조건부 검증"""
        if self.mode in ("price", "greeks"):
            if self.sigma is None:
                raise ValueError("mode=price/greeks 에서는 sigma가 필요합니다")
        elif self.mode == "iv":
            if self.market_price is None:
                raise ValueError("mode=iv 에서는 market_price가 필요합니다")
            # iv 모드에서는 sigma 입력이 있더라도 무시할 수 있음(선택)
        return self

class BlackScholesOutput(BaseModel):
    mode: str = Field(..., description="계산 모드")
    success: bool = Field(..., description="계산 성공 여부")
    result: Optional[Union[float, Dict[str, float]]] = Field(None, description="계산 결과")
    error: Optional[str] = Field(None, description="에러 메시지")
    calculation_time: float = Field(..., description="계산 소요 시간(초)")
    input_params: Dict[str, Any] = Field(..., description="입력 파라미터")

# ───────────────────────── Utility Functions ───────────────────────── #

def _norm_cdf(x: float) -> float:
    """표준정규 CDF (scipy 없이 erf로 계산)"""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def _norm_pdf(x: float) -> float:
    """표준정규 PDF"""
    return (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-0.5 * x * x)

# ───────────────────────── Main Tool Class ───────────────────────── #

class BlackScholesTool(BaseFinanceTool):
    """
    블랙-숄즈 모델을 사용한 유럽형 옵션 가격/그릭스/내재변동성 계산기
    
    주요 기능:
    - 옵션 이론가 계산 (price)
    - 그릭스 계산 (delta, gamma, theta, vega, rho)
    - 내재변동성 역산 (implied volatility)
    
    사용 예시:
    - 콜 옵션 가격: mode="price", option_type="call"
    - 풋 옵션 그릭스: mode="greeks", option_type="put"  
    - 내재변동성: mode="iv", market_price=5.0
    """
    
    def __init__(self, ai_chat_service=None):
        """
        초기화 (ai_chat_service는 선택적 - 외부 API 불필요)
        
        Args:
            ai_chat_service: AIChatService 인스턴스 (선택적)
        """
        super().__init__()
        self.ai_chat_service = ai_chat_service
        
    def get_data(self, **params) -> BlackScholesOutput:
        """
        BaseFinanceTool 표준 인터페이스
        
        Args:
            **params: BlackScholesInput 모델의 파라미터들
            
        Returns:
            BlackScholesOutput: 계산 결과 또는 에러 정보
        """
        start_time = time.time()
        
        try:
            # 입력 검증
            input_data = BlackScholesInput(**params)
            
            # 모드별 계산 실행
            if input_data.mode == "price":
                result = self.price(
                    S=input_data.S, K=input_data.K, T=input_data.T,
                    r=input_data.r, sigma=input_data.sigma,
                    option_type=input_data.option_type, q=input_data.q
                )
                result_data = {"price": result}
                
            elif input_data.mode == "greeks":
                result = self.greeks(
                    S=input_data.S, K=input_data.K, T=input_data.T,
                    r=input_data.r, sigma=input_data.sigma,
                    option_type=input_data.option_type, q=input_data.q
                )
                result_data = result
                
            elif input_data.mode == "iv":
                if input_data.market_price is None:
                    raise ValueError("IV 계산시 market_price가 필요합니다")
                
                result = self.implied_vol(
                    market_price=input_data.market_price,
                    S=input_data.S, K=input_data.K, T=input_data.T,
                    r=input_data.r, option_type=input_data.option_type,
                    q=input_data.q, init_sigma=input_data.init_sigma
                )
                
                if result is None:
                    raise ValueError("내재변동성 계산에 실패했습니다. 입력값을 확인해주세요")
                    
                result_data = {"implied_vol": result}
            else:
                raise ValueError(f"지원하지 않는 모드: {input_data.mode}")
            
            calculation_time = time.time() - start_time
            
            return BlackScholesOutput(
                mode=input_data.mode,
                success=True,
                result=result_data,
                error=None,
                calculation_time=calculation_time,
                input_params=input_data.model_dump()
            )
            
        except Exception as e:
            calculation_time = time.time() - start_time
            return BlackScholesOutput(
                mode=params.get("mode", "unknown"),
                success=False,
                result=None,
                error=str(e),
                calculation_time=calculation_time,
                input_params=params
            )

    # ───────────────────────── Core Calculation Methods ───────────────────────── #
    
    def price(
        self,
        S: float,        # 현재가 (spot)
        K: float,        # 행사가
        T: float,        # 만기까지 남은 시간(년)
        r: float,        # 무위험이자율 (연)
        sigma: float,    # 변동성 (연)
        option_type: Literal["call", "put"] = "call",
        q: float = 0.0   # 배당수익률(연, 있으면)
    ) -> float:
        """
        유럽형 옵션 이론가 계산 (Black-Scholes-Merton 모델)
        
        Args:
            S: 현재가
            K: 행사가  
            T: 만기까지 시간(년) - 예: 30일이면 T=30/365
            r: 무위험이자율 (연)
            sigma: 변동성 (연)
            option_type: 옵션 타입 ("call" 또는 "put")
            q: 배당수익률 (연, 기본값: 0.0)
            
        Returns:
            float: 옵션 이론가
            
        Raises:
            ValueError: 잘못된 입력값
        """
        if S <= 0 or K <= 0 or T <= 0 or sigma <= 0:
            raise ValueError("S, K, T, sigma는 양수여야 합니다")
        
        if option_type not in ["call", "put"]:
            raise ValueError("option_type은 'call' 또는 'put'이어야 합니다")

        # d1, d2 계산
        d1 = (math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)

        if option_type == "call":
            return S * math.exp(-q * T) * _norm_cdf(d1) - K * math.exp(-r * T) * _norm_cdf(d2)
        else:  # put
            return K * math.exp(-r * T) * _norm_cdf(-d2) - S * math.exp(-q * T) * _norm_cdf(-d1)

    def greeks(
        self,
        S: float, K: float, T: float, r: float, sigma: float,
        option_type: Literal["call", "put"] = "call",
        q: float = 0.0
    ) -> Dict[str, float]:
        """
        옵션 그릭스 계산 (Δ, Γ, Θ, ρ, Vega)
        
        Args:
            S: 현재가
            K: 행사가
            T: 만기까지 시간(년)
            r: 무위험이자율 (연)
            sigma: 변동성 (연)
            option_type: 옵션 타입
            q: 배당수익률 (연)
            
        Returns:
            Dict[str, float]: 그릭스 값들
                - delta: 델타 (가격 변화에 대한 민감도)
                - gamma: 감마 (델타 변화에 대한 민감도)
                - vega: 베가 (변동성 변화에 대한 민감도)
                - theta: 세타 (시간 경과에 대한 민감도, 연 단위)
                - rho: 로 (이자율 변화에 대한 민감도)
        """
        if S <= 0 or K <= 0 or T <= 0 or sigma <= 0:
            raise ValueError("S, K, T, sigma는 양수여야 합니다")
        
        if option_type not in ["call", "put"]:
            raise ValueError("option_type은 'call' 또는 'put'이어야 합니다")

        sqrtT = math.sqrt(T)
        d1 = (math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / (sigma * sqrtT)
        d2 = d1 - sigma * sqrtT

        pdf_d1 = _norm_pdf(d1)
        cdf_d1 = _norm_cdf(d1)
        cdf_m_d1 = _norm_cdf(-d1)
        cdf_d2 = _norm_cdf(d2)
        cdf_m_d2 = _norm_cdf(-d2)

        disc_r = math.exp(-r * T)
        disc_q = math.exp(-q * T)

        # Vega (per 1.0 of sigma, not per 1%)
        vega = S * disc_q * pdf_d1 * sqrtT

        # Delta
        if option_type == "call":
            delta = disc_q * cdf_d1
            theta = (- (S * disc_q * pdf_d1 * sigma) / (2 * sqrtT)
                     - r * K * disc_r * cdf_d2
                     + q * S * disc_q * cdf_d1)
            rho = K * T * disc_r * cdf_d2
        else:  # put
            delta = disc_q * (cdf_d1 - 1.0)
            theta = (- (S * disc_q * pdf_d1 * sigma) / (2 * sqrtT)
                     + r * K * disc_r * cdf_m_d2
                     - q * S * disc_q * cdf_m_d1)
            rho = -K * T * disc_r * cdf_m_d2

        gamma = (disc_q * pdf_d1) / (S * sigma * sqrtT)

        # 주의: theta는 "연 단위" 절댓값. 일 단위가 필요하면 /365 등으로 변환
        return {
            "delta": delta,
            "gamma": gamma,
            "vega": vega,
            "theta": theta,
            "rho": rho
        }

    def implied_vol(
        self,
        market_price: float,
        S: float, K: float, T: float, r: float,
        option_type: Literal["call", "put"] = "call",
        q: float = 0.0,
        init_sigma: float = 0.2,
        tol: float = 1e-8,
        max_iter: int = 100
    ) -> Optional[float]:
        """
        시장가로부터 내재변동성 추정 (Newton-Raphson 방법)
        
        Args:
            market_price: 시장에서 관찰된 옵션 가격
            S: 현재가
            K: 행사가
            T: 만기까지 시간(년)
            r: 무위험이자율 (연)
            option_type: 옵션 타입
            q: 배당수익률 (연)
            init_sigma: 초기 변동성 추정값
            tol: 수렴 허용오차
            max_iter: 최대 반복 횟수
            
        Returns:
            Optional[float]: 내재변동성 (실패시 None)
        """
        if market_price <= 0 or S <= 0 or K <= 0 or T <= 0:
            return None

        # 합리적 가격 범위 검증 (이론적 하한/상한)
        if option_type == "call":
            intrinsic = max(0.0, S * math.exp(-q * T) - K * math.exp(-r * T))
        else:  # put
            intrinsic = max(0.0, K * math.exp(-r * T) - S * math.exp(-q * T))
        
        # 시장가가 이론적 하한보다 낮으면 계산 불가
        if market_price < intrinsic:
            return None

        sigma = max(1e-6, init_sigma)
        for _ in range(max_iter):
            price = self.price(S, K, T, r, sigma, option_type, q)
            diff = price - market_price
            if abs(diff) < tol:
                return float(sigma)

            # Vega가 너무 작으면 수렴 어려움
            vega = self.greeks(S, K, T, r, sigma, option_type, q)["vega"]
            if vega < 1e-12:
                break

            sigma -= diff / vega
            # 수치 안정화
            if sigma <= 0:
                sigma = 1e-6
            if sigma > 5.0:  # 변동성 500% cap
                sigma = 5.0
        return None

    # ───────────────────────── Utility Methods ───────────────────────── #
    
    def validate_inputs(self, S: float, K: float, T: float, sigma: float) -> bool:
        """입력값 유효성 검사"""
        return S > 0 and K > 0 and T > 0 and sigma > 0
    
    def get_time_to_expiry_days(self, days: int) -> float:
        """일 단위를 년 단위로 변환"""
        return days / 365.0
    
    def get_time_to_expiry_months(self, months: int) -> float:
        """월 단위를 년 단위로 변환"""
        return months / 12.0

    def get_option_recommendation(
        self,
        S: float,           # 현재가
        K: float,           # 행사가
        T: float,           # 만기(년)
        r: float,           # 무위험이자율
        sigma: float,       # 변동성
        market_price: float, # 시장가
        option_type: str,   # "call" or "put"
        q: float = 0.0,    # 배당수익률
        threshold: float = 0.05  # 5% 임계값
    ) -> Dict[str, Any]:
        """
        이론가 계산 + 시장가 비교해서 BUY/SELL/HOLD 신호 생성
        
        Args:
            S: 현재가
            K: 행사가
            T: 만기까지 시간(년)
            r: 무위험이자율 (연)
            sigma: 변동성 (연)
            market_price: 시장가
            option_type: 옵션 타입 ("call" 또는 "put")
            q: 배당수익률 (연, 기본값: 0.0)
            threshold: 임계값 (기본값: 0.05 = 5%)
            
        Returns:
            Dict[str, Any]: 옵션 추천 정보
                - strike: 행사가
                - theoretical_price: 이론가
                - market_price: 시장가
                - signal: "BUY", "SELL", "HOLD", "ERROR"
                - reason: 신호 이유
                - ratio: 시장가/이론가 비율
        """
        try:
            # 1) 이론가 계산
            theoretical_price = self.price(S, K, T, r, sigma, option_type, q)
            
            # 2) 시장가와 비교
            if theoretical_price <= 0:
                signal = "ERROR"
                reason = "이론가 0 이하 (계산 확인 필요)"
                ratio = 0.0
            else:
                ratio = market_price / theoretical_price
                
                if ratio < (1 - threshold):
                    discount = (1 - ratio) * 100
                    signal = "BUY"
                    reason = f"시장가가 이론가 대비 {discount:.1f}% 싸요"
                elif ratio > (1 + threshold):
                    premium = (ratio - 1) * 100
                    signal = "SELL"
                    reason = f"시장가가 이론가 대비 {premium:.1f}% 비싸요"
                else:
                    signal = "HOLD"
                    reason = "시장가 ≈ 이론가, 관망"
            
            return {
                "strike": K,
                "theoretical_price": theoretical_price,
                "market_price": market_price,
                "signal": signal,
                "reason": reason,
                "ratio": ratio
            }
            
        except Exception as e:
            return {
                "strike": K,
                "theoretical_price": 0.0,
                "market_price": market_price,
                "signal": "ERROR",
                "reason": f"계산 오류: {str(e)}",
                "ratio": 0.0
            }

# ───────────────────────── Example Usage ───────────────────────── #

if __name__ == "__main__":
    # 테스트 예시
    tool = BlackScholesTool()
    
    # 콜 옵션 가격 계산
    result = tool.get_data(
        mode="price",
        S=100.0, K=100.0, T=30/365, r=0.05, sigma=0.3,
        option_type="call", q=0.0
    )
    print(f"콜 옵션 가격: {result}")
    
    # 풋 옵션 그릭스 계산
    result = tool.get_data(
        mode="greeks", 
        S=100.0, K=100.0, T=30/365, r=0.05, sigma=0.3,
        option_type="put", q=0.0
    )
    print(f"풋 옵션 그릭스: {result}") 