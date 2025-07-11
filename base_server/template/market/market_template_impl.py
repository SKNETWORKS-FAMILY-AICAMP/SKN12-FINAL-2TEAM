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
            
            # 1. 종목 검색 DB 프로시저 호출
            search_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_search_securities",
                (request.query, request.exchange, request.sector, request.limit)
            )
            
            if not search_result:
                response.securities = []
                response.total_count = 0
                response.errorCode = 0
                return response
            
            # 2. 검색 기록 저장
            await db_service.call_shard_procedure(
                shard_id,
                "fp_save_search_history",
                (account_db_key, request.query, "SECURITIES")
            )
            
            # 3. DB 결과를 바탕으로 응답 생성
            from template.market.common.market_model import SecurityInfo
            securities_data = search_result[0] if isinstance(search_result[0], list) else search_result
            total_count_data = search_result[1] if len(search_result) > 1 else {}
            
            response.securities = []
            for security in securities_data:
                response.securities.append(SecurityInfo(
                    symbol=security.get('symbol'),
                    name=security.get('name'),
                    exchange=security.get('exchange'),
                    sector=security.get('sector'),
                    industry=security.get('industry'),
                    market_cap=security.get('market_cap', 0),
                    currency=security.get('currency', 'KRW'),
                    description=security.get('description', '')
                ))
            
            response.total_count = total_count_data.get('total_count', len(response.securities))
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
            
            db_service = ServiceContainer.get_database_service()
            
            # 1. 가격 데이터 조회 DB 프로시저 호출
            price_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_get_price_data",
                (json.dumps(request.symbols), request.period, request.interval)
            )
            
            # 2. 기술적 지표 조회 DB 프로시저 호출
            tech_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_get_technical_indicators",
                (json.dumps(request.symbols),)
            )
            
            # 3. 응답 데이터 구성
            from template.market.common.market_model import PriceData, TechnicalIndicators
            
            response.price_data = {}
            if price_result:
                for price_item in price_result:
                    symbol = price_item.get('symbol')
                    if symbol not in response.price_data:
                        response.price_data[symbol] = []
                    
                    response.price_data[symbol].append(PriceData(
                        symbol=symbol,
                        timestamp=str(price_item.get('timestamp')),
                        open=float(price_item.get('open_price', 0)),
                        high=float(price_item.get('high_price', 0)),
                        low=float(price_item.get('low_price', 0)),
                        close=float(price_item.get('close_price', 0)),
                        volume=int(price_item.get('volume', 0)),
                        change=float(price_item.get('change_amount', 0)),
                        change_percent=float(price_item.get('change_rate', 0))
                    ))
            
            response.technical_indicators = {}
            if tech_result:
                for tech_item in tech_result:
                    symbol = tech_item.get('symbol')
                    response.technical_indicators[symbol] = TechnicalIndicators(
                        symbol=symbol,
                        rsi=float(tech_item.get('rsi', 0)),
                        macd=float(tech_item.get('macd', 0)),
                        macd_signal=float(tech_item.get('macd_signal', 0)),
                        bollinger_upper=float(tech_item.get('bollinger_upper', 0)),
                        bollinger_middle=float(tech_item.get('bollinger_middle', 0)),
                        bollinger_lower=float(tech_item.get('bollinger_lower', 0)),
                        ma5=float(tech_item.get('ma5', 0)),
                        ma20=float(tech_item.get('ma20', 0)),
                        ma60=float(tech_item.get('ma60', 0))
                    )
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
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            db_service = ServiceContainer.get_database_service()
            
            # 1. 뉴스 데이터 조회 DB 프로시저 호출
            symbols_json = json.dumps(request.symbols) if request.symbols else None
            news_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_get_news",
                (symbols_json, request.category, request.page, request.limit)
            )
            
            if not news_result or len(news_result) < 3:
                response.news = []
                response.total_count = 0
                response.sentiment_summary = {"positive": 0.0, "negative": 0.0, "neutral": 0.0}
                response.errorCode = 0
                return response
            
            # 2. 응답 데이터 구성
            from template.market.common.market_model import NewsItem
            
            news_data = news_result[0] if isinstance(news_result[0], list) else news_result
            total_count_data = news_result[1] if len(news_result) > 1 else {}
            sentiment_data = news_result[2] if len(news_result) > 2 else {}
            
            response.news = []
            for news_item in news_data:
                response.news.append(NewsItem(
                    news_id=news_item.get('news_id'),
                    title=news_item.get('title'),
                    summary=news_item.get('summary'),
                    source=news_item.get('source'),
                    published_at=str(news_item.get('published_at')),
                    url=news_item.get('url'),
                    category=news_item.get('category'),
                    sentiment_score=float(news_item.get('sentiment_score', 0.0)),
                    related_symbols=json.loads(news_item.get('related_symbols', '[]'))
                ))
            
            response.total_count = total_count_data.get('total_count', len(response.news))
            response.sentiment_summary = {
                "positive": float(sentiment_data.get('positive_count', 0)),
                "negative": float(sentiment_data.get('negative_count', 0)),
                "neutral": float(sentiment_data.get('neutral_count', 0))
            }
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
            
            # 1. 시장 개요 데이터 조회 DB 프로시저 호출
            market_data = await db_service.call_shard_procedure(
                shard_id,
                "fp_get_market_overview",
                (json.dumps(request.indices),)
            )
            
            if not market_data:
                response.errorCode = 7001
                response.indices = {}
                response.top_gainers = []
                response.top_losers = []
                response.most_active = []
                response.market_sentiment = "NEUTRAL"
                return response
            
            # 2. 시장 분석 결과 저장
            analysis_data = {
                "indices": request.indices,
                "sentiment": "NEUTRAL",  # 실제로는 시장 데이터 기반 계산
                "analysis_time": str(datetime.now())
            }
            
            await db_service.call_shard_procedure(
                shard_id,
                "fp_save_market_analysis",
                (account_db_key, "OVERVIEW", json.dumps(analysis_data))
            )
            
            # 3. 응답 데이터 구성
            from template.market.common.market_model import PriceData
            
            response.indices = {}
            response.top_gainers = []
            response.top_losers = []
            response.most_active = []
            
            # 주요 지수 데이터 처리
            for market_item in market_data:
                symbol = market_item.get('symbol')
                if symbol in request.indices:
                    response.indices[symbol] = PriceData(
                        symbol=symbol,
                        name=market_item.get('name'),
                        close=float(market_item.get('current_price', 0)),
                        change=float(market_item.get('change_amount', 0)),
                        change_percent=float(market_item.get('change_rate', 0)),
                        volume=int(market_item.get('volume', 0))
                    )
                    
                    # 상승/하락 종목 분류 (간단한 예시)
                    change_rate = float(market_item.get('change_rate', 0))
                    if change_rate > 3.0:
                        response.top_gainers.append(response.indices[symbol])
                    elif change_rate < -3.0:
                        response.top_losers.append(response.indices[symbol])
                    
                    # 거래량 많은 종목
                    if int(market_item.get('volume', 0)) > 1000000:
                        response.most_active.append(response.indices[symbol])
            
            # 시장 심리 계산 (간단한 예시)
            total_change = sum(float(item.get('change_rate', 0)) for item in market_data)
            avg_change = total_change / len(market_data) if market_data else 0
            
            if avg_change > 1.0:
                response.market_sentiment = "BULLISH"
            elif avg_change < -1.0:
                response.market_sentiment = "BEARISH"
            else:
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