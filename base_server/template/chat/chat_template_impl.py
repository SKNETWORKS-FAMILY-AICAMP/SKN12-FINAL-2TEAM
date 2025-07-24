from template.base.base_template import BaseTemplate
from template.chat.common.chat_serialize import (
    ChatRoomListRequest, ChatRoomListResponse,
    ChatRoomCreateRequest, ChatRoomCreateResponse,
    ChatMessageSendRequest, ChatMessageSendResponse,
    ChatMessageListRequest, ChatMessageListResponse,
    ChatRoomDeleteRequest, ChatRoomDeleteResponse
)
from template.chat.common.chat_model import ChatRoom, ChatMessage
from service.core.logger import Logger
from service.service_container import ServiceContainer
from datetime import datetime
from service.llm.AIChat_service import AIChatService
import uuid
import json
import redis.asyncio as redis  # 비동기 Redis 클라이언트

class ChatTemplateImpl(BaseTemplate):
    def __init__(self, llm_config=None):
        super().__init__()
        # 서비스 컨테이너에 미리 등록된 AIChatService 인스턴스를 가져옵니다.
        self.redis = redis.from_url("redis://localhost:6379")  # decode_responses 빼고
        self.ai_service: AIChatService = ServiceContainer.get_ai_chat_service()

    # 채팅방 목록 조회 (Redis)
    async def on_chat_room_list_req(self, client_session, request: ChatRoomListRequest):
        response = ChatRoomListResponse()
        Logger.info(f"Chat room list request: page={request.page}")
        try:
            user_key = f"rooms:{client_session.session.account_id}"
            room_ids = await self.redis.smembers(user_key)
            rooms = []
            for room_id in room_ids:
                room_key = f"room:{room_id}"
                room_data = await self.redis.hgetall(room_key)
                if room_data:
                    rooms.append(ChatRoom(**room_data))
            response.rooms = rooms
            response.total_count = len(rooms)
            response.errorCode = 0
        except Exception as e:
            Logger.error(f"Chat room list error: {e}")
            response.errorCode = 1000
            response.rooms = []
            response.total_count = 0
        return response

    # 새 채팅방 생성
    async def on_chat_room_create_req(self, client_session, request: ChatRoomCreateRequest):
        response = ChatRoomCreateResponse()
        Logger.info(f"Chat room create request: persona={request.ai_persona}")
        try:
            # 1. 방 ID 생성
            room_id = str(uuid.uuid4())
            now = datetime.now().isoformat()

            # 2. 방 정보 dict 생성
            room_data = {
                "room_id": str(room_id),
                "title": str(request.title or ""),
                "ai_persona": str(request.ai_persona or ""),
                "created_at": str(now),
                "last_message_at": str(now),
                "message_count": str(1)
            }
            room_key = f"room:{room_id}"
            Logger.info(f"Creating chat room: {room_data}")
            # 3. Redis에 방 정보 저장 (해시 or JSON)
            await self.redis.hset(room_key, mapping=room_data)

            # 4. 유저별 방 목록에 추가
            user_key = f"rooms:{client_session.session.account_id}"
            await self.redis.sadd(user_key, room_id)

            # 5. 응답 객체 생성
            response.room = ChatRoom(**room_data)
            response.errorCode = 0
        except Exception as e:
            Logger.error(f"Chat room create error: {e}")
            response.errorCode = 1000
        return response

    # 채팅 메시지 전송 → DB에 저장 + AIChatService.chat 으로 답변 생성
    async def on_chat_message_send_req(self, client_session, request: ChatMessageSendRequest):
        from template.chat.common.chat_model import ChatMessage
        from datetime import datetime

        response = ChatMessageSendResponse()
        # 1) Redis 메모리에 사용자 메시지 기록
        ai_service: AIChatService = ServiceContainer.get_ai_chat_service()
        # session_id 로 방 ID 사용
        session_id = request.room_id
        # add user message into redis-backed memory 
        ai_service.mem(session_id).chat_memory.add_user_message(request.content)

        # 2) LLM 에 질문 보내고 답변 받기
        result = await ai_service.chat(request.content, session_id=session_id)
        # result 는 {"session_id": ..., "reply": "..."}
        reply_text = result["reply"]

        # 3) Redis 메모리에 AI 답변 기록
        ai_service.mem(session_id).chat_memory.add_ai_message(reply_text)

        # 4) 클라이언트에게 ChatMessage 형태로 돌려주기
        response.message = ChatMessage(
            message_id=f"msg_{uuid.uuid4().hex}",  # 필요에 따라 ID 생성
            room_id=session_id,
            sender_type="AI",
            content=reply_text,
            timestamp=datetime.utcnow().isoformat(),
            metadata=None,
            is_streaming=False
        )
        response.errorCode = 0
        return response

    # 채팅 메시지 목록 조회 (Redis)
    async def on_chat_message_list_req(self, client_session, request: ChatMessageListRequest):
        response = ChatMessageListResponse()
        Logger.info(f"Chat message list: room_id={request.room_id}")
        try:
            msg_key = f"messages:{request.room_id}"
            messages_raw = await self.redis.lrange(msg_key, 0, -1)
            messages = [json.loads(m) for m in messages_raw]
            response.messages = [ChatMessage(**m) for m in messages]
            response.has_more = len(response.messages) >= request.limit
            response.errorCode = 0
        except Exception as e:
            Logger.error(f"Chat message list error: {e}")
            response.messages = []
            response.has_more = False
            response.errorCode = 1000
        return response

    # 채팅방 삭제 (Redis)
    async def on_chat_room_delete_req(self, client_session, request: ChatRoomDeleteRequest):
        response = ChatRoomDeleteResponse()
        Logger.info(f"Chat room delete: room_id={request.room_id}")
        try:
            user_key = f"rooms:{client_session.session.account_id}"
            room_key = f"room:{request.room_id}"
            await self.redis.srem(user_key, request.room_id)
            await self.redis.delete(room_key)
            response.errorCode = 0
            response.message = "삭제 성공"
        except Exception as e:
            Logger.error(f"Chat room delete error: {e}")
            response.errorCode = 1000
            response.message = "삭제 오류"
        return response
