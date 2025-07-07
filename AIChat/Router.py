from __future__ import annotations

import json
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, ToolExecutor, tools_condition

# ✅ 환경 변수 자동 로드용 (필요 시 pip install python-dotenv)
load_dotenv()


# ---------------------------------------------------------------------------
# ToolCall 모델
# ---------------------------------------------------------------------------
class ToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any]


# ---------------------------------------------------------------------------
# Router 클래스
# ---------------------------------------------------------------------------
class Router:
    """LLM Router – 적절한 tool 선택을 담당"""

    def __init__(
        self,
        tool_specs: List[Dict[str, Any]],
        model: str = "gpt-4o",
        api_key: str | None = None,
        system_prompt: str | None = None,
    ) -> None:
        if not tool_specs:
            raise ValueError("tool_specs must contain at least one tool schema.")

        resolved_key = api_key or os.getenv("OPENAI_API_KEY")
        if not resolved_key:
            raise ValueError("❌ OpenAI API 키가 설정되지 않았습니다. .env 또는 직접 전달 필요.")

        self.tool_specs = tool_specs
        self.client = OpenAI(api_key=resolved_key)
        self.model = model
        self.system_prompt = (
            system_prompt
            or "You are a router that decides which tools (functions) the assistant should invoke to best answer the user's query."
        )

    def route(self, query: str, extra_context: str | None = None) -> List[ToolCall]:
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": self.system_prompt},
        ]
        if extra_context:
            messages.append({"role": "system", "content": extra_context})
        messages.append({"role": "user", "content": query})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=self.tool_specs,
            tool_choice="auto",
            temperature=0,
        )

        tool_calls_raw = response.choices[0].message.tool_calls or []

        result = []
        for tc in tool_calls_raw:
            try:
                name = tc.function.name
                args = json.loads(tc.function.arguments)
                result.append(ToolCall(name=name, arguments=args))
            except Exception as e:
                print(f"[Router] Failed to parse tool call: {e}")
        return result


# ---------------------------------------------------------------------------
# TOOL 스펙 정의
# ---------------------------------------------------------------------------
TOOL_SPECS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "인터넷에서 최신 뉴스나 사실 정보를 검색합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "검색할 키워드 (영어)"},
                    "k": {"type": "integer", "description": "가져올 문서 수", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "financial_statements",
            "description": "주식/암호화폐 실시간 가격, 재무 지표를 조회합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "종목 기호 (e.g., TSLA, 005930.KS)"},
                    "limit": {"type": "integer","description": "조회할 재무제표 개수 (기본값: 3)","default": 3,
                    },
                },
                "required": ["ticker"],
            },
        },
    }
]
# ---------------------------------------------------------------------------
# 툴 함수 정의
# ---------------------------------------------------------------------------
@tool
def web_search(query: str, k: int = 5):
    """인터넷에서 최신 뉴스나 사실 정보를 검색합니다."""
    from tool.newsAPI import GNewsClient
    news = GNewsClient()
    answer = news.get(keyword=query, max_results=k)
    return answer

@tool
def financial_statements(ticker: str, limit: int = 1):
    """주식/암호화폐 실시간 가격, 재무 지표를 조회합니다."""
    from tool.financial_statements import IncomeStatementClient
    client = IncomeStatementClient()
    answer = client.get(ticker, limit)
    return f"ticker {ticker} financial_data {answer}"

tools = [web_search, financial_statements]

# ---------------------------------------------------------------------------
# 툴 이름과 실제 함수 매핑
#
TOOL_FUNCTIONS = {
    "web_search": web_search,
    "financial_statements": financial_statements,
}
# ---------------------------------------------------------------------------
# CLI 테스트 실행
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("LangGraph 기반 Tool Router 시작!")
    graph = StateGraph()
    graph.add_node("tools", ToolNode(tools=tools, llm=llm))
    graph.add_edge("tools", END)
    graph.set_entry_point("tools")
    workflow = graph.compile()

    while True:
        try:
            user_inp = input("\nQuestion > ")
        except (EOFError, KeyboardInterrupt):
            print("\n종료합니다.")
            break

        # LangGraph 워크플로우 실행
        result = workflow.invoke({"input": user_inp})
        print(result["output"])
