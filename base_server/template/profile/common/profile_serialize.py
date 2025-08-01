from typing import Optional
from service.net.protocol_base import BaseRequest, BaseResponse
from .profile_model import ProfileSettings, ApiKeyInfo, PaymentPlanInfo

# ============================================================================
# 프로필 설정 조회
# ============================================================================

class ProfileGetRequest(BaseRequest):
    """프로필 설정 조회 요청 - 세션에서 사용자 정보 가져옴"""
    pass

class ProfileGetResponse(BaseResponse):
    """프로필 설정 조회 응답"""
    profile: Optional[ProfileSettings] = None

# ============================================================================
# 전체 프로필 업데이트 (마이페이지 한번에 저장) - 결제 플랜 제외
# ============================================================================

class ProfileUpdateAllRequest(BaseRequest):
    """전체 프로필 설정 업데이트 요청 - 마이페이지에서 모든 설정을 한번에 저장 (결제 플랜 제외)"""
    # 기본 프로필
    nickname: str
    email: str
    phone_number: Optional[str] = None
    
    # 알림 설정
    email_notifications_enabled: bool
    sms_notifications_enabled: bool
    push_notifications_enabled: bool
    price_alert_enabled: bool
    news_alert_enabled: bool
    portfolio_alert_enabled: bool
    trade_alert_enabled: bool
    
    # 비밀번호 변경 (선택사항)
    current_password: Optional[str] = None
    new_password: Optional[str] = None
    
    # API 키 (선택사항)
    korea_investment_app_key: Optional[str] = None
    korea_investment_app_secret: Optional[str] = None
    alpha_vantage_key: Optional[str] = None
    polygon_key: Optional[str] = None
    finnhub_key: Optional[str] = None

class ProfileUpdateAllResponse(BaseResponse):
    """전체 프로필 설정 업데이트 응답"""
    message: str = ""
    updated_profile: Optional[ProfileSettings] = None
    password_changed: bool = False
    api_keys_saved: bool = False
    require_relogin: bool = False

# ============================================================================
# 기본 프로필 업데이트 (전화번호, 이메일)
# ============================================================================

class ProfileUpdateBasicRequest(BaseRequest):
    """기본 프로필 업데이트 요청"""
    nickname: str
    email: str
    phone_number: Optional[str] = None

class ProfileUpdateBasicResponse(BaseResponse):
    """기본 프로필 업데이트 응답"""
    message: str = ""
    updated_profile: Optional[ProfileSettings] = None

# ============================================================================
# 알림 설정 업데이트
# ============================================================================

class ProfileUpdateNotificationRequest(BaseRequest):
    """알림 설정 업데이트 요청"""
    email_notifications_enabled: bool
    sms_notifications_enabled: bool
    push_notifications_enabled: bool
    price_alert_enabled: bool
    news_alert_enabled: bool
    portfolio_alert_enabled: bool
    trade_alert_enabled: bool

class ProfileUpdateNotificationResponse(BaseResponse):
    """알림 설정 업데이트 응답"""
    message: str = ""

# ============================================================================
# 비밀번호 변경
# ============================================================================

class ProfileChangePasswordRequest(BaseRequest):
    """비밀번호 변경 요청"""
    current_password: str
    new_password: str

class ProfileChangePasswordResponse(BaseResponse):
    """비밀번호 변경 응답"""
    message: str = ""
    require_relogin: bool = False

# ============================================================================
# 결제 플랜 관리 (별도 처리)
# ============================================================================

class ProfileGetPaymentPlanRequest(BaseRequest):
    """결제 플랜 조회 요청"""
    pass

class ProfileGetPaymentPlanResponse(BaseResponse):
    """결제 플랜 조회 응답"""
    payment_info: Optional[PaymentPlanInfo] = None

class ProfileChangePlanRequest(BaseRequest):
    """결제 플랜 변경 요청 (별도 결제 처리 필요)"""
    new_plan: str  # FREE, BASIC, PREMIUM, ENTERPRISE
    payment_method: str  # card, bank_transfer, etc
    billing_cycle: str = "monthly"  # monthly, yearly

class ProfileChangePlanResponse(BaseResponse):
    """결제 플랜 변경 응답"""
    message: str = ""
    payment_url: Optional[str] = None  # 결제 페이지 URL
    requires_payment: bool = True

# ============================================================================
# API 키 관리
# ============================================================================

class ProfileSaveApiKeysRequest(BaseRequest):
    """API 키 저장 요청"""
    korea_investment_app_key: str
    korea_investment_app_secret: str
    alpha_vantage_key: Optional[str] = ""
    polygon_key: Optional[str] = ""
    finnhub_key: Optional[str] = ""

class ProfileSaveApiKeysResponse(BaseResponse):
    """API 키 저장 응답"""
    message: str = ""

class ProfileGetApiKeysRequest(BaseRequest):
    """API 키 조회 요청"""
    pass

class ProfileGetApiKeysResponse(BaseResponse):
    """API 키 조회 응답"""
    api_keys: Optional[ApiKeyInfo] = None