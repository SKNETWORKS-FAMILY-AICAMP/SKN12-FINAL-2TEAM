from .admin_model import *
from datetime import datetime
import time

class AdminSerialize:
    """관리자 직렬화"""
    
    @staticmethod
    def serialize_health_check_response(status: str, services: dict, error_code: int = 0, error_message: str = None) -> dict:
        """헬스체크 응답 직렬화"""
        return {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "services": services,
            "error_code": error_code,
            "error_message": error_message
        }
    
    @staticmethod
    def serialize_server_status_response(server_name: str, environment: str, version: str, 
                                       uptime: str, status: str, metrics: dict = None,
                                       error_code: int = 0, error_message: str = None) -> dict:
        """서버 상태 응답 직렬화"""
        return {
            "server_name": server_name,
            "environment": environment,
            "version": version,
            "uptime": uptime,
            "status": status,
            "metrics": metrics,
            "error_code": error_code,
            "error_message": error_message
        }
    
    @staticmethod
    def serialize_session_count_response(total_sessions: int, active_sessions: int,
                                       error_code: int = 0, error_message: str = None) -> dict:
        """세션 수 응답 직렬화"""
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "error_code": error_code,
            "error_message": error_message
        }