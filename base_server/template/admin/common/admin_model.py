from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class HealthCheckRequest(BaseModel):
    """헬스체크 요청"""
    check_type: str = "all"  # "all", "db", "cache", "services"

class HealthCheckResponse(BaseModel):
    """헬스체크 응답"""
    status: str  # "healthy", "unhealthy", "degraded"
    timestamp: str
    services: Dict[str, Any]
    error_code: int = 0
    error_message: Optional[str] = None

class ServerStatusRequest(BaseModel):
    """서버 상태 요청"""
    include_metrics: bool = False

class ServerStatusResponse(BaseModel):
    """서버 상태 응답"""
    server_name: str
    environment: str
    version: str
    uptime: str
    status: str
    metrics: Optional[Dict[str, Any]] = None
    error_code: int = 0
    error_message: Optional[str] = None

class SessionCountRequest(BaseModel):
    """세션 수 요청"""
    pass

class SessionCountResponse(BaseModel):
    """세션 수 응답"""
    total_sessions: int
    active_sessions: int
    error_code: int = 0
    error_message: Optional[str] = None

class QueueStatsRequest(BaseModel):
    """큐 통계 요청"""
    queue_names: Optional[List[str]] = None

class QueueStatsResponse(BaseModel):
    """큐 통계 응답"""
    service_stats: Dict[str, Any]
    event_stats: Dict[str, Any]
    queue_details: Dict[str, Any]
    timestamp: str
    error_code: int = 0
    error_message: Optional[str] = None

class QuickTestRequest(BaseModel):
    """빠른 테스트 요청"""
    test_types: Optional[List[str]] = None

class QuickTestResponse(BaseModel):
    """빠른 테스트 응답"""
    results: Dict[str, Any]
    summary: Dict[str, Any]
    timestamp: str
    error_code: int = 0
    error_message: Optional[str] = None