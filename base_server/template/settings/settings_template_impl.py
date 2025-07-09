from template.base.base_template import BaseTemplate
from template.settings.common.settings_serialize import (
    SettingsGetRequest, SettingsGetResponse,
    SettingsUpdateRequest, SettingsUpdateResponse,
    SettingsResetRequest, SettingsResetResponse,
    SettingsOTPToggleRequest, SettingsOTPToggleResponse,
    SettingsPasswordChangeRequest, SettingsPasswordChangeResponse,
    SettingsExportDataRequest, SettingsExportDataResponse
)
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
            
            # TODO: 설정 조회 로직 구현
            # - 사용자별 설정 데이터 조회
            # - 기본값 적용
            # - 섹션별 필터링
            
            # 설정 데이터 조회
            settings_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_get_user_settings",
                (account_db_key, request.section)
            )
            
            # 가데이터 응답
            response.settings = {
                "notifications": {
                    "email_enabled": True,
                    "push_enabled": True,
                    "sms_enabled": False,
                    "price_alerts": True
                },
                "trading": {
                    "auto_invest": False,
                    "risk_level": "MODERATE",
                    "max_loss_percent": 10.0,
                    "preferred_currency": "KRW"
                },
                "privacy": {
                    "data_sharing": True,
                    "analytics": True,
                    "marketing": False
                },
                "display": {
                    "theme": "LIGHT",
                    "language": "ko-KR",
                    "timezone": "Asia/Seoul"
                }
            }
            response.defaults = {
                "risk_level": "MODERATE",
                "theme": "LIGHT",
                "language": "ko-KR"
            }
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            response.settings = {}
            response.defaults = {}
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
            
            # TODO: 설정 업데이트 로직 구현
            # - 설정 값 검증
            # - 업데이트 가능 여부 확인
            # - 변경 이력 기록
            
            # 설정 업데이트 DB 저장
            await db_service.call_shard_procedure(
                shard_id,
                "fp_update_user_settings",
                (account_db_key, request.section, json.dumps(request.settings))
            )
            
            # 설정 변경 이력 저장
            await db_service.call_shard_procedure(
                shard_id,
                "fp_save_settings_history",
                (account_db_key, request.section, "UPDATE", json.dumps(request.settings))
            )
            
            response.updated_settings = request.settings
            response.message = "설정이 업데이트되었습니다"
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            response.message = "설정 업데이트 실패"
            response.updated_settings = {}
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
            
            # TODO: 설정 초기화 로직 구현
            # - 기본값으로 복원
            # - 초기화 확인
            # - 백업 데이터 생성
            
            # 설정 초기화 (기본값으로 복원)
            await db_service.call_shard_procedure(
                shard_id,
                "fp_reset_user_settings",
                (account_db_key, request.section)
            )
            
            # 초기화 이력 저장
            await db_service.call_shard_procedure(
                shard_id,
                "fp_save_settings_history",
                (account_db_key, request.section, "RESET", "{}")
            )
            
            # 가데이터 기본값
            default_settings = {
                "notifications": {"email_enabled": True, "push_enabled": True, "sms_enabled": False},
                "trading": {"auto_invest": False, "risk_level": "MODERATE", "max_loss_percent": 10.0},
                "privacy": {"data_sharing": True, "analytics": True, "marketing": False},
                "display": {"theme": "LIGHT", "language": "ko-KR", "timezone": "Asia/Seoul"}
            }
            
            response.reset_settings = default_settings.get(request.section, {})
            response.message = "설정이 초기화되었습니다"
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            response.message = "설정 초기화 실패"
            response.reset_settings = {}
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
            
            # TODO: OTP 토글 로직 구현
            # - OTP 시크릿 생성/삭제
            # - QR 코드 생성 (활성화시)
            # - 검증 과정
            
            if request.enable:
                # OTP 활성화
                otp_secret = f"secret_{uuid.uuid4().hex[:16]}"
                qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?data=otpauth://totp/FinanceApp:{account_db_key}?secret={otp_secret}"
                
                await db_service.call_shard_procedure(
                    shard_id,
                    "fp_enable_user_otp",
                    (account_db_key, otp_secret)
                )
                
                response.qr_code_url = qr_code_url
                response.backup_codes = [f"backup_{i:04d}" for i in range(1, 11)]  # 가데이터
            else:
                # OTP 비활성화
                await db_service.call_shard_procedure(
                    shard_id,
                    "fp_disable_user_otp",
                    (account_db_key,)
                )
                
                response.qr_code_url = ""
                response.backup_codes = []
            
            response.otp_enabled = request.enable
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
            
            # TODO: 비밀번호 변경 로직 구현
            # - 현재 비밀번호 검증
            # - 새 비밀번호 강도 검사
            # - 암호화 처리
            # - 세션 무효화
            
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
            
            # 비밀번호 변경 이력 저장
            await db_service.call_shard_procedure(
                shard_id,
                "fp_save_password_change_log",
                (account_db_key, "SUCCESS")
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
            
            # TODO: 데이터 내보내기 로직 구현
            # - 요청된 데이터 타입별 수집
            # - 개인정보 마스킹
            # - ZIP 파일 생성
            # - 임시 다운로드 URL 생성
            # - 만료 시간 설정
            
            # 내보내기 작업 생성
            export_id = f"export_{uuid.uuid4().hex[:16]}"
            expires_at = datetime.now() + timedelta(hours=24)
            
            await db_service.call_shard_procedure(
                shard_id,
                "fp_create_export_job",
                (export_id, account_db_key, json.dumps(request.data_types), "PROCESSING")
            )
            
            # 가데이터 응답
            response.export_id = export_id
            response.download_url = f"https://api.finance.com/exports/{export_id}"
            response.file_size = 1024000  # 1MB
            response.expires_at = str(expires_at)
            response.status = "PROCESSING"
            response.estimated_completion_time = str(datetime.now() + timedelta(minutes=5))
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            response.export_id = ""
            response.download_url = ""
            response.file_size = 0
            response.expires_at = ""
            response.status = "FAILED"
            Logger.error(f"Settings export data error: {e}")
        
        return response