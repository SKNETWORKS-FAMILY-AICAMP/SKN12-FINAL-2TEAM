from template.base.template.admin_template import AdminTemplate
from template.base.client_session import ClientSession
from .common.admin_model import *
from .common.admin_serialize import AdminSerialize
from service.core.logger import Logger
from datetime import datetime
import time

class AdminTemplateImpl(AdminTemplate):
    def __init__(self):
        super().__init__()
        self.start_time = time.time()
    
    async def on_health_check_req(self, client_session: ClientSession, request: HealthCheckRequest) -> HealthCheckResponse:
        """헬스체크 요청 처리"""
        print(f"Health check request received: {request.check_type}")
        
        try:
            services = {
                "database": {"status": "healthy", "response_time": "< 100ms"},
                "cache": {"status": "healthy", "response_time": "< 50ms"},
                "services": {"status": "healthy", "details": "All services operational"}
            }
            
            return HealthCheckResponse(
                status="healthy",
                timestamp=datetime.now().isoformat(),
                services=services,
                error_code=0
            )
            
        except Exception as e:
            print(f"Health check failed: {e}")
            return HealthCheckResponse(
                status="unhealthy",
                timestamp=datetime.now().isoformat(),
                services={},
                error_code=500,
                error_message=str(e)
            )
    
    async def on_server_status_req(self, client_session: ClientSession, request: ServerStatusRequest) -> ServerStatusResponse:
        """서버 상태 요청 처리"""
        print(f"Server status request received: include_metrics={request.include_metrics}")
        
        try:
            uptime_seconds = time.time() - self.start_time
            uptime_str = f"{int(uptime_seconds // 3600)}h {int((uptime_seconds % 3600) // 60)}m {int(uptime_seconds % 60)}s"
            
            metrics = None
            if request.include_metrics:
                metrics = {
                    "cpu_usage": "25%",
                    "memory_usage": "60%",
                    "disk_usage": "45%",
                    "active_connections": 10
                }
            
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
            print(f"Server status check failed: {e}")
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
        print(f"Session count request received")
        
        try:
            return SessionCountResponse(
                total_sessions=5,
                active_sessions=3,
                error_code=0
            )
            
        except Exception as e:
            print(f"Session count check failed: {e}")
            return SessionCountResponse(
                total_sessions=0,
                active_sessions=0,
                error_code=500,
                error_message=str(e)
            )