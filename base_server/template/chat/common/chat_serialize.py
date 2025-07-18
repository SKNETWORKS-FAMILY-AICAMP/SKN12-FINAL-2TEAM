from typing import Optional, List
from service.net.protocol_base import BaseRequest, BaseResponse
from .chat_model import ChatRoom, ChatMessage

# ============================================================================
# AI 채팅 기본 기능 (REQ-CHAT-001~005)
# ============================================================================

class ChatRoomListRequest(BaseRequest):
    """채팅방 목록 요청"""
    page: int = 1
    limit: int = 20

class ChatRoomListResponse(BaseResponse):
    """채팅방 목록 응답"""
    rooms: List[ChatRoom] = []
    total_count: int = 0

class ChatRoomCreateRequest(BaseRequest):
    """새 채팅방 생성 요청"""
    ai_persona: str
    title: Optional[str] = ""

class ChatRoomCreateResponse(BaseResponse):
    """새 채팅방 생성 응답"""
    room: Optional[ChatRoom] = None

class ChatMessageSendRequest(BaseRequest):
    """채팅 메시지 전송 요청"""
    room_id: str
    content: str
    persona: str 

class ChatMessageSendResponse(BaseResponse):
    """채팅 메시지 전송 응답"""
    message: Optional[ChatMessage] = None

class ChatMessageListRequest(BaseRequest):
    """채팅 메시지 목록 요청"""
    room_id: str
    page: int = 1
    limit: int = 50
    before_timestamp: Optional[str] = ""

class ChatMessageListResponse(BaseResponse):
    """채팅 메시지 목록 응답"""
    messages: List[ChatMessage] = []
    has_more: bool = False

class ChatRoomDeleteRequest(BaseRequest):
    """채팅방 삭제 요청"""
    room_id: str

class ChatRoomDeleteResponse(BaseResponse):
    """채팅방 삭제 응답"""
    message: str = ""
