from __future__ import annotations

"""AIChatRouter – Finance‑focused LangGraph pipeline
====================================================

🔑 **핵심**
    • LLM(system prompt) ↔ **구체적인 description 이 포함된 Tool** ↔ 사용자 질문.
    • should_continue 로직에서 *dict* 형태와 *pydantic 객체* 형태의 `tool_calls`를 모두 처리하도록 개선했습니다.

변경 내역
---------
1. **_extract_tool_name(…)** 헬퍼 함수 추가  
   – dict(`{"name": …}`)이든 객체든 안전하게 이름 추출.
2. **should_continue()**와 **print_clean_messages()** 로직을 이 헬퍼로 교체.

"""

import json
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any, Dict, List

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langgraph.graph import StateGraph, MessagesState, END, START
from langgraph.prebuilt import ToolNode
from langchain_core.prompts import ChatPromptTemplate

# ──────────────── 툴 임포트 ──────────────────────────────────────────
from service.llm.AIChat.BasicTools.FinancialStatementTool import (
    FinancialStatementTool,
    FinancialStatementParams,
)
from service.llm.AIChat.BasicTools.MacroEconomicTool import (
    MacroEconomicTool,
    MacroEconomicInput,
)
from service.llm.AIChat.BasicTools.SectorAnalysisTool import (
    SectorAnalysisTool,
    SectorAnalysisInput,
)
from service.llm.AIChat.BasicTools.TechnicalAnalysisTool import (
    TechnicalAnalysisTool,
    TechnicalAnalysisInput,
)
from service.llm.AIChat.BasicTools.MarketDataTool import (
    MarketDataTool,
    MarketDataInput,
)
from service.llm.AIChat.BasicTools.NewsTool import NewsTool, NewsInput
from service.llm.AIChat.BasicTools.IndustryAnalysisTool import (
    IndustryAnalysisTool,
    IndustryAnalysisInput,
)

from service.llm.AIChat.tool.MarketRegimeDetectorTool import (
    MarketRegimeDetector,
    MarketRegimeDetectorInput,
)
from service.llm.AIChat.tool.KalmanRegimeFilterTool import (
    KalmanRegimeFilterTool,
    KalmanRegimeFilterInput,
)

# ──────────────────── 유틸 ──────────────────────────────────────────

def _extract_tool_name(tc: Any) -> str | None:
    """`tool_calls` 요소에서 안전하게 name을 추출합니다.

    OpenAI(ChatOpenAI) 응답은 list[dict] 타입이고,
    일부 LangChain 내부 객체는 `.name` attribute를 갖습니다.
    """
    if isinstance(tc, dict):
        return tc.get("name")
    return getattr(tc, "name", None)


