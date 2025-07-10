import requests
from AIChat.BaseFinanceTool import BaseFinanceTool
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class FinancialStatementParams(BaseModel):
    ticker: str = Field(..., description="조회할 미국 주식의 종목 코드 (예: AAPL)")
    period: str = Field("annual", description="조회 주기: 'annual' 또는 'quarter'")
    limit: int = Field(5, description="조회할 기간 개수 (최대 120)")


class FinancialStatementOutput:
    summary: str
    data: List[Dict[str, Any]]
    statement_type: str
    ticker: str
    period: Optional[str] = None

    def __init__(
        self,
        summary: str,
        data: List[Dict[str, Any]],
        statement_type: str,
        ticker: str,
        period: Optional[str] = None
    ):
        self.summary = summary
        self.data = data
        self.statement_type = statement_type
        self.ticker = ticker
        self.period = period


class FinancialStatementTool(BaseFinanceTool):
    SUPPORTED_TYPES = {
        "income-statement": "손익계산서",
        "balance-sheet-statement": "대차대조표",
        "cash-flow-statement": "현금흐름표",
        "ratios": "재무 비율",
        "key-metrics": "핵심 지표",
        "financial-growth": "성장률",
        "enterprise-values": "기업가치"
    }
    BASE_URL = "https://financialmodelingprep.com/api/v3"

    def __init__(self, statement_type: str, api_key_name: str = "FMP_API_KEY"):
        super().__init__(key_name=api_key_name)
        if not self.api_key:
            raise ValueError("❌ FMP_API_KEY가 설정돼 있지 않습니다.")

        statement_type = statement_type.lower()
        if statement_type not in self.SUPPORTED_TYPES:
            raise ValueError(f"❌ 지원하지 않는 유형입니다: {statement_type}")
        self.statement_type = statement_type

    @staticmethod
    def format_number(val):
        try:
            if val in (None, '', '.', 'N/A'):
                return str(val)
            if isinstance(val, str) and val.replace('.', '', 1).isdigit():
                val = float(val)
            return f"{val:,.0f}" if isinstance(val, (int, float)) else str(val)
        except Exception:
            return str(val)

    def get_data(self, **kwargs) -> FinancialStatementOutput:
        try:
            params = FinancialStatementParams(**kwargs)
        except Exception as e:
            return FinancialStatementOutput(
                summary=f"❌ 매개변수 오류: {e}",
                data=[],
                statement_type=self.statement_type,
                ticker=kwargs.get("ticker", "UNKNOWN"),
                period=kwargs.get("period", "annual")
            )

        ticker = params.ticker.upper()
        period = params.period
        limit = params.limit

        url = f"{self.BASE_URL}/{self.statement_type}/{ticker}"
        req_params = {
            "apikey": self.api_key,
            "limit": limit
        }

        if self.statement_type in [
            "income-statement", "balance-sheet-statement",
            "cash-flow-statement", "ratios", "key-metrics", "financial-growth"
        ]:
            req_params["period"] = period

        try:
            res = requests.get(url, params=req_params, timeout=5)
            res.raise_for_status()
        except requests.RequestException as e:
            return FinancialStatementOutput(
                summary=f"🌐 HTTP 오류: {e}",
                data=[],
                statement_type=self.statement_type,
                ticker=ticker,
                period=period
            )

        data = res.json()
        if not data:
            return FinancialStatementOutput(
                summary=f"📭 {ticker}의 {self.SUPPORTED_TYPES[self.statement_type]} 데이터가 없습니다.",
                data=[],
                statement_type=self.statement_type,
                ticker=ticker,
                period=period
            )

        fn = self.format_number  # static 메서드라서 이렇게 편하게 씁니다

        lines = [f"📊 [ {ticker} ] 최근 {len(data)}개 {period} {self.SUPPORTED_TYPES[self.statement_type]} 요약"]
        for report in data:
            date = report.get("date", "N/A")
            line = f"- 📅 {date}"

            if self.statement_type == "income-statement":
                line += f"\n  매출액: ${fn(report.get('revenue', 'N/A'))}" \
                        f"\n  순이익: ${fn(report.get('netIncome', 'N/A'))}" \
                        f"\n  EPS: {report.get('eps', 'N/A')}"
            elif self.statement_type == "balance-sheet-statement":
                line += f"\n  총자산: ${fn(report.get('totalAssets', 'N/A'))}" \
                        f"\n  총부채: ${fn(report.get('totalLiabilities', 'N/A'))}" \
                        f"\n  자본: ${fn(report.get('totalEquity', 'N/A'))}"
            elif self.statement_type == "cash-flow-statement":
                line += f"\n  영업현금흐름: ${fn(report.get('operatingCashFlow', 'N/A'))}" \
                        f"\n  투자현금흐름: ${fn(report.get('investingCashFlow', 'N/A'))}" \
                        f"\n  재무현금흐름: ${fn(report.get('financingCashFlow', 'N/A'))}"
            elif self.statement_type == "ratios":
                line += f"\n  PER: {report.get('priceEarningsRatio', 'N/A')}" \
                        f"\n  ROE: {report.get('returnOnEquity', 'N/A')}" \
                        f"\n  유동비율: {report.get('currentRatio', 'N/A')}"
            elif self.statement_type == "key-metrics":
                line += f"\n  시가총액: ${fn(report.get('marketCap', 'N/A'))}" \
                        f"\n  영업마진: {report.get('operatingMargin', 'N/A')}" \
                        f"\n  배당수익률: {report.get('dividendYield', 'N/A')}"
            elif self.statement_type == "financial-growth":
                line += f"\n  매출 성장률: {report.get('revenueGrowth', 'N/A')}" \
                        f"\n  순이익 성장률: {report.get('netIncomeGrowth', 'N/A')}" \
                        f"\n  EPS 성장률: {report.get('epsgrowth', 'N/A')}"
            elif self.statement_type == "enterprise-values":
                line += f"\n  EV: ${fn(report.get('enterpriseValue', 'N/A'))}" \
                        f"\n  EV/EBITDA: {report.get('evToEbitda', 'N/A')}" \
                        f"\n  Net Debt: ${fn(report.get('netDebt', 'N/A'))}"

            lines.append(line)

        summary = "\n\n".join(lines)

        return FinancialStatementOutput(
            summary=summary,
            data=data,
            statement_type=self.statement_type,
            ticker=ticker,
            period=period
        )
