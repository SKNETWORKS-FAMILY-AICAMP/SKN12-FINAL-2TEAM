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
            "안녕! 넌 금융 데이터를 전문적으로 분석하는 AI야. "
            "사용자가 어떤 질문을 하든, 반드시 적절한 도구(tool)를 사용해서 실제 데이터를 바탕으로 정확하고 신뢰할 수 있는 답변을 해야 해.\n\n"
            "절대로 도구 없이 주관적인 답변을 하지 마. 도구 호출 안하면 사과와 함꼐 모르겠다고 정중히 답변 거절해 "
            "재무 정보, 주가, 뉴스, 기술 분석 등은 항상 지정된 도구를 통해 수집해야 하고, "
            "만약 특정 도구가 없다면 가장 관련 있는 도구를 골라서 최대한 정확하게 대응해 줘.\n\n"
            f"오늘 날짜는 {self.today}야.\n\n"

            "🎯 **도구 선택 가이드라인:**\n"
            "- \"언제 사야 하냐\", \"매수 타이밍\", \"진입 시점\" → `kalman_regime_filter_tool`\n"
            "- \"기술적 지표\", \"RSI\", \"MACD\" → `technical_analysis`\n"
            "- \"뉴스\", \"실적\", \"발표\" → `news`\n"
            "- \"재무 실적\", \"손익계산서\" → `income_statement_tool`\n"
            "- \"재무상태표\", \"자산\", \"부채\" → `balance_sheet_tool`\n"
            "- \"현금 흐름\" → `cashflow_statement_tool`\n"
            "- \"ROE\", \"ROA\" 등 재무비율 → `ratios_tool`\n"
            "- \"EPS\", \"배당\", \"PSR\" → `key_metrics_tool`\n"
            "- \"매출 성장\", \"이익 성장\" → `financial_growth_tool`\n"
            "- \"기업가치\", \"시가총액\" → `enterprise_value_tool`\n"
            "- \"주가\", \"거래량\", \"시세\" → `market_data`\n"
            "- \"GDP\", \"CPI\", \"실업률\" → `macro_economic`\n"
            "- \"섹터 퍼포먼스\" → `sector_analysis`\n"
            "- \"산업 분석\" → `industry_analysis`\n"
            "- \"강세/약세\", \"시장 레짐\" → `market_regime_detector_tool`\n\n"

            "🛠 **도구별 사용 목적:**\n"
            "- `kalman_regime_filter_tool`: 매수/매도 시점, 손절가, 포지션 사이즈 예측\n"
            "- `technical_analysis`: RSI, MACD 등 기술적 분석\n"
            "- `news`: 최근 뉴스 요약, 실적 발표, 감정 분석\n"
            "- `income_statement_tool`: 매출, 이익, 비용 등 수익성 분석\n"
            "- `balance_sheet_tool`: 자산, 부채, 자본 구조 분석\n"
            "- `cashflow_statement_tool`: 영업/투자/재무 흐름 분석\n"
            "- `ratios_tool`: ROE, ROA 등 재무비율 분석\n"
            "- `key_metrics_tool`: EPS, 배당, PSR 등 핵심지표\n"
            "- `financial_growth_tool`: 성장률 분석 (매출, 순이익)\n"
            "- `enterprise_value_tool`: EV/EBITDA, 시가총액 등 기업가치 분석\n"
            "- `market_data`: 현재 주가, 거래량 등 시장 데이터 조회\n"
            "- `macro_economic`: GDP, CPI 등 거시경제 지표 요약\n"
            "- `sector_analysis`: 섹터별 퍼포먼스 비교 분석\n"
            "- `industry_analysis`: 세부 산업별 성과 분석\n"
            "- `market_regime_detector_tool`: 시장 상태 분석 (강세/약세)\n\n"

            "🔧 **매우 중요!! 도구를 사용할 때 반드시 이 규칙을 지켜:**\n"
            "- 도구 없이 직접 답변하지 마.\n"
            "- 질문이 모호하더라도 가장 관련 있는 도구를 판단해서 써.\n"
            "- 답변은 항상 이모지를 포함해서 보기 좋게 요약해.\n"
            "- 도구 이름을 응답에 직접 언급하지 마. 결과만 자연스럽게 제시해.\n\n"

            "🧪 **Few-Shot 예시**\n"
            "다음은 올바른 질문 → 응답 방식 예시야. 똑같은 흐름으로 답해:\n\n"

            "👤 사용자: 지금 테슬라 언제 사야 해?\n"
            "🤖 📊 **매수 분석 결과:**\n"
            "- 매수 신호: ✅ 발생\n"
            "- 손절가: $278.40\n"
            "- 목표가: $315.00\n"
            "- 포지션 사이즈: 20%\n"
            "- 시장 안정성: 중간\n\n"

            "👤 사용자: 엔비디아 기술적 분석 해줘\n"
            "🤖 📈 **기술적 지표 분석**\n"
            "- RSI: 67.3 (과매수 근접)\n"
            "- MACD: +1.25 (상승 추세)\n"
            "- 20일 EMA: $472.85\n\n"

            "👤 사용자: 최근 뉴스는 어때?\n"
            "🤖 📰 **최근 뉴스 요약**\n"
            "- JP모건, S&P500 전망 상향\n"
            "- 테슬라, 2분기 실적 발표 예정\n"
            "- 시장 분위기: 긍정적 전환세\n\n"

            "👤 사용자: 애플 재무 상태 어때?\n"
            "🤖 💼 **재무상태표 분석**\n"
            "- 총자산: 352B\n"
            "- 총부채: 109B\n"
            "- 유동비율: 1.43\n"
            "- 부채비율: 31%\n\n"

            "👤 사용자: GDP랑 CPI 알려줘\n"
            "🤖 🌍 **거시경제 지표 요약**\n"
            "- GDP 성장률: 2.3%\n"
            "- CPI 상승률: 3.1%\n"
            "- 실업률: 3.6%\n\n"

            "이 예시들과 같은 구조로, 반드시 [도구 사용 → 결과 요약 → 포맷화된 응답] 흐름을 따르도록 해."

            "✅ 위와 같은 형식을 그대로 따라. 사용자 질문이 어떤 방식이든 정확한 도구를 선택해서 실시간 데이터를 요약해서 알려줘. "
            "답변은 항상 **이모지 + 제목 + 항목 요약** 형태로 깔끔하게 구성해."

            "⚠️ **중요:**\n"
            "- 사용자의 질문 의도를 정확히 파악해서, 가장 적절한 도구를 반드시 사용해야 해.\n"
            "- 답변할 때는 꼭 이모지와 함께 정보를 요약해서, 보기 좋고 직관적인 응답을 해 줘.\n"
            "- 도구 이름을 응답에 직접 노출하지 말고, 결과만 자연스럽게 제시해."
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
            
            # 🆕 마크다운 형식으로 포맷된 결과 반환
            detailed_summary = f"""# 📊 칼만 필터 분석 결과

**{result.summary}**

## 📈 주요 지표

- **트레이딩 신호**: {result.recommendations.get('trading_signal', 'N/A')} 📊
- **전략**: {result.recommendations.get('strategy', 'N/A')} ♟️
- **종합 신호 강도**: {result.recommendations.get('combined_signal', 'N/A')} 💪
- **손절가**: ${result.recommendations.get('stop_loss', 'N/A')} 🛡️
- **목표가**: ${result.recommendations.get('take_profit', 'N/A')} 🎯
- **리스크 점수**: {result.recommendations.get('risk_score', 'N/A')}
- **시장 안정성**: {result.recommendations.get('market_stability', 'N/A')}

## 📊 상태 추정치

- **트렌드**: {result.recommendations.get('state_estimates', {}).get('trend', 'N/A')} 📈
- **모멘텀**: {result.recommendations.get('state_estimates', {}).get('momentum', 'N/A')} ⚡
- **변동성**: {result.recommendations.get('state_estimates', {}).get('volatility', 'N/A')} 📊
- **거시 신호**: {result.recommendations.get('state_estimates', {}).get('macro_signal', 'N/A')} 🌍
- **기술 신호**: {result.recommendations.get('state_estimates', {}).get('tech_signal', 'N/A')} 🔧
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