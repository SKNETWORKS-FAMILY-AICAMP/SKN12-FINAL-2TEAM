"""섹터별 주요 종목(PER, PBR 등) 조회 도구"""
import requests
import os
from typing import List, Optional, Dict, Any
from service.llm.AIChat.BaseFinanceTool import BaseFinanceTool
from pydantic import BaseModel, Field

class SectorAnalysisInput(BaseModel):
    sector_name: str = Field(
        ..., 
        description="조회할 섹터 이름 (예: 'Technology', 'Energy', 'Healthcare')"
    )
    limit: int = Field(
        10,
        description="조회할 종목 개수 (기본값: 10)"
    )

class SectorAnalysisOutput:
    def __init__(
        self,
        agent: str,
        summary: str,
        tickers: Optional[List[str]] = None,
        avg_marketcap: Optional[float] = None,
        avg_dividend: Optional[float] = None,
        avg_price: Optional[float] = None,
        data: Optional[Any] = None
    ):
        self.agent = agent
        self.summary = summary
        self.tickers = tickers
        self.avg_marketcap = avg_marketcap
        self.avg_dividend = avg_dividend
        self.avg_price = avg_price
        self.data = data

class SectorAnalysisTool(BaseFinanceTool):
    BASE_URL = "https://financialmodelingprep.com/api/v3/stock-screener"

    def __init__(self, ai_chat_service):
        # 지연 임포트로 순환 참조 방지
        from service.llm.AIChat_service import AIChatService
        if not isinstance(ai_chat_service, AIChatService):
            raise TypeError("Expected AIChatService instance")
        self.ai_chat_service = ai_chat_service

    def get_data(self, **kwargs) -> SectorAnalysisOutput:
        try:
            params = SectorAnalysisInput(**kwargs)
        except Exception as e:
            return SectorAnalysisOutput(agent="error", summary=f"❌ 매개변수 오류: {e}")

        api_key = self.ai_chat_service.llm_config.API_Key.get("FMP_API_KEY")
        if not api_key:
            return SectorAnalysisOutput(agent="error", summary="❌ FMP_API_KEY가 설정돼 있지 않습니다.")

        params_dict = {
            "sector": params.sector_name,
            "apikey": api_key,
            "limit": params.limit
        }

        try:
            res = requests.get(self.BASE_URL, params=params_dict, timeout=5)
            res.raise_for_status()
            stocks = res.json()
            if not stocks:
                return SectorAnalysisOutput(agent="error", summary=f"📭 '{params.sector_name}' 섹터의 종목을 찾을 수 없습니다.")

            tickers = [s["symbol"] for s in stocks if "symbol" in s]
            marketcaps = [s.get("marketCap") for s in stocks if isinstance(s.get("marketCap"), (int, float))]
            dividends = [s.get("lastAnnualDividend") for s in stocks if isinstance(s.get("lastAnnualDividend"), (int, float))]
            prices = [s.get("price") for s in stocks if isinstance(s.get("price"), (int, float))]

            avg_marketcap = round(sum(marketcaps) / len(marketcaps), 2) if marketcaps else None
            avg_dividend = round(sum(dividends) / len(dividends), 4) if dividends else None
            avg_price = round(sum(prices) / len(prices), 2) if prices else None

            summary = (
                f"📊 '{params.sector_name}' 섹터 주요 종목: {', '.join(tickers)}\n"
                f"🏦 평균 시가총액: {avg_marketcap}, 평균 배당: {avg_dividend}, 평균 주가: {avg_price}"
            )

            return SectorAnalysisOutput(
                agent="SectorAnalysisTool",
                summary=summary,
                tickers=tickers,
                avg_marketcap=avg_marketcap,
                avg_dividend=avg_dividend,
                avg_price=avg_price,
                data=stocks
            )
        except Exception as e:
            return SectorAnalysisOutput(agent="error", summary=f"⚠️ 섹터 분석 오류: {e}")