from fastapi import APIRouter, Request
from template.base.template_context import TemplateContext, TemplateType
from template.base.template_service import TemplateService
from template.autotrade.common.autotrade_protocol import AutoTradeProtocol
from template.autotrade.common.autotrade_serialize import (
    AutoTradeYahooSearchRequest,
    AutoTradeYahooDetailRequest,
    SignalAlarmCreateRequest,
    SignalAlarmListRequest,
    SignalAlarmToggleRequest,
    SignalAlarmDeleteRequest,
    SignalHistoryRequest
)

router = APIRouter()

autotrade_protocol = AutoTradeProtocol()

def setup_autotrade_protocol_callbacks():
    """AutoTrade protocol 콜백 설정 (main.py에서 한 번만 호출됨)"""
    autotrade_template = TemplateContext.get_template(TemplateType.AUTOTRADE)
    autotrade_protocol.on_autotrade_yahoo_search_req_callback = getattr(autotrade_template, "on_autotrade_yahoo_search_req", None)
    autotrade_protocol.on_autotrade_yahoo_detail_req_callback = getattr(autotrade_template, "on_autotrade_yahoo_detail_req", None)
    
    # 시그널 알림 콜백 설정
    autotrade_protocol.on_signal_alarm_create_req_callback = getattr(autotrade_template, "on_signal_alarm_create_req", None)
    autotrade_protocol.on_signal_alarm_list_req_callback = getattr(autotrade_template, "on_signal_alarm_list_req", None)
    autotrade_protocol.on_signal_alarm_toggle_req_callback = getattr(autotrade_template, "on_signal_alarm_toggle_req", None)
    autotrade_protocol.on_signal_alarm_delete_req_callback = getattr(autotrade_template, "on_signal_alarm_delete_req", None)
    autotrade_protocol.on_signal_history_req_callback = getattr(autotrade_template, "on_signal_history_req", None)

@router.post("/yahoo/search")
async def yahoo_search(request: AutoTradeYahooSearchRequest, req: Request):
    """야후 파이낸스 주식 검색"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    
    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        autotrade_protocol.autotrade_yahoo_search_req_controller
    )

@router.post("/yahoo/detail")
async def yahoo_detail(request: AutoTradeYahooDetailRequest, req: Request):
    """야후 파이낸스 주식 상세 정보"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    
    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        autotrade_protocol.autotrade_yahoo_detail_req_controller
    )

@router.post("/signal/alarm/create")
async def signal_alarm_create(request: SignalAlarmCreateRequest, req: Request):
    """시그널 알림 등록"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    
    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        autotrade_protocol.signal_alarm_create_req_controller
    )

@router.post("/signal/alarm/list")
async def signal_alarm_list(request: SignalAlarmListRequest, req: Request):
    """시그널 알림 목록 조회"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    
    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        autotrade_protocol.signal_alarm_list_req_controller
    )

@router.post("/signal/alarm/toggle")
async def signal_alarm_toggle(request: SignalAlarmToggleRequest, req: Request):
    """시그널 알림 ON/OFF 토글"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    
    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        autotrade_protocol.signal_alarm_toggle_req_controller
    )

@router.post("/signal/alarm/delete")
async def signal_alarm_delete(request: SignalAlarmDeleteRequest, req: Request):
    """시그널 알림 삭제"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    
    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        autotrade_protocol.signal_alarm_delete_req_controller
    )

@router.post("/signal/history")
async def signal_history(request: SignalHistoryRequest, req: Request):
    """시그널 히스토리 조회"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    
    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        autotrade_protocol.signal_history_req_controller
    )