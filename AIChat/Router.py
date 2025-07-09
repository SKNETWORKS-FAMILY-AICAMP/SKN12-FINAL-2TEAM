from __future__ import annotations

import json, os
from typing import List, Dict, Any
from dotenv import load_dotenv
from pydantic import BaseModel

from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langgraph.graph import StateGraph, MessagesState, END
from langgraph.prebuilt import ToolNode

from .tool.specialist_agents import (
    FinancialStatementAgent, FinancialStatementInput,
    NewsAgent, NewsInput,
    TechnicalAnalysisAgent, TechnicalAnalysisInput,
    MacroEconomicAgent, MacroEconomicInput,
    SectorAnalysisAgent, SectorAnalysisInput
)

# ──────────────────────────── 0. 환경 변수
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not (OPENAI_API_KEY and OPENAI_API_KEY.startswith("sk-")):
    raise ValueError("❌ 유효한 OPENAI_API_KEY가 없습니다.")

# ──────────────────────────── 1. Tool 정의
@tool
def financial_statement(ticker: str) -> str:
    """종목의 재무제표를 조회합니다 (매출, 순이익, EPS)."""
    agent = FinancialStatementAgent()
    result = agent.process(FinancialStatementInput(ticker=ticker))
    return result.summary

@tool
def news(query: str, k: int = 5) -> str:
    """특정 키워드에 대한 최신 뉴스를 조회합니다."""
    agent = NewsAgent()
    result = agent.process(NewsInput(query=query, k=k))
    return result.summary

@tool
def technical_analysis(tickers: list[str]) -> str:
    """종목들의 기술적 지표 (RSI, MACD, EMA)를 분석합니다."""
    agent = TechnicalAnalysisAgent()
    results = agent.process(TechnicalAnalysisInput(tickers=tickers))
    return "\n".join([r.summary for r in results])

@tool
def macro_economic(series_ids: list[str]) -> str:
    """거시경제 지표 (금리, CPI 등)를 조회합니다."""
    agent = MacroEconomicAgent()
    result = agent.process(MacroEconomicInput(series_ids=series_ids))
    return result.summary

@tool
def sector_analysis(sector_name: str) -> str:
    """섹터 PER/PBR 및 대표 종목을 조회합니다."""
    agent = SectorAnalysisAgent()
    result = agent.process(SectorAnalysisInput(sector_name=sector_name))
    return result.summary

TOOLS = [
    financial_statement,
    news,
    technical_analysis,
    macro_economic,
    sector_analysis
]

# ──────────────────────────── 2. LLM + 툴 바인딩
llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=OPENAI_API_KEY,
    temperature=0,
)
llm_with_tools = llm.bind_tools(TOOLS)

# ──────────────────────────── 3. LangGraph 노드 정의

def should_continue(state: MessagesState):
    last = state["messages"][-1]
    tool_calls = getattr(last, "tool_calls", None)
    if not tool_calls:
        return END

    called_names = set()
    for msg in state["messages"]:
        for tc in getattr(msg, "tool_calls", []):
            if hasattr(tc, "name"):
                called_names.add(tc.name)

    for tc in tool_calls:
        if hasattr(tc, "name") and tc.name in called_names:
            return END

    return "tools"

def call_model(state: MessagesState):
    print("🔄 call_model: ", state["messages"])
    resp = llm_with_tools.invoke(state["messages"])
    return {"messages": state["messages"] + [resp]}

# ──────────────────────────── 4. 그래프 구축 함수
def build_workflow():
    builder = StateGraph(MessagesState)
    builder.add_node("call_model", call_model)
    builder.add_node("tools", ToolNode(TOOLS))

    from langgraph.graph import START
    builder.add_edge(START, "call_model")
    builder.add_conditional_edges("call_model", should_continue, {"tools", END})
    builder.add_edge("tools", "call_model")

    return builder.compile()

# ──────────────────────────── 5. 외부 실행 함수
def run_question(question: str) -> str:
    graph = build_workflow()
    result = graph.invoke({"messages": [{"role": "user", "content": question}]})
    return "\n".join(getattr(m, "content", str(m)) for m in result["messages"])
