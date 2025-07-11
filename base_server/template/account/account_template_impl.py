import hashlib
import uuid
import json
from datetime import datetime, timedelta
from template.base.template.account_template import AccountTemplate
from template.base.template_context import TemplateContext
from template.base.template_type import TemplateType
from template.account.common.account_serialize import (
    AccountLoginRequest, AccountLoginResponse,
    AccountLogoutRequest, AccountLogoutResponse,
    AccountSignupRequest, AccountSignupResponse,
    AccountInfoRequest, AccountInfoResponse,
    AccountEmailVerifyRequest, AccountEmailVerifyResponse,
    AccountEmailConfirmRequest, AccountEmailConfirmResponse,
    AccountOTPSetupRequest, AccountOTPSetupResponse,
    AccountOTPVerifyRequest, AccountOTPVerifyResponse,
    AccountOTPLoginRequest, AccountOTPLoginResponse,
    AccountProfileSetupRequest, AccountProfileSetupResponse,
    AccountProfileGetRequest, AccountProfileGetResponse,
    AccountProfileUpdateRequest, AccountProfileUpdateResponse,
    AccountTokenRefreshRequest, AccountTokenRefreshResponse,
    AccountTokenValidateRequest, AccountTokenValidateResponse
)
from template.account.common.account_model import AccountInfo, UserInfo, OTPInfo, UserProfile
from service.service_container import ServiceContainer
from service.core.logger import Logger
from service.cache.cache_service import CacheService
from service.security.security_utils import SecurityUtils

class AccountTemplateImpl(AccountTemplate):
    def __init__(self):
        super().__init__()
    
    def _hash_password(self, password: str) -> str:
        """패스워드 해시화 - bcrypt 사용"""
        return SecurityUtils.hash_password(password)
    
    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """비밀번호 검증"""
        # 기존 SHA-256 해시와의 호환성 검사
        if len(hashed_password) == 64:  # SHA-256 해시 길이
            legacy_hash = SecurityUtils.hash_for_legacy_compatibility(password)
            return legacy_hash == hashed_password
        # bcrypt 검증
        return SecurityUtils.verify_password(password, hashed_password)
    
    async def on_account_login_req(self, client_session, request: AccountLoginRequest):
        """로그인 요청 처리"""
        response = AccountLoginResponse()
        response.sequence = request.sequence
        
        Logger.info(f"Login request received: {request.account_id}")
        
        try:
            # 데이터베이스 서비스 가져오기
            db_service = ServiceContainer.get_database_service()
            
            # 1. 글로벌 DB에서 계정 인증 (finance DB 구조)
            hashed_password = self._hash_password(request.password)
            result = await db_service.call_global_procedure(
                "fp_user_login",
                (request.platform_type, request.account_id, hashed_password)
            )
            
            if result and len(result) > 0:
                user_data = result[0]
                login_result = user_data.get('result')
                
                if login_result == 'SUCCESS':
                    account_db_key = user_data.get('account_db_key')
                    shard_id = user_data.get('shard_id', 1)
                    
                    # 응답 설정
                    response.errorCode = 0
                    response.nickname = user_data.get('nickname', '')
                    
                    # account_info 설정 (내부 세션 생성용, 클라이언트 응답에서는 제거됨)
                    response.account_info = {
                        "account_db_key": account_db_key,
                        "platform_type": request.platform_type,
                        "account_id": request.account_id,
                        "account_level": user_data.get('account_level', 1),
                        "shard_id": shard_id
                    }
                    
                    Logger.info(f"Login successful: account_db_key={account_db_key}, shard_id={shard_id}")
                    
                elif login_result == 'BLOCKED':
                    response.errorCode = 1003  # 계정 블록
                    Logger.info(f"Login failed: account blocked {request.account_id}")
                else:
                    response.errorCode = 1001  # 로그인 실패
                    Logger.info(f"Login failed: invalid credentials for {request.account_id}")
            else:
                response.errorCode = 1002  # 사용자 없음
                Logger.info(f"Login failed: user not found {request.account_id}")
                
        except Exception as e:
            response.errorCode = 1000  # 서버 오류
            Logger.error(f"Login error: {e}")
        
        return response

    async def on_account_logout_req(self, client_session, request: AccountLogoutRequest):
        """로그아웃 요청 처리"""
        response = AccountLogoutResponse()
        response.sequence = request.sequence
        
        Logger.info(f"Logout request received")
        
        try:
            db_service = ServiceContainer.get_database_service()
            
            if client_session and hasattr(client_session, 'session') and client_session.session:
                account_db_key = getattr(client_session.session, 'account_db_key', None)
                if account_db_key:
                    # 글로벌 DB에서 로그아웃 처리 (finance DB 구조)
                    await db_service.call_global_procedure(
                        "fp_user_logout",
                        (account_db_key,)
                    )
                    Logger.info(f"Account {account_db_key} logged out")
            
            response.errorCode = 0
            response.message = "로그아웃 성공"
            
        except Exception as e:
            response.errorCode = 2000  # 로그아웃 오류
            response.message = "로그아웃 실패"
            Logger.error(f"Logout error: {e}")
        
        return response

    async def on_account_signup_req(self, client_session, request: AccountSignupRequest):
        """회원가입 요청 처리"""
        response = AccountSignupResponse()
        response.sequence = request.sequence
        
        Logger.info(f"Signup request received: {request.account_id}")
        
        try:
            db_service = ServiceContainer.get_database_service()
            
            # 글로벌 DB에서 회원가입 처리 (finance DB 구조)
            hashed_password = self._hash_password(request.password)
            result = await db_service.call_global_procedure(
                "fp_user_register",
                (request.platform_type, request.account_id, hashed_password, request.nickname, request.email)
            )
            
            if result and len(result) > 0:
                signup_result = result[0]
                signup_status = signup_result.get('result')
                
                if signup_status == 'SUCCESS':
                    account_db_key = signup_result.get('account_db_key', 0)
                    
                    response.errorCode = 0
                    response.message = "회원가입 성공"
                    Logger.info(f"Signup successful: account_db_key={account_db_key}")
                    
                elif signup_status == 'DUPLICATE_ID':
                    response.errorCode = 3001  # 중복 ID
                    response.message = "이미 존재하는 ID입니다"
                    Logger.info(f"Signup failed: duplicate ID {request.account_id}")
                else:
                    response.errorCode = 3002  # 회원가입 실패
                    response.message = "회원가입 실패"
                    Logger.info(f"Signup failed: {response.message}")
            else:
                response.errorCode = 3003  # 처리 오류
                response.message = "회원가입 처리 오류"
                Logger.error(f"Signup failed: no result returned")
                
        except Exception as e:
            response.errorCode = 3000  # 서버 오류
            response.message = "서버 오류"
            Logger.error(f"Signup error: {e}")
        
        return response
    
    async def on_account_info_req(self, client_session, request: AccountInfoRequest):
        """계좌 정보 조회 (샤딩 DB 사용 예시)"""
        response = AccountInfoResponse()
        response.sequence = request.sequence
        
        Logger.info(f"Account info request received")
        
        try:
            if not client_session or not client_session.session:
                response.errorCode = 2001  # 세션 없음
                Logger.info("Account info failed: no session")
                return response
            
            # 세션에서 사용자 정보 가져오기
            account_db_key = getattr(client_session.session, 'account_db_key', 0)
            shard_id = getattr(client_session.session, 'shard_id', 1)
            
            if account_db_key == 0:
                response.errorCode = 2002  # 잘못된 세션
                Logger.info("Account info failed: invalid session")
                return response
            
            # 데이터베이스 서비스 가져오기
            db_service = ServiceContainer.get_database_service()
            
            # 샤드 DB에서 계좌 정보 조회
            Logger.info(f"Querying shard {shard_id} for account_db_key {account_db_key}")
            result = await db_service.call_shard_procedure(
                shard_id,
                "fp_get_account_info",
                (account_db_key,)
            )
            
            if result and len(result) > 0:
                account_data = result[0]
                
                # AccountInfo 모델로 변환
                account_info = AccountInfo(
                    account_number=account_data.get('account_number', ''),
                    balance=float(account_data.get('balance', 0.0)),
                    account_type=account_data.get('account_type', ''),
                    account_status=account_data.get('account_status', ''),
                    currency_code=account_data.get('currency_code', 'USD'),
                    created_at=str(account_data.get('created_at', ''))
                )
                
                response.errorCode = 0
                response.account_info = account_info
                
                Logger.info(f"Account info retrieved successfully from shard {shard_id}")
            else:
                # 계좌가 없으면 새로 생성
                Logger.info(f"No account found, creating new account for account_db_key {account_db_key}")
                create_result = await db_service.call_shard_procedure(
                    shard_id,
                    "fp_create_account",
                    (account_db_key, "checking")
                )
                
                if create_result and len(create_result) > 0:
                    create_data = create_result[0]
                    if create_data.get('result') == 'SUCCESS':
                        account_number = create_data.get('account_number', '')
                        
                        account_info = AccountInfo(
                            account_number=account_number,
                            balance=0.0,
                            account_type="checking",
                            account_status="active",
                            currency_code="USD",
                            created_at=str(datetime.now())
                        )
                        
                        response.errorCode = 0
                        response.account_info = account_info
                        
                        Logger.info(f"New account created: {account_number} on shard {shard_id}")
                    else:
                        response.errorCode = 2004  # 계좌 생성 실패
                        Logger.error("Account creation failed")
                else:
                    response.errorCode = 2003  # 계좌 없음
                    Logger.info("No account found and creation failed")
                
        except Exception as e:
            response.errorCode = 2000  # 서버 오류
            Logger.error(f"Account info error: {e}")
        
        return response

    # ============================================================================
    # 새로운 메서드들 - 패킷명세서 기반
    # ============================================================================

    async def on_account_email_verify_req(self, client_session, request: AccountEmailVerifyRequest):
        """이메일 인증 코드 전송"""
        response = AccountEmailVerifyResponse()
        response.sequence = request.sequence
        
        Logger.info(f"Email verify request: {request.email}")
        
        try:
            # 이메일 인증 코드 생성 및 전송 로직
            verification_code = str(uuid.uuid4())[:6].upper()
            
            # Redis에 인증 코드 저장 (5분 만료)
            cache_service = ServiceContainer.get_cache_service()
            await cache_service.set(f"email_verify:{request.email}", verification_code, 300)
            
            # 실제로는 이메일 발송 서비스 호출
            Logger.info(f"Email verification code sent: {verification_code}")
            
            response.errorCode = 0
            response.message = "인증 코드가 전송되었습니다"
            response.expire_time = 300
            
        except Exception as e:
            response.errorCode = 1000
            response.message = "이메일 전송 실패"
            Logger.error(f"Email verify error: {e}")
        
        return response

    async def on_account_email_confirm_req(self, client_session, request: AccountEmailConfirmRequest):
        """이메일 인증 코드 확인"""
        response = AccountEmailConfirmResponse()
        response.sequence = request.sequence
        
        Logger.info(f"Email confirm request: {request.email}")
        
        try:
            # Redis에서 인증 코드 확인
            cache_service = ServiceContainer.get_cache_service()
            stored_code = await cache_service.get(f"email_verify:{request.email}")
            
            if stored_code and stored_code == request.verification_code:
                response.errorCode = 0
                response.is_verified = True
                response.message = "이메일 인증 완료"
                response.next_step = "OTP_SETUP"
                
                # 인증 완료 플래그 설정
                await cache_service.set(f"email_verified:{request.email}", "true", 3600)
                
            else:
                response.errorCode = 1001
                response.is_verified = False
                response.message = "인증 코드가 올바르지 않습니다"
            
        except Exception as e:
            response.errorCode = 1000
            response.message = "인증 확인 실패"
            Logger.error(f"Email confirm error: {e}")
        
        return response

    async def on_account_otp_setup_req(self, client_session, request: AccountOTPSetupRequest):
        """OTP 설정"""
        response = AccountOTPSetupResponse()
        response.sequence = request.sequence
        
        Logger.info(f"OTP setup request: {request.account_id}")
        
        try:
            # OTP 시크릿 키 생성 (실제로는 pyotp 라이브러리 사용)
            secret_key = "JBSWY3DPEHPK3PXP"  # 샘플 키
            
            # QR 코드 URL 생성
            qr_url = f"otpauth://totp/Investment Platform:{request.account_id}?secret={secret_key}&issuer=Investment Platform"
            
            otp_info = OTPInfo(
                secret_key=secret_key,
                qr_code_url=qr_url,
                backup_codes=[],
                is_enabled=False
            )
            
            response.errorCode = 0
            response.otp_info = otp_info
            response.qr_code_data = qr_url
            
        except Exception as e:
            response.errorCode = 1000
            Logger.error(f"OTP setup error: {e}")
        
        return response

    async def on_account_otp_verify_req(self, client_session, request: AccountOTPVerifyRequest):
        """OTP 인증"""
        response = AccountOTPVerifyResponse()
        response.sequence = request.sequence
        
        Logger.info(f"OTP verify request: {request.account_id}")
        
        try:
            # 실제로는 DB에서 사용자의 OTP 시크릿 키를 가져와서 검증
            response.errorCode = 0
            response.is_verified = True
            response.message = "OTP 인증 완료"
            response.next_step = "PROFILE_SETUP"
            
        except Exception as e:
            response.errorCode = 1000
            Logger.error(f"OTP verify error: {e}")
        
        return response

    async def on_account_otp_login_req(self, client_session, request: AccountOTPLoginRequest):
        """OTP 로그인 2단계"""
        response = AccountOTPLoginResponse()
        response.sequence = request.sequence
        
        Logger.info("OTP login request received")
        
        try:
            # temp_token 검증 및 OTP 코드 확인
            response.errorCode = 0
            response.accessToken = "final_access_token"
            response.refreshToken = "refresh_token"
            response.nickname = "투자왕"
            response.profile_completed = True
            
        except Exception as e:
            response.errorCode = 1000
            Logger.error(f"OTP login error: {e}")
        
        return response

    async def on_account_profile_setup_req(self, client_session, request: AccountProfileSetupRequest):
        """프로필 설정"""
        response = AccountProfileSetupResponse()
        response.sequence = request.sequence
        
        Logger.info("Profile setup request received")
        
        try:
            if not client_session or not client_session.session:
                response.errorCode = 2001
                return response
            
            account_db_key = getattr(client_session.session, 'account_db_key', 0)
            
            # 프로필 정보 저장
            profile = UserProfile(
                account_db_key=account_db_key,
                investment_experience=request.investment_experience,
                risk_tolerance=request.risk_tolerance,
                investment_goal=request.investment_goal,
                monthly_budget=request.monthly_budget,
                profile_completed=True
            )
            
            response.errorCode = 0
            response.profile = profile
            response.message = "프로필 설정 완료"
            response.next_step = "TUTORIAL"
            
        except Exception as e:
            response.errorCode = 1000
            Logger.error(f"Profile setup error: {e}")
        
        return response

    async def on_account_profile_get_req(self, client_session, request: AccountProfileGetRequest):
        """프로필 조회"""
        response = AccountProfileGetResponse()
        response.sequence = request.sequence
        
        try:
            if not client_session or not client_session.session:
                response.errorCode = 2001
                return response
            
            account_db_key = getattr(client_session.session, 'account_db_key', 0)
            
            # 샘플 프로필 데이터
            profile = UserProfile(
                account_id="user@example.com",
                nickname="투자왕",
                email="user@example.com",
                investment_experience="INTERMEDIATE",
                risk_tolerance="MODERATE",
                investment_goal="GROWTH",
                monthly_budget=100000.0,
                profile_completed=True
            )
            
            response.errorCode = 0
            response.profile = profile
            
        except Exception as e:
            response.errorCode = 1000
            Logger.error(f"Profile get error: {e}")
        
        return response

    async def on_account_profile_update_req(self, client_session, request: AccountProfileUpdateRequest):
        """프로필 수정"""
        response = AccountProfileUpdateResponse()
        response.sequence = request.sequence
        
        try:
            if not client_session or not client_session.session:
                response.errorCode = 2001
                return response
            
            # 프로필 업데이트 로직
            response.errorCode = 0
            response.message = "프로필이 업데이트되었습니다"
            
        except Exception as e:
            response.errorCode = 1000
            Logger.error(f"Profile update error: {e}")
        
        return response

    async def on_account_token_refresh_req(self, client_session, request: AccountTokenRefreshRequest):
        """토큰 갱신"""
        response = AccountTokenRefreshResponse()
        response.sequence = request.sequence
        
        try:
            # refreshToken 검증 및 새 토큰 발급
            response.errorCode = 0
            response.accessToken = "new_access_token"
            response.refreshToken = "new_refresh_token"
            response.expires_in = 3600
            
        except Exception as e:
            response.errorCode = 1000
            Logger.error(f"Token refresh error: {e}")
        
        return response

    async def on_account_token_validate_req(self, client_session, request: AccountTokenValidateRequest):
        """토큰 검증"""
        response = AccountTokenValidateResponse()
        response.sequence = request.sequence
        
        try:
            if client_session and client_session.session:
                response.errorCode = 0
                response.is_valid = True
                response.expires_at = str(datetime.now() + timedelta(hours=1))
            else:
                response.errorCode = 1002
                response.is_valid = False
                
        except Exception as e:
            response.errorCode = 1000
            Logger.error(f"Token validate error: {e}")
        
        return response
