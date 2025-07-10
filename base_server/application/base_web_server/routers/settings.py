from fastapi import APIRouter, Request
from template.base.template_context import TemplateContext, TemplateType
from template.base.template_service import TemplateService
from template.settings.common.settings_serialize import (
    SettingsGetRequest, SettingsUpdateRequest, SettingsResetRequest,
    SettingsOTPToggleRequest, SettingsPasswordChangeRequest, SettingsExportDataRequest
)
from template.settings.common.settings_protocol import SettingsProtocol

router = APIRouter()

settings_protocol = SettingsProtocol()

def setup_settings_protocol_callbacks():
    """Settings protocol 콜백 설정 (main.py에서 한 번만 호출됨)"""
    settings_template = TemplateContext.get_template(TemplateType.SETTINGS)
    settings_protocol.on_settings_get_req_callback = getattr(settings_template, "on_settings_get_req", None)
    settings_protocol.on_settings_update_req_callback = getattr(settings_template, "on_settings_update_req", None)
    settings_protocol.on_settings_reset_req_callback = getattr(settings_template, "on_settings_reset_req", None)
    settings_protocol.on_settings_otp_toggle_req_callback = getattr(settings_template, "on_settings_otp_toggle_req", None)
    settings_protocol.on_settings_password_change_req_callback = getattr(settings_template, "on_settings_password_change_req", None)
    settings_protocol.on_settings_export_data_req_callback = getattr(settings_template, "on_settings_export_data_req", None)

@router.post("/get")
async def settings_get(request: SettingsGetRequest, req: Request):
    """설정 조회"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        settings_protocol.settings_get_req_controller
    )

@router.post("/update")
async def settings_update(request: SettingsUpdateRequest, req: Request):
    """설정 업데이트"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        settings_protocol.settings_update_req_controller
    )

@router.post("/reset")
async def settings_reset(request: SettingsResetRequest, req: Request):
    """설정 초기화"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        settings_protocol.settings_reset_req_controller
    )

@router.post("/otp/toggle")
async def settings_otp_toggle(request: SettingsOTPToggleRequest, req: Request):
    """OTP 활성화/비활성화"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        settings_protocol.settings_otp_toggle_req_controller
    )

@router.post("/password/change")
async def settings_password_change(request: SettingsPasswordChangeRequest, req: Request):
    """비밀번호 변경"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        settings_protocol.settings_password_change_req_controller
    )

@router.post("/export-data")
async def settings_export_data(request: SettingsExportDataRequest, req: Request):
    """데이터 내보내기"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        settings_protocol.settings_export_data_req_controller
    )