from fastapi import APIRouter, Request
from template.base.template_context import TemplateContext, TemplateType
from template.base.template_service import TemplateService
from template.profile.common.profile_serialize import (
    ProfileGetRequest, ProfileUpdateAllRequest, ProfileUpdateBasicRequest,
    ProfileUpdateNotificationRequest, ProfileChangePasswordRequest,
    ProfileGetPaymentPlanRequest, ProfileChangePlanRequest,
    ProfileSaveApiKeysRequest, ProfileGetApiKeysRequest
)
from template.profile.common.profile_protocol import ProfileProtocol

router = APIRouter()

profile_protocol = ProfileProtocol()

def setup_profile_protocol_callbacks():
    """Profile protocol 콜백 설정 (main.py에서 한 번만 호출됨)"""
    profile_template = TemplateContext.get_template(TemplateType.PROFILE)
    profile_protocol.on_profile_get_req_callback = getattr(profile_template, "on_profile_get_req", None)
    profile_protocol.on_profile_update_all_req_callback = getattr(profile_template, "on_profile_update_all_req", None)
    profile_protocol.on_profile_update_basic_req_callback = getattr(profile_template, "on_profile_update_basic_req", None)
    profile_protocol.on_profile_update_notification_req_callback = getattr(profile_template, "on_profile_update_notification_req", None)
    profile_protocol.on_profile_change_password_req_callback = getattr(profile_template, "on_profile_change_password_req", None)
    profile_protocol.on_profile_get_payment_plan_req_callback = getattr(profile_template, "on_profile_get_payment_plan_req", None)
    profile_protocol.on_profile_change_plan_req_callback = getattr(profile_template, "on_profile_change_plan_req", None)
    profile_protocol.on_profile_save_api_keys_req_callback = getattr(profile_template, "on_profile_save_api_keys_req", None)
    profile_protocol.on_profile_get_api_keys_req_callback = getattr(profile_template, "on_profile_get_api_keys_req", None)

@router.post("/get")
async def profile_get(request: ProfileGetRequest, req: Request):
    """프로필 설정 조회"""
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
        profile_protocol.profile_get_req_controller
    )

@router.post("/update-all")
async def profile_update_all(request: ProfileUpdateAllRequest, req: Request):
    """전체 프로필 설정 업데이트 (마이페이지 전체 저장)"""
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
        profile_protocol.profile_update_all_req_controller
    )

@router.post("/update-basic")
async def profile_update_basic(request: ProfileUpdateBasicRequest, req: Request):
    """기본 프로필 업데이트 (닉네임, 이메일, 전화번호)"""
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
        profile_protocol.profile_update_basic_req_controller
    )

@router.post("/update-notification")
async def profile_update_notification(request: ProfileUpdateNotificationRequest, req: Request):
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
        profile_protocol.profile_update_notification_req_controller
    )

@router.post("/change-password")
async def profile_change_password(request: ProfileChangePasswordRequest, req: Request):
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
        profile_protocol.profile_change_password_req_controller
    )

@router.post("/payment/get-plan")
async def profile_get_payment_plan(request: ProfileGetPaymentPlanRequest, req: Request):
    """결제 플랜 조회"""
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
        profile_protocol.profile_get_payment_plan_req_controller
    )

@router.post("/payment/change-plan")
async def profile_change_plan(request: ProfileChangePlanRequest, req: Request):
    """결제 플랜 변경 (PG사 연동)"""
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
        profile_protocol.profile_change_plan_req_controller
    )

@router.post("/api-keys/save")
async def profile_save_api_keys(request: ProfileSaveApiKeysRequest, req: Request):
    """API 키 저장"""
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
        profile_protocol.profile_save_api_keys_req_controller
    )

@router.post("/api-keys/get")
async def profile_get_api_keys(request: ProfileGetApiKeysRequest, req: Request):
    """API 키 조회"""
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
        profile_protocol.profile_get_api_keys_req_controller
    )