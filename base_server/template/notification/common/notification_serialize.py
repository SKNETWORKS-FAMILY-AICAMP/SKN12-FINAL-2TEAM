from service.net.protocol_base import BaseRequest, BaseResponse
from .notification_model import Notification, PriceAlert, AlertRule
from typing import Optional, List, Dict, Any

# ============================================================================
# REQ-NOTI-001: 알림 목록 조회
# 의거: 화면 018 (알림 목록), REQ-NOTI-001
# ============================================================================

class NotificationGetListRequest(BaseRequest):
    """알림 목록 조회 요청"""
    type_filter: str = "ALL"  # ALL, PRICE_ALERT, NEWS, PORTFOLIO, TRADE, SYSTEM
    read_status: str = "ALL"  # ALL, READ, UNREAD
    page: int = 1
    limit: int = 20

class NotificationGetListResponse(BaseResponse):
    """알림 목록 조회 응답"""
    notifications: List[Notification] = []
    total_count: int = 0
    unread_count: int = 0
    page: int = 1
    total_pages: int = 1

# ============================================================================
# REQ-NOTI-002: 알림 읽음 처리
# 의거: 화면 018 (알림 관리), REQ-NOTI-002
# ============================================================================

class NotificationMarkReadRequest(BaseRequest):
    """알림 읽음 처리 요청"""
    notification_ids: List[str]

class NotificationMarkReadResponse(BaseResponse):
    """알림 읽음 처리 응답"""
    updated_count: int = 0
    message: str = ""

# ============================================================================
# REQ-NOTI-003: 가격 알림 생성
# 의거: 화면 018 (가격 알림 설정), REQ-NOTI-003
# ============================================================================

class NotificationCreatePriceAlertRequest(BaseRequest):
    """가격 알림 생성 요청"""
    symbol: str
    alert_type: str  # PRICE_ABOVE, PRICE_BELOW, CHANGE_RATE_ABOVE, CHANGE_RATE_BELOW, VOLUME_SPIKE
    target_value: float
    message: str = ""

class NotificationCreatePriceAlertResponse(BaseResponse):
    """가격 알림 생성 응답"""
    alert: Optional[PriceAlert] = None
    message: str = ""

# ============================================================================
# REQ-NOTI-004: 가격 알림 목록 조회
# 의거: 화면 018 (알림 관리), REQ-NOTI-004
# ============================================================================

class NotificationGetPriceAlertsRequest(BaseRequest):
    """가격 알림 목록 조회 요청"""
    symbol: str = ""
    is_active: Optional[bool] = None

class NotificationGetPriceAlertsResponse(BaseResponse):
    """가격 알림 목록 조회 응답"""
    alerts: List[PriceAlert] = []
    total_count: int = 0

# ============================================================================
# REQ-NOTI-005: 가격 알림 삭제
# 의거: 화면 018 (알림 삭제), REQ-NOTI-005
# ============================================================================

class NotificationDeletePriceAlertRequest(BaseRequest):
    """가격 알림 삭제 요청"""
    alert_id: str

class NotificationDeletePriceAlertResponse(BaseResponse):
    """가격 알림 삭제 응답"""
    message: str = ""

# ============================================================================
# REQ-NOTI-006: 알림 규칙 생성
# 의거: 화면 019 (알림 규칙), REQ-NOTI-006
# ============================================================================

class NotificationCreateRuleRequest(BaseRequest):
    """알림 규칙 생성 요청"""
    name: str
    description: str = ""
    rule_type: str  # PRICE, VOLUME, NEWS, PORTFOLIO, TECHNICAL
    conditions: Dict[str, Any]  # JSON 형태의 조건
    actions: List[str]  # EMAIL, PUSH, SMS, IN_APP
    priority: str = "NORMAL"  # LOW, NORMAL, HIGH, URGENT

class NotificationCreateRuleResponse(BaseResponse):
    """알림 규칙 생성 응답"""
    rule: Optional[AlertRule] = None
    message: str = ""

# ============================================================================
# REQ-NOTI-007: 알림 규칙 목록 조회
# 의거: 화면 019 (규칙 관리), REQ-NOTI-007
# ============================================================================

class NotificationGetRulesRequest(BaseRequest):
    """알림 규칙 목록 조회 요청"""
    rule_type: str = "ALL"  # ALL, PRICE, VOLUME, NEWS, PORTFOLIO, TECHNICAL
    is_active: Optional[bool] = None

class NotificationGetRulesResponse(BaseResponse):
    """알림 규칙 목록 조회 응답"""
    rules: List[AlertRule] = []
    total_count: int = 0

# ============================================================================
# REQ-NOTI-008: 알림 규칙 수정
# 의거: 화면 019 (규칙 편집), REQ-NOTI-008
# ============================================================================

class NotificationUpdateRuleRequest(BaseRequest):
    """알림 규칙 수정 요청"""
    rule_id: str
    name: str = ""
    description: str = ""
    conditions: Dict[str, Any] = {}
    actions: List[str] = []
    is_active: Optional[bool] = None
    priority: str = ""

class NotificationUpdateRuleResponse(BaseResponse):
    """알림 규칙 수정 응답"""
    rule: Optional[AlertRule] = None
    message: str = ""

# ============================================================================
# REQ-NOTI-009: 알림 설정 조회
# 의거: 화면 020 (알림 설정), REQ-NOTI-009
# ============================================================================

class NotificationGetSettingsRequest(BaseRequest):
    """알림 설정 조회 요청"""
    category: str = "ALL"  # ALL, NOTIFICATION, CHANNELS, SCHEDULE

class NotificationGetSettingsResponse(BaseResponse):
    """알림 설정 조회 응답"""
    settings: Dict[str, Any] = {}

# ============================================================================
# REQ-NOTI-010: 알림 설정 업데이트
# 의거: 화면 020 (설정 변경), REQ-NOTI-010
# ============================================================================

class NotificationUpdateSettingsRequest(BaseRequest):
    """알림 설정 업데이트 요청"""
    price_alerts: bool = True
    news_alerts: bool = True
    portfolio_alerts: bool = False
    trade_alerts: bool = True
    system_alerts: bool = True
    email_notifications: bool = True
    push_notifications: bool = True
    sms_notifications: bool = False
    quiet_hours_enabled: bool = False
    quiet_hours_start: str = "22:00"
    quiet_hours_end: str = "08:00"
    frequency: str = "REAL_TIME"  # REAL_TIME, DAILY, WEEKLY

class NotificationUpdateSettingsResponse(BaseResponse):
    """알림 설정 업데이트 응답"""
    message: str = ""

# ============================================================================
# REQ-NOTI-011: 알림 전송 테스트
# 의거: 화면 020 (테스트 전송), REQ-NOTI-011
# ============================================================================

class NotificationTestSendRequest(BaseRequest):
    """알림 전송 테스트 요청"""
    channel: str  # EMAIL, PUSH, SMS
    message: str = "테스트 알림입니다."

class NotificationTestSendResponse(BaseResponse):
    """알림 전송 테스트 응답"""
    success: bool = False
    message: str = ""
    delivery_time: float = 0.0  # 초 단위

# ============================================================================
# REQ-NOTI-012: 알림 통계 조회
# 의거: 화면 018 (알림 통계), REQ-NOTI-012
# ============================================================================

class NotificationGetStatsRequest(BaseRequest):
    """알림 통계 조회 요청"""
    period: str = "1W"  # 1D, 1W, 1M, 3M

class NotificationGetStatsResponse(BaseResponse):
    """알림 통계 조회 응답"""
    total_sent: int = 0
    total_read: int = 0
    by_type: Dict[str, int] = {}  # 타입별 알림 수
    by_channel: Dict[str, int] = {}  # 채널별 전송 수
    read_rate: float = 0.0  # 읽음률
    response_time: float = 0.0  # 평균 응답 시간

# ============================================================================
# REQ-NOTI-013: 대량 알림 삭제
# 의거: 화면 018 (알림 정리), REQ-NOTI-013
# ============================================================================

class NotificationBulkDeleteRequest(BaseRequest):
    """대량 알림 삭제 요청"""
    filter_type: str = "READ"  # READ, OLDER_THAN, BY_TYPE
    older_than_days: int = 30
    notification_type: str = ""

class NotificationBulkDeleteResponse(BaseResponse):
    """대량 알림 삭제 응답"""
    deleted_count: int = 0
    message: str = ""