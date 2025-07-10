from .dashboard_serialize import (
    DashboardMainRequest, DashboardAlertsRequest, DashboardPerformanceRequest
)

class DashboardProtocol:
    def __init__(self):
        # 콜백 속성
        self.on_dashboard_main_req_callback = None
        self.on_dashboard_alerts_req_callback = None
        self.on_dashboard_performance_req_callback = None

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