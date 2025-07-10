"""거시경제(MacroEconomic) 데이터를 조회하고 요약해주는 도구"""
import requests
import os
import time
import random
from typing import List, Optional, Dict, Any
from BaseFinanceTool import BaseFinanceTool
from pydantic import BaseModel, Field

class MacroEconomicInput(BaseModel):
    series_ids: List[str] = Field(
        ...,
        description=(
            "FRED(Federal Reserve Economic Data)의 시리즈 ID 리스트.\n"
            "예시: ['CPIAUCSL', 'FEDFUNDS', 'UNRATE']"
        )
    )
def get_with_retry(url, max_retries=3, backoff=2):
    for i in range(max_retries):
        try:
            resp = requests.get(url)
            if resp.status_code == 200:
                return resp
            print(f"[MacroEconomicTool] {url} status {resp.status_code}, retry {i+1}")
        except Exception as e:
            print(f"[MacroEconomicTool] {url} 예외: {e}, retry {i+1}")
        time.sleep(backoff ** i + random.uniform(0, 1))
    return resp  # 마지막 응답 반환

class MacroEconomicSeries:
    def __init__(
        self,
        series_id: str,
        latest_value: Optional[float],
        observation_date: Optional[str],
        units: Optional[str]
    ):
        self.series_id = series_id
        self.latest_value = latest_value
        self.observation_date = observation_date
        self.units = units

class MacroEconomicOutput:
    def __init__(
        self,
        agent: str,
        summary: str,
        series: List[MacroEconomicSeries],
        data: Optional[Any] = None
    ):
        self.agent = agent
        self.summary = summary
        self.series = series
        self.data = data

class MacroEconomicTool(BaseFinanceTool):
    def get_data(self, series_ids: List[str]) -> MacroEconomicOutput:
        try:
            print(f"[MacroEconomicTool] Processing: {series_ids}")
            api_key = self.api_key or os.getenv("FRED_API_KEY")
            if not api_key:
                return MacroEconomicOutput(agent="error", summary="FRED API 키가 없습니다.", series=[], data=None)

            series_list = []

            for sid in series_ids:
                url = (
                    f"https://api.stlouisfed.org/fred/series/observations"
                    f"?series_id={sid}&api_key={api_key}&file_type=json&sort_order=desc&limit=1"
                )

                resp = get_with_retry(url)
                if resp.status_code != 200:
                    series_list.append({
                        "series_id": sid,
                        "latest_value": None,
                        "observation_date": None,
                        "units": None
                    })
                    continue

                obs = resp.json().get("observations", [])
                if obs:
                    latest = obs[0]
                    value = float(latest["value"]) if latest["value"] not in ("", ".") else None
                    date = latest["date"]
                    units = resp.json().get("units", "")
                else:
                    value, date, units = None, None, None

                series_list.append({
                    "series_id": sid,
                    "latest_value": value,
                    "observation_date": date,
                    "units": units
                })

            summary = "📈 거시경제 주요 지표:\n" + "\n".join(
                [f"- {s['series_id']}: {s['latest_value']} ({s['observation_date']})" for s in series_list]
            )

            return MacroEconomicOutput(
                agent="MacroEconomicTool",
                summary=summary,
                series=[MacroEconomicSeries(**s) for s in series_list],
                data=series_list
            )

        except Exception as e:
            print(f"[MacroEconomicTool] 오류: {e}")
            return MacroEconomicOutput(agent="error", summary=f"거시경제 데이터 오류: {e}", series=[], data=None)
