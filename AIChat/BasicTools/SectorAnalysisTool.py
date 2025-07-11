"""섹터별 주요 종목(PER, PBR 등) 조회 도구"""
import requests
import os
from typing import List, Optional, Dict, Any
from AIChat.BaseFinanceTool import BaseFinanceTool
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
        avg_per: Optional[float] = None,
        avg_pbr: Optional[float] = None,
        avg_roe: Optional[float] = None,
        sector_performance: Optional[float] = None,
        data: Optional[Any] = None
    ):
        self.agent = agent
        self.summary = summary
        self.tickers = tickers
        self.avg_per = avg_per
        self.avg_pbr = avg_pbr
        self.avg_roe = avg_roe
        self.sector_performance = sector_performance
        self.data = data
class SectorAnalysisTool(BaseFinanceTool):
    BASE_URL = "https://financialmodelingprep.com/api/v3/stock-screener"

    def get_data(self, **kwargs) -> SectorAnalysisOutput:
        try:
            # kwargs를 pydantic 모델로 변환 (필수!)
            params = SectorAnalysisInput(**kwargs)
        except Exception as e:
            return SectorAnalysisOutput(agent="error", summary=f"❌ 매개변수 오류: {e}")

        api_key = self.api_key or os.getenv("FMP_API_KEY")
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
            pers = [s.get("pe") for s in stocks if isinstance(s.get("pe"), (int, float))]
            pbrs = [s.get("pb") for s in stocks if isinstance(s.get("pb"), (int, float))]
            roes = [s.get("roe") for s in stocks if isinstance(s.get("roe"), (int, float))]
            avg_per = round(sum(pers) / len(pers), 2) if pers else None
            avg_pbr = round(sum(pbrs) / len(pbrs), 2) if pbrs else None
            avg_roe = round(sum(roes) / len(roes), 4) if roes else None
            perf_6m = [s.get("priceChange6M") for s in stocks if isinstance(s.get("priceChange6M"), (int, float))]
            sector_performance = round(sum(perf_6m) / len(perf_6m), 4) if perf_6m else None

            summary = (
                f"📊 '{params.sector_name}' 섹터 주요 종목: {', '.join(tickers)}\n"
                f"📈 평균 PER: {avg_per}, 평균 PBR: {avg_pbr}, 평균 ROE: {avg_roe}\n"
                f"📉 섹터 6개월 수익률(평균): {sector_performance}"
            )

            return SectorAnalysisOutput(
                agent="SectorAnalysisTool",
                summary=summary,
                tickers=tickers,
                avg_per=avg_per,
                avg_pbr=avg_pbr,
                avg_roe=avg_roe,
                sector_performance=sector_performance,
                data=stocks
            )

        except Exception as e:
            return SectorAnalysisOutput(agent="error", summary=f"⚠️ 섹터 분석 오류: {e}")