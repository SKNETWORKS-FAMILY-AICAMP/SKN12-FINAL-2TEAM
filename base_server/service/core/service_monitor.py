import asyncio
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
from service.core.logger import Logger
from service.cache.cache_service import CacheService
from service.db.database_service import DatabaseService
from service.service_container import ServiceContainer
from service.lock.lock_service import LockService
from service.scheduler.scheduler_service import SchedulerService
from service.queue.queue_service import QueueService

class ServiceStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class ServiceHealth:
    name: str
    status: ServiceStatus
    last_check: datetime
    response_time_ms: float
    error_message: Optional[str] = None
    consecutive_failures: int = 0
    last_success: Optional[datetime] = None

class ServiceMonitor:
    """
    런타임 서비스 상태 모니터링 시스템
    - 기존 AdminTemplate의 health check 패턴 활용
    - Circuit Breaker 패턴으로 연쇄 장애 방지
    - 자동 복구 및 알림 기능
    """
    
    def __init__(self):
        self._service_health: Dict[str, ServiceHealth] = {}
        self._monitoring_active = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._check_interval = 30  # 30초마다 체크
        self._failure_threshold = 3  # 3회 연속 실패시 circuit open
        self._recovery_timeout = 300  # 5분 후 circuit half-open
        
    async def start_monitoring(self):
        """모니터링 시작"""
        if self._monitoring_active:
            Logger.warn("Service monitoring already active")
            return
            
        self._monitoring_active = True
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        Logger.info("Service monitoring started")
        
    async def stop_monitoring(self):
        """모니터링 중지"""
        self._monitoring_active = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        Logger.info("Service monitoring stopped")
        
    async def _monitoring_loop(self):
        """모니터링 루프"""
        while self._monitoring_active:
            try:
                await self._check_all_services()
                await self._handle_unhealthy_services()
                await asyncio.sleep(self._check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                Logger.error(f"Service monitoring error: {e}")
                await asyncio.sleep(5)  # 오류 시 5초 후 재시도
                
    async def _check_all_services(self):
        """모든 서비스 상태 체크"""
        checks = [
            ("database", self._check_database),
            ("cache", self._check_cache),
            ("lock", self._check_lock_service),
            ("scheduler", self._check_scheduler),
            ("queue", self._check_queue_service)
        ]
        
        for service_name, check_func in checks:
            try:
                await check_func(service_name)
            except Exception as e:
                self._record_failure(service_name, str(e))
                
    async def _check_database(self, service_name: str):
        """데이터베이스 상태 체크 (AdminTemplate 패턴 사용)"""
        start_time = time.time()
        
        try:
            db_service = ServiceContainer.get_database_service()
            if not db_service:
                raise Exception("Database service not available")
                
            result = await db_service.execute_global_query("SELECT 1 as monitor_check", ())
            response_time = (time.time() - start_time) * 1000
            
            if result:
                self._record_success(service_name, response_time)
            else:
                raise Exception("Database query returned no result")
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self._record_failure(service_name, str(e), response_time)
            
    async def _check_cache(self, service_name: str):
        """캐시 상태 체크 (AdminTemplate 패턴 사용)"""
        start_time = time.time()
        
        try:
            if not CacheService.is_initialized():
                raise Exception("Cache service not initialized")
                
            cache_client = CacheService.get_redis_client()
            async with cache_client as client:
                test_key = "monitor_health_check"
                test_value = f"test_{int(time.time())}"
                
                await client.set_string(test_key, test_value, expire=10)
                retrieved_value = await client.get_string(test_key)
                await client.delete(test_key)
                
                response_time = (time.time() - start_time) * 1000
                
                if retrieved_value == test_value:
                    self._record_success(service_name, response_time)
                else:
                    raise Exception("Cache test value mismatch")
                    
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self._record_failure(service_name, str(e), response_time)
            
    async def _check_lock_service(self, service_name: str):
        """Lock 서비스 상태 체크"""
        start_time = time.time()
        
        try:
            if not LockService.is_initialized():
                self._record_success(service_name, 0, ServiceStatus.DEGRADED)
                return
                
            test_lock = "monitor_lock_test"
            token = await LockService.acquire(test_lock, ttl=5, timeout=1)
            response_time = (time.time() - start_time) * 1000
            
            if token:
                await LockService.release(test_lock, token)
                self._record_success(service_name, response_time)
            else:
                raise Exception("Failed to acquire test lock")
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self._record_failure(service_name, str(e), response_time)
            
    async def _check_scheduler(self, service_name: str):
        """Scheduler 서비스 상태 체크"""
        start_time = time.time()
        
        try:
            if not SchedulerService.is_initialized():
                self._record_success(service_name, 0, ServiceStatus.DEGRADED)
                return
                
            jobs_status = SchedulerService.get_all_jobs_status()
            response_time = (time.time() - start_time) * 1000
            self._record_success(service_name, response_time)
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self._record_failure(service_name, str(e), response_time)
            
    async def _check_queue_service(self, service_name: str):
        """Queue 서비스 상태 체크"""
        start_time = time.time()
        
        try:
            if not (hasattr(QueueService, '_initialized') and QueueService._initialized):
                self._record_success(service_name, 0, ServiceStatus.DEGRADED)
                return
                
            queue_service = QueueService.get_instance()
            stats = queue_service.get_stats()
            response_time = (time.time() - start_time) * 1000
            self._record_success(service_name, response_time)
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self._record_failure(service_name, str(e), response_time)
            
    def _record_success(self, service_name: str, response_time_ms: float, status: ServiceStatus = ServiceStatus.HEALTHY):
        """성공 기록"""
        now = datetime.now()
        if service_name not in self._service_health:
            self._service_health[service_name] = ServiceHealth(
                name=service_name,
                status=status,
                last_check=now,
                response_time_ms=response_time_ms,
                consecutive_failures=0,
                last_success=now
            )
        else:
            health = self._service_health[service_name]
            health.status = status
            health.last_check = now
            health.response_time_ms = response_time_ms
            health.error_message = None
            health.consecutive_failures = 0
            health.last_success = now
            
    def _record_failure(self, service_name: str, error_message: str, response_time_ms: float = 0):
        """실패 기록"""
        now = datetime.now()
        if service_name not in self._service_health:
            self._service_health[service_name] = ServiceHealth(
                name=service_name,
                status=ServiceStatus.UNHEALTHY,
                last_check=now,
                response_time_ms=response_time_ms,
                error_message=error_message,
                consecutive_failures=1
            )
        else:
            health = self._service_health[service_name]
            health.status = ServiceStatus.UNHEALTHY
            health.last_check = now
            health.response_time_ms = response_time_ms
            health.error_message = error_message
            health.consecutive_failures += 1
            
        Logger.warn(f"Service {service_name} health check failed: {error_message}")
        
    async def _handle_unhealthy_services(self):
        """비정상 서비스 처리 (Circuit Breaker 패턴)"""
        for service_name, health in self._service_health.items():
            if health.consecutive_failures >= self._failure_threshold:
                await self._handle_circuit_breaker(service_name, health)
                
    async def _handle_circuit_breaker(self, service_name: str, health: ServiceHealth):
        """Circuit Breaker 처리"""
        if health.status == ServiceStatus.UNHEALTHY:
            Logger.error(f"Service {service_name} circuit breaker activated - {health.consecutive_failures} consecutive failures")
            
            # 자동 복구 시도 (5분 후)
            if health.last_success and (datetime.now() - health.last_success).seconds > self._recovery_timeout:
                Logger.info(f"Attempting automatic recovery for service {service_name}")
                # 여기서 실제 복구 로직을 추가할 수 있음
                
    def get_all_service_health(self) -> Dict[str, ServiceHealth]:
        """모든 서비스 상태 반환"""
        return self._service_health.copy()
        
    def get_service_health(self, service_name: str) -> Optional[ServiceHealth]:
        """특정 서비스 상태 반환"""
        return self._service_health.get(service_name)
        
    def get_overall_status(self) -> ServiceStatus:
        """전체 시스템 상태 반환"""
        if not self._service_health:
            return ServiceStatus.UNKNOWN
            
        statuses = [health.status for health in self._service_health.values()]
        
        if ServiceStatus.UNHEALTHY in statuses:
            return ServiceStatus.UNHEALTHY
        elif ServiceStatus.DEGRADED in statuses:
            return ServiceStatus.DEGRADED
        else:
            return ServiceStatus.HEALTHY
            
    def get_health_summary(self) -> Dict[str, Any]:
        """상태 요약 반환"""
        total_services = len(self._service_health)
        healthy_count = sum(1 for h in self._service_health.values() if h.status == ServiceStatus.HEALTHY)
        degraded_count = sum(1 for h in self._service_health.values() if h.status == ServiceStatus.DEGRADED)
        unhealthy_count = sum(1 for h in self._service_health.values() if h.status == ServiceStatus.UNHEALTHY)
        
        return {
            "overall_status": self.get_overall_status().value,
            "total_services": total_services,
            "healthy": healthy_count,
            "degraded": degraded_count,
            "unhealthy": unhealthy_count,
            "monitoring_active": self._monitoring_active,
            "last_check": max([h.last_check for h in self._service_health.values()]) if self._service_health else None
        }

# 글로벌 모니터 인스턴스
service_monitor = ServiceMonitor()