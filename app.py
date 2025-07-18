"""
app_chat_stream.py
FastAPI  :  REST /chat   +   WebSocket /stream  (토큰 스트리밍)
RedisChatMessageHistory :  세션별 대화 영구 저장
"""

import os, uuid, asyncio, json
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate
from base_server.service.llm.AIChat.Router import run_question           # LangGraph 툴 실행

# ── 환경
REDIS_URL  = os.getenv("REDIS_URL", "redis://localhost:6379/0")
KEY_PREFIX = "chat:"
MAX_TOKENS = 8_000

app = FastAPI()

llm        = ChatOpenAI(model="gpt-4o", temperature=0)
llm_stream = ChatOpenAI(model="gpt-4o", temperature=0, streaming=True)   # 스트리밍용

# ── 세션별 메모리
_session_mem: dict[str, ConversationBufferMemory] = {}
def mem(session_id: str) -> ConversationBufferMemory:
    if session_id not in _session_mem:
        history = RedisChatMessageHistory(
            session_id=session_id,
            url=REDIS_URL,
            key_prefix=KEY_PREFIX,
        )
        _session_mem[session_id] = ConversationBufferMemory(
            chat_memory=history,
            return_messages=True
        )
    return _session_mem[session_id]

# ─────────────────────────── REST  /chat
@app.post("/chat")
async def chat(req: Request):
    body = await req.json()
    q = body["message"].strip()
    if not q:
        raise HTTPException(400, "message empty")
    sid = body.get("session_id") or str(uuid.uuid4())

    loop = asyncio.get_event_loop()
    tool_out = await loop.run_in_executor(None, run_question, q)
    answer = await _full_answer(sid, q, tool_out)
    return {"session_id": sid, "reply": answer}

# ─────────────────────────── WebSocket /stream
@app.websocket("/stream")
async def ws_stream(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            # ── 0) 클라이언트 질문 대기
            data = await ws.receive_text()
            try:
                req = json.loads(data)
                q   = req["message"].strip()
                sid = req.get("session_id") or str(uuid.uuid4())
            except (KeyError, json.JSONDecodeError):
                await ws.send_text(json.dumps({"error": "bad payload"}))
                continue
            if not q:
                await ws.send_text(json.dumps({"error": "empty message"}))
                continue

            # ── 1) LangGraph 툴 (blocking → executor)
            tool_out = await asyncio.get_running_loop().run_in_executor(
                None, run_question, q
            )
            joined = "\n".join(tool_out) if isinstance(tool_out, list) else str(tool_out)

            # ── 2) 프롬프트
            memory = mem(sid)
            prompt = ChatPromptTemplate.from_messages(
                [("system", "당신은 친절하고 정확한 AI 비서입니다.")] +
                memory.buffer +
                [("user", f'{q}\n\n🛠 도구 결과:\n{joined}')]
            )

            # ── 3) 스트리밍 호출
            stream = (prompt | llm_stream).astream({})
            full_resp = ""
            async for chunk in stream:
                token = getattr(chunk, "content", "")     # ✔️ LangChain 0.2
                if token:
                    full_resp += token
                    await ws.send_text(token)             # 토큰 단위 전송

            # ── 4) 종료 신호
            await ws.send_text("[DONE]")

            # ── 5) 히스토리 저장
            memory.chat_memory.add_user_message(q)
            memory.chat_memory.add_ai_message(full_resp)

    except WebSocketDisconnect:
        return

# ─────────────────────────── 내부 함수 (REST 전체 응답)
async def _full_answer(sid: str, question: str, tool_out):
    joined = "\n".join(tool_out) if isinstance(tool_out, list) else str(tool_out)
    memory = mem(sid)
    prompt = ChatPromptTemplate.from_messages(
        [("system", "당신은 친절하고 정확한 AI 비서입니다.")] +
        memory.buffer +
        [("user", f'{question}\n\n🛠 도구 결과:\n{joined}')]
    )
    answer = (prompt | llm).invoke({}).content
    memory.chat_memory.add_user_message(question)
    if isinstance(answer, list):
        answer = "\n".join(str(x) for x in answer)
    memory.chat_memory.add_ai_message(answer)
    return answer
