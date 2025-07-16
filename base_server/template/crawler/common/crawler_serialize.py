from typing import Optional, List, Dict, Any
from service.net.protocol_base import BaseRequest, BaseResponse
from .crawler_model import CrawlerTask, CrawlerData

# ============================================================================
# 크롤러 작업 실행 (AWS Lambda -> Server)
# ============================================================================

class CrawlerExecuteRequest(BaseRequest):
    """크롤러 작업 실행 요청"""
    task_id: str
    task_type: str  # news_crawl, market_data, financial_report, etc.
    target_url: Optional[str] = None
    target_api: Optional[str] = None  
    parameters: Optional[Dict[str, Any]] = None
    priority: int = 0
    lock_key: Optional[str] = None  # 분산락 키 (중복 실행 방지)
    lock_ttl: int = 3600  # 락 TTL (초)

class CrawlerExecuteResponse(BaseResponse):
    """크롤러 작업 실행 응답"""
    task_id: str = ""
    status: str = ""  # pending, running, completed, failed, skipped
    message: str = ""
    started_at: Optional[str] = None
    lock_acquired: bool = False

# ============================================================================
# 크롤러 상태 조회
# ============================================================================

class CrawlerStatusRequest(BaseRequest):
    """크롤러 상태 조회 요청"""
    task_id: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    status: Optional[str] = None
    limit: int = 100

class CrawlerStatusResponse(BaseResponse):
    """크롤러 상태 조회 응답"""
    tasks: List[Dict[str, Any]] = []
    total_count: int = 0

# ============================================================================
# 크롤러 헬스체크
# ============================================================================

class CrawlerHealthRequest(BaseRequest):
    """크롤러 헬스체크 요청"""
    check_services: bool = True
    include_stats: bool = True

class CrawlerHealthResponse(BaseResponse):
    """크롤러 헬스체크 응답"""
    status: str = "healthy"
    timestamp: str = ""
    last_run: Optional[str] = None
    active_tasks: int = 0
    completed_today: int = 0
    failed_today: int = 0
    services: Dict[str, Any] = {}

# ============================================================================
# 크롤러 작업 중단
# ============================================================================

class CrawlerStopRequest(BaseRequest):
    """크롤러 작업 중단 요청"""
    task_id: str
    force: bool = False

class CrawlerStopResponse(BaseResponse):
    """크롤러 작업 중단 응답"""
    task_id: str = ""
    stopped: bool = False
    message: str = ""

# ============================================================================
# 크롤러 데이터 조회
# ============================================================================

class CrawlerDataRequest(BaseRequest):
    """크롤러 데이터 조회 요청"""
    task_id: Optional[str] = None
    data_id: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    limit: int = 100

class CrawlerDataResponse(BaseResponse):
    """크롤러 데이터 조회 응답"""
    data: List[Dict[str, Any]] = []
    total_count: int = 0