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
class ChatTemplateImpl(BaseTemplate):
    def __init__(self, llm_config=None):
        super().__init__()
        # 서비스 컨테이너에 미리 등록된 AIChatService 인스턴스를 가져옵니다.
        self.ai_service: AIChatService = ServiceContainer.get_ai_chat_service()

    # 채팅방 목록 조회
    async def on_chat_room_list_req(self, client_session, request: ChatRoomListRequest):
        response = ChatRoomListResponse()
        Logger.info(f"Chat room list request: page={request.page}")
        try:
            rows, meta = await ServiceContainer.get_database_service().call_shard_procedure(
                client_session.session.shard_id, "fp_get_chat_rooms",
                (client_session.session.account_db_key, request.page, request.limit)
            )
            # rows: List[dict], meta: dict
            response.rooms = [
                ChatRoom(
                    room_id=str(r["room_id"]),
                    title=r["title"],
                    ai_persona=r["ai_persona"],
                    created_at=str(r["created_at"]),
                    last_message_at=str(r["last_message_at"]),
                    message_count=r["message_count"]
                ) for r in rows
            ]
            response.total_count = meta.get("total_count", len(response.rooms))
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
            result = await ServiceContainer.get_database_service().call_shard_procedure(
                client_session.session.shard_id, "fp_create_chat_room",
                (client_session.session.account_db_key, request.ai_persona, request.title)
            )
            if not result or result[0].get("result") != "SUCCESS":
                response.errorCode = 6002
                return response

            room_id = result[0]["room_id"]
            response.room = ChatRoom(
                room_id=str(room_id),
                title=request.title,
                ai_persona=request.ai_persona,
                created_at=str(datetime.now()),
                last_message_at=str(datetime.now()),
                message_count=1
            )
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

    # 채팅 메시지 목록 조회
    async def on_chat_message_list_req(self, client_session, request: ChatMessageListRequest):
        response = ChatMessageListResponse()
        Logger.info(f"Chat message list: room_id={request.room_id}")
        try:
            rows = await ServiceContainer.get_database_service().call_shard_procedure(
                client_session.session.shard_id, "fp_get_chat_messages",
                (client_session.session.account_db_key,
                 request.room_id, request.page, request.limit, None)
            )
            response.messages = [
                ChatMessage(
                    message_id=str(m["message_id"]),
                    room_id=str(m["room_id"]),
                    sender_type=m["sender_type"],
                    content=m["content"],
                    metadata=m.get("metadata"),
                    timestamp=str(m["timestamp"]),
                    is_streaming=False
                ) for m in rows
            ]
            response.has_more = len(response.messages) >= request.limit
            response.errorCode = 0
        except Exception as e:
            Logger.error(f"Chat message list error: {e}")
            response.messages = []
            response.has_more = False
            response.errorCode = 1000
        return response

    # 채팅방 삭제
    async def on_chat_room_delete_req(self, client_session, request: ChatRoomDeleteRequest):
        response = ChatRoomDeleteResponse()
        Logger.info(f"Chat room delete: room_id={request.room_id}")
        try:
            result = await ServiceContainer.get_database_service().call_shard_procedure(
                client_session.session.shard_id, "fp_delete_chat_room",
                (request.room_id, client_session.session.account_db_key)
            )
            if not result or result[0].get("result") != "SUCCESS":
                response.errorCode = 6004
                response.message = "삭제 실패"
                return response

            response.errorCode = 0
            response.message   = "삭제 성공"
        except Exception as e:
            Logger.error(f"Chat room delete error: {e}")
            response.errorCode = 1000
            response.message   = "삭제 오류"
        return response
