from typing import Optional, Dict, Any, List
from service.net.protocol_base import BaseRequest, BaseResponse
from .settings_model import UserSettings, NotificationSettings, SecuritySettings

# ============================================================================
# 설정 조회/수정 (REQ-SET-001~010)
# 의거: 화면 009-1~6 (설정), REQ-SET-001~010
# ============================================================================

class SettingsGetRequest(BaseRequest):
    """설정 조회 요청"""
    section: str = "ALL"  # ALL, PROFILE, NOTIFICATION, SECURITY, DISPLAY, TRADING

class SettingsGetResponse(BaseResponse):
    """설정 조회 응답"""
    settings: Optional[UserSettings] = None
    notification_settings: Optional[NotificationSettings] = None
    security_settings: Optional[SecuritySettings] = None

class SettingsUpdateRequest(BaseRequest):
    """설정 업데이트 요청"""
    section: str  # PROFILE, NOTIFICATION, SECURITY, DISPLAY, TRADING
    settings: Dict[str, Any]

class SettingsUpdateResponse(BaseResponse):
    """설정 업데이트 응답"""
    updated_settings: Optional[UserSettings] = None
    message: str = ""

class SettingsResetRequest(BaseRequest):
    """설정 초기화 요청"""
    section: str  # PROFILE, NOTIFICATION, SECURITY, DISPLAY, TRADING, ALL
    confirm: bool = False

class SettingsResetResponse(BaseResponse):
    """설정 초기화 응답"""
    reset_settings: Optional[UserSettings] = None
    message: str = ""

# ============================================================================
# 보안 설정 특수 기능
# ============================================================================

class SettingsOTPToggleRequest(BaseRequest):
    """OTP 활성화/비활성화"""
    enable: bool
    current_password: str
    otp_code: Optional[str] = ""  # 비활성화시 필요

class SettingsOTPToggleResponse(BaseResponse):
    """OTP 토글 응답"""
    otp_enabled: bool = False
    qr_code_url: Optional[str] = ""  # 활성화시 제공
    backup_codes: List[str] = []
    message: str = ""

class SettingsPasswordChangeRequest(BaseRequest):
    """비밀번호 변경"""
    current_password: str
    new_password: str
    otp_code: Optional[str] = ""

class SettingsPasswordChangeResponse(BaseResponse):
    """비밀번호 변경 응답"""
    message: str = ""
    require_relogin: bool = True

class SettingsExportDataRequest(BaseRequest):
    """데이터 내보내기"""
    data_types: List[str] = ["PORTFOLIO", "TRANSACTIONS", "SETTINGS"]
    format: str = "JSON"  # JSON, CSV, XLSX

class SettingsExportDataResponse(BaseResponse):
    """데이터 내보내기 응답"""
    download_url: str = ""
    file_size: int = 0
    expires_at: str = ""