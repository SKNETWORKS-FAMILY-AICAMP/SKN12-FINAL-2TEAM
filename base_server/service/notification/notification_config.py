"""
알림 서비스 설정
"""
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel


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


class NotificationConfig(BaseModel):
    """간소화된 알림 서비스 설정 - 실제 사용 항목만 포함"""
    
    # 채널별 활성화 여부
    enabled_channels: Optional[Dict[str, bool]] = None
    
    # 배치 설정
    batch_size: int = 100
    batch_timeout_seconds: float = 5.0
    
    # 중복 방지 설정
    dedup_window_hours: int = 24
    
    # 우선순위 설정  
    priority_channels: Optional[Dict[str, int]] = None
    
    # Rate Limiting 설정
    rate_limit_per_user_per_hour: int = 100
    
    def model_post_init(self, __context):
        """기본값 설정 (pydantic v2)"""
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