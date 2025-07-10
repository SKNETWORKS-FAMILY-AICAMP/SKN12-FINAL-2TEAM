import asyncio
import aiohttp
import time
import random
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from service.core.logger import Logger
from .external_client import IExternalClient

class CircuitState(Enum):
    CLOSED = "closed"  # 정상 상태
    OPEN = "open"      # 차단 상태 
    HALF_OPEN = "half_open"  # 반개방 상태

@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5      # 실패 임계값
    timeout_seconds: int = 60       # 차단 시간
    success_threshold: int = 2      # 반개방 상태에서 성공 임계값

@dataclass
class ClientMetrics:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0.0
    last_request_time: Optional[float] = None
    circuit_breaker_state: CircuitState = CircuitState.CLOSED
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    circuit_open_time: Optional[float] = None

class HttpExternalClient(IExternalClient):
    """HTTP External API 클라이언트 - Connection Pool, Health Check, Circuit Breaker 포함"""
    
    def __init__(self, api_name: str, api_config, proxy_config=None):
        self.api_name = api_name
        self.api_config = api_config
        self.proxy_config = proxy_config
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Circuit Breaker 설정
        self.circuit_config = CircuitBreakerConfig()
        self.metrics = ClientMetrics()
        
        # Connection Pool 설정
        self._connector_kwargs = {
            "limit": 100,              # 총 연결 수 제한
            "limit_per_host": 30,     # 호스트당 연결 수 제한
            "ttl_dns_cache": 300,     # DNS 캐시 TTL
            "use_dns_cache": True,
            "keepalive_timeout": 60,  # Keep-alive 타임아웃
            "enable_cleanup_closed": True
        }
        
    async def start(self):
        """클라이언트 시작 - 개선된 Connection Pool 설정"""
        if self._session is None:
            # 프록시 설정 병합
            connector_kwargs = self._connector_kwargs.copy()
            if self.proxy_config:
                connector_kwargs['trust_env'] = True
            
            # 타임아웃 설정 (더 세분화)
            timeout = aiohttp.ClientTimeout(
                total=self.api_config.timeout,
                connect=10,      # 연결 타임아웃
                sock_read=30,    # 소켓 읽기 타임아웃
                sock_connect=10  # 소켓 연결 타임아웃
            )
            
            # 기본 헤더 설정
            headers = self.api_config.headers.copy()
            if hasattr(self.api_config, 'api_key') and self.api_config.api_key:
                headers['Authorization'] = f"Bearer {self.api_config.api_key}"
            
            # User-Agent 추가
            headers['User-Agent'] = f"base_server-external-client/{self.api_name}"
            
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers,
                connector=aiohttp.TCPConnector(**connector_kwargs)
            )
            Logger.info(f"HTTP External client started for API: {self.api_name} with enhanced connection pool")
    
    async def close(self):
        """클라이언트 종료"""
        if self._session:
            await self._session.close()
            self._session = None
            Logger.info(f"HTTP External client closed for API: {self.api_name}")
            
        # 최종 메트릭 로깅
        final_metrics = self.get_metrics()
        Logger.info(f"Final metrics for {self.api_name}: {final_metrics}")
    
    async def request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """HTTP 요청"""
        if self._session is None:
            await self.start()
        
        # URL이 상대 경로인 경우 base_url과 결합
        if not url.startswith(('http://', 'https://')):
            url = self.api_config.base_url.rstrip('/') + '/' + url.lstrip('/')
        
        # 프록시 설정
        proxy_url = None
        proxy_auth = None
        if self.proxy_config and self.proxy_config.url:
            proxy_url = self.proxy_config.url
            if self.proxy_config.username and self.proxy_config.password:
                proxy_auth = aiohttp.BasicAuth(
                    self.proxy_config.username, 
                    self.proxy_config.password
                )
        
        # Circuit Breaker 확인
        if not self._can_execute_request():
            return {
                "success": False,
                "error": "Circuit breaker is OPEN",
                "circuit_state": self.metrics.circuit_breaker_state.value
            }
        
        # 메트릭 시작
        start_time = time.time()
        self.metrics.total_requests += 1
        self.metrics.last_request_time = start_time
        
        # 재시도 로직 (Exponential Backoff)
        last_error = None
        max_attempts = self.api_config.retry_count + 1
        
        for attempt in range(max_attempts):
            try:
                async with self._session.request(
                    method=method,
                    url=url,
                    proxy=proxy_url,
                    proxy_auth=proxy_auth,
                    **kwargs
                ) as response:
                    
                    # 응답 데이터 읽기
                    if response.content_type == 'application/json':
                        data = await response.json()
                    else:
                        text = await response.text()
                        data = {"text": text}
                    
                    # 성공 응답
                    if response.status == 200:
                        response_time = time.time() - start_time
                        self._record_success(response_time)
                        Logger.debug(f"HTTP External API success: {self.api_name} {method} {url} ({response_time:.3f}s)")
                        return {
                            "success": True,
                            "status": response.status,
                            "data": data,
                            "response_time": response_time,
                            "attempt": attempt + 1
                        }
                    else:
                        self._record_failure()
                        Logger.warn(f"HTTP External API error: {self.api_name} {method} {url} - Status: {response.status}")
                        return {
                            "success": False,
                            "status": response.status,
                            "error": f"HTTP {response.status}",
                            "data": data,
                            "attempt": attempt + 1
                        }
                        
            except asyncio.TimeoutError as e:
                self._record_failure()
                last_error = f"Timeout: {e}"
                Logger.warn(f"HTTP External API timeout (attempt {attempt + 1}/{max_attempts}): {self.api_name} {method} {url}")
                
            except aiohttp.ClientError as e:
                self._record_failure()
                last_error = f"Client error: {e}"
                Logger.warn(f"HTTP External API client error (attempt {attempt + 1}/{max_attempts}): {self.api_name} {method} {url} - {e}")
                
            except Exception as e:
                self._record_failure()
                last_error = f"Unexpected error: {e}"
                Logger.error(f"HTTP External API unexpected error (attempt {attempt + 1}/{max_attempts}): {self.api_name} {method} {url} - {e}")
            
            # 마지막 시도가 아니면 Exponential Backoff으로 대기
            if attempt < self.api_config.retry_count:
                delay = self._calculate_backoff_delay(attempt)
                Logger.debug(f"Retrying in {delay:.2f}s...")
                await asyncio.sleep(delay)
        
        # 모든 재시도 실패
        self._record_failure()
        total_time = time.time() - start_time
        Logger.error(f"HTTP External API failed after {max_attempts} attempts: {self.api_name} {method} {url} (total: {total_time:.3f}s)")
        return {
            "success": False,
            "error": last_error or "Unknown error",
            "total_attempts": max_attempts,
            "total_time": total_time,
            "circuit_state": self.metrics.circuit_breaker_state.value
        }
    
    async def get(self, url: str, **kwargs) -> Dict[str, Any]:
        """GET 요청"""
        return await self.request("GET", url, **kwargs)
    
    async def post(self, url: str, **kwargs) -> Dict[str, Any]:
        """POST 요청"""
        return await self.request("POST", url, **kwargs)
    
    async def health_check(self) -> Dict[str, Any]:
        """Health Check - 기본 연결 상태 확인"""
        try:
            if self._session is None:
                await self.start()
            
            # 간단한 HEAD 요청으로 연결 상태 확인
            start_time = time.time()
            async with self._session.head(self.api_config.base_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                response_time = time.time() - start_time
                
                return {
                    "healthy": True,
                    "status_code": response.status,
                    "response_time": response_time,
                    "metrics": self.get_metrics()
                }
                
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "metrics": self.get_metrics()
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """클라이언트 메트릭 조회"""
        avg_response_time = 0.0
        if self.metrics.successful_requests > 0:
            avg_response_time = self.metrics.total_response_time / self.metrics.successful_requests
        
        success_rate = 0.0
        if self.metrics.total_requests > 0:
            success_rate = self.metrics.successful_requests / self.metrics.total_requests
        
        return {
            "api_name": self.api_name,
            "total_requests": self.metrics.total_requests,
            "successful_requests": self.metrics.successful_requests,
            "failed_requests": self.metrics.failed_requests,
            "success_rate": success_rate,
            "average_response_time": avg_response_time,
            "circuit_breaker_state": self.metrics.circuit_breaker_state.value,
            "consecutive_failures": self.metrics.consecutive_failures,
            "last_request_time": self.metrics.last_request_time
        }
    
    def reset_metrics(self):
        """메트릭 초기화"""
        self.metrics = ClientMetrics()
        Logger.info(f"Metrics reset for API: {self.api_name}")
    
    # === Circuit Breaker & Metrics 내부 메소드들 ===
    
    def _can_execute_request(self) -> bool:
        """Circuit Breaker - 요청 실행 가능 여부 확인"""
        current_time = time.time()
        
        if self.metrics.circuit_breaker_state == CircuitState.CLOSED:
            return True
        elif self.metrics.circuit_breaker_state == CircuitState.OPEN:
            if (current_time - self.metrics.circuit_open_time) >= self.circuit_config.timeout_seconds:
                self.metrics.circuit_breaker_state = CircuitState.HALF_OPEN
                self.metrics.consecutive_successes = 0
                Logger.info(f"Circuit breaker changed to HALF_OPEN for API: {self.api_name}")
                return True
            return False
        elif self.metrics.circuit_breaker_state == CircuitState.HALF_OPEN:
            return True
        
        return False
    
    def _record_success(self, response_time: float):
        """성공 기록 및 Circuit Breaker 상태 업데이트"""
        self.metrics.successful_requests += 1
        self.metrics.total_response_time += response_time
        self.metrics.consecutive_failures = 0
        
        if self.metrics.circuit_breaker_state == CircuitState.HALF_OPEN:
            self.metrics.consecutive_successes += 1
            if self.metrics.consecutive_successes >= self.circuit_config.success_threshold:
                self.metrics.circuit_breaker_state = CircuitState.CLOSED
                Logger.info(f"Circuit breaker changed to CLOSED for API: {self.api_name}")
    
    def _record_failure(self):
        """실패 기록 및 Circuit Breaker 상태 업데이트"""
        self.metrics.failed_requests += 1
        self.metrics.consecutive_failures += 1
        self.metrics.consecutive_successes = 0
        
        if (self.metrics.circuit_breaker_state == CircuitState.CLOSED and 
            self.metrics.consecutive_failures >= self.circuit_config.failure_threshold):
            self.metrics.circuit_breaker_state = CircuitState.OPEN
            self.metrics.circuit_open_time = time.time()
            Logger.warn(f"Circuit breaker changed to OPEN for API: {self.api_name}")
        elif self.metrics.circuit_breaker_state == CircuitState.HALF_OPEN:
            self.metrics.circuit_breaker_state = CircuitState.OPEN
            self.metrics.circuit_open_time = time.time()
            Logger.warn(f"Circuit breaker changed to OPEN for API: {self.api_name}")
    
    def _calculate_backoff_delay(self, attempt: int) -> float:
        """Exponential Backoff 지연 시간 계산"""
        base_delay = getattr(self.api_config, 'retry_delay', 1.0)
        max_delay = 30.0  # 최대 30초
        
        # 2^attempt * base_delay + jitter
        delay = min(base_delay * (2 ** attempt), max_delay)
        
        # Jitter 추가 (delay의 ±25%)
        jitter = delay * 0.25 * (2 * random.random() - 1)
        return max(0.1, delay + jitter)