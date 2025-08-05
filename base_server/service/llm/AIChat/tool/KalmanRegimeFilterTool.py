from __future__ import annotations

import time
import json
from datetime import datetime
from typing import Dict, Any, List
import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, Field

# --- 외부 툴 의존부 ---
from service.llm.AIChat.SessionAwareTool import SessionAwareTool
from service.llm.AIChat.manager.KalmanStateManager import KalmanStateManager
from service.llm.AIChat.manager.KalmanRegimeFilterCore import KalmanRegimeFilterCore

__all__ = ["KalmanRegimeFilterTool"]

# ───────────────────────── Input / Output ───────────────────────── #

class KalmanRegimeFilterInput(BaseModel):
    tickers: List[str] = Field(..., description="분석할 종목 리스트")
    start_date: str    = Field(..., description="데이터 시작일(YYYY-MM-DD)")
    end_date: str      = Field(..., description="데이터 종료일(YYYY-MM-DD)")

    # ▶️ 실전 운용 파라미터
    account_value: float = Field(... ,description="계좌 가치")
    exchange_rate: str = Field("KWR", description="화폐 단위(예시: KWR, USD)" )
    risk_pct: float      = Field(0.02,      description="한 트레이드당 위험 비율(0~1)")
    max_leverage: float  = Field(10.0,      description="허용 최대 레버리지")


class KalmanRegimeFilterActionOutput(BaseModel):
    summary: str
    recommendations: Dict[str, Any]
    start_time: str
    end_time: str

# ─────────────────────────── Kalman Filter Core ───────────────────────── #

