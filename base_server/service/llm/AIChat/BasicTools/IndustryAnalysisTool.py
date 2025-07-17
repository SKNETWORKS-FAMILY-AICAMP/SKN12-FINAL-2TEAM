"""산업(Industry)별 주요 종목(시가총액, 가격, 배당 등) 조회 도구"""
import requests
import os
from typing import List, Optional, Dict, Any
from service.llm.AIChat.BaseFinanceTool import BaseFinanceTool
from pydantic import BaseModel, Field
from service.llm.AIChat_service import AIChatService

class IndustryAnalysisInput(BaseModel):
    industry_name: str = Field(
        ..., 
        description="조회할 산업(인더스트리) 이름 (예: 'Semiconductors', 'Software - Infrastructure')"
    )
    limit: int = Field(
        10,
        description="조회할 종목 개수 (기본값: 10)"
    )

class IndustryAnalysisOutput:
    def __init__(
        self,
        agent: str,
        summary: str,
        tickers: Optional[List[str]] = None,
        top_market_cap: Optional[str] = None,
        avg_market_cap: Optional[float] = None,
        avg_price: Optional[float] = None,
        avg_dividend: Optional[float] = None,
        countries: Optional[List[str]] = None,
        data: Optional[Any] = None
    ):
        self.agent = agent
        self.summary = summary
        self.tickers = tickers
        self.top_market_cap = top_market_cap
        self.avg_market_cap = avg_market_cap
        self.avg_price = avg_price
        self.avg_dividend = avg_dividend
        self.countries = countries
        self.data = data

class IndustryAnalysisTool(BaseFinanceTool):
    BASE_URL = "https://financialmodelingprep.com/api/v3/stock-screener"

    def __init__(self, ai_chat_service: AIChatService):
        self.ai_chat_service = ai_chat_service

    def get_data(self, **kwargs) -> IndustryAnalysisOutput:
        try:
            params = IndustryAnalysisInput(**kwargs)
        except Exception as e:
            return IndustryAnalysisOutput(agent="error", summary=f"❌ 매개변수 오류: {e}")

        api_key = self.ai_chat_service.llm_config.API_Key.FMP_API_KEY
        if not api_key:
            return IndustryAnalysisOutput(agent="error", summary="❌ FMP_API_KEY가 설정돼 있지 않습니다.")

        params_dict = {
            "industry": params.industry_name,
            "apikey": api_key,
            "limit": params.limit
        }

        try:
            res = requests.get(self.BASE_URL, params=params_dict, timeout=5)
            res.raise_for_status()
            stocks = res.json()
            if not stocks:
                return IndustryAnalysisOutput(agent="error", summary=f"📭 '{params.industry_name}' 인더스트리의 종목을 찾을 수 없습니다.")

            tickers = [s.get("symbol") for s in stocks if s.get("symbol")]
            market_caps = [s.get("marketCap") for s in stocks if isinstance(s.get("marketCap"), (int, float))]
            prices = [s.get("price") for s in stocks if isinstance(s.get("price"), (int, float))]
            dividends = [s.get("lastAnnualDividend") for s in stocks if isinstance(s.get("lastAnnualDividend"), (int, float))]
            countries = list({s.get("country", "N/A") for s in stocks})

            # 시가총액 최대 기업
            top_market_cap = None
            if market_caps:
                idx = market_caps.index(max(market_caps))
                top_market_cap = tickers[idx] if idx < len(tickers) else None

            avg_market_cap = round(sum(market_caps) / len(market_caps), 2) if market_caps else None
            avg_price = round(sum(prices) / len(prices), 2) if prices else None
            avg_dividend = round(sum(dividends) / len(dividends), 4) if dividends else None

            summary = (
                f"'{params.industry_name}' 인더스트리 주요 종목: {', '.join(tickers)}\n"
                f"🧮 평균 시가총액: {avg_market_cap}, 평균 가격: {avg_price}, 평균 배당: {avg_dividend}\n"
                f"🏆 시가총액 1위: {top_market_cap}\n"
                f"🌎 국가: {', '.join(countries)}"
            )

            return IndustryAnalysisOutput(
                agent="IndustryAnalysisTool",
                summary=summary,
                tickers=tickers,
                top_market_cap=top_market_cap,
                avg_market_cap=avg_market_cap,
                avg_price=avg_price,
                avg_dividend=avg_dividend,
                countries=countries,
                data=stocks
            )

        except Exception as e:
            return IndustryAnalysisOutput(agent="error", summary=f"⚠️ 인더스트리 분석 오류: {e}")
