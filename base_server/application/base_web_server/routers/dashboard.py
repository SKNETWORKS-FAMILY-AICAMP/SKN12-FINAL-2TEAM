import json
import aiohttp
from fastapi import APIRouter, Request
from template.base.template_context import TemplateContext, TemplateType
from template.base.template_service import TemplateService
from template.dashboard.common.dashboard_serialize import (
    DashboardMainRequest, DashboardAlertsRequest, DashboardPerformanceRequest, PriceRequest, SecuritiesLoginRequest,
    StockRecommendationRequest, EconomicCalendarRequest, MarketRiskPremiumRequest
)
from template.dashboard.common.dashboard_protocol import DashboardProtocol
from fastapi import Header
from typing import Annotated
router = APIRouter()

dashboard_protocol = DashboardProtocol()

def setup_dashboard_protocol_callbacks():
    """Dashboard protocol 콜백 설정 (main.py에서 한 번만 호출됨)"""
    dashboard_template = TemplateContext.get_template(TemplateType.DASHBOARD)
    dashboard_protocol.on_dashboard_main_req_callback = getattr(dashboard_template, "on_dashboard_main_req", None)
    dashboard_protocol.on_dashboard_alerts_req_callback = getattr(dashboard_template, "on_dashboard_alerts_req", None)
    dashboard_protocol.on_dashboard_performance_req_callback = getattr(dashboard_template, "on_dashboard_performance_req", None)
    dashboard_protocol.on_dashboard_oauth_req_callback = getattr(dashboard_template, "on_dashboard_oauth_req", None)
    dashboard_protocol.on_dashboard_price_us_req_callback = getattr(dashboard_template, "on_dashboard_price_us_req", None)
    dashboard_protocol.on_stock_recommendation_req_callback = getattr(dashboard_template, "on_stock_recommendation_req", None)
    dashboard_protocol.on_economic_calendar_req_callback = getattr(dashboard_template, "on_economic_calendar_req", None)
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

@router.post("/oauth")
async def dashboard_oauth(
    request: SecuritiesLoginRequest,
    req: Request,
):
    """OAuth 인증"""
    print(f"📥 OAuth body received: {request.model_dump_json()}")

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
        dashboard_protocol.dashboard_oauth_req_controller
    )


@router.post("/price/us")
async def dashboard_price_us(
    request: PriceRequest,
    req: Request,
):
    """미국 나스닥 종가 조회"""
    print(f"📥 미국 종가 요청: {request.model_dump_json()}")

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
        dashboard_protocol.dashboard_price_us_req_controller
    )


@router.post("/stock/recommendation")
async def stock_recommendation(
    request: StockRecommendationRequest,
    req: Request,
):
    """주식 종목 추천 (매개변수 2개만 사용)"""
    print(f"📥 주식 추천 요청: {request.model_dump_json()}")
    print(f"🎯 시장: {request.market}, 전략: {request.strategy}")

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
        dashboard_protocol.stock_recommendation_req_controller
    )

@router.post("/economic-calendar")
async def economic_calendar(
    request: EconomicCalendarRequest,
    req: Request,
):
    """경제 일정 조회"""
    print(f"📥 경제 일정 요청: {request.model_dump_json()}")
    print(f"🔍 콜백 확인: {dashboard_protocol.on_economic_calendar_req_callback}")

    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]

    # 콜백이 설정되지 않은 경우 직접 템플릿 호출
    if dashboard_protocol.on_economic_calendar_req_callback is None:
        print("⚠️ 콜백이 설정되지 않음 - 직접 템플릿 호출")
        from template.base.template_context import TemplateContext, TemplateType
        dashboard_template = TemplateContext.get_template(TemplateType.DASHBOARD)
        if hasattr(dashboard_template, "on_economic_calendar_req"):
            print("✅ 템플릿 메서드 발견 - 직접 호출")
            result = await dashboard_template.on_economic_calendar_req(None, request)
            print(f"📤 템플릿 응답: {result}")
            # Pydantic 모델을 JSON으로 변환하여 반환
            return result.model_dump()
        else:
            print("❌ 템플릿 메서드 없음")
            return {"errorCode": -1, "sequence": request.sequence, "message": "템플릿 메서드 없음"}

    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        dashboard_protocol.economic_calendar_req_controller
    )


@router.post("/market-risk-premium")
async def market_risk_premium(
    request: MarketRiskPremiumRequest,
    req: Request,
):
    """시장 위험 프리미엄 조회"""
    print(f"📥 시장 위험 프리미엄 요청: {request.model_dump_json()}")

    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]

    # 콜백이 설정되지 않은 경우 직접 템플릿 호출
    if dashboard_protocol.on_market_risk_premium_req_callback is None:
        print("⚠️ 콜백이 설정되지 않음 - 직접 템플릿 호출")
        from template.base.template_context import TemplateContext, TemplateType
        dashboard_template = TemplateContext.get_template(TemplateType.DASHBOARD)
        if hasattr(dashboard_template, "on_market_risk_premium_req"):
            print("✅ 템플릿 메서드 발견 - 직접 호출")
            result = await dashboard_template.on_market_risk_premium_req(None, request)
            print(f"📤 템플릿 응답: {result}")
            # Pydantic 모델을 JSON으로 변환하여 반환
            return result.model_dump()
        else:
            print("❌ 템플릿 메서드 없음")
            return {"errorCode": -1, "sequence": request.sequence, "message": "템플릿 메서드 없음"}

    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        dashboard_protocol.market_risk_premium_req_controller
    )