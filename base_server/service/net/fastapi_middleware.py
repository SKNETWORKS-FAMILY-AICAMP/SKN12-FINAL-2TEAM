"""
FastAPI 미들웨어 서비스
- 기존 Service 패턴 활용 (정적 클래스, init(), shutdown(), is_initialized())
- Logger 및 NetConfig 활용
- CLAUDE.md 패턴 준수: 안전한 개선 + 기존 로직 유지
"""

import asyncio
import time
from typing import Optional, Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from service.core.logger import Logger
from service.net.net_config import NetConfig, FastApiConfig


class RequestTimeoutMiddleware(BaseHTTPMiddleware):
    """
    FastAPI 요청 타임아웃 미들웨어
    
    🎯 목적:
    - HTTP 요청 전체 처리 시간 제한
    - LLM API 호출 등 긴 작업 시 클라이언트 hang up 방지
    - 타임아웃 발생 시 504 Gateway Timeout 응답
    
    🔧 CLAUDE.md 패턴 준수:
    - 기존 로직 유지 + 예외 처리 강화
    - Logger 활용으로 기존 로깅 패턴 유지
    """
    
    def __init__(self, app, timeout_seconds: int = 300):
        super().__init__(app)
        self.timeout_seconds = timeout_seconds
        Logger.info(f"🕒 RequestTimeoutMiddleware 초기화: {timeout_seconds}초 타임아웃")

    async def dispatch(self, request: Request, call_next):
        try:
            # ✅ 기존 로직 유지: 비동기 타임아웃 적용
            response = await asyncio.wait_for(
                call_next(request), 
                timeout=self.timeout_seconds
            )
            return response
            
        except asyncio.TimeoutError:
            # ✅ 예외 처리 강화: 상세 로깅 + 적절한 HTTP 응답
            Logger.warn(f"⏰ 요청 타임아웃 발생 ({self.timeout_seconds}초): {request.method} {request.url.path}")
            return Response(
                content=f"Request timeout after {self.timeout_seconds} seconds",
                status_code=504,
                headers={
                    "Content-Type": "text/plain",
                    "X-Timeout": str(self.timeout_seconds)
                }
            )
        except Exception as e:
            # ✅ 로깅 개선: 기존 Logger 패턴 활용
            Logger.error(f"❌ RequestTimeoutMiddleware 처리 중 오류: {e}")
            return Response(
                content="Internal server error during timeout handling",
                status_code=500,
                headers={"Content-Type": "text/plain"}
            )


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI 요청 크기 제한 미들웨어
    
    🎯 목적:
    - HTTP 요청 본문 크기 제한으로 시스템 보호
    - 대용량 업로드 공격 방지
    - 메모리 사용량 제어
    """
    
    def __init__(self, app, max_size: int = 16777216):  # 16MB 기본값
        super().__init__(app)
        self.max_size = max_size
        Logger.info(f"📏 RequestSizeLimitMiddleware 초기화: 최대 {max_size} bytes ({max_size/1024/1024:.1f}MB)")

    async def dispatch(self, request: Request, call_next):
        try:
            # Content-Length 헤더 확인
            content_length = request.headers.get("content-length")
            
            if content_length:
                content_length_int = int(content_length)
                if content_length_int > self.max_size:
                    Logger.warn(f"📦 요청 크기 제한 초과: {content_length_int} > {self.max_size} bytes")
                    return Response(
                        content=f"Request too large. Max size: {self.max_size} bytes ({self.max_size/1024/1024:.1f}MB)",
                        status_code=413,
                        headers={
                            "Content-Type": "text/plain",
                            "X-Max-Size": str(self.max_size)
                        }
                    )
            
            return await call_next(request)
            
        except ValueError as e:
            # ✅ 예외 처리 강화: Content-Length 파싱 오류 대응
            Logger.warn(f"⚠️ Content-Length 파싱 오류: {e}")
            return await call_next(request)
        except Exception as e:
            Logger.error(f"❌ RequestSizeLimitMiddleware 오류: {e}")
            return await call_next(request)


class SlowRequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    느린 요청 로깅 미들웨어
    
    🎯 목적:
    - 설정된 임계값보다 느린 요청 감지 및 로깅
    - 응답 시간 헤더 추가로 성능 모니터링 지원
    - 시스템 성능 병목 지점 파악
    """
    
    def __init__(self, app, threshold: float = 5.0, log_all_requests: bool = False):
        super().__init__(app)
        self.threshold = threshold
        self.log_all_requests = log_all_requests
        Logger.info(f"🐌 SlowRequestLoggingMiddleware 초기화: {threshold}초 임계값, 전체 로깅: {log_all_requests}")

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # ✅ 새 함수 추가: 응답 시간 헤더 추가 (기존 로직 영향 없음)
            response.headers["X-Process-Time"] = f"{process_time:.3f}"
            
            # ✅ 로깅 개선: 기존 Logger 패턴 활용
            if process_time > self.threshold:
                Logger.warn(f"🐌 느린 요청 감지: {request.method} {request.url.path} - {process_time:.2f}초")
            elif self.log_all_requests:
                Logger.debug(f"📊 요청 처리 완료: {request.method} {request.url.path} - {process_time:.3f}초")
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            Logger.error(f"❌ 요청 처리 중 오류 ({process_time:.3f}초): {request.method} {request.url.path} - {e}")
            raise


