from fastapi import APIRouter, Request
from template.base.template_context import TemplateContext, TemplateType
from template.base.template_service import TemplateService
from template.market.common.market_serialize import (
    MarketSearchSecuritiesRequest, MarketGetPriceDataRequest, MarketGetRealtimePriceRequest,
    MarketGetTechnicalIndicatorsRequest, MarketGetOverviewRequest, MarketGetNewsRequest,
    MarketGetTrendingRequest, MarketGetSectorPerformanceRequest, MarketGetEconomicIndicatorsRequest,
    MarketGetSecurityDetailRequest, MarketCreatePriceAlertRequest, MarketManageWatchlistRequest,
    MarketGetCalendarRequest
)
from template.market.common.market_protocol import MarketProtocol

router = APIRouter()

market_protocol = MarketProtocol()

def setup_market_protocol_callbacks():
    """Market protocol 콜백 설정 (main.py에서 한 번만 호출됨)"""
    market_template = TemplateContext.get_template(TemplateType.MARKET)
    market_protocol.on_market_search_securities_req_callback = getattr(market_template, "on_market_search_securities_req", None)
    market_protocol.on_market_get_price_data_req_callback = getattr(market_template, "on_market_get_price_data_req", None)
    market_protocol.on_market_get_realtime_price_req_callback = getattr(market_template, "on_market_get_realtime_price_req", None)
    market_protocol.on_market_get_technical_indicators_req_callback = getattr(market_template, "on_market_get_technical_indicators_req", None)
    market_protocol.on_market_get_overview_req_callback = getattr(market_template, "on_market_get_overview_req", None)
    market_protocol.on_market_get_news_req_callback = getattr(market_template, "on_market_get_news_req", None)
    market_protocol.on_market_get_trending_req_callback = getattr(market_template, "on_market_get_trending_req", None)
    market_protocol.on_market_get_sector_performance_req_callback = getattr(market_template, "on_market_get_sector_performance_req", None)
    market_protocol.on_market_get_economic_indicators_req_callback = getattr(market_template, "on_market_get_economic_indicators_req", None)
    market_protocol.on_market_get_security_detail_req_callback = getattr(market_template, "on_market_get_security_detail_req", None)
    market_protocol.on_market_create_price_alert_req_callback = getattr(market_template, "on_market_create_price_alert_req", None)
    market_protocol.on_market_manage_watchlist_req_callback = getattr(market_template, "on_market_manage_watchlist_req", None)
    market_protocol.on_market_get_calendar_req_callback = getattr(market_template, "on_market_get_calendar_req", None)

@router.post("/search-securities")
async def market_search_securities(request: MarketSearchSecuritiesRequest, req: Request):
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
        market_protocol.market_search_securities_req_controller
    )

@router.post("/get-price-data")
async def market_get_price_data(request: MarketGetPriceDataRequest, req: Request):
    """가격 데이터 조회"""
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
        market_protocol.market_get_price_data_req_controller
    )

@router.post("/get-realtime-price")
async def market_get_realtime_price(request: MarketGetRealtimePriceRequest, req: Request):
    """실시간 가격 조회"""
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
        market_protocol.market_get_realtime_price_req_controller
    )

@router.post("/get-technical-indicators")
async def market_get_technical_indicators(request: MarketGetTechnicalIndicatorsRequest, req: Request):
    """기술적 지표 조회"""
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
        market_protocol.market_get_technical_indicators_req_controller
    )

@router.post("/get-overview")
async def market_get_overview(request: MarketGetOverviewRequest, req: Request):
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
        market_protocol.market_get_overview_req_controller
    )

@router.post("/get-news")
async def market_get_news(request: MarketGetNewsRequest, req: Request):
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
        market_protocol.market_get_news_req_controller
    )

@router.post("/get-trending")
async def market_get_trending(request: MarketGetTrendingRequest, req: Request):
    """인기 종목 조회"""
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
        market_protocol.market_get_trending_req_controller
    )

@router.post("/get-sector-performance")
async def market_get_sector_performance(request: MarketGetSectorPerformanceRequest, req: Request):
    """섹터 성과 조회"""
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
        market_protocol.market_get_sector_performance_req_controller
    )

@router.post("/get-economic-indicators")
async def market_get_economic_indicators(request: MarketGetEconomicIndicatorsRequest, req: Request):
    """경제 지표 조회"""
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
        market_protocol.market_get_economic_indicators_req_controller
    )

@router.post("/get-security-detail")
async def market_get_security_detail(request: MarketGetSecurityDetailRequest, req: Request):
    """종목 상세 조회"""
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
        market_protocol.market_get_security_detail_req_controller
    )

@router.post("/create-price-alert")
async def market_create_price_alert(request: MarketCreatePriceAlertRequest, req: Request):
    """가격 알림 생성"""
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
        market_protocol.market_create_price_alert_req_controller
    )

@router.post("/manage-watchlist")
async def market_manage_watchlist(request: MarketManageWatchlistRequest, req: Request):
    """관심 종목 관리"""
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
        market_protocol.market_manage_watchlist_req_controller
    )

@router.post("/get-calendar")
async def market_get_calendar(request: MarketGetCalendarRequest, req: Request):
    """경제 캘린더 조회"""
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
        market_protocol.market_get_calendar_req_controller
    )