from fastapi import APIRouter, Request
from template.base.template_context import TemplateContext, TemplateType
from template.base.template_service import TemplateService
from template.chat.common.chat_serialize import (
    ChatRoomListRequest, ChatRoomCreateRequest, ChatMessageSendRequest,
    ChatMessageListRequest, ChatSummaryRequest, ChatAnalysisRequest,
    ChatPersonaListRequest, ChatRoomDeleteRequest
)
from template.chat.common.chat_protocol import ChatProtocol

router = APIRouter()

chat_protocol = ChatProtocol()

def setup_chat_protocol_callbacks():
    """Chat protocol 콜백 설정 (main.py에서 한 번만 호출됨)"""
    chat_template = TemplateContext.get_template(TemplateType.CHAT)
    chat_protocol.on_chat_room_list_req_callback = getattr(chat_template, "on_chat_room_list_req", None)
    chat_protocol.on_chat_room_create_req_callback = getattr(chat_template, "on_chat_room_create_req", None)
    chat_protocol.on_chat_message_send_req_callback = getattr(chat_template, "on_chat_message_send_req", None)
    chat_protocol.on_chat_message_list_req_callback = getattr(chat_template, "on_chat_message_list_req", None)
    chat_protocol.on_chat_summary_req_callback = getattr(chat_template, "on_chat_summary_req", None)
    chat_protocol.on_chat_analysis_req_callback = getattr(chat_template, "on_chat_analysis_req", None)
    chat_protocol.on_chat_persona_list_req_callback = getattr(chat_template, "on_chat_persona_list_req", None)
    chat_protocol.on_chat_room_delete_req_callback = getattr(chat_template, "on_chat_room_delete_req", None)

@router.post("/rooms")
async def chat_room_list(request: ChatRoomListRequest, req: Request):
    """채팅방 목록 조회"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host if req.client else "unknown"
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        chat_protocol.chat_room_list_req_controller
    )

@router.post("/room/create")
async def chat_room_create(request: ChatRoomCreateRequest, req: Request):
    """새 채팅방 생성"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host if req.client else "unknown"
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        chat_protocol.chat_room_create_req_controller
    )

@router.post("/message/send")
async def chat_message_send(request: ChatMessageSendRequest, req: Request):
    """메시지 전송"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host if req.client else "unknown"
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        chat_protocol.chat_message_send_req_controller
    )

@router.post("/messages")
async def chat_message_list(request: ChatMessageListRequest, req: Request):
    """채팅 메시지 목록"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host if req.client else "unknown"
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        chat_protocol.chat_message_list_req_controller
    )

@router.post("/summary")
async def chat_summary(request: ChatSummaryRequest, req: Request):
    """채팅 요약"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host if req.client else "unknown"
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        chat_protocol.chat_summary_req_controller
    )

@router.post("/analysis")
async def chat_analysis(request: ChatAnalysisRequest, req: Request):
    """종목 분석"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host if req.client else "unknown"
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        chat_protocol.chat_analysis_req_controller
    )

@router.post("/personas")
async def chat_persona_list(request: ChatPersonaListRequest, req: Request):
    """AI 페르소나 목록"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host if req.client else "unknown"
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        chat_protocol.chat_persona_list_req_controller
    )

@router.post("/room/delete")
async def chat_room_delete(request: ChatRoomDeleteRequest, req: Request):
    """채팅방 삭제"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host if req.client else "unknown"
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        chat_protocol.chat_room_delete_req_controller
    )