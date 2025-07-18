from .chat_serialize import (
    ChatRoomListRequest, ChatRoomCreateRequest,
    ChatMessageSendRequest, ChatMessageListRequest,
    ChatRoomDeleteRequest
)
from typing import Callable, Awaitable, Optional

class ChatProtocol:
    def __init__(self):
        # 사용하지 않는 콜백 제거: 필요한 콜백만 정의
        self.on_chat_room_list_req_callback: Optional[Callable[..., Awaitable]] = None
        self.on_chat_room_create_req_callback: Optional[Callable[..., Awaitable]] = None
        self.on_chat_message_send_req_callback: Optional[Callable[..., Awaitable]] = None
        self.on_chat_message_list_req_callback: Optional[Callable[..., Awaitable]] = None
        self.on_chat_room_delete_req_callback: Optional[Callable[..., Awaitable]] = None

    async def chat_room_list_req_controller(self, session, msg: bytes, length: int):
        request = ChatRoomListRequest.model_validate_json(msg)
        if self.on_chat_room_list_req_callback:
            return await self.on_chat_room_list_req_callback(session, request)
        raise NotImplementedError('on_chat_room_list_req_callback is not set')

    async def chat_room_create_req_controller(self, session, msg: bytes, length: int):
        request = ChatRoomCreateRequest.model_validate_json(msg)
        if self.on_chat_room_create_req_callback:
            return await self.on_chat_room_create_req_callback(session, request)
        raise NotImplementedError('on_chat_room_create_req_callback is not set')

    async def chat_message_send_req_controller(self, session, msg: bytes, length: int):
        request = ChatMessageSendRequest.model_validate_json(msg)
        if self.on_chat_message_send_req_callback:
            persona = request.persona  # 여기가 페르소나 추출 지점
            return await self.on_chat_message_send_req_callback(session, request)
        raise NotImplementedError('on_chat_message_send_req_callback is not set')

    async def chat_message_list_req_controller(self, session, msg: bytes, length: int):
        request = ChatMessageListRequest.model_validate_json(msg)
        if self.on_chat_message_list_req_callback:
            return await self.on_chat_message_list_req_callback(session, request)
        raise NotImplementedError('on_chat_message_list_req_callback is not set')

    async def chat_room_delete_req_controller(self, session, msg: bytes, length: int):
        request = ChatRoomDeleteRequest.model_validate_json(msg)
        if self.on_chat_room_delete_req_callback:
            return await self.on_chat_room_delete_req_callback(session, request)
        raise NotImplementedError('on_chat_room_delete_req_callback is not set')
