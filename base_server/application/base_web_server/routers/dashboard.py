from fastapi import APIRouter, Request
from template.base.template_context import TemplateContext, TemplateType
from template.base.template_service import TemplateService
from template.dashboard.common.dashboard_serialize import (
    DashboardMainRequest, DashboardAlertsRequest, DashboardPerformanceRequest
)
from template.dashboard.common.dashboard_protocol import DashboardProtocol

router = APIRouter()

dashboard_protocol = DashboardProtocol()

def setup_dashboard_protocol_callbacks():
    """Dashboard protocol 콜백 설정 (main.py에서 한 번만 호출됨)"""
    dashboard_template = TemplateContext.get_template(TemplateType.DASHBOARD)
    dashboard_protocol.on_dashboard_main_req_callback = getattr(dashboard_template, "on_dashboard_main_req", None)
    dashboard_protocol.on_dashboard_alerts_req_callback = getattr(dashboard_template, "on_dashboard_alerts_req", None)
    dashboard_protocol.on_dashboard_performance_req_callback = getattr(dashboard_template, "on_dashboard_performance_req", None)

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