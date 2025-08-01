from template.base.base_template import BaseTemplate
from template.profile.common.profile_serialize import (
    ProfileGetRequest, ProfileGetResponse,
    ProfileUpdateAllRequest, ProfileUpdateAllResponse,
    ProfileUpdateBasicRequest, ProfileUpdateBasicResponse,
    ProfileUpdateNotificationRequest, ProfileUpdateNotificationResponse,
    ProfileChangePasswordRequest, ProfileChangePasswordResponse,
    ProfileGetPaymentPlanRequest, ProfileGetPaymentPlanResponse,
    ProfileChangePlanRequest, ProfileChangePlanResponse,
    ProfileSaveApiKeysRequest, ProfileSaveApiKeysResponse,
    ProfileGetApiKeysRequest, ProfileGetApiKeysResponse
)
from template.profile.common.profile_model import ProfileSettings, ApiKeyInfo, PaymentPlanInfo
from service.core.logger import Logger
from service.service_container import ServiceContainer
from service.security.security_utils import SecurityUtils
import time

class ProfileTemplateImpl(BaseTemplate):
    def __init__(self):
        super().__init__()
    
    def _hash_password(self, password: str) -> str:
        """패스워드 해시화 - bcrypt 사용 (Account와 동일)"""
        return SecurityUtils.hash_password(password)
    
    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """비밀번호 검증 (Account와 동일)"""
        # 기존 SHA-256 해시와의 호환성 검사
        if len(hashed_password) == 64:  # SHA-256 해시 길이
            legacy_hash = SecurityUtils.hash_for_legacy_compatibility(password)
            return legacy_hash == hashed_password
        # bcrypt 검증
        return SecurityUtils.verify_password(password, hashed_password)
    
    async def on_profile_get_req(self, client_session, request: ProfileGetRequest):
        """프로필 설정 조회"""
        response = ProfileGetResponse()
        
        Logger.info("Profile get request received")
        
        try:
            account_db_key = client_session.session.account_db_key
            
            db_service = ServiceContainer.get_database_service()
            
            # 프로필 설정 조회 (Global DB)
            profile_result = await db_service.call_global_procedure(
                "fp_get_user_profile_settings",
                (account_db_key,)
            )
            
            if not profile_result:
                response.errorCode = 9001
                response.profile = None
                Logger.info(f"No profile found for account_db_key: {account_db_key}")
                return response
            
            profile_data = profile_result[0]
            
            # ProfileSettings 객체 생성
            response.profile = ProfileSettings(
                account_id=profile_data.get('account_id', ''),
                nickname=profile_data.get('nickname', ''),
                email=profile_data.get('email', ''),
                phone_number=profile_data.get('phone_number'),
                email_verified=bool(profile_data.get('email_verified', False)),
                phone_verified=bool(profile_data.get('phone_verified', False)),
                email_notifications_enabled=bool(profile_data.get('email_notifications_enabled', True)),
                sms_notifications_enabled=bool(profile_data.get('sms_notifications_enabled', False)),
                push_notifications_enabled=bool(profile_data.get('push_notifications_enabled', True)),
                price_alert_enabled=bool(profile_data.get('price_alert_enabled', True)),
                news_alert_enabled=bool(profile_data.get('news_alert_enabled', True)),
                portfolio_alert_enabled=bool(profile_data.get('portfolio_alert_enabled', False)),
                trade_alert_enabled=bool(profile_data.get('trade_alert_enabled', True)),
                payment_plan=profile_data.get('payment_plan', 'FREE'),
                plan_expires_at=str(profile_data.get('plan_expires_at')) if profile_data.get('plan_expires_at') else None,
                created_at=str(profile_data.get('created_at', '')),
                updated_at=str(profile_data.get('updated_at', ''))
            )
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            response.profile = None
            Logger.error(f"Profile get error: {e}")
        
        return response

    async def on_profile_update_all_req(self, client_session, request: ProfileUpdateAllRequest):
        """전체 프로필 설정 업데이트 (트랜잭션으로 한번에 처리)"""
        response = ProfileUpdateAllResponse()
        
        Logger.info("Profile update all request received")
        
        try:
            account_db_key = client_session.session.account_db_key
            db_service = ServiceContainer.get_database_service()
            
            # 통합 업데이트 프로시저 호출 (트랜잭션 처리)
            result = await db_service.call_global_procedure(
                "fp_update_profile_all",
                (
                    account_db_key,
                    # 기본 프로필
                    request.nickname, request.email, request.phone_number,
                    # 알림 설정
                    request.email_notifications_enabled, request.sms_notifications_enabled,
                    request.push_notifications_enabled, request.price_alert_enabled,
                    request.news_alert_enabled, request.portfolio_alert_enabled,
                    request.trade_alert_enabled,
                    # 비밀번호 변경 (선택사항)
                    request.current_password, request.new_password,
                    # API 키 (선택사항)
                    request.korea_investment_app_key, request.korea_investment_app_secret,
                    request.alpha_vantage_key, request.polygon_key, request.finnhub_key
                )
            )
            
            if not result or result[0].get('result') != 'SUCCESS':
                response.errorCode = 9002
                response.message = result[0].get('message', '프로필 업데이트 실패') if result else '프로필 업데이트 실패'
                return response
            
            # 결과 정보 설정
            result_data = result[0]
            response.password_changed = bool(result_data.get('password_changed', False))
            response.api_keys_saved = bool(result_data.get('api_keys_saved', False))
            response.require_relogin = response.password_changed  # 비밀번호 변경 시 재로그인 필요
            
            # 업데이트된 프로필 조회
            updated_profile_result = await db_service.call_global_procedure(
                "fp_get_user_profile_settings",
                (account_db_key,)
            )
            
            if updated_profile_result:
                profile_data = updated_profile_result[0]
                response.updated_profile = ProfileSettings(
                    account_id=profile_data.get('account_id', ''),
                    nickname=profile_data.get('nickname', ''),
                    email=profile_data.get('email', ''),
                    phone_number=profile_data.get('phone_number'),
                    email_verified=bool(profile_data.get('email_verified', False)),
                    phone_verified=bool(profile_data.get('phone_verified', False)),
                    email_notifications_enabled=bool(profile_data.get('email_notifications_enabled', True)),
                    sms_notifications_enabled=bool(profile_data.get('sms_notifications_enabled', False)),
                    push_notifications_enabled=bool(profile_data.get('push_notifications_enabled', True)),
                    price_alert_enabled=bool(profile_data.get('price_alert_enabled', True)),
                    news_alert_enabled=bool(profile_data.get('news_alert_enabled', True)),
                    portfolio_alert_enabled=bool(profile_data.get('portfolio_alert_enabled', False)),
                    trade_alert_enabled=bool(profile_data.get('trade_alert_enabled', True)),
                    payment_plan=profile_data.get('payment_plan', 'FREE'),
                    plan_expires_at=str(profile_data.get('plan_expires_at')) if profile_data.get('plan_expires_at') else None,
                    created_at=str(profile_data.get('created_at', '')),
                    updated_at=str(profile_data.get('updated_at', ''))
                )
            
            response.message = "프로필 설정이 업데이트되었습니다"
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            response.message = "프로필 설정 업데이트 실패"
            response.updated_profile = None
            response.password_changed = False
            response.api_keys_saved = False
            response.require_relogin = False
            Logger.error(f"Profile update all error: {e}")
        
        return response

    async def on_profile_update_basic_req(self, client_session, request: ProfileUpdateBasicRequest):
        """기본 프로필 업데이트"""
        response = ProfileUpdateBasicResponse()
        
        Logger.info("Profile update basic request received")
        
        try:
            account_db_key = client_session.session.account_db_key
            db_service = ServiceContainer.get_database_service()
            
            # 기본 프로필 업데이트
            result = await db_service.call_global_procedure(
                "fp_update_basic_profile",
                (account_db_key, request.nickname, request.email, request.phone_number)
            )
            
            if not result or result[0].get('result') != 'SUCCESS':
                response.errorCode = 9002
                response.message = "기본 프로필 업데이트 실패"
                return response
            
            response.message = "기본 프로필이 업데이트되었습니다"
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            response.message = "기본 프로필 업데이트 실패"
            Logger.error(f"Profile update basic error: {e}")
        
        return response

    async def on_profile_update_notification_req(self, client_session, request: ProfileUpdateNotificationRequest):
        """알림 설정 업데이트"""
        response = ProfileUpdateNotificationResponse()
        
        Logger.info("Profile update notification request received")
        
        try:
            account_db_key = client_session.session.account_db_key
            db_service = ServiceContainer.get_database_service()
            
            # 알림 설정 업데이트
            result = await db_service.call_global_procedure(
                "fp_update_notification_settings",
                (account_db_key, request.email_notifications_enabled, request.sms_notifications_enabled,
                 request.push_notifications_enabled, request.price_alert_enabled, request.news_alert_enabled,
                 request.portfolio_alert_enabled, request.trade_alert_enabled)
            )
            
            if not result or result[0].get('result') != 'SUCCESS':
                response.errorCode = 9003
                response.message = "알림 설정 업데이트 실패"
                return response
            
            response.message = "알림 설정이 업데이트되었습니다"
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            response.message = "알림 설정 업데이트 실패"
            Logger.error(f"Profile update notification error: {e}")
        
        return response

    async def on_profile_change_password_req(self, client_session, request: ProfileChangePasswordRequest):
        """비밀번호 변경"""
        response = ProfileChangePasswordResponse()
        
        Logger.info("Profile change password request received")
        
        try:
            account_db_key = client_session.session.account_db_key
            db_service = ServiceContainer.get_database_service()
            
            # IP 주소 가져오기 (client_session에서 또는 기본값 사용)
            client_ip = getattr(client_session, 'ip_address', '127.0.0.1')
            
            # 현재 저장된 비밀번호 해시 조회
            password_query = "SELECT password_hash FROM table_accountid WHERE account_db_key = %s"
            password_result = await db_service.execute_global_query(password_query, (account_db_key,))
            
            if not password_result:
                response.errorCode = 9004
                response.message = "계정 정보를 찾을 수 없습니다"
                return response
            
            stored_hash = password_result[0].get('password_hash', '')
            
            # 현재 비밀번호 검증 (Account와 동일한 방식)
            if not self._verify_password(request.current_password, stored_hash):
                response.errorCode = 9004
                response.message = "현재 비밀번호가 일치하지 않습니다"
                return response
            
            # 새 비밀번호 해싱 (Account와 동일한 방식)
            new_password_hash = self._hash_password(request.new_password)
            
            # 비밀번호 변경
            result = await db_service.call_global_procedure(
                "fp_change_password",
                (account_db_key, new_password_hash, client_ip)
            )
            
            if not result or result[0].get('result') != 'SUCCESS':
                response.errorCode = 9004
                response.message = "비밀번호 변경 실패"
                return response
            
            response.message = "비밀번호가 변경되었습니다"
            response.require_relogin = True
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            response.message = "비밀번호 변경 실패"
            Logger.error(f"Profile change password error: {e}")
        
        return response

    async def on_profile_get_payment_plan_req(self, client_session, request: ProfileGetPaymentPlanRequest):
        """결제 플랜 조회"""
        response = ProfileGetPaymentPlanResponse()
        
        Logger.info("Profile get payment plan request received")
        
        try:
            account_db_key = client_session.session.account_db_key
            db_service = ServiceContainer.get_database_service()
            
            # 결제 플랜 조회
            result = await db_service.call_global_procedure(
                "fp_get_payment_plan",
                (account_db_key,)
            )
            
            if not result:
                response.errorCode = 9005
                response.payment_info = None
                return response
            
            plan_data = result[0]
            response.payment_info = PaymentPlanInfo(
                current_plan=plan_data.get('current_plan', 'FREE'),
                plan_name=plan_data.get('plan_name', ''),
                plan_price=float(plan_data.get('plan_price', 0.0)),
                plan_expires_at=str(plan_data.get('plan_expires_at')) if plan_data.get('plan_expires_at') else None,
                auto_renewal=bool(plan_data.get('auto_renewal', False)),
                payment_method=plan_data.get('payment_method', '')
            )
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            response.payment_info = None
            Logger.error(f"Profile get payment plan error: {e}")
        
        return response

    async def on_profile_change_plan_req(self, client_session, request: ProfileChangePlanRequest):
        """결제 플랜 변경 (결제 처리 필요)"""
        response = ProfileChangePlanResponse()
        
        Logger.info(f"Profile change plan request: {request.new_plan}")
        
        try:
            account_db_key = client_session.session.account_db_key
            
            # 현재 플랜 확인
            db_service = ServiceContainer.get_database_service()
            current_plan_result = await db_service.call_global_procedure(
                "fp_get_payment_plan",
                (account_db_key,)
            )
            
            if not current_plan_result:
                response.errorCode = 9008
                response.message = "현재 플랜 조회 실패"
                return response
            
            current_plan = current_plan_result[0].get('current_plan', 'FREE')
            
            # 같은 플랜으로 변경 시도 시
            if current_plan == request.new_plan:
                response.errorCode = 9009
                response.message = "이미 해당 플랜을 사용 중입니다"
                response.requires_payment = False
                return response
            
            # FREE 플랜으로 다운그레이드
            if request.new_plan == 'FREE':
                # 즉시 FREE 플랜으로 변경 (결제 필요 없음)
                # TODO: 실제로는 구독 취소 API 호출 필요
                response.message = "무료 플랜으로 변경되었습니다"
                response.requires_payment = False
                response.errorCode = 0
                return response
            
            # 유료 플랜으로 업그레이드 - 결제 필요
            # TODO: 실제 PG사 연동 구현 필요
            # 1. 결제 세션 생성
            # 2. 결제 URL 생성
            # 3. 결제 완료 콜백 처리
            
            # 임시 결제 URL 생성 (실제로는 PG사 API 호출)
            payment_session_id = f"pay_{account_db_key}_{request.new_plan}_{int(time.time())}"
            response.payment_url = f"https://payment.example.com/checkout?session={payment_session_id}"
            response.requires_payment = True
            response.message = f"{request.new_plan} 플랜 결제를 진행해주세요"
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            response.message = "플랜 변경 실패"
            response.payment_url = None
            response.requires_payment = False
            Logger.error(f"Profile change plan error: {e}")
        
        return response

    async def on_profile_save_api_keys_req(self, client_session, request: ProfileSaveApiKeysRequest):
        """API 키 저장"""
        response = ProfileSaveApiKeysResponse()
        
        Logger.info("Profile save API keys request received")
        
        try:
            account_db_key = client_session.session.account_db_key
            db_service = ServiceContainer.get_database_service()
            
            # API 키 저장
            result = await db_service.call_global_procedure(
                "fp_save_api_keys",
                (account_db_key, request.korea_investment_app_key, request.korea_investment_app_secret,
                 request.alpha_vantage_key, request.polygon_key, request.finnhub_key)
            )
            
            if not result or result[0].get('result') != 'SUCCESS':
                response.errorCode = 9006
                response.message = "API 키 저장 실패"
                return response
            
            response.message = "API 키가 저장되었습니다"
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            response.message = "API 키 저장 실패"
            Logger.error(f"Profile save API keys error: {e}")
        
        return response

    async def on_profile_get_api_keys_req(self, client_session, request: ProfileGetApiKeysRequest):
        """API 키 조회"""
        response = ProfileGetApiKeysResponse()
        
        Logger.info("Profile get API keys request received")
        
        try:
            account_db_key = client_session.session.account_db_key
            db_service = ServiceContainer.get_database_service()
            
            # API 키 조회
            result = await db_service.call_global_procedure(
                "fp_get_api_keys",
                (account_db_key,)
            )
            
            if not result:
                response.errorCode = 9007
                response.api_keys = None
                return response
            
            api_data = result[0]
            response.api_keys = ApiKeyInfo(
                korea_investment_app_key=api_data.get('korea_investment_app_key', ''),
                korea_investment_app_secret_masked=self._mask_secret(api_data.get('korea_investment_app_secret', '')),
                alpha_vantage_key=api_data.get('alpha_vantage_key', ''),
                polygon_key=api_data.get('polygon_key', ''),
                finnhub_key=api_data.get('finnhub_key', ''),
                created_at=str(api_data.get('created_at', '')),
                updated_at=str(api_data.get('updated_at', ''))
            )
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            response.api_keys = None
            Logger.error(f"Profile get API keys error: {e}")
        
        return response
    
    def _mask_secret(self, secret: str) -> str:
        """시크릿 키 마스킹"""
        if not secret or len(secret) < 8:
            return "****"
        return f"{secret[:4]}****{secret[-4:]}"