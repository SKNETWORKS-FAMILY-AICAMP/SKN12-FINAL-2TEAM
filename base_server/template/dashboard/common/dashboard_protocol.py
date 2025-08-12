from .dashboard_serialize import (
    DashboardMainRequest, DashboardAlertsRequest, DashboardPerformanceRequest, PriceRequest, SecuritiesLoginRequest
)

class DashboardProtocol:
    def __init__(self):
        # 콜백 속성
        self.on_dashboard_main_req_callback = None
        self.on_dashboard_alerts_req_callback = None
        self.on_dashboard_performance_req_callback = None
        self.on_dashboard_oauth_req_callback = None
        self.on_dashboard_price_us_req_callback = None

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
