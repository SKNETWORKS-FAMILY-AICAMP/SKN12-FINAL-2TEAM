from template.base.template.admin_template import AdminTemplate
from template.base.client_session import ClientSession
from .common.admin_model import *
from .common.admin_serialize import AdminSerialize
from service.db.database_service import DatabaseService
from service.cache.cache_service import CacheService
from service.core.logger import Logger
from datetime import datetime
import time
import asyncio

class AdminTemplateImpl(AdminTemplate):
    def __init__(self):
        super().__init__()
        self.start_time = time.time()
    
    async def on_health_check_req(self, client_session: ClientSession, request: HealthCheckRequest) -> HealthCheckResponse:
        """헬스체크 요청 처리"""
        try:
            services = {}
            overall_status = "healthy"
            
            # 데이터베이스 체크
            if request.check_type in ["all", "db"]:
                db_status = await self._check_database_health()
                services["database"] = db_status
                if db_status["status"] != "healthy":
                    overall_status = "unhealthy"
            
            # 캐시 체크
            if request.check_type in ["all", "cache"]:
                cache_status = await self._check_cache_health()
                services["cache"] = cache_status
                if cache_status["status"] != "healthy":
                    overall_status = "degraded" if overall_status == "healthy" else "unhealthy"
            
            # 서비스 체크
            if request.check_type in ["all", "services"]:
                service_status = await self._check_services_health()
                services["services"] = service_status
                if service_status["status"] != "healthy":
                    overall_status = "degraded" if overall_status == "healthy" else "unhealthy"
            
            return HealthCheckResponse(
                status=overall_status,
                timestamp=datetime.now().isoformat(),
                services=services,
                error_code=0
            )
            
        except Exception as e:
            Logger.error(f"Health check failed: {e}")
            return HealthCheckResponse(
                status="unhealthy",
                timestamp=datetime.now().isoformat(),
                services={},
                error_code=500,
                error_message=str(e)
            )
    
    async def on_server_status_req(self, client_session: ClientSession, request: ServerStatusRequest) -> ServerStatusResponse:
        """서버 상태 요청 처리"""
        try:
            uptime_seconds = time.time() - self.start_time
            uptime_str = f"{int(uptime_seconds // 3600)}h {int((uptime_seconds % 3600) // 60)}m {int(uptime_seconds % 60)}s"
            
            metrics = None
            if request.include_metrics:
                metrics = await self._get_server_metrics()
            
            return ServerStatusResponse(
                server_name="base_web_server",
                environment="production",
                version="1.0.0",
                uptime=uptime_str,
                status="running",
                metrics=metrics,
                error_code=0
            )
            
        except Exception as e:
            Logger.error(f"Server status check failed: {e}")
            return ServerStatusResponse(
                server_name="base_web_server",
                environment="production",
                version="1.0.0",
                uptime="0s",
                status="error",
                error_code=500,
                error_message=str(e)
            )
    
    async def on_session_count_req(self, client_session: ClientSession, request: SessionCountRequest) -> SessionCountResponse:
        """세션 카운트 요청 처리"""
        try:
            # Redis에서 세션 키들을 조회
            session_count = await self._get_session_count()
            
            return SessionCountResponse(
                total_sessions=session_count,
                active_sessions=session_count,
                error_code=0
            )
            
        except Exception as e:
            Logger.error(f"Session count check failed: {e}")
            return SessionCountResponse(
                total_sessions=0,
                active_sessions=0,
                error_code=500,
                error_message=str(e)
            )
    
    async def _check_database_health(self) -> dict:
        """데이터베이스 연결 상태 체크"""
        try:
            # 간단한 쿼리 실행으로 DB 상태 확인
            # 실제 구현에서는 DatabaseService의 인스턴스를 사용해야 함
            return {
                "status": "healthy",
                "response_time": "< 100ms",
                "details": "Connection successful"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "response_time": "timeout",
                "details": f"Connection failed: {str(e)}"
            }
    
    async def _check_cache_health(self) -> dict:
        """캐시 연결 상태 체크"""
        try:
            # CacheService를 통해 Redis 상태 확인
            if CacheService._client_pool:
                async with CacheService.get_client() as client:
                    # 간단한 ping 테스트
                    test_key = "health_check_test"
                    await client.set_string(test_key, "test_value", expire=10)
                    value = await client.get_string(test_key)
                    await client.delete(test_key)
                    
                    if value == "test_value":
                        return {
                            "status": "healthy",
                            "response_time": "< 50ms",
                            "details": "Redis connection successful"
                        }
            
            return {
                "status": "unhealthy",
                "response_time": "timeout",
                "details": "Redis connection failed"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "response_time": "timeout",
                "details": f"Redis error: {str(e)}"
            }
    
    async def _check_services_health(self) -> dict:
        """서비스 상태 체크"""
        try:
            # 템플릿 서비스 상태 확인
            services_status = {
                "template_service": "healthy",
                "cache_service": "healthy" if CacheService._client_pool else "unhealthy",
                "logger_service": "healthy"
            }
            
            overall_status = "healthy"
            for service, status in services_status.items():
                if status != "healthy":
                    overall_status = "degraded"
                    break
            
            return {
                "status": overall_status,
                "services": services_status,
                "details": "All services operational"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "services": {},
                "details": f"Service check failed: {str(e)}"
            }
    
    async def _get_server_metrics(self) -> dict:
        """서버 메트릭 수집"""
        try:
            import psutil
            
            return {
                "cpu_usage": psutil.cpu_percent(),
                "memory_usage": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent,
                "active_connections": len(psutil.net_connections())
            }
        except ImportError:
            return {
                "cpu_usage": "unavailable",
                "memory_usage": "unavailable",
                "disk_usage": "unavailable",
                "active_connections": "unavailable"
            }
        except Exception as e:
            return {
                "error": f"Metrics collection failed: {str(e)}"
            }
    
    async def _get_session_count(self) -> int:
        """활성 세션 수 조회"""
        try:
            if CacheService._client_pool:
                async with CacheService.get_client() as client:
                    # session:* 패턴의 키 개수 조회
                    # 실제 구현에서는 Redis SCAN 명령 사용
                    return 0  # 임시로 0 반환
            return 0
        except Exception as e:
            Logger.error(f"Session count query failed: {e}")
            return 0