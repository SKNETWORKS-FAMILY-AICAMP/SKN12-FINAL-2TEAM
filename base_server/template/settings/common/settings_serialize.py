from service.net.protocol_base import BaseRequest, BaseResponse
from .settings_model import UserSettings, NotificationSettings, SecuritySettings
from typing import Optional, List, Dict, Any

# ============================================================================
# REQ-SET-001: 설정 조회
# 의거: 화면 020 (설정 메인), REQ-SET-001
# ============================================================================

class SettingsGetRequest(BaseRequest):
    """설정 조회 요청"""
    category: str = "ALL"  # ALL, PROFILE, NOTIFICATION, SECURITY, DISPLAY, TRADING

class SettingsGetResponse(BaseResponse):
    """설정 조회 응답"""
    settings: Optional[UserSettings] = None
    notification_settings: Optional[NotificationSettings] = None
    security_settings: Optional[SecuritySettings] = None

# ============================================================================
# REQ-SET-002: 프로필 설정 업데이트
# 의거: 화면 020-1 (프로필 설정), REQ-SET-002
# ============================================================================

class SettingsUpdateProfileRequest(BaseRequest):
    """프로필 설정 업데이트 요청"""
    investment_experience: str = ""  # BEGINNER, INTERMEDIATE, EXPERT
    risk_tolerance: str = ""  # CONSERVATIVE, MODERATE, AGGRESSIVE
    investment_goal: str = ""  # GROWTH, INCOME, PRESERVATION
    monthly_budget: float = 0.0

class SettingsUpdateProfileResponse(BaseResponse):
    """프로필 설정 업데이트 응답"""
    message: str = ""

# ============================================================================
# REQ-SET-003: 알림 설정 업데이트
# 의거: 화면 020-2 (알림 설정), REQ-SET-003
# ============================================================================

class SettingsUpdateNotificationRequest(BaseRequest):
    """알림 설정 업데이트 요청"""
    price_alerts: bool = True
    news_alerts: bool = True
    portfolio_alerts: bool = False
    trade_alerts: bool = True
    system_alerts: bool = True
    email_notifications: bool = True
    push_notifications: bool = True
    sms_notifications: bool = False
    price_change_threshold: float = 0.05  # 5%
    news_keywords: List[str] = []
    daily_summary: bool = True
    weekly_report: bool = True
    quiet_hours_enabled: bool = False
    quiet_hours_start: str = "22:00"
    quiet_hours_end: str = "08:00"

class SettingsUpdateNotificationResponse(BaseResponse):
    """알림 설정 업데이트 응답"""
    message: str = ""

# ============================================================================
# REQ-SET-004: 보안 설정 업데이트
# 의거: 화면 020-3 (보안 설정), REQ-SET-004
# ============================================================================

class SettingsUpdateSecurityRequest(BaseRequest):
    """보안 설정 업데이트 요청"""
    otp_enabled: bool = False
    biometric_enabled: bool = False
    session_timeout: int = 30  # 분
    login_alerts: bool = True
    device_trust_enabled: bool = True
    auto_logout_inactive: bool = True
    transaction_pin_required: bool = False
    ip_whitelist: List[str] = []

class SettingsUpdateSecurityResponse(BaseResponse):
    """보안 설정 업데이트 응답"""
    message: str = ""

# ============================================================================
# REQ-SET-005: 화면 설정 업데이트
# 의거: 화면 020-4 (화면 설정), REQ-SET-005
# ============================================================================

class SettingsUpdateDisplayRequest(BaseRequest):
    """화면 설정 업데이트 요청"""
    theme: str = "DARK"  # LIGHT, DARK, AUTO
    language: str = "KO"  # KO, EN
    currency: str = "KRW"  # KRW, USD, EUR, JPY
    chart_style: str = "CANDLE"  # CANDLE, LINE, BAR
    default_chart_period: str = "1D"  # 1D, 1W, 1M, 3M, 1Y
    auto_refresh_interval: int = 30  # 초
    sound_effects: bool = True
    animation_effects: bool = True
    compact_mode: bool = False

class SettingsUpdateDisplayResponse(BaseResponse):
    """화면 설정 업데이트 응답"""
    message: str = ""

# ============================================================================
# REQ-SET-006: 거래 설정 업데이트
# 의거: 화면 020-5 (거래 설정), REQ-SET-006
# ============================================================================

class SettingsUpdateTradingRequest(BaseRequest):
    """거래 설정 업데이트 요청"""
    auto_trading_enabled: bool = False
    max_daily_trades: int = 10
    max_position_size: float = 0.1  # 10%
    default_order_type: str = "LIMIT"  # MARKET, LIMIT, STOP
    default_stop_loss: float = -0.05  # -5%
    default_take_profit: float = 0.15  # +15%
    risk_management_level: str = "MEDIUM"  # LOW, MEDIUM, HIGH
    confirmation_required: bool = True
    pre_market_trading: bool = False
    after_hours_trading: bool = False

class SettingsUpdateTradingResponse(BaseResponse):
    """거래 설정 업데이트 응답"""
    message: str = ""

# ============================================================================
# REQ-SET-007: 설정 초기화
# 의거: 화면 020 (설정 초기화), REQ-SET-007
# ============================================================================

class SettingsResetRequest(BaseRequest):
    """설정 초기화 요청"""
    category: str  # PROFILE, NOTIFICATION, SECURITY, DISPLAY, TRADING, ALL
    confirm: bool = False

class SettingsResetResponse(BaseResponse):
    """설정 초기화 응답"""
    message: str = ""

# ============================================================================
# REQ-SET-008: 설정 내보내기
# 의거: 화면 020 (설정 백업), REQ-SET-008
# ============================================================================

class SettingsExportRequest(BaseRequest):
    """설정 내보내기 요청"""
    format: str = "JSON"  # JSON, CSV
    include_security: bool = False  # 보안 설정 포함 여부

class SettingsExportResponse(BaseResponse):
    """설정 내보내기 응답"""
    data: str = ""
    filename: str = ""
    export_date: str = ""

# ============================================================================
# REQ-SET-009: 설정 가져오기
# 의거: 화면 020 (설정 복원), REQ-SET-009
# ============================================================================

class SettingsImportRequest(BaseRequest):
    """설정 가져오기 요청"""
    data: str
    overwrite: bool = False
    validate_only: bool = False  # 검증만 수행

class SettingsImportResponse(BaseResponse):
    """설정 가져오기 응답"""
    success: bool = False
    imported_count: int = 0
    skipped_count: int = 0
    errors: List[str] = []
    message: str = ""

# ============================================================================
# REQ-SET-010: 설정 템플릿 적용
# 의거: 화면 020 (설정 템플릿), REQ-SET-010
# ============================================================================

class SettingsApplyTemplateRequest(BaseRequest):
    """설정 템플릿 적용 요청"""
    template_id: str  # conservative_template, moderate_template, aggressive_template, beginner_template

class SettingsApplyTemplateResponse(BaseResponse):
    """설정 템플릿 적용 응답"""
    applied_settings: Dict[str, Any] = {}
    message: str = ""

# ============================================================================
# REQ-SET-011: 설정 템플릿 목록 조회
# 의거: 화면 020 (템플릿 선택), REQ-SET-011
# ============================================================================

class SettingsGetTemplatesRequest(BaseRequest):
    """설정 템플릿 목록 조회 요청"""
    category: str = "ALL"  # ALL, CONSERVATIVE, MODERATE, AGGRESSIVE, BEGINNER, EXPERT

class SettingsGetTemplatesResponse(BaseResponse):
    """설정 템플릿 목록 조회 응답"""
    templates: List[Dict[str, Any]] = []
    total_count: int = 0

# ============================================================================
# REQ-SET-012: 설정 변경 이력 조회
# 의거: 화면 020 (설정 이력), REQ-SET-012
# ============================================================================

class SettingsGetHistoryRequest(BaseRequest):
    """설정 변경 이력 조회 요청"""
    category: str = "ALL"
    start_date: str = ""
    end_date: str = ""
    page: int = 1
    limit: int = 20

class SettingsGetHistoryResponse(BaseResponse):
    """설정 변경 이력 조회 응답"""
    history: List[Dict[str, Any]] = []
    total_count: int = 0
    page: int = 1
    total_pages: int = 1

# ============================================================================
# REQ-SET-013: 개인화 설정 업데이트
# 의거: 화면 020-6 (개인화), REQ-SET-013
# ============================================================================

class SettingsUpdatePersonalizationRequest(BaseRequest):
    """개인화 설정 업데이트 요청"""
    dashboard_layout: Dict[str, Any] = {}  # 대시보드 레이아웃
    watchlist_columns: List[str] = []  # 관심종목 표시 컬럼
    portfolio_view: str = "LIST"  # LIST, GRID, CARD
    default_portfolio_period: str = "1M"
    chart_indicators: List[str] = []  # 기본 차트 지표

class SettingsUpdatePersonalizationResponse(BaseResponse):
    """개인화 설정 업데이트 응답"""
    message: str = ""