from .market_serialize import (
    MarketSearchSecuritiesRequest, MarketGetPriceDataRequest, MarketGetRealtimePriceRequest,
    MarketGetTechnicalIndicatorsRequest, MarketGetOverviewRequest, MarketGetNewsRequest,
    MarketGetTrendingRequest, MarketGetSectorPerformanceRequest, MarketGetEconomicIndicatorsRequest,
    MarketGetSecurityDetailRequest, MarketCreatePriceAlertRequest, MarketManageWatchlistRequest,
    MarketGetCalendarRequest
)

class MarketProtocol:
    def __init__(self):
        self.on_market_search_securities_req_callback = None
        self.on_market_get_price_data_req_callback = None
        self.on_market_get_realtime_price_req_callback = None
        self.on_market_get_technical_indicators_req_callback = None
        self.on_market_get_overview_req_callback = None
        self.on_market_get_news_req_callback = None
        self.on_market_get_trending_req_callback = None
        self.on_market_get_sector_performance_req_callback = None
        self.on_market_get_economic_indicators_req_callback = None
        self.on_market_get_security_detail_req_callback = None
        self.on_market_create_price_alert_req_callback = None
        self.on_market_manage_watchlist_req_callback = None
        self.on_market_get_calendar_req_callback = None

    async def market_search_securities_req_controller(self, session, msg: bytes, length: int):
        request = MarketSearchSecuritiesRequest.model_validate_json(msg)
        if self.on_market_search_securities_req_callback:
            return await self.on_market_search_securities_req_callback(session, request)
        raise NotImplementedError('on_market_search_securities_req_callback is not set')

    async def market_get_price_data_req_controller(self, session, msg: bytes, length: int):
        request = MarketGetPriceDataRequest.model_validate_json(msg)
        if self.on_market_get_price_data_req_callback:
            return await self.on_market_get_price_data_req_callback(session, request)
        raise NotImplementedError('on_market_get_price_data_req_callback is not set')

    async def market_get_realtime_price_req_controller(self, session, msg: bytes, length: int):
        request = MarketGetRealtimePriceRequest.model_validate_json(msg)
        if self.on_market_get_realtime_price_req_callback:
            return await self.on_market_get_realtime_price_req_callback(session, request)
        raise NotImplementedError('on_market_get_realtime_price_req_callback is not set')

    async def market_get_technical_indicators_req_controller(self, session, msg: bytes, length: int):
        request = MarketGetTechnicalIndicatorsRequest.model_validate_json(msg)
        if self.on_market_get_technical_indicators_req_callback:
            return await self.on_market_get_technical_indicators_req_callback(session, request)
        raise NotImplementedError('on_market_get_technical_indicators_req_callback is not set')

    async def market_get_overview_req_controller(self, session, msg: bytes, length: int):
        request = MarketGetOverviewRequest.model_validate_json(msg)
        if self.on_market_get_overview_req_callback:
            return await self.on_market_get_overview_req_callback(session, request)
        raise NotImplementedError('on_market_get_overview_req_callback is not set')

    async def market_get_news_req_controller(self, session, msg: bytes, length: int):
        request = MarketGetNewsRequest.model_validate_json(msg)
        if self.on_market_get_news_req_callback:
            return await self.on_market_get_news_req_callback(session, request)
        raise NotImplementedError('on_market_get_news_req_callback is not set')

    async def market_get_trending_req_controller(self, session, msg: bytes, length: int):
        request = MarketGetTrendingRequest.model_validate_json(msg)
        if self.on_market_get_trending_req_callback:
            return await self.on_market_get_trending_req_callback(session, request)
        raise NotImplementedError('on_market_get_trending_req_callback is not set')

    async def market_get_sector_performance_req_controller(self, session, msg: bytes, length: int):
        request = MarketGetSectorPerformanceRequest.model_validate_json(msg)
        if self.on_market_get_sector_performance_req_callback:
            return await self.on_market_get_sector_performance_req_callback(session, request)
        raise NotImplementedError('on_market_get_sector_performance_req_callback is not set')

    async def market_get_economic_indicators_req_controller(self, session, msg: bytes, length: int):
        request = MarketGetEconomicIndicatorsRequest.model_validate_json(msg)
        if self.on_market_get_economic_indicators_req_callback:
            return await self.on_market_get_economic_indicators_req_callback(session, request)
        raise NotImplementedError('on_market_get_economic_indicators_req_callback is not set')

    async def market_get_security_detail_req_controller(self, session, msg: bytes, length: int):
        request = MarketGetSecurityDetailRequest.model_validate_json(msg)
        if self.on_market_get_security_detail_req_callback:
            return await self.on_market_get_security_detail_req_callback(session, request)
        raise NotImplementedError('on_market_get_security_detail_req_callback is not set')

    async def market_create_price_alert_req_controller(self, session, msg: bytes, length: int):
        request = MarketCreatePriceAlertRequest.model_validate_json(msg)
        if self.on_market_create_price_alert_req_callback:
            return await self.on_market_create_price_alert_req_callback(session, request)
        raise NotImplementedError('on_market_create_price_alert_req_callback is not set')

    async def market_manage_watchlist_req_controller(self, session, msg: bytes, length: int):
        request = MarketManageWatchlistRequest.model_validate_json(msg)
        if self.on_market_manage_watchlist_req_callback:
            return await self.on_market_manage_watchlist_req_callback(session, request)
        raise NotImplementedError('on_market_manage_watchlist_req_callback is not set')

    async def market_get_calendar_req_controller(self, session, msg: bytes, length: int):
        request = MarketGetCalendarRequest.model_validate_json(msg)
        if self.on_market_get_calendar_req_callback:
            return await self.on_market_get_calendar_req_callback(session, request)
        raise NotImplementedError('on_market_get_calendar_req_callback is not set')