# application/base_web_server/routers/chat.py

from fastapi import APIRouter, Request
from template.base.template_context import TemplateContext, TemplateType
from template.base.template_service import TemplateService
from template.chat.common.chat_serialize import (
    ChatRoomListRequest, ChatRoomCreateRequest,
    ChatMessageSendRequest, ChatMessageListRequest,
    ChatRoomDeleteRequest, ChatRoomUpdateRequest, 
    ChatMessageDeleteRequest
)
from template.chat.common.chat_protocol import ChatProtocol
from service.websocket.websocket_service import WebSocketService
from datetime import datetime

router = APIRouter()
chat_protocol = ChatProtocol()

def setup_chat_protocol_callbacks():
    t = TemplateContext.get_template(TemplateType.CHAT)
    chat_protocol.on_chat_room_list_req_callback   = getattr(t, "on_chat_room_list_req", None)
    chat_protocol.on_chat_room_create_req_callback = getattr(t, "on_chat_room_create_req", None)
    chat_protocol.on_chat_message_send_req_callback = getattr(t, "on_chat_message_send_req", None)
    chat_protocol.on_chat_message_list_req_callback = getattr(t, "on_chat_message_list_req", None)
    chat_protocol.on_chat_room_delete_req_callback = getattr(t, "on_chat_room_delete_req", None)
    chat_protocol.on_chat_room_update_req_callback = getattr(t, "on_chat_room_update_req", None)
    chat_protocol.on_chat_message_delete_req_callback = getattr(t, "on_chat_message_delete_req", None)

async def broadcast_chat_update(message_type: str, data: dict):
    """WebSocket을 통해 채팅 관련 업데이트를 모든 클라이언트에게 브로드캐스트"""
    try:
        if WebSocketService.is_initialized():
            await WebSocketService.broadcast_message({
                "type": message_type,
                "timestamp": datetime.now().isoformat(),
                **data
            })
            print(f"[WebSocket] 브로드캐스트 전송: {message_type}")
        else:
            print(f"[WebSocket] WebSocket 서비스가 초기화되지 않음")
    except Exception as e:
        print(f"[WebSocket] 브로드캐스트 실패: {e}")

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
    
    # 채팅방 생성 요청 처리
    result = await TemplateService.run_user(
        req.method, req.url.path, ip,
        request.model_dump_json(),
        chat_protocol.chat_room_create_req_controller
    )
    
    # 성공적으로 생성된 경우 WebSocket으로 알림 전송
    try:
        if result and hasattr(result, 'get') and result.get('errorCode') == 0:
            await broadcast_chat_update('chat_room_created', {
                'room': result.get('room', {})
            })
    except Exception as e:
        print(f"[WebSocket] 채팅방 생성 알림 전송 실패: {e}")
    
    return result

@router.post("/message/send")
async def chat_message_send(request: ChatMessageSendRequest, req: Request):
    ip = req.headers.get("X-Forwarded-For", req.client.host if req.client else "unknown").split(",")[0]
    
    # 요청 데이터 로깅 추가
    print(f"[DEBUG] Chat message send request data: {request.model_dump()}")
    print(f"[DEBUG] Request headers: {dict(req.headers)}")
    
    # 메시지 전송 요청 처리
    result = await TemplateService.run_user(
        req.method, req.url.path, ip,
        request.model_dump_json(),
        chat_protocol.chat_message_send_req_controller
    )
    
    # 성공적으로 전송된 경우 WebSocket으로 알림 전송
    try:
        if result and hasattr(result, 'get') and result.get('errorCode') == 0:
            message_data = result.get('message', {})
            await broadcast_chat_update('chat_message', {
                'room_id': request.room_id,
                'message_id': message_data.get('message_id'),
                'content': message_data.get('content'),
                'role': 'assistant',
                'timestamp': message_data.get('timestamp')
            })
    except Exception as e:
        print(f"[WebSocket] 메시지 전송 알림 전송 실패: {e}")
    
    return result

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
    
    # 채팅방 삭제 요청 처리
    result = await TemplateService.run_user(
        req.method, req.url.path, ip,
        request.model_dump_json(),
        chat_protocol.chat_room_delete_req_controller
    )
    
    # 성공적으로 삭제된 경우 WebSocket으로 알림 전송
    try:
        if result and hasattr(result, 'get') and result.get('errorCode') == 0:
            await broadcast_chat_update('chat_room_deleted', {
                'room_id': request.room_id
            })
    except Exception as e:
        print(f"[WebSocket] 채팅방 삭제 알림 전송 실패: {e}")
    
    return result

@router.post("/room/update")
async def chat_room_update(request: ChatRoomUpdateRequest, req: Request):
    ip = req.headers.get("X-Forwarded-For", req.client.host if req.client else "unknown").split(",")[0]
    
    # 채팅방 업데이트 요청 처리
    result = await TemplateService.run_user(
        req.method, req.url.path, ip,
        request.model_dump_json(),
        chat_protocol.chat_room_update_req_controller
    )
    
    # 성공적으로 업데이트된 경우 WebSocket으로 알림 전송
    try:
        if result and hasattr(result, 'get') and result.get('errorCode') == 0:
            await broadcast_chat_update('chat_room_updated', {
                'room': result.get('room', {})
            })
    except Exception as e:
        print(f"[WebSocket] 채팅방 업데이트 알림 전송 실패: {e}")
    
    return result

@router.post("/message/delete")
async def chat_message_delete(request: ChatMessageDeleteRequest, req: Request):
    ip = req.headers.get("X-Forwarded-For", req.client.host if req.client else "unknown").split(",")[0]
    return await TemplateService.run_user(
        req.method, req.url.path, ip,
        request.model_dump_json(),
        chat_protocol.chat_message_delete_req_controller
    )
