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

class ChatTemplateImpl(BaseTemplate):
    def __init__(self, llm_config=None):
        super().__init__()
        # AIChatService 인스턴스를 컨테이너에서 가져옵니다.
        self.ai_service: AIChatService = ServiceContainer.get_ai_chat_service()
    # 채팅방 목록 조회 처리 함수
    async def on_chat_room_list_req(self, client_session, request: ChatRoomListRequest):
        response = ChatRoomListResponse()
        Logger.info(f"Chat room list request: page={request.page}")
        try:
            # DB 호출: 사용자 채팅방 목록 조회
            rooms_result = await ServiceContainer.get_database_service().call_shard_procedure(
                client_session.session.shard_id, "fp_get_chat_rooms",
                (client_session.session.account_db_key, request.page, request.limit)
            )
            # 결과 매핑
            rooms = rooms_result[0] if isinstance(rooms_result[0], list) else rooms_result
            response.rooms = [
                ChatRoom(
                    room_id=str(r.get('room_id') or ""),
                    title=r.get('title', ""),
                    ai_persona=r.get('ai_persona', ""),
                    created_at=str(r.get('created_at', datetime.now())),
                    last_message_at=str(r.get('last_message_at', datetime.now())),
                    message_count=r.get('message_count', 0)
                ) for r in rooms if isinstance(r, dict)
            ]
            # 총 개수 설정
            response.total_count = (
                rooms_result[1].get('total_count')
                if len(rooms_result) > 1 else len(response.rooms)
            )
            response.errorCode = 0
        except Exception as e:
            response.errorCode = 1000
            response.rooms = []
            response.total_count = 0
            Logger.error(f"Chat room list error: {e}")
        return response

    # 새로운 채팅방 생성 처리 함수
    async def on_chat_room_create_req(self, client_session, request: ChatRoomCreateRequest):
        response = ChatRoomCreateResponse()
        Logger.info(f"Chat room create request: persona={request.ai_persona}")
        try:
            # DB 호출: 채팅방 생성
            result = await ServiceContainer.get_database_service().call_shard_procedure(
                client_session.session.shard_id, "fp_create_chat_room",
                (client_session.session.account_db_key, request.ai_persona, request.title)
            )
            # 생성 실패 체크
            if not result or result[0].get('result') != 'SUCCESS':
                response.errorCode = 6002
                return response
            # 응답 생성: 생성된 채팅방 정보
            room_id = result[0].get('room_id')
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
            response.errorCode = 1000
            Logger.error(f"Chat room create error: {e}")
        return response

    # 채팅 메시지 전송 처리 함수
    async def on_chat_message_send_req(self, client_session, request: ChatMessageSendRequest):
        response = ChatMessageSendResponse()
        Logger.info(f"Chat message send request: room_id={request.room_id}")
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            db_service = ServiceContainer.get_database_service()

            # 1. 사용자 메시지 DB 저장
            user_msg_result = await db_service.call_shard_procedure(
                shard_id, "fp_send_chat_message",
                (account_db_key, request.room_id, request.content, False, [])
            )
            if not user_msg_result or user_msg_result[0].get('result') != 'SUCCESS':
                response.errorCode = 6003
                return response
            user_msg_id = user_msg_result[0].get('message_id')
            # 응답 객체에 사용자 메시지 설정
            response.message = ChatMessage(
                message_id=str(user_msg_id),
                room_id=request.room_id,
                sender_type="USER",
                content=request.content,
                timestamp=str(datetime.now()),
                is_streaming=False
            )

            # 2. AIChatService.chat 호출하여 AI 답변 생성
            ai_result = await self.ai_service.chat(request.content, session_id=client_session.session.session_id)
            ai_reply = ai_result.get('reply', '')

            # 3. AI 메시지 DB 저장
            ai_msg_result = await db_service.call_shard_procedure(
                shard_id, "fp_save_ai_message",
                (account_db_key, request.room_id, ai_reply, user_msg_id)
            )
            ai_msg_id = ai_msg_result[0].get('ai_message_id') if ai_msg_result else None

            # 4. 응답 객체에 AI 메시지 설정
            response.ai_response = ChatMessage(
                message_id=str(ai_msg_id),
                room_id=request.room_id,
                sender_type="AI",
                content=ai_reply,
                timestamp=str(datetime.now()),
                is_streaming=False
            )

            response.errorCode = 0
        except Exception as e:
            response.errorCode = 1000
            Logger.error(f"Chat message send error: {e}")
        return response

    # 채팅 메시지 목록 조회 처리 함수
    async def on_chat_message_list_req(self, client_session, request: ChatMessageListRequest):
        response = ChatMessageListResponse()
        Logger.info(f"Chat message list: room_id={request.room_id}")
        try:
            # DB 호출: 메시지 목록 조회
            result = await ServiceContainer.get_database_service().call_shard_procedure(
                client_session.session.shard_id, "fp_get_chat_messages",
                (
                    client_session.session.account_db_key,
                    request.room_id,
                    request.page,
                    request.limit,
                    None
                )
            )
            # 결과 매핑: ChatMessage 모델 리스트 생성
            response.messages = [
                ChatMessage(
                    message_id=str(m.get('message_id') or ""),
                    room_id=str(m.get('room_id') or ""),
                    sender_type=m.get('sender_type', ""),
                    content=m.get('content', ""),
                    metadata=m.get('metadata'),
                    timestamp=str(m.get('timestamp', datetime.now())),
                    is_streaming=False
                ) for m in (result or []) if isinstance(m, dict)
            ]
            response.has_more = len(response.messages) >= request.limit
            response.errorCode = 0
        except Exception as e:
            response.errorCode = 1000
            response.messages = []
            response.has_more = False
            Logger.error(f"Chat message list error: {e}")
        return response

    # 채팅방 삭제 처리 함수
    async def on_chat_room_delete_req(self, client_session, request: ChatRoomDeleteRequest):
        response = ChatRoomDeleteResponse()
        Logger.info(f"Chat room delete: room_id={request.room_id}")
        try:
            # DB 호출: 채팅방 삭제
            result = await ServiceContainer.get_database_service().call_shard_procedure(
                client_session.session.shard_id, "fp_delete_chat_room",
                (request.room_id, client_session.session.account_db_key)
            )
            if not result or result[0].get('result') != 'SUCCESS':
                response.errorCode = 6004
                response.message = "삭제 실패"
                return response
            response.message = "삭제 성공"
            response.errorCode = 0
        except Exception as e:
            response.errorCode = 1000
            response.message = "삭제 오류"
            Logger.error(f"Chat room delete error: {e}")
        return response
