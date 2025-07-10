from fastapi import APIRouter, Request
from template.base.template_context import TemplateContext, TemplateType
from template.base.template_service import TemplateService
from template.portfolio.common.portfolio_serialize import (
    PortfolioGetRequest, PortfolioAddStockRequest, PortfolioRemoveStockRequest,
    PortfolioRebalanceRequest, PortfolioPerformanceRequest
)
from template.portfolio.common.portfolio_protocol import PortfolioProtocol

router = APIRouter()

portfolio_protocol = PortfolioProtocol()

def setup_portfolio_protocol_callbacks():
    """Portfolio protocol 콜백 설정 (main.py에서 한 번만 호출됨)"""
    portfolio_template = TemplateContext.get_template(TemplateType.PORTFOLIO)
    portfolio_protocol.on_portfolio_get_req_callback = getattr(portfolio_template, "on_portfolio_get_req", None)
    portfolio_protocol.on_portfolio_add_stock_req_callback = getattr(portfolio_template, "on_portfolio_add_stock_req", None)
    portfolio_protocol.on_portfolio_remove_stock_req_callback = getattr(portfolio_template, "on_portfolio_remove_stock_req", None)
    portfolio_protocol.on_portfolio_rebalance_req_callback = getattr(portfolio_template, "on_portfolio_rebalance_req", None)
    portfolio_protocol.on_portfolio_performance_req_callback = getattr(portfolio_template, "on_portfolio_performance_req", None)

@router.post("/get")
async def portfolio_get(request: PortfolioGetRequest, req: Request):
    """포트폴리오 조회"""
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
        portfolio_protocol.portfolio_get_req_controller
    )

@router.post("/add-stock")
async def portfolio_add_stock(request: PortfolioAddStockRequest, req: Request):
    """종목 추가"""
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
        portfolio_protocol.portfolio_add_stock_req_controller
    )

@router.post("/remove-stock")
async def portfolio_remove_stock(request: PortfolioRemoveStockRequest, req: Request):
    """종목 삭제"""
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
        portfolio_protocol.portfolio_remove_stock_req_controller
    )

@router.post("/rebalance")
async def portfolio_rebalance(request: PortfolioRebalanceRequest, req: Request):
    """리밸런싱 분석"""
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
        portfolio_protocol.portfolio_rebalance_req_controller
    )

@router.post("/performance")
async def portfolio_performance(request: PortfolioPerformanceRequest, req: Request):
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
        portfolio_protocol.portfolio_performance_req_controller
    )