class AIChatRouter:
    """LLM + LangGraph 기반 금융 분석 라우터"""

    # ────────────────── 초기화 ───────────────────────────────
    def __init__(self):
        # 서비스 컨테이너에서 AI 서비스 싱글톤 주입
        from service.service_container import ServiceContainer

        self.ai_chat_service = ServiceContainer.get_ai_chat_service()
        self.OPENAI_API_KEY = (
            self.ai_chat_service.llm_config
            .providers[self.ai_chat_service.llm_config.default_provider]
            .api_key
        )

        self.today = datetime.now(ZoneInfo("Asia/Seoul")).date()
        self.SYSTEM_PROMPT = {
            "role": "system",
            "content": (
                "너는 금융 데이터를 분석하고 요약하는 AI 전문가야. "
                "사용자의 질문을 분석해서 필요한 데이터를 툴을 통해 수집하고, "
                "각 데이터의 출처와 근거를 들어 설명해. "
                f"오늘 날짜는 {self.today}야."
            ),
        }

        # 툴 정의 + LLM 준비
        self.TOOLS = self._define_tools()
        self.llm = ChatOpenAI(
            model=self.ai_chat_service.llm_config.providers[
        self.ai_chat_service.llm_config.default_provider
    ].model, api_key=self.OPENAI_API_KEY, temperature=0
        )
        self.llm_with_tools = self.llm.bind_tools(self.TOOLS)

    # ────────────────── 툴 정의 ───────────────────────────────
    def _define_tools(self):
        """self.ai_chat_service를 재사용하며 description을 명확히 기재"""

        @tool(
            args_schema=FinancialStatementParams,
            description="기업 손익계산서(Income Statement) 핵심 항목을 조회·요약합니다.",
        )
        def income_statement_tool(**params):
            agent = FinancialStatementTool(self.ai_chat_service, "income-statement")
            return agent.get_data(**params)

        @tool(
            args_schema=FinancialStatementParams,
            description="기업 재무상태표(Balance Sheet) 핵심 항목을 조회·요약합니다.",
        )
        def balance_sheet_tool(**params):
            agent = FinancialStatementTool(
                self.ai_chat_service, "balance-sheet-statement"
            )
            return agent.get_data(**params)

        @tool(
            args_schema=FinancialStatementParams,
            description="기업 현금흐름표(Cash‑Flow Statement)를 조회·요약합니다.",
        )
        def cashflow_statement_tool(**params):
            agent = FinancialStatementTool(self.ai_chat_service, "cash-flow-statement")
            return agent.get_data(**params)

        @tool(
            args_schema=FinancialStatementParams,
            description="수익성·효율성 등 재무비율(Ratios)을 조회합니다.",
        )
        def ratios_tool(**params):
            agent = FinancialStatementTool(self.ai_chat_service, "ratios")
            return agent.get_data(**params)

        @tool(
            args_schema=FinancialStatementParams,
            description="주당지표·배당·PSR 등 핵심지표(Key Metrics)를 조회합니다.",
        )
        def key_metrics_tool(**params):
            agent = FinancialStatementTool(self.ai_chat_service, "key-metrics")
            return agent.get_data(**params)

        @tool(
            args_schema=FinancialStatementParams,
            description="매출·이익 성장률 등 Financial Growth 데이터를 조회합니다.",
        )
        def financial_growth_tool(**params):
            agent = FinancialStatementTool(self.ai_chat_service, "financial-growth")
            return agent.get_data(**params)

        @tool(
            args_schema=FinancialStatementParams,
            description="시가총액·EV/EBITDA 등 Enterprise Value 관련 지표를 조회합니다.",
        )
        def enterprise_value_tool(**params):
            agent = FinancialStatementTool(self.ai_chat_service, "enterprise-values")
            return agent.get_data(**params)

        @tool(
            args_schema=NewsInput,
            description="실시간·과거 뉴스 헤드라인을 요약해 제공합니다.",
        )
        def news(**params):
            agent = NewsTool(self.ai_chat_service)
            return agent.get_data(**params).summary

        @tool(
            args_schema=TechnicalAnalysisInput,
            description="RSI·MACD 등 기술적 분석 결과를 요약해 제공합니다.",
        )
        def technical_analysis(**params):
            agent = TechnicalAnalysisTool(self.ai_chat_service)
            results = agent.get_data(**params).results
            return "\n".join(r if isinstance(r, str) else r.summary for r in results)

        @tool(
            args_schema=MarketDataInput,
            description="주가·거래량 등 일/분/틱 Market Data를 요약합니다.",
        )
        def market_data(**params):
            agent = MarketDataTool(self.ai_chat_service)
            return agent.get_data(**params).summary

        @tool(
            args_schema=MacroEconomicInput,
            description="GDP·CPI·실업률 등 거시경제 지표를 요약합니다.",
        )
        def macro_economic(**params):
            agent = MacroEconomicTool(self.ai_chat_service)
            return agent.get_data(**params).summary

        @tool(
            args_schema=SectorAnalysisInput,
            description="11개 GICS 섹터의 퍼포먼스·밸류에이션을 분석합니다.",
        )
        def sector_analysis(**params):
            agent = SectorAnalysisTool(self.ai_chat_service)
            return agent.get_data(**params).summary

        @tool(
            args_schema=IndustryAnalysisInput,
            description="세부 산업(Industry) 레벨에서 주요 지표를 요약합니다.",
        )
        def industry_analysis(**params):
            agent = IndustryAnalysisTool(self.ai_chat_service)
            return agent.get_data(**params).summary

        @tool(
            args_schema=MarketRegimeDetectorInput,
            description="시장 레짐(강세/약세/횡보) 판단을 위한 통계 모델을 실행합니다.",
        )
        def market_regime_detector_tool(**params):
            agent = MarketRegimeDetector()
            return agent.get_data(**params).summary

        @tool(
            args_schema=KalmanRegimeFilterInput,
            description="칼만 필터 기반 레짐 전환 감지 결과를 제공합니다.",
        )
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

    # ────────────────── LangGraph 로직 ───────────────────────────
    def should_continue(self, state: MessagesState):
        """마지막 메시지에 툴 호출이 있으면 →툴 노드, 없으면 END"""

        last = state["messages"][-1]
        tool_calls = getattr(last, "tool_calls", None)
        if not tool_calls:
            return END

        # 이미 호출된 툴 set
        already_called = {
            _extract_tool_name(tc)
            for msg in state["messages"]
            for tc in getattr(msg, "tool_calls", [])
            if _extract_tool_name(tc)
        }

        # 새로운 호출이 중복되면 종료, 아니면 툴 실행
        for tc in tool_calls:
            name = _extract_tool_name(tc)
            if name and name in already_called:
                return END
        return "tools"

    def call_model(self, state: MessagesState):
        print("🔄 call_model: ", state["messages"])

        has_system = any(getattr(m, "role", None) == "system" for m in state["messages"])
        messages = ([self.SYSTEM_PROMPT] if not has_system else []) + state["messages"]

        resp = self.llm_with_tools.invoke(messages)
        return {"messages": state["messages"] + [resp]}

    def build_workflow(self):
        g = StateGraph(MessagesState)
        g.add_node("call_model", self.call_model)
        g.add_node("tools", ToolNode(self.TOOLS))
        g.add_edge(START, "call_model")
        g.add_conditional_edges("call_model", self.should_continue, {"tools", END})
        g.add_edge("tools", "call_model")
        return g.compile()

    # ───────────────────────── Public API ──────────────────────────
    def run_question(self, question: str) -> str:
        graph = self.build_workflow()
        init = [self.SYSTEM_PROMPT, {"role": "user", "content": question}]
        result = graph.invoke({"messages": init})
        return "\n".join(getattr(m, "content", str(m)) for m in result["messages"])

    def print_clean_messages(self, messages):
        """터미널용 간략 로그 출력"""
        print("🔄 호출 로그 정리")
        for m in messages:
            cls = getattr(m, "__class__", type("x", (), {})).__name__
            content = getattr(m, "content", "")
            if cls == "HumanMessage":
                print(f"👤 Human: {content}")
            elif cls == "AIMessage":
                tool_calls = m.additional_kwargs.get("tool_calls", [])
                for tc in tool_calls:
                    print(f"🤖 AI → Tool: {tc.get('name', '')} {tc.get('arguments', '')}")
                if content.strip():
                    print(f"🤖 AI 응답: {content.strip()}")
            elif cls == "ToolMessage":
                print(f"🛠 Tool({getattr(m, 'name', '')}): {content}")
            else:
                print(f"❓ {cls}: {content}")
