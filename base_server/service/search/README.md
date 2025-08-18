# 📁 Search Service

## 📌 개요
Search 서비스는 OpenSearch/Elasticsearch를 기반으로 한 검색 엔진 서비스로, 문서 인덱싱, 검색, 클러스터 관리 기능을 제공합니다. 정적 클래스 구조를 사용하여 서비스 생명주기를 관리합니다.

## 🏗️ 구조
```
base_server/service/search/
├── __init__.py                    # 모듈 초기화
├── search_service.py              # 메인 서비스 클래스 (정적 클래스)
├── search_config.py               # 설정 관리 (Pydantic)
├── search_client.py               # 클라이언트 인터페이스
├── search_client_pool.py          # 클라이언트 풀 관리
└── opensearch_client.py           # OpenSearch 구현체
```

## 🔧 핵심 기능

### SearchService (정적 클래스)
- **정적 클래스**: 정적 클래스로 서비스 인스턴스 관리
- **초기화 관리**: `init()`, `shutdown()`, `is_initialized()` 메서드
- **클라이언트 풀**: `SearchClientPool`을 통한 연결 관리

### 주요 기능 그룹

#### 1. 인덱스 관리 (Index Management)
```python
# 인덱스 생성
await SearchService.create_index("index_name", mappings, settings)

# 인덱스 삭제
await SearchService.delete_index("index_name")

# 인덱스 존재 확인
await SearchService.index_exists("index_name")

# 테스트용 인덱스 생성 (유연한 매핑)
await SearchService.create_test_index("test_index")
```

#### 2. 문서 관리 (Document Management)
```python
# 문서 인덱싱
await SearchService.index_document("index_name", document, doc_id)

# 문서 조회
await SearchService.get_document("index_name", doc_id)

# 문서 업데이트
await SearchService.update_document("index_name", doc_id, document)

# 문서 삭제
await SearchService.delete_document("index_name", doc_id)

# 벌크 인덱싱
await SearchService.bulk_index(operations)
```

#### 3. 검색 (Search)
```python
# 기본 검색
await SearchService.search("index_name", query)

# 스크롤 검색
await SearchService.scroll_search("index_name", query, scroll_time="5m")
```

#### 4. 모니터링 및 관리
```python
# 서비스 상태 확인
await SearchService.health_check()

# 메트릭 조회
SearchService.get_metrics()

# 메트릭 리셋
SearchService.reset_metrics()

# 클러스터 정보 조회
await SearchService.cluster_info()
```

## 🔄 Template-Service 연동

### 사용하는 Service
- **자체 관리**: Search 클라이언트 풀을 통한 OpenSearch 연결
- **의존성**: `service.core.logger.Logger`를 통한 로깅

### 연동 방식
1. **초기화**: `SearchService.init(config)` 호출
2. **클라이언트 획득**: `cls.get_client()` (정적 메서드 내부에서 사용)
3. **작업 수행**: 인덱스 관리, 문서 관리, 검색 등의 비즈니스 로직
4. **정리**: `shutdown()` 호출로 리소스 해제

## 📊 데이터 흐름

### 인덱스 생성 프로세스
```
Request → SearchService.create_index() → ClientPool.get_client() → OpenSearchClient.create_index() → OpenSearch → Response
```

### 문서 인덱싱 프로세스
```
Request → SearchService.index_document() → ClientPool.get_client() → OpenSearchClient.index_document() → OpenSearch → Response
```

### 검색 프로세스
```
Query → SearchService.search() → ClientPool.get_client() → OpenSearchClient.search() → OpenSearch → Results
```

## 🚀 사용 예제

### 기본 초기화
```python
from service.search.search_config import SearchConfig
from service.search.search_service import SearchService

# 설정 구성
config = SearchConfig(
    search_type="opensearch",
    hosts=["localhost:9200"],
    username="admin",
    password="password",
    use_ssl=True,
    verify_certs=False,
    timeout=30,
    max_retries=3
)

# 서비스 초기화
SearchService.init(config)
```

### 인덱스 생성 및 문서 인덱싱
```python
# 테스트 인덱스 생성
index_name = "finance_news"
create_result = await SearchService.create_test_index(index_name)

if create_result.get('success'):
    # 문서 인덱싱
    document = {
        "title": "금융 시장 동향",
        "content": "최근 주식 시장이 상승세를 보이고 있습니다.",
        "timestamp": 1640995200,
        "category": "market_analysis"
    }
    
    index_result = await SearchService.index_document(
        index_name, 
        document, 
        doc_id="doc_001"
    )
    
    if index_result.get('success'):
        print("문서 인덱싱 성공")
```

### 검색 실행
```python
# 검색 쿼리 구성
search_query = {
    "query": {
        "match": {
            "content": "주식 시장"
        }
    },
    "size": 10
}

# 검색 실행
search_result = await SearchService.search(index_name, search_query)

if search_result.get('success'):
    hits = search_result.get('hits', {}).get('hits', [])
    for hit in hits:
        print(f"문서 ID: {hit['_id']}, 점수: {hit['_score']}")
        print(f"내용: {hit['_source']['content']}")
```

## ⚙️ 설정

### SearchConfig 주요 설정
```python
class SearchConfig(BaseModel):
    search_type: str = "opensearch"                    # 검색 엔진 타입
    hosts: List[str] = []                              # OpenSearch 호스트 목록
    username: Optional[str] = None                     # 사용자명
    password: Optional[str] = None                     # 비밀번호
    aws_access_key_id: Optional[str] = None            # AWS 액세스 키
    aws_secret_access_key: Optional[str] = None        # AWS 시크릿 키
    region_name: str = "ap-northeast-2"                # AWS 리전
    use_ssl: bool = True                               # SSL 사용 여부
    verify_certs: bool = True                          # 인증서 검증 여부
    ca_certs: Optional[str] = None                     # CA 인증서 경로
    timeout: int = 30                                  # 타임아웃 (초)
    max_retries: int = 3                               # 최대 재시도 횟수
    retry_on_timeout: bool = True                      # 타임아웃 시 재시도
    default_index: Optional[str] = None                # 기본 인덱스
    index_prefix: str = ""                             # 인덱스 접두사
```

### 설정 파일 구성
Search 서비스 설정은 `base_web_server-config.json` 파일의 `searchConfig` 섹션에서 관리됩니다:

```json
{
  "searchConfig": {
    "search_type": "opensearch",
    "hosts": ["localhost:9200"],
    "username": "admin",
    "password": "password",
    "use_ssl": true,
    "verify_certs": false,
    "timeout": 30,
    "max_retries": 3,
    "default_index": "finance_search",
    "index_prefix": "finance_"
  }
}
```

## 🔗 연관 폴더

### 의존성 관계
- **`service.core`**: Logger 서비스, Service Monitor
- **`service.rag`**: RAG 인프라 시스템과 직접 연동 (RAG 서비스에서 Search 사용)
- **`service.service_container`**: 서비스 컨테이너를 통한 의존성 주입
- **`application.base_web_server.main`**: 메인 서버에서 Search 초기화 및 테스트

### 사용하는 Template
- **`template.crawler`**: 크롤링된 데이터의 검색 인덱싱 및 검색

### 외부 시스템
- **OpenSearch**: 문서 저장 및 검색 엔진
- **Elasticsearch**: 호환 검색 엔진
- **AWS OpenSearch Service**: 관리형 OpenSearch 서비스
