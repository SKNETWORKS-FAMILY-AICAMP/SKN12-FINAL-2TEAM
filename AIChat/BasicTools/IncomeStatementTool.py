"""기업의 재무제표를 가져오는 도구입니다.
이 도구는 Financial Modeling Prep API를 사용하여 기업의 손익계산서(income statement)를 가져옵니다."""
import requests
from AIChat.BaseFinanceTool import BaseFinanceTool

class IncomeStatementTool(BaseFinanceTool):
    BASE_URL = "https://financialmodelingprep.com/api/v3/income-statement"

    def __init__(self, api_key_name: str = "FMP_API_KEY"):
        super().__init__(key_name=api_key_name)
        if not self.api_key:
            raise ValueError("❌ FMP_API_KEY가 설정돼 있지 않습니다.")

    def get_data(self, ticker: str, limit: int = 1) -> str:
        url = f"{self.BASE_URL}/{ticker.upper()}"
        params = {"apikey": self.api_key, "limit": limit}

        try:
            res = requests.get(url, params=params, timeout=5)
            res.raise_for_status()
        except requests.RequestException as e:
            return f"🌐 HTTP 오류 (재무제표): {e}"

        data = res.json()
        if not data:
            return f"📭 {ticker}의 재무제표 데이터가 없습니다."

        lines = [f"📊 [ {ticker.upper()} ] 최근 {len(data)}개 재무제표 요약"]
        for report in data:
            date = report.get("date", "N/A")
            revenue = report.get("revenue", "N/A")
            net_income = report.get("netIncome", "N/A")
            eps = report.get("eps", "N/A")
            lines.append(
                f"- 📅 {date}\n"
                f"  매출액: ${revenue:,}\n"
                f"  순이익: ${net_income:,}\n"
                f"  EPS: {eps}"
            )

        return "\n\n".join(lines)
