from fastapi import FastAPI, Request
import uuid

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from AIChat.Router import run_question  # LangGraph 툴 실행 결과

app = FastAPI()

# ─────────────────────────── 1. LangChain GPT 모델 준비
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# ─────────────────────────── 2. GPT 응답 생성 함수
def generate_response(user_question: str, tool_result: str | list) -> str:
    # 문자열 배열이면 줄바꿈으로 이어붙임
    if isinstance(tool_result, list):
        joined_result = "\n".join(tool_result)
    else:
        joined_result = str(tool_result)

    # LLM 프롬프트 구성 (질문 + 도구 결과 모두 포함)
    prompt = PromptTemplate.from_template(
        "사용자의 질문: \"{user_question}\"\n\n"
        "아래는 위 질문에 대해 도구를 통해 수집한 정보입니다:\n\n"
        "{tool_result}\n\n"
        "이 정보를 바탕으로 질문에 정확하고 친절하게 답변해 주세요."
    )
    chain = prompt | llm

    # GPT 응답 생성
    return chain.invoke({
        "user_question": user_question,
        "tool_result": joined_result
    }).content

# ─────────────────────────── 3. /chat 엔드포인트 (API용)
@app.post("/chat")
async def chat(req: Request):
    data = await req.json()
    user_msg: str = data["message"]
    session_id: str = data.get("session_id") or str(uuid.uuid4())

    # 툴 실행 및 GPT 응답 생성
    tool_result = run_question(user_msg)
    reply = generate_response(user_msg, tool_result)

    return {
        "session_id": session_id,
        "reply": reply
    }

# ─────────────────────────── 4. CLI 실행 (터미널에서 테스트용)
if __name__ == "__main__":
    print("💬 LangGraph 기반 GPT CLI (종료: Ctrl+C)\n")
    try:
        while True:
            q = input("질문 > ").strip()
            if not q:
                continue
            tool_result = run_question(q)
            answer = generate_response(q, tool_result)
            print("\n🧠 GPT 응답:\n" + answer + "\n")
    except (EOFError, KeyboardInterrupt):
        print("\n종료합니다.")
