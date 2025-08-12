import json
import aiohttp
from fastapi import APIRouter, Request
from template.base.template_context import TemplateContext, TemplateType
from template.base.template_service import TemplateService
from template.dashboard.common.dashboard_serialize import (
    DashboardMainRequest, DashboardAlertsRequest, DashboardPerformanceRequest,
    SecuritiesLoginRequest, SecuritiesLoginResponse,
    PriceRequest, PriceResponse
)
from template.dashboard.common.dashboard_protocol import DashboardProtocol
from fastapi import Header
from typing import Annotated
router = APIRouter()

dashboard_protocol = DashboardProtocol()

def setup_dashboard_protocol_callbacks():
    """Dashboard protocol 콜백 설정 (main.py에서 한 번만 호출됨)"""
    dashboard_template = TemplateContext.get_template(TemplateType.DASHBOARD)
    dashboard_protocol.on_dashboard_main_req_callback = getattr(dashboard_template, "on_dashboard_main_req", None)
    dashboard_protocol.on_dashboard_alerts_req_callback = getattr(dashboard_template, "on_dashboard_alerts_req", None)
    dashboard_protocol.on_dashboard_performance_req_callback = getattr(dashboard_template, "on_dashboard_performance_req", None)
    dashboard_protocol.on_dashboard_oauth_req_callback = getattr(dashboard_template, "on_dashboard_oauth_req", None)
    dashboard_protocol.on_dashboard_price_us_req_callback = getattr(dashboard_template, "on_dashboard_price_us_req", None)
@router.post("/main")
async def dashboard_main(request: DashboardMainRequest, req: Request):
    """대시보드 메인 데이터"""
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
        dashboard_protocol.dashboard_main_req_controller
    )

@router.post("/alerts")
async def dashboard_alerts(request: DashboardAlertsRequest, req: Request):
    """알림 목록"""
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
        dashboard_protocol.dashboard_alerts_req_controller
    )

@router.post("/performance")
async def dashboard_performance(request: DashboardPerformanceRequest, req: Request):
    """성과 분석"""
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
        dashboard_protocol.dashboard_performance_req_controller
    )

@router.post("/oauth")
async def dashboard_oauth(
    request: SecuritiesLoginRequest,
    req: Request,
    authorization: Annotated[str | None, Header()] = None,
):
    """OAuth 인증"""
    print(f"📥 OAuth body received: {request.model_dump_json()}")

    # 바디에서 accessToken 우선 사용
    payload = request.model_dump()
    access_token = payload.get("accessToken")

    # 바디에 없으면 헤더에서 추출
    if not access_token and authorization and authorization.startswith("Bearer "):
        access_token = authorization.removeprefix("Bearer ").strip()

    print(f"🔑 최종 accessToken: {access_token}")

    # IP 추출
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(",")[0]

    # accessToken이 있으면 payload에 반영
    if access_token:
        payload["accessToken"] = access_token

    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        json.dumps(payload, ensure_ascii=False),
        dashboard_protocol.dashboard_oauth_req_controller
    )


@router.post("/price/us")
async def dashboard_price_us(
    request: PriceRequest,
    req: Request,
    authorization: Annotated[str | None, Header()] = None,
):
    """미국 나스닥 종가 조회"""
    print(f"📥 미국 종가 요청: {request.model_dump_json()}")

    # 바디에서 accessToken 우선 사용
    payload = request.model_dump()
    access_token = payload.get("accessToken")

    # 바디에 없으면 헤더에서 추출
    if not access_token and authorization and authorization.startswith("Bearer "):
        access_token = authorization.removeprefix("Bearer ").strip()

    print(f"🔑 최종 accessToken: {access_token}")

    # IP 추출
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(",")[0]

    # accessToken이 있으면 payload에 반영
    if access_token:
        payload["accessToken"] = access_token

    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        json.dumps(payload, ensure_ascii=False),
        dashboard_protocol.dashboard_price_us_req_controller
    )