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
    def __init__(self, client_session=None):
        # 🆕 세션 정보 저장
        self.client_session = client_session
        
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
                "너는 금융 데이터를 분석하는 AI 전문가야. "
                "중요: 사용자의 질문에 답하기 위해서는 반드시 적절한 도구를 사용해야 해. "
                "절대로 도구 없이 답변하지 마. "
                "재무 실적, 주가, 시세, 뉴스 등 모든 금융 정보는 도구를 통해 수집해야 해. "
                "도구를 사용해서 실제 데이터를 기반으로 정확한 정보를 제공해. "
                "도구 사용이 불가능한 경우에도 가능한 도구를 찾아서 사용해. "
                f"오늘 날짜는 {self.today}야.\n\n"
                "🎯 도구 선택 가이드라인:\n"
                "- \"언제 사야하냐\", \"매수 타이밍\", \"진입 시점\" → kalman_regime_filter_tool 사용\n"
                "- \"기술적 지표\", \"RSI\", \"MACD\" → technical_analysis 사용\n"
                "- \"뉴스\", \"실적\", \"발표\" → news 사용\n"
                "- \"재무 실적\", \"손익계산서\", \"수익성\" → income_statement_tool 사용\n"
                "- \"재무상태표\", \"자산\", \"부채\" → balance_sheet_tool 사용\n"
                "- \"현금흐름표\", \"현금 흐름\" → cashflow_statement_tool 사용\n"
                "- \"재무비율\", \"ROE\", \"ROA\" → ratios_tool 사용\n"
                "- \"핵심지표\", \"EPS\", \"배당\" → key_metrics_tool 사용\n"
                "- \"성장률\", \"매출 성장\" → financial_growth_tool 사용\n"
                "- \"기업가치\", \"EV\", \"시가총액\" → enterprise_value_tool 사용\n"
                "- \"주가\", \"거래량\", \"시세\" → market_data 사용\n"
                "- \"거시경제\", \"GDP\", \"CPI\" → macro_economic 사용\n"
                "- \"섹터\", \"산업별\" → sector_analysis 사용\n"
                "- \"산업\", \"Industry\" → industry_analysis 사용\n"
                "- \"시장 레짐\", \"강세/약세\" → market_regime_detector_tool 사용\n\n"
                "🔧 도구별 용도:\n"
                "- kalman_regime_filter_tool: 매수/매도 시점, 포지션 크기, 손절가 예측\n"
                "- technical_analysis: RSI, MACD 등 기술적 지표 분석\n"
                "- news: 뉴스, 실적, 시장 감정 분석\n"
                "- income_statement_tool: 손익계산서, 수익성 지표 분석\n"
                "- balance_sheet_tool: 재무상태표, 자산/부채 분석\n"
                "- cashflow_statement_tool: 현금흐름표, 현금 흐름 분석\n"
                "- ratios_tool: 재무비율, ROE/ROA 등 분석\n"
                "- key_metrics_tool: 핵심지표, EPS/배당 등 분석\n"
                "- financial_growth_tool: 성장률, 매출/이익 성장 분석\n"
                "- enterprise_value_tool: 기업가치, EV/시가총액 분석\n"
                "- market_data: 주가, 거래량 등 시장 데이터\n"
                "- macro_economic: 거시경제, GDP/CPI 등 분석\n"
                "- sector_analysis: 섹터별 퍼포먼스 분석\n"
                "- industry_analysis: 산업별 세부 분석\n"
                "- market_regime_detector_tool: 시장 레짐(강세/약세) 분석\n\n"
                "📋 예시:\n"
                "사용자: \"언제 사야하냐\" → kalman_regime_filter_tool\n"
                "답변: 📊 매수 시점 분석 결과: 매수 신호, 포지션 크기 15%, 손절가 $280.50\n\n"
                "사용자: \"기술적 지표는?\" → technical_analysis\n"
                "답변: 📈 기술적 분석: RSI 45.2 (중립), MACD -0.85 (하락), 20일 EMA $315.20\n\n"
                "사용자: \"뉴스는?\" → news\n"
                "답변: 📰 최근 뉴스: 실적 발표 예상, 시장 반응 긍정적, 투자자 관심 증가\n\n"
                "사용자: \"재무 실적은?\" → income_statement_tool\n"
                "답변: 💰 재무 실적: 매출 성장 12%, 순이익 증가 8%, 수익성 개선\n\n"
                "사용자: \"주가는?\" → market_data\n"
                "답변: 📊 현재 주가: $308.50, 거래량 85M, 전일 대비 +2.3%\n\n"
                "사용자: \"거시경제는?\" → macro_economic\n"
                "답변: 🌍 거시경제: GDP 성장률 2.1%, CPI 3.2%, 실업률 3.8%\n\n"
                "중요: 질문 의도를 정확히 파악하여 적절한 도구를 선택하고, 답변 시 적절한 이모지를 사용하여 가독성을 높여라."
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

        @tool(args_schema=FinancialStatementParams)
        def income_statement_tool(**params):
            """기업의 손익계산서(Income Statement)를 조회합니다. 매출, 비용, 순이익 등 수익성 지표를 제공합니다. \"재무 실적\", \"손익계산서\", \"수익성\" 질문에 적합합니다."""
            agent = FinancialStatementTool(self.ai_chat_service, "income-statement")
            return agent.get_data(**params)

        @tool(args_schema=FinancialStatementParams)
        def balance_sheet_tool(**params):
            """기업의 재무상태표(Balance Sheet)를 조회합니다. 자산, 부채, 자본 등 재무 건전성 지표를 제공합니다. \"재무상태표\", \"자산\", \"부채\", \"재무 건전성\" 질문에 적합합니다."""
            agent = FinancialStatementTool(self.ai_chat_service, "balance-sheet-statement")
            return agent.get_data(**params)

        @tool(args_schema=FinancialStatementParams)
        def cashflow_statement_tool(**params):
            """기업의 현금흐름표(Cash Flow Statement)를 조회합니다. 영업, 투자, 재무 활동의 현금 흐름을 제공합니다. \"현금흐름표\", \"현금 흐름\", \"영업 현금\" 질문에 적합합니다."""
            agent = FinancialStatementTool(self.ai_chat_service, "cash-flow-statement")
            return agent.get_data(**params)

        @tool(args_schema=FinancialStatementParams)
        def ratios_tool(**params):
            """수익성, 효율성 등 재무비율(Ratios)을 조회합니다. \"재무비율\", \"ROE\", \"ROA\", \"수익성\" 질문에 적합합니다."""
            agent = FinancialStatementTool(self.ai_chat_service, "ratios")
            return agent.get_data(**params)

        @tool(args_schema=FinancialStatementParams)
        def key_metrics_tool(**params):
            """주당지표, 배당, PSR 등 핵심지표(Key Metrics)를 조회합니다. \"핵심지표\", \"EPS\", \"배당\", \"PSR\" 질문에 적합합니다."""
            agent = FinancialStatementTool(self.ai_chat_service, "key-metrics")
            return agent.get_data(**params)

        @tool(args_schema=FinancialStatementParams)
        def financial_growth_tool(**params):
            """매출, 이익 성장률 등 Financial Growth 데이터를 조회합니다. \"성장률\", \"매출 성장\", \"이익 성장\" 질문에 적합합니다."""
            agent = FinancialStatementTool(self.ai_chat_service, "financial-growth")
            return agent.get_data(**params)

        @tool(args_schema=FinancialStatementParams)
        def enterprise_value_tool(**params):
            """시가총액, EV/EBITDA 등 Enterprise Value 관련 지표를 조회합니다. \"기업가치\", \"EV\", \"시가총액\" 질문에 적합합니다."""
            agent = FinancialStatementTool(self.ai_chat_service, "enterprise-values")
            return agent.get_data(**params)

        @tool(args_schema=NewsInput)
        def news(**params):
            """뉴스, 실적, 시장 감정 분석을 제공합니다. \"뉴스\", \"실적\", \"발표\" 질문에 적합합니다."""
            agent = NewsTool(self.ai_chat_service)
            return agent.get_data(**params).summary

        @tool(args_schema=TechnicalAnalysisInput)
        def technical_analysis(**params):
            """RSI, MACD, EMA 등 기술적 지표 분석을 제공합니다. \"기술적 지표\", \"RSI\", \"MACD\" 질문에 적합합니다."""
            agent = TechnicalAnalysisTool(self.ai_chat_service)
            results = agent.get_data(**params).results
            return "\n".join(r if isinstance(r, str) else r.summary for r in results)

        @tool(args_schema=MarketDataInput)
        def market_data(**params):
            """주가, 거래량 등 일/분/틱 Market Data를 요약합니다. \"주가\", \"거래량\", \"시세\" 질문에 적합합니다."""
            agent = MarketDataTool(self.ai_chat_service)
            return agent.get_data(**params).summary

        @tool(args_schema=MacroEconomicInput)
        def macro_economic(**params):
            """GDP, CPI, 실업률 등 거시경제 지표를 요약합니다. \"거시경제\", \"GDP\", \"CPI\", \"실업률\" 질문에 적합합니다."""
            agent = MacroEconomicTool(self.ai_chat_service)
            return agent.get_data(**params).summary

        @tool(args_schema=SectorAnalysisInput)
        def sector_analysis(**params):
            """11개 GICS 섹터의 퍼포먼스, 밸류에이션을 분석합니다. \"섹터\", \"산업별\", \"GICS\" 질문에 적합합니다."""
            agent = SectorAnalysisTool(self.ai_chat_service)
            return agent.get_data(**params).summary

        @tool(args_schema=IndustryAnalysisInput)
        def industry_analysis(**params):
            """세부 산업(Industry) 레벨에서 주요 지표를 요약합니다. \"산업\", \"Industry\", \"세부 산업\" 질문에 적합합니다."""
            agent = IndustryAnalysisTool(self.ai_chat_service)
            return agent.get_data(**params).summary

        @tool(args_schema=MarketRegimeDetectorInput)
        def market_regime_detector_tool(**params):
            """시장 레짐(강세/약세/횡보) 판단을 위한 통계 모델을 실행합니다. \"시장 레짐\", \"강세/약세\", \"시장 상태\" 질문에 적합합니다."""
            agent = MarketRegimeDetector()
            return agent.get_data(**params).summary

        @tool(args_schema=KalmanRegimeFilterInput)
        def kalman_regime_filter_tool(**params):
            """매수/매도 시점 예측, 포지션 크기 계산, 손절가/목표가 설정을 제공합니다. \"언제 사야하냐\", \"매수 타이밍\", \"진입 시점\" 질문에 적합합니다."""
            agent = KalmanRegimeFilterTool(self.ai_chat_service)
            
            # 🆕 세션 정보 주입 (SessionAwareTool 지원)
            print(f"[Router] client_session: {self.client_session}")
            if self.client_session:
                print(f"[Router] client_session.session: {self.client_session.session}")
                from service.llm.AIChat.SessionAwareTool import ClientSession
                session = ClientSession.from_template_session(self.client_session.session)
                print(f"[Router] created session: {session}")
                if session:
                    agent.inject_session(session)
                    print(f"[Router] 세션 주입 완료: account_db_key={session.account_db_key}")
                else:
                    print(f"[Router] 세션 생성 실패")
            else:
                print(f"[Router] client_session이 None")
            
            result = agent.get_data(**params)
            
            # 🆕 상세 정보를 포함한 포맷된 결과 반환
            detailed_summary = f"""
{result.summary}

📊 **상세 분석 결과:**
• **트레이딩 신호**: {result.recommendations.get('trading_signal', 'N/A')}
• **전략**: {result.recommendations.get('strategy', 'N/A')}
• **종합 신호 강도**: {result.recommendations.get('combined_signal', 'N/A')}
• **손절가**: ${result.recommendations.get('stop_loss', 'N/A')}
• **목표가**: ${result.recommendations.get('take_profit', 'N/A')}
• **리스크 점수**: {result.recommendations.get('risk_score', 'N/A')}
• **시장 안정성**: {result.recommendations.get('market_stability', 'N/A')}

📈 **상태 추정치:**
• **트렌드**: {result.recommendations.get('state_estimates', {}).get('trend', 'N/A')}
• **모멘텀**: {result.recommendations.get('state_estimates', {}).get('momentum', 'N/A')}
• **변동성**: {result.recommendations.get('state_estimates', {}).get('volatility', 'N/A')}
• **거시 신호**: {result.recommendations.get('state_estimates', {}).get('macro_signal', 'N/A')}
• **기술 신호**: {result.recommendations.get('state_estimates', {}).get('tech_signal', 'N/A')}
"""
            return detailed_summary

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
        from service.core.logger import Logger

        last = state["messages"][-1]
        tool_calls = getattr(last, "tool_calls", None)
        
        Logger.debug(f"should_continue: 마지막 메시지 타입={type(last).__name__}")
        Logger.debug(f"should_continue: tool_calls={tool_calls}")
        
        if not tool_calls:
            Logger.debug("should_continue: 도구 호출 없음 → END")
            return END

        # 현재 메시지의 도구 호출만 확인 (중복 체크 제거)
        current_tool_calls = []
        for tc in tool_calls:
            name = _extract_tool_name(tc)
            if name:
                current_tool_calls.append(name)
        
        Logger.debug(f"should_continue: 현재 도구 호출들={current_tool_calls}")
        
        if current_tool_calls:
            Logger.debug("should_continue: 도구 호출 있음 → tools")
            return "tools"
        else:
            Logger.debug("should_continue: 유효한 도구 호출 없음 → END")
            return END

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
        from service.core.logger import Logger
        
        Logger.debug(f"Router.run_question 시작: {question}")
        graph = self.build_workflow()
        init = [self.SYSTEM_PROMPT, {"role": "user", "content": question}]
        result = graph.invoke({"messages": init})
        
        Logger.debug(f"Router 실행 완료, 메시지 수: {len(result['messages'])}")
        
        # 도구 호출 결과만 추출하여 반환
        tool_results = []
        for i, m in enumerate(result["messages"]):
            Logger.debug(f"메시지 {i}: {type(m).__name__}, content={getattr(m, 'content', 'N/A')[:100]}...")
            if hasattr(m, 'name') and m.name:  # ToolMessage인 경우
                tool_results.append(f"🛠 {m.name}: {m.content}")
                Logger.debug(f"도구 결과 발견: {m.name}")
        
        if tool_results:
            Logger.debug(f"도구 결과 반환: {len(tool_results)}개")
            return "\n".join(tool_results)
        else:
            # 도구 호출이 없으면 마지막 AI 응답 반환
            for m in reversed(result["messages"]):
                if hasattr(m, 'content') and m.content and not hasattr(m, 'name'):
                    Logger.debug(f"AI 응답 반환: {m.content[:100]}...")
                    return m.content
            Logger.warn("도구 실행 결과를 찾을 수 없습니다.")
            return "도구 실행 결과를 찾을 수 없습니다."

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

# 지운 항목들
#• **포지션 크기**: {result.recommendations.get('position_size', 'N/A')} 주
# **레버리지**: {result.recommendations.get('leverage', 'N/A')} 배