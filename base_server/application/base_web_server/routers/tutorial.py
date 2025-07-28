from fastapi import APIRouter, Request
from template.base.template_context import TemplateContext, TemplateType
from template.base.template_service import TemplateService
from template.tutorial.common.tutorial_serialize import (
    TutorialCompleteStepRequest, TutorialGetProgressRequest
)
from template.tutorial.common.tutorial_protocol import TutorialProtocol

router = APIRouter()

tutorial_protocol = TutorialProtocol()

def setup_tutorial_protocol_callbacks():
    """Tutorial protocol 콜백 설정 (main.py에서 한 번만 호출됨)"""
    tutorial_template = TemplateContext.get_template(TemplateType.TUTORIAL)
    tutorial_protocol.on_tutorial_complete_step_req_callback = getattr(tutorial_template, "on_tutorial_complete_step_req", None)
    tutorial_protocol.on_tutorial_get_progress_req_callback = getattr(tutorial_template, "on_tutorial_get_progress_req", None)

@router.post("/complete/step")
async def tutorial_complete_step(request: TutorialCompleteStepRequest, req: Request):
    """튜토리얼 스텝 완료 저장"""
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
        tutorial_protocol.tutorial_complete_step_req_controller
    )

@router.post("/progress")
async def tutorial_get_progress(request: TutorialGetProgressRequest, req: Request):
    """튜토리얼 진행 상태 조회"""
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
        tutorial_protocol.tutorial_get_progress_req_controller
    )