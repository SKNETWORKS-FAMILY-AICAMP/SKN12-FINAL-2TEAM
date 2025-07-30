import asyncio
import re
from typing import Dict, List, Optional
import aiohttp
from urllib.parse import quote
from dataclasses import dataclass
from service.cache.cache_service import CacheService
from service.core.logger import Logger

logger = Logger

@dataclass
class StockQuote:
    """주식 정보 데이터 클래스"""
    symbol: str
    name: str
    current_price: float
    change_amount: float
    change_percent: float
    volume: int
    open_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    market_cap: Optional[int] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    currency: str = "USD"
    exchange: str = "NASDAQ"

@dataclass
class SearchResult:
    """검색 결과 데이터 클래스"""
    errorCode: int
    securities: List[StockQuote]
    total_count: int
    message: str = ""

class YahooFinanceClient:
    """Yahoo Finance API 클라이언트"""
    
    def __init__(self, cache_service: CacheService):
        self.cache_service = cache_service
        self.base_url = "https://query2.finance.yahoo.com"
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limit_delay = 0.1
        self.timeout = 10
        self.max_retries = 3
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://finance.yahoo.com/',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers=self.headers
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.session:
            await self.session.close()

    async def _make_request(self, url: str, retries: int = 0) -> Optional[Dict]:
        """HTTP 요청 실행 (재시도 로직 및 속도 제한 포함)"""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        try:
            if retries > 0:
                await asyncio.sleep(self.rate_limit_delay * (2 ** retries))

            async with self.session.get(url) as response:
                if response.status == 403:
                    logger.warning(f"Rate limited for {url}")
                    if retries < self.max_retries:
                        await asyncio.sleep(2 ** retries)
                        return await self._make_request(url, retries + 1)
                    return None
                
                if response.status == 429:
                    retry_after = response.headers.get('Retry-After', '60')
                    wait_time = int(retry_after)
                    logger.warning(f"Rate limited, waiting {wait_time} seconds")
                    await asyncio.sleep(wait_time)
                    return await self._make_request(url, retries + 1)

                if response.status != 200:
                    logger.error(f"HTTP {response.status} for {url}")
                    return None

                return await response.json()

        except asyncio.TimeoutError:
            logger.error(f"Timeout for {url}")
            if retries < self.max_retries:
                return await self._make_request(url, retries + 1)
            return None
        except Exception as e:
            logger.error(f"Request failed for {url}: {e}")
            if retries < self.max_retries:
                return await self._make_request(url, retries + 1)
            return None

    def _encode_symbol(self, symbol: str) -> str:
        """심볼을 URL 인코딩"""
        print("DEBUG _encode_symbol type:", type(symbol), symbol)
        # 모든 가능한 타입을 str로 변환
        if symbol is None:
            return ""
        if isinstance(symbol, bytes):
            symbol = symbol.decode('utf-8')
        elif not isinstance(symbol, str):
            symbol = str(symbol)
        return quote(symbol, safe='')

    def _parse_quote_data(self, data: Dict) -> Optional[StockQuote]:
        """Yahoo Finance 인용 데이터 파싱"""
        try:
            chart = data.get('chart', {})
            result = chart.get('result', [{}])[0]
            meta = result.get('meta', {})
            indicators = result.get('indicators', {})
            quote = indicators.get('quote', [{}])[0]
            
            timestamp = result.get('timestamp', [])
            close = quote.get('close', [])
            open_prices = quote.get('open', [])
            high = quote.get('high', [])
            low = quote.get('low', [])
            volume = quote.get('volume', [])

            if not timestamp or not close:
                return None

            current_price = float(close[-1]) if close[-1] else 0
            open_price = float(open_prices[0]) if open_prices and open_prices[0] else current_price
            # Fix: filter out None values for max/min
            high_filtered = [h for h in high if h is not None]
            low_filtered = [l for l in low if l is not None]
            high_price = float(max(high_filtered)) if high_filtered else current_price
            low_price = float(min(low_filtered)) if low_filtered else current_price
            change_amount = current_price - open_price
            change_percent = (change_amount / open_price * 100) if open_price > 0 else 0
            total_volume = sum(v for v in volume if v) if volume else 0

            return StockQuote(
                symbol=meta.get('symbol', ''),
                name=meta.get('shortName', meta.get('longName', '')),
                current_price=current_price,
                change_amount=change_amount,
                change_percent=change_percent,
                volume=total_volume,
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                currency=meta.get('currency', 'USD'),
                exchange=meta.get('exchangeName', 'NASDAQ')
            )

        except Exception as e:
            logger.error(f"Failed to parse quote data: {e}")
            return None

    async def get_stock_detail(self, symbol: str) -> Optional[StockQuote]:
        """주식 상세 정보 조회"""
        # symbol 타입 강제 변환
        if symbol is None:
            return None
        if isinstance(symbol, bytes):
            symbol = symbol.decode('utf-8')
        elif not isinstance(symbol, str):
            symbol = str(symbol)
    
        try:
            encoded_symbol = self._encode_symbol(symbol)
            url = f"{self.base_url}/v8/finance/chart/{encoded_symbol}?range=1d&interval=1m&includePrePost=false"
            
            data = await self._make_request(url)
            if not data:
                return None

            result = self._parse_quote_data(data)
            if result is None:
                # 기본 StockQuote 객체 반환
                return StockQuote(
                    symbol=symbol,
                    name=symbol,
                    current_price=0.0,
                    change_amount=0.0,
                    change_percent=0.0,
                    volume=0,
                    currency="USD",
                    exchange="NASDAQ"
                )
            return result
        except Exception as e:
            logger.error(f"get_stock_detail error for {symbol}: {e}")
            return None

    async def search_stocks(self, query: str) -> SearchResult:
        """주식 검색 (한국어 지원)"""
        if not query.strip():
            # 검색어가 없으면 빈 결과 반환
            return SearchResult(
                errorCode=0,
                securities=[],
                total_count=0,
                message="Please enter a search query"
            )

        logger.info(f"Search query: '{query}'")

        try:
            search_url = f"{self.base_url}/v1/finance/search?q={quote(query)}&quotesCount=10&newsCount=0"
            data = await self._make_request(search_url)
            
            if not data:
                return SearchResult(
                    errorCode=0,
                    securities=[],
                    total_count=0,
                    message=f"No results found for '{query}'"
                )

            quotes = data.get('quotes', [])
            if not quotes:
                return SearchResult(
                    errorCode=0,
                    securities=[],
                    total_count=0,
                    message=f"No results found for '{query}'"
                )

            stocks = []
            for quote_data in quotes[:10]:
                symbol = quote_data.get('symbol')
                # symbol이 유효한지 확인
                if not symbol or not isinstance(symbol, str) or not symbol.strip():
                    continue  # 유효하지 않은 symbol은 건너뛰기
                    
                stock_detail = await self.get_stock_detail(symbol)
                if stock_detail:
                    stocks.append(stock_detail)
                else:
                    stocks.append(StockQuote(
                        symbol=symbol,
                        name=quote_data.get('longname', quote_data.get('shortname', symbol)),
                        current_price=quote_data.get('regularMarketPrice', 0.0),
                        change_amount=quote_data.get('regularMarketChange', 0.0),
                        change_percent=quote_data.get('regularMarketChangePercent', 0.0),
                        volume=quote_data.get('regularMarketVolume', 0),
                        open_price=quote_data.get('regularMarketOpen', None),
                        high_price=quote_data.get('regularMarketDayHigh', None),
                        low_price=quote_data.get('regularMarketDayLow', None),
                        market_cap=quote_data.get('marketCap'),
                        sector=quote_data.get('sector'),
                        industry=quote_data.get('industry'),
                        currency=quote_data.get('currency', 'USD'),
                        exchange=quote_data.get('exchange', 'NASDAQ')
                    ))

            return SearchResult(
                errorCode=0,
                securities=stocks,
                total_count=len(stocks)
            )

        except Exception as e:
            return SearchResult(
                errorCode=1,
                securities=[],
                total_count=0,
                message=f"Search failed: {str(e)}"
            )

 