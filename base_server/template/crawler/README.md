# 📁 Crawler Template

## 📌 개요
- **Yahoo Finance** 뉴스 수집을 담당하는 템플릿 구현.
- 수집 → 중복 제거 → **OpenSearch 인덱싱** → **S3 업로드 후 Knowledge Base 동기화(ingestion job 트리거)**까지를 처리.
- 헬스체크/상태조회/저장 검증 유틸을 포함.

## 🏗️ 구조
```
base_server/template/crawler/
├── crawler_template_impl.py          # 크롤러 템플릿 구현체
├── common/                           # 공통 모델 및 프로토콜
│   ├── __init__.py
│   ├── crawler_model.py             # 크롤러 데이터 모델
│   ├── crawler_protocol.py          # 크롤러 프로토콜 정의
│   └── crawler_serialize.py         # 크롤러 직렬화 클래스
└── README.md                         
```

## 🔧 핵심 기능

### **CrawlerTemplateImpl 클래스**
- **Yahoo Finance 뉴스 수집**: `on_crawler_yahoo_finance_req()` - 150+ 대형 주식 심볼들의 뉴스 자동 수집
- **크롤러 작업 실행**: `on_crawler_execute_req()` - 다양한 크롤링 작업 실행 및 관리
- **크롤러 상태 조회**: `on_crawler_status_req()` - 활성 작업 및 진행 상황 모니터링
- **크롤러 헬스체크**: `on_crawler_health_req()` - 서비스 상태 및 의존성 확인
- **크롤러 데이터 조회**: `on_crawler_data_req()` - 수집된 데이터 검색 및 조회
- **크롤러 작업 중단**: `on_crawler_stop_req()` - 실행 중인 작업 강제 종료
- **저장소 상태 검증**: `verify_opensearch_storage()`, `verify_vectordb_storage()`, `verify_storage_health()` - OpenSearch 및 VectorDB 저장 상태 확인

### **주요 메서드**
- `on_crawler_yahoo_finance_req()`: Yahoo Finance API를 통한 실시간 뉴스 수집 (FAANG+, 반도체, ETF, 금융, 헬스케어, 소비재, 에너지, 산업재, 통신, 자동차, 부동산, 유틸리티, 엔터테인먼트, 중국 ADR, 암호화폐 등 150+ 심볼)
- `on_crawler_execute_req()`: 크롤링 작업 실행 및 작업 타입별 라우팅
- `on_crawler_status_req()`: 활성 작업 목록, 스케줄러 상태, 처리된 해시키 수 조회
- `on_crawler_health_req()`: CacheService, SearchService, VectorDbService, SchedulerService 상태 확인
- `on_crawler_data_req()`: 수집된 뉴스 데이터 필터링 및 제한된 결과 반환
- `_collect_yahoo_finance_data()`: yfinance 라이브러리를 사용한 실제 데이터 수집
- `_process_duplicate_removal()`: MD5 해시 기반 중복 뉴스 제거
- `_store_to_opensearch()`: OpenSearch에 뉴스 데이터 인덱싱
- `_store_to_vectordb()`: AWS Bedrock Knowledge Base에 임베딩 데이터 저장
- `_generate_hash_key()`: MD5 해시 기반 뉴스 제목 해시키 생성
- `_save_hash_cache()`: 처리된 해시키를 캐시에 저장 (7일 TTL)
- `_parse_yahoo_news_item()`: Yahoo Finance 뉴스 아이템 파싱
- `_parse_and_filter_date()`: 날짜 파싱 및 일주일 이내 필터링
- `verify_opensearch_storage()`: OpenSearch 저장 상태 검증
- `verify_vectordb_storage()`: VectorDB 저장 상태 검증
- `verify_storage_health()`: 전체 저장소 상태 확인

## 🔄 Template-Service 연동

### **사용하는 Service 목록**
- **ExternalService**: 외부 API 접근 및 웹 크롤링
- **SearchService**: OpenSearch 연동 및 뉴스 데이터 인덱싱
- **VectorDbService**: AWS Bedrock Knowledge Base 연동 및 임베딩 저장
- **CacheService**: 처리된 뉴스 해시키 캐싱 및 작업 상태 관리
- **LockService**: 분산락을 통한 중복 크롤링 작업 방지
- **SchedulerService**: 정기적인 크롤링 작업 스케줄링
- **StorageService**: S3를 통한 파일 업로드 및 Knowledge Base 동기화

### **연동 방식 설명**
1. **데이터 수집** → yfinance 라이브러리를 통한 Yahoo Finance 뉴스 수집
2. **중복 제거** → MD5 해시 기반 중복 뉴스 필터링 및 CacheService 캐싱
3. **데이터 저장** → SearchService를 통한 OpenSearch 인덱싱
4. **벡터 저장** → VectorDbService를 통한 AWS Bedrock Knowledge Base 저장
5. **작업 관리** → LockService를 통한 중복 실행 방지 및 상태 추적
6. **스케줄링** → SchedulerService를 통한 정기적인 크롤링 작업 관리

## 📊 데이터 흐름

### **Request → Template → Service → Response**

```
1. Yahoo Finance 뉴스 수집 요청 (Request)
   ↓
2. CrawlerTemplateImpl.on_crawler_yahoo_finance_req()
   ↓
3. LockService.acquire() - 중복 실행 방지
   ↓
4. yfinance 라이브러리로 뉴스 수집 (150+ 심볼)
   ↓
5. MD5 해시 기반 중복 제거 (CacheService)
   ↓
6. SearchService.store_to_opensearch() - OpenSearch 저장
   ↓
7. VectorDbService.store_to_vectordb() - Knowledge Base 저장
   ↓
8. LockService.release() - 락 해제
   ↓
9. 크롤링 결과 응답 (Response)
```

### **크롤러 상태 관리 플로우**
```
1. 크롤러 헬스체크 요청
   ↓
2. CrawlerTemplateImpl.on_crawler_health_req()
   ↓
3. 각 서비스 상태 확인 (CacheService, SearchService, VectorDbService, SchedulerService)
   ↓
4. 활성 작업 수 및 처리된 해시키 수 집계
   ↓
5. 전체 시스템 상태 응답
```

### **데이터 저장 및 검증 플로우**
```
1. 수집된 뉴스 데이터
   ↓
2. OpenSearch 인덱싱 (SearchService)
   ↓
3. S3 업로드 (StorageService)
   ↓
4. Knowledge Base 동기화 (VectorDbService)
   ↓
5. 저장 상태 검증 및 모니터링
```

### **스케줄러 기반 자동 크롤링 플로우**
```
1. 1시간마다 스케줄러 실행
   ↓
2. _scheduled_crawling_task() 호출
   ↓
3. 자동 크롤링 요청 생성 (task_id: scheduled_{timestamp})
   ↓
4. Yahoo Finance 뉴스 수집 실행
   ↓
5. 중복 제거 및 저장 처리
   ↓
6. 해시키 캐시 업데이트
```

## 🚀 사용 예제

### **Yahoo Finance 뉴스 수집 예제**
```python
# Yahoo Finance 뉴스 수집 요청 처리
async def on_crawler_yahoo_finance_req(self, client_session, request: CrawlerYahooFinanceRequest):
    """Yahoo Finance 뉴스 수집 요청 처리"""
    response = CrawlerYahooFinanceResponse()
    
    try:
        # 1. 중복 실행 방지 (Lock 사용)
        v_lock_key = f"crawler_yahoo_finance_{request.task_id}"
        lock_service = ServiceContainer.get_lock_service()
        v_lock_token = await lock_service.acquire(v_lock_key, ttl=7200, timeout=5)
        
        # 2. Yahoo Finance 데이터 수집 (150+ 심볼)
        v_collected_news = await self._collect_yahoo_finance_data(request)
        
        # 3. 중복 제거 처리 (MD5 해시 기반)
        v_filtered_news = await self._process_duplicate_removal(v_collected_news)
        
        # 4. OpenSearch에 저장
        v_opensearch_result = await self._store_to_opensearch(v_filtered_news, request.task_id)
        
        # 5. VectorDB에 저장 (Knowledge Base 동기화)
        v_vectordb_result = await self._store_to_vectordb(v_filtered_news, request.task_id)
        
        response.errorCode = 0
        response.collected_count = len(v_collected_news)
        response.new_count = len(v_filtered_news)
        response.duplicate_count = len(v_collected_news) - len(v_filtered_news)
        
    except Exception as e:
        response.errorCode = 5000
        Logger.error(f"Yahoo Finance 수집 오류: {e}")
    
    return response
```

### **크롤러 헬스체크 예제**
```python
# 크롤러 헬스체크 요청 처리
async def on_crawler_health_req(self, client_session, request: CrawlerHealthRequest):
    """크롤러 헬스체크 요청 처리"""
    response = CrawlerHealthResponse()
    
    try:
        response.errorCode = 0
        response.status = "healthy"
        response.timestamp = datetime.now().isoformat()
        response.active_tasks = len([t for t in self.v_active_tasks.values() if t.status == "running"])
        response.processed_hashes_count = len(self.v_processed_hashes)
        response.scheduler_active = self.v_scheduler_task_id is not None
        
        # 서비스 상태 체크
        if request.check_services:
            v_services = {}
            v_services["cache_service"] = ServiceContainer.get_cache_service() is not None
            v_services["search_service"] = SearchService.is_initialized()
            v_services["vectordb_service"] = VectorDbService.is_initialized()
            v_services["scheduler_service"] = SchedulerService.is_initialized()
            response.services = v_services
        
        Logger.info(f"크롤러 헬스체크 완료: {response.status}")
        
    except Exception as e:
        response.errorCode = 5000
        response.status = "unhealthy"
        response.message = "헬스체크 중 오류 발생"
        Logger.error(f"크롤러 헬스체크 오류: {e}")
    
    return response
```

### **저장소 상태 검증 예제**
```python
# OpenSearch 저장 상태 검증
async def verify_opensearch_storage(self, p_task_id: str = None, p_limit: int = 10) -> Dict[str, Any]:
    """OpenSearch 저장 확인"""
    try:
        if not SearchService.is_initialized():
            return {'success': False, 'error': 'SearchService not available'}
        
        v_index_name = 'yahoo_finance_news'
        
        # 인덱스 존재 확인
        v_index_check = await SearchService.index_exists(v_index_name)
        if not v_index_check.get('exists', False):
            return {'success': False, 'error': f'Index {v_index_name} does not exist'}
        
        # 문서 수 조회
        v_count_query = {"query": {"match_all": {}}}
        if p_task_id:
            v_count_query = {"query": {"term": {"task_id": p_task_id}}}
        
        v_count_result = await SearchService.count_documents(v_index_name, v_count_query)
        v_total_count = v_count_result.get('count', 0) if v_count_result.get('success') else 0
        
        return {
            'success': True,
            'index_name': v_index_name,
            'total_count': v_total_count
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}
```

## ⚙️ 설정

### **OpenSearch 인덱스/콘텐츠**
```python
# OpenSearch 인덱스 설정
index_name = 'yahoo_finance_news'         # 인덱스 이름
content_type = 'yahoo_finance_news'       # 콘텐츠 타입

# 도큐먼트 필드 구조
document_fields = {
    'task_id': 'keyword',                 # 작업 ID
    'ticker': 'keyword',                  # 주식 심볼
    'title': 'text',                      # 뉴스 제목
    'source': 'keyword',                  # 뉴스 출처
    'date': 'date',                       # 발행일
    'link': 'keyword',                    # 뉴스 링크
    'collected_at': 'date',               # 수집 시간
    'created_at': 'date',                 # 생성 시간
    'content_type': 'keyword'             # 콘텐츠 타입
}
```

### **캐시 키/TTL**
```python
# 처리된 해시 캐시 설정
cache_key = "crawler:processed_hashes"    # 해시키 캐시 키
cache_ttl = 604800                       # 해시키 캐시 TTL (7일)
```

### **락/스케줄러 설정**
```python
# 락 설정
lock_key_prefix = "crawler_yahoo_finance_"  # 락 키 접두사
lock_ttl = 7200                            # 크롤링 작업 락 TTL (2시간)
lock_timeout = 5                            # 락 획득 타임아웃 (5초)

# 스케줄러 설정
scheduler_job_id = "yahoo_finance_crawler"  # 스케줄러 작업 ID
scheduler_interval = 3600                   # 실행 주기 (1시간)
scheduler_lock_ttl = 1800                   # 스케줄러 작업 락 TTL (30분)
```

### **VectorDB(Knowledge Base) 설정**
```python
# VectorDbService._config에서 관리되는 설정들
vectordb_config = {
    's3_bucket': 'string',                # S3 버킷명
    's3_prefix': 'knowledge-base-data/',  # S3 키 접두사
    'knowledge_base_id': 'string',         # Knowledge Base ID
    'data_source_id': 'string',            # Data Source ID
    'region_name': 'string',               # AWS 리전
    'embedding_model': 'string'            # 임베딩 모델
}

# 주의사항: 본 템플릿은 S3 업로드 후 ingestion job을 시작합니다
# 임베딩 생성은 Knowledge Base 측에서 수행됩니다
```

### **크롤러 템플릿 구현체 설정**
```python
# 크롤러 템플릿 구현체에서 실제 사용되는 설정값들
class CrawlerTemplateImpl:
    def __init__(self):
        self.v_active_tasks = {}          # 활성 작업 관리
        self.v_processed_hashes = set()   # 처리된 뉴스 해시키 세트
        self.v_news_cache = []            # 수집된 뉴스 캐시
        self.v_scheduler_task_id = None   # 스케줄러 작업 ID

# API 호출 간격
sleep_interval = 0.5                      # yfinance API 호출 간격 (초)
```

## 🔗 연관 폴더

### **의존성 관계**
- **`service.external.external_service`**: ExternalService - 외부 API 접근 및 웹 크롤링
- **`service.search.search_service`**: SearchService - OpenSearch 연동 및 뉴스 데이터 인덱싱
- **`service.vectordb.vectordb_service`**: VectorDbService - AWS Bedrock Knowledge Base 연동 및 임베딩 저장
- **`service.cache.cache_service`**: CacheService - 처리된 뉴스 해시키 캐싱 및 작업 상태 관리
- **`service.lock.lock_service`**: LockService - 분산락을 통한 중복 크롤링 작업 방지
- **`service.scheduler.scheduler_service`**: SchedulerService - 정기적인 크롤링 작업 스케줄링
- **`service.storage.storage_service`**: StorageService - S3를 통한 파일 업로드 및 Knowledge Base 동기화

### **기본 템플릿 연관**
- **`template.base.template.crawler_template`**: CrawlerTemplate - 크롤러 템플릿 기본 클래스
- **`template.base.template_context`**: TemplateContext - 템플릿 컨텍스트 관리
- **`template.base.template_type`**: TemplateType - 템플릿 타입 정의

---