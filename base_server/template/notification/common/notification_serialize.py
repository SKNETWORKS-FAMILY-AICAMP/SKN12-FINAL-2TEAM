from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from service.net.protocol_base import BaseRequest, BaseResponse
from .notification_model import InAppNotification, NotificationStats

# ========================================
# 인앱 알림 목록 조회
# ========================================
class NotificationListRequest(BaseRequest):
    """인앱 알림 목록 조회 요청"""
    read_filter: str = "unread_only"  # all, unread_only, read_only (게임 패턴)
    type_id: Optional[str] = None  # SIGNAL_ALERT, TRADE_COMPLETE 등
    page: int = 1
    limit: int = 20

class NotificationListResponse(BaseResponse):
    """인앱 알림 목록 조회 응답"""
    notifications: List[InAppNotification] = []
    total_count: int = 0
    unread_count: int = 0  # 현재 총 미읽음 수
    has_more: bool = False

# ========================================
# 알림 읽음 처리
# ========================================
class NotificationMarkReadRequest(BaseRequest):
    """알림 읽음 처리 요청"""
    notification_id: str = ""

class NotificationMarkReadResponse(BaseResponse):
    """알림 읽음 처리 응답"""
    result: str = ""  # SUCCESS, FAILED, ALREADY_READ
    message: str = ""

# ========================================
# 알림 일괄 읽음 처리
# ========================================
class NotificationMarkAllReadRequest(BaseRequest):
    """알림 일괄 읽음 처리 요청"""
    type_id: Optional[str] = None  # 특정 타입만 읽음 처리 (None이면 전체)

class NotificationMarkAllReadResponse(BaseResponse):
    """알림 일괄 읽음 처리 응답"""
    result: str = ""  # SUCCESS, FAILED
    message: str = ""
    updated_count: int = 0  # 읽음 처리된 개수

# ========================================
# 알림 삭제 (소프트 삭제)
# ========================================
class NotificationDeleteRequest(BaseRequest):
    """알림 삭제 요청"""
    notification_id: str = ""

class NotificationDeleteResponse(BaseResponse):
    """알림 삭제 응답"""
    result: str = ""  # SUCCESS, FAILED
    message: str = ""

# ========================================
# 알림 통계 조회
# ========================================
class NotificationStatsRequest(BaseRequest):
    """알림 통계 조회 요청"""
    days: int = 7  # 최근 N일

class NotificationStatsResponse(BaseResponse):
    """알림 통계 조회 응답"""
    daily_stats: List[NotificationStats] = []  # 일별 통계
    current_unread_count: int = 0  # 현재 미읽음 수

# ========================================
# 알림 생성 (운영자용 - OPERATOR 권한 필요)
# ========================================
class NotificationCreateRequest(BaseRequest):
    """운영자 알림 생성 요청 (운영진용)"""
    target_type: str = "ALL"  # ALL, SPECIFIC_USER, USER_GROUP
    target_users: Optional[List[int]] = None  # target_type이 SPECIFIC_USER일 때 account_db_key 리스트
    user_group: Optional[str] = None  # target_type이 USER_GROUP일 때 (PREMIUM, FREE 등)
    type_id: str = "SYSTEM_NOTICE"  # SYSTEM_NOTICE, MAINTENANCE, PROMOTION 등
    title: str = ""
    message: str = ""
    data: Optional[Dict[str, Any]] = None
    priority: int = 3  # 1(HIGH), 2(MEDIUM), 3(LOW)
    expires_at: Optional[str] = None  # YYYY-MM-DD HH:MM:SS 형식

class NotificationCreateResponse(BaseResponse):
    """운영자 알림 생성 응답"""
    notification_ids: List[str] = []  # 생성된 알림 ID 목록
    created_count: int = 0  # 실제 생성된 알림 개수
    message: str = ""

# ========================================
# 알림 생성 (서버 내부용 - 클라이언트 요청 없음)
# ========================================
class InternalNotificationCreateRequest(BaseModel):
    """서버 내부 알림 생성 요청 (SignalMonitoringService에서 사용)"""
    account_db_key: int
    type_id: str  # NotificationType 사용
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None
    priority: int = 3  # NotificationPriority 사용
    expires_at: Optional[str] = None