# base_server/service/llm/AIChat_service.py

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
        self.KEY_PREFIX = "chat:"

    def mem(self, session_id: str) -> ConversationBufferMemory:
        """세션별 대화 메모리 관리 (Redis 기반)"""
        if session_id not in self._session_mem:
            cache_client = self.cache_service.get_client()
            redis_url = f"redis://{cache_client._host}:{cache_client._port}/{cache_client._db}"
            if cache_client._password:
                redis_url = f"redis://:{cache_client._password}@{cache_client._host}:{cache_client._port}/{cache_client._db}"
            history = RedisChatMessageHistory(
                session_id=session_id,
                url=redis_url,
                key_prefix=self.KEY_PREFIX,
            )
            self._session_mem[session_id] = ConversationBufferMemory(
                chat_memory=history,
                return_messages=True
            )
        return self._session_mem[session_id]

    async def chat(self, message: str, session_id: str = ""):
        """REST API용 채팅 응답 생성"""
        if not message.strip():
            raise HTTPException(400, "message empty")
        sid = session_id or str(uuid.uuid4())
        loop = asyncio.get_event_loop()
        router = AIChatRouter()
        tool_out = await loop.run_in_executor(None, router.run_question, message)
        answer = await self._full_answer(sid, message, tool_out)
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
