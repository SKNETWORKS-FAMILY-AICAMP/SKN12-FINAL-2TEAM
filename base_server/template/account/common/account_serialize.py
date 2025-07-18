from typing import Optional, Dict, Any, List
from service.net.protocol_base import BaseRequest, BaseResponse
from .account_model import UserInfo, OTPInfo, UserProfile, AccountInfo

# ============================================================================
# 회원가입 (REQ-AUTH-001~009)
# 의거: 화면 002-2 (회원가입 페이지), REQ-AUTH-001~009
# ============================================================================

class AccountSignupRequest(BaseRequest):
    """회원가입 요청"""
    platform_type: int = 1
    account_id: str
    password: str
    password_confirm: str = ""
    nickname: str = ""
    email: str = ""
    name: str = ""
    birth_year: int = 0
    birth_month: int = 0
    birth_day: int = 0
    gender: str = ""  # M, F, OTHER

class AccountSignupResponse(BaseResponse):
    """회원가입 응답"""
    user_id: str = ""
    message: str = ""
    next_step: str = "EMAIL_VERIFICATION"

# ============================================================================
# 이메일 인증 (REQ-AUTH-008)  
# 의거: 화면 002-3 (이메일 인증), REQ-AUTH-008
# ============================================================================

class AccountEmailVerifyRequest(BaseRequest):
    """이메일 인증 코드 전송 요청"""
    email: str

class AccountEmailVerifyResponse(BaseResponse):
    """이메일 인증 코드 전송 응답"""
    message: str = ""
    expire_time: int = 300  # 5분

class AccountEmailConfirmRequest(BaseRequest):
    """이메일 인증 코드 확인 요청"""
    email: str
    verification_code: str

class AccountEmailConfirmResponse(BaseResponse):
    """이메일 인증 코드 확인 응답"""
    is_verified: bool = False
    message: str = ""
    next_step: str = "OTP_SETUP"

# ============================================================================
# OTP 설정 (REQ-AUTH-013~016)
# 의거: 화면 002-4 (OTP 등록), REQ-AUTH-013~016  
# ============================================================================

class AccountOTPSetupRequest(BaseRequest):
    """OTP 설정 요청"""
    account_id: str

class AccountOTPSetupResponse(BaseResponse):
    """OTP 설정 응답"""
    otp_info: Optional[OTPInfo] = None
    qr_code_data: str = ""

class AccountOTPVerifyRequest(BaseRequest):
    """OTP 인증 요청"""
    account_id: str
    otp_code: str

class AccountOTPVerifyResponse(BaseResponse):
    """OTP 인증 응답"""
    is_verified: bool = False
    message: str = ""
    next_step: str = "PROFILE_SETUP"

# ============================================================================
# 로그인 (REQ-AUTH-010~016)
# 의거: 화면 002-1 (로그인 페이지), REQ-AUTH-010~016, 기존 account_serialize.py
# ============================================================================

class AccountLoginRequest(BaseRequest):
    """로그인 1단계 요청"""
    platform_type: int = 1
    account_id: str
    password: str

class AccountLoginResponse(BaseResponse):
    """로그인 1단계 응답"""
    accessToken: str = ""  # OTP 미사용시 바로 발급
    temp_token: str = ""   # OTP 사용시 임시 토큰
    nickname: str = ""
    requires_otp: bool = False
    profile_completed: bool = False
    account_info: Optional[Dict[str, Any]] = None  # 내부 세션 생성용, 클라이언트 응답에서는 제거됨

class AccountOTPLoginRequest(BaseRequest):
    """로그인 2단계 OTP 인증"""
    temp_token: str
    otp_code: str

class AccountOTPLoginResponse(BaseResponse):
    """로그인 2단계 OTP 인증 응답"""
    accessToken: str = ""
    refreshToken: str = ""
    nickname: str = ""
    profile_completed: bool = False

class AccountLogoutRequest(BaseRequest):
    """로그아웃 요청"""
    pass

class AccountLogoutResponse(BaseResponse):
    """로그아웃 응답"""
    message: str = "Successfully logged out"

# ============================================================================
# 계좌 정보 조회 (기존 코드 기반)
# ============================================================================

class AccountInfoRequest(BaseRequest):
    """계좌 정보 조회 요청"""
    pass

class AccountInfoResponse(BaseResponse):
    """계좌 정보 조회 응답"""
    account_info: Optional[AccountInfo] = None

# ============================================================================
# 프로필 설정 (사용자 정의 질문)
# 의거: 화면 003 (프로필설정), REQ-AUTH-009
# ============================================================================

class AccountProfileSetupRequest(BaseRequest):
    """프로필 설정 요청 - 투자 정보만 처리 (생년월일/성별은 회원가입 시 처리됨)"""
    investment_experience: str  # "초급", "중급", "고급"
    risk_tolerance: str         # "보수적", "보통", "공격적"  
    investment_goal: str        # "장기투자", "단기수익", "안정성"
    monthly_budget: float       # 월 투자 예산

class AccountProfileSetupResponse(BaseResponse):
    """프로필 설정 응답"""
    profile: Optional[UserProfile] = None
    message: str = ""
    next_step: str = "TUTORIAL"

class AccountProfileGetRequest(BaseRequest):
    """프로필 조회 요청"""
    pass

class AccountProfileGetResponse(BaseResponse):
    """프로필 조회 응답"""
    profile: Optional[UserProfile] = None
    message: str = ""

class AccountProfileUpdateRequest(BaseRequest):
    """프로필 수정 요청 - 투자 정보만 처리 (생년월일/성별은 회원가입 시 처리됨)"""
    investment_experience: str  # "초급", "중급", "고급" - 필수
    risk_tolerance: str         # "보수적", "보통", "공격적" - 필수
    investment_goal: str        # "장기투자", "단기수익", "안정성" - 필수
    monthly_budget: float       # 월 투자 예산 - 필수

class AccountProfileUpdateResponse(BaseResponse):
    """프로필 수정 응답"""
    profile: Optional[UserProfile] = None
    message: str = ""

# ============================================================================
# 토큰 관리
# ============================================================================

class AccountTokenRefreshRequest(BaseRequest):
    """토큰 갱신 요청"""
    refreshToken: str

class AccountTokenRefreshResponse(BaseResponse):
    """토큰 갱신 응답"""
    accessToken: str = ""
    refreshToken: str = ""
    expires_in: int = 3600  # 1시간

class AccountTokenValidateRequest(BaseRequest):
    """토큰 검증 요청"""
    pass

class AccountTokenValidateResponse(BaseResponse):
    """토큰 검증 응답"""
    is_valid: bool = False
    user_info: Optional[UserInfo] = None
    expires_at: str = ""