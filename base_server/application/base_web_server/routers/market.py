from fastapi import APIRouter, Request
from template.base.template_context import TemplateContext, TemplateType
from template.base.template_service import TemplateService
from template.market.common.market_serialize import (
    MarketSecuritySearchRequest, MarketPriceRequest, MarketNewsRequest,
    MarketOverviewRequest, MarketRealTimeRequest
)
from template.market.common.market_protocol import MarketProtocol

router = APIRouter()

market_protocol = MarketProtocol()

def setup_market_protocol_callbacks():
    """Market protocol 콜백 설정 (main.py에서 한 번만 호출됨)"""
    market_template = TemplateContext.get_template(TemplateType.MARKET)
    market_protocol.on_market_security_search_req_callback = getattr(market_template, "on_market_security_search_req", None)
    market_protocol.on_market_price_req_callback = getattr(market_template, "on_market_price_req", None)
    market_protocol.on_market_news_req_callback = getattr(market_template, "on_market_news_req", None)
    market_protocol.on_market_overview_req_callback = getattr(market_template, "on_market_overview_req", None)
    market_protocol.on_market_real_time_req_callback = getattr(market_template, "on_market_real_time_req", None)

@router.post("/security/search")
async def market_security_search(request: MarketSecuritySearchRequest, req: Request):
    """종목 검색"""
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
        market_protocol.market_security_search_req_controller
    )

@router.post("/price")
async def market_price(request: MarketPriceRequest, req: Request):
    """시세 조회"""
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
        market_protocol.market_price_req_controller
    )

@router.post("/overview")
async def market_overview(request: MarketOverviewRequest, req: Request):
    """시장 개요"""
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
        market_protocol.market_overview_req_controller
    )

@router.post("/news")
async def market_news(request: MarketNewsRequest, req: Request):
    """뉴스 조회"""
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
        market_protocol.market_news_req_controller
    )

@router.post("/real-time")
async def market_real_time(request: MarketRealTimeRequest, req: Request):
    """실시간 시장 데이터 조회"""
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
        market_protocol.market_real_time_req_controller
    )

