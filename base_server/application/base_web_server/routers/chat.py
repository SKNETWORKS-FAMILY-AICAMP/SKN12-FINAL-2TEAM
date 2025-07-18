# application/base_web_server/routers/chat.py

from fastapi import APIRouter, Request
from template.base.template_context import TemplateContext, TemplateType
from template.base.template_service import TemplateService
from template.chat.common.chat_serialize import (
    ChatRoomListRequest, ChatRoomCreateRequest,
    ChatMessageSendRequest, ChatMessageListRequest,
    ChatRoomDeleteRequest
)
from template.chat.common.chat_protocol import ChatProtocol

router = APIRouter()
chat_protocol = ChatProtocol()

def setup_chat_protocol_callbacks():
    t = TemplateContext.get_template(TemplateType.CHAT)
    chat_protocol.on_chat_room_list_req_callback   = getattr(t, "on_chat_room_list_req", None)
    chat_protocol.on_chat_room_create_req_callback = getattr(t, "on_chat_room_create_req", None)
    chat_protocol.on_chat_message_send_req_callback = getattr(t, "on_chat_message_send_req", None)
    chat_protocol.on_chat_message_list_req_callback = getattr(t, "on_chat_message_list_req", None)
    chat_protocol.on_chat_room_delete_req_callback = getattr(t, "on_chat_room_delete_req", None)

@router.post("/rooms")
async def chat_room_list(request: ChatRoomListRequest, req: Request):
    ip = req.headers.get("X-Forwarded-For", req.client.host if req.client else "unknown").split(",")[0]
    return await TemplateService.run_user(
        req.method, req.url.path, ip,
        request.model_dump_json(),
        chat_protocol.chat_room_list_req_controller
    )

@router.post("/room/create")
async def chat_room_create(request: ChatRoomCreateRequest, req: Request):
    ip = req.headers.get("X-Forwarded-For", req.client.host if req.client else "unknown").split(",")[0]
    return await TemplateService.run_user(
        req.method, req.url.path, ip,
        request.model_dump_json(),
        chat_protocol.chat_room_create_req_controller
    )

@router.post("/message/send")
async def chat_message_send(request: ChatMessageSendRequest, req: Request):
    ip = req.headers.get("X-Forwarded-For", req.client.host if req.client else "unknown").split(",")[0]
    return await TemplateService.run_user(
        req.method, req.url.path, ip,
        request.model_dump_json(),
        chat_protocol.chat_message_send_req_controller
    )

@router.post("/messages")
async def chat_message_list(request: ChatMessageListRequest, req: Request):
    ip = req.headers.get("X-Forwarded-For", req.client.host if req.client else "unknown").split(",")[0]
    return await TemplateService.run_user(
        req.method, req.url.path, ip,
        request.model_dump_json(),
        chat_protocol.chat_message_list_req_controller
    )

@router.post("/room/delete")
async def chat_room_delete(request: ChatRoomDeleteRequest, req: Request):
    ip = req.headers.get("X-Forwarded-For", req.client.host if req.client else "unknown").split(",")[0]
    return await TemplateService.run_user(
        req.method, req.url.path, ip,
        request.model_dump_json(),
        chat_protocol.chat_room_delete_req_controller
    )
