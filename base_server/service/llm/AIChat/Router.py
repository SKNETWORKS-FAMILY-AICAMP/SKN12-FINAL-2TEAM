from __future__ import annotations

import json, os
from typing import List, Dict, Any
from dotenv import load_dotenv
from pydantic import BaseModel
from datetime import datetime
from zoneinfo import ZoneInfo

from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langgraph.graph import StateGraph, MessagesState, END
from langgraph.prebuilt import ToolNode
from langchain_core.prompts import ChatPromptTemplate

from service.llm.AIChat.BasicTools.FinancialStatementTool import FinancialStatementTool, FinancialStatementParams
from service.llm.AIChat.BasicTools.MacroEconomicTool import MacroEconomicTool, MacroEconomicInput
from service.llm.AIChat.BasicTools.SectorAnalysisTool import SectorAnalysisTool, SectorAnalysisInput
from service.llm.AIChat.BasicTools.TechnicalAnalysisTool import TechnicalAnalysisTool, TechnicalAnalysisInput
from service.llm.AIChat.BasicTools.MarketDataTool import MarketDataTool, MarketDataInput
from service.llm.AIChat.BasicTools.NewsTool import NewsTool, NewsInput
from service.llm.AIChat.BasicTools.IndustryAnalysisTool import IndustryAnalysisTool, IndustryAnalysisInput
from service.llm.AIChat.tool.MarketRegimeDetectorTool import MarketRegimeDetector, MarketRegimeDetectorInput
from service.llm.AIChat.tool.KalmanRegimeFilterTool import KalmanRegimeFilterTool, KalmanRegimeFilterInput

class AIChatRouter:
    def __init__(self, ai_chat_service : any):
        from service.llm.AIChat_service import AIChatService
        if not isinstance(ai_chat_service, AIChatService):
            raise TypeError("Expected AIChatService instance")
        self.ai_chat_service = ai_chat_service
        self.OPENAI_API_KEY = ai_chat_service.llm_config.providers[ai_chat_service.llm_config.default_provider].api_key
        now_seoul = datetime.now(ZoneInfo("Asia/Seoul"))
        self.today = now_seoul.date()
        self.SYSTEM_PROMPT = {
            "role": "system",
            "content": (
                "너는 금융 데이터를 분석하고 요약하는 AI 전문가야."
                "사용자의 질문을 분석해서 필요한 데이터를 툴을 통해 수집하고, "
                "최대한 근거를 세워서 대답 할 수 있도록 필요한 툴을 호출해."
                f"참고로 오늘 날짜는 {self.today}이야"
            )
        }
        # Tool definitions
        self.TOOLS = self._define_tools()
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=self.OPENAI_API_KEY,
            temperature=0,
        )
        self.llm_with_tools = self.llm.bind_tools(self.TOOLS)

    def _define_tools(self):
        @tool(args_schema=FinancialStatementParams)
        def income_statement_tool(**params):
            from service.service_container import ServiceContainer
            ai = ServiceContainer.get_ai_chat_service()
            agent = FinancialStatementTool(ai, "income-statement")
            return agent.get_data(**params)

        @tool(args_schema=FinancialStatementParams)
        def balance_sheet_tool(**params):
            from service.service_container import ServiceContainer
            ai = ServiceContainer.get_ai_chat_service()
            agent = FinancialStatementTool(ai, "balance-sheet-statement")
            return agent.get_data(**params)

        @tool(args_schema=FinancialStatementParams)
        def cashflow_statement_tool(**params):
            from service.service_container import ServiceContainer
            ai = ServiceContainer.get_ai_chat_service()
            agent = FinancialStatementTool(ai, "cash-flow-statement")
            return agent.get_data(**params)

        @tool(args_schema=FinancialStatementParams)
        def ratios_tool(**params):
            from service.service_container import ServiceContainer
            ai = ServiceContainer.get_ai_chat_service()
            agent = FinancialStatementTool(ai, "ratios")
            return agent.get_data(**params)

        @tool(args_schema=FinancialStatementParams)
        def key_metrics_tool(**params):
            from service.service_container import ServiceContainer
            ai = ServiceContainer.get_ai_chat_service()
            agent = FinancialStatementTool(ai, "key-metrics")
            return agent.get_data(**params)

        @tool(args_schema=FinancialStatementParams)
        def financial_growth_tool(**params):
            from service.service_container import ServiceContainer
            ai = ServiceContainer.get_ai_chat_service()
            agent = FinancialStatementTool(ai, "financial-growth")
            return agent.get_data(**params)

        @tool(args_schema=FinancialStatementParams)
        def enterprise_value_tool(**params):
            from service.service_container import ServiceContainer
            ai = ServiceContainer.get_ai_chat_service()
            agent = FinancialStatementTool(ai, "enterprise-values")
            return agent.get_data(**params)

        @tool(args_schema=NewsInput)
        def news(**params):
            from service.service_container import ServiceContainer
            ai = ServiceContainer.get_ai_chat_service()
            agent = NewsTool(ai)
            result = agent.get_data(**params)
            return result.summary

        @tool(args_schema=TechnicalAnalysisInput)
        def technical_analysis(**params):
            from service.service_container import ServiceContainer
            ai = ServiceContainer.get_ai_chat_service()
            agent = TechnicalAnalysisTool(ai)
            results = agent.get_data(**params)
            return "\n".join([r if isinstance(r, str) else r.summary for r in results.results])

        @tool(args_schema=MarketDataInput)
        def market_data(**params):
            from service.service_container import ServiceContainer
            ai = ServiceContainer.get_ai_chat_service()
            agent = MarketDataTool(ai)
            results = agent.get_data(**params)
            return results.summary

        @tool(args_schema=MacroEconomicInput)
        def macro_economic(**params):
            from service.service_container import ServiceContainer
            ai = ServiceContainer.get_ai_chat_service()
            agent = MacroEconomicTool(ai)
            result = agent.get_data(**params)
            return result.summary

        @tool(args_schema=SectorAnalysisInput)
        def sector_analysis(**params):
            from service.service_container import ServiceContainer
            ai = ServiceContainer.get_ai_chat_service()
            agent = SectorAnalysisTool(ai)
            result = agent.get_data(**params)
            return result.summary

        @tool(args_schema=IndustryAnalysisInput)
        def industry_analysis(**params):
            from service.service_container import ServiceContainer
            ai = ServiceContainer.get_ai_chat_service()
            agent = IndustryAnalysisTool(ai)
            result = agent.get_data(**params)
            return result.summary

        @tool(args_schema=MarketRegimeDetectorInput)
        def MarketRegimeDetectortool(**params):
            agent = MarketRegimeDetector()
            result = agent.get_data(**params)
            return result.summary

        @tool(args_schema=KalmanRegimeFilterInput)
        def KalmanRegimeFiltertool(**params):
            from service.service_container import ServiceContainer
            ai = ServiceContainer.get_ai_chat_service()
            agent = KalmanRegimeFilterTool(ai)
            result = agent.get_data(**params)
            return result.summary

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
            MarketRegimeDetectortool,
            KalmanRegimeFiltertool
        ]

    def should_continue(self, state: MessagesState):
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

        from langgraph.graph import START
        builder.add_edge(START, "call_model")
        builder.add_conditional_edges("call_model", self.should_continue, {"tools", END})
        builder.add_edge("tools", "call_model")

        return builder.compile()

    def run_question(self, question: str) -> str:
        graph = self.build_workflow()
        initial_messages = [
            self.SYSTEM_PROMPT,
            {"role": "user", "content": question}
        ]
        result = graph.invoke({"messages": initial_messages})
        return "\n".join(getattr(m, "content", str(m)) for m in result["messages"])

    def print_clean_messages(self, messages):
        print("🔄 요약된 모델 호출 로그")
        for m in messages:
            if hasattr(m, "content") and hasattr(m, "__class__"):
                cname = m.__class__.__name__
                if cname == "HumanMessage":
                    print(f"👤 Human: {m.content}")
                elif cname == "AIMessage":
                    calls = m.additional_kwargs.get("tool_calls", []) if hasattr(m, "additional_kwargs") else []
                    if calls:
                        for call in calls:
                            if "name" in call:
                                print(f"🤖 AI -> Tool: {call['name']} {call.get('args', '')}")
                            elif "function" in call:
                                func = call["function"]
                                print(f"🤖 AI -> Tool: {func.get('name', '')} {func.get('arguments', '')}")
                            else:
                                print(f"🤖 AI -> Tool: {call}")
                    if m.content and m.content.strip():
                        print(f"🤖 AI 응답: {m.content.strip()}")
                elif cname == "ToolMessage":
                    name = getattr(m, "name", None)
                    print(f"🛠️ Tool({name}) 결과: {getattr(m, 'content', '')}")
                else:
                    print(f"❓ {cname}: {getattr(m, 'content', '')}")
            else:
                print(str(m))