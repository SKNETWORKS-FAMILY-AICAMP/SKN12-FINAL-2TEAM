from fastapi import APIRouter, Request, Body
from template.base.template_context import TemplateContext, TemplateType
from template.base.template_service import TemplateService
from template.account.common.account_serialize import (
    AccountLoginRequest, AccountLoginResponse,
    AccountSignupRequest, AccountLogoutRequest, AccountLogoutResponse,
    AccountInfoRequest, AccountInfoResponse
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

@router.post("/login")
async def account_login(request: AccountLoginRequest, req: Request):
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

@router.post("/accountlogout")
async def account_logout(request: AccountLogoutRequest, req: Request):
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
    """계좌 정보 조회 (샤딩 DB 사용 예시)"""
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