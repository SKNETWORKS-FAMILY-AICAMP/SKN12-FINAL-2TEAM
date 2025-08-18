from .dashboard_serialize import (
    DashboardMainRequest, DashboardAlertsRequest, DashboardPerformanceRequest, PriceRequest, SecuritiesLoginRequest,
    StockRecommendationRequest, StockRecommendationResponse, EconomicCalendarRequest, EconomicCalendarResponse, MarketRiskPremiumRequest
)

class DashboardProtocol:
    def __init__(self):
        # 콜백 속성
        self.on_dashboard_main_req_callback = None
        self.on_dashboard_alerts_req_callback = None
        self.on_dashboard_performance_req_callback = None
        self.on_dashboard_oauth_req_callback = None
        self.on_dashboard_price_us_req_callback = None
        self.on_stock_recommendation_req_callback = None
        self.on_economic_calendar_req_callback = None
        self.on_market_risk_premium_req_callback = None

    async def dashboard_main_req_controller(self, session, msg: bytes, length: int):
        request = DashboardMainRequest.model_validate_json(msg)
        if self.on_dashboard_main_req_callback:
            return await self.on_dashboard_main_req_callback(session, request)
        raise NotImplementedError('on_dashboard_main_req_callback is not set')

    async def dashboard_alerts_req_controller(self, session, msg: bytes, length: int):
        request = DashboardAlertsRequest.model_validate_json(msg)
        if self.on_dashboard_alerts_req_callback:
            return await self.on_dashboard_alerts_req_callback(session, request)
        raise NotImplementedError('on_dashboard_alerts_req_callback is not set')

    async def dashboard_performance_req_controller(self, session, msg: bytes, length: int):
        request = DashboardPerformanceRequest.model_validate_json(msg)
        if self.on_dashboard_performance_req_callback:
            return await self.on_dashboard_performance_req_callback(session, request)
        raise NotImplementedError('on_dashboard_performance_req_callback is not set')
    
    async def dashboard_oauth_req_controller(self, session, msg: bytes, length: int):
        # OAuth 관련 요청 처리 (예시로 추가)
        request = SecuritiesLoginRequest.model_validate_json(msg)
        if self.on_dashboard_oauth_req_callback:
            return await self.on_dashboard_oauth_req_callback(session, request)
        raise NotImplementedError('on_dashboard_oauth_req_callback is not set')
    
    async def dashboard_price_us_req_controller(self, session, msg: bytes, length: int):
        # 미국 나스닥 종가 조회 요청 처리
        request = PriceRequest.model_validate_json(msg)
        if self.on_dashboard_price_us_req_callback:
            return await self.on_dashboard_price_us_req_callback(session, request)
        raise NotImplementedError('on_dashboard_price_us_req_callback is not set')

    async def stock_recommendation_req_controller(self, session, msg: bytes, length: int):
        # 주식 종목 추천 요청 처리 (매개변수 2개만 사용)
        request = StockRecommendationRequest.model_validate_json(msg)
        if self.on_stock_recommendation_req_callback:
            return await self.on_stock_recommendation_req_callback(session, request)
        raise NotImplementedError('on_stock_recommendation_req_callback is not set')

    async def economic_calendar_req_controller(self, session, msg: bytes, length: int):
        # 경제 일정 요청 처리
        request = EconomicCalendarRequest.model_validate_json(msg)
        if self.on_economic_calendar_req_callback:
            return await self.on_economic_calendar_req_callback(session, request)
        raise NotImplementedError('on_economic_calendar_req_callback is not set')

    async def market_risk_premium_req_controller(self, session, msg: bytes, length: int):
        request = MarketRiskPremiumRequest.model_validate_json(msg)
        if self.on_market_risk_premium_req_callback:
            return await self.on_market_risk_premium_req_callback(session, request)
        raise NotImplementedError('on_market_risk_premium_req_callback is not set')
