from .portfolio_serialize import (
    PortfolioGetRequest, PortfolioAddStockRequest, PortfolioRemoveStockRequest,
    PortfolioRebalanceRequest, PortfolioPerformanceRequest
)

class PortfolioProtocol:
    def __init__(self):
        self.on_portfolio_get_req_callback = None
        self.on_portfolio_add_stock_req_callback = None
        self.on_portfolio_remove_stock_req_callback = None
        self.on_portfolio_rebalance_req_callback = None
        self.on_portfolio_performance_req_callback = None

    async def portfolio_get_req_controller(self, session, msg: bytes, length: int):
        request = PortfolioGetRequest.model_validate_json(msg)
        if self.on_portfolio_get_req_callback:
            return await self.on_portfolio_get_req_callback(session, request)
        raise NotImplementedError('on_portfolio_get_req_callback is not set')

    async def portfolio_add_stock_req_controller(self, session, msg: bytes, length: int):
        request = PortfolioAddStockRequest.model_validate_json(msg)
        if self.on_portfolio_add_stock_req_callback:
            return await self.on_portfolio_add_stock_req_callback(session, request)
        raise NotImplementedError('on_portfolio_add_stock_req_callback is not set')

    async def portfolio_remove_stock_req_controller(self, session, msg: bytes, length: int):
        request = PortfolioRemoveStockRequest.model_validate_json(msg)
        if self.on_portfolio_remove_stock_req_callback:
            return await self.on_portfolio_remove_stock_req_callback(session, request)
        raise NotImplementedError('on_portfolio_remove_stock_req_callback is not set')

    async def portfolio_rebalance_req_controller(self, session, msg: bytes, length: int):
        request = PortfolioRebalanceRequest.model_validate_json(msg)
        if self.on_portfolio_rebalance_req_callback:
            return await self.on_portfolio_rebalance_req_callback(session, request)
        raise NotImplementedError('on_portfolio_rebalance_req_callback is not set')

    async def portfolio_performance_req_controller(self, session, msg: bytes, length: int):
        request = PortfolioPerformanceRequest.model_validate_json(msg)
        if self.on_portfolio_performance_req_callback:
            return await self.on_portfolio_performance_req_callback(session, request)
        raise NotImplementedError('on_portfolio_performance_req_callback is not set')