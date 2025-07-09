"""섹터별 주요 종목(PER, PBR 등) 조회 도구"""
import requests
import os
from typing import List, Optional, Dict, Any
from BaseFinanceTool import BaseFinanceTool


class SectorAnalysisOutput:
    def __init__(
        self,
        agent: str,
        summary: str,
        tickers: Optional[List[str]] = None,
        avg_per: Optional[float] = None,
        avg_pbr: Optional[float] = None,
        data: Optional[Any] = None
    ):
        self.agent = agent
        self.summary = summary
        self.tickers = tickers
        self.avg_per = avg_per
        self.avg_pbr = avg_pbr
        self.data = data
class SectorAnalysisTool(BaseFinanceTool):
    BASE_URL = "https://financialmodelingprep.com/api/v3/stock-screener"

    def get_data(self, sector_name: str, limit: int = 10) -> SectorAnalysisOutput:
        try:
            api_key = self.api_key or os.getenv("FMP_API_KEY")
            if not api_key:
                return SectorAnalysisOutput(agent="error", summary="❌ FMP_API_KEY가 설정돼 있지 않습니다.")

            params = {
                "sector": sector_name,
                "apikey": api_key,
                "limit": limit
            }

            res = requests.get(self.BASE_URL, params=params, timeout=5)
            res.raise_for_status()

            stocks = res.json()
            if not stocks:
                return SectorAnalysisOutput(agent="error", summary=f"📭 '{sector_name}' 섹터의 종목을 찾을 수 없습니다.")

            tickers = [s["symbol"] for s in stocks if "symbol" in s]
            pers = [s.get("pe") for s in stocks if isinstance(s.get("pe"), (int, float))]
            pbrs = [s.get("pb") for s in stocks if isinstance(s.get("pb"), (int, float))]

            avg_per = round(sum(pers) / len(pers), 2) if pers else None
            avg_pbr = round(sum(pbrs) / len(pbrs), 2) if pbrs else None

            summary = (
                f"📊 '{sector_name}' 섹터 주요 종목: {', '.join(tickers)}\n"
                f"📈 평균 PER: {avg_per}, 평균 PBR: {avg_pbr}"
            )

            return SectorAnalysisOutput(
                agent="SectorAnalysisTool",
                summary=summary,
                tickers=tickers,
                avg_per=avg_per,
                avg_pbr=avg_pbr,
                data=stocks
            )

        except Exception as e:
            return SectorAnalysisOutput(agent="error", summary=f"⚠️ 섹터 분석 오류: {e}")
