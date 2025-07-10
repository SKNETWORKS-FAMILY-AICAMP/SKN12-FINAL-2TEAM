from template.base.base_template import BaseTemplate
from template.market.common.market_serialize import (
    MarketSecuritySearchRequest, MarketSecuritySearchResponse,
    MarketPriceRequest, MarketPriceResponse,
    MarketNewsRequest, MarketNewsResponse,
    MarketOverviewRequest, MarketOverviewResponse
)
from service.core.logger import Logger
from service.service_container import ServiceContainer
import json
from datetime import datetime

class MarketTemplateImpl(BaseTemplate):
    def __init__(self):
        super().__init__()
    
    async def on_market_security_search_req(self, client_session, request: MarketSecuritySearchRequest):
        """종목 검색 요청 처리"""
        response = MarketSecuritySearchResponse()
        
        Logger.info(f"Market security search request: query={request.query}")
        
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            db_service = ServiceContainer.get_database_service()
            
            # TODO: 종목 검색 로직 구현
            # - 종목명, 티커 검색
            # - 섹터, 업종 필터링
            # - 인기도, 관련성 순 정렬
            
            # 검색 기록 저장
            await db_service.call_shard_procedure(
                shard_id,
                "fp_save_search_history",
                (account_db_key, request.query, "SECURITIES")
            )
            
            # 가데이터 응답
            response.securities = [
                {"symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ", "sector": "Technology"},
                {"symbol": "GOOGL", "name": "Alphabet Inc.", "exchange": "NASDAQ", "sector": "Technology"}
            ]
            response.total_count = 2
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            response.securities = []
            response.total_count = 0
            Logger.error(f"Market security search error: {e}")
        
        return response

    async def on_market_price_req(self, client_session, request: MarketPriceRequest):
        """시세 조회 요청 처리"""
        response = MarketPriceResponse()
        
        Logger.info(f"Market price request: symbols={request.symbols}")
        
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            # TODO: 시세 조회 로직 구현
            # - 실시간 가격 데이터 조회
            # - 기술적 지표 계산
            # - 차트 데이터 생성
            
            # 가데이터 응답
            response.price_data = {
                "AAPL": {"price": 150.0, "change": 2.5, "change_percent": 1.69},
                "GOOGL": {"price": 240.0, "change": -3.2, "change_percent": -1.31}
            }
            response.technical_indicators = {
                "AAPL": {"rsi": 65.5, "macd": 1.2, "ma20": 148.5},
                "GOOGL": {"rsi": 45.2, "macd": -0.8, "ma20": 242.3}
            }
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            response.price_data = {}
            response.technical_indicators = {}
            Logger.error(f"Market price error: {e}")
        
        return response

    async def on_market_news_req(self, client_session, request: MarketNewsRequest):
        """뉴스 조회 요청 처리"""
        response = MarketNewsResponse()
        
        Logger.info(f"Market news request: category={request.category}")
        
        try:
            # TODO: 뉴스 조회 로직 구현
            # - 뉴스 API 호출
            # - 감정 분석
            # - 종목 연관성 분석
            
            # 가데이터 응답
            response.news = [
                {"title": "Apple announces new product", "source": "Reuters", "sentiment": "POSITIVE"},
                {"title": "Tech stocks rally", "source": "Bloomberg", "sentiment": "POSITIVE"}
            ]
            response.total_count = 2
            response.sentiment_summary = {"positive": 2, "negative": 0, "neutral": 0}
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            response.news = []
            response.total_count = 0
            response.sentiment_summary = {}
            Logger.error(f"Market news error: {e}")
        
        return response

    async def on_market_overview_req(self, client_session, request: MarketOverviewRequest):
        """시장 개요 요청 처리"""
        response = MarketOverviewResponse()
        
        Logger.info(f"Market overview request: indices={request.indices}")
        
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            db_service = ServiceContainer.get_database_service()
            
            # TODO: 시장 개요 조회 로직 구현
            # - 주요 지수 데이터 조회
            # - 상승/하락 종목 분석
            # - 거래량 분석
            # - 시장 심리 분석
            
            # 시장 개요 데이터 조회
            market_data = await db_service.call_shard_procedure(
                shard_id,
                "fp_get_market_overview",
                (json.dumps(request.indices),)
            )
            
            # 시장 분석 결과 저장
            await db_service.call_shard_procedure(
                shard_id,
                "fp_save_market_analysis",
                (account_db_key, "OVERVIEW", json.dumps({
                    "indices": ["KOSPI", "KOSDAQ"],
                    "sentiment": "NEUTRAL",
                    "top_gainers_count": 150,
                    "top_losers_count": 120
                }))
            )
            
            # 가데이터 응답
            response.indices = {
                "KOSPI": {"value": 2500.0, "change": 15.2, "change_percent": 0.61},
                "KOSDAQ": {"value": 850.0, "change": -8.5, "change_percent": -0.99}
            }
            response.top_gainers = [{"symbol": "AAPL", "change_percent": 5.2}]
            response.top_losers = [{"symbol": "GOOGL", "change_percent": -3.1}]
            response.most_active = [{"symbol": "TSLA", "volume": 50000000}]
            response.market_sentiment = "NEUTRAL"
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            response.indices = {}
            response.top_gainers = []
            response.top_losers = []
            response.most_active = []
            response.market_sentiment = "NEUTRAL"
            Logger.error(f"Market overview error: {e}")
        
        return response