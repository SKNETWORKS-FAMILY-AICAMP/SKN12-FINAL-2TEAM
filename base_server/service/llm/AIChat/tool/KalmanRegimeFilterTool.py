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

    # 🆕 예측 관련 유틸리티 함수들
    _Z_MAP = {0.8: 1.2816, 0.9: 1.6449, 0.95: 1.96}

    def _get_z(self, ci: float) -> float:
        keys = sorted(self._Z_MAP.keys())
        closest = min(keys, key=lambda k: abs(k - ci))
        return self._Z_MAP[closest]

    def _forecast_price(self, s0: float, mu_daily: float, sigma_daily: float,
                        horizon_days: int, z: float) -> Dict[str, float]:
        h = max(1, int(horizon_days))
        center = s0 * ((1.0 + mu_daily) ** h)
        width = sigma_daily * math.sqrt(h)
        lower = max(0.01, center * math.exp(-z * width))
        upper = center * math.exp(+z * width)
        return {"center": center, "lower": lower, "upper": upper}
 
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

        rec["trading_signal"] = signal
        rec["strategy"] = strategy
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

        # 🆕 항상 가격 예측 수행
        # 1) 드리프트/변동성 산출
        #    - 드리프트: combined_signal(±5) → 일간 기대수익률로 선형 매핑
        #      예) drift_scale=0.0015이면, 신호 +1 ≈ +0.15%/일
        mu_daily = float(np.clip(inp.drift_scale * combined_signal, -0.05, 0.05))
        #    - 변동성: ATR%를 일간 표준편차 근사로 사용(간단하고 일관적)
        sigma_daily = float(np.clip(atr_pct, 0.005, 0.15))

        # 2) z-score 선택 (0.8/0.9/0.95 지원)
        z = self._get_z(inp.ci_level)

        # 3) 예측
        pred = self._forecast_price(entry_price, mu_daily, sigma_daily, inp.horizon_days, z)

        # 4) 출력용 포맷
        def _pct(x): return (x / entry_price - 1.0) * 100.0
        rec["prediction"] = {
            "enabled": True,
            "horizon_days": inp.horizon_days,
            "center": f"${pred['center']:.2f} ({_pct(pred['center']):+.2f}%)",
            "ci": f"{int(round(inp.ci_level*100))}%",
            "lower":  f"${pred['lower']:.2f} ({_pct(pred['lower']):+.2f}%)",
            "upper":  f"${pred['upper']:.2f} ({_pct(pred['upper']):+.2f}%)",
            # 사용자 노출용 간단 가정(모델 내부 스케일 언급 없이)
            "assumption": "일간 드리프트(신호 기반)·변동성(ATR%) 고정 가정"
        }
        
        # 🆕 디버그 로그 추가
        print(f"[KalmanFilter] 예측 계산 완료:")
        print(f"  - entry_price: ${entry_price:.2f}")
        print(f"  - combined_signal: {combined_signal:.3f}")
        print(f"  - mu_daily: {mu_daily:.6f}")
        print(f"  - sigma_daily: {sigma_daily:.6f}")
        print(f"  - z-score: {z:.4f}")
        print(f"  - prediction: {rec['prediction']}")
        
        # 손절가 및 목표가 계산 (바닥 가드 포함)
        stop_loss = max(entry_price * (1 - 1.5 * atr_pct), entry_price * 0.5)  # 최소 50% 가드
        take_profit = entry_price * (1 + 3.0 * atr_pct)
        
        # 🆕 출력 포맷 개선
        sl_pct = (stop_loss - entry_price) / entry_price * 100
        tp_pct = (take_profit - entry_price) / entry_price * 100
        rr = abs(tp_pct / sl_pct) if sl_pct != 0 else None
        
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
        
        # 🆕 개선된 출력 포맷
        rec["current_price"] = f"${entry_price:.2f}"
        rec["stop_loss"] = f"${stop_loss:.2f} ({sl_pct:+.2f}%)"
        rec["take_profit"] = f"${take_profit:.2f} ({tp_pct:+.2f}%)"
        if rr is not None:
            rec["risk_reward_ratio"] = f"{rr:.2f}"
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
        data_status = "완전" if not missing_features else f"부분 ({len(missing_features)}개 누락)"
        summary = (
            f"5차원 칼만 필터 분석 완료 - {signal} 신호, 변동성: {vol:.3f}, "
            f"성능: {performance_metrics['status']}, 데이터: {data_status} · "
            f"예측:{inp.horizon_days}D {int(round(inp.ci_level*100))}%CI"
        )
        
        if missing_features:
            rec["data_warnings"] = f"다음 피처들이 기본값으로 대체됨: {missing_features}"
        
        return KalmanRegimeFilterActionOutput(
            summary=summary,
            recommendations=rec,
            start_time=inp.start_date,
            end_time=inp.end_date
        )
