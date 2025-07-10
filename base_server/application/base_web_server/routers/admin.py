from fastapi import APIRouter, Request, Body
from template.base.template_context import TemplateContext, TemplateType
from template.base.template_service import TemplateService
from template.admin.common.admin_model import *
from template.admin.common.admin_protocol import AdminProtocol
from service.core.logger import Logger
from datetime import datetime

router = APIRouter()

admin_protocol = AdminProtocol()

def setup_admin_protocol_callbacks():
    """Admin protocol 콜백 설정"""
    admin_template = TemplateContext.get_template(TemplateType.ADMIN)
    admin_protocol.on_health_check_req_callback = getattr(admin_template, "on_health_check_req", None)
    admin_protocol.on_server_status_req_callback = getattr(admin_template, "on_server_status_req", None)
    admin_protocol.on_session_count_req_callback = getattr(admin_template, "on_session_count_req", None)

@router.post("/healthcheck")
async def health_check(request: HealthCheckRequest, req: Request):
    """
    헬스체크 엔드포인트
    - 데이터베이스, 캐시, 서비스 상태 확인
    """
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_administrator(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        admin_protocol.health_check_req_controller
    )

@router.post("/serverstatus")
async def server_status(request: ServerStatusRequest, req: Request):
    """
    서버 상태 엔드포인트
    - 서버 기본 정보 및 메트릭 조회
    """
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_administrator(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        admin_protocol.server_status_req_controller
    )

@router.post("/sessioncount")
async def session_count(request: SessionCountRequest, req: Request):
    """
    세션 카운트 엔드포인트
    - 활성 세션 수 조회
    """
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_administrator(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        admin_protocol.session_count_req_controller
    )

@router.get("/ping")
async def ping():
    """
    간단한 생존 확인 엔드포인트
    """
    return {"status": "pong", "timestamp": datetime.now().isoformat()}

@router.get("/metrics")
async def metrics(req: Request):
    """
    메트릭 정보만 조회하는 엔드포인트
    """
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    
    request = ServerStatusRequest(include_metrics=True)
    response_json = await TemplateService.run_administrator(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        admin_protocol.server_status_req_controller
    )
    
    # JSON 응답을 파싱해서 메트릭만 반환
    import json
    response_data = json.loads(response_json)
    return {
        "server_name": response_data.get("server_name"),
        "environment": response_data.get("environment"),
        "uptime": response_data.get("uptime"),
        "metrics": response_data.get("metrics")
    }