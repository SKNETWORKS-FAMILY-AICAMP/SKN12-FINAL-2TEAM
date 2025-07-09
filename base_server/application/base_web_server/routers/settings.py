from fastapi import APIRouter, Request
from template.base.template_context import TemplateContext, TemplateType
from template.base.template_service import TemplateService
from template.settings.common.settings_serialize import (
    SettingsGetRequest, SettingsUpdateProfileRequest, SettingsUpdateNotificationRequest,
    SettingsUpdateSecurityRequest, SettingsUpdateDisplayRequest, SettingsUpdateTradingRequest,
    SettingsResetRequest, SettingsExportRequest, SettingsImportRequest,
    SettingsApplyTemplateRequest, SettingsGetTemplatesRequest, SettingsGetHistoryRequest,
    SettingsUpdatePersonalizationRequest
)
from template.settings.common.settings_protocol import SettingsProtocol

router = APIRouter()

settings_protocol = SettingsProtocol()

def setup_settings_protocol_callbacks():
    """Settings protocol 콜백 설정 (main.py에서 한 번만 호출됨)"""
    settings_template = TemplateContext.get_template(TemplateType.SETTINGS)
    settings_protocol.on_settings_get_req_callback = getattr(settings_template, "on_settings_get_req", None)
    settings_protocol.on_settings_update_profile_req_callback = getattr(settings_template, "on_settings_update_profile_req", None)
    settings_protocol.on_settings_update_notification_req_callback = getattr(settings_template, "on_settings_update_notification_req", None)
    settings_protocol.on_settings_update_security_req_callback = getattr(settings_template, "on_settings_update_security_req", None)
    settings_protocol.on_settings_update_display_req_callback = getattr(settings_template, "on_settings_update_display_req", None)
    settings_protocol.on_settings_update_trading_req_callback = getattr(settings_template, "on_settings_update_trading_req", None)
    settings_protocol.on_settings_reset_req_callback = getattr(settings_template, "on_settings_reset_req", None)
    settings_protocol.on_settings_export_req_callback = getattr(settings_template, "on_settings_export_req", None)
    settings_protocol.on_settings_import_req_callback = getattr(settings_template, "on_settings_import_req", None)
    settings_protocol.on_settings_apply_template_req_callback = getattr(settings_template, "on_settings_apply_template_req", None)
    settings_protocol.on_settings_get_templates_req_callback = getattr(settings_template, "on_settings_get_templates_req", None)
    settings_protocol.on_settings_get_history_req_callback = getattr(settings_template, "on_settings_get_history_req", None)
    settings_protocol.on_settings_update_personalization_req_callback = getattr(settings_template, "on_settings_update_personalization_req", None)

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

@router.post("/update-profile")
async def settings_update_profile(request: SettingsUpdateProfileRequest, req: Request):
    """프로필 설정 업데이트"""
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
        settings_protocol.settings_update_profile_req_controller
    )

@router.post("/update-notification")
async def settings_update_notification(request: SettingsUpdateNotificationRequest, req: Request):
    """알림 설정 업데이트"""
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
        settings_protocol.settings_update_notification_req_controller
    )

@router.post("/update-security")
async def settings_update_security(request: SettingsUpdateSecurityRequest, req: Request):
    """보안 설정 업데이트"""
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
        settings_protocol.settings_update_security_req_controller
    )

@router.post("/update-display")
async def settings_update_display(request: SettingsUpdateDisplayRequest, req: Request):
    """화면 설정 업데이트"""
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
        settings_protocol.settings_update_display_req_controller
    )

@router.post("/update-trading")
async def settings_update_trading(request: SettingsUpdateTradingRequest, req: Request):
    """거래 설정 업데이트"""
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
        settings_protocol.settings_update_trading_req_controller
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

@router.post("/export")
async def settings_export(request: SettingsExportRequest, req: Request):
    """설정 내보내기"""
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
        settings_protocol.settings_export_req_controller
    )

@router.post("/import")
async def settings_import(request: SettingsImportRequest, req: Request):
    """설정 가져오기"""
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
        settings_protocol.settings_import_req_controller
    )

@router.post("/apply-template")
async def settings_apply_template(request: SettingsApplyTemplateRequest, req: Request):
    """설정 템플릿 적용"""
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
        settings_protocol.settings_apply_template_req_controller
    )

@router.post("/get-templates")
async def settings_get_templates(request: SettingsGetTemplatesRequest, req: Request):
    """설정 템플릿 목록 조회"""
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
        settings_protocol.settings_get_templates_req_controller
    )

@router.post("/get-history")
async def settings_get_history(request: SettingsGetHistoryRequest, req: Request):
    """설정 변경 이력 조회"""
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
        settings_protocol.settings_get_history_req_controller
    )

@router.post("/update-personalization")
async def settings_update_personalization(request: SettingsUpdatePersonalizationRequest, req: Request):
    """개인화 설정 업데이트"""
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
        settings_protocol.settings_update_personalization_req_controller
    )