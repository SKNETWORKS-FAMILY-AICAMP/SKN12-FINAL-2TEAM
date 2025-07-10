from __future__ import annotations

import json, os
from typing import List, Dict, Any
from dotenv import load_dotenv
from pydantic import BaseModel

from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langgraph.graph import StateGraph, MessagesState, END
from langgraph.prebuilt import ToolNode

from BasicTools.FinancialStatementTool import FinancialStatementTool, FinancialStatementParams
from BasicTools.MacroEconomicTool import MacroEconomicAgent, MacroEconomicInput
from BasicTools.MarketDataTool import NewsAgent, NewsInput
from BasicTools.SectorAnalysisTool import SectorAnalysisAgent, SectorAnalysisInput
from BasicTools.TechnicalAnalysisTool import TechnicalAnalysisAgent, TechnicalAnalysisInput

# ──────────────────────────── 0. 환경 변수
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not (OPENAI_API_KEY and OPENAI_API_KEY.startswith("sk-")):
    raise ValueError("❌ 유효한 OPENAI_API_KEY가 없습니다.")

# ──────────────────────────── 1. Tool 정의
@tool
def income_statement_tool(params: FinancialStatementParams) -> str:
    """기업의 손익계산서를 조회합니다 (매출, 순이익, EPS 등)."""
    agent = FinancialStatementTool("income-statement")
    return agent.get_data(ticker=params.ticker, period=params.period, limit=params.limit)

@tool
def balance_sheet_tool(params: FinancialStatementParams) -> str:
    """기업의 대차대조표를 조회합니다 (자산, 부채, 자본 등)."""
    agent = FinancialStatementTool("balance-sheet-statement")
    return agent.get_data(ticker=params.ticker, period=params.period, limit=params.limit)

@tool
def cashflow_statement_tool(params: FinancialStatementParams) -> str:
    """기업의 현금흐름표를 조회합니다 (영업/투자/재무 현금흐름)."""
    agent = FinancialStatementTool("cash-flow-statement")
    return agent.get_data(ticker=params.ticker, period=params.period, limit=params.limit)

@tool
def ratios_tool(params: FinancialStatementParams) -> str:
    """기업의 주요 재무비율을 조회합니다 (PER, ROE, 유동비율 등)."""
    agent = FinancialStatementTool("ratios")
    return agent.get_data(ticker=params.ticker, period=params.period, limit=params.limit)

@tool
def key_metrics_tool(params: FinancialStatementParams) -> str:
    """기업의 핵심 지표를 조회합니다 (시가총액, 마진율, 배당수익률 등)."""
    agent = FinancialStatementTool("key-metrics")
    return agent.get_data(ticker=params.ticker, period=params.period, limit=params.limit)

@tool
def financial_growth_tool(params: FinancialStatementParams) -> str:
    """기업의 성장률 지표를 조회합니다 (매출 성장률, EPS 성장률 등)."""
    agent = FinancialStatementTool("financial-growth")
    return agent.get_data(ticker=params.ticker, period=params.period, limit=params.limit)

@tool
def enterprise_value_tool(params: FinancialStatementParams) -> str:
    """기업의 기업가치 지표를 조회합니다 (EV, Net Debt 등)."""
    agent = FinancialStatementTool("enterprise-values")
    return agent.get_data(ticker=params.ticker, period=params.period, limit=params.limit)

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
    income_statement_tool,
    balance_sheet_tool,
    cashflow_statement_tool,
    ratios_tool,
    key_metrics_tool,
    financial_growth_tool,
    enterprise_value_tool,
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
