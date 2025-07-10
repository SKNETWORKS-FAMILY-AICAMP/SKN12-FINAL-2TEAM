from typing import Optional, List, Dict, Any
from service.net.protocol_base import BaseRequest, BaseResponse
from .notification_model import Notification, PriceAlert, AlertRule

# ============================================================================
# 알림 관리
# ============================================================================

class NotificationListRequest(BaseRequest):
    """알림 목록 조회"""
    type_filter: str = "ALL"
    read_status: str = "ALL"  # ALL, READ, UNREAD
    page: int = 1
    limit: int = 20

class NotificationListResponse(BaseResponse):
    """알림 목록 응답"""
    notifications: List[Notification] = []
    total_count: int = 0
    unread_count: int = 0

class NotificationMarkReadRequest(BaseRequest):
    """알림 읽음 처리"""
    notification_ids: List[str]

class NotificationMarkReadResponse(BaseResponse):
    """알림 읽음 처리 응답"""
    updated_count: int = 0
    message: str = ""

class NotificationCreateAlertRequest(BaseRequest):
    """가격 알림 생성"""
    symbol: str
    alert_type: str
    target_value: float
    message: Optional[str] = ""

class NotificationCreateAlertResponse(BaseResponse):
    """가격 알림 생성 응답"""
    alert: Optional[PriceAlert] = None
    message: str = ""

class NotificationAlertListRequest(BaseRequest):
    """알림 설정 목록"""
    symbol: Optional[str] = None
    status_filter: str = "ACTIVE"  # ALL, ACTIVE, TRIGGERED

class NotificationAlertListResponse(BaseResponse):
    """알림 설정 목록 응답"""
    alerts: List[PriceAlert] = []
    total_count: int = 0

class NotificationDeleteAlertRequest(BaseRequest):
    """알림 삭제"""
    alert_ids: List[str]

class NotificationDeleteAlertResponse(BaseResponse):
    """알림 삭제 응답"""
    deleted_count: int = 0
    message: str = ""