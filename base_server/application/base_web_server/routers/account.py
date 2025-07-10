from fastapi import APIRouter, Request
from template.base.template_context import TemplateContext, TemplateType
from template.base.template_service import TemplateService
from template.account.common.account_serialize import (
    AccountLoginRequest, AccountLogoutRequest, AccountSignupRequest, AccountInfoRequest,
    AccountEmailVerifyRequest, AccountEmailConfirmRequest, AccountOTPSetupRequest,
    AccountOTPVerifyRequest, AccountOTPLoginRequest, AccountProfileSetupRequest,
    AccountProfileGetRequest, AccountProfileUpdateRequest, AccountTokenRefreshRequest,
    AccountTokenValidateRequest
)
from template.account.common.account_protocol import AccountProtocol

router = APIRouter()

account_protocol = AccountProtocol()

def setup_account_protocol_callbacks():
    """Account protocol 콜백 설정 (main.py에서 한 번만 호출됨)"""
    account_template = TemplateContext.get_template(TemplateType.ACCOUNT)
    account_protocol.on_account_login_req_callback = getattr(account_template, "on_account_login_req", None)
    account_protocol.on_account_logout_req_callback = getattr(account_template, "on_account_logout_req", None)
    account_protocol.on_account_signup_req_callback = getattr(account_template, "on_account_signup_req", None)
    account_protocol.on_account_info_req_callback = getattr(account_template, "on_account_info_req", None)
    account_protocol.on_account_email_verify_req_callback = getattr(account_template, "on_account_email_verify_req", None)
    account_protocol.on_account_email_confirm_req_callback = getattr(account_template, "on_account_email_confirm_req", None)
    account_protocol.on_account_otp_setup_req_callback = getattr(account_template, "on_account_otp_setup_req", None)
    account_protocol.on_account_otp_verify_req_callback = getattr(account_template, "on_account_otp_verify_req", None)
    account_protocol.on_account_otp_login_req_callback = getattr(account_template, "on_account_otp_login_req", None)
    account_protocol.on_account_profile_setup_req_callback = getattr(account_template, "on_account_profile_setup_req", None)
    account_protocol.on_account_profile_get_req_callback = getattr(account_template, "on_account_profile_get_req", None)
    account_protocol.on_account_profile_update_req_callback = getattr(account_template, "on_account_profile_update_req", None)
    account_protocol.on_account_token_refresh_req_callback = getattr(account_template, "on_account_token_refresh_req", None)
    account_protocol.on_account_token_validate_req_callback = getattr(account_template, "on_account_token_validate_req", None)

@router.post("/login")
async def account_login(request: AccountLoginRequest, req: Request):
    """로그인 1단계 요청"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_anonymous(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        account_protocol.account_login_req_controller
    )

@router.post("/logout")
async def account_logout(request: AccountLogoutRequest, req: Request):
    """로그아웃 요청"""
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
        account_protocol.account_logout_req_controller
    )

@router.post("/signup")
async def account_signup(request: AccountSignupRequest, req: Request):
    """회원가입 요청"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_anonymous(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        account_protocol.account_signup_req_controller
    )

@router.post("/info")
async def account_info(request: AccountInfoRequest, req: Request):
    """계좌 정보 조회 요청"""
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
        account_protocol.account_info_req_controller
    )

@router.post("/email/verify")
async def account_email_verify(request: AccountEmailVerifyRequest, req: Request):
    """이메일 인증 코드 전송 요청"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_anonymous(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        account_protocol.account_email_verify_req_controller
    )

@router.post("/email/confirm")
async def account_email_confirm(request: AccountEmailConfirmRequest, req: Request):
    """이메일 인증 코드 확인 요청"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_anonymous(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        account_protocol.account_email_confirm_req_controller
    )

@router.post("/otp/setup")
async def account_otp_setup(request: AccountOTPSetupRequest, req: Request):
    """OTP 설정 요청"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_anonymous(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        account_protocol.account_otp_setup_req_controller
    )

@router.post("/otp/verify")
async def account_otp_verify(request: AccountOTPVerifyRequest, req: Request):
    """OTP 인증 요청"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_anonymous(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        account_protocol.account_otp_verify_req_controller
    )

@router.post("/otp/login")
async def account_otp_login(request: AccountOTPLoginRequest, req: Request):
    """로그인 2단계 OTP 인증"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_anonymous(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        account_protocol.account_otp_login_req_controller
    )

@router.post("/profile/setup")
async def account_profile_setup(request: AccountProfileSetupRequest, req: Request):
    """프로필 설정 요청"""
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
        account_protocol.account_profile_setup_req_controller
    )

@router.post("/profile/get")
async def account_profile_get(request: AccountProfileGetRequest, req: Request):
    """프로필 조회 요청"""
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
        account_protocol.account_profile_get_req_controller
    )

@router.post("/profile/update")
async def account_profile_update(request: AccountProfileUpdateRequest, req: Request):
    """프로필 업데이트 요청"""
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
        account_protocol.account_profile_update_req_controller
    )

@router.post("/token/refresh")
async def account_token_refresh(request: AccountTokenRefreshRequest, req: Request):
    """토큰 갱신 요청"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_anonymous(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        account_protocol.account_token_refresh_req_controller
    )

@router.post("/token/validate")
async def account_token_validate(request: AccountTokenValidateRequest, req: Request):
    """토큰 검증 요청"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_anonymous(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        account_protocol.account_token_validate_req_controller
    )