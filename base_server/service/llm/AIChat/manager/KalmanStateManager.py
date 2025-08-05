from __future__ import annotations

import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
import numpy as np
from numpy.typing import NDArray

from service.llm.AIChat.manager.KalmanRegimeFilterCore import KalmanRegimeFilterCore

__all__ = ["KalmanStateManager"]

class KalmanStateManager:
    """
    Redis + SQL 하이브리드 칼만 필터 상태 관리
    
    Redis: 실시간 상태 저장 (빠른 접근)
    SQL: 이력 데이터 저장 (분석용, 복원용)
    """
    
    def __init__(self, redis_pool, db_service):
        self.redis_pool = redis_pool
        self.db = db_service
        self.ttl_seconds = 3600  # Redis TTL 1시간
        self.last_save_times = {}  # 마지막 SQL 저장 시간 추적
        
    def _get_redis_key(self, ticker: str, account_db_key: int, field: str) -> str:
        """Redis 키 생성"""
        return f"kalman:{ticker}:{account_db_key}:{field}"
    
    async def get_filter(self, ticker: str, account_db_key: int) -> KalmanRegimeFilterCore:
        """
        Redis에서 상태 로드하거나 새로 생성
        
        Returns:
            KalmanRegimeFilterCore: 복원된 또는 새로 생성된 필터 인스턴스
        """
        # 1. Redis에서 시도
        filter_instance = await self._restore_from_redis(ticker, account_db_key)
        
        if filter_instance:
            print(f"[KalmanStateManager] Redis에서 복원: {ticker} (step_count: {filter_instance.step_count})")
            return filter_instance
        
        # 2. Redis에 없으면 SQL에서 복원 시도
        filter_instance = await self._restore_from_sql(ticker, account_db_key)
        
        if filter_instance:
            print(f"[KalmanStateManager] SQL에서 복원: {ticker} (step_count: {filter_instance.step_count})")
            # SQL에서 복원 후 Redis에 저장
            await self.save_state(ticker, account_db_key, filter_instance)
            return filter_instance
        
        # 3. SQL에도 없으면 Rule-Based 초기화
        print(f"[KalmanStateManager] Rule-Based 초기화: {ticker}")
        return await self._initialize_with_rules(ticker, account_db_key)
    
    async def save_state(self, ticker: str, account_db_key: int, filter_instance: KalmanRegimeFilterCore) -> None:
        """
        Redis에 상태 저장
        
        Args:
            ticker: 종목 코드
            account_db_key: 사용자 계정 키
            filter_instance: 칼만 필터 인스턴스
        """
        try:
            # JSON 직렬화
            state_json = json.dumps(filter_instance.x.tolist())
            cov_json = json.dumps(filter_instance.P.tolist())
            performance_json = json.dumps(filter_instance.get_performance_metrics())
            
            # Redis에 저장 (TTL 설정)
            async with self.redis_pool.new() as redis_client:
                await redis_client.set_string(self._get_redis_key(ticker, account_db_key, "x"), 
                                            state_json, expire=self.ttl_seconds)
                await redis_client.set_string(self._get_redis_key(ticker, account_db_key, "P"), 
                                            cov_json, expire=self.ttl_seconds)
                await redis_client.set_string(self._get_redis_key(ticker, account_db_key, "step_count"), 
                                            str(filter_instance.step_count), expire=self.ttl_seconds)
                await redis_client.set_string(self._get_redis_key(ticker, account_db_key, "last_update"), 
                                            datetime.now().isoformat(), expire=self.ttl_seconds)
                await redis_client.set_string(self._get_redis_key(ticker, account_db_key, "performance"), 
                                            performance_json, expire=self.ttl_seconds)
            
        except Exception as e:
            print(f"[KalmanStateManager] Redis 저장 실패: {ticker}, 에러: {e}")
    
    async def save_history(self, ticker: str, account_db_key: int, filter_instance: KalmanRegimeFilterCore,
                          trading_signal: str, market_data: Dict[str, Any]) -> None:
        """
        SQL에 이력 저장 (주기적)
        
        Args:
            ticker: 종목 코드
            account_db_key: 사용자 계정 키
            filter_instance: 칼만 필터 인스턴스
            trading_signal: 생성된 트레이딩 신호
            market_data: 시장 데이터 스냅샷
        """
        try:
            # JSON 직렬화
            state_json = json.dumps(filter_instance.x.tolist())
            cov_json = json.dumps(filter_instance.P.tolist())
            market_json = json.dumps(market_data)
            performance_json = json.dumps(filter_instance.get_performance_metrics())
            
            # 프로시저 호출
            result = await self.db.call_stored_procedure(
                "fp_kalman_history_insert",
                (ticker, account_db_key, datetime.now(),
                 state_json, cov_json, filter_instance.step_count,
                 trading_signal, market_json, performance_json)
            )
            
            if result and result[0] and result[0].get('result') == 'SUCCESS':
                print(f"[KalmanStateManager] 이력 저장 성공: {ticker} (idx: {result[0].get('idx')})")
                # 성공적으로 저장되면 마지막 저장 시간 업데이트
                key = f"{ticker}:{account_db_key}"
                self.last_save_times[key] = time.time()
            else:
                print(f"[KalmanStateManager] 이력 저장 실패: {ticker}")
                
        except Exception as e:
            print(f"[KalmanStateManager] SQL 이력 저장 실패: {ticker}, 에러: {e}")
    
    async def _restore_from_redis(self, ticker: str, account_db_key: int) -> Optional[KalmanRegimeFilterCore]:
        """Redis에서 상태 복원"""
        try:
            # Redis에서 데이터 조회
            async with self.redis_pool.new() as redis_client:
                state_data = await redis_client.get_string(self._get_redis_key(ticker, account_db_key, "x"))
                cov_data = await redis_client.get_string(self._get_redis_key(ticker, account_db_key, "P"))
                step_count_data = await redis_client.get_string(self._get_redis_key(ticker, account_db_key, "step_count"))
            
            if not all([state_data, cov_data, step_count_data]):
                return None
            
            # JSON 역직렬화
            state_vector = np.array(json.loads(state_data))
            cov_matrix = np.array(json.loads(cov_data))
            step_count = int(step_count_data)
            
            # 필터 인스턴스 생성 및 복원
            filter_instance = KalmanRegimeFilterCore()
            filter_instance.x = state_vector
            filter_instance.P = cov_matrix
            filter_instance.step_count = step_count
            
            return filter_instance
            
        except Exception as e:
            print(f"[KalmanStateManager] Redis 복원 실패: {ticker}, 에러: {e}")
            return None
    
    async def _restore_from_sql(self, ticker: str, account_db_key: int) -> Optional[KalmanRegimeFilterCore]:
        """SQL에서 최신 상태 복원"""
        try:
            # 프로시저 호출
            result = await self.db.call_stored_procedure(
                "fp_kalman_latest_state_get",
                (ticker, account_db_key)
            )
            
            if not result or not result[0]:
                return None
            
            row = result[0]
            
            # JSON 역직렬화
            state_vector = np.array(json.loads(row['state_vector_x']))
            cov_matrix = np.array(json.loads(row['covariance_matrix_p']))
            step_count = int(row['step_count'])
            
            # 필터 인스턴스 생성 및 복원
            filter_instance = KalmanRegimeFilterCore()
            filter_instance.x = state_vector
            filter_instance.P = cov_matrix
            filter_instance.step_count = step_count
            
            return filter_instance
            
        except Exception as e:
            print(f"[KalmanStateManager] SQL 복원 실패: {ticker}, 에러: {e}")
            return None
    
    async def get_history(self, ticker: str, account_db_key: int, 
                         start_date: datetime, end_date: datetime,
                         limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        칼만 필터 이력 조회 (분석용)
        
        Args:
            ticker: 종목 코드
            account_db_key: 사용자 계정 키
            start_date: 시작 날짜
            end_date: 종료 날짜
            limit: 조회 개수
            offset: 오프셋
            
        Returns:
            List[Dict[str, Any]]: 이력 데이터 리스트
        """
        try:
            result = await self.db.call_stored_procedure(
                "fp_kalman_history_get",
                (ticker, account_db_key, start_date, end_date, limit, offset)
            )
            
            if result:
                return [dict(row) for row in result]
            return []
            
        except Exception as e:
            print(f"[KalmanStateManager] 이력 조회 실패: {ticker}, 에러: {e}")
            return []
    
    def should_save_to_sql(self, ticker: str, account_db_key: int, min_interval_minutes: int = 1) -> bool:
        """
        SQL 저장 여부 결정 (시간 기반)
        
        Args:
            ticker: 종목 코드
            account_db_key: 사용자 계정 키
            min_interval_minutes: 최소 저장 간격 (분)
            
        Returns:
            bool: 저장 여부
        """
        key = f"{ticker}:{account_db_key}"
        last_save_time = self.last_save_times.get(key, 0)
        current_time = time.time()
        
        # 마지막 저장으로부터 min_interval_minutes 이상 지났으면 저장
        return (current_time - last_save_time) >= (min_interval_minutes * 60)
    
    async def clear_state(self, ticker: str, account_db_key: int) -> None:
        """Redis에서 상태 삭제"""
        try:
            async with self.redis_pool.new() as redis_client:
                await redis_client.delete(self._get_redis_key(ticker, account_db_key, "x"))
                await redis_client.delete(self._get_redis_key(ticker, account_db_key, "P"))
                await redis_client.delete(self._get_redis_key(ticker, account_db_key, "step_count"))
                await redis_client.delete(self._get_redis_key(ticker, account_db_key, "last_update"))
                await redis_client.delete(self._get_redis_key(ticker, account_db_key, "performance"))
            
            print(f"[KalmanStateManager] 상태 삭제 완료: {ticker}")
            
        except Exception as e:
            print(f"[KalmanStateManager] 상태 삭제 실패: {ticker}, 에러: {e}")
    
    async def _initialize_with_rules(self, ticker: str, account_db_key: int) -> KalmanRegimeFilterCore:
        """Rule-Based 초기화"""
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
            
            # Redis에 초기화된 상태 저장
            await self.save_state(ticker, account_db_key, filter_instance)
            
            print(f"[KalmanStateManager] Rule-Based 초기화 완료: {ticker}")
            return filter_instance
            
        except Exception as e:
            print(f"[KalmanStateManager] Rule-Based 초기화 실패: {ticker}, 에러: {e}")
            # 실패 시 기본 필터 반환
            return KalmanRegimeFilterCore()
    
    async def get_state_info(self, ticker: str, account_db_key: int) -> Optional[Dict[str, Any]]:
        """Redis에서 상태 정보 조회"""
        try:
            async with self.redis_pool.new() as redis_client:
                last_update = await redis_client.get_string(self._get_redis_key(ticker, account_db_key, "last_update"))
                step_count = await redis_client.get_string(self._get_redis_key(ticker, account_db_key, "step_count"))
                performance = await redis_client.get_string(self._get_redis_key(ticker, account_db_key, "performance"))
            
            if not all([last_update, step_count]):
                return None
            
            return {
                "ticker": ticker,
                "account_db_key": account_db_key,
                "last_update": last_update,
                "step_count": int(step_count) if step_count else 0,
                "performance": json.loads(performance) if performance else None
            }
            
        except Exception as e:
            print(f"[KalmanStateManager] 상태 정보 조회 실패: {ticker}, 에러: {e}")
            return None 