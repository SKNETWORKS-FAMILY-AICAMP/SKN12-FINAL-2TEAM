"""
알림 서비스 설정
"""
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass


class NotificationChannel(Enum):
    """알림 채널 타입"""
    WEBSOCKET = "websocket"     # 실시간 웹소켓
    PUSH = "push"               # 모바일 푸시
    EMAIL = "email"             # 이메일
    SMS = "sms"                 # SMS
    IN_APP = "in_app"           # 앱 내 알림함


class NotificationType(Enum):
    """알림 타입"""
    # 예측 관련
    PREDICTION_ALERT = "prediction_alert"           # 매수/매도 신호
    PRICE_TARGET_REACHED = "price_target_reached"   # 목표가 도달
    STOP_LOSS_TRIGGERED = "stop_loss_triggered"     # 손절 알림
    
    # 포트폴리오 관련
    PORTFOLIO_REBALANCE = "portfolio_rebalance"     # 리밸런싱 제안
    TRADE_EXECUTED = "trade_executed"               # 거래 체결
    DAILY_SUMMARY = "daily_summary"                 # 일일 요약
    
    # 시스템 관련
    SYSTEM_MAINTENANCE = "system_maintenance"       # 시스템 점검
    FEATURE_UPDATE = "feature_update"               # 기능 업데이트
    ACCOUNT_SECURITY = "account_security"           # 계정 보안


@dataclass
class NotificationConfig:
    """알림 서비스 설정"""
    # 채널별 활성화 여부
    enabled_channels: Dict[str, bool] = None
    
    # 배치 설정
    batch_size: int = 100
    batch_timeout_seconds: float = 5.0
    
    # 재시도 설정
    max_retries: int = 3
    retry_delay_seconds: int = 60
    
    # 중복 방지 설정
    dedup_window_hours: int = 24
    
    # 우선순위 설정
    priority_channels: Dict[str, int] = None  # 낮을수록 높은 우선순위
    
    # 제한 설정
    rate_limit_per_user_per_hour: int = 100
    rate_limit_per_channel_per_hour: Dict[str, int] = None
    
    # 템플릿 설정
    template_path: str = "templates/notifications"
    
    # 외부 서비스 설정
    push_service_config: Optional[Dict[str, Any]] = None
    email_service_config: Optional[Dict[str, Any]] = None
    sms_service_config: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """기본값 설정"""
        if self.enabled_channels is None:
            self.enabled_channels = {
                NotificationChannel.WEBSOCKET.value: True,
                NotificationChannel.IN_APP.value: True,
                NotificationChannel.PUSH.value: False,
                NotificationChannel.EMAIL.value: False,
                NotificationChannel.SMS.value: False
            }
        
        if self.priority_channels is None:
            self.priority_channels = {
                NotificationChannel.WEBSOCKET.value: 1,
                NotificationChannel.PUSH.value: 2,
                NotificationChannel.IN_APP.value: 3,
                NotificationChannel.EMAIL.value: 4,
                NotificationChannel.SMS.value: 5
            }
        
        if self.rate_limit_per_channel_per_hour is None:
            self.rate_limit_per_channel_per_hour = {
                NotificationChannel.WEBSOCKET.value: 1000,
                NotificationChannel.PUSH.value: 50,
                NotificationChannel.EMAIL.value: 10,
                NotificationChannel.SMS.value: 5,
                NotificationChannel.IN_APP.value: 200
            }