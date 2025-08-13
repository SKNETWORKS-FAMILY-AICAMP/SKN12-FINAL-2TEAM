from __future__ import annotations

import time
import json
import math
from datetime import datetime
from typing import Dict, Any, List, Optional
import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, Field

# 🆕 Manager Core 사용
from service.llm.AIChat.manager.KalmanRegimeFilterCore import KalmanRegimeFilterCore
from service.llm.AIChat.SessionAwareTool import SessionAwareTool
from service.llm.AIChat.manager.KalmanStateManager import KalmanStateManager

__all__ = ["KalmanRegimeFilterTool"]

# ───────────────────────── Input / Output ───────────────────────── #

class KalmanRegimeFilterInput(BaseModel):
    tickers: List[str] = Field(..., description="분석할 종목 리스트")
    start_date: str    = Field(..., description="데이터 시작일(YYYY-MM-DD)")
    end_date: str      = Field(..., description="데이터 종료일(YYYY-MM-DD)")

    # 실전 운용 파라미터
    account_value: float = Field(... ,description="계좌 가치")
    account_ccy: str = Field("KRW", description="계좌 통화(예시: KRW, USD)")
    exchange_rate: str = Field("KRW", description="화폐 단위(예시: KRW, USD)")
    risk_pct: float      = Field(0.02, description="한 트레이드당 위험 비율(0~1)")
    max_leverage: float  = Field(10.0, description="허용 최대 레버리지")

    # 🆕 항상 예측에 쓰일 기본값
    horizon_days: int    = Field(3,    ge=1, le=30, description="예측 기간(일)")
    ci_level: float      = Field(0.8,  gt=0, lt=1,  description="신뢰구간 신뢰수준(예: 0.8, 0.9, 0.95)")
    drift_scale: float   = Field(0.0015, description="combined_signal → 일간 기대수익률 변환 계수")

    # 🆕 옵션 시장가 입력 (선택적)
    option_market_prices: Optional[Dict[str, Dict[str, float]]] = Field(
        None, 
        description="옵션 시장가: {'306.76': {'call': 35.0, 'put': 0.8}, '340.84': {'call': 9.5, 'put': 9.4}}"
    )
    
    # 🆕 옵션 시그널 임계값
    option_signal_threshold: float = Field(
        0.05, 
        description="이론가 대비 시장가 편차 임계값 (5% = 0.05)"
    )


class KalmanRegimeFilterActionOutput(BaseModel):
    summary: str
    recommendations: Dict[str, Any]
    start_time: str
    end_time: str

# ─────────────────────────── Kalman Filter Core ───────────────────────── #

# ─────────────────────────── Tool Wrapper ───────────────────────── #

class KalmanRegimeFilterTool(SessionAwareTool):
    """
    매 호출 시:
      1) 거시·기술·가격 데이터 수집 (raw 값)
      2) 피처 조합 후 정규화
      3) 칼만 필터 업데이트 (Redis + SQL 하이브리드 상태 관리)
      4) 트레이딩 신호·리스크·경고 생성
    """
    
    def __init__(self, ai_chat_service):
        # SessionAwareTool 초기화
        super().__init__()
        
        from service.llm.AIChat_service import AIChatService
        if not isinstance(ai_chat_service, AIChatService):
            raise TypeError("Expected AIChatService instance")
        self.ai_chat_service = ai_chat_service
        self.max_latency = 5.0  # seconds
        
        # 🆕 Redis + SQL 하이브리드 상태 관리
        try:
            from service.service_container import ServiceContainer
            
            # ServiceContainer에서 기존 서비스 가져오기
            db_service = ServiceContainer.get_database_service()
            redis_pool = ServiceContainer.get_cache_service()._client_pool
            
            self.state_manager = KalmanStateManager(redis_pool, db_service)
            print("[KalmanRegimeFilterTool] Redis + SQL 하이브리드 상태 관리 초기화 완료")
        except Exception as e:
            print(f"[KalmanRegimeFilterTool] 상태 관리 초기화 실패: {e}")
            print("[KalmanRegimeFilterTool] 메모리 기반 fallback 모드로 동작")
            self.state_manager = None

    def require_session(self) -> bool:
        """세션은 선택사항 (fallback 지원)"""
        return False

    # 🆕 블랙-숄즈 옵션 뷰 어댑터 메서드들
    
    def _simple_action_from_ratio(self, ratio: float, threshold: float) -> str:
        """
        편차율을 기반으로 매수/매도/관망 액션 결정
        
        Args:
            ratio: (시장가 - 이론가) / 이론가
            threshold: 임계값 (예: 0.05 = 5%)
            
        Returns:
            "매수", "매도", "관망" 중 하나
        """
        if ratio <= -threshold:
            return "매수"    # 이론가 대비 싸다 → 매수
        elif ratio >= +threshold:
            return "매도"    # 이론가 대비 비싸다 → 매도
        else:
            return "관망"    # 적정가 범위
    
    def _analyze_option_signals(
        self, 
        bs_inputs: Dict[str, Any], 
        market_prices: Dict[str, Dict[str, float]], 
        threshold: float, 
        bias: str
    ) -> List[Dict[str, Any]]:
        """
        옵션 이론가 vs 시장가 비교하여 매수/매도/관망 시그널 생성
        
        Args:
            bs_inputs: 블랙-숄즈 입력 파라미터
            market_prices: 시장가 딕셔너리
            threshold: 편차 임계값
            bias: 칼만 필터 방향성 (Long/Short/Neutral)
            
        Returns:
            정렬된 옵션 신호 리스트 (bias_ok 우선 → 절대편차 큰 순)
        """
        try:
            from service.llm.AIChat.BasicTools.BlackScholesTool import BlackScholesTool
            bs = BlackScholesTool()
            
            S, T, r, q, sigma = bs_inputs["S"], bs_inputs["T"], bs_inputs["r"], bs_inputs["q"], bs_inputs["sigma"]
            signals = []
            
            print(f"[DEBUG] _analyze_option_signals 시작:")
            print(f"  - S: {S}, T: {T}, r: {r}, q: {q}, sigma: {sigma}")
            print(f"  - threshold: {threshold}, bias: {bias}")
            print(f"  - market_prices: {market_prices}")
            
            for strike_str, prices in market_prices.items():
                try:
                    K = float(strike_str)
                    print(f"[DEBUG] Strike {K} 분석 중...")
                    
                    # 이론가 계산
                    theo_call = bs.price(S=S, K=K, T=T, r=r, sigma=sigma, option_type="call", q=q)
                    theo_put = bs.price(S=S, K=K, T=T, r=r, sigma=sigma, option_type="put", q=q)
                    
                    print(f"[DEBUG]  - 이론가: CALL=${theo_call:.4f}, PUT=${theo_put:.4f}")
                    
                    # 시장가
                    mcall = prices.get("call")
                    mput = prices.get("put")
                    
                    print(f"[DEBUG]  - 시장가: CALL=${mcall}, PUT=${mput}")
                    
                    # 콜 옵션 분석
                    if mcall and theo_call > 1e-8:
                        ratio = (mcall - theo_call) / theo_call
                        action = self._simple_action_from_ratio(ratio, threshold)
                        
                        # 칼만 방향성과 정합성 체크
                        bias_ok = (
                            (bias == "Long" and action == "매수") or 
                            (bias == "Short" and action == "매도") or 
                            (bias == "Neutral")
                        )
                        
                        signals.append({
                            "option": f"CALL {K:g}",
                            "action": action,
                            "why": f"시장가 ${mcall:.2f} vs 이론가 ${theo_call:.2f} ({ratio*100:+.1f}%)",
                            "bias_ok": bias_ok,
                            "ratio": ratio,
                            "strike": K
                        })
                        
                        print(f"[DEBUG]  - 콜 신호: {action}, ratio: {ratio:.4f}, bias_ok: {bias_ok}")
                    
                    # 풋 옵션 분석
                    if mput and theo_put > 1e-8:
                        ratio = (mput - theo_put) / theo_put
                        action = self._simple_action_from_ratio(ratio, threshold)
                        
                        # 칼만 방향성과 정합성 체크 (풋은 콜과 반대)
                        bias_ok = (
                            (bias == "Short" and action == "매수") or 
                            (bias == "Long" and action == "매도") or 
                            (bias == "Neutral")
                        )
                        
                        signals.append({
                            "option": f"PUT {K:g}",
                            "action": action,
                            "why": f"시장가 ${mput:.2f} vs 이론가 ${theo_put:.2f} ({ratio*100:+.1f}%)",
                            "bias_ok": bias_ok,
                            "ratio": ratio,
                            "strike": K
                        })
                        
                        print(f"[DEBUG]  - 풋 신호: {action}, ratio: {ratio:.4f}, bias_ok: {bias_ok}")
                        
                except Exception as e:
                    print(f"[DEBUG] Strike {strike_str} 분석 실패: {e}")
                    signals.append({
                        "option": strike_str, 
                        "action": "관망", 
                        "why": f"계산오류: {e}", 
                        "bias_ok": False,
                        "ratio": 0.0,
                        "strike": float(strike_str) if strike_str.replace('.', '').isdigit() else 0.0
                    })
            
            # 우선순위 정렬: bias_ok 우선 → 절대편차 큰 순
            def sort_key(s):
                return (not s["bias_ok"], -abs(s["ratio"]))
            
            signals.sort(key=sort_key)
            
            print(f"[DEBUG] _analyze_option_signals 완료: {len(signals)}개 신호")
            for i, s in enumerate(signals[:3]):  # 상위 3개만 로그
                print(f"[DEBUG]  - {i+1}: {s['action']} {s['option']} - {s['why']}")
            
            return signals
            
        except Exception as e:
            print(f"[DEBUG] _analyze_option_signals 전체 실패: {e}")
            import traceback
            print(f"[DEBUG] 에러 상세: {traceback.format_exc()}")
            return []
    
    def _generate_basic_option_signals(
        self, 
        bs_inputs: Dict[str, Any], 
        signal: str, 
        preferred: str
    ) -> List[Dict[str, Any]]:
        """
        시장가 데이터가 없을 때 기본적인 옵션 전략 신호 생성
        
        Args:
            bs_inputs: 블랙-숄즈 입력 파라미터
            signal: 칼만 필터 신호 (Long/Short/Neutral)
            preferred: 선호 옵션 타입 (call/put/neutral)
            
        Returns:
            기본 옵션 전략 액션 리스트
        """
        try:
            S = bs_inputs["S"]
            sigma = bs_inputs["sigma"]
            T = bs_inputs["T"]
            
            actions = []
            
            print(f"[DEBUG] _generate_basic_option_signals 시작:")
            print(f"  - S: {S}, sigma: {sigma}, T: {T}")
            print(f"  - signal: {signal}, preferred: {preferred}")
            
            # 1. 기본 전략: 현재가 기준 ITM/ATM/OTM 옵션 추천
            if signal.lower() == "long":
                # Long 신호일 때 콜 옵션 전략
                if preferred == "call":
                    # ITM 콜 (현재가보다 낮은 행사가)
                    itm_strike = round(S * 0.95, 2)  # 현재가의 95%
                    actions.append({
                        "label": "매수",
                        "why": f"ITM 콜 옵션 전략 - 강한 상승 모멘텀 활용",
                        "what": f"콜 매수(행사가 ${itm_strike}) - 높은 델타로 상승 수익 극대화",
                        "confidence": "높음"
                    })
                    
                    # ATM 콜 (현재가 근처)
                    atm_strike = round(S, 2)
                    actions.append({
                        "label": "매수",
                        "why": f"ATM 콜 옵션 전략 - 균형잡힌 리스크/수익",
                        "what": f"콜 매수(행사가 ${atm_strike}) - 중간 델타로 안정적 상승 수익",
                        "confidence": "보통"
                    })
                    
                    # OTM 콜 (현재가보다 높은 행사가)
                    otm_strike = round(S * 1.05, 2)  # 현재가의 105%
                    actions.append({
                        "label": "매수",
                        "why": f"OTM 콜 옵션 전략 - 높은 수익률 추구",
                        "what": f"콜 매수(행사가 ${otm_strike}) - 낮은 델타로 높은 수익률",
                        "confidence": "낮음"
                    })
                    
            elif signal.lower() == "short":
                # Short 신호일 때 풋 옵션 전략
                if preferred == "put":
                    # ITM 풋 (현재가보다 높은 행사가)
                    itm_strike = round(S * 1.05, 2)  # 현재가의 105%
                    actions.append({
                        "label": "매수",
                        "why": f"ITM 풋 옵션 전략 - 강한 하락 모멘텀 활용",
                        "what": f"풋 매수(행사가 ${itm_strike}) - 높은 델타로 하락 수익 극대화",
                        "confidence": "높음"
                    })
                    
                    # ATM 풋 (현재가 근처)
                    atm_strike = round(S, 2)
                    actions.append({
                        "label": "매수",
                        "why": f"ATM 풋 옵션 전략 - 균형잡힌 리스크/수익",
                        "what": f"풋 매수(행사가 ${atm_strike}) - 중간 델타로 안정적 하락 수익",
                        "confidence": "보통"
                    })
                    
                    # OTM 풋 (현재가보다 낮은 행사가)
                    otm_strike = round(S * 0.95, 2)  # 현재가의 95%
                    actions.append({
                        "label": "매수",
                        "why": f"OTM 풋 옵션 전략 - 높은 수익률 추구",
                        "what": f"풋 매수(행사가 ${otm_strike}) - 낮은 델타로 높은 수익률",
                        "confidence": "낮음"
                    })
            
            # 2. 변동성 기반 전략 추가
            if sigma > 0.4:  # 높은 변동성
                actions.append({
                    "label": "관망",
                    "why": f"높은 변동성({sigma*100:.1f}%) - 스트래들/스트랭글 전략 고려",
                    "what": "변동성 확대 시점까지 대기 후 방향성 전략 실행",
                    "confidence": "보통"
                })
            elif sigma < 0.2:  # 낮은 변동성
                actions.append({
                    "label": "매수",
                    "why": f"낮은 변동성({sigma*100:.1f}%) - 방향성 전략 유리",
                    "what": "방향성 옵션 매수로 변동성 확대 수익 기대",
                    "confidence": "높음"
                })
            
            # 3. 시간 가치 고려
            if T < 0.02:  # 1주일 이내 만기
                actions.append({
                    "label": "매도",
                    "why": f"단기 만기({T*365:.0f}일) - 시간가치 급감 주의",
                    "what": "기존 옵션 포지션 정리 또는 단기 전략 실행",
                    "confidence": "보통"
                })
            
            print(f"[DEBUG] _generate_basic_option_signals 완료: {len(actions)}개 액션")
            return actions
            
        except Exception as e:
            print(f"[DEBUG] _generate_basic_option_signals 실패: {e}")
            import traceback
            print(f"[DEBUG] 에러 상세: {traceback.format_exc()}")
            return []

    def _build_bs_inputs(
        self,
        entry_price: float,
        atr_pct: float,
        *,
        rate: float = 0.02,        # r 기본 2%
        div_yield: float = 0.0,    # q 기본 0
        days_to_expiry: int = 30   # 기본 30D
    ) -> Dict[str, Any]:
        """
        칼만 필터 데이터를 블랙-숄즈 입력으로 변환
        
        Args:
            entry_price: 현재가 (S)
            atr_pct: ATR 백분율 (일간 변동성)
            rate: 무위험이자율 (연)
            div_yield: 배당수익률 (연)
            days_to_expiry: 만기까지 일수
            
        Returns:
            블랙-숄즈 계산에 필요한 입력 딕셔너리
        """
        print(f"[DEBUG] _build_bs_inputs 시작:")
        print(f"  - entry_price: {entry_price}")
        print(f"  - atr_pct: {atr_pct}")
        print(f"  - rate: {rate}")
        print(f"  - div_yield: {div_yield}")
        print(f"  - days_to_expiry: {days_to_expiry}")
        
        # 1) 변동성: 일간 → 연환산 (안전 가드 포함)
        sigma_daily = float(np.clip(atr_pct, 0.005, 0.15))
        sigma_annual = float(np.clip(sigma_daily * math.sqrt(252.0), 0.05, 1.50))
        
        print(f"[DEBUG] 변동성 계산:")
        print(f"  - 원본 atr_pct: {atr_pct}")
        print(f"  - 클리핑된 sigma_daily: {sigma_daily}")
        print(f"  - sqrt(252): {math.sqrt(252.0)}")
        print(f"  - sigma_annual (클리핑 전): {sigma_daily * math.sqrt(252.0)}")
        print(f"  - 최종 sigma_annual: {sigma_annual}")

        # 2) 만기(연) - 최소 1일 보장
        T = max(days_to_expiry, 1) / 365.0
        print(f"[DEBUG] 만기 계산:")
        print(f"  - days_to_expiry: {days_to_expiry}")
        print(f"  - max(days_to_expiry, 1): {max(days_to_expiry, 1)}")
        print(f"  - T (연): {T}")

        # 3) 행사가 그리드 (기본 ATM ±5%, ±10%)
        multipliers = [0.9, 0.95, 1.0, 1.05, 1.1]
        strikes = [entry_price * m for m in multipliers]
        strikes = [float(round(k, 4)) for k in strikes]
        
        print(f"[DEBUG] 행사가 그리드 생성:")
        print(f"  - multipliers: {multipliers}")
        print(f"  - 원본 strikes: {[entry_price * m for m in multipliers]}")
        print(f"  - 최종 strikes: {strikes}")

        result = {
            "S": float(entry_price),
            "T": float(T),
            "r": float(rate),
            "q": float(div_yield),
            "sigma": float(sigma_annual),
            "strikes": strikes,
        }
        
        print(f"[DEBUG] _build_bs_inputs 결과:")
        print(f"  - S: {result['S']}")
        print(f"  - T: {result['T']}")
        print(f"  - r: {result['r']}")
        print(f"  - q: {result['q']}")
        print(f"  - sigma: {result['sigma']}")
        print(f"  - strikes: {result['strikes']}")
        
        return result

    def _attach_option_view(
        self, 
        rec: Dict[str, Any], 
        bs_inputs: Dict[str, Any], 
        signal: str, 
        market_prices: Optional[Dict[str, Dict[str, float]]] = None, 
        threshold: float = 0.05
    ):
        """
        블랙-숄즈 계산 실행 및 결과를 recommendations에 추가
        
        Args:
            rec: recommendations 딕셔너리
            bs_inputs: 블랙-숄즈 입력 파라미터
            signal: 트레이딩 신호 (Long/Short/Neutral)
            market_prices: 옵션 시장가 (선택적)
            threshold: 편차 임계값 (기본 5%)
        """
        print(f"[DEBUG] _attach_option_view 시작:")
        print(f"  - signal: {signal}")
        print(f"  - bs_inputs: {bs_inputs}")
        
        try:
            print(f"[DEBUG] BlackScholesTool import 시도...")
            from service.llm.AIChat.BasicTools.BlackScholesTool import BlackScholesTool
            print(f"[DEBUG] BlackScholesTool import 성공!")
            
            # BlackScholesTool 인스턴스 생성
            print(f"[DEBUG] BlackScholesTool 인스턴스 생성...")
            bs = BlackScholesTool()
            print(f"[DEBUG] BlackScholesTool 인스턴스 생성 완료: {type(bs)}")
            
            S, T, r, q, sigma = bs_inputs["S"], bs_inputs["T"], bs_inputs["r"], bs_inputs["q"], bs_inputs["sigma"]
            print(f"[DEBUG] 블랙-숄즈 파라미터:")
            print(f"  - S: {S}")
            print(f"  - T: {T}")
            print(f"  - r: {r}")
            print(f"  - q: {q}")
            print(f"  - sigma: {sigma}")
            
            table = []
            print(f"[DEBUG] strikes 개수: {len(bs_inputs['strikes'])}")

            # 각 strike에 대해 콜/풋 가격과 그릭스 계산
            for i, K in enumerate(bs_inputs["strikes"]):
                print(f"[DEBUG] Strike {i+1}/{len(bs_inputs['strikes'])} 계산 중: K={K}")
                row = {"K": round(K, 4)}
                
                # 콜/풋 가격 계산
                try:
                    print(f"[DEBUG]  - 콜 옵션 가격 계산...")
                    call_price = bs.price(S=S, K=K, T=T, r=r, sigma=sigma, option_type="call", q=q)
                    print(f"[DEBUG]  - 콜 가격: {call_price}")
                    
                    print(f"[DEBUG]  - 풋 옵션 가격 계산...")
                    put_price = bs.price(S=S, K=K, T=T, r=r, sigma=sigma, option_type="put", q=q)
                    print(f"[DEBUG]  - 풋 가격: {put_price}")
                    
                    print(f"[DEBUG]  - 콜 그릭스 계산...")
                    greeks_call = bs.greeks(S=S, K=K, T=T, r=r, sigma=sigma, option_type="call", q=q)
                    print(f"[DEBUG]  - 그릭스: {greeks_call}")
                    
                    row.update({
                        "call": round(call_price, 4),
                        "put": round(put_price, 4),
                        "delta": round(greeks_call["delta"], 6),
                        "gamma": round(greeks_call["gamma"], 6),
                        "vega": round(greeks_call["vega"], 6),
                        "theta": round(greeks_call["theta"], 6),
                        "rho": round(greeks_call["rho"], 6),
                    })
                    print(f"[DEBUG]  - 행 추가 완료: {row}")
                    
                except Exception as e:
                    print(f"[DEBUG]  - Strike {K} 계산 실패: {e}")
                    # 계산 실패시 에러 정보 기록
                    row.update({
                        "call": "ERROR",
                        "put": "ERROR",
                        "delta": "ERROR",
                        "gamma": "ERROR",
                        "vega": "ERROR",
                        "theta": "ERROR",
                        "rho": "ERROR",
                        "error": str(e)
                    })
                
                table.append(row)

            print(f"[DEBUG] 테이블 생성 완료: {len(table)}개 행")
            print(f"[DEBUG] 테이블 내용: {table}")

            # 신호 방향에 따라 선호 옵션 타입 결정
            print(f"[DEBUG] 선호 옵션 타입 결정...")
            if signal.lower() == "long":
                preferred = "call"
            elif signal.lower() == "short":
                preferred = "put"
            else:
                preferred = "neutral"
            print(f"[DEBUG] 선호 옵션 타입: {preferred}")

            # recommendations에 옵션 뷰 추가
            print(f"[DEBUG] rec['options'] 설정...")
            rec["options"] = {
                "spot": round(S, 4),
                "r": r,
                "q": q,
                "T_years": round(T, 6),
                "sigma_annual": round(sigma, 6),
                "view": "call/put grid by strikes",
                "preferred": preferred,
                "table": table
            }
            
            print(f"[DEBUG] rec['options'] 설정 완료:")
            print(f"  - spot: {rec['options']['spot']}")
            print(f"  - sigma_annual: {rec['options']['sigma_annual']}")
            print(f"  - preferred: {rec['options']['preferred']}")
            print(f"  - table 행 수: {len(rec['options']['table'])}")
            
            # 🆕 시장가 비교 신호 분석 및 액션 요약 생성
            if market_prices:
                print(f"[DEBUG] 시장가 비교 신호 분석 시작...")
                raw_signals = self._analyze_option_signals(bs_inputs, market_prices, threshold, signal)
                
                if raw_signals:
                    # 상세 옵션 신호
                    rec["options"]["trading_signals"] = [
                        f"{s['action'].upper()} {s['option']}: {s['why']}" for s in raw_signals[:6]
                    ]
                    rec["options"]["signal_analysis"] = f"이론가 대비 {int(threshold*100)}% 편차 기준"
                    
                    print(f"[DEBUG] 옵션 신호 생성 완료: {len(raw_signals)}개")
                    
                    # 🆕 사용자 친화적 3줄 액션 요약 생성
                    friendly_actions = []
                    for s in raw_signals:
                        if len(friendly_actions) >= 3:  # 최대 3개까지만
                            break
                        if s["action"] == "관망":  # 관망은 건너뛰기
                            continue
                        
                        # what 필드 생성 (구체적인 행동 지침)
                        if "CALL" in s["option"]:
                            if s["action"] == "매수":
                                what = f"콜 매수({s['option']})"
                            else:  # 매도
                                what = f"콜 매도({s['option']})"
                        elif "PUT" in s["option"]:
                            if s["action"] == "매수":
                                what = f"풋 매수({s['option']})"
                            else:  # 매도
                                what = f"풋 매도({s['option']})"
                        else:
                            what = f"옵션 {s['action']}({s['option']})"
                        
                        # confidence 결정 (편차폭 + 칼만 정합성 기반)
                        if s["bias_ok"] and abs(s["ratio"]) > threshold * 2:  # bias_ok + 큰 편차
                            confidence = "높음"
                        elif s["bias_ok"] or abs(s["ratio"]) > threshold * 1.5:  # bias_ok 또는 중간 편차
                            confidence = "보통"
                        else:
                            confidence = "낮음"
                        
                        friendly_actions.append({
                            "label": s["action"],
                            "why": s["why"],
                            "what": what,
                            "confidence": confidence
                        })
                    
                    if friendly_actions:
                        # rec["actions"] = friendly_actions  # 🆕 액션 생성 비활성화
                        print(f"[DEBUG] 액션 요약 생성 완료: {len(friendly_actions)}개")
                        for i, action in enumerate(friendly_actions):
                            print(f"[DEBUG]  - {i+1}: {action['label']} - {action['why']} → {action['what']} (신뢰도: {action['confidence']})")
                    else:
                        print(f"[DEBUG] 액션 요약 생성 실패: 유효한 액션이 없음")
                else:
                    print(f"[DEBUG] 옵션 신호 분석 실패: raw_signals가 비어있음")
            else:
                print(f"[DEBUG] 시장가 미제공: 기본 옵션 전략 신호 생성")
                # 🆕 시장가가 없어도 기본적인 옵션 전략 신호 생성
                basic_actions = self._generate_basic_option_signals(bs_inputs, signal, preferred)
                if basic_actions:
                    # rec["actions"] = basic_actions  # 🆕 액션 생성 비활성화
                    print(f"[DEBUG] 기본 옵션 신호 생성 완료: {len(basic_actions)}개")
                    for i, action in enumerate(basic_actions):
                        print(f"[DEBUG]  - {i+1}: {action['label']} - {action['why']} → {action['what']} (신뢰도: {action['confidence']})")
                else:
                    print(f"[DEBUG] 기본 옵션 신호 생성 실패")
                
                # 🆕 블랙-숄즈 기반 손절가/목표가 계산
                if signal.lower() == "long":
                    # Long 신호: 상승 예상
                    # ATM 콜 옵션 이론가 기반으로 목표가 설정
                    atm_call_price = bs.price(S=S, K=S, T=T, r=r, sigma=sigma, option_type="call", q=q)
                    # 목표가: 현재가 + (ATM 콜 가격의 2배만큼 상승)
                    take_profit = S + (atm_call_price * 2.0)
                    # 손절가: 현재가 - (ATM 콜 가격의 1.5배만큼 하락)
                    stop_loss = S - (atm_call_price * 1.5)
                elif signal.lower() == "short":
                    # Short 신호: 하락 예상
                    # ATM 풋 옵션 이론가 기반으로 목표가 설정
                    atm_put_price = bs.price(S=S, K=S, T=T, r=r, sigma=sigma, option_type="put", q=q)
                    # 목표가: 현재가 - (ATM 풋 가격의 2배만큼 하락)
                    take_profit = S - (atm_put_price * 2.0)
                    # 손절가: 현재가 + (ATM 풋 가격의 1.5배만큼 상승)
                    stop_loss = S + (atm_put_price * 1.5)
                else:
                    # Neutral 신호: 중립
                    # 기본 변동성 기반
                    stop_loss = S * (1 - 1.0 * sigma * math.sqrt(T))
                    take_profit = S * (1 + 1.0 * sigma * math.sqrt(T))
                
                # 손절가/목표가를 rec에 추가
                rec["stop_loss"] = f"${stop_loss:.2f}"
                rec["take_profit"] = f"${take_profit:.2f}"
                
                print(f"[DEBUG] 블랙-숄즈 기반 손절가/목표가 계산 완료:")
                print(f"  - 손절가: ${stop_loss:.2f}")
                print(f"  - 목표가: ${take_profit:.2f}")
                
                # 🆕 옵션 추천 정보 생성 (간단한 형태)
                option_recommendations = []
                
                # 🆕 현재가와 가장 가까운 행사가 찾기 (진짜 ATM 옵션)
                current_price = S
                closest_strike = None
                min_distance = float('inf')
                
                for strike in bs_inputs["strikes"]:
                    distance = abs(strike - current_price)
                    if distance < min_distance:
                        min_distance = distance
                        closest_strike = strike
                
                print(f"[DEBUG] ATM 옵션 선택:")
                print(f"  - 현재가: ${current_price:.2f}")
                print(f"  - 선택된 행사가: ${closest_strike:.2f}")
                print(f"  - 거리: ${min_distance:.2f}")
                
                if closest_strike:
                    # 🆕 현재가를 기준으로 현실적인 옵션 시장가 추정
                    # ITM/ATM/OTM에 따라 다른 가격 추정
                    if closest_strike < current_price:  # ITM 콜 (행사가 < 현재가)
                        # 🆕 ITM 콜: 내재가치 + 시간가치 (더 현실적으로)
                        intrinsic_value = current_price - closest_strike
                        time_value = max(0.01, current_price * 0.005)  # 현재가의 0.5%
                        estimated_call_market_price = intrinsic_value + time_value
                        estimated_put_market_price = max(0.01, current_price * 0.005)  # 시간가치만
                        option_type = "ITM 콜"
                    elif abs(closest_strike - current_price) / current_price < 0.02:  # ATM (행사가 ≈ 현재가)
                        # 🆕 ATM 옵션은 더 현실적인 가격으로 추정
                        estimated_call_market_price = max(0.01, current_price * 0.008)  # 현재가의 0.8% (약 $2.73)
                        estimated_put_market_price = max(0.01, current_price * 0.008)  # 현재가의 0.8% (약 $2.73)
                        option_type = "ATM"
                    else:  # OTM (행사가 > 현재가)
                        # 🆕 OTM 콜: 시간가치만 (더 현실적으로)
                        estimated_call_market_price = max(0.01, current_price * 0.003)  # 현재가의 0.3%
                        intrinsic_value = closest_strike - current_price
                        time_value = max(0.01, current_price * 0.005)  # 현재가의 0.5%
                        estimated_put_market_price = intrinsic_value + time_value
                        option_type = "OTM 콜"
                    
                    print(f"[DEBUG] 옵션 타입: {option_type}")
                    print(f"[DEBUG] 추정 시장가:")
                    print(f"  - 콜: ${estimated_call_market_price:.4f}")
                    print(f"  - 풋: ${estimated_put_market_price:.4f}")
                    
                    # 콜 옵션 추천 (실제 시장가와 비교)
                    call_rec = bs.get_option_recommendation(
                        S=current_price, K=closest_strike, T=T, r=r, sigma=sigma,
                        market_price=estimated_call_market_price,  # 추정 시장가 사용
                        option_type="call", q=q
                    )
                    
                    # 풋 옵션 추천 (실제 시장가와 비교)
                    put_rec = bs.get_option_recommendation(
                        S=current_price, K=closest_strike, T=T, r=r, sigma=sigma,
                        market_price=estimated_put_market_price,   # 추정 시장가 사용
                        option_type="put", q=q
                    )
                    
                    option_recommendations.append({
                        "strike": closest_strike,
                        "call": call_rec,
                        "put": put_rec,
                        "option_type": option_type
                    })
                    print(f"[DEBUG] 옵션 추천 생성 완료: {option_type}")
                
                # 옵션 추천 정보를 rec에 추가
                if option_recommendations:
                    rec["option_recommendations"] = option_recommendations
                    print(f"[DEBUG] 옵션 추천 정보 생성 완료: {len(option_recommendations)}개")
                
                print(f"[KalmanFilter] 블랙-숄즈 옵션 뷰 추가 완료: {len(table)}개 strike")
            
            print(f"[KalmanFilter] 블랙-숄즈 옵션 뷰 추가 완료: {len(table)}개 strike")
            
        except Exception as e:
            print(f"[DEBUG] _attach_option_view 전체 실패: {e}")
            print(f"[DEBUG] 에러 타입: {type(e)}")
            import traceback
            print(f"[DEBUG] 에러 상세: {traceback.format_exc()}")
            
            print(f"[KalmanFilter] 블랙-숄즈 옵션 뷰 추가 실패: {e}")
            # 에러 발생시 기본 옵션 정보라도 제공
            rec["options"] = {
                "error": f"옵션 계산 실패: {str(e)}",
                "spot": round(bs_inputs["S"], 4),
                "sigma_annual": round(bs_inputs["sigma"], 6)
            }
 
    # ---------- 유틸 ----------
    @staticmethod
    def _find_value(data_list, series_id, default=0.0):
        for item in data_list:
            if isinstance(item, dict) and item.get('series_id') == series_id:
                return item.get('latest_value', default)
            if hasattr(item, 'series_id') and getattr(item, 'series_id') == series_id:
                return getattr(item, 'latest_value', default)
        return default

    def _convert_to_level_with_description(self, value: float, feature_type: str) -> str:
        """숫자를 5단계 수준어로 변환하고 설명도 함께 표시"""
        
        # 각 피처별 범위와 설명 정의
        ranges_and_descriptions = {
            "trend": {
                "매우낮음": {"range": (-5, -2), "desc": "강한 하락 추세"},
                "낮음": {"range": (-2, -0.5), "desc": "약한 하락 추세"},
                "보통": {"range": (-0.5, 0.5), "desc": "횡보/중립"},
                "높음": {"range": (0.5, 2), "desc": "약한 상승 추세"},
                "매우높음": {"range": (2, 5), "desc": "강한 상승 추세"}
            },
            "momentum": {
                "매우낮음": {"range": (-5, -2), "desc": "매우 약한 모멘텀"},
                "낮음": {"range": (-2, -0.5), "desc": "약한 모멘텀"},
                "보통": {"range": (-0.5, 0.5), "desc": "중립 모멘텀"},
                "높음": {"range": (0.5, 2), "desc": "강한 모멘텀"},
                "매우높음": {"range": (2, 5), "desc": "매우 강한 모멘텀"}
            },
            "volatility": {
                "매우낮음": {"range": (0, 0.2), "desc": "매우 안정적"},
                "낮음": {"range": (0.2, 0.5), "desc": "안정적"},
                "보통": {"range": (0.5, 1.0), "desc": "보통 변동성"},
                "높음": {"range": (1.0, 2.0), "desc": "불안정"},
                "매우높음": {"range": (2.0, 5.0), "desc": "매우 불안정"}
            },
            "macro_signal": {
                "매우낮음": {"range": (-5, -2), "desc": "매우 부정적 거시환경"},
                "낮음": {"range": (-2, -0.5), "desc": "부정적 거시환경"},
                "보통": {"range": (-0.5, 0.5), "desc": "중립적 거시환경"},
                "높음": {"range": (0.5, 2), "desc": "긍정적 거시환경"},
                "매우높음": {"range": (2, 5), "desc": "매우 긍정적 거시환경"}
            },
            "tech_signal": {
                "매우낮음": {"range": (-5, -2), "desc": "매우 약한 기술적 신호"},
                "낮음": {"range": (-2, -0.5), "desc": "약한 기술적 신호"},
                "보통": {"range": (-0.5, 0.5), "desc": "중립적 기술적 신호"},
                "높음": {"range": (0.5, 2), "desc": "강한 기술적 신호"},
                "매우높음": {"range": (2, 5), "desc": "매우 강한 기술적 신호"}
            }
        }
        
        # 범위에 따른 수준어와 설명 찾기
        level = "보통"
        description = "중립"
        
        for level_name, info in ranges_and_descriptions[feature_type].items():
            min_val, max_val = info["range"]
            if min_val <= value < max_val:
                level = level_name
                description = info["desc"]
                break
        
        # 수준어 + 설명 + 원본 값 반환
        return f"{level} ({value:.3f}) - {description}"

    def _convert_signal_strength_with_description(self, combined_signal: float) -> str:
        """종합 신호 강도를 범위별로 설명과 함께 변환"""
        
        # 신호 강도별 범위와 설명 정의
        signal_ranges = {
            "매우약함": {"range": (-0.5, 0.5), "desc": "매우 불확실한 신호"},
            "약함": {"range": (-1.0, -0.5), "desc": "약한 신호 (관망 권장)"},
            "보통": {"range": (-2.0, -1.0), "desc": "보통 신호 (신중한 진입)"},
            "강함": {"range": (-3.0, -2.0), "desc": "강한 신호 (적극적 진입)"},
            "매우강함": {"range": (-5.0, -3.0), "desc": "매우 강한 신호 (확실한 진입)"}
        }
        
        # 양수 신호 처리
        if combined_signal > 0:
            signal_ranges = {
                "매우약함": {"range": (0, 0.5), "desc": "매우 불확실한 신호"},
                "약함": {"range": (0.5, 1.0), "desc": "약한 신호 (관망 권장)"},
                "보통": {"range": (1.0, 2.0), "desc": "보통 신호 (신중한 진입)"},
                "강함": {"range": (2.0, 3.0), "desc": "강한 신호 (적극적 진입)"},
                "매우강함": {"range": (3.0, 5.0), "desc": "매우 강한 신호 (확실한 진입)"}
            }
        
        # 범위에 따른 수준어와 설명 찾기
        level = "보통"
        description = "보통 신호 (신중한 진입)"
        
        for level_name, info in signal_ranges.items():
            min_val, max_val = info["range"]
            if min_val <= combined_signal < max_val:
                level = level_name
                description = info["desc"]
                break
        
        # 신호 방향 추가
        direction = "매수" if combined_signal > 0 else "매도"
        
        # 수준어 + 설명 + 원본 값 + 방향 반환
        return f"{level} ({combined_signal:.3f}) - {description} ({direction} 신호)"

    def _convert_risk_score_with_description(self, risk_score: float) -> str:
        """리스크 점수를 범위별로 설명과 함께 변환"""
        
        # 리스크 점수별 범위와 설명 정의
        risk_ranges = {
            "매우낮음": {"range": (0.0, 0.2), "desc": "매우 안전한 투자 환경"},
            "낮음": {"range": (0.2, 0.4), "desc": "안전한 투자 환경"},
            "보통": {"range": (0.4, 0.6), "desc": "일반적인 투자 환경"},
            "높음": {"range": (0.6, 0.8), "desc": "위험한 투자 환경"},
            "매우높음": {"range": (0.8, 1.0), "desc": "매우 위험한 투자 환경"}
        }
        
        # 범위에 따른 수준어와 설명 찾기
        level = "보통"
        description = "일반적인 투자 환경"
        
        for level_name, info in risk_ranges.items():
            min_val, max_val = info["range"]
            if min_val <= risk_score < max_val:
                level = level_name
                description = info["desc"]
                break
        
        # 수준어 + 설명 + 원본 값 반환
        return f"{level} ({risk_score:.3f}) - {description}"

    # ---------- main ----------
    def get_data(self, **kwargs) -> KalmanRegimeFilterActionOutput:
        # 🆕 Debug 모드 설정
        debug = True  # 또는 kwargs.get('debug', True)
        
        # 🆕 시작 시간 기록
        t_start = time.time()
        
        # 입력 파라미터 파싱
        inp = KalmanRegimeFilterInput(**kwargs)
        
        if debug:
            print(f"[KalmanRegimeFilterTool] 시작: {inp.tickers[0]} 분석")
            print(f"[KalmanRegimeFilterTool] 계좌 가치: {inp.account_value} {inp.exchange_rate}")
            print(f"[KalmanRegimeFilterTool] 위험 비율: {inp.risk_pct}")

        # 🆕 안전한 import
        try:
            from service.llm.AIChat.tool.FeaturePipelineTool import FeaturePipelineTool
        except ImportError as e:
            error_msg = f"FeaturePipelineTool import 실패: {str(e)}"
            print(f"[KalmanRegimeFilterTool] {error_msg}")
            return KalmanRegimeFilterActionOutput(
                summary="데이터 수집/정규화 실패",
                recommendations={"error": error_msg},
                start_time=datetime.now().isoformat(),
                end_time=datetime.now().isoformat()
            )

        # 1️⃣ Composite 공식 정의 (5차원 칼만 필터 전용)
        kalman_composite_formulas = {
            # 거시경제 + 변동성 복합 지표 (trend 추정용) - macro 가중치 대폭 감소
            "kalman_trend": lambda feats: (
                0.001 * feats.get("GDP", 0.0) + 
                0.01 * feats.get("CPIAUCSL", 0.0) + 
                0.989 * feats.get("VIX", 0.0)
            ),
            # 기술적 + 거시경제 복합 지표 (momentum 추정용) - macro 가중치 대폭 감소
            "kalman_momentum": lambda feats: (
                0.7 * feats.get("RSI", 0.0) + 
                0.25 * feats.get("MACD", 0.0) + 
                0.05 * feats.get("CPIAUCSL", 0.0)
            ),
            # 변동성 (VIX만 사용)
            "kalman_volatility": lambda feats: feats.get("VIX", 0.0),
            # 거시경제 신호 (macro_signal)
            "kalman_macro": lambda feats: (
                0.001 * feats.get("GDP", 0.0) + 
                0.999 * feats.get("CPIAUCSL", 0.0)
            ),
            # 기술적 신호 (tech_signal)
            "kalman_tech": lambda feats: (
                0.6 * feats.get("RSI", 0.0) + 
                0.4 * feats.get("MACD", 0.0)
            )
        }

        # 2️⃣ Feature Pipeline 실행 (정규화 + Composite 생성)
        pipeline_result = FeaturePipelineTool(self.ai_chat_service).transform(
            tickers=inp.tickers,
            start_date=inp.start_date,
            end_date=inp.end_date,
            feature_set=["GDP", "CPIAUCSL", "DEXKOUS", "RSI", "MACD", "VIX", "PRICE"],
            normalize=True,  # ✅ 정규화 활성화
            normalize_targets=["GDP", "CPIAUCSL", "VIX", "RSI", "MACD"],  # ✅ Composite 자동 추가됨
            generate_composites=True,  # ✅ 복합 피처 생성
            composite_formula_map=kalman_composite_formulas,  # 🆕 5차원 칼만 전용 공식 사용
            return_raw=True,  # 🆕 Raw + Normalized 동시 반환
            debug=debug
        )

        # 3️⃣ Raw 값과 Normalized 값 분리
        raw_features = pipeline_result["raw"]      # 계산용 (가격, 환율)
        norm_features = pipeline_result["normalized"]  # 신호용 (모델 입력)
        

        
        # Raw 값으로 계산용 데이터 추출
        exchange_rate = raw_features.get("DEXKOUS", 1300.0)  # ✅ KRW/USD (올바른 방향)
        entry_price = raw_features.get("PRICE", 0.0)

        # 통화 처리 수정: 계정 통화와 종목 통화 일치
        instrument_ccy = "USD"  # SOXL 등 대부분 종목은 USD
        account_ccy = inp.account_ccy.upper()  # 'KRW' or 'USD'
        
        # 통화 코드 오타 보정
        if account_ccy == "KWR":
            account_ccy = "KRW"
            if debug:
                print(f"[KalmanFilter] Currency code corrected: KWR → KRW")
        
        account_value_usd = inp.account_value
        if account_ccy == "KRW" and instrument_ccy == "USD":
            # KRW 계정 → USD 변환 (DEXKOUS: KRW/USD)
            account_value_usd = inp.account_value / exchange_rate
            if debug:
                print(f"[KalmanFilter] Currency conversion: {inp.account_value} KRW → {account_value_usd:.2f} USD (rate: {exchange_rate})")
        elif account_ccy == "USD" and instrument_ccy == "USD":
            # USD 계정 → 변환 불필요
            account_value_usd = inp.account_value
            if debug:
                print(f"[KalmanFilter] USD account: {account_value_usd} USD")
        else:
            # 기타 통화 조합은 기본값 사용
            account_value_usd = inp.account_value
            if debug:
                print(f"[KalmanFilter] Unknown currency pair: {account_ccy} → {instrument_ccy}, using original value")

        if entry_price == 0.0:
            raise RuntimeError(f"{inp.tickers[0]}의 가격 데이터를 찾을 수 없습니다.")
        
        # 🆕 누락된 기술적 지표에 대한 기본값 설정
        missing_features = []
        
        if "RSI" not in norm_features:
            print("⚠️ RSI 데이터 누락, 기본값 50.0 사용")
            norm_features["RSI"] = 50.0
            missing_features.append("RSI")
        if "MACD" not in norm_features:
            print("⚠️ MACD 데이터 누락, 기본값 0.0 사용")
            norm_features["MACD"] = 0.0
            missing_features.append("MACD")
        if "VIX" not in norm_features:
            print("⚠️ VIX 데이터 누락, 기본값 20.0 사용")
            norm_features["VIX"] = 20.0
            missing_features.append("VIX")
        if "GDP" not in norm_features:
            print("⚠️ GDP 데이터 누락, 기본값 25000.0 사용")
            norm_features["GDP"] = 25000.0
            missing_features.append("GDP")
        if "CPIAUCSL" not in norm_features:
            print("⚠️ CPIAUCSL 데이터 누락, 기본값 300.0 사용")
            norm_features["CPIAUCSL"] = 300.0
            missing_features.append("CPIAUCSL")
        if "DEXKOUS" not in norm_features:
            print("⚠️ DEXKOUS 데이터 누락, 기본값 0.0008 사용")
            norm_features["DEXKOUS"] = 0.0008
            missing_features.append("DEXKOUS")
        
        if missing_features:
            print(f"⚠️ 총 {len(missing_features)}개 피처가 누락되어 기본값 사용: {missing_features}")
        else:
            print("✅ 모든 피처 데이터 정상 수집됨")

        # 4️⃣ 5차원 관측 벡터 구성 (5차원 칼만 필터용)
        z = np.array([
            norm_features.get("kalman_trend", 0.0),      # trend
            norm_features.get("kalman_momentum", 0.0),   # momentum
            norm_features.get("kalman_volatility", 0.0), # volatility
            norm_features.get("kalman_macro", 0.0),      # macro_signal
            norm_features.get("kalman_tech", 0.0)        # tech_signal
        ])

        # 5️⃣ 칼만 필터 실행 (Redis + SQL 하이브리드 상태 관리)
        ticker = inp.tickers[0]
        
        # 🆕 경고 메시지 리스트 초기화
        warning_messages: List[str] = []
        
        # 🆕 상태 관리자에서 필터 가져오기 (Redis → SQL → Rule-Based 초기화 순서)
        if self.state_manager:
            # SessionAwareTool에서 사용자 정보 가져오기 (fallback 포함)
            account_db_key = self.get_account_db_key()
            shard_id = getattr(self.get_session(), 'shard_id', 1) if self.get_session() else 1
            
            # 🆕 세션 유효성 검증 및 fallback
            if account_db_key == 0:
                # 임시로 고유한 계정 키 생성 (세션 ID 기반)
                import hashlib
                session_hash = hashlib.md5(f"session_{ticker}".encode()).hexdigest()[:8]
                account_db_key = int(session_hash, 16) % 10000  # 0-9999 범위
                warning_messages.append(f"⚠️ 사용자 세션이 없어 임시 계정({account_db_key})으로 실행됩니다")
                print(f"[KalmanFilter] 세션 없음, 임시 계정 사용: {ticker} -> {account_db_key} (샤드 {shard_id})")
            
            try:
                # 🆕 동기 방식으로 SQL에서 직접 복원
                def restore_from_sql_sync():
                    try:
                        import pymysql
                        import json
                        import numpy as np
                        
                        # 설정 파일에서 데이터베이스 정보 읽기
                        config_path = "application/base_web_server/base_web_server-config_local.json"
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                        
                        db_config = config["databaseConfig"]
                        
                        # 직접 MySQL 연결 (동기 방식)
                        connection = pymysql.connect(
                            host=db_config["host"],
                            port=db_config["port"],
                            user=db_config["user"],
                            password=db_config["password"],
                            database="finance_shard_2",  # shard_id에 따라
                            charset=db_config["charset"]
                        )
                        
                        try:
                            with connection.cursor() as cursor:
                                # 최신 상태 조회
                                query = """
                                SELECT state_vector_x, covariance_matrix_p, step_count, performance_metrics
                                FROM table_kalman_history 
                                WHERE ticker = %s AND account_db_key = %s 
                                ORDER BY created_at DESC LIMIT 1
                                """
                                cursor.execute(query, (ticker, account_db_key))
                                result = cursor.fetchone()
                                
                                if result:
                                    # 칼만 필터 인스턴스 생성 및 복원
                                    filter_instance = KalmanRegimeFilterCore()
                                    filter_instance.x = np.array(json.loads(result[0]))  # state_vector_x
                                    filter_instance.P = np.array(json.loads(result[1]))  # covariance_matrix_p
                                    filter_instance.step_count = result[2]  # step_count
                                    
                                    print(f"[KalmanFilter] SQL에서 복원 성공: {ticker} (step_count: {filter_instance.step_count})")
                                    return filter_instance
                                else:
                                    print(f"[KalmanFilter] SQL에서 데이터 없음: {ticker}")
                                    return None
                                    
                        finally:
                            connection.close()
                            
                    except Exception as e:
                        print(f"[KalmanFilter] SQL 복원 실패: {e}")
                        return None
                
                # 동기적으로 SQL 복원 실행
                filter_instance = restore_from_sql_sync()
                
                if filter_instance is None:
                    # SQL에서 복원 실패 시 Rule-Based 초기화
                    print(f"[KalmanFilter] Rule-Based 초기화: {ticker}")
                    
                    # 동기적으로 Rule-Based 초기화 실행
                    try:
                        from service.llm.AIChat.manager.KalmanInitializerTool import KalmanInitializerTool
                        
                        # Rule-Based 초기화 툴 사용
                        initializer = KalmanInitializerTool()
                        x, P = initializer.initialize_kalman_state(ticker)
                        
                        # 칼만 필터 인스턴스 생성 및 초기화
                        filter_instance = KalmanRegimeFilterCore()
                        filter_instance.x = x
                        filter_instance.P = P
                        filter_instance.step_count = 0  # 초기화된 상태는 step_count = 0
                        
                        print(f"[KalmanFilter] Rule-Based 초기화 적용 완료: {ticker}")
                        
                    except Exception as e:
                        print(f"[KalmanFilter] Rule-Based 초기화 실패: {e}")
                        # 실패 시 기본 필터 반환
                        filter_instance = KalmanRegimeFilterCore()
                
                # 칼만 필터 실행
                filter_instance.step(z)
                state, cov = filter_instance.x.copy(), filter_instance.P.copy()
                
                print(f"[KalmanFilter] 상태 복원 완료: {ticker} (step_count: {filter_instance.step_count})")
                
                # Redis 저장 (챗봇과 동일한 방식)
                if self.state_manager:
                    try:
                        # 챗봇과 동일한 방식으로 Redis 저장 (동기 방식)
                        try:
                            from service.cache.cache_service import CacheService
                            import asyncio
                            
                            # 동기적으로 Redis 저장 실행
                            async def save_to_redis():
                                async with CacheService.get_client() as redis:
                                    # 칼만 필터 상태를 JSON으로 직렬화
                                    state_data = {
                                        "x": filter_instance.x.tolist(),
                                        "P": filter_instance.P.tolist(),
                                        "step_count": filter_instance.step_count,
                                        "last_update": datetime.now().isoformat(),
                                        "performance": json.dumps(filter_instance.get_performance_metrics()),
                                        "account_db_key": account_db_key,
                                        "shard_id": shard_id
                                    }
                                    
                                    # Redis에 저장 (샤드 ID 포함)
                                    redis_key = f"kalman:{ticker}:{account_db_key}:{shard_id}"
                                    await redis.set_string(redis_key, json.dumps(state_data), expire=3600)
                                    print(f"[KalmanFilter] Redis 저장 완료: {ticker} (샤드 {shard_id})")
                            
                            # ThreadPoolExecutor에서 실행되는 경우를 대비한 안전한 처리
                            import threading
                            def run_async_in_thread():
                                import asyncio
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                try:
                                    loop.run_until_complete(save_to_redis())
                                except Exception as e:
                                    print(f"[KalmanFilter] Redis 저장 스레드 실패: {e}")
                                finally:
                                    loop.close()
                            
                            thread = threading.Thread(target=run_async_in_thread)
                            thread.daemon = True
                            thread.start()
                                
                        except Exception as e:
                            print(f"[KalmanFilter] Redis 저장 실패: {e}")
                            
                    except Exception as e:
                        print(f"[KalmanFilter] Redis 저장 실패: {e}")
                
                # 성능 모니터링
                performance_metrics = filter_instance.get_performance_metrics()
                
                print(f"[KalmanFilter] Redis+SQL 하이브리드 상태 관리: {ticker} (step_count: {filter_instance.step_count})")
                
            except Exception as e:
                print(f"[KalmanFilter] 상태 관리 실패, fallback 사용: {e}")
                # fallback으로 전환
                if not hasattr(self, '_filters'):
                    self._filters = {}
                
                if ticker not in self._filters:
                    self._filters[ticker] = KalmanRegimeFilterCore()
                    print(f"[KalmanFilter] 새로운 필터 생성 (fallback): {ticker}")
                else:
                    print(f"[KalmanFilter] 기존 필터 사용 (fallback): {ticker} (step_count: {self._filters[ticker].step_count})")
                
                self._filters[ticker].step(z)
                state, cov = self._filters[ticker].x.copy(), self._filters[ticker].P.copy()
                performance_metrics = self._filters[ticker].get_performance_metrics()
                filter_instance = self._filters[ticker]  # fallback용 filter_instance 설정
        else:
            # 상태 관리자가 없으면 기존 방식 사용 (fallback)
            if not hasattr(self, '_filters'):
                self._filters = {}
            
            if ticker not in self._filters:
                self._filters[ticker] = KalmanRegimeFilterCore()
                print(f"[KalmanFilter] 새로운 필터 생성 (fallback): {ticker}")
            else:
                print(f"[KalmanFilter] 기존 필터 사용 (fallback): {ticker} (step_count: {self._filters[ticker].step_count})")
            
            self._filters[ticker].step(z)
            state, cov = self._filters[ticker].x.copy(), self._filters[ticker].P.copy()
            performance_metrics = self._filters[ticker].get_performance_metrics()
        
        # 7️⃣ 액션 엔진
        rec: Dict[str, Any] = {}

        # ── 변동성 클리핑
        raw_vol = float(state[2])  # volatility
        vol = float(np.clip(raw_vol, 0.05, 2.0))
        if vol != raw_vol:
            warning_messages.append(f"Volatility clipped: {raw_vol:.4f}→{vol:.2f}")

        # ── 신호 결정
        trend = state[0]
        momentum = state[1]
        macro_signal = state[3]
        tech_signal = state[4]
        
        # 종합 신호 계산
        combined_signal = 0.4 * trend + 0.3 * momentum + 0.2 * macro_signal + 0.1 * tech_signal
        
        # 가드 & 위생 체크: combined_signal을 합리적 범위로 클리핑
        combined_signal = np.clip(combined_signal, -5.0, 5.0)
        
        if combined_signal > 0.5:
            signal = "Long"
            strategy = "Trend Following"
        elif combined_signal < -0.5:
            signal = "Short"
            strategy = "Mean Reversion"
        else:
            signal = "Neutral"
            strategy = "Market Neutral"

        # 🆕 신뢰도 계산
        signal_confidence = abs(combined_signal) / 5.0  # 0.0 ~ 1.0 (0% ~ 100%)
        confidence_level = "높음" if signal_confidence > 0.7 else "보통" if signal_confidence > 0.4 else "낮음"
        
        rec["trading_signal"] = signal
        rec["strategy"] = strategy
        rec["signal_confidence"] = f"{confidence_level} ({signal_confidence:.1%})"
        rec["combined_signal"] = self._convert_signal_strength_with_description(combined_signal)

        # ── 포지션 크기
        # 🆕 최소 주문 금액 및 수량 적용
        min_order_value_usd = 50.0  # 최소 주문 금액 (USD)
        min_order_quantity = 1      # 최소 수량 (1주)
        
        # 계좌 통화별 최소 주문 금액 조정
        if account_ccy == "KRW":
            min_order_value_usd = 10000.0 / exchange_rate  # 10,000원을 USD로 변환
        elif account_ccy == "USD":
            min_order_value_usd = 50.0  # $50 최소 주문
        
        risk_dollar = account_value_usd * inp.risk_pct
        
        # 최소 주문 금액 체크
        if risk_dollar < min_order_value_usd:
            if debug:
                print(f"[KalmanFilter] Risk amount {risk_dollar:.2f} USD < min order {min_order_value_usd:.2f} USD")
            pos_size = 0.0
            warning_messages.append(f"Risk amount too small for minimum order: ${risk_dollar:.2f} < ${min_order_value_usd:.2f}")
        else:
            # ATR 기반 포지션 크기 계산
            pos_size = risk_dollar / (atr * entry_price)
            
            # 가드 & 위생 체크: position_size가 비정상적으로 크면 클램프
            max_position_size = account_value_usd / entry_price  # 계좌 전체로 살 수 있는 최대 주식 수
            if pos_size < 0: # 음수 방지
                pos_size = 0
            if pos_size < min_order_quantity: # 최소 수량 클램프
                pos_size = min_order_quantity
                warning_messages.append(f"Position size clamped to minimum: {pos_size:.2f} shares")
            if pos_size > max_position_size:
                warning_messages.append(f"Position size clamped: {pos_size:.2f} → {max_position_size:.2f} (max account size)")
                pos_size = max_position_size
        
        rec["position_size"] = round(pos_size, 4)

        # ── 레버리지 계산
        leverage = pos_size * entry_price / account_value_usd
        
        # 🆕 레버리지/노출비율 표기 개선
        if leverage < 1.0:
            exposure_str = f"노출 {leverage*100:.0f}%"
        else:
            exposure_str = f"{leverage:.2f}x 레버리지"
        
        rec["leverage"] = exposure_str

        # ── SL/TP & ATR 먼저 계산 ---
        vol_clamped = float(np.clip(raw_vol, 0.05, 2.0))
        atr_pct = 0.02 + 0.03 * (vol_clamped / 2.0)  # 0.02~0.05
        atr = entry_price * atr_pct

        # 🆕 블랙-숄즈 옵션 뷰로 대체
        print(f"[DEBUG] 🚀 블랙-숄즈 옵션 뷰 시작!")
        print(f"[DEBUG] 입력값:")
        print(f"  - entry_price: {entry_price}")
        print(f"  - atr_pct: {atr_pct}")
        print(f"  - horizon_days: {inp.horizon_days}")
        print(f"  - signal: {signal}")
        
        # 1) 블랙-숄즈 입력 파라미터 생성
        print(f"[DEBUG] _build_bs_inputs 호출...")
        bs_inputs = self._build_bs_inputs(
            entry_price=entry_price,
            atr_pct=atr_pct,
            rate=0.02,                  # 기본 2% (필요시 설정/환경변수로)
            div_yield=0.0,              # 기본 0% (주식/ETF 배당 정보 필요시 수정)
            days_to_expiry=inp.horizon_days  # 예측 기간과 동일
        )
        print(f"[DEBUG] _build_bs_inputs 완료: {bs_inputs}")

        # 2) 블랙-숄즈 옵션 뷰 추가
        print(f"[DEBUG] _attach_option_view 호출...")
        market_prices = getattr(inp, 'option_market_prices', None)
        threshold = getattr(inp, 'option_signal_threshold', 0.05)
        
        print(f"[DEBUG] 옵션 파라미터:")
        print(f"  - market_prices: {market_prices}")
        print(f"  - threshold: {threshold}")
        
        self._attach_option_view(rec, bs_inputs, signal, market_prices, threshold)
        print(f"[DEBUG] _attach_option_view 완료!")
        
        # 🆕 최종 확인 로그
        print(f"[DEBUG] 🎯 블랙-숄즈 옵션 뷰 최종 결과:")
        print(f"  - rec에 'options' 키 존재: {'options' in rec}")
        if 'options' in rec:
            print(f"  - options 내용: {rec['options']}")
        else:
            print(f"  - ❌ options 키가 rec에 없음!")
        
        # 🆕 actions 키 확인
        print(f"  - rec에 'actions' 키 존재: {'actions' in rec}")
        if 'actions' in rec:
            print(f"  - actions 내용: {rec['actions']}")
            print(f"  - actions 개수: {len(rec['actions'])}")
        else:
            print(f"  - ❌ actions 키가 rec에 없음!")
        
        print(f"[KalmanFilter] 블랙-숄즈 옵션 뷰 계산 완료:")
        print(f"  - entry_price: ${entry_price:.2f}")
        print(f"  - atr_pct: {atr_pct:.6f}")
        print(f"  - sigma_annual: {bs_inputs['sigma']:.6f}")
        print(f"  - T_years: {bs_inputs['T']:.6f}")
        print(f"  - strikes: {bs_inputs['strikes']}")
        print(f"  - signal: {signal}")
        
        # 🆕 손절가/목표가는 블랙-숄즈에서 계산됨 (위에서 이미 설정됨)
        # rec["stop_loss"]와 rec["take_profit"]은 이미 설정되어 있음
        
        # VIX 기준 시장 안정성
        vix_value = raw_features.get("VIX", 20.0)
        if vix_value < 15:
            stability = "Stable"
        elif vix_value < 20:
            stability = "Neutral"
        elif vix_value < 30:
            stability = "Unstable"
        else:
            stability = "Turbulent"
        
        # 🆕 개선된 출력 포맷 (손절가/목표가는 이미 설정됨)
        rec["current_price"] = f"${entry_price:.2f}"
        # rec["stop_loss"]와 rec["take_profit"]은 블랙-숄즈에서 이미 설정됨
        rec["market_stability"] = f"{stability} (VIX={vix_value:.2f})"

        # ── 리스크 지표
        # 🆕 시장 불안정성 계산 (거시/기술적 지표의 불일치 정도)
        market_instability = abs(macro_signal - tech_signal) / 2.0  # 0~1 범위로 정규화
        market_instability = np.clip(market_instability, 0.0, 1.0)
        
        risk_score = 0.3 * vol + 0.3 * abs(momentum) + 0.2 * abs(trend) + 0.2 * market_instability
        risk_score = np.clip(risk_score, 0.0, 1.0)  # 0~1 범위로 클리핑
        
        rec["risk_score"] = self._convert_risk_score_with_description(risk_score)

        # ── 성능 지표 추가
        rec["filter_performance"] = performance_metrics
        # 🆕 상태 추정치 저장 (수준어 + 설명 + 원본 값)
        rec["state_estimates"] = {
            "trend": self._convert_to_level_with_description(trend, "trend"),
            "momentum": self._convert_to_level_with_description(momentum, "momentum"),
            "volatility": self._convert_to_level_with_description(vol, "volatility"),
            "macro_signal": self._convert_to_level_with_description(macro_signal, "macro_signal"),
            "tech_signal": self._convert_to_level_with_description(tech_signal, "tech_signal")
        }

        # 🆕 SQL 저장 (샤드 ID 포함)
        if self.state_manager and hasattr(filter_instance, 'step_count'):
            # 1분마다 SQL 저장 (샤드 ID 포함)
            market_data = {
                "price": entry_price,
                "exchange_rate": exchange_rate,
                "features": norm_features,
                "raw_features": raw_features
            }
            
            # SQL 저장 조건 확인 (1분 간격 또는 첫 번째 실행)
            should_save = self.state_manager.should_save_to_sql(ticker, account_db_key, min_interval_minutes=1)
            is_first_run = filter_instance.step_count <= 1  # 첫 번째 실행인지 확인
            
            if should_save or is_first_run:
                print(f"[KalmanFilter] SQL 저장 조건 만족: {ticker} (샤드 {shard_id}) - 첫 실행: {is_first_run}")
                try:
                    # SQL 저장 (aiomysql 비동기 방식)
                    async def save_to_sql_async():
                        try:
                            import aiomysql
                            import json
                            from datetime import datetime
                            
                            # 설정 파일에서 데이터베이스 정보 읽기
                            config_path = "application/base_web_server/base_web_server-config_local.json"
                            with open(config_path, 'r', encoding='utf-8') as f:
                                config = json.load(f)
                            
                            db_config = config["databaseConfig"]
                            
                            # aiomysql로 비동기 연결 (설정 파일에서 읽어온 값 사용)
                            pool = await aiomysql.create_pool(
                                host=db_config["host"],
                                port=db_config["port"],
                                user=db_config["user"],
                                password=db_config["password"],
                                db="finance_shard_2",  # shard_id에 따라
                                charset=db_config["charset"],
                                autocommit=True
                            )
                            
                            try:
                                async with pool.acquire() as conn:
                                    async with conn.cursor() as cursor:
                                        # 저장 프로시저 호출 (올바른 파라미터 순서)
                                        stored_proc_name = "fp_kalman_history_insert"
                                        params = (
                                            ticker,  # p_ticker
                                            account_db_key,  # p_account_db_key
                                            datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],  # p_timestamp (MySQL datetime 형식)
                                            json.dumps(filter_instance.x.tolist()),  # p_state_vector_x
                                            json.dumps(filter_instance.P.tolist()),  # p_covariance_matrix_p
                                            filter_instance.step_count,  # p_step_count
                                            signal,  # p_trading_signal
                                            json.dumps(market_data),  # p_market_data
                                            json.dumps(filter_instance.get_performance_metrics())  # p_performance_metrics
                                        )
                                        
                                        await cursor.callproc(stored_proc_name, params)
                                        print(f"[KalmanFilter] SQL 저장 완료: {ticker} (샤드 {shard_id})")
                                        
                            finally:
                                pool.close()
                                await pool.wait_closed()
                                
                        except Exception as e:
                            print(f"[KalmanFilter] SQL 저장 실패: {e}")
                    
                    # 새로운 이벤트 루프에서 비동기 실행
                    def run_async_in_thread():
                        import asyncio
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            loop.run_until_complete(save_to_sql_async())
                        except Exception as e:
                            print(f"[KalmanFilter] SQL 저장 스레드 실패: {e}")
                        finally:
                            loop.close()
                    
                    # 백그라운드 스레드에서 실행
                    import threading
                    thread = threading.Thread(target=run_async_in_thread)
                    thread.daemon = True
                    thread.start()
                        
                except Exception as e:
                    print(f"[KalmanFilter] SQL 저장 실패: {e}")
            else:
                print(f"[KalmanFilter] SQL 저장 조건 불만족: {ticker} (샤드 {shard_id}) - 1분 간격 대기 중 (step_count: {filter_instance.step_count})")

        # ── 지연
        latency = time.time() - t_start
        if latency > self.max_latency:
            warning_messages.append(f"Latency {latency:.3f}s > limit {self.max_latency}s")
        rec["latency"] = round(latency, 3)

        if warning_messages:
            rec["warnings"] = warning_messages

        # 8️⃣ 결과 반환
        print(f"[DEBUG] 🎯 최종 결과 반환 준비:")
        print(f"  - rec 키들: {list(rec.keys())}")
        print(f"  - 'options' 키 존재: {'options' in rec}")
        if 'options' in rec:
            print(f"  - options 타입: {type(rec['options'])}")
            print(f"  - options 내용: {rec['options']}")
        else:
            print(f"  - ❌ options 키가 최종 rec에 없음!")
        
        data_status = "완전" if not missing_features else f"부분 ({len(missing_features)}개 누락)"
        summary = (
            f"5차원 칼만 필터 + 블랙-숄즈 옵션 분석 완료 - {signal} 신호, 변동성: {vol:.3f}, "
            f"성능: {performance_metrics['status']}, 데이터: {data_status} · "
            f"옵션 분석: {inp.horizon_days}D 만기, {len(bs_inputs['strikes'])}개 행사가"
        )
        
        if missing_features:
            rec["data_warnings"] = f"다음 피처들이 기본값으로 대체됨: {missing_features}"
        
        print(f"[DEBUG] 🚀 KalmanRegimeFilterActionOutput 반환:")
        print(f"  - summary: {summary}")
        print(f"  - recommendations 키 수: {len(rec)}")
        print(f"  - options 포함 여부: {'options' in rec}")
        
        return KalmanRegimeFilterActionOutput(
            summary=summary,
            recommendations=rec,
            start_time=inp.start_date,
            end_time=inp.end_date
        )
