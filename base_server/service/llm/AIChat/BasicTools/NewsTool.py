import os
import requests
from typing import Optional, List, Dict, Any
from service.llm.AIChat.BaseFinanceTool import BaseFinanceTool
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
        super().__init__(
            agent=agent,
            summary=summary,
            news=news,
            data=data,
        )

class NewsTool(BaseFinanceTool):
    BASE_URL = "https://gnews.io/api/v4/search"

    def __init__(self, ai_chat_service):
        from service.llm.AIChat_service import AIChatService
        if not isinstance(ai_chat_service, AIChatService):
            raise TypeError("Expected AIChatService instance")
        self.ai_chat_service = ai_chat_service

    # **params로 받도록 변경!
    def get_data(self, **kwargs) -> NewsOutput:
        try:
            input = NewsInput(**kwargs)
        except Exception as e:
            return NewsOutput(agent="error", summary=f"❌ 매개변수 오류: {e}")

        api_key = self.ai_chat_service.llm_config.API_Key.get("NEWSAPI_KEY")
        params = {
            "q": input.query,
            "lang": "en",
            "token": api_key,
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
                "date": a.get("publishedAt", "")[:10],
                "sentiment": "positive" if any(keyword in a.get("title", "").lower() for keyword in ["상승", "호재", "증가", "강세"]) else \
                             "negative" if any(keyword in a.get("title", "").lower() for keyword in ["하락", "악재", "감소", "약세"]) else "neutral"
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