class KalmanRegimeFilterCore:
    """
    5차원 실전용 칼만 필터
    상태 벡터: [trend, momentum, volatility, macro_signal, tech_signal]
    """
    def __init__(self) -> None:
        # 상태 벡터: [trend, momentum, volatility, macro_signal, tech_signal]
        self.x = np.array([0.0, 0.0, 0.2, 0.0, 0.0])  # volatility만 0.2로 초기화
        
        # 공분산 행렬 (5x5)
        self.P = np.eye(5) * 1.0
        self.P[2, 2] = 0.1  # volatility는 더 작은 불확실성
        
        # 시스템 노이즈 (5x5)
        self.Q = np.eye(5) * 0.01
        self.Q[0, 0] = 0.005  # trend는 더 안정적
        self.Q[2, 2] = 0.02   # volatility는 더 변동적
        
        # 측정 노이즈 (5x5)
        self.R = np.eye(5) * 0.1
        self.R[3, 3] = 0.5    # macro_signal은 더 노이즈 많음
        self.R[4, 4] = 0.3    # tech_signal은 중간 노이즈
        
        # 상태 전이 행렬 (5x5)
        self.F = np.eye(5)
        self.F[0, 1] = 0.1    # trend ← momentum
        self.F[1, 0] = 0.05   # momentum ← trend
        self.F[3, 0] = 0.1    # macro_signal ← trend
        self.F[4, 1] = 0.1    # tech_signal ← momentum
        
        # 측정 행렬 (5x5) - 단위행렬 (각 상태를 직접 관측)
        self.H = np.eye(5)
        
        # 성능 모니터링
        self.innovation_history = []
        self.state_history = []
        self.step_count = 0

    def _predict(self) -> None:
        """예측 단계"""
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q

    def _update(self, z: NDArray) -> None:
        """업데이트 단계"""
        # Innovation (예측 오차)
        y = z - self.H @ self.x
        
        # Innovation 공분산
        S = self.H @ self.P @ self.H.T + self.R
        
        # Kalman Gain
        K = self.P @ self.H.T @ np.linalg.inv(S)
        
        # 상태 업데이트
        self.x = self.x + K @ y
        self.P = (np.eye(5) - K @ self.H) @ self.P
        
        # 성능 모니터링
        self.innovation_history.append(y)
        self.state_history.append(self.x.copy())
        self.step_count += 1

    def step(self, z: NDArray) -> None:
        """칼만 필터 한 스텝 실행"""
        self._predict()
        self._update(z)
    
    def get_performance_metrics(self) -> dict:
        """성능 지표 반환"""
        if len(self.innovation_history) < 1:
            return {
                "innovation_mean": [0.0] * 5,
                "innovation_std": [0.0] * 5,
                "state_std": [0.0] * 5,
                "max_innovation": [0.0] * 5,
                "is_diverging": False,
                "step_count": self.step_count,
                "status": "initializing"
            }
        
        innovations = np.array(self.innovation_history)
        states = np.array(self.state_history)
        
        # Innovation 통계
        innovation_mean = np.mean(innovations, axis=0)
        innovation_std = np.std(innovations, axis=0) if len(innovations) > 1 else np.zeros_like(innovation_mean)
        
        # 상태 안정성
        state_std = np.std(states, axis=0) if len(states) > 1 else np.zeros_like(states[0])
        
        # Divergence 감지 (innovation이 너무 크면)
        max_innovation = np.max(np.abs(innovations), axis=0)
        is_diverging = np.any(max_innovation > 5.0)  # 임계값
        
        # 상태 결정: 초기화 중이거나 안정적이거나 발산 중
        if self.step_count < 3:
            status = "initializing"
        elif is_diverging:
            status = "diverging"
        else:
            status = "stable"
        
        return {
            "innovation_mean": innovation_mean.tolist(),
            "innovation_std": innovation_std.tolist(),
            "state_std": state_std.tolist(),
            "max_innovation": max_innovation.tolist(),
            "is_diverging": bool(is_diverging),
            "step_count": self.step_count,
            "status": status
        }
    
    def reset(self) -> None:
        """필터 초기화"""
        self.x = np.array([0.0, 0.0, 0.2, 0.0, 0.0])
        self.P = np.eye(5) * 1.0
        self.P[2, 2] = 0.1
        self.innovation_history = []
        self.state_history = []
        self.step_count = 0

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
            from service.cache.cache_service import CacheService
            
            # ServiceContainer에서 기존 서비스 가져오기
            db_service = ServiceContainer.get_database_service()
            
            # Redis 클라이언트 풀 생성 (기존 설정 사용)
            redis_pool = CacheService._client_pool
            
            self.state_manager = KalmanStateManager(redis_pool, db_service)
            print("[KalmanRegimeFilterTool] Redis + SQL 하이브리드 상태 관리 초기화 완료")
        except Exception as e:
            print(f"[KalmanRegimeFilterTool] 상태 관리 초기화 실패: {e}")
            self.state_manager = None
    
    def require_session(self) -> bool:
        """세션은 선택사항 (fallback 지원)"""
        return False

    # ---------- 정규화 유틸리티 함수들 ----------
    # ❌ 중복 정규화 메서드 제거 - FeaturePipelineTool에서 처리
    # _log1p_normalize, _zscore_normalize 메서드 삭제

    # ---------- 유틸 ----------
    @staticmethod
    def _find_value(data_list, series_id, default=0.0):
        for item in data_list:
            if isinstance(item, dict) and item.get('series_id') == series_id:
                return item.get('latest_value', default)
            if hasattr(item, 'series_id') and getattr(item, 'series_id') == series_id:
                return getattr(item, 'latest_value', default)
        return default

    # ---------- main ----------
    def get_data(self, **kwargs) -> KalmanRegimeFilterActionOutput:
        """
        칼만 필터 기반 시장 체제 감지 + 자동 트레이딩 신호 생성
        
        Returns:
            KalmanRegimeFilterActionOutput: 트레이딩 추천사항
        """
        # SessionAwareTool의 세션 검증 (세션은 선택사항)
        self.validate_session()
        t_start = time.time()
        
        # 1️⃣ kwargs → input class 파싱
        inp = KalmanRegimeFilterInput(**kwargs)
        
        # 🆕 5차원 칼만 필터 전용 Composite 공식 정의
        kalman_composite_formulas = {
            # 거시경제 + 변동성 복합 지표 (trend 추정용)
            "kalman_trend": lambda feats: (
                0.4 * feats.get("GDP", 0.0) + 
                0.3 * feats.get("CPIAUCSL", 0.0) + 
                0.3 * feats.get("VIX", 0.0)
            ),
            # 기술적 + 거시경제 복합 지표 (momentum 추정용)
            "kalman_momentum": lambda feats: (
                0.5 * feats.get("RSI", 0.0) + 
                0.3 * feats.get("MACD", 0.0) + 
                0.2 * feats.get("CPIAUCSL", 0.0)
            ),
            # 변동성 + 환율 복합 지표 (volatility 추정용)
            "kalman_volatility": lambda feats: (
                0.7 * feats.get("VIX", 0.0) + 
                0.3 * feats.get("DEXKOUS", 0.0)
            ),
            # 거시경제 신호 (macro_signal)
            "kalman_macro": lambda feats: (
                0.6 * feats.get("GDP", 0.0) + 
                0.4 * feats.get("CPIAUCSL", 0.0)
            ),
            # 기술적 신호 (tech_signal)
            "kalman_tech": lambda feats: (
                0.6 * feats.get("RSI", 0.0) + 
                0.4 * feats.get("MACD", 0.0)
            )
        }

        # 2️⃣ 완전한 피처 파이프라인 활용 (5차원 칼만 전용 composite 공식 사용)
        from service.llm.AIChat.tool.FeaturePipelineTool import FeaturePipelineTool
        
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
            debug=True
        )

        # 3️⃣ Raw 값과 Normalized 값 분리
        raw_features = pipeline_result["raw"]      # 계산용 (가격, 환율)
        norm_features = pipeline_result["normalized"]  # 신호용 (모델 입력)
        

        
        # Raw 값으로 계산용 데이터 추출
        exchange_rate = raw_features.get("DEXKOUS", 0.00072)
        entry_price = raw_features.get("PRICE", 0.0)

        if inp.exchange_rate.upper() == "KWR":
            inp.account_value *= exchange_rate

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
        rec["combined_signal"] = round(combined_signal, 4)

        # ── 포지션 크기
        risk_dollar = inp.account_value * inp.risk_pct
        pos_size = risk_dollar / (vol * entry_price)
        rec["position_size"] = round(pos_size, 4)

        # ── 레버리지
        target_vol = 0.5
        leverage = min(target_vol / vol, inp.max_leverage)
        if leverage >= inp.max_leverage:
            warning_messages.append(f"Leverage capped at {inp.max_leverage}×")
        rec["leverage"] = round(leverage, 2)

        # ── SL / TP (ATR 기반)
        atr = vol * entry_price
        stop_loss   = entry_price - atr * 1.5
        take_profit = entry_price + atr * 3.0
        rec["stop_loss"]   = round(stop_loss, 2)
        rec["take_profit"] = round(take_profit, 2)

        # ── 리스크 지표
        rec["risk_score"] = round(float(np.trace(cov)), 3)
        rec["market_stability"] = "Stable" if vol < 0.3 else "Unstable"

        # ── 성능 지표 추가
        rec["filter_performance"] = performance_metrics
        rec["state_estimates"] = {
            "trend": round(float(state[0]), 4),
            "momentum": round(float(state[1]), 4),
            "volatility": round(float(state[2]), 4),
            "macro_signal": round(float(state[3]), 4),
            "tech_signal": round(float(state[4]), 4)
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
        summary = f"5차원 칼만 필터 분석 완료 - {signal} 신호, 변동성: {vol:.3f}, 성능: {performance_metrics['status']}, 데이터: {data_status}"
        
        if missing_features:
            rec["data_warnings"] = f"다음 피처들이 기본값으로 대체됨: {missing_features}"
        
        return KalmanRegimeFilterActionOutput(
            summary=summary,
            recommendations=rec,
            start_time=inp.start_date,
            end_time=inp.end_date
        )
