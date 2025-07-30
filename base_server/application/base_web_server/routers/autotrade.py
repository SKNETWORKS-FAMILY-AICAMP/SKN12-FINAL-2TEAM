from fastapi import APIRouter, Request
from template.base.template_context import TemplateContext, TemplateType
from template.base.template_service import TemplateService
from template.autotrade.common.autotrade_serialize import (
    AutoTradeStrategyListRequest, AutoTradeStrategyCreateRequest, AutoTradeStrategyUpdateRequest,
    AutoTradeExecutionListRequest, AutoTradeBacktestRequest, AutoTradeAIStrategyRequest
)
from template.autotrade.common.autotrade_protocol import AutoTradeProtocol
import json

router = APIRouter()

autotrade_protocol = AutoTradeProtocol()

def setup_autotrade_protocol_callbacks():
    """AutoTrade protocol 콜백 설정 (main.py에서 한 번만 호출됨)"""
    autotrade_template = TemplateContext.get_template(TemplateType.AUTOTRADE)
    autotrade_protocol.on_autotrade_strategy_list_req_callback = getattr(autotrade_template, "on_autotrade_strategy_list_req", None)
    autotrade_protocol.on_autotrade_strategy_create_req_callback = getattr(autotrade_template, "on_autotrade_strategy_create_req", None)
    autotrade_protocol.on_autotrade_strategy_update_req_callback = getattr(autotrade_template, "on_autotrade_strategy_update_req", None)
    autotrade_protocol.on_autotrade_execution_list_req_callback = getattr(autotrade_template, "on_autotrade_execution_list_req", None)
    autotrade_protocol.on_autotrade_backtest_req_callback = getattr(autotrade_template, "on_autotrade_backtest_req", None)
    autotrade_protocol.on_autotrade_ai_strategy_req_callback = getattr(autotrade_template, "on_autotrade_ai_strategy_req", None)
    autotrade_protocol.autotrade_yahoo_search_req_controller = getattr(autotrade_template, "on_autotrade_yahoo_search_req", None)
    autotrade_protocol.autotrade_yahoo_detail_req_controller = getattr(autotrade_template, "on_autotrade_yahoo_detail_req", None)

# 유틸리티 함수들
async def decode_request_body(req: Request) -> dict:
    """요청 body 디코딩 및 JSON 파싱"""
    body = await req.body()
    if isinstance(body, bytes):
        body = body.decode("utf-8")
    return json.loads(body) if body else {}

def normalize_symbol(symbol: str) -> str:
    """symbol 정규화"""
    if isinstance(symbol, bytes):
        symbol = symbol.decode('utf-8')
    return str(symbol) if symbol else ""

def normalize_response(response) -> dict:
    """응답 정규화 (camelCase 변환)"""
    if hasattr(response, '__dict__'):
        response = response.__dict__
    if isinstance(response, dict) and 'error_code' in response:
        response['errorCode'] = response.pop('error_code')
    return response

@router.post("/strategy/list")
async def autotrade_strategy_list(request: AutoTradeStrategyListRequest, req: Request):
    """매매 전략 목록"""
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
        autotrade_protocol.autotrade_strategy_list_req_controller
    )

@router.post("/strategy/create")
async def autotrade_strategy_create(request: AutoTradeStrategyCreateRequest, req: Request):
    """매매 전략 생성"""
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
        autotrade_protocol.autotrade_strategy_create_req_controller
    )

@router.post("/strategy/update")
async def autotrade_strategy_update(request: AutoTradeStrategyUpdateRequest, req: Request):
    """매매 전략 수정"""
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
        autotrade_protocol.autotrade_strategy_update_req_controller
    )

@router.post("/backtest")
async def autotrade_backtest(request: AutoTradeBacktestRequest, req: Request):
    """백테스트 실행"""
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
        autotrade_protocol.autotrade_backtest_req_controller
    )

@router.post("/execution/list")
async def autotrade_execution_list(request: AutoTradeExecutionListRequest, req: Request):
    """거래 실행 내역 조회"""
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
        autotrade_protocol.autotrade_execution_list_req_controller
    )

@router.post("/ai-strategy")
async def autotrade_ai_strategy(request: AutoTradeAIStrategyRequest, req: Request):
    """AI 전략 생성"""
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
        autotrade_protocol.autotrade_ai_strategy_req_controller
    )

# 정리된 야후 엔드포인트들
@router.post("/yahoo/search")
async def yahoo_search(req: Request):
    """야후 파이낸스 주식 검색"""
    try:
        request_dict = await decode_request_body(req)
        
        # query 정규화
        if 'query' in request_dict:
            request_dict['query'] = normalize_symbol(request_dict['query'])
        
        client_session = await TemplateService.create_client_session(json.dumps(request_dict))
        response = await autotrade_protocol.autotrade_yahoo_search_req_controller(client_session, request_dict)
        
        return normalize_response(response)
    except Exception as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(content={"errorCode": -1, "message": str(e)})

@router.post("/yahoo/detail/{symbol}")
async def yahoo_detail(symbol: str, req: Request):
    """야후 파이낸스 주식 상세 정보"""
    try:
        request_dict = await decode_request_body(req)
        
        # symbol 정규화
        normalized_symbol = normalize_symbol(symbol)
        request_dict['symbol'] = normalized_symbol
        
        client_session = await TemplateService.create_client_session(json.dumps(request_dict))
        response = await autotrade_protocol.autotrade_yahoo_detail_req_controller(client_session, request_dict)
        
        return normalize_response(response)
    except Exception as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(content={"errorCode": -1, "message": str(e)})