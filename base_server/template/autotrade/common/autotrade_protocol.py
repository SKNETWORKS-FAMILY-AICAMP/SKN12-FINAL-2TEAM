from .autotrade_serialize import (
    AutoTradeCreateStrategyRequest, AutoTradeGetStrategiesRequest, AutoTradeControlStrategyRequest,
    AutoTradeBacktestRequest, AutoTradeGetBacktestRequest, AutoTradeGetExecutionsRequest,
    AutoTradeGetRecommendationsRequest, AutoTradeGetPerformanceRequest, AutoTradeCopyStrategyRequest
)

class AutoTradeProtocol:
    def __init__(self):
        self.on_autotrade_create_strategy_req_callback = None
        self.on_autotrade_get_strategies_req_callback = None
        self.on_autotrade_control_strategy_req_callback = None
        self.on_autotrade_backtest_req_callback = None
        self.on_autotrade_get_backtest_req_callback = None
        self.on_autotrade_get_executions_req_callback = None
        self.on_autotrade_get_recommendations_req_callback = None
        self.on_autotrade_get_performance_req_callback = None
        self.on_autotrade_copy_strategy_req_callback = None

    async def autotrade_create_strategy_req_controller(self, session, msg: bytes, length: int):
        request = AutoTradeCreateStrategyRequest.model_validate_json(msg)
        if self.on_autotrade_create_strategy_req_callback:
            return await self.on_autotrade_create_strategy_req_callback(session, request)
        raise NotImplementedError('on_autotrade_create_strategy_req_callback is not set')

    async def autotrade_get_strategies_req_controller(self, session, msg: bytes, length: int):
        request = AutoTradeGetStrategiesRequest.model_validate_json(msg)
        if self.on_autotrade_get_strategies_req_callback:
            return await self.on_autotrade_get_strategies_req_callback(session, request)
        raise NotImplementedError('on_autotrade_get_strategies_req_callback is not set')

    async def autotrade_control_strategy_req_controller(self, session, msg: bytes, length: int):
        request = AutoTradeControlStrategyRequest.model_validate_json(msg)
        if self.on_autotrade_control_strategy_req_callback:
            return await self.on_autotrade_control_strategy_req_callback(session, request)
        raise NotImplementedError('on_autotrade_control_strategy_req_callback is not set')

    async def autotrade_backtest_req_controller(self, session, msg: bytes, length: int):
        request = AutoTradeBacktestRequest.model_validate_json(msg)
        if self.on_autotrade_backtest_req_callback:
            return await self.on_autotrade_backtest_req_callback(session, request)
        raise NotImplementedError('on_autotrade_backtest_req_callback is not set')

    async def autotrade_get_backtest_req_controller(self, session, msg: bytes, length: int):
        request = AutoTradeGetBacktestRequest.model_validate_json(msg)
        if self.on_autotrade_get_backtest_req_callback:
            return await self.on_autotrade_get_backtest_req_callback(session, request)
        raise NotImplementedError('on_autotrade_get_backtest_req_callback is not set')

    async def autotrade_get_executions_req_controller(self, session, msg: bytes, length: int):
        request = AutoTradeGetExecutionsRequest.model_validate_json(msg)
        if self.on_autotrade_get_executions_req_callback:
            return await self.on_autotrade_get_executions_req_callback(session, request)
        raise NotImplementedError('on_autotrade_get_executions_req_callback is not set')

    async def autotrade_get_recommendations_req_controller(self, session, msg: bytes, length: int):
        request = AutoTradeGetRecommendationsRequest.model_validate_json(msg)
        if self.on_autotrade_get_recommendations_req_callback:
            return await self.on_autotrade_get_recommendations_req_callback(session, request)
        raise NotImplementedError('on_autotrade_get_recommendations_req_callback is not set')

    async def autotrade_get_performance_req_controller(self, session, msg: bytes, length: int):
        request = AutoTradeGetPerformanceRequest.model_validate_json(msg)
        if self.on_autotrade_get_performance_req_callback:
            return await self.on_autotrade_get_performance_req_callback(session, request)
        raise NotImplementedError('on_autotrade_get_performance_req_callback is not set')

    async def autotrade_copy_strategy_req_controller(self, session, msg: bytes, length: int):
        request = AutoTradeCopyStrategyRequest.model_validate_json(msg)
        if self.on_autotrade_copy_strategy_req_callback:
            return await self.on_autotrade_copy_strategy_req_callback(session, request)
        raise NotImplementedError('on_autotrade_copy_strategy_req_callback is not set')