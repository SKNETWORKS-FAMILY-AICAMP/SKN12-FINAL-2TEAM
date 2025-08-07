# base_server/service/llm/AIChat_service.py

from service.core.logger import Logger
import os, uuid, asyncio, json
from fastapi import WebSocket, WebSocketDisconnect, HTTPException
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate

from service.service_container import ServiceContainer
from service.cache.cache_service import CacheService
from service.llm.AIChat.Router import AIChatRouter
from service.llm.llm_config import LlmConfig
from markdown import markdown
class AIChatService:
    """AI 채팅 서비스 - LLM 응답 생성에만 집중"""
    def __init__(self, llm_config: LlmConfig):
        self.llm_config = llm_config
        # llm 인스턴스는 llm_config에서 직접 생성
        from langchain_openai import ChatOpenAI
        api_key = os.getenv("OPENAI_API_KEY") or llm_config.providers[llm_config.default_provider].api_key
        self.llm = ChatOpenAI(model=llm_config.providers[llm_config.default_provider].model,
                              temperature=llm_config.providers[llm_config.default_provider].temperature,
                              openai_api_key=api_key)
        # 스트리밍용 LLM
        self.llm_stream = ChatOpenAI(model=llm_config.providers[llm_config.default_provider].model,
                                     temperature=llm_config.providers[llm_config.default_provider].temperature,
                                     streaming=True,
                                     openai_api_key=api_key)
        self._session_mem: dict[str, ConversationBufferMemory] = {}

        if not CacheService.is_initialized():
            raise RuntimeError("CacheService is not initialized. Please initialize CacheService first.")

        self.cache_service = CacheService.get_instance()
        # CacheService의 네임스페이스를 가져와서 사용
        cache_client = self.cache_service.get_client()
        # RedisChatMessageHistory의 key_prefix에 네임스페이스 포함
        # 주의: RedisChatMessageHistory는 key_prefix와 session_id를 조합하여 키를 생성
        # 실제 키: {key_prefix}{session_id}
        self.KEY_PREFIX = f"{cache_client.cache_key}:chat:"
        Logger.info(f"AIChatService initialized with key prefix: {self.KEY_PREFIX}")

    def mem(self, session_id: str) -> ConversationBufferMemory:
        """세션별 대화 메모리 관리 (Redis 기반)"""
        if session_id not in self._session_mem:
            cache_client = self.cache_service.get_client()
            redis_url = f"redis://{cache_client._host}:{cache_client._port}/{cache_client._db}"
            if cache_client._password:
                redis_url = f"redis://:{cache_client._password}@{cache_client._host}:{cache_client._port}/{cache_client._db}"
            
            # RedisChatMessageHistory는 key_prefix + session_id로 키를 생성
            # 예: finance_app:LOCAL:chat:room_123 형태로 저장됨
            history = RedisChatMessageHistory(
                session_id=session_id,
                url=redis_url,
                key_prefix=self.KEY_PREFIX,  # finance_app:LOCAL:chat:
            )
            
            # 디버깅을 위한 로그 추가
            Logger.debug(f"Creating RedisChatMessageHistory with key_prefix={self.KEY_PREFIX}, session_id={session_id}")
            Logger.debug(f"Expected Redis key pattern: {self.KEY_PREFIX}{session_id}")
            
            self._session_mem[session_id] = ConversationBufferMemory(
                chat_memory=history,
                return_messages=True
            )
        return self._session_mem[session_id]

    async def chat(self, message: str, session_id: str = "", client_session=None):
        """REST API용 채팅 응답 생성"""
        if not message.strip():
            raise HTTPException(400, "message empty")
        sid = session_id or str(uuid.uuid4())
        Logger.debug(f"AIChatService.chat called with session_id={sid}, message={message}")
        
        # 🆕 세션 정보를 포함한 라우터 생성
        Logger.debug(f"AIChatService.chat client_session: {client_session}")
        router = AIChatRouter(client_session)
        
        # 🆕 클로저로 안전하게 감싸기 (비동기 처리 안전성)
        def run_question_with_session():
            return router.run_question(message)
        
        # 비동기 실행으로 변경하여 도구 호출이 제대로 작동하도록 함
        loop = asyncio.get_event_loop()
        tool_out = await loop.run_in_executor(None, run_question_with_session)
        answer = await self._full_answer(sid, message, tool_out)
        Logger.debug(f"AIChatService.chat response for session_id={sid}: {answer}")
        return {"session_id": sid, "reply": answer}

    async def stream(self, ws: WebSocket):
        """WebSocket용 스트리밍 채팅 응답 생성"""
        await ws.accept()
        try:
            while True:
                data = await ws.receive_text()
                try:
                    req = json.loads(data)
                    q = req["message"].strip()
                    sid = req.get("session_id") or str(uuid.uuid4())
                except (KeyError, json.JSONDecodeError):
                    await ws.send_text(json.dumps({"error": "bad payload"}))
                    continue
                if not q:
                    await ws.send_text(json.dumps({"error": "empty message"}))
                    continue

                router = AIChatRouter()
                tool_out = await asyncio.get_running_loop().run_in_executor(
                    None, router.run_question, q
                )
                joined = "\n".join(tool_out) if isinstance(tool_out, list) else str(tool_out)

                memory = self.mem(sid)
                prompt = ChatPromptTemplate.from_messages(
                    [("system", "당신은 친절하고 정확한 AI 비서입니다.")] +
                    memory.buffer +
                    [("user", f'{q}\n\n🛠 도구 결과:\n{joined}')]
                )

                stream = (prompt | self.llm_stream).astream({})
                full_resp = ""
                async for chunk in stream:
                    token = getattr(chunk, "content", "")
                    if token:
                        full_resp += token
                        await ws.send_text(token)
                await ws.send_text("[DONE]")
                memory.chat_memory.add_user_message(q)
                memory.chat_memory.add_ai_message(full_resp)
        except WebSocketDisconnect:
            return

    async def _full_answer(self, sid: str, question: str, tool_out):
        """전체 응답 생성 (REST API용)"""
        joined = "\n".join(tool_out) if isinstance(tool_out, list) else str(tool_out)
        memory = self.mem(sid)
        prompt = ChatPromptTemplate.from_messages(
            [("system", "당신은 친절하고 정확한 AI 비서입니다.")] +
            memory.buffer +
            [("user", f'{question}\n\n🛠 도구 결과:\n{joined}')]
        )
        answer = markdown((prompt | self.llm).invoke({}).content)
        memory.chat_memory.add_user_message(question)
        if isinstance(answer, list):
            answer = "\n".join(str(x) for x in answer)
        memory.chat_memory.add_ai_message(answer)
        return answer

    async def load_chat_history(self, session_id: str, messages: list):
        """DB/Redis에서 로드한 채팅 히스토리를 메모리에 복원
        
        Args:
            session_id: 채팅 세션 ID (room_id)
            messages: ChatMessage 객체 리스트 (시간순 정렬됨)
        """
        try:
            memory = self.mem(session_id)
            
            # 메모리가 이미 있는지 다시 한번 확인 (안전장치)
            if len(memory.buffer) > 0:
                Logger.debug(f"Memory already exists for session {session_id}, skipping history load")
                return
            
            # 메시지가 없으면 로드할 필요 없음
            if not messages:
                Logger.debug(f"No messages to load for session {session_id}")
                return
            
            # 메시지를 시간순으로 메모리에 추가 (clear 하지 않고 추가만)
            loaded_count = 0
            for msg in messages:
                try:
                    if msg.sender_type == "USER":
                        memory.chat_memory.add_user_message(msg.content)
                        loaded_count += 1
                    elif msg.sender_type == "AI":
                        memory.chat_memory.add_ai_message(msg.content)
                        loaded_count += 1
                    else:
                        Logger.debug(f"Skipping message with unknown sender_type: {msg.sender_type}")
                except Exception as msg_error:
                    Logger.warn(f"Failed to load message {msg.message_id}: {msg_error}")
                    continue
            
            Logger.info(f"Loaded {loaded_count}/{len(messages)} messages into AI memory for session {session_id}")
            
        except Exception as e:
            Logger.error(f"Failed to load chat history for session {session_id}: {e}")
            # 히스토리 로드 실패해도 계속 진행 (새 대화로 시작)
    
    async def get_session_memory_keys(self, session_id: str) -> list:
        """특정 세션의 Redis 키 패턴 반환 (디버깅용)
        
        Returns:
            실제 Redis에 저장되는 키 리스트
        """
        # RedisChatMessageHistory의 기본 키 패턴
        # LangChain은 보통 {key_prefix}{session_id} 형태로 키를 생성
        base_key = f"{self.KEY_PREFIX}{session_id}"
        
        # LangChain의 일반적인 패턴
        return [
            base_key,  # 메인 키
            f"{base_key}:messages",  # 메시지 리스트 (가능한 패턴)
        ]

    async def do_with_lock(self, key: str, ttl: int = 10):
        """분산 락을 사용한 작업 실행"""
        lock_service = ServiceContainer.get_lock_service()
        token = await lock_service.acquire(key, ttl=ttl)
        if not token:
            raise Exception("락 획득 실패")
        try:
            # 락이 보장된 작업
            pass
        finally:
            await lock_service.release(key, token)
