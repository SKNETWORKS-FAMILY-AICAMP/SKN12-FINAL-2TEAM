import requests
from AIChat.BaseFinanceTool import BaseFinanceTool
from pydantic import BaseModel, Field

class FinancialStatementParams(BaseModel):
    ticker: str = Field(..., description="조회할 미국 주식의 종목 코드 (예: AAPL)")
    period: str = Field("annual", description="조회 주기: 'annual' 또는 'quarter'")
    limit: int = Field(5, description="조회할 기간 개수 (최대 120)")

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

    def get_data(self, ticker: str, period: str = "annual", limit: int = 120) -> str:
        url = f"{self.BASE_URL}/{self.statement_type}/{ticker.upper()}"
        params = {
            "apikey": self.api_key,
            "limit": limit
        }

        if self.statement_type in [
            "income-statement", "balance-sheet-statement",
            "cash-flow-statement", "ratios", "key-metrics", "financial-growth"
        ]:
            params["period"] = period

        try:
            res = requests.get(url, params=params, timeout=5)
            res.raise_for_status()
        except requests.RequestException as e:
            return f"🌐 HTTP 오류: {e}"

        data = res.json()
        if not data:
            return f"📭 {ticker}의 {self.SUPPORTED_TYPES[self.statement_type]} 데이터가 없습니다."

        lines = [f"📊 [ {ticker.upper()} ] 최근 {len(data)}개 {period} {self.SUPPORTED_TYPES[self.statement_type]} 요약"]

        for report in data:
            date = report.get("date", "N/A")
            line = f"- 📅 {date}"

            if self.statement_type == "income-statement":
                line += f"\n  매출액: ${report.get('revenue', 'N/A'):,}" \
                        f"\n  순이익: ${report.get('netIncome', 'N/A'):,}" \
                        f"\n  EPS: {report.get('eps', 'N/A')}"
            elif self.statement_type == "balance-sheet-statement":
                line += f"\n  총자산: ${report.get('totalAssets', 'N/A'):,}" \
                        f"\n  총부채: ${report.get('totalLiabilities', 'N/A'):,}" \
                        f"\n  자본: ${report.get('totalEquity', 'N/A'):,}"
            elif self.statement_type == "cash-flow-statement":
                line += f"\n  영업현금흐름: ${report.get('operatingCashFlow', 'N/A'):,}" \
                        f"\n  투자현금흐름: ${report.get('investingCashFlow', 'N/A'):,}" \
                        f"\n  재무현금흐름: ${report.get('financingCashFlow', 'N/A'):,}"
            elif self.statement_type == "ratios":
                line += f"\n  PER: {report.get('priceEarningsRatio', 'N/A')}" \
                        f"\n  ROE: {report.get('returnOnEquity', 'N/A')}" \
                        f"\n  유동비율: {report.get('currentRatio', 'N/A')}"
            elif self.statement_type == "key-metrics":
                line += f"\n  시가총액: ${report.get('marketCap', 'N/A'):,}" \
                        f"\n  영업마진: {report.get('operatingMargin', 'N/A')}" \
                        f"\n  배당수익률: {report.get('dividendYield', 'N/A')}"
            elif self.statement_type == "financial-growth":
                line += f"\n  매출 성장률: {report.get('revenueGrowth', 'N/A')}" \
                        f"\n  순이익 성장률: {report.get('netIncomeGrowth', 'N/A')}" \
                        f"\n  EPS 성장률: {report.get('epsgrowth', 'N/A')}"
            elif self.statement_type == "enterprise-values":
                line += f"\n  EV: ${report.get('enterpriseValue', 'N/A'):,}" \
                        f"\n  EV/EBITDA: {report.get('evToEbitda', 'N/A')}" \
                        f"\n  Net Debt: ${report.get('netDebt', 'N/A'):,}"

            lines.append(line)

        return "\n\n".join(lines)
