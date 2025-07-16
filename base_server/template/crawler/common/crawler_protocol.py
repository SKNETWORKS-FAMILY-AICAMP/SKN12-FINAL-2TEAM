from .crawler_serialize import (
    CrawlerExecuteRequest, CrawlerStatusRequest, CrawlerHealthRequest,
    CrawlerStopRequest, CrawlerDataRequest
)

class CrawlerProtocol:
    def __init__(self):
        self.on_crawler_execute_req_callback = None
        self.on_crawler_status_req_callback = None
        self.on_crawler_health_req_callback = None
        self.on_crawler_stop_req_callback = None
        self.on_crawler_data_req_callback = None

    async def crawler_execute_req_controller(self, session, msg: bytes, length: int):
        request = CrawlerExecuteRequest.model_validate_json(msg)
        if self.on_crawler_execute_req_callback:
            return await self.on_crawler_execute_req_callback(session, request)
        raise NotImplementedError('on_crawler_execute_req_callback is not set')

    async def crawler_status_req_controller(self, session, msg: bytes, length: int):
        request = CrawlerStatusRequest.model_validate_json(msg)
        if self.on_crawler_status_req_callback:
            return await self.on_crawler_status_req_callback(session, request)
        raise NotImplementedError('on_crawler_status_req_callback is not set')

    async def crawler_health_req_controller(self, session, msg: bytes, length: int):
        request = CrawlerHealthRequest.model_validate_json(msg)
        if self.on_crawler_health_req_callback:
            return await self.on_crawler_health_req_callback(session, request)
        raise NotImplementedError('on_crawler_health_req_callback is not set')

    async def crawler_stop_req_controller(self, session, msg: bytes, length: int):
        request = CrawlerStopRequest.model_validate_json(msg)
        if self.on_crawler_stop_req_callback:
            return await self.on_crawler_stop_req_callback(session, request)
        raise NotImplementedError('on_crawler_stop_req_callback is not set')

    async def crawler_data_req_controller(self, session, msg: bytes, length: int):
        request = CrawlerDataRequest.model_validate_json(msg)
        if self.on_crawler_data_req_callback:
            return await self.on_crawler_data_req_callback(session, request)
        raise NotImplementedError('on_crawler_data_req_callback is not set')