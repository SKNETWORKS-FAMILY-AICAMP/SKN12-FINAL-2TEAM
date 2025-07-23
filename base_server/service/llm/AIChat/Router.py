from __future__ import annotations

import os, json
from typing import List, Dict, Any
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langgraph.graph import StateGraph, MessagesState, END, START
from langgraph.prebuilt import ToolNode
from langchain_core.prompts import ChatPromptTemplate

# ──────────────── 기본 툴들 ─────────────────────────────────────────────
from service.llm.AIChat.BasicTools.FinancialStatementTool import (
    FinancialStatementTool, FinancialStatementParams,
)
from service.llm.AIChat.BasicTools.MacroEconomicTool import (
    MacroEconomicTool, MacroEconomicInput,
)
from service.llm.AIChat.BasicTools.SectorAnalysisTool import (
    SectorAnalysisTool, SectorAnalysisInput,
)
from service.llm.AIChat.BasicTools.TechnicalAnalysisTool import (
    TechnicalAnalysisTool, TechnicalAnalysisInput,
)
from service.llm.AIChat.BasicTools.MarketDataTool import (
    MarketDataTool, MarketDataInput,
)
from service.llm.AIChat.BasicTools.NewsTool import NewsTool, NewsInput
from service.llm.AIChat.BasicTools.IndustryAnalysisTool import (
    IndustryAnalysisTool, IndustryAnalysisInput,
)

# ──────────────── 커스텀 툴들 ────────────────────────────────────────────
from service.llm.AIChat.tool.MarketRegimeDetectorTool import (
    MarketRegimeDetector, MarketRegimeDetectorInput,
)
from service.llm.AIChat.tool.KalmanRegimeFilterTool import (
    KalmanRegimeFilterTool, KalmanRegimeFilterInput,
)


class AIChatRouter:
    """LLM + LangGraph 기반 금융 분석 라우터"""
    def __init__(self):
        # 서비스 컨테이너에서 AI 서비스 1회만 주입
        from service.service_container import ServiceContainer
        self.ai_chat_service = ServiceContainer.get_ai_chat_service()

        # OpenAI 키
        self.OPENAI_API_KEY = (
            self.ai_chat_service.llm_config
            .providers[self.ai_chat_service.llm_config.default_provider]
            .api_key
        )

        # 오늘 날짜(서울)
        self.today = datetime.now(ZoneInfo("Asia/Seoul")).date()

        # 시스템 프롬프트
        self.SYSTEM_PROMPT = {
            "role": "system",
            "content": (
                "너는 금융 데이터를 분석하고 요약하는 AI 전문가야. "
                "사용자의 질문을 분석해서 필요한 데이터를 툴을 통해 수집하고, "
                "최대한 근거를 세워서 대답 할 수 있도록 필요한 툴을 호출해. "
                f"참고로 오늘 날짜는 {self.today}이야"
            ),
        }

        # 툴 정의
        self.TOOLS = self._define_tools()

        # LLM 초기화(+툴 바인딩)
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=self.OPENAI_API_KEY,
            temperature=0,
        )
        self.llm_with_tools = self.llm.bind_tools(self.TOOLS)

    # ─────────────────── 내부 메서드 ──────────────────────────────────
    def _define_tools(self):
        """self.ai_chat_service를 직접 사용하도록 모든 툴 정의"""

        @tool(args_schema=FinancialStatementParams)
        def income_statement_tool(**params):
            agent = FinancialStatementTool(self.ai_chat_service, "income-statement")
            return agent.get_data(**params)

        @tool(args_schema=FinancialStatementParams)
        def balance_sheet_tool(**params):
            agent = FinancialStatementTool(self.ai_chat_service, "balance-sheet-statement")
            return agent.get_data(**params)

        @tool(args_schema=FinancialStatementParams)
        def cashflow_statement_tool(**params):
            agent = FinancialStatementTool(self.ai_chat_service, "cash-flow-statement")
            return agent.get_data(**params)

        @tool(args_schema=FinancialStatementParams)
        def ratios_tool(**params):
            agent = FinancialStatementTool(self.ai_chat_service, "ratios")
            return agent.get_data(**params)

        @tool(args_schema=FinancialStatementParams)
        def key_metrics_tool(**params):
            agent = FinancialStatementTool(self.ai_chat_service, "key-metrics")
            return agent.get_data(**params)

        @tool(args_schema=FinancialStatementParams)
        def financial_growth_tool(**params):
            agent = FinancialStatementTool(self.ai_chat_service, "financial-growth")
            return agent.get_data(**params)

        @tool(args_schema=FinancialStatementParams)
        def enterprise_value_tool(**params):
            agent = FinancialStatementTool(self.ai_chat_service, "enterprise-values")
            return agent.get_data(**params)

        @tool(args_schema=NewsInput)
        def news(**params):
            agent = NewsTool(self.ai_chat_service)
            return agent.get_data(**params).summary

        @tool(args_schema=TechnicalAnalysisInput)
        def technical_analysis(**params):
            agent = TechnicalAnalysisTool(self.ai_chat_service)
            results = agent.get_data(**params).results
            return "\n".join(r if isinstance(r, str) else r.summary for r in results)

        @tool(args_schema=MarketDataInput)
        def market_data(**params):
            agent = MarketDataTool(self.ai_chat_service)
            return agent.get_data(**params).summary

        @tool(args_schema=MacroEconomicInput)
        def macro_economic(**params):
            agent = MacroEconomicTool(self.ai_chat_service)
            return agent.get_data(**params).summary

        @tool(args_schema=SectorAnalysisInput)
        def sector_analysis(**params):
            agent = SectorAnalysisTool(self.ai_chat_service)
            return agent.get_data(**params).summary

        @tool(args_schema=IndustryAnalysisInput)
        def industry_analysis(**params):
            agent = IndustryAnalysisTool(self.ai_chat_service)
            return agent.get_data(**params).summary

        @tool(args_schema=MarketRegimeDetectorInput)
        def market_regime_detector_tool(**params):
            agent = MarketRegimeDetector()
            return agent.get_data(**params).summary

        @tool(args_schema=KalmanRegimeFilterInput)
        def kalman_regime_filter_tool(**params):
            agent = KalmanRegimeFilterTool(self.ai_chat_service)
            return agent.get_data(**params).summary

        return [
            income_statement_tool,
            balance_sheet_tool,
            cashflow_statement_tool,
            ratios_tool,
            key_metrics_tool,
            financial_growth_tool,
            enterprise_value_tool,
            news,
            technical_analysis,
            market_data,
            macro_economic,
            sector_analysis,
            industry_analysis,
            market_regime_detector_tool,
            kalman_regime_filter_tool,
        ]

    # ─────────────────── LangGraph 관련 ──────────────────────────────
    def should_continue(self, state: MessagesState):
        last = state["messages"][-1]
        tool_calls = getattr(last, "tool_calls", None)
        if not tool_calls:
            return END

        already_called = {
            tc.name
            for msg in state["messages"]
            for tc in getattr(msg, "tool_calls", [])
            if hasattr(tc, "name")
        }

        # 새로 호출된 툴이 이전에도 나왔으면 종료
        for tc in tool_calls:
            if hasattr(tc, "name") and tc.name in already_called:
                return END

        return "tools"

    def call_model(self, state: MessagesState):
        print("🔄 call_model: ", state["messages"])

        has_system = any(getattr(m, "role", None) == "system" for m in state["messages"])
        messages = ([self.SYSTEM_PROMPT] if not has_system else []) + state["messages"]

        resp = self.llm_with_tools.invoke(messages)
        return {"messages": state["messages"] + [resp]}

    def build_workflow(self):
        builder = StateGraph(MessagesState)

        builder.add_node("call_model", self.call_model)
        builder.add_node("tools", ToolNode(self.TOOLS))

        builder.add_edge(START, "call_model")
        builder.add_conditional_edges("call_model", self.should_continue, {"tools", END})
        builder.add_edge("tools", "call_model")

        return builder.compile()

    # ─────────────────── 외부 API ────────────────────────────────────
    def run_question(self, question: str) -> str:
        graph = self.build_workflow()
        initial_messages = [self.SYSTEM_PROMPT, {"role": "user", "content": question}]
        result = graph.invoke({"messages": initial_messages})
        return "\n".join(getattr(m, "content", str(m)) for m in result["messages"])

    def print_clean_messages(self, messages):
        print("🔄 요약된 모델 호출 로그")
        for m in messages:
            if not hasattr(m, "__class__") or not hasattr(m, "content"):
                print(str(m))
                continue

            cname = m.__class__.__name__
            if cname == "HumanMessage":
                print(f"👤 Human: {m.content}")
            elif cname == "AIMessage":
                tool_calls = m.additional_kwargs.get("tool_calls", [])
                for call in tool_calls:
                    if "name" in call:
                        print(f"🤖 AI → Tool: {call['name']} {call.get('args', '')}")
                    elif "function" in call:
                        func = call["function"]
                        print(f"🤖 AI → Tool: {func.get('name', '')} {func.get('arguments', '')}")
                if m.content and m.content.strip():
                    print(f"🤖 AI 응답: {m.content.strip()}")
            elif cname == "ToolMessage":
                print(f"🛠️ Tool({getattr(m, 'name', None)}) 결과: {m.content}")
            else:
                print(f"❓ {cname}: {m.content}")
