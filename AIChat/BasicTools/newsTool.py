"""기업 관련 최신 뉴스를 가져오는 도구입니다.
이 도구는 GNews API를 사용하여 특정 키워드에 대한 최신 뉴스를"""
import os
import requests
from typing import Optional, List, Dict, Any
from AIChat.BaseFinanceTool import BaseFinanceTool
from pydantic import BaseModel, Field
class NewsInput(BaseModel):
    query: str = Field(..., description="검색할 뉴스 키워드 또는 종목 코드 (예: 'TSLA', '금리 인상')")
    k: int = Field(5, description="검색할 뉴스 개수 (기본값: 5)")

class NewsOutput(BaseModel):
    agent: str
    summary: str
    news: Optional[List[Dict[str, str]]] = None
    data: Optional[Any] = None
    def __init__(
        self,
        agent: str,
        summary: str,
        news: Optional[List[Dict[str, str]]] = None,
        data: Optional[Any] = None,
    ):
        self.agent = agent
        self.summary = summary
        self.news = news
        self.data = data


class NewsTool(BaseFinanceTool):
    BASE_URL = "https://gnews.io/api/v4/search"

    def __init__(self, api_key: Optional[str] = os.getenv("GNEWS_API_KEY")):
        super().__init__("GNEWS_API_KEY" if api_key is None else None)
        self.api_key = api_key or os.getenv("GNEWS_API_KEY")
        if not self.api_key:
            raise ValueError("❌ GNEWS_API_KEY가 설정돼 있지 않습니다.")

    def get_data(self, input: NewsInput) -> NewsOutput:
        params = {
            "q": input.query,
            "lang": "en",
            "token": self.api_key,
            "max": input.k
        }

        try:
            res = requests.get(self.BASE_URL, params=params, timeout=5)
            res.raise_for_status()
        except requests.RequestException as e:
            return NewsOutput(agent="error", summary=f"🌐 HTTP 오류: {e}")

        articles = res.json().get("articles", [])
        if not articles:
            return NewsOutput(agent="error", summary=f"📭 '{input.query}'에 대한 뉴스를 찾을 수 없습니다.")

        news_list = [
            {
                "title": a.get("title", "제목 없음"),
                "url": a.get("url", ""),
                "source": a.get("source", {}).get("name", "알 수 없음"),
                "date": a.get("publishedAt", "")[:10]
            }
            for a in articles
        ]

        summary = (
            f"📰 '{input.query}' 관련 최신 뉴스 {len(news_list)}건:\n" +
            "\n".join([f"- {n['title']} ({n['url']})" for n in news_list])
        )

        return NewsOutput(
            agent="NewsTool",
            summary=summary,
            news=[{"title": n["title"], "url": n["url"]} for n in news_list],
            data=news_list
        )