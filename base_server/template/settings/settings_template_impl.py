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
            
            # 설정 데이터 조회
            settings_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_get_user_settings",
                (account_db_key, request.section)
            )
            
            # 가데이터 응답
            response.settings = UserSettings(
                investment_experience="INTERMEDIATE",
                risk_tolerance="MODERATE",
                investment_goal="GROWTH",
                monthly_budget=1000000.0,
                price_alerts=True,
                news_alerts=True,
                portfolio_alerts=False,
                trade_alerts=True,
                otp_enabled=False,
                biometric_enabled=True,
                session_timeout=30,
                login_alerts=True,
                theme="DARK",
                language="KO",
                currency="KRW",
                chart_style="CANDLE",
                auto_trading_enabled=False,
                max_position_size=0.1,
                stop_loss_default=-0.05,
                take_profit_default=0.15
            )
            response.notification_settings = NotificationSettings(
                price_change_threshold=0.05,
                news_keywords=["AI", "투자"],
                portfolio_rebalance_alerts=True,
                daily_summary=True,
                weekly_report=True
            )
            response.security_settings = SecuritySettings(
                password_change_required=False,
                last_password_change=str(datetime.now()),
                failed_login_attempts=0,
                device_trust_enabled=True,
                ip_whitelist=[]
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
            
            # 설정 업데이트 DB 저장
            await db_service.call_shard_procedure(
                shard_id,
                "fp_update_user_settings",
                (account_db_key, request.section, json.dumps(request.settings))
            )
            
            response.updated_settings = UserSettings(**request.settings)
            response.message = "설정이 업데이트되었습니다"
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
            
            # 설정 초기화 DB 저장
            await db_service.call_shard_procedure(
                shard_id,
                "fp_reset_user_settings",
                (account_db_key, request.section)
            )
            
            response.reset_settings = UserSettings()  # 기본값
            response.message = "설정이 초기화되었습니다"
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
            
            # OTP 토글 DB 저장
            await db_service.call_shard_procedure(
                shard_id,
                "fp_toggle_otp",
                (account_db_key, request.enable, request.current_password)
            )
            
            response.otp_enabled = request.enable
            if request.enable:
                response.qr_code_url = f"https://api.finance.com/otp/qr/{account_db_key}"
                response.backup_codes = [f"CODE{i:04d}" for i in range(1, 11)]
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
            current_pass_result = await db_service.call_procedure(
                "fp_verify_user_password",
                (account_db_key, request.current_password)
            )
            
            # 새 비밀번호로 업데이트
            await db_service.call_procedure(
                "fp_update_user_password",
                (account_db_key, request.new_password)
            )
            
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
            
            # 내보내기 작업 생성
            export_id = f"export_{uuid.uuid4().hex[:16]}"
            expires_at = datetime.now() + timedelta(hours=24)
            
            await db_service.call_shard_procedure(
                shard_id,
                "fp_create_export_job",
                (export_id, account_db_key, json.dumps(request.data_types), "PROCESSING")
            )
            
            response.download_url = f"https://api.finance.com/exports/{export_id}"
            response.file_size = 1024000  # 1MB
            response.expires_at = str(expires_at)
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            response.download_url = ""
            response.file_size = 0
            response.expires_at = ""
            Logger.error(f"Settings export data error: {e}")
        
        return response