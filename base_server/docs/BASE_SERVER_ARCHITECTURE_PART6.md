# Base Server Architecture Documentation - Part 6: 외부 서비스 & 검색 시스템

## 목차
1. [외부 서비스 아키텍처](#외부-서비스-아키텍처)
2. [ExternalService 구현](#externalservice-구현)
3. [HTTP 클라이언트 고급 기능](#http-클라이언트-고급-기능)
4. [검색 시스템 아키텍처](#검색-시스템-아키텍처)
5. [OpenSearch 클라이언트](#opensearch-클라이언트)
6. [API 통합 패턴](#api-통합-패턴)
7. [모니터링 및 장애 복구](#모니터링-및-장애-복구)

---

## 외부 서비스 아키텍처

### 외부 API 통합 전략

Base Server는 다양한 외부 API를 통합하여 금융 서비스에 필요한 데이터를 제공합니다.

```
┌─────────────────────────────────────────────────────────────┐
│                    ExternalService                          │
│                  (Static Methods)                           │
├─────────────────────────────────────────────────────────────┤
│  API Management      │  Connection Pool                     │
│  ┌─────────────────┐ │  ┌──────────────────────────────────┐ │
│  │ - stock_market  │ │  │ HttpExternalClient Pool          │ │
│  │ - news          │ │  │ - Connection Pooling             │ │
│  │ - exchange_rate │ │  │ - Circuit Breaker                │ │
│  │ - weather       │ │  │ - Retry Logic                    │ │
│  └─────────────────┘ │  │ - Health Check                   │ │
├─────────────────────────────────────────────────────────────┤
│                Advanced Features                            │
│  ┌─────────────────┐ ┌──────────────────────────────────┐  │
│  │ Circuit Breaker │ │        Metrics & Monitoring      │  │
│  │ - CLOSED        │ │ - Success Rate                   │  │
│  │ - OPEN          │ │ - Response Time                  │  │
│  │ - HALF_OPEN     │ │ - Error Tracking                 │  │
│  └─────────────────┘ └──────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
           │                        │
┌─────────────────┐    ┌──────────────────────────────────┐
│  External APIs  │    │         HTTP/HTTPS               │
│  - Yahoo Finance│    │  - JSON/XML Response             │
│  - News APIs    │    │  - Authentication                │
│  - Currency API │    │  - Rate Limiting                 │
└─────────────────┘    └──────────────────────────────────┘
```

### 핵심 설계 특징

1. **API별 개별 설정**: 각 API마다 독립적인 설정 (URL, 인증, 타임아웃)
2. **연결 풀 관리**: aiohttp 기반 비동기 HTTP 연결 풀
3. **Circuit Breaker**: 장애 감지 및 자동 복구
4. **자동 재시도**: Exponential Backoff with Jitter
5. **메트릭 수집**: 성공률, 응답 시간, 오류율 추적

---

## ExternalService 구현

### 서비스 구조 분석

```python
class ExternalService:
    """External API 서비스 (정적 클래스) - 순수 라이브러리"""
    
    _config: Optional[ExternalConfig] = None
    _client_pool: Optional[IExternalClientPool] = None
    _initialized: bool = False
```

### 초기화 및 생명주기

#### 서비스 초기화
```python
@classmethod
async def init(cls, config: ExternalConfig):
    """서비스 초기화"""
    cls._config = config
    cls._client_pool = ExternalClientPool(config)
    
    # 모든 API 클라이언트 사전 시작
    for api_name in config.apis.keys():
        client = cls._client_pool.new(api_name)
        await client.start()
        Logger.info(f"External client initialized for API: {api_name}")
        
    cls._initialized = True
    Logger.info("External service initialized")
```

**특징:**
- 모든 API 클라이언트를 사전에 초기화
- 연결 풀을 미리 준비하여 첫 요청 시 지연 최소화
- 각 API별 독립적인 클라이언트 관리

#### 서비스 종료
```python
@classmethod
async def shutdown(cls):
    """서비스 종료"""
    if cls._initialized and cls._client_pool:
        try:
            # 모든 클라이언트 강제 종료
            await cls._client_pool.close_all()
            
            # 조금 더 대기하여 모든 연결이 정리되도록 함
            import asyncio
            await asyncio.sleep(0.1)
            
        except Exception as e:
            Logger.error(f"External service shutdown error: {e}")
        finally:
            cls._client_pool = None
            cls._initialized = False
            Logger.info("External service shutdown")
```

### API 요청 메서드

#### 표준 HTTP 메서드
```python
@classmethod
async def request(cls, api_name: str, method: str, url: str, **kwargs) -> Dict[str, Any]:
    """일반 API 요청"""
    client = cls.get_client(api_name)
    return await client.request(method, url, **kwargs)

@classmethod
async def get(cls, api_name: str, url: str, **kwargs) -> Dict[str, Any]:
    """GET 요청"""
    client = cls.get_client(api_name)
    return await client.get(url, **kwargs)

@classmethod
async def post(cls, api_name: str, url: str, **kwargs) -> Dict[str, Any]:
    """POST 요청"""
    client = cls.get_client(api_name)
    return await client.post(url, **kwargs)
```

#### 실제 사용 예시
```python
# 주식 시장 데이터 조회
market_data = await ExternalService.get(
    api_name="stock_market",
    url="/quote",
    params={"symbol": "AAPL", "interval": "1d"}
)

# 뉴스 데이터 검색
news_data = await ExternalService.post(
    api_name="news",
    url="/search",
    json={
        "query": "stock market",
        "language": "en",
        "sort": "publishedAt",
        "pageSize": 10
    }
)

# 환율 정보 조회
exchange_rate = await ExternalService.get(
    api_name="exchange_rate",
    url="/latest",
    params={"base": "USD", "symbols": "KRW,EUR,JPY"}
)
```

### 설정 관리

#### ExternalConfig 구조
```python
class ApiEndpointConfig(BaseModel):
    """API 엔드포인트 설정"""
    base_url: str
    api_key: Optional[str] = None
    headers: Dict[str, str] = {}
    timeout: int = 30
    retry_count: int = 3
    retry_delay: float = 1.0

class ExternalConfig(BaseModel):
    """External API 서비스 설정"""
    timeout: int = 30
    max_retries: int = 3
    proxy: Optional[ProxyConfig] = None
    
    apis: Dict[str, ApiEndpointConfig] = {
        "stock_market": ApiEndpointConfig(
            base_url="https://api.stock-market.com/v1",
            timeout=10,
            retry_count=2
        ),
        "news": ApiEndpointConfig(
            base_url="https://api.news-service.com/v1",
            timeout=15,
            retry_count=3
        ),
        "exchange_rate": ApiEndpointConfig(
            base_url="https://api.exchange-rates.com/v1",
            timeout=10,
            retry_count=2
        )
    }
```

**설정 특징:**
- API별 독립적인 타임아웃 및 재시도 설정
- 공통 프록시 설정 지원
- 개별 헤더 및 인증 키 관리

---

## HTTP 클라이언트 고급 기능

### HttpExternalClient 아키텍처

```python
class HttpExternalClient(IExternalClient):
    """HTTP External API 클라이언트 - Connection Pool, Health Check, Circuit Breaker 포함"""
    
    def __init__(self, api_name: str, api_config, proxy_config=None):
        self.api_name = api_name
        self.api_config = api_config
        self.proxy_config = proxy_config
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Circuit Breaker 설정
        self.circuit_config = CircuitBreakerConfig()
        self.metrics = ClientMetrics()
```

### Circuit Breaker 구현

#### 상태 관리
```python
class CircuitState(Enum):
    CLOSED = "closed"      # 정상 상태
    OPEN = "open"          # 차단 상태 
    HALF_OPEN = "half_open"  # 반개방 상태

@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5      # 실패 임계값
    timeout_seconds: int = 60       # 차단 시간
    success_threshold: int = 2      # 반개방 상태에서 성공 임계값
```

#### Circuit Breaker 로직
```python
def _can_execute_request(self) -> bool:
    """Circuit Breaker - 요청 실행 가능 여부 확인"""
    current_time = time.time()
    
    if self.metrics.circuit_breaker_state == CircuitState.CLOSED:
        return True
    elif self.metrics.circuit_breaker_state == CircuitState.OPEN:
        if (current_time - self.metrics.circuit_open_time) >= self.circuit_config.timeout_seconds:
            self.metrics.circuit_breaker_state = CircuitState.HALF_OPEN
            self.metrics.consecutive_successes = 0
            Logger.info(f"Circuit breaker changed to HALF_OPEN for API: {self.api_name}")
            return True
        return False
    elif self.metrics.circuit_breaker_state == CircuitState.HALF_OPEN:
        return True
    
    return False

def _record_success(self, response_time: float):
    """성공 기록 및 Circuit Breaker 상태 업데이트"""
    self.metrics.successful_requests += 1
    self.metrics.total_response_time += response_time
    self.metrics.consecutive_failures = 0
    
    if self.metrics.circuit_breaker_state == CircuitState.HALF_OPEN:
        self.metrics.consecutive_successes += 1
        if self.metrics.consecutive_successes >= self.circuit_config.success_threshold:
            self.metrics.circuit_breaker_state = CircuitState.CLOSED
            Logger.info(f"Circuit breaker changed to CLOSED for API: {self.api_name}")

def _record_failure(self):
    """실패 기록 및 Circuit Breaker 상태 업데이트"""
    self.metrics.failed_requests += 1
    self.metrics.consecutive_failures += 1
    self.metrics.consecutive_successes = 0
    
    if (self.metrics.circuit_breaker_state == CircuitState.CLOSED and 
        self.metrics.consecutive_failures >= self.circuit_config.failure_threshold):
        self.metrics.circuit_breaker_state = CircuitState.OPEN
        self.metrics.circuit_open_time = time.time()
        Logger.warn(f"Circuit breaker changed to OPEN for API: {self.api_name}")
    elif self.metrics.circuit_breaker_state == CircuitState.HALF_OPEN:
        self.metrics.circuit_breaker_state = CircuitState.OPEN
        self.metrics.circuit_open_time = time.time()
        Logger.warn(f"Circuit breaker changed to OPEN for API: {self.api_name}")
```

### 연결 풀 관리

#### 고급 연결 풀 설정
```python
async def start(self):
    """클라이언트 시작 - 개선된 Connection Pool 설정"""
    if self._session is None:
        # Connection Pool 설정
        connector_kwargs = {
            "limit": 100,              # 총 연결 수 제한
            "limit_per_host": 30,     # 호스트당 연결 수 제한
            "ttl_dns_cache": 300,     # DNS 캐시 TTL
            "use_dns_cache": True,
            "keepalive_timeout": 60,  # Keep-alive 타임아웃
            "enable_cleanup_closed": True
        }
        
        # 타임아웃 설정 (더 세분화)
        timeout = aiohttp.ClientTimeout(
            total=self.api_config.timeout,
            connect=10,      # 연결 타임아웃
            sock_read=30,    # 소켓 읽기 타임아웃
            sock_connect=10  # 소켓 연결 타임아웃
        )
        
        # 기본 헤더 설정
        headers = self.api_config.headers.copy()
        if hasattr(self.api_config, 'api_key') and self.api_config.api_key:
            headers['Authorization'] = f"Bearer {self.api_config.api_key}"
        
        headers['User-Agent'] = f"base_server-external-client/{self.api_name}"
        
        self._session = aiohttp.ClientSession(
            timeout=timeout,
            headers=headers,
            connector=aiohttp.TCPConnector(**connector_kwargs)
        )
```

### 재시도 및 백오프 전략

#### Exponential Backoff with Jitter
```python
def _calculate_backoff_delay(self, attempt: int) -> float:
    """Exponential Backoff 지연 시간 계산"""
    base_delay = getattr(self.api_config, 'retry_delay', 1.0)
    max_delay = 30.0  # 최대 30초
    
    # 2^attempt * base_delay + jitter
    delay = min(base_delay * (2 ** attempt), max_delay)
    
    # Jitter 추가 (delay의 ±25%)
    jitter = delay * 0.25 * (2 * random.random() - 1)
    return max(0.1, delay + jitter)

# 재시도 로직 구현
for attempt in range(max_attempts):
    try:
        # HTTP 요청 실행
        async with self._session.request(method=method, url=url, **kwargs) as response:
            if response.status == 200:
                response_time = time.time() - start_time
                self._record_success(response_time)
                return {"success": True, "data": data, "response_time": response_time}
            else:
                self._record_failure()
                return {"success": False, "status": response.status}
                
    except (asyncio.TimeoutError, aiohttp.ClientError) as e:
        self._record_failure()
        if attempt < self.api_config.retry_count:
            delay = self._calculate_backoff_delay(attempt)
            await asyncio.sleep(delay)
        
# 모든 재시도 실패
return {"success": False, "error": "All retries failed"}
```

---

## 검색 시스템 아키텍처

### SearchService 개요

OpenSearch(Elasticsearch) 기반 검색 엔진을 통합하여 문서 검색 및 인덱싱 기능을 제공합니다.

```
┌─────────────────────────────────────────────────────────────┐
│                    SearchService                            │
│                  (Static Methods)                           │
├─────────────────────────────────────────────────────────────┤
│  Index Management    │  Document Operations                 │
│  ┌─────────────────┐ │  ┌──────────────────────────────────┐ │
│  │ - create_index  │ │  │ - index_document                 │ │
│  │ - delete_index  │ │  │ - get_document                   │ │
│  │ - index_exists  │ │  │ - update_document                │ │
│  │ - mappings      │ │  │ - delete_document                │ │
│  └─────────────────┘ │  │ - bulk_index                     │ │
├─────────────────────────────────────────────────────────────┤
│                Search Operations                            │
│  ┌─────────────────┐ ┌──────────────────────────────────┐  │
│  │ - search        │ │        Advanced Features         │  │
│  │ - scroll_search │ │ - Connection Pooling             │  │
│  │ - aggregations  │ │ - Automatic Retry                │  │
│  │ - filtering     │ │ - Health Monitoring              │  │
│  └─────────────────┘ └──────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
           │                        │
┌─────────────────┐    ┌──────────────────────────────────┐
│   OpenSearch    │    │         Cluster                  │
│   - Indices     │    │  - Multiple Nodes               │
│   - Documents   │    │  - Load Balancing               │
│   - Mappings    │    │  - Health Monitoring            │
└─────────────────┘    └──────────────────────────────────┘
```

### 핵심 기능

1. **인덱스 관리**: 동적 인덱스 생성 및 스키마 관리
2. **문서 작업**: CRUD 작업 및 벌크 인덱싱
3. **검색 기능**: 전문 검색, 필터링, 집계
4. **클러스터 관리**: 노드 상태 모니터링 및 로드 밸런싱

---

## OpenSearch 클라이언트

### 클라이언트 구조

```python
class OpenSearchClient(ISearchClient):
    """OpenSearch 클라이언트 - 연결 관리, 재시도, 메트릭 포함"""
    
    def __init__(self, config):
        self.config = config
        self._client = None
        self.metrics = SearchMetrics()
        self.connection_state = ConnectionState.HEALTHY
        self._max_retries = getattr(config, 'max_retries', 3)
```

### 연결 관리

#### 고급 연결 설정
```python
async def _get_client(self):
    """OpenSearch 클라이언트 가져오기 (Enhanced connection management)"""
    if self._client is None:
        client_kwargs = {
            'hosts': self.config.hosts,
            'timeout': self.config.timeout,
            'max_retries': self._max_retries,
            'retry_on_timeout': True,
            'use_ssl': True,
            'verify_certs': False,
            'pool_maxsize': 20,
            'pool_block': True
        }
        
        # 인증 설정
        if self.config.username and self.config.password:
            client_kwargs['http_auth'] = (self.config.username, self.config.password)
        
        # AWS 설정
        if self.config.aws_access_key_id and self.config.aws_secret_access_key:
            from requests_aws4auth import AWS4Auth
            auth = AWS4Auth(
                self.config.aws_access_key_id,
                self.config.aws_secret_access_key,
                self.config.aws_region,
                'es'
            )
            client_kwargs['http_auth'] = auth
        
        self._client = AsyncOpenSearch(**client_kwargs)
        await self._test_connection()
        Logger.info(f"OpenSearch client connected to {self.config.hosts}")
    
    return self._client
```

### 문서 작업

#### 개선된 인덱싱
```python
async def index_document(self, index: str, document: Dict[str, Any], doc_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """문서 인덱싱 (향상된 에러 처리 및 메트릭)"""
    start_time = time.time()
    self.metrics.total_operations += 1
    self.metrics.last_operation_time = start_time
    
    for attempt in range(self._max_retries):
        try:
            client = await self._get_client()
            
            index_kwargs = {
                'index': index,
                'body': document,
                **kwargs
            }
            
            if doc_id:
                index_kwargs['id'] = doc_id
            
            response = await client.index(**index_kwargs)
            
            # 성공 메트릭
            index_time = time.time() - start_time
            self.metrics.successful_operations += 1
            self.metrics.total_index_time += index_time
            self.metrics.documents_indexed += 1
            
            return {
                "success": True,
                "index": index,
                "doc_id": response.get('_id'),
                "index_time": index_time,
                "attempt": attempt + 1,
                "response": response
            }
            
        except (ConnectionError, TransportError) as e:
            self.metrics.index_errors += 1
            if attempt < self._max_retries - 1:
                delay = self._retry_delay_base * (2 ** attempt) + random.uniform(0, 1)
                await asyncio.sleep(delay)
            else:
                Logger.error(f"OpenSearch index_document failed after {self._max_retries} attempts")
        
    return {"success": False, "error": "Index failed after all retries"}
```

#### 고급 검색
```python
async def search(self, index: str, query: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """검색 (향상된 에러 처리 및 메트릭)"""
    start_time = time.time()
    self.metrics.total_operations += 1
    
    for attempt in range(self._max_retries):
        try:
            client = await self._get_client()
            
            response = await client.search(
                index=index,
                body=query,
                **kwargs
            )
            
            hits = response.get('hits', {})
            documents = [hit.get('_source') for hit in hits.get('hits', [])]
            total_hits = hits.get('total', {}).get('value', 0)
            
            # 성공 메트릭
            search_time = time.time() - start_time
            self.metrics.successful_operations += 1
            self.metrics.total_search_time += search_time
            self.metrics.documents_searched += total_hits
            
            return {
                "success": True,
                "index": index,
                "total": total_hits,
                "documents": documents,
                "search_time": search_time,
                "response": response
            }
            
        except (ConnectionError, TransportError) as e:
            self.metrics.search_errors += 1
            if attempt < self._max_retries - 1:
                delay = self._retry_delay_base * (2 ** attempt)
                await asyncio.sleep(delay)
        
    return {"success": False, "error": "Search failed after all retries"}
```

### 벌크 작업

#### 대용량 데이터 처리
```python
async def bulk_index(self, operations: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
    """벌크 인덱싱"""
    try:
        client = await self._get_client()
        
        response = await client.bulk(
            body=operations,
            **kwargs
        )
        
        errors = response.get('errors', False)
        items = response.get('items', [])
        
        Logger.info(f"OpenSearch bulk operation: {len(items)} items, errors: {errors}")
        return {
            "success": not errors,
            "items_count": len(items),
            "has_errors": errors,
            "response": response
        }
        
    except Exception as e:
        Logger.error(f"OpenSearch bulk_index failed: {e}")
        return {"success": False, "error": str(e)}
```

---

## API 통합 패턴

### 금융 데이터 API 통합

#### 주식 시장 데이터
```python
class StockMarketService:
    """주식 시장 데이터 서비스"""
    
    @staticmethod
    async def get_stock_quote(symbol: str) -> Dict[str, Any]:
        """주식 시세 조회"""
        try:
            result = await ExternalService.get(
                api_name="stock_market",
                url="/quote",
                params={"symbol": symbol.upper()}
            )
            
            if result["success"]:
                quote_data = result["data"]
                return {
                    "symbol": symbol,
                    "price": quote_data.get("regularMarketPrice"),
                    "change": quote_data.get("regularMarketChange"),
                    "change_percent": quote_data.get("regularMarketChangePercent"),
                    "volume": quote_data.get("regularMarketVolume"),
                    "timestamp": quote_data.get("regularMarketTime"),
                    "success": True
                }
            else:
                return {"success": False, "error": result["error"]}
                
        except Exception as e:
            Logger.error(f"Stock quote error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def get_market_summary() -> Dict[str, Any]:
        """시장 요약 정보"""
        major_indices = ["^GSPC", "^DJI", "^IXIC"]  # S&P 500, Dow Jones, NASDAQ
        summary = {"indices": {}, "success": True}
        
        for index in major_indices:
            quote = await StockMarketService.get_stock_quote(index)
            if quote["success"]:
                summary["indices"][index] = quote
            else:
                summary["success"] = False
        
        return summary
```

#### 뉴스 API 통합
```python
class NewsService:
    """뉴스 서비스"""
    
    @staticmethod
    async def get_financial_news(keywords: str = "stock market", limit: int = 10) -> Dict[str, Any]:
        """금융 뉴스 조회"""
        try:
            result = await ExternalService.post(
                api_name="news",
                url="/search",
                json={
                    "query": keywords,
                    "category": "business",
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": limit
                }
            )
            
            if result["success"]:
                articles = result["data"].get("articles", [])
                processed_news = []
                
                for article in articles:
                    processed_news.append({
                        "title": article.get("title"),
                        "description": article.get("description"),
                        "url": article.get("url"),
                        "published_at": article.get("publishedAt"),
                        "source": article.get("source", {}).get("name"),
                        "sentiment": "neutral"  # TODO: 감정 분석 추가
                    })
                
                return {
                    "success": True,
                    "news": processed_news,
                    "total": len(processed_news)
                }
            else:
                return {"success": False, "error": result["error"]}
                
        except Exception as e:
            Logger.error(f"News service error: {e}")
            return {"success": False, "error": str(e)}
```

### 검색 서비스 통합

#### 문서 인덱싱 및 검색
```python
class DocumentSearchService:
    """문서 검색 서비스"""
    
    @staticmethod
    async def index_financial_document(doc_id: str, title: str, content: str, category: str) -> Dict[str, Any]:
        """금융 문서 인덱싱"""
        document = {
            "title": title,
            "content": content,
            "category": category,
            "indexed_at": datetime.now().isoformat(),
            "word_count": len(content.split()),
            "language": "ko"
        }
        
        result = await SearchService.index_document(
            index="financial_documents",
            document=document,
            doc_id=doc_id
        )
        
        return result
    
    @staticmethod
    async def search_documents(query: str, category: Optional[str] = None, size: int = 10) -> Dict[str, Any]:
        """문서 검색"""
        search_query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["title^2", "content"],
                                "type": "best_fields"
                            }
                        }
                    ]
                }
            },
            "highlight": {
                "fields": {
                    "title": {},
                    "content": {"fragment_size": 150, "number_of_fragments": 3}
                }
            },
            "size": size,
            "sort": [{"_score": {"order": "desc"}}]
        }
        
        # 카테고리 필터 추가
        if category:
            search_query["query"]["bool"]["filter"] = [
                {"term": {"category": category}}
            ]
        
        result = await SearchService.search(
            index="financial_documents",
            query=search_query
        )
        
        if result["success"]:
            # 검색 결과 후처리
            processed_documents = []
            for doc in result["documents"]:
                processed_documents.append({
                    "title": doc.get("title"),
                    "content_preview": doc.get("content", "")[:200] + "...",
                    "category": doc.get("category"),
                    "indexed_at": doc.get("indexed_at"),
                    "relevance_score": "high"  # TODO: 실제 스코어 계산
                })
            
            return {
                "success": True,
                "documents": processed_documents,
                "total": result["total"],
                "query": query
            }
        
        return result
```

---

## 모니터링 및 장애 복구

### 통합 헬스체크

#### 외부 서비스 모니터링
```python
async def check_external_services_health():
    """외부 서비스 전체 헬스체크"""
    health_report = {
        "timestamp": datetime.now().isoformat(),
        "overall_healthy": True,
        "services": {}
    }
    
    # ExternalService 헬스체크
    external_health = await ExternalService.health_check()
    health_report["services"]["external_apis"] = external_health
    
    if not external_health.get("overall_healthy", False):
        health_report["overall_healthy"] = False
    
    # SearchService 헬스체크
    search_health = await SearchService.health_check()
    health_report["services"]["search"] = search_health
    
    if not search_health.get("healthy", False):
        health_report["overall_healthy"] = False
    
    return health_report
```

#### API별 상태 모니터링
```python
async def monitor_api_performance():
    """API 성능 모니터링"""
    performance_report = {}
    
    # 각 API별 메트릭 수집
    for api_name in ["stock_market", "news", "exchange_rate"]:
        try:
            # 헬스체크 수행
            health_result = await ExternalService.health_check(api_name)
            
            # 메트릭 수집
            metrics = ExternalService.get_metrics(api_name)
            
            performance_report[api_name] = {
                "health": health_result,
                "metrics": metrics,
                "status": "healthy" if health_result.get("healthy") else "unhealthy"
            }
            
        except Exception as e:
            performance_report[api_name] = {
                "status": "error",
                "error": str(e)
            }
    
    return performance_report
```

### 자동 복구 메커니즘

#### Circuit Breaker 자동 복구
```python
async def auto_recovery_service():
    """자동 복구 서비스"""
    while True:
        try:
            # 모든 API 상태 확인
            health_status = await check_external_services_health()
            
            for api_name, api_health in health_status["services"].get("external_apis", {}).get("apis", {}).items():
                if not api_health.get("healthy", False):
                    Logger.warn(f"API {api_name} is unhealthy, attempting recovery")
                    
                    # Circuit Breaker 상태 확인 및 복구 시도
                    client = ExternalService.get_client(api_name)
                    if hasattr(client, 'metrics'):
                        if client.metrics.circuit_breaker_state.value == "open":
                            Logger.info(f"Circuit breaker is OPEN for {api_name}, waiting for timeout")
                        else:
                            # 간단한 헬스체크 요청으로 복구 시도
                            try:
                                await client.health_check()
                                Logger.info(f"Recovery attempt successful for {api_name}")
                            except Exception as e:
                                Logger.error(f"Recovery attempt failed for {api_name}: {e}")
            
            # 10분마다 자동 복구 시도
            await asyncio.sleep(600)
            
        except Exception as e:
            Logger.error(f"Auto recovery service error: {e}")
            await asyncio.sleep(60)
```

### 메트릭 수집 및 알림

#### 성능 메트릭 집계
```python
def aggregate_service_metrics():
    """서비스 메트릭 집계"""
    aggregated_metrics = {
        "external_apis": {},
        "search_service": {},
        "overall_performance": {}
    }
    
    # External API 메트릭
    external_metrics = ExternalService.get_metrics()
    if external_metrics:
        aggregated_metrics["external_apis"] = external_metrics
        
        # 전체 성공률 계산
        overall_requests = external_metrics.get("overall_metrics", {}).get("total_requests", 0)
        overall_successes = external_metrics.get("overall_metrics", {}).get("successful_requests", 0)
        overall_success_rate = overall_successes / overall_requests if overall_requests > 0 else 0
        
        aggregated_metrics["overall_performance"]["external_api_success_rate"] = overall_success_rate
    
    # Search Service 메트릭
    search_metrics = SearchService.get_metrics()
    if search_metrics:
        aggregated_metrics["search_service"] = search_metrics
    
    # 임계값 기반 알림
    if overall_success_rate < 0.95:  # 95% 미만
        Logger.warn(f"External API success rate is low: {overall_success_rate:.2%}")
        # TODO: 알림 시스템 연동
    
    return aggregated_metrics
```

---

## 보안 고려사항

### API 인증 및 보안

#### 현재 구현된 보안 기능
1. **API 키 관리**: 설정을 통한 API 키 저장 및 헤더 자동 추가
2. **HTTPS 강제**: 모든 외부 API 호출에 SSL/TLS 사용
3. **타임아웃 설정**: 응답 시간 제한으로 DoS 공격 방지
4. **재시도 제한**: 과도한 요청 방지

#### 추후 보완 필요 사항

```python
# TODO: API 키 암호화 저장
class SecureApiKeyManager:
    def encrypt_api_key(self, api_key: str) -> str:
        # API 키 암호화 로직
        pass
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        # API 키 복호화 로직
        pass

# TODO: Rate Limiting
class RateLimiter:
    def check_rate_limit(self, api_name: str, client_ip: str) -> bool:
        # API별, 클라이언트별 요청 제한 체크
        pass

# TODO: Request/Response 로깅
class SecurityAuditLogger:
    def log_api_request(self, api_name: str, endpoint: str, user_id: str):
        # API 요청 감사 로그
        pass
```

---

이것으로 Part 6이 완료되었습니다. Part 7에서는 스케줄러와 백그라운드 작업에 대해 상세히 다루겠습니다.