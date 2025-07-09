from fastapi import APIRouter, Request
from template.base.template_context import TemplateContext, TemplateType
from template.base.template_service import TemplateService
from template.tutorial.common.tutorial_serialize import (
    TutorialStartRequest, TutorialProgressRequest, TutorialCompleteRequest, TutorialListRequest
)
from template.tutorial.common.tutorial_protocol import TutorialProtocol

router = APIRouter()

tutorial_protocol = TutorialProtocol()

def setup_tutorial_protocol_callbacks():
    """Tutorial protocol 콜백 설정 (main.py에서 한 번만 호출됨)"""
    tutorial_template = TemplateContext.get_template(TemplateType.TUTORIAL)
    tutorial_protocol.on_tutorial_start_req_callback = getattr(tutorial_template, "on_tutorial_start_req", None)
    tutorial_protocol.on_tutorial_progress_req_callback = getattr(tutorial_template, "on_tutorial_progress_req", None)
    tutorial_protocol.on_tutorial_complete_req_callback = getattr(tutorial_template, "on_tutorial_complete_req", None)
    tutorial_protocol.on_tutorial_list_req_callback = getattr(tutorial_template, "on_tutorial_list_req", None)

@router.post("/start")
async def tutorial_start(request: TutorialStartRequest, req: Request):
    """튜토리얼 시작"""
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
        tutorial_protocol.tutorial_start_req_controller
    )

@router.post("/progress")
async def tutorial_progress(request: TutorialProgressRequest, req: Request):
    """튜토리얼 진행 상태 업데이트"""
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
        tutorial_protocol.tutorial_progress_req_controller
    )

@router.post("/complete")
async def tutorial_complete(request: TutorialCompleteRequest, req: Request):
    """튜토리얼 완료"""
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
        tutorial_protocol.tutorial_complete_req_controller
    )

@router.post("/list")
async def tutorial_list(request: TutorialListRequest, req: Request):
    """이용 가능한 튜토리얼 목록"""
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
        tutorial_protocol.tutorial_list_req_controller
    )