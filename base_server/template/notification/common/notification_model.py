from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class Notification(BaseModel):
    """알림 정보"""
    notification_id: str = ""
    title: str = ""
    message: str = ""
    type: str = ""  # PRICE_ALERT, NEWS, PORTFOLIO, TRADE, SYSTEM
    priority: str = "NORMAL"  # LOW, NORMAL, HIGH, URGENT
    data: Optional[Dict[str, Any]] = None
    is_read: bool = False
    created_at: str = ""
    expires_at: Optional[str] = None

class PriceAlert(BaseModel):
    """가격 알림 설정"""
    alert_id: str = ""
    symbol: str = ""
    alert_type: str = ""  # PRICE_ABOVE, PRICE_BELOW, CHANGE_RATE
    target_value: float = 0.0
    current_value: float = 0.0
    is_active: bool = True
    created_at: str = ""
    triggered_at: Optional[str] = None

class AlertRule(BaseModel):
    """알림 규칙"""
    rule_id: str = ""
    name: str = ""
    description: str = ""
    conditions: Dict[str, Any] = {}
    actions: List[str] = []  # EMAIL, PUSH, SMS
    is_active: bool = True
    priority: str = "NORMAL"