class FastAPIMiddlewareService:
    """
    FastAPI 미들웨어 관리 서비스
    
    🏗️ 기존 Service 패턴 준수:
    - 정적 클래스 구조
    - init(), shutdown(), is_initialized() 메서드
    - ServiceContainer와 연동 가능한 구조
    
    🎯 CLAUDE.md 원칙 준수:
    - 안전한 개선: 기존 시스템에 영향 없이 미들웨어 추가
    - 기존 패턴 활용: Logger, NetConfig 등 기존 컴포넌트 활용
    - 예외 처리 강화: 모든 단계에서 예외 상황 대응
    """
    
    _initialized: bool = False
    _config: Optional[Dict[str, Any]] = None
    _metrics: Dict[str, Any] = {}
    
    @classmethod
    def init(cls, net_config: NetConfig) -> bool:
        """
        FastAPI 미들웨어 서비스 초기화
        
        Args:
            net_config: NetConfig 객체 (fastApiConfig 포함)
        
        Returns:
            bool: 초기화 성공 여부
        """
        try:
            cls._config = net_config.fastApiConfig.dict() if net_config.fastApiConfig else {}
            cls._metrics = {
                "total_requests": 0,
                "timeout_count": 0,
                "size_limit_exceeded": 0,
                "slow_requests": 0
            }
            
            cls._initialized = True
            Logger.info("✅ FastAPIMiddlewareService 초기화 완료")
            return True
            
        except Exception as e:
            Logger.error(f"❌ FastAPIMiddlewareService 초기화 실패: {e}")
            return False
    
    @classmethod
    def shutdown(cls) -> bool:
        """
        FastAPI 미들웨어 서비스 종료
        
        Returns:
            bool: 종료 성공 여부
        """
        try:
            if cls._initialized:
                # 메트릭 정리
                Logger.info(f"📊 FastAPI 미들웨어 최종 메트릭: {cls._metrics}")
                cls._metrics.clear()
                cls._config = None
                cls._initialized = False
                Logger.info("✅ FastAPIMiddlewareService 종료 완료")
            return True
            
        except Exception as e:
            Logger.error(f"❌ FastAPIMiddlewareService 종료 실패: {e}")
            return False
    
    @classmethod
    def is_initialized(cls) -> bool:
        """
        초기화 상태 확인
        
        Returns:
            bool: 초기화 여부
        """
        return cls._initialized
    
    @classmethod
    def setup_middlewares(cls, app, net_config: NetConfig):
        """
        설정에 따라 미들웨어를 FastAPI 앱에 추가
        
        🔧 CLAUDE.md 패턴 준수:
        - 기존 NetConfig 활용
        - 안전한 미들웨어 추가 (기존 로직 영향 없음)
        - 상세한 로깅으로 디버깅 지원
        
        Args:
            app: FastAPI 앱 인스턴스
            net_config: NetConfig 객체
        """
        if not cls._initialized:
            Logger.warn("⚠️ FastAPIMiddlewareService가 초기화되지 않았습니다")
            return False
        
        try:
            Logger.info("🔧 FastAPI 미들웨어 설정 시작")
            
            # 기존 NetConfig에서 설정 읽기 (CLAUDE.md: 기존 패턴 활용)
            fastapi_config = getattr(net_config, 'fastApiConfig', {})
            
            # 기본값 설정 (CLAUDE.md: 기본값으로 기존 동작 보장)
            if isinstance(fastapi_config, dict):
                enable_timeout = fastapi_config.get("enable_request_timeout", True)
                enable_size_limit = fastapi_config.get("enable_size_limit", True) 
                enable_slow_logging = fastapi_config.get("enable_slow_request_logging", True)
                
                timeout_seconds = fastapi_config.get("request_timeout", 300)
                max_size = fastapi_config.get("max_request_size", 16777216)
                slow_threshold = fastapi_config.get("slow_request_threshold", 5.0)
            else:
                # NetConfig 기본값 활용
                enable_timeout = True
                enable_size_limit = True
                enable_slow_logging = True
                
                timeout_seconds = getattr(net_config, 'timeout_keep_alive', 300)
                max_size = 16777216  # 16MB
                slow_threshold = 5.0
            
            # 1. 느린 요청 로깅 미들웨어 (가장 바깥쪽)
            if enable_slow_logging:
                app.add_middleware(
                    SlowRequestLoggingMiddleware,
                    threshold=slow_threshold,
                    log_all_requests=False  # 운영 환경 고려
                )
                Logger.info("✅ SlowRequestLoggingMiddleware 추가됨")
            
            # 2. 요청 크기 제한 미들웨어
            if enable_size_limit:
                app.add_middleware(
                    RequestSizeLimitMiddleware,
                    max_size=max_size
                )
                Logger.info("✅ RequestSizeLimitMiddleware 추가됨")
            
            # 3. 요청 타임아웃 미들웨어 (가장 안쪽)
            if enable_timeout:
                app.add_middleware(
                    RequestTimeoutMiddleware,
                    timeout_seconds=timeout_seconds
                )
                Logger.info("✅ RequestTimeoutMiddleware 추가됨")
            
            Logger.info("🎉 FastAPI 미들웨어 설정 완료")
            return True
            
        except Exception as e:
            Logger.error(f"❌ FastAPI 미들웨어 설정 실패: {e}")
            return False
    
    @classmethod
    def get_metrics(cls) -> Dict[str, Any]:
        """
        현재 메트릭 반환
        
        Returns:
            Dict[str, Any]: 메트릭 딕셔너리
        """
        if not cls._initialized:
            return {}
        return cls._metrics.copy()
    
    @classmethod
    def health_check(cls) -> Dict[str, Any]:
        """
        서비스 상태 확인 (CLAUDE.md: ServiceMonitor와 연동 가능)
        
        Returns:
            Dict[str, Any]: 헬스체크 결과
        """
        return {
            "service_name": "FastAPIMiddlewareService",
            "initialized": cls._initialized,
            "healthy": cls._initialized,
            "metrics": cls.get_metrics()
        }