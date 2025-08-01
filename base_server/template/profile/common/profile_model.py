from pydantic import BaseModel
from typing import Optional

class ProfileSettings(BaseModel):
    """사용자 프로필 설정 정보"""
    # 기본 프로필 정보
    account_id: str = ""
    nickname: str = ""
    email: str = ""
    phone_number: Optional[str] = None
    email_verified: bool = False
    phone_verified: bool = False
    
    # 알림 설정
    email_notifications_enabled: bool = True
    sms_notifications_enabled: bool = False
    push_notifications_enabled: bool = True
    price_alert_enabled: bool = True
    news_alert_enabled: bool = True
    portfolio_alert_enabled: bool = False
    trade_alert_enabled: bool = True
    
    # 결제 정보
    payment_plan: str = "FREE"
    plan_expires_at: Optional[str] = None
    
    # 기타
    created_at: str = ""
    updated_at: str = ""

class ApiKeyInfo(BaseModel):
    """API 키 정보"""
    korea_investment_app_key: str = ""
    korea_investment_app_secret_masked: str = ""  # 마스킹된 시크릿
    alpha_vantage_key: str = ""
    polygon_key: str = ""
    finnhub_key: str = ""
    created_at: str = ""
    updated_at: str = ""

class PaymentPlanInfo(BaseModel):
    """결제 플랜 정보"""
    current_plan: str = "FREE"
    plan_name: str = ""
    plan_price: float = 0.0
    plan_expires_at: Optional[str] = None
    auto_renewal: bool = False
    payment_method: str = ""