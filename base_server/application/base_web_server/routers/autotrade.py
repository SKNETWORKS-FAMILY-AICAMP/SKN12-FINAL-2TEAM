from fastapi import APIRouter, Request
from template.base.template_context import TemplateContext, TemplateType
from template.base.template_service import TemplateService
from template.autotrade.common.autotrade_serialize import (
    AutoTradeCreateStrategyRequest, AutoTradeGetStrategiesRequest, AutoTradeControlStrategyRequest,
    AutoTradeBacktestRequest, AutoTradeGetBacktestRequest, AutoTradeGetExecutionsRequest,
    AutoTradeGetRecommendationsRequest, AutoTradeGetPerformanceRequest, AutoTradeCopyStrategyRequest
)
from template.autotrade.common.autotrade_protocol import AutoTradeProtocol

router = APIRouter()

autotrade_protocol = AutoTradeProtocol()

def setup_autotrade_protocol_callbacks():
    """AutoTrade protocol 콜백 설정 (main.py에서 한 번만 호출됨)"""
    autotrade_template = TemplateContext.get_template(TemplateType.AUTOTRADE)
    autotrade_protocol.on_autotrade_create_strategy_req_callback = getattr(autotrade_template, "on_autotrade_create_strategy_req", None)
    autotrade_protocol.on_autotrade_get_strategies_req_callback = getattr(autotrade_template, "on_autotrade_get_strategies_req", None)
    autotrade_protocol.on_autotrade_control_strategy_req_callback = getattr(autotrade_template, "on_autotrade_control_strategy_req", None)
    autotrade_protocol.on_autotrade_backtest_req_callback = getattr(autotrade_template, "on_autotrade_backtest_req", None)
    autotrade_protocol.on_autotrade_get_backtest_req_callback = getattr(autotrade_template, "on_autotrade_get_backtest_req", None)
    autotrade_protocol.on_autotrade_get_executions_req_callback = getattr(autotrade_template, "on_autotrade_get_executions_req", None)
    autotrade_protocol.on_autotrade_get_recommendations_req_callback = getattr(autotrade_template, "on_autotrade_get_recommendations_req", None)
    autotrade_protocol.on_autotrade_get_performance_req_callback = getattr(autotrade_template, "on_autotrade_get_performance_req", None)
    autotrade_protocol.on_autotrade_copy_strategy_req_callback = getattr(autotrade_template, "on_autotrade_copy_strategy_req", None)

@router.post("/create-strategy")
async def autotrade_create_strategy(request: AutoTradeCreateStrategyRequest, req: Request):
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
        autotrade_protocol.autotrade_create_strategy_req_controller
    )

@router.post("/get-strategies")
async def autotrade_get_strategies(request: AutoTradeGetStrategiesRequest, req: Request):
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
        autotrade_protocol.autotrade_get_strategies_req_controller
    )

@router.post("/control-strategy")
async def autotrade_control_strategy(request: AutoTradeControlStrategyRequest, req: Request):
    """매매 전략 제어"""
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
        autotrade_protocol.autotrade_control_strategy_req_controller
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

@router.post("/get-backtest")
async def autotrade_get_backtest(request: AutoTradeGetBacktestRequest, req: Request):
    """백테스트 결과 조회"""
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
        autotrade_protocol.autotrade_get_backtest_req_controller
    )

@router.post("/get-executions")
async def autotrade_get_executions(request: AutoTradeGetExecutionsRequest, req: Request):
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
        autotrade_protocol.autotrade_get_executions_req_controller
    )

@router.post("/get-recommendations")
async def autotrade_get_recommendations(request: AutoTradeGetRecommendationsRequest, req: Request):
    """추천 전략 조회"""
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
        autotrade_protocol.autotrade_get_recommendations_req_controller
    )

@router.post("/get-performance")
async def autotrade_get_performance(request: AutoTradeGetPerformanceRequest, req: Request):
    """성과 조회"""
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
        autotrade_protocol.autotrade_get_performance_req_controller
    )

@router.post("/copy-strategy")
async def autotrade_copy_strategy(request: AutoTradeCopyStrategyRequest, req: Request):
    """전략 복사"""
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
        autotrade_protocol.autotrade_copy_strategy_req_controller
    )