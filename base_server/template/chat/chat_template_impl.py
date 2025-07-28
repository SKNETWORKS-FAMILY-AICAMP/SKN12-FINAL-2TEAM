from template.base.base_template import BaseTemplate
from template.chat.common.chat_serialize import (
    ChatRoomListRequest, ChatRoomListResponse,
    ChatRoomCreateRequest, ChatRoomCreateResponse,
    ChatMessageSendRequest, ChatMessageSendResponse,
    ChatMessageListRequest, ChatMessageListResponse,
    ChatRoomDeleteRequest, ChatRoomDeleteResponse,
    ChatRoomUpdateRequest, ChatRoomUpdateResponse,
    ChatMessageDeleteRequest, ChatMessageDeleteResponse
)
from template.chat.common.chat_model import ChatRoom, ChatMessage
from service.core.logger import Logger
from service.service_container import ServiceContainer
from datetime import datetime
from service.llm.AIChat_service import AIChatService
import uuid
import json
import asyncio
import redis.asyncio as redis  # 비동기 Redis 클라이언트
from service.cache.cache_service import CacheService
from service.queue.queue_service import QueueService, get_queue_service
from service.queue.message_queue import QueueMessage, MessagePriority

# State Machine 추가
from template.chat.chat_state_machine import get_chat_state_machine, MessageState, RoomState

class ChatTemplateImpl(BaseTemplate):
    def __init__(self, llm_config=None):
        super().__init__()
        # 서비스 컨테이너에 미리 등록된 AIChatService 인스턴스를 가져옵니다.
        self.ai_service: AIChatService = ServiceContainer.get_ai_chat_service()

    # 챗봇 세션 목록 조회 (Redis + MySQL 하이브리드)
    async def on_chat_room_list_req(self, client_session, request):
        response = ChatRoomListResponse()
        try:
            account_db_key = getattr(client_session.session, 'account_db_key', 0)
            shard_id = getattr(client_session.session, 'shard_id', 1)
            user_key = f"rooms:{client_session.session.account_id}"
            rooms = []
            
            # 1단계: Redis에서 챗봇 세션 목록 조회 시도
            redis_success = False
            try:
                async with CacheService.get_client() as redis:
                    room_ids = await redis._client.smembers(redis._get_key(user_key))
                    if room_ids:  # Redis에 데이터가 있으면
                        for room_id in room_ids:
                            room_key = f"room:{room_id}"
                            raw = await redis.get_string(room_key)
                            if raw:
                                room_data = json.loads(raw)
                                rooms.append(ChatRoom(**room_data))
                        redis_success = True
                        Logger.debug(f"Redis에서 챗봇 세션 목록 조회 성공: {len(rooms)}개")
            except Exception as redis_e:
                Logger.warn(f"Redis 챗봇 세션 목록 조회 실패: {redis_e}")
            
            # 2단계: Redis 실패 또는 비어있을 때 DB에서 조회
            if not redis_success or not rooms:
                try:
                    database_service = ServiceContainer.get_database_service()
                    db_result = await database_service.call_shard_procedure(
                        shard_id,
                        'fp_chat_rooms_get',
                        (account_db_key,)
                    )
                    
                    if db_result:
                        # DB 데이터를 Redis 형식으로 변환 (챗봇 세션 정보)
                        db_rooms = []
                        for row in db_result:
                            room_data = {
                                "room_id": str(row.get('room_id', '')),
                                "title": str(row.get('title', '')),  # 챗봇 세션 제목
                                "ai_persona": str(row.get('ai_persona', '')),  # 챗봇 페르소나
                                "created_at": row.get('created_at').isoformat() if row.get('created_at') else '',
                                "last_message_at": row.get('last_message_at').isoformat() if row.get('last_message_at') else '',
                                "message_count": str(row.get('message_count', 0))
                            }
                            db_rooms.append(room_data)
                            rooms.append(ChatRoom(**room_data))
                        
                        Logger.info(f"DB에서 챗봇 세션 목록 조회 성공: {len(rooms)}개 (Redis 캐시 미스)")
                        
                        # 3단계: DB 데이터를 Redis에 캐시링 (비동기)
                        if db_rooms:
                            try:
                                await self._cache_chatbot_sessions_to_redis(client_session.session.account_id, db_rooms)
                                Logger.debug(f"챗봇 세션 목록 Redis 캐싱 완료: {len(db_rooms)}개")
                            except Exception as cache_e:
                                Logger.warn(f"Redis 캐싱 실패 (서비스는 정상 작동): {cache_e}")
                        
                except Exception as db_e:
                    Logger.error(f"DB 챗봇 세션 목록 조회 실패: {db_e}")
            
            response.rooms = rooms
            response.total_count = len(rooms)
            response.errorCode = 0
            
        except Exception as e:
            Logger.error(f"Chatbot session list error: {e}")
            response.errorCode = 1000
            response.rooms = []
            response.total_count = 0
        return response

    async def _cache_chatbot_sessions_to_redis(self, account_id: str, db_rooms: list):
        """DB에서 조회한 챗봇 세션 목록을 Redis에 캐싱"""
        try:
            user_key = f"rooms:{account_id}"
            
            async with CacheService.get_client() as redis:
                # 기존 세션 목록 삭제
                await redis.delete(user_key)
                
                # 각 세션을 Redis에 저장
                for room_data in db_rooms:
                    room_id = room_data["room_id"]
                    room_key = f"room:{room_id}"
                    
                    # 세션 상세 정보 저장 (JSON 형태)
                    await redis.set_string(room_key, json.dumps(room_data), expire=3600)  # 1시간 TTL
                    
                    # 사용자별 세션 목록에 추가
                    await redis.set_add(user_key, room_id)
                
                # 사용자별 세션 목록에 TTL 설정
                await redis._client.expire(redis._get_key(user_key), 3600)  # 1시간 TTL
                
        except Exception as e:
            Logger.error(f"Redis 캐싱 중 오류: {e}")
            raise

    async def _cache_chatbot_messages_to_redis(self, room_id: str, db_messages: list):
        """DB에서 조회한 챗봇 메시지 목록을 Redis에 캐싱"""
        try:
            msg_key = f"messages:{room_id}"
            
            async with CacheService.get_client() as redis:
                # 기존 메시지 목록 삭제
                await redis.delete(msg_key)
                
                # 메시지들을 Redis List에 의식의 흐름 순서로 저장
                if db_messages:
                    # DB에서 이미 시간순(ASC)으로 정렬되어 있으므로 그대로 사용
                    # push_right로 순서대로 추가하여 [첫메시지, 중간메시지, 최신메시지] 순서 유지
                    for message_data in db_messages:
                        await redis.list_push_right(msg_key, json.dumps(message_data))
                    
                    # TTL 설정 (1시간)
                    await redis.set_expire(msg_key, 3600)
                
        except Exception as e:
            Logger.error(f"Redis 메시지 캐싱 중 오류: {e}")
            raise

    # 새 채팅방 생성
    async def on_chat_room_create_req(self, client_session, request: ChatRoomCreateRequest):
        response = ChatRoomCreateResponse()
        Logger.info(f"Chat room create request: persona={request.ai_persona}")
        try:
            # 1. 방 ID 생성
            room_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            account_db_key = getattr(client_session.session, 'account_db_key', 0)
            shard_id = getattr(client_session.session, 'shard_id', 1)  # 세션에서 샤드 ID 가져오기

            # 1.5. State Machine으로 방 상태 초기화 (CREATING 상태로 시작)
            state_machine = get_chat_state_machine()
            await state_machine.transition_room(room_id, RoomState.CREATING)

            # 2. 방 정보 dict 생성
            room_data = {
                "room_id": str(room_id),
                "title": str(request.title or "New Chat"),
                "ai_persona": str(request.ai_persona or "GPT4O"),
                "created_at": str(now),
                "last_message_at": str(now),
                "message_count": str(0)  # 초기 메시지 카운트는 0
            }
            room_key = f"room:{room_id}"
            Logger.info(f"Creating chat room: {room_data}")

            # 3. Redis에 방 정보 저장 (해시 or JSON)
            async with CacheService.get_client() as redis:
                await redis.set_string(room_key, json.dumps(room_data))

            # 4. 유저별 방 목록에 추가
            user_key = f"rooms:{client_session.session.account_id}"
            async with CacheService.get_client() as redis:
                await redis.set_add(user_key, room_id)

            # 4.5. Redis 저장 완료 후 CREATING → PENDING 전이 (메시지 패턴과 동일)
            await state_machine.transition_room(room_id, RoomState.PENDING, RoomState.CREATING)

            # 5. MessageQueue로 DB 저장 이벤트 발행 (비동기 처리)
            if ServiceContainer.is_queue_service_initialized():
                try:
                    queue_service = get_queue_service()
                    message = QueueMessage(
                        id=str(uuid.uuid4()),
                        queue_name="chat_persistence",
                        message_type="CHAT_ROOM_CREATE",
                        payload={
                            "room_id": room_id,
                            "account_db_key": account_db_key,
                            "shard_id": shard_id,  # 매핑 테이블에서 조회된 샤드 ID
                            "title": request.title or "New Chat",
                            "ai_persona": request.ai_persona or "GPT4O",
                            "created_at": now
                        },
                        partition_key=room_id,  # 채팅방별 순서 보장
                        priority=MessagePriority.NORMAL
                    )
                    await queue_service.send_message("chat_persistence", message.payload, message.message_type, message.priority)
                    Logger.info(f"채팅방 생성 이벤트 큐에 발행: room_id={room_id}")
                except Exception as queue_error:
                    Logger.error(f"MessageQueue 발행 실패 (채팅방 생성): {queue_error}")
                    # 큐 실패해도 Redis는 성공했으므로 계속 진행

            # 6. 응답 객체 생성
            response.room = ChatRoom(**room_data)
            response.errorCode = 0
        except Exception as e:
            Logger.error(f"Chat room create error: {e}")
            # 예외 발생 시 실제 생성된 리소스 정리
            try:
                # Redis에 저장된 데이터 정리 (실제 의미 있는 cleanup)
                room_key = f"room:{room_id}"
                user_key = f"rooms:{client_session.session.account_id}"
                async with CacheService.get_client() as redis:
                    await redis.delete(room_key)
                    await redis.set_remove(user_key, room_id)
                Logger.info(f"방 생성 실패로 Redis 데이터 정리 완료: {room_id}")
            except Exception as cleanup_error:
                Logger.warn(f"방 생성 실패 후 Redis 정리 중 오류: {cleanup_error}")
            response.errorCode = 1000
        return response

    # 채팅 메시지 전송 → DB에 저장 + AIChatService.chat 으로 답변 생성
    async def on_chat_message_send_req(self, client_session, request: ChatMessageSendRequest):
        from template.chat.common.chat_model import ChatMessage
        from datetime import datetime

        response = ChatMessageSendResponse()
        account_db_key = getattr(client_session.session, 'account_db_key', 0)
        shard_id = getattr(client_session.session, 'shard_id', 1)  # 세션에서 샤드 ID 가져오기
        
        try:
            # 1) 채팅방 상태 확인 (ACTIVE 상태인지 검증)
            state_machine = get_chat_state_machine()
            room_state = await state_machine.get_room_state(request.room_id)
            
            if room_state != RoomState.ACTIVE:
                Logger.warn(f"메시지 전송 실패: 채팅방이 활성 상태가 아님 (room_id={request.room_id}, state={room_state})")
                response.errorCode = 1001
                response.message = "채팅방이 활성 상태가 아닙니다"
                return response
            
            # 2) 사용자 메시지 ID 생성
            user_message_id = f"msg_{uuid.uuid4().hex}"
            user_timestamp = datetime.utcnow().isoformat()
            
            # 3) State Machine으로 메시지 상태 초기화 (COMPOSING 상태로 시작)
            await state_machine.transition_message(user_message_id, MessageState.COMPOSING)
            
            # 3) Redis 메모리에 사용자 메시지 기록
            ai_service: AIChatService = ServiceContainer.get_ai_chat_service()
            session_id = request.room_id
            ai_service.mem(session_id).chat_memory.add_user_message(request.content)

            # 3) 사용자 메시지를 MessageQueue로 발행 (DB 저장용)
            if ServiceContainer.is_queue_service_initialized():
                try:
                    queue_service = get_queue_service()
                    user_message = QueueMessage(
                        id=str(uuid.uuid4()),
                        queue_name="chat_persistence",
                        message_type="CHAT_MESSAGE_SAVE",
                        payload={
                            "message_id": user_message_id,
                            "room_id": request.room_id,
                            "account_db_key": account_db_key,
                            "shard_id": shard_id,  # 매핑 테이블에서 조회된 샤드 ID
                            "message_type": "USER",
                            "content": request.content,
                            "metadata": json.dumps({
                                "client_type": getattr(request, 'client_type', 'web'),
                                "ip": getattr(client_session, 'client_ip', ''),
                                "sequence": int(datetime.now().timestamp() * 1000000)  # 마이크로초 시퀀스
                            }),
                            "created_at": user_timestamp
                        },
                        partition_key=request.room_id,  # 채팅방별 순서 보장
                        priority=MessagePriority.HIGH  # 채팅 메시지는 높은 우선순위
                    )
                    await queue_service.send_message("chat_persistence", user_message.payload, user_message.message_type, user_message.priority)
                    Logger.info(f"사용자 메시지 큐에 발행: message_id={user_message_id}")
                    
                    # 3.5) MessageQueue 발행 완료 후 COMPOSING → PENDING 전이
                    await state_machine.transition_message(user_message_id, MessageState.PENDING, MessageState.COMPOSING)
                    
                except Exception as queue_error:
                    Logger.error(f"MessageQueue 발행 실패 (사용자 메시지): {queue_error}")

            # 4) AI 메시지 ID 생성 (LLM 호출 전 미리 생성)
            ai_message_id = f"msg_{uuid.uuid4().hex}"
            ai_timestamp = datetime.utcnow().isoformat()
            
            # 5) AI 메시지 상태 초기화 (COMPOSING 상태로 시작)
            await state_machine.transition_message(ai_message_id, MessageState.COMPOSING)
            
            # 6) LLM에 질문 보내고 답변 받기
            try:
                result = await ai_service.chat(request.content, session_id=session_id)
                reply_text = result["reply"]
            except Exception as llm_error:
                # LLM 호출 실패 시 AI 메시지 상태를 DELETED로 전이
                await state_machine.transition_message(ai_message_id, MessageState.DELETED, MessageState.PENDING)
                Logger.error(f"LLM 호출 실패: {llm_error}")
                raise

            # 7) Redis 메모리에 AI 답변 기록
            ai_service.mem(session_id).chat_memory.add_ai_message(reply_text)

            # 7) AI 응답을 MessageQueue로 발행 (DB 저장용)
            if ServiceContainer.is_queue_service_initialized():
                try:
                    queue_service = get_queue_service()
                    ai_message = QueueMessage(
                        id=str(uuid.uuid4()),
                        queue_name="chat_persistence",
                        message_type="CHAT_MESSAGE_SAVE",
                        payload={
                            "message_id": ai_message_id,
                            "room_id": request.room_id,
                            "account_db_key": account_db_key,
                            "shard_id": shard_id,  # 매핑 테이블에서 조회된 샤드 ID
                            "message_type": "AI",
                            "content": reply_text,
                            "metadata": json.dumps({
                                "model": result.get("model", "unknown"),
                                "tokens": result.get("tokens", {}),
                                "parent_message_id": user_message_id,
                                "sequence": int(datetime.now().timestamp() * 1000000)  # 마이크로초 시퀀스
                            }),
                            "parent_message_id": user_message_id,
                            "created_at": ai_timestamp
                        },
                        partition_key=request.room_id,  # 채팅방별 순서 보장
                        priority=MessagePriority.HIGH
                    )
                    await queue_service.send_message("chat_persistence", ai_message.payload, ai_message.message_type, ai_message.priority)
                    Logger.info(f"AI 응답 메시지 큐에 발행: message_id={ai_message_id}")
                    
                    # 7.5) MessageQueue 발행 완료 후 COMPOSING → PENDING 전이
                    await state_machine.transition_message(ai_message_id, MessageState.PENDING, MessageState.COMPOSING)
                    
                except Exception as queue_error:
                    Logger.error(f"MessageQueue 발행 실패 (AI 응답): {queue_error}")

            # 8) Redis에 메시지 실시간 캐싱 (사용자 + AI 메시지)
            try:
                msg_key = f"messages:{request.room_id}"
                
                # 사용자 메시지 데이터
                user_msg_data = {
                    "message_id": user_message_id,
                    "room_id": request.room_id,
                    "sender_type": "USER",
                    "content": request.content,
                    "timestamp": user_timestamp,
                    "metadata": {
                        "client_type": getattr(request, 'client_type', 'web'),
                        "ip": getattr(client_session, 'client_ip', ''),
                        "sequence": int(datetime.now().timestamp() * 1000000)
                    },
                    "is_streaming": False
                }
                
                # AI 응답 메시지 데이터
                ai_msg_data = {
                    "message_id": ai_message_id,
                    "room_id": request.room_id,
                    "sender_type": "AI",
                    "content": reply_text,
                    "timestamp": ai_timestamp,
                    "metadata": {
                        "model": result.get("model", "unknown"),
                        "tokens": result.get("tokens", {}),
                        "parent_message_id": user_message_id
                    },
                    "is_streaming": False
                }
                
                # Redis에 시간 순서대로 추가 (의식의 흐름 순서 유지)
                async with CacheService.get_client() as redis:
                    # 1. 사용자 메시지 먼저 (시간적으로 먼저) - 리스트 끝에 추가
                    await redis.list_push_right(msg_key, json.dumps(user_msg_data))
                    # 2. AI 응답 메시지 (시간적으로 나중) - 리스트 끝에 추가
                    await redis.list_push_right(msg_key, json.dumps(ai_msg_data))
                    await redis.set_expire(msg_key, 3600)  # 1시간 TTL
                
                Logger.debug(f"메시지 Redis 실시간 캐싱 완료: {request.room_id}")
                
            except Exception as cache_error:
                Logger.warn(f"Redis 실시간 캐싱 실패 (서비스는 정상 작동): {cache_error}")

            # 9) 클라이언트에게 ChatMessage 형태로 돌려주기
            response.message = ChatMessage(
                message_id=ai_message_id,
                room_id=request.room_id,
                sender_type="AI",
                content=reply_text,
                timestamp=ai_timestamp,
                metadata=None,
                is_streaming=False
            )
            response.errorCode = 0
            
        except Exception as e:
            Logger.error(f"Chat message send error: {e}")
            response.errorCode = 1000
            response.message = None
            
        return response

    # 챗봇 메시지 목록 조회 (Redis + MySQL 하이브리드)
    async def on_chat_message_list_req(self, client_session, request: ChatMessageListRequest):
        response = ChatMessageListResponse()
        Logger.info(f"Chatbot message list: room_id={request.room_id}")
        try:
            account_db_key = getattr(client_session.session, 'account_db_key', 0)
            shard_id = getattr(client_session.session, 'shard_id', 1)
            msg_key = f"messages:{request.room_id}"
            messages = []
            
            # 1단계: Redis에서 메시지 목록 조회 시도
            redis_success = False
            try:
                async with CacheService.get_client() as redis:
                    # Redis List에서 페이징 처리 (기존 list_range 사용)
                    start_idx = getattr(request, 'offset', 0)
                    end_idx = start_idx + getattr(request, 'limit', 50) - 1
                    messages_raw = await redis.list_range(msg_key, start_idx, end_idx)
                    
                    if messages_raw:  # Redis에 데이터가 있으면
                        messages_data = [json.loads(m) for m in messages_raw]
                        # Redis에서 온 데이터도 metadata 타입 검증
                        for msg_data in messages_data:
                            if 'metadata' in msg_data and isinstance(msg_data['metadata'], str):
                                try:
                                    msg_data['metadata'] = json.loads(msg_data['metadata'])
                                except json.JSONDecodeError:
                                    msg_data['metadata'] = {}
                        messages = [ChatMessage(**m) for m in messages_data]
                        redis_success = True
                        Logger.debug(f"Redis에서 챗봇 메시지 조회 성공: {len(messages)}개")
            except Exception as redis_e:
                Logger.warn(f"Redis 챗봇 메시지 조회 실패: {redis_e}")
            
            # 2단계: Redis 실패 또는 비어있을 때 DB에서 조회
            if not redis_success or not messages:
                try:
                    database_service = ServiceContainer.get_database_service()
                    # page를 offset으로 변환
                    page = getattr(request, 'page', 1)
                    limit = getattr(request, 'limit', 50)
                    offset = (page - 1) * limit
                    
                    db_result = await database_service.call_shard_procedure(
                        shard_id,
                        'fp_chat_messages_get',
                        (request.room_id, account_db_key, limit, offset)
                    )
                    
                    if db_result:
                        # DB 데이터를 ChatMessage 형식으로 변환
                        db_messages = []
                        for row in db_result:
                            # metadata JSON 문자열을 딕셔너리로 변환
                            metadata_raw = row.get('metadata', {})
                            if isinstance(metadata_raw, str):
                                try:
                                    metadata = json.loads(metadata_raw)
                                except json.JSONDecodeError:
                                    metadata = {}
                            else:
                                metadata = metadata_raw if metadata_raw else {}
                            
                            message_data = {
                                "message_id": str(row.get('message_id', '')),
                                "room_id": str(row.get('room_id', '')),
                                "sender_type": str(row.get('message_type', 'USER')),
                                "content": str(row.get('content', '')),
                                "timestamp": row.get('created_at').isoformat() if row.get('created_at') else '',
                                "metadata": metadata,
                                "is_streaming": False
                            }
                            db_messages.append(message_data)
                            messages.append(ChatMessage(**message_data))
                        
                        Logger.info(f"DB에서 챗봇 메시지 조회 성공: {len(messages)}개 (Redis 캐시 미스)")
                        
                        # 3단계: DB 데이터를 Redis에 캐시링 (비동기)
                        if db_messages:
                            try:
                                await self._cache_chatbot_messages_to_redis(request.room_id, db_messages)
                                Logger.debug(f"챗봇 메시지 목록 Redis 캐싱 완료: {len(db_messages)}개")
                            except Exception as cache_e:
                                Logger.warn(f"Redis 메시지 캐싱 실패 (서비스는 정상 작동): {cache_e}")
                        
                except Exception as db_e:
                    Logger.error(f"DB 챗봇 메시지 조회 실패: {db_e}")
            
            # DB에서 이미 시간순(ASC)으로 조회되므로 그대로 전달
            response.messages = messages
            response.has_more = len(messages) >= getattr(request, 'limit', 50)
            response.errorCode = 0
            
        except Exception as e:
            Logger.error(f"Chatbot message list error: {e}")
            response.messages = []
            response.has_more = False
            response.errorCode = 1000
        return response

    # 채팅방 삭제 (Redis + MessageQueue)
    async def on_chat_room_delete_req(self, client_session, request: ChatRoomDeleteRequest):
        response = ChatRoomDeleteResponse()
        Logger.info(f"Chat room delete: room_id={request.room_id}")
        try:
            account_db_key = getattr(client_session.session, 'account_db_key', 0)
            shard_id = getattr(client_session.session, 'shard_id', 1)
            
            # 0.5. State Machine으로 방 상태를 DELETING으로 전이
            state_machine = get_chat_state_machine()
            await state_machine.transition_room(request.room_id, RoomState.DELETING, RoomState.ACTIVE)
            
            # 1. 즉시 Redis에서 삭제 (사용자 경험 우선)
            user_key = f"rooms:{client_session.session.account_id}"
            room_key = f"room:{request.room_id}"
            msg_key = f"messages:{request.room_id}"
            
            async with CacheService.get_client() as redis:
                # 사용자별 방 목록에서 제거
                await redis.set_remove(user_key, request.room_id)
                # 방 정보 삭제
                await redis.delete(room_key)
                # 메시지 캐시 삭제
                await redis.delete(msg_key)
            
            # 1.5. Redis 삭제 성공 시 DELETED 상태로 전이
            await state_machine.transition_room(request.room_id, RoomState.DELETED, RoomState.DELETING)
            
            # 2. MessageQueue로 DB Soft Delete 이벤트 발행 (비동기 처리)
            if ServiceContainer.is_queue_service_initialized():
                try:
                    queue_service = get_queue_service()
                    message = QueueMessage(
                        id=str(uuid.uuid4()),
                        queue_name="chat_persistence",
                        message_type="CHAT_ROOM_DELETE",
                        payload={
                            "room_id": request.room_id,
                            "account_db_key": account_db_key,
                            "shard_id": shard_id
                        },
                        partition_key=request.room_id,  # 채팅방별 순서 보장
                        priority=MessagePriority.HIGH
                    )
                    await queue_service.send_message("chat_persistence", message.payload, message.message_type, message.priority)
                    Logger.info(f"채팅방 삭제 이벤트 큐에 발행: room_id={request.room_id}")
                except Exception as queue_error:
                    Logger.error(f"MessageQueue 발행 실패 (채팅방 삭제): {queue_error}")
                    # 큐 실패해도 Redis는 성공했으므로 계속 진행
            
            response.errorCode = 0
            response.message = "채팅방이 삭제되었습니다"
        except Exception as e:
            Logger.error(f"Chat room delete error: {e}")
            # 예외 발생해도 삭제 시도했으므로 DELETED 상태로 전이
            try:
                state_machine = get_chat_state_machine()
                await state_machine.transition_room(request.room_id, RoomState.DELETED, RoomState.DELETING)
            except:
                pass  # State Machine 오류는 무시
            response.errorCode = 1000
            response.message = "삭제 처리 중 오류가 발생했습니다"
        return response

    # 채팅방 제목 변경 (신규 기능)
    async def on_chat_room_update_req(self, client_session, request: ChatRoomUpdateRequest):
        response = ChatRoomUpdateResponse()
        Logger.info(f"Chat room update title: room_id={request.room_id}, new_title={request.new_title}")
        try:
            account_db_key = getattr(client_session.session, 'account_db_key', 0)
            shard_id = getattr(client_session.session, 'shard_id', 1)
            
            # 1. 즉시 Redis 캐시 업데이트 (사용자 경험 우선)
            room_key = f"room:{request.room_id}"
            async with CacheService.get_client() as redis:
                # 기존 방 정보 조회
                room_data_raw = await redis.get_string(room_key)
                if room_data_raw:
                    room_data = json.loads(room_data_raw)
                    room_data["title"] = request.new_title
                    # 업데이트된 정보로 캐시 갱신
                    await redis.set_string(room_key, json.dumps(room_data), expire=3600)
                    Logger.info(f"Redis 캐시 제목 업데이트 완료: {request.new_title}")
            
            # 2. MessageQueue로 DB 업데이트 이벤트 발행 (비동기 처리)
            if ServiceContainer.is_queue_service_initialized():
                try:
                    queue_service = get_queue_service()
                    message = QueueMessage(
                        id=str(uuid.uuid4()),
                        queue_name="chat_persistence",
                        message_type="CHAT_ROOM_UPDATE",
                        payload={
                            "room_id": request.room_id,
                            "account_db_key": account_db_key,
                            "shard_id": shard_id,
                            "new_title": request.new_title
                        },
                        partition_key=request.room_id,  # 채팅방별 순서 보장
                        priority=MessagePriority.NORMAL
                    )
                    await queue_service.send_message("chat_persistence", message.payload, message.message_type, message.priority)
                    Logger.info(f"채팅방 제목 변경 이벤트 큐에 발행: room_id={request.room_id}")
                except Exception as queue_error:
                    Logger.error(f"MessageQueue 발행 실패 (채팅방 제목 변경): {queue_error}")
                    # 큐 실패해도 Redis는 성공했으므로 계속 진행
            
            response.errorCode = 0
            response.message = "채팅방 제목이 변경되었습니다"
            response.new_title = request.new_title
        except Exception as e:
            Logger.error(f"Chat room update error: {e}")
            response.errorCode = 1000
            response.message = "제목 변경 중 오류가 발생했습니다"
        return response

    # 개별 메시지 삭제 (신규 기능) - State Machine 지능형 삭제 적용
    async def on_chat_message_delete_req(self, client_session, request: ChatMessageDeleteRequest):
        response = ChatMessageDeleteResponse()
        Logger.info(f"Chat message delete: message_id={request.message_id}, room_id={request.room_id}")
        try:
            account_db_key = getattr(client_session.session, 'account_db_key', 0)
            shard_id = getattr(client_session.session, 'shard_id', 1)
            
            # 1. State Machine으로 지능형 삭제 처리
            state_machine = get_chat_state_machine()
            delete_success, delete_message = await state_machine.smart_delete_message(request.message_id)
            
            if not delete_success:
                response.errorCode = 1001
                response.message = f"삭제 실패: {delete_message}"
                return response
            
            # 2. 즉시 Redis 메시지 캐시 무효화 (사용자 경험 우선)
            msg_key = f"messages:{request.room_id}"
            async with CacheService.get_client() as redis:
                # 메시지 목록 캐시 삭제 (다음 조회 시 DB에서 재로딩)
                await redis.delete(msg_key)
                Logger.info(f"Redis 메시지 캐시 무효화 완료: room_id={request.room_id}")
            
            # 3. MessageQueue로 DB Soft Delete 이벤트 발행 (상태에 따라 처리)
            if ServiceContainer.is_queue_service_initialized():
                try:
                    # DELETING 상태인 경우에만 DB 삭제 이벤트 발행
                    current_state = await state_machine.get_message_state(request.message_id)
                    if current_state == MessageState.DELETING:
                        queue_service = get_queue_service()
                        message = QueueMessage(
                            id=str(uuid.uuid4()),
                            queue_name="chat_persistence",
                            message_type="CHAT_MESSAGE_DELETE",
                            payload={
                                "message_id": request.message_id,
                                "room_id": request.room_id,
                                "account_db_key": account_db_key,
                                "shard_id": shard_id
                            },
                            partition_key=request.room_id,  # 채팅방별 순서 보장
                            priority=MessagePriority.HIGH
                        )
                        await queue_service.send_message("chat_persistence", message.payload, message.message_type, message.priority)
                        Logger.info(f"메시지 삭제 이벤트 큐에 발행: message_id={request.message_id}")
                    else:
                        Logger.info(f"메시지 상태가 {current_state}이므로 DB 삭제 이벤트 발행 건너뜀: {request.message_id}")
                except Exception as queue_error:
                    Logger.error(f"MessageQueue 발행 실패 (메시지 삭제): {queue_error}")
                    # 큐 실패해도 State Machine은 성공했으므로 계속 진행
            
            response.errorCode = 0
            response.message = delete_message  # State Machine에서 반환한 상세 메시지
        except Exception as e:
            Logger.error(f"Chat message delete error: {e}")
            response.errorCode = 1000
            response.message = "메시지 삭제 중 오류가 발생했습니다"
        return response
