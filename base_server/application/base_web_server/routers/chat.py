from fastapi import APIRouter, Request
from template.base.template_context import TemplateContext, TemplateType
from template.base.template_service import TemplateService
from template.chat.common.chat_serialize import (
    ChatRoomListRequest, ChatRoomCreateRequest,
    ChatMessageSendRequest, ChatMessageListRequest,
    ChatRoomDeleteRequest
)
from template.chat.common.chat_protocol import ChatProtocol

# FastAPI 라우터 생성: 이 라우터에 채팅 관련 엔드포인트를 등록합니다.
router = APIRouter()

# ChatProtocol 인스턴스 생성: 요청을 처리할 각 컨트롤러를 담고 있는 프로토콜 객체
chat_protocol = ChatProtocol()

def setup_chat_protocol_callbacks():
    """ChatProtocol 콜백 설정 함수
    애플리케이션 시작 시 한 번 호출되어,
    TemplateContext의 CHAT 템플릿 메서드를 ChatProtocol에 연결합니다.
    """
    chat_template = TemplateContext.get_template(TemplateType.CHAT)
    chat_protocol.on_chat_room_list_req_callback   = getattr(chat_template, "on_chat_room_list_req", None)
    chat_protocol.on_chat_room_create_req_callback = getattr(chat_template, "on_chat_room_create_req", None)
    chat_protocol.on_chat_message_send_req_callback = getattr(chat_template, "on_chat_message_send_req", None)
    chat_protocol.on_chat_message_list_req_callback = getattr(chat_template, "on_chat_message_list_req", None)
    chat_protocol.on_chat_room_delete_req_callback = getattr(chat_template, "on_chat_room_delete_req", None)

# 엔드포인트 정의: Request 모델, 클라이언트 IP 추출, TemplateService 실행 순서

@router.post("/rooms")
async def chat_room_list(request: ChatRoomListRequest, req: Request):
    """채팅방 목록 조회 엔드포인트"""
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
    """새 채팅방 생성 엔드포인트"""
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
    """채팅 메시지 전송 엔드포인트"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host if req.client else "unknown"
    else:
        ip = ip.split(", ")[0]
    # request.persona 를 포함한 모든 필드가 model_dump_json()에 직렬화됩니다.
    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        chat_protocol.chat_message_send_req_controller
    )

@router.post("/messages")
async def chat_message_list(request: ChatMessageListRequest, req: Request):
    """채팅 메시지 목록 조회 엔드포인트"""
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

@router.post("/room/delete")
async def chat_room_delete(request: ChatRoomDeleteRequest, req: Request):
    """채팅방 삭제 엔드포인트"""
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
