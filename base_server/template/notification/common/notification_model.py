from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

# ========================================
# 인앱 알림 모델 (SQL 스키마 기반)
# ========================================

class InAppNotification(BaseModel):
    """인앱 알림 정보 (table_inapp_notifications 기반)"""
    idx: Optional[int] = None
    notification_id: str = ""
    account_db_key: int = 0
    type_id: str = ""  # SIGNAL_ALERT, TRADE_COMPLETE, PRICE_ALERT, SYSTEM_NOTICE, ACCOUNT_SECURITY
    title: str = ""
    message: str = ""
    data: Optional[Dict[str, Any]] = None  # JSON 추가 데이터
    priority: int = 3  # 1=긴급, 2=높음, 3=보통, 4=낮음, 5=매우낮음
    is_read: bool = False
    read_at: Optional[str] = None
    expires_at: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""

class NotificationStats(BaseModel):
    """알림 통계 정보 (table_inapp_notification_stats 기반)"""
    date: str = ""
    total_count: int = 0
    read_count: int = 0
    unread_count: int = 0
    priority_1_count: int = 0  # 긴급
    priority_2_count: int = 0  # 높음
    priority_3_count: int = 0  # 보통
    auto_deleted_count: int = 0  # 게임 패턴 자동 삭제
    current_unread_count: int = 0  # 실시간 미읽음 수

class NotificationType:
    """알림 타입 상수"""
    SIGNAL_ALERT = "SIGNAL_ALERT"  # 시그널 발생 알림
    TRADE_COMPLETE = "TRADE_COMPLETE"  # 거래 완료 알림
    PRICE_ALERT = "PRICE_ALERT"  # 가격 알림
    SYSTEM_NOTICE = "SYSTEM_NOTICE"  # 시스템 공지
    ACCOUNT_SECURITY = "ACCOUNT_SECURITY"  # 계정 보안 알림

class NotificationPriority:
    """알림 우선순위"""
    URGENT = 1  # 긴급
    HIGH = 2    # 높음
    NORMAL = 3  # 보통
    LOW = 4     # 낮음
    VERY_LOW = 5  # 매우 낮음

class NotificationReadFilter:
    """알림 읽음 필터"""
    ALL = "all"  # 전체
    UNREAD_ONLY = "unread_only"  # 읽지 않은 것만
    READ_ONLY = "read_only"  # 읽은 것만 (자동 삭제)