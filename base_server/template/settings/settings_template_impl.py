from template.base.base_template import BaseTemplate
from template.settings.common.settings_serialize import (
    SettingsGetRequest, SettingsGetResponse,
    SettingsUpdateRequest, SettingsUpdateResponse,
    SettingsResetRequest, SettingsResetResponse,
    SettingsOTPToggleRequest, SettingsOTPToggleResponse,
    SettingsPasswordChangeRequest, SettingsPasswordChangeResponse,
    SettingsExportDataRequest, SettingsExportDataResponse
)
from template.settings.common.settings_model import UserSettings, NotificationSettings, SecuritySettings
from service.core.logger import Logger
from service.service_container import ServiceContainer
import json
import uuid
from datetime import datetime, timedelta

class SettingsTemplateImpl(BaseTemplate):
    def __init__(self):
        super().__init__()
    
    async def on_settings_get_req(self, client_session, request: SettingsGetRequest):
        """설정 조회 요청 처리"""
        response = SettingsGetResponse()
        
        Logger.info(f"Settings get request: section={request.section}")
        
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            db_service = ServiceContainer.get_database_service()
            
            # 1. 설정 데이터 조회 (section별 처리)
            if request.section == "notification":
                settings_result = await db_service.call_shard_procedure(
                    shard_id,
                    "fp_get_notification_settings",
                    (account_db_key, "ALL")
                )
            elif request.section == "personalization":
                settings_result = await db_service.call_shard_procedure(
                    shard_id,
                    "fp_get_personalization_settings",
                    (account_db_key,)
                )
            elif request.section == "trading":
                settings_result = await db_service.call_shard_procedure(
                    shard_id,
                    "fp_get_trading_settings",
                    (account_db_key,)
                )
            else:
                # 전체 설정 조회
                settings_result = await db_service.call_shard_procedure(
                    shard_id,
                    "fp_get_personalization_settings",
                    (account_db_key,)
                )
            
            # 2. DB 결과를 바탕으로 응답 생성
            if not settings_result:
                response.errorCode = 9001
                response.settings = None
                response.notification_settings = None
                response.security_settings = None
                Logger.info(f"No settings found for section: {request.section}")
                return response
            
            settings_data = settings_result[0] if settings_result else {}
            
            # 개인화 설정 데이터
            response.settings = UserSettings(
                investment_experience=settings_data.get('investment_experience', 'BEGINNER'),
                risk_tolerance=settings_data.get('risk_tolerance', 'MODERATE'),
                investment_goal=settings_data.get('investment_goal', 'GROWTH'),
                monthly_budget=float(settings_data.get('monthly_budget', 100000.0)),
                price_alerts=bool(settings_data.get('price_alerts', True)),
                news_alerts=bool(settings_data.get('news_alerts', True)),
                portfolio_alerts=bool(settings_data.get('portfolio_alerts', False)),
                trade_alerts=bool(settings_data.get('trade_alerts', True)),
                otp_enabled=bool(settings_data.get('otp_enabled', False)),
                biometric_enabled=bool(settings_data.get('biometric_enabled', True)),
                session_timeout=int(settings_data.get('session_timeout', 30)),
                login_alerts=bool(settings_data.get('login_alerts', True)),
                theme=settings_data.get('theme_preference', 'DARK'),
                language=settings_data.get('language', 'ko'),
                currency=settings_data.get('currency_display', 'KRW'),
                chart_style=settings_data.get('chart_style', 'CANDLE'),
                auto_trading_enabled=bool(settings_data.get('auto_trading_enabled', False)),
                max_position_size=float(settings_data.get('max_position_size', 0.1)),
                stop_loss_default=float(settings_data.get('default_stop_loss', -0.05)),
                take_profit_default=float(settings_data.get('default_take_profit', 0.15))
            )
            
            # 알림 설정
            response.notification_settings = NotificationSettings(
                price_change_threshold=float(settings_data.get('price_change_threshold', 0.05)),
                news_keywords=json.loads(settings_data.get('news_keywords', '["AI", "투자"]')),
                portfolio_rebalance_alerts=bool(settings_data.get('portfolio_rebalance_alerts', True)),
                daily_summary=bool(settings_data.get('daily_summary', True)),
                weekly_report=bool(settings_data.get('weekly_report', True))
            )
            
            # 보안 설정
            response.security_settings = SecuritySettings(
                password_change_required=bool(settings_data.get('password_change_required', False)),
                last_password_change=str(settings_data.get('last_password_change', datetime.now())),
                failed_login_attempts=int(settings_data.get('failed_login_attempts', 0)),
                device_trust_enabled=bool(settings_data.get('device_trust_enabled', True)),
                ip_whitelist=json.loads(settings_data.get('ip_whitelist', '[]'))
            )
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            response.settings = None
            response.notification_settings = None
            response.security_settings = None
            Logger.error(f"Settings get error: {e}")
        
        return response

    async def on_settings_update_req(self, client_session, request: SettingsUpdateRequest):
        """설정 업데이트 요청 처리"""
        response = SettingsUpdateResponse()
        
        Logger.info(f"Settings update request: section={request.section}")
        
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            db_service = ServiceContainer.get_database_service()
            
            # 1. 설정 업데이트 (section별 처리)
            update_result = None
            
            if request.section == "notification":
                # 알림 설정 업데이트
                update_result = await db_service.call_shard_procedure(
                    shard_id,
                    "fp_update_notification_settings",
                    (account_db_key, request.settings.get('notification_type', 'ALL'),
                     request.settings.get('channel', 'ALL'),
                     request.settings.get('is_enabled', True),
                     request.settings.get('frequency', 'REAL_TIME'),
                     None, None, json.dumps(request.settings))
                )
            elif request.section == "personalization":
                # 개인화 설정 업데이트
                update_result = await db_service.call_shard_procedure(
                    shard_id,
                    "fp_update_personalization_settings",
                    (account_db_key, request.settings.get('theme', 'DARK'),
                     request.settings.get('language', 'ko'),
                     request.settings.get('timezone', 'Asia/Seoul'),
                     request.settings.get('currency', 'KRW'),
                     request.settings.get('chart_style', 'CANDLE'),
                     json.dumps(request.settings.get('dashboard_layout', {})),
                     request.settings.get('sound_effects', True),
                     request.settings.get('animation_effects', True))
                )
            elif request.section == "trading":
                # 거래 설정 업데이트
                update_result = await db_service.call_shard_procedure(
                    shard_id,
                    "fp_update_trading_settings",
                    (account_db_key, request.settings.get('auto_trading_enabled', False),
                     request.settings.get('max_daily_trades', 10),
                     request.settings.get('max_position_size', 0.1),
                     request.settings.get('default_order_type', 'LIMIT'),
                     request.settings.get('default_stop_loss', -0.05),
                     request.settings.get('default_take_profit', 0.15),
                     request.settings.get('risk_management_level', 'MEDIUM'),
                     request.settings.get('confirmation_required', True))
                )
            
            if not update_result or update_result[0].get('result') != 'SUCCESS':
                response.errorCode = 9002
                response.message = f"{request.section} 설정 업데이트 실패"
                response.updated_settings = None
                return response
            
            response.updated_settings = UserSettings(**request.settings)
            response.message = f"{request.section} 설정이 업데이트되었습니다"
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            response.message = "설정 업데이트 실패"
            response.updated_settings = None
            Logger.error(f"Settings update error: {e}")
        
        return response

    async def on_settings_reset_req(self, client_session, request: SettingsResetRequest):
        """설정 초기화 요청 처리"""
        response = SettingsResetResponse()
        
        Logger.info(f"Settings reset request: section={request.section}")
        
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            db_service = ServiceContainer.get_database_service()
            
            # 1. 설정 초기화 - 시스템 템플릿 적용
            # 기본 템플릿 ID 결정
            template_id = "moderate_template"  # 기본적으로 중도적 템플릿 사용
            
            reset_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_apply_setting_template",
                (account_db_key, template_id)
            )
            
            if not reset_result or reset_result[0].get('result') != 'SUCCESS':
                response.errorCode = 9003
                response.message = f"{request.section} 설정 초기화 실패"
                response.reset_settings = None
                return response
            
            # 2. 초기화된 설정 데이터 반환
            template_data = json.loads(reset_result[0].get('settings_data', '{}'))
            
            response.reset_settings = UserSettings(
                investment_experience="INTERMEDIATE",
                risk_tolerance=template_data.get('risk_level', 'MEDIUM'),
                investment_goal="GROWTH",
                monthly_budget=100000.0,
                price_alerts=template_data.get('notifications', {}).get('price_alerts', True),
                news_alerts=template_data.get('notifications', {}).get('news', True),
                portfolio_alerts=False,
                trade_alerts=True,
                otp_enabled=False,
                biometric_enabled=True,
                session_timeout=30,
                login_alerts=True,
                theme=template_data.get('theme', 'DARK'),
                language="ko",
                currency="KRW",
                chart_style="CANDLE",
                auto_trading_enabled=template_data.get('auto_trading', False),
                max_position_size=template_data.get('max_position', 0.1),
                stop_loss_default=-0.05,
                take_profit_default=0.15
            )
            response.message = f"{request.section} 설정이 초기화되었습니다"
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            response.message = "설정 초기화 실패"
            response.reset_settings = None
            Logger.error(f"Settings reset error: {e}")
        
        return response

    async def on_settings_otp_toggle_req(self, client_session, request: SettingsOTPToggleRequest):
        """OTP 활성화/비활성화 요청 처리"""
        response = SettingsOTPToggleResponse()
        
        Logger.info(f"Settings OTP toggle request: enable={request.enable}")
        
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            db_service = ServiceContainer.get_database_service()
            
            # 1. 현재 비밀번호 확인 (글로벌 DB)
            password_check = await db_service.call_global_procedure(
                "fp_verify_user_password",
                (account_db_key, request.current_password)
            )
            
            if not password_check or password_check[0].get('result') != 'SUCCESS':
                response.errorCode = 9004
                response.message = "현재 비밀번호가 올바르지 않습니다"
                response.otp_enabled = False
                return response
            
            # 2. OTP 설정 업데이트 (보안 설정 테이블)
            # 실제로는 보안 설정 테이블에 OTP 설정을 업데이트해야 함
            security_update = await db_service.call_shard_procedure(
                shard_id,
                "fp_update_personalization_settings",  # 보안 설정 업데이트 프로시저 필요
                (account_db_key, None, None, None, None, None,
                 json.dumps({"otp_enabled": request.enable}), None, None)
            )
            
            if not security_update:
                response.errorCode = 9005
                response.message = "OTP 설정 업데이트 실패"
                response.otp_enabled = False
                return response
            
            response.otp_enabled = request.enable
            if request.enable:
                # OTP 시크릿 키 생성 (실제로는 pyotp 라이브러리 사용)
                secret_key = "JBSWY3DPEHPK3PXP"  # 예시 키
                response.qr_code_url = f"otpauth://totp/Investment:{account_db_key}?secret={secret_key}&issuer=Investment"
                response.backup_codes = [f"BAK{i:05d}" for i in range(1, 11)]
            response.message = "OTP 설정이 변경되었습니다"
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            response.message = "OTP 설정 변경 실패"
            response.otp_enabled = False
            response.qr_code_url = ""
            response.backup_codes = []
            Logger.error(f"Settings OTP toggle error: {e}")
        
        return response

    async def on_settings_password_change_req(self, client_session, request: SettingsPasswordChangeRequest):
        """비밀번호 변경 요청 처리"""
        response = SettingsPasswordChangeResponse()
        
        Logger.info("Settings password change request received")
        
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            db_service = ServiceContainer.get_database_service()
            
            # 현재 비밀번호 확인 (글로벌 DB)
            current_pass_result = await db_service.call_global_procedure(
                "fp_verify_user_password",
                (account_db_key, request.current_password)
            )
            
            if not current_pass_result or current_pass_result[0].get('result') != 'SUCCESS':
                response.errorCode = 9007
                response.message = "현재 비밀번호가 올바르지 않습니다"
                response.require_relogin = False
                return response
            
            # 새 비밀번호로 업데이트
            update_result = await db_service.call_global_procedure(
                "fp_update_user_password",
                (account_db_key, request.new_password)
            )
            
            if not update_result or update_result[0].get('result') != 'SUCCESS':
                response.errorCode = 9008
                response.message = "비밀번호 업데이트 실패"
                response.require_relogin = False
                return response
            
            response.message = "비밀번호가 변경되었습니다"
            response.require_relogin = True
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            response.message = "비밀번호 변경 실패"
            response.require_relogin = False
            Logger.error(f"Settings password change error: {e}")
        
        return response

    async def on_settings_export_data_req(self, client_session, request: SettingsExportDataRequest):
        """데이터 내보내기 요청 처리"""
        response = SettingsExportDataResponse()
        
        Logger.info(f"Settings export data request: types={request.data_types}")
        
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            db_service = ServiceContainer.get_database_service()
            
            # 1. 내보내기 작업 생성 (Settings History 테이블 활용)
            export_id = f"export_{uuid.uuid4().hex[:16]}"
            expires_at = datetime.now() + timedelta(hours=24)
            
            # 내보내기 요청을 설정 히스토리에 기록
            export_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_update_personalization_settings",  # 예시: 설정 업데이트로 내보내기 요청 기록
                (account_db_key, None, None, None, None, None,
                 json.dumps({
                     "export_request": {
                         "export_id": export_id,
                         "data_types": request.data_types,
                         "status": "PROCESSING",
                         "created_at": str(datetime.now()),
                         "expires_at": str(expires_at)
                     }
                 }), None, None)
            )
            
            if not export_result:
                response.errorCode = 9006
                response.download_url = ""
                response.file_size = 0
                response.expires_at = ""
                Logger.error("Failed to create export job")
                return response
            
            # 2. 내보내기 파일 생성 (비동기 처리 예시)
            estimated_size = len(request.data_types) * 50000  # 데이터 타입별 50KB 추정
            
            response.download_url = f"https://api.finance.com/exports/{export_id}"
            response.file_size = estimated_size
            response.expires_at = str(expires_at)
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            response.download_url = ""
            response.file_size = 0
            response.expires_at = ""
            Logger.error(f"Settings export data error: {e}")
        
        return response