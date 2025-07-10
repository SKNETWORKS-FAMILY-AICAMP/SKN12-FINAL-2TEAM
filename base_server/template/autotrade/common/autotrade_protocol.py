from .autotrade_serialize import (
    AutoTradeStrategyListRequest, AutoTradeStrategyCreateRequest, AutoTradeStrategyUpdateRequest,
    AutoTradeExecutionListRequest, AutoTradeBacktestRequest, AutoTradeAIStrategyRequest
)

class AutoTradeProtocol:
    def __init__(self):
        self.on_autotrade_strategy_list_req_callback = None
        self.on_autotrade_strategy_create_req_callback = None
        self.on_autotrade_strategy_update_req_callback = None
        self.on_autotrade_execution_list_req_callback = None
        self.on_autotrade_backtest_req_callback = None
        self.on_autotrade_ai_strategy_req_callback = None

    async def autotrade_strategy_list_req_controller(self, session, msg: bytes, length: int):
        request = AutoTradeStrategyListRequest.model_validate_json(msg)
        if self.on_autotrade_strategy_list_req_callback:
            return await self.on_autotrade_strategy_list_req_callback(session, request)
        raise NotImplementedError('on_autotrade_strategy_list_req_callback is not set')

    async def autotrade_strategy_create_req_controller(self, session, msg: bytes, length: int):
        request = AutoTradeStrategyCreateRequest.model_validate_json(msg)
        if self.on_autotrade_strategy_create_req_callback:
            return await self.on_autotrade_strategy_create_req_callback(session, request)
        raise NotImplementedError('on_autotrade_strategy_create_req_callback is not set')

    async def autotrade_strategy_update_req_controller(self, session, msg: bytes, length: int):
        request = AutoTradeStrategyUpdateRequest.model_validate_json(msg)
        if self.on_autotrade_strategy_update_req_callback:
            return await self.on_autotrade_strategy_update_req_callback(session, request)
        raise NotImplementedError('on_autotrade_strategy_update_req_callback is not set')

    async def autotrade_execution_list_req_controller(self, session, msg: bytes, length: int):
        request = AutoTradeExecutionListRequest.model_validate_json(msg)
        if self.on_autotrade_execution_list_req_callback:
            return await self.on_autotrade_execution_list_req_callback(session, request)
        raise NotImplementedError('on_autotrade_execution_list_req_callback is not set')

    async def autotrade_backtest_req_controller(self, session, msg: bytes, length: int):
        request = AutoTradeBacktestRequest.model_validate_json(msg)
        if self.on_autotrade_backtest_req_callback:
            return await self.on_autotrade_backtest_req_callback(session, request)
        raise NotImplementedError('on_autotrade_backtest_req_callback is not set')

    async def autotrade_ai_strategy_req_controller(self, session, msg: bytes, length: int):
        request = AutoTradeAIStrategyRequest.model_validate_json(msg)
        if self.on_autotrade_ai_strategy_req_callback:
            return await self.on_autotrade_ai_strategy_req_callback(session, request)
        raise NotImplementedError('on_autotrade_ai_strategy_req_callback is not set')