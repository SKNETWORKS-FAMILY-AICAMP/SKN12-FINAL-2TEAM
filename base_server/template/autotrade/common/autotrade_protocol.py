from .autotrade_serialize import (
    AutoTradeYahooSearchRequest,
    AutoTradeYahooDetailRequest,
    SignalAlarmCreateRequest,
    SignalAlarmListRequest,
    SignalAlarmToggleRequest,
    SignalAlarmDeleteRequest,
    SignalHistoryRequest
)
from typing import Callable, Optional

class AutoTradeProtocol:
    def __init__(self):
        # Yahoo Finance 관련 콜백
        self.on_autotrade_yahoo_search_req_callback: Optional[Callable] = None
        self.on_autotrade_yahoo_detail_req_callback: Optional[Callable] = None
        
        # 시그널 알림 관련 콜백
        self.on_signal_alarm_create_req_callback: Optional[Callable] = None
        self.on_signal_alarm_list_req_callback: Optional[Callable] = None
        self.on_signal_alarm_toggle_req_callback: Optional[Callable] = None
        self.on_signal_alarm_delete_req_callback: Optional[Callable] = None
        self.on_signal_history_req_callback: Optional[Callable] = None

    async def autotrade_yahoo_search_req_controller(self, session, msg: bytes, length: int):
        """야후 파이낸스 검색 컨트롤러"""
        request = AutoTradeYahooSearchRequest.model_validate_json(msg)
        if self.on_autotrade_yahoo_search_req_callback:
            return await self.on_autotrade_yahoo_search_req_callback(session, request)
        raise NotImplementedError('on_autotrade_yahoo_search_req_callback is not set')

    async def autotrade_yahoo_detail_req_controller(self, session, msg: bytes, length: int):
        """야후 파이낸스 상세정보 컨트롤러"""
        request = AutoTradeYahooDetailRequest.model_validate_json(msg)
        if self.on_autotrade_yahoo_detail_req_callback:
            return await self.on_autotrade_yahoo_detail_req_callback(session, request)
        raise NotImplementedError('on_autotrade_yahoo_detail_req_callback is not set')

    async def signal_alarm_create_req_controller(self, session, msg: bytes, length: int):
        """시그널 알림 등록 컨트롤러"""
        request = SignalAlarmCreateRequest.model_validate_json(msg)
        if self.on_signal_alarm_create_req_callback:
            return await self.on_signal_alarm_create_req_callback(session, request)
        raise NotImplementedError('on_signal_alarm_create_req_callback is not set')

    async def signal_alarm_list_req_controller(self, session, msg: bytes, length: int):
        """시그널 알림 목록 조회 컨트롤러"""
        request = SignalAlarmListRequest.model_validate_json(msg)
        if self.on_signal_alarm_list_req_callback:
            return await self.on_signal_alarm_list_req_callback(session, request)
        raise NotImplementedError('on_signal_alarm_list_req_callback is not set')

    async def signal_alarm_toggle_req_controller(self, session, msg: bytes, length: int):
        """시그널 알림 ON/OFF 컨트롤러"""
        request = SignalAlarmToggleRequest.model_validate_json(msg)
        if self.on_signal_alarm_toggle_req_callback:
            return await self.on_signal_alarm_toggle_req_callback(session, request)
        raise NotImplementedError('on_signal_alarm_toggle_req_callback is not set')

    async def signal_alarm_delete_req_controller(self, session, msg: bytes, length: int):
        """시그널 알림 삭제 컨트롤러"""
        request = SignalAlarmDeleteRequest.model_validate_json(msg)
        if self.on_signal_alarm_delete_req_callback:
            return await self.on_signal_alarm_delete_req_callback(session, request)
        raise NotImplementedError('on_signal_alarm_delete_req_callback is not set')

    async def signal_history_req_controller(self, session, msg: bytes, length: int):
        """시그널 히스토리 조회 컨트롤러"""
        request = SignalHistoryRequest.model_validate_json(msg)
        if self.on_signal_history_req_callback:
            return await self.on_signal_history_req_callback(session, request)
        raise NotImplementedError('on_signal_history_req_callback is not set')