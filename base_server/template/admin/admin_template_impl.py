from template.base.template.admin_template import AdminTemplate
from template.base.client_session import ClientSession
from .common.admin_model import (
    HealthCheckRequest, HealthCheckResponse, ServerStatusRequest, ServerStatusResponse,
    SessionCountRequest, SessionCountResponse, QueueStatsRequest, QueueStatsResponse,
    QuickTestRequest, QuickTestResponse
)
from .common.admin_serialize import AdminSerialize
from service.db.database_service import DatabaseService
from service.cache.cache_service import CacheService
from service.lock.lock_service import LockService
from service.scheduler.scheduler_service import SchedulerService  
from service.queue.queue_service import QueueService
from service.core.logger import Logger
from datetime import datetime
import time
import asyncio

class AdminTemplateImpl(AdminTemplate):
    def __init__(self):
        super().__init__()
        self.start_time = time.time()
    
    def init(self, config):
        """관리자 템플릿 초기화"""
        try:
            Logger.info("Admin 템플릿 초기화 시작")
            # 관리자 관련 초기화 작업이 있다면 여기서 수행
            Logger.info("Admin 템플릿 초기화 완료")
        except Exception as e:
            Logger.error(f"Admin 템플릿 초기화 실패: {e}")
    
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
            from template.base.template_service import TemplateService
            db_service = TemplateService.get_database_service()
            
            if db_service:
                start_time = time.time()
                test_result = await db_service.execute_global_query("SELECT 1 as test", ())
                response_time = (time.time() - start_time) * 1000
                
                return {
                    "status": "healthy" if test_result else "unhealthy",
                    "response_time": f"{response_time:.2f}ms",
                    "details": "Connection test successful" if test_result else "Connection test failed"
                }
            else:
                return {
                    "status": "unhealthy",
                    "response_time": "N/A",
                    "details": "Database service not initialized"
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
            if CacheService.is_initialized():
                start_time = time.time()
                cache_client = CacheService.get_redis_client()
                
                async with cache_client as client:
                    test_key = "admin_health_check_test"
                    await client.set_string(test_key, "test_value", expire=10)
                    value = await client.get_string(test_key)
                    await client.delete(test_key)
                    
                    response_time = (time.time() - start_time) * 1000
                    
                    if value == "test_value":
                        return {
                            "status": "healthy",
                            "response_time": f"{response_time:.2f}ms",
                            "details": "Redis connection successful"
                        }
                    else:
                        return {
                            "status": "unhealthy", 
                            "response_time": f"{response_time:.2f}ms",
                            "details": "Redis test failed"
                        }
            else:
                return {
                    "status": "unhealthy",
                    "response_time": "N/A",
                    "details": "Cache service not initialized"
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
            services_status = {}
            
            # LockService 상태
            services_status["lock_service"] = "healthy" if LockService.is_initialized() else "not_configured"
            
            # SchedulerService 상태  
            services_status["scheduler_service"] = "healthy" if SchedulerService.is_initialized() else "not_configured"
            
            # QueueService 상태
            services_status["queue_service"] = "healthy" if (hasattr(QueueService, '_initialized') and QueueService._initialized) else "not_configured"
            
            # CacheService 상태
            services_status["cache_service"] = "healthy" if CacheService.is_initialized() else "not_configured"
            
            # 전체 상태 결정
            unhealthy_count = sum(1 for status in services_status.values() if status == "unhealthy")
            not_configured_count = sum(1 for status in services_status.values() if status == "not_configured")
            
            if unhealthy_count > 0:
                overall_status = "unhealthy"
            elif not_configured_count > 0:
                overall_status = "degraded"
            else:
                overall_status = "healthy"
            
            return {
                "status": overall_status,
                "services": services_status,
                "details": f"Services: {len([s for s in services_status.values() if s == 'healthy'])} healthy, {unhealthy_count} unhealthy, {not_configured_count} not configured"
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
            metrics = {}
            
            # 시스템 메트릭 (psutil 사용)
            try:
                import psutil
                metrics.update({
                    "cpu_usage": f"{psutil.cpu_percent()}%",
                    "memory_usage": f"{psutil.virtual_memory().percent}%",
                    "disk_usage": f"{psutil.disk_usage('/').percent}%",
                    "active_connections": len(psutil.net_connections())
                })
            except ImportError:
                metrics.update({
                    "cpu_usage": "unavailable (psutil not installed)",
                    "memory_usage": "unavailable (psutil not installed)",
                    "disk_usage": "unavailable (psutil not installed)",
                    "active_connections": "unavailable (psutil not installed)"
                })
            
            # 서비스별 메트릭
            service_metrics = {}
            
            # Cache 서비스 메트릭
            if CacheService.is_initialized():
                try:
                    cache_metrics = CacheService.get_metrics()
                    service_metrics["cache"] = cache_metrics
                except Exception as e:
                    service_metrics["cache"] = {"error": str(e)}
            
            # Queue 서비스 메트릭
            if hasattr(QueueService, '_initialized') and QueueService._initialized:
                try:
                    queue_service = QueueService.get_instance()
                    queue_stats = queue_service.get_stats()
                    service_metrics["queue"] = queue_stats
                except Exception as e:
                    service_metrics["queue"] = {"error": str(e)}
            
            # Scheduler 서비스 메트릭
            if SchedulerService.is_initialized():
                try:
                    jobs_status = SchedulerService.get_all_jobs_status()
                    service_metrics["scheduler"] = {
                        "active_jobs": len(jobs_status),
                        "jobs": jobs_status
                    }
                except Exception as e:
                    service_metrics["scheduler"] = {"error": str(e)}
            
            metrics["services"] = service_metrics
            return metrics
            
        except Exception as e:
            return {
                "error": f"Metrics collection failed: {str(e)}"
            }
    
    async def _get_session_count(self) -> int:
        """활성 세션 수 조회"""
        try:
            if CacheService.is_initialized():
                cache_client = CacheService.get_redis_client()
                async with cache_client as client:
                    # session:* 패턴의 키 개수 조회
                    session_keys = await client.scan_keys("session:*")
                    return len(session_keys)
            return 0
        except Exception as e:
            Logger.error(f"Session count query failed: {e}")
            return 0
    
    async def on_queue_stats_req(self, client_session: ClientSession, request: QueueStatsRequest) -> QueueStatsResponse:
        """큐 통계 요청 처리"""
        try:
            if hasattr(QueueService, '_initialized') and QueueService._initialized:
                queue_service = QueueService.get_instance()
                
                # 서비스 전체 통계
                service_stats = queue_service.get_stats()
                
                # 이벤트큐 통계
                event_stats = await queue_service.get_event_stats()
                
                # 특정 큐들의 통계 (요청에 큐 이름이 있으면 사용, 없으면 기본값)
                queue_names = request.queue_names or ["user_notifications", "trade_processing", "risk_analysis", "price_alerts"]
                queue_details = {}
                
                for queue_name in queue_names:
                    try:
                        stats = await queue_service.get_queue_stats(queue_name)
                        if stats:
                            queue_details[queue_name] = stats
                    except Exception as e:
                        queue_details[queue_name] = {"error": str(e)}
                
                return QueueStatsResponse(
                    service_stats=service_stats,
                    event_stats=event_stats,
                    queue_details=queue_details,
                    timestamp=datetime.now().isoformat(),
                    error_code=0
                )
            else:
                return QueueStatsResponse(
                    service_stats={},
                    event_stats={},
                    queue_details={},
                    timestamp=datetime.now().isoformat(),
                    error_code=404,
                    error_message="QueueService not initialized"
                )
                
        except Exception as e:
            Logger.error(f"Queue stats request failed: {e}")
            return QueueStatsResponse(
                service_stats={},
                event_stats={},
                queue_details={},
                timestamp=datetime.now().isoformat(),
                error_code=500,
                error_message=str(e)
            )
    
    async def on_quick_test_req(self, client_session: ClientSession, request: QuickTestRequest) -> QuickTestResponse:
        """빠른 테스트 요청 처리"""
        try:
            # 테스트할 서비스 목록 (요청에 있으면 사용, 없으면 기본값)
            test_types = request.test_types or ["cache", "database", "queue", "lock"]
            results = {}
            summary = {"total": 0, "passed": 0, "failed": 0}
            
            for test_type in test_types:
                summary["total"] += 1
                try:
                    if test_type == "cache":
                        if CacheService.is_initialized():
                            cache_client = CacheService.get_redis_client()
                            async with cache_client as client:
                                test_key = "admin_quick_test_cache"
                                await client.set_string(test_key, "test_value", expire=10)
                                value = await client.get_string(test_key)
                                await client.delete(test_key)
                                
                                if value == "test_value":
                                    results[test_type] = {"status": "passed", "details": "Cache read/write successful"}
                                    summary["passed"] += 1
                                else:
                                    results[test_type] = {"status": "failed", "details": "Cache test failed"}
                                    summary["failed"] += 1
                        else:
                            results[test_type] = {"status": "skipped", "details": "Cache service not initialized"}
                    
                    elif test_type == "database":
                        from template.base.template_service import TemplateService
                        db_service = TemplateService.get_database_service()
                        if db_service:
                            test_result = await db_service.execute_global_query("SELECT 1 as test", ())
                            if test_result:
                                results[test_type] = {"status": "passed", "details": "Database connection successful"}
                                summary["passed"] += 1
                            else:
                                results[test_type] = {"status": "failed", "details": "Database test failed"}
                                summary["failed"] += 1
                        else:
                            results[test_type] = {"status": "skipped", "details": "Database service not initialized"}
                    
                    elif test_type == "queue":
                        if hasattr(QueueService, '_initialized') and QueueService._initialized:
                            queue_service = QueueService.get_instance()
                            stats = queue_service.get_stats()
                            results[test_type] = {"status": "passed", "details": f"Queue service operational, processed: {stats.get('messages_processed', 0)}"}
                            summary["passed"] += 1
                        else:
                            results[test_type] = {"status": "skipped", "details": "Queue service not initialized"}
                    
                    elif test_type == "lock":
                        if LockService.is_initialized():
                            test_result = await LockService.is_locked("admin_quick_test_lock")
                            results[test_type] = {"status": "passed", "details": "Lock service operational"}
                            summary["passed"] += 1
                        else:
                            results[test_type] = {"status": "skipped", "details": "Lock service not initialized"}
                    
                    else:
                        results[test_type] = {"status": "unknown", "details": f"Unknown test type: {test_type}"}
                        summary["failed"] += 1
                        
                except Exception as e:
                    results[test_type] = {"status": "failed", "details": f"Test error: {str(e)}"}
                    summary["failed"] += 1
            
            return QuickTestResponse(
                results=results,
                summary=summary,
                timestamp=datetime.now().isoformat(),
                error_code=0
            )
            
        except Exception as e:
            Logger.error(f"Quick test request failed: {e}")
            return QuickTestResponse(
                results={},
                summary={"total": 0, "passed": 0, "failed": 0},
                timestamp=datetime.now().isoformat(),
                error_code=500,
                error_message=str(e)
            )