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
from service.data.data_table_manager import DataTableManager

class AccountTemplateImpl(AccountTemplate):
    def __init__(self):
        super().__init__()
        
    def on_load_data(self, config):
        """계정 템플릿 전용 데이터 로딩"""
        try:
            # 예: 계정 관련 설정 테이블이 있다면 여기서 로드
            Logger.info("Account 템플릿 데이터 로드 시작")
            
            # 아이템 테이블 예제 (다른 템플릿에서도 사용 가능)
            items_table = DataTableManager.get_table("items")
            if items_table:
                Logger.info(f"Account 템플릿에서 아이템 테이블 접근 가능: {items_table.count()}개")
            
            Logger.info("Account 템플릿 데이터 로드 완료")
        except Exception as e:
            Logger.error(f"Account 템플릿 데이터 로드 실패: {e}")
            
    def on_client_create(self, db_client, client_session):
        """신규 클라이언트 생성 시 호출"""
        try:
            account_db_key = getattr(client_session.session, 'account_db_key', 0) if client_session.session else 0
            Logger.info(f"Account: 신규 클라이언트 생성 - Account DB Key: {account_db_key}")
            
            # 예: 신규 유저 기본 아이템 지급
            items_table = DataTableManager.get_table("items")
            if items_table:
                # 초급 검과 초급 갑옷 지급
                starter_sword = items_table.get("1001")
                starter_armor = items_table.get("2001")
                
                if starter_sword and starter_armor:
                    Logger.info(f"신규 유저에게 시작 아이템 지급: {starter_sword.name}, {starter_armor.name}")
                    # TODO: 실제 DB에 아이템 추가 로직
                    
        except Exception as e:
            Logger.error(f"Account 클라이언트 생성 처리 실패: {e}")
            
    def on_client_update(self, db_client, client_session):
        """클라이언트 업데이트 시 호출"""
        try:
            account_db_key = getattr(client_session.session, 'account_db_key', 0) if client_session.session else 0
            Logger.info(f"Account: 클라이언트 업데이트 - Account DB Key: {account_db_key}")
            # 예: 로그인 시간 업데이트, 일일 보상 체크 등
        except Exception as e:
            Logger.error(f"Account 클라이언트 업데이트 처리 실패: {e}")
    
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
            
            # 1. 먼저 DB에서 저장된 해시값 및 프로필 완료 상태 조회
            user_query = """
            SELECT a.account_db_key, a.password_hash, a.nickname, a.account_level, a.account_status,
                   COALESCE(p.profile_completed, 0) as profile_completed
            FROM table_accountid a
            LEFT JOIN table_user_profiles p ON a.account_db_key = p.account_db_key
            WHERE a.platform_type = %s AND a.account_id = %s
            """
            user_result = await db_service.execute_global_query(user_query, (request.platform_type, request.account_id))
            
            if not user_result:
                response.errorCode = 1002  # 사용자 없음
                Logger.info(f"Login failed: user not found {request.account_id}")
                return response
                
            user_data = user_result[0]
            stored_hash = user_data.get('password_hash', '')
            
            # 2. 비밀번호 검증
            if not self._verify_password(request.password, stored_hash):
                response.errorCode = 1001  # 로그인 실패
                Logger.info(f"Login failed: invalid credentials for {request.account_id}")
                return response
                
            # 3. 계정 상태 확인
            if user_data.get('account_status') != 'Normal':
                response.errorCode = 1003  # 계정 블록
                Logger.info(f"Login failed: account blocked {request.account_id}")
                return response
                
            # 4. 로그인 성공 처리
            account_db_key = user_data.get('account_db_key')
            
            # 5. 샤드 정보 조회
            shard_query = """
            SELECT shard_id FROM table_user_shard_mapping 
            WHERE account_db_key = %s
            """
            shard_result = await db_service.execute_global_query(shard_query, (account_db_key,))
            
            shard_id = 1  # 기본값
            if shard_result:
                shard_id = shard_result[0].get('shard_id', 1)
            else:
                # 샤드가 없으면 자동 할당
                shard_id = (account_db_key % 2) + 1
                insert_shard = """
                INSERT INTO table_user_shard_mapping (account_db_key, shard_id)
                VALUES (%s, %s)
                """
                await db_service.execute_global_query(insert_shard, (account_db_key, shard_id))
            
            # 6. 로그인 시간 업데이트
            update_login = """
            UPDATE table_accountid SET login_time = NOW() 
            WHERE account_db_key = %s
            """
            await db_service.execute_global_query(update_login, (account_db_key,))
            
            # 7. 성공 응답 설정
            response.errorCode = 0
            response.nickname = user_data.get('nickname', '')
            response.profile_completed = bool(user_data.get('profile_completed', 0))
            
            # account_info 설정 (내부 세션 생성용, 클라이언트 응답에서는 제거됨)
            response.account_info = {
                "account_db_key": account_db_key,
                "platform_type": request.platform_type,
                "account_id": request.account_id,
                "account_level": user_data.get('account_level', 1),
                "shard_id": shard_id
            }
            
            Logger.info(f"Login successful: account_db_key={account_db_key}, shard_id={shard_id}")
                
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
            
            # 글로벌 DB에서 회원가입 처리 (finance DB 구조) - 옵션 1: 생년월일/성별 포함
            hashed_password = self._hash_password(request.password)
            result = await db_service.call_global_procedure(
                "fp_user_signup",
                (request.platform_type, request.account_id, hashed_password, request.email, request.nickname,
                 request.birth_year, request.birth_month, request.birth_day, request.gender)
            )
            
            if result and len(result) > 0:
                signup_result = result[0]
                signup_status = signup_result.get('result')
                
                if signup_status == 'SUCCESS':
                    account_db_key = signup_result.get('account_db_key', 0)
                    
                    response.errorCode = 0
                    response.user_id = str(account_db_key)
                    response.message = "회원가입 완료"
                    response.next_step = "LOGIN"  # 개발용: 이메일 인증 건너뛰고 바로 로그인 가능
                    Logger.info(f"Signup successful: account_db_key={account_db_key} (ready for login)")
                    
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
            # 세션에서 사용자 정보 가져오기 (세션 검증은 template_service에서 이미 완료)
            account_db_key = getattr(client_session.session, 'account_db_key', 0)
            shard_id = getattr(client_session.session, 'shard_id', 1)
            
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
            # 1. 세션에서 사용자 정보 가져오기 (세션 검증은 template_service에서 이미 완료)
            account_db_key = getattr(client_session.session, 'account_db_key', 0)
            
            # 2. 입력값 검증
            if not all([request.investment_experience, request.risk_tolerance, 
                       request.investment_goal]) or request.monthly_budget < 0:
                response.errorCode = 2004
                response.message = "필수 입력값이 누락되었거나 잘못되었습니다"
                Logger.error("Profile setup failed: Invalid input values")
                return response
            
            db_service = ServiceContainer.get_database_service()
            
            # 3. DB에 프로필 정보 저장 (투자 정보만 처리)
            profile_result = await db_service.call_global_procedure(
                "fp_profile_setup",
                (
                    account_db_key,
                    request.investment_experience,
                    request.risk_tolerance,
                    request.investment_goal,
                    request.monthly_budget
                )
            )
            
            if not profile_result or profile_result[0].get('result') != 'SUCCESS':
                response.errorCode = 2002
                response.message = "프로필 저장 실패"
                Logger.error(f"Profile setup failed for account_db_key={account_db_key}")
                return response
            
            # 4. 저장된 프로필 정보 조회 (최신 데이터 반환)
            profile_get_result = await db_service.call_global_procedure(
                "fp_profile_get",
                (account_db_key,)
            )
            
            if profile_get_result and len(profile_get_result) > 0:
                profile_data = profile_get_result[0]
                profile = UserProfile(
                    account_id=profile_data.get('account_id', ''),
                    nickname=profile_data.get('nickname', ''),
                    email=profile_data.get('email', ''),
                    investment_experience=profile_data.get('investment_experience', request.investment_experience),
                    risk_tolerance=profile_data.get('risk_tolerance', request.risk_tolerance),
                    investment_goal=profile_data.get('investment_goal', request.investment_goal),
                    monthly_budget=float(profile_data.get('monthly_budget', request.monthly_budget)),
                    birth_year=profile_data.get('birth_year'),       # DB에서 조회된 출생년도
                    birth_month=profile_data.get('birth_month'),     # DB에서 조회된 출생월
                    birth_day=profile_data.get('birth_day'),         # DB에서 조회된 출생일
                    gender=profile_data.get('gender'),               # DB에서 조회된 성별
                    profile_completed=True
                )
            else:
                # 조회 실패 시 요청 데이터로 응답 생성
                profile = UserProfile(
                    account_id=getattr(client_session.session, 'account_id', ''),
                    nickname='',
                    email='',
                    investment_experience=request.investment_experience,
                    risk_tolerance=request.risk_tolerance,
                    investment_goal=request.investment_goal,
                    monthly_budget=request.monthly_budget,
                    birth_year=None,                     # 프로필 설정에서는 생년월일 처리 안함
                    birth_month=None,                    # 프로필 설정에서는 생년월일 처리 안함
                    birth_day=None,                      # 프로필 설정에서는 생년월일 처리 안함
                    gender=None,                         # 프로필 설정에서는 성별 처리 안함
                    profile_completed=True
                )
            
            # 5. 포트폴리오 초기화 (프로필 설정 완료 시)
            shard_id = getattr(client_session.session, 'shard_id', 1)
            await self._initialize_user_portfolio_in_shard(db_service, account_db_key, shard_id, request.monthly_budget)
            
            # 6. 성공 응답 설정
            response.errorCode = 0
            response.profile = profile
            response.message = "프로필 설정 완료"
            response.next_step = "TUTORIAL"
            
            Logger.info(f"Profile setup completed successfully for account_db_key={account_db_key}")
            
        except Exception as e:
            response.errorCode = 1000
            response.message = "프로필 설정 중 오류가 발생했습니다"
            Logger.error(f"Profile setup error: {e}")
        
        return response

    async def on_account_profile_get_req(self, client_session, request: AccountProfileGetRequest):
        """프로필 조회"""
        response = AccountProfileGetResponse()
        response.sequence = request.sequence
        
        Logger.info("Profile get request received")
        
        try:
            # 1. 세션에서 사용자 정보 가져오기 (세션 검증은 template_service에서 이미 완료)
            account_db_key = getattr(client_session.session, 'account_db_key', 0)
            
            db_service = ServiceContainer.get_database_service()
            
            # 2. DB에서 프로필 조회
            profile_result = await db_service.call_global_procedure(
                "fp_profile_get",
                (account_db_key,)
            )
            
            if not profile_result or len(profile_result) == 0:
                # 프로필이 없는 경우 기본 프로필 정보 반환
                Logger.warn(f"Profile not found for account_db_key={account_db_key}, returning default profile")
                
                # 기본 계정 정보 조회 (birth/gender 필드 포함)
                account_query = """
                SELECT account_id, nickname, email, birth_year, birth_month, birth_day, gender
                FROM table_accountid 
                WHERE account_db_key = %s
                """
                account_result = await db_service.execute_global_query(account_query, (account_db_key,))
                
                if account_result and len(account_result) > 0:
                    account_data = account_result[0]
                    profile = UserProfile(
                        account_id=account_data.get('account_id', ''),
                        nickname=account_data.get('nickname', ''),
                        email=account_data.get('email', ''),
                        investment_experience='BEGINNER',
                        risk_tolerance='MODERATE',
                        investment_goal='GROWTH',
                        monthly_budget=0.0,
                        birth_year=account_data.get('birth_year'),         # table_accountid에서 조회
                        birth_month=account_data.get('birth_month'),       # table_accountid에서 조회
                        birth_day=account_data.get('birth_day'),           # table_accountid에서 조회
                        gender=account_data.get('gender'),                 # table_accountid에서 조회
                        profile_completed=False
                    )
                    
                    response.errorCode = 0
                    response.profile = profile
                    response.message = "프로필이 설정되지 않았습니다. 프로필을 설정해주세요."
                else:
                    response.errorCode = 2003
                    response.message = "계정 정보를 찾을 수 없습니다"
                
                return response
            
            # 3. 조회된 데이터로 프로필 객체 생성 (클라이언트용)
            profile_data = profile_result[0]
            
            # 데이터 타입 안전성 보장
            try:
                monthly_budget = float(profile_data.get('monthly_budget', 0.0))
            except (ValueError, TypeError):
                monthly_budget = 0.0
                Logger.warn(f"Invalid monthly_budget value for account_db_key={account_db_key}")
            
            profile = UserProfile(
                account_id=profile_data.get('account_id', ''),
                nickname=profile_data.get('nickname', ''),
                email=profile_data.get('email', ''),
                investment_experience=profile_data.get('investment_experience', 'BEGINNER'),
                risk_tolerance=profile_data.get('risk_tolerance', 'MODERATE'),
                investment_goal=profile_data.get('investment_goal', 'GROWTH'),
                monthly_budget=monthly_budget,
                birth_year=profile_data.get('birth_year'),          # table_accountid에서 조회된 출생년도
                birth_month=profile_data.get('birth_month'),        # table_accountid에서 조회된 출생월
                birth_day=profile_data.get('birth_day'),            # table_accountid에서 조회된 출생일
                gender=profile_data.get('gender'),                  # table_accountid에서 조회된 성별
                profile_completed=bool(profile_data.get('profile_completed', 0))
            )
            
            # 4. 성공 응답 설정
            response.errorCode = 0
            response.profile = profile
            response.message = "프로필 조회 성공" if profile.profile_completed else "프로필 설정을 완료해주세요"
            
            Logger.info(f"Profile retrieved successfully for account_db_key={account_db_key}, completed={profile.profile_completed}")
            
        except Exception as e:
            response.errorCode = 1000
            response.message = "프로필 조회 중 오류가 발생했습니다"
            Logger.error(f"Profile get error: {e}")
        
        return response

    async def on_account_profile_update_req(self, client_session, request: AccountProfileUpdateRequest):
        """프로필 수정"""
        response = AccountProfileUpdateResponse()
        response.sequence = request.sequence
        
        Logger.info("Profile update request received")
        
        try:
            # 세션에서 사용자 정보 가져오기 (세션 검증은 template_service에서 이미 완료)
            account_db_key = getattr(client_session.session, 'account_db_key', 0)
            
            db_service = ServiceContainer.get_database_service()
            
            # 1. DB에 프로필 업데이트 (투자 정보만 처리)
            profile_result = await db_service.call_global_procedure(
                "fp_profile_setup",
                (
                    account_db_key,
                    request.investment_experience,
                    request.risk_tolerance,
                    request.investment_goal,
                    request.monthly_budget
                )
            )
            
            if not profile_result or profile_result[0].get('result') != 'SUCCESS':
                response.errorCode = 2002
                response.message = "프로필 업데이트 실패"
                Logger.error(f"Profile update failed for account_db_key={account_db_key}")
                return response
            
            # 2. 업데이트된 프로필 조회
            updated_result = await db_service.call_global_procedure(
                "fp_profile_get",
                (account_db_key,)
            )
            
            if updated_result and len(updated_result) > 0:
                profile_data = updated_result[0]
                profile = UserProfile(
                    account_id=profile_data.get('account_id', ''),
                    nickname=profile_data.get('nickname', ''),
                    email=profile_data.get('email', ''),
                    investment_experience=profile_data.get('investment_experience', 'BEGINNER'),
                    risk_tolerance=profile_data.get('risk_tolerance', 'MODERATE'),
                    investment_goal=profile_data.get('investment_goal', 'GROWTH'),
                    monthly_budget=float(profile_data.get('monthly_budget', 0.0)),
                    birth_year=profile_data.get('birth_year'),          # table_accountid에서 조회된 출생년도
                    birth_month=profile_data.get('birth_month'),        # table_accountid에서 조회된 출생월
                    birth_day=profile_data.get('birth_day'),            # table_accountid에서 조회된 출생일
                    gender=profile_data.get('gender'),                  # table_accountid에서 조회된 성별
                    profile_completed=bool(profile_data.get('profile_completed', 0))
                )
                response.profile = profile
            
            response.errorCode = 0
            response.message = "프로필이 업데이트되었습니다"
            
            Logger.info(f"Profile updated successfully for account_db_key={account_db_key}")
            
        except Exception as e:
            response.errorCode = 1000
            response.message = "프로필 업데이트 중 오류가 발생했습니다"
            Logger.error(f"Profile update error: {e}")
        
        return response

    async def _initialize_user_portfolio_in_shard(self, db_service, account_db_key: int, shard_id: int, monthly_budget: float):
        """샤드 DB에 사용자 포트폴리오 초기화 (프로필 설정 완료 시)"""
        try:
            Logger.info(f"Initializing portfolio in shard {shard_id} for account_db_key={account_db_key}")
            
            # 1. 샤드 DB에 투자 계좌 생성 (fp_create_account 프로시저 사용)
            account_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_create_account",
                (account_db_key, "investment")
            )
            
            if account_result and len(account_result) > 0:
                account_data = account_result[0]
                if account_data.get('result') == 'SUCCESS':
                    account_number = account_data.get('account_number', '')
                    Logger.info(f"Investment account created: {account_number} for account_db_key={account_db_key}")
                elif account_data.get('result') == 'EXISTS':
                    Logger.info(f"Investment account already exists for account_db_key={account_db_key}")
                else:
                    Logger.warn(f"Account creation failed: {account_data}")
                    return
            
            # 2. 포트폴리오 테이블에 초기 현금 설정
            initial_cash = max(monthly_budget * 12, 1000000.0)  # 최소 100만원
            
            # 기존 포트폴리오 확인
            portfolio_check = await db_service.execute_shard_query(
                shard_id,
                "SELECT COUNT(*) as portfolio_count FROM table_user_portfolios WHERE account_db_key = %s",
                (account_db_key,)
            )
            
            if portfolio_check and portfolio_check[0].get('portfolio_count', 0) == 0:
                # 새 포트폴리오 생성 (현금 포지션으로 시작)
                await db_service.execute_shard_query(
                    shard_id,
                    """
                    INSERT INTO table_user_portfolios 
                    (account_db_key, asset_code, asset_type, quantity, average_cost, current_value, last_updated) 
                    VALUES (%s, 'KRW', 'CASH', %s, 1.0, %s, NOW())
                    """,
                    (account_db_key, initial_cash, initial_cash)
                )
                Logger.info(f"Portfolio initialized with {initial_cash:,.0f} KRW cash for account_db_key={account_db_key}")
            else:
                Logger.info(f"Portfolio already exists for account_db_key={account_db_key}")
                
        except Exception as e:
            Logger.error(f"Portfolio initialization failed for account_db_key={account_db_key} in shard {shard_id}: {e}")
            # 포트폴리오 초기화 실패는 프로필 설정을 중단시키지 않음

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
