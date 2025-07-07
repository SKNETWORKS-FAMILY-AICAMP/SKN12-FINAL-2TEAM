# Router.py  ───────────────────────────────────────────────────
from __future__ import annotations

import json, os
from typing import List, Dict, Any

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langgraph.graph import StateGraph, MessagesState, END
from langgraph.prebuilt import ToolNode

# ──────────────────────────── 0. 환경 변수
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not (OPENAI_API_KEY and OPENAI_API_KEY.startswith("sk-")):
    raise ValueError("❌ 유효한 OPENAI_API_KEY가 없습니다.")

# ──────────────────────────── 1. ToolCall 모델
class ToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any]

# ──────────────────────────── 2. Router (필요 시 사용)
class Router:
    """OpenAI 함수-콜로 어떤 툴을 쓸지 결정하는 라우터"""
    def __init__(
        self,
        tool_specs: List[Dict[str, Any]],
        *,
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
        system_prompt: str | None = None,
    ):
        self.tool_specs = tool_specs
        self.client = OpenAI(api_key=api_key or OPENAI_API_KEY)
        self.model = model
        self.system_prompt = system_prompt or (
            "You are a router that decides which tools the assistant should call."
        )

    def route(self, query: str) -> List[ToolCall]:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": query},
        ]
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=self.tool_specs,
            temperature=0,
        )
        calls = resp.choices[0].message.tool_calls or []
        out: List[ToolCall] = []
        for tc in calls:
            try:
                out.append(ToolCall(name=tc.function.name,
                                    arguments=json.loads(tc.function.arguments)))
            except Exception:
                pass
        return out

# ──────────────────────────── 3. 툴 정의
@tool
def web_search(query: str, k: int = 5) -> str:
    """인터넷 뉴스/정보 검색"""
    from tool.newsAPI import GNewsClient  # local import
    return GNewsClient().get(keyword=query, max_results=k)

@tool
def financial_statements(ticker: str, limit: int = 3) -> str:
    """종목 재무제표 조회"""
    from tool.financial_statements import IncomeStatementClient
    data = IncomeStatementClient().get(ticker, limit)
    return f"{ticker}: {data}"

TOOLS = [web_search, financial_statements]

# ──────────────────────────── 4. LLM (툴 바인딩)
llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=OPENAI_API_KEY,
    temperature=0,
)
llm_with_tools = llm.bind_tools(TOOLS)

# ──────────────────────────── 5. LangGraph 워크플로
def should_continue(state: MessagesState):
    """마지막 AI 메시지에 tool_calls 가 있으면 툴 실행 단계로"""
    last = state["messages"][-1]
    return "tools" if getattr(last, "tool_calls", None) else END

def call_model(state: MessagesState):
    msgs = state["messages"]
    resp = llm_with_tools.invoke(msgs)
    return {"messages": [resp]}

def build_workflow():
    builder = StateGraph(MessagesState)
    tool_node = ToolNode(TOOLS)                      # ★ agent 인자 없음 :contentReference[oaicite:0]{index=0}
    builder.add_node("call_model", call_model)
    builder.add_node("tools", tool_node)

    from langgraph.graph import START
    builder.add_edge(START, "call_model")
    builder.add_conditional_edges("call_model", should_continue, ["tools", END])
    builder.add_edge("tools", "call_model")

    return builder.compile()

# ──────────────────────────── 6. CLI
if __name__ == "__main__":
    print("🔧 LangGraph Tool Router CLI (Ctrl-C to exit)")
    graph = build_workflow()

    try:
        while True:
            q = input("\nQuestion > ").strip()
            if not q:
                continue
            result = graph.invoke({"messages": [{"role": "user", "content": q}]})
            for m in result["messages"]:
                print("→", getattr(m, "content", m))
    except (EOFError, KeyboardInterrupt):
        print("\n종료합니다.")
