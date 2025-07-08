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
    AccountInfoRequest, AccountInfoResponse
)
from template.account.common.account_model import AccountInfo
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
                    response.account_db_key = account_db_key
                    response.nickname = user_data.get('nickname', '')
                    response.account_level = user_data.get('account_level', 1)
                    response.shard_id = shard_id
                    
                    # account_info 설정 (run_anonymous에서 accessToken 생성 및 Redis 세션 생성에 사용됨)
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
                    response.account_db_key = account_db_key
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
                response.shard_id = shard_id  # 디버깅용
                
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
                        response.shard_id = shard_id
                        
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
