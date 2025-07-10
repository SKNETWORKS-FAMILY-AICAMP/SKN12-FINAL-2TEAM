from .market_serialize import (
    MarketSecuritySearchRequest, MarketPriceRequest, MarketNewsRequest,
    MarketOverviewRequest
)

class MarketProtocol:
    def __init__(self):
        self.on_market_security_search_req_callback = None
        self.on_market_price_req_callback = None
        self.on_market_news_req_callback = None
        self.on_market_overview_req_callback = None

    async def market_security_search_req_controller(self, session, msg: bytes, length: int):
        request = MarketSecuritySearchRequest.model_validate_json(msg)
        if self.on_market_security_search_req_callback:
            return await self.on_market_security_search_req_callback(session, request)
        raise NotImplementedError('on_market_security_search_req_callback is not set')

    async def market_price_req_controller(self, session, msg: bytes, length: int):
        request = MarketPriceRequest.model_validate_json(msg)
        if self.on_market_price_req_callback:
            return await self.on_market_price_req_callback(session, request)
        raise NotImplementedError('on_market_price_req_callback is not set')

    async def market_news_req_controller(self, session, msg: bytes, length: int):
        request = MarketNewsRequest.model_validate_json(msg)
        if self.on_market_news_req_callback:
            return await self.on_market_news_req_callback(session, request)
        raise NotImplementedError('on_market_news_req_callback is not set')

    async def market_overview_req_controller(self, session, msg: bytes, length: int):
        request = MarketOverviewRequest.model_validate_json(msg)
        if self.on_market_overview_req_callback:
            return await self.on_market_overview_req_callback(session, request)
        raise NotImplementedError('on_market_overview_req_callback is not set')