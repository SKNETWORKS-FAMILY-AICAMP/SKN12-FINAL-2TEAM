from fastapi import APIRouter, Request
from template.base.template_service import TemplateService
from template.securities.common.securities_serialize import SecuritiesLoginRequest
from template.securities.common.securities_protocol import SecuritiesProtocol

router = APIRouter()
securities_protocol = SecuritiesProtocol()

@router.post("/login")
async def securities_login(request: SecuritiesLoginRequest, req: Request):
    ip = req.headers.get("X-Forwarded-For", req.client.host if req.client else "unknown").split(",")[0]
    return await TemplateService.run_anonymous(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        securities_protocol.securities_login_req_controller
    )
