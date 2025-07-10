from fastapi import APIRouter, Request
from template.base.template_context import TemplateContext, TemplateType
from template.base.template_service import TemplateService
from template.autotrade.common.autotrade_serialize import (
    AutoTradeStrategyListRequest, AutoTradeStrategyCreateRequest, AutoTradeStrategyUpdateRequest,
    AutoTradeExecutionListRequest, AutoTradeBacktestRequest, AutoTradeAIStrategyRequest
)
from template.autotrade.common.autotrade_protocol import AutoTradeProtocol

router = APIRouter()

autotrade_protocol = AutoTradeProtocol()

def setup_autotrade_protocol_callbacks():
    """AutoTrade protocol 콜백 설정 (main.py에서 한 번만 호출됨)"""
    autotrade_template = TemplateContext.get_template(TemplateType.AUTOTRADE)
    autotrade_protocol.on_autotrade_strategy_list_req_callback = getattr(autotrade_template, "on_autotrade_strategy_list_req", None)
    autotrade_protocol.on_autotrade_strategy_create_req_callback = getattr(autotrade_template, "on_autotrade_strategy_create_req", None)
    autotrade_protocol.on_autotrade_strategy_update_req_callback = getattr(autotrade_template, "on_autotrade_strategy_update_req", None)
    autotrade_protocol.on_autotrade_execution_list_req_callback = getattr(autotrade_template, "on_autotrade_execution_list_req", None)
    autotrade_protocol.on_autotrade_backtest_req_callback = getattr(autotrade_template, "on_autotrade_backtest_req", None)
    autotrade_protocol.on_autotrade_ai_strategy_req_callback = getattr(autotrade_template, "on_autotrade_ai_strategy_req", None)

@router.post("/strategy/list")
async def autotrade_strategy_list(request: AutoTradeStrategyListRequest, req: Request):
    """매매 전략 목록"""
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
        autotrade_protocol.autotrade_strategy_list_req_controller
    )

@router.post("/strategy/create")
async def autotrade_strategy_create(request: AutoTradeStrategyCreateRequest, req: Request):
    """매매 전략 생성"""
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
        autotrade_protocol.autotrade_strategy_create_req_controller
    )

@router.post("/strategy/update")
async def autotrade_strategy_update(request: AutoTradeStrategyUpdateRequest, req: Request):
    """매매 전략 수정"""
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
        autotrade_protocol.autotrade_strategy_update_req_controller
    )

@router.post("/backtest")
async def autotrade_backtest(request: AutoTradeBacktestRequest, req: Request):
    """백테스트 실행"""
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
        autotrade_protocol.autotrade_backtest_req_controller
    )

@router.post("/execution/list")
async def autotrade_execution_list(request: AutoTradeExecutionListRequest, req: Request):
    """거래 실행 내역 조회"""
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
        autotrade_protocol.autotrade_execution_list_req_controller
    )

@router.post("/ai-strategy")
async def autotrade_ai_strategy(request: AutoTradeAIStrategyRequest, req: Request):
    """AI 전략 생성"""
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
        autotrade_protocol.autotrade_ai_strategy_req_controller
    )