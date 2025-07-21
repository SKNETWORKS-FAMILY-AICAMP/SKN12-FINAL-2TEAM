from pydantic import BaseModel
from typing import Optional, Dict, Any

class ChatRoom(BaseModel):
    """채팅방 정보"""
    room_id: str = ""
    title: str = ""
    ai_persona: str = "GPT4O"
    created_at: str = ""
    last_message_at: str = ""
    message_count: int = 0

class ChatMessage(BaseModel):
    """채팅 메시지"""
    message_id: str = ""
    room_id: str = ""
    sender_type: str = ""
    content: str = ""
    metadata: Optional[Dict[str, Any]] = None
    timestamp: str = ""
    is_streaming: bool = False