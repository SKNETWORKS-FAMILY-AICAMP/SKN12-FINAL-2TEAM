# 📁 RAG Service

## 📌 개요
RAG (Retrieval-Augmented Generation) 서비스는 SearchService(키워드 검색)와 VectorDbService(벡터 검색)를 조합한 하이브리드 문서 검색 기능을 제공하는 정적 클래스입니다. 111 패턴을 사용하여 서비스 생명주기를 관리하며, 금융 도메인 특성에 최적화된 검색 기능을 제공합니다.

## 🏗️ 구조
```
base_server/service/rag/
├── __init__.py                    # 모듈 초기화
├── rag_service.py                 # 메인 서비스 클래스 (정적 클래스)
├── rag_config.py                  # 설정 관리 (Pydantic)
├── rag_client.py                  # RAG 클라이언트 인터페이스
└── rag_vectordb_client.py        # RAG 전용 벡터 DB 클라이언트
```

## 🔧 핵심 기능

### RagService (정적 클래스)
- **정적 클래스**: 111 패턴으로 서비스 인스턴스 관리
- **초기화 관리**: `init()`, `shutdown()`, `is_initialized()` 메서드
- **하이브리드 검색**: BM25 키워드 검색과 벡터 유사도 검색 조합
- **의존성 관리**: SearchService와 VectorDbService 상태 검증

### 주요 기능 그룹

#### 1. 문서 관리 (Document Management)
```python
# 문서 인지션 파이프라인
await RagService.add_documents(documents)

# 문서 전처리 및 청킹
processed_docs = cls._preprocess_documents(documents)
chunked_docs = cls._chunk_documents(processed_docs)

# 병렬 저장 실행
storage_results = await cls._parallel_storage(chunked_docs)
```

#### 2. 하이브리드 검색 (Hybrid Search)
```python
# 하이브리드 검색 (기본)
results = await RagService.retrieve(query, top_k=10, hybrid=True)

# BM25 키워드 검색만
results = await RagService._bm25_search_only(query, k)

# 벡터 유사도 검색만
results = await RagService._vector_search_only(query, k)

# 하이브리드 검색 실행
results = await cls._hybrid_search(query, k, bm25_weight, vector_weight)
```

#### 3. 검색어 전처리 (Query Preprocessing)
```python
# 주식 심볼 매핑 및 검색어 확장
processed_query = cls._preprocess_query(query)

# 한국어/영어 주식명 → 티커 심볼 변환
# 예: "삼성전자" → "005930", "Apple" → "AAPL"

# 검색어 정규화 (소문자 변환)
normalized_query = query.lower().strip()
```

#### 4. 점수 합성 및 순위 결정
```python
# BM25와 벡터 검색 결과 조합
combined_results = cls._fuse_search_results(
    bm25_results, vector_results, 
    bm25_weight, vector_weight
)

# BM25 점수 정규화
bm25_score = cls._normalize_bm25_score(bm25_result["score"])

# 점수 합성 및 메타데이터 추가
combined_result = {
    **primary_result,
    "score": combined_score,
    "search_type": "hybrid",
    "score_details": {...}
}
```

#### 5. 모니터링 및 통계
```python
# 성능 통계 조회
stats = RagService.get_stats()

# 서비스 상태 확인
health_status = await RagService.health_check()

# 검색 성능 통계 업데이트
cls._update_search_stats(search_time)

# 통계 초기화
cls._reset_stats()
```

## 🔄 Template-Service 연동

### 사용하는 Service
- **`service.search.search_service.SearchService`**: BM25 키워드 검색
- **`service.vectordb.vectordb_service.VectorDbService`**: 벡터 유사도 검색
- **`service.core.logger.Logger`**: 로깅

### 연동 방식
1. **초기화**: `RagService.init(rag_config)` 호출
2. **의존성 검증**: `_validate_dependencies()` - SearchService와 VectorDbService 상태 확인
3. **하이브리드 검색**: 두 서비스의 검색 결과를 조합하여 반환
4. **정리**: `shutdown()` 호출로 리소스 해제

## 📊 데이터 흐름

### 하이브리드 검색 프로세스
```
Query → RagService.retrieve() → 검색어 전처리 → 병렬 검색 실행
                                ├── BM25 검색 (SearchService)
                                └── 벡터 검색 (VectorDbService)
                                ↓
                            점수 합성 및 순위 결정 (_fuse_search_results)
                                ↓
                            통합된 검색 결과 반환
```

### 문서 인지션 파이프라인
```
Documents → 전처리 (_preprocess_documents) → 청킹 (_chunk_documents) → 병렬 저장 (_parallel_storage)
                        ├── SearchService (OpenSearch) - _store_to_search_service
                        └── VectorDbService (AWS Bedrock) - _store_to_vector_service
```

## 🚀 사용 예제

### 기본 초기화
```python
from service.rag.rag_config import RagConfig
from service.rag.rag_service import RagService

# 설정 구성
config = RagConfig(
    collection_name="financial_documents",
    embedding_model="amazon.titan-embed-text-v2:0",
    default_k=10,
    search_mode="hybrid",
    bm25_weight=0.4,
    vector_weight=0.6,
    enable_vector_db=True,
    enable_fallback_search=True
)

# 서비스 초기화
RagService.init(config)
```

### 하이브리드 검색 실행
```python
# 기본 하이브리드 검색
results = await RagService.retrieve(
    query="삼성전자 최근 실적",
    top_k=10,
    hybrid=True
)

# 가중치 조정 검색
results = await RagService.retrieve(
    query="Apple 주가 전망",
    top_k=15,
    hybrid=True,
    bm25_weight=0.3,
    vector_weight=0.7
)
```

### 문서 추가
```python
documents = [
    {
        "id": "doc_001",
        "content": "삼성전자 2024년 1분기 실적 발표...",
        "metadata": {
            "title": "삼성전자 실적",
            "source": "financial_news",
            "date": "2024-01-15"
        }
    }
]

result = await RagService.add_documents(documents)
if result.get("success"):
    print(f"문서 인덱싱 성공: {result['success_count']}개")
```

## ⚙️ 설정

### RagConfig 주요 설정
```python
class RagConfig(BaseModel):
    collection_name: str = "financial_documents"     # 문서 컬렉션 이름
    embedding_model: str = "amazon.titan-embed-text-v2:0"  # 임베딩 모델 (Titan v2)
    search_mode: SearchMode = SearchMode.HYBRID      # 검색 모드
    default_k: int = 10                              # 기본 반환 문서 수
    max_k: int = 50                                  # 최대 반환 문서 수
    similarity_threshold: float = 0.75               # 벡터 유사도 임계값
    bm25_weight: float = 0.4                        # BM25 가중치
    vector_weight: float = 0.6                      # 벡터 가중치
    score_fusion_method: ScoreFusionMethod = ScoreFusionMethod.WEIGHTED_SUM
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.SENTENCE
    enable_vector_db: bool = True                    # 벡터 DB 사용 활성화
    enable_fallback_search: bool = True              # 폴백 검색 활성화
    max_content_length: int = 512                    # 최대 콘텐츠 길이
```

### 설정 파일 구성
RAG 서비스 설정은 `base_web_server-config.json` 파일의 `ragConfig` 섹션에서 관리됩니다:

```json
{
  "ragConfig": {
    "collection_name": "financial_documents",
    "embedding_model": "amazon.titan-embed-text-v2:0",
    "default_k": 10,
    "search_mode": "hybrid",
    "bm25_weight": 0.4,
    "vector_weight": 0.6,
    "similarity_threshold": 0.75,
    "chunking_strategy": "sentence",
    "enable_vector_db": true,
    "enable_fallback_search": true,
    "max_content_length": 512
  }
}
```

## 🔗 연관 폴더

### 의존성 관계
- **`service.search`**: BM25 키워드 검색을 위한 SearchService 사용
- **`service.vectordb`**: 벡터 유사도 검색을 위한 VectorDbService 사용
- **`service.core.logger`**: 로깅 서비스
- **`service.core.service_monitor`**: 서비스 모니터링
- **`application.base_web_server.main`**: 메인 서버에서 RAG 초기화 및 테스트

### 사용하는 Template
- **`template.base`**: RAG 설정을 통한 기본 템플릿 연동
- **`service.llm.AIChat.BasicTools.RagTool`**: AI 채팅에서 RAG 검색 도구로 사용

### 외부 시스템
- **AWS Bedrock Knowledge Base**: 벡터 데이터베이스
- **OpenSearch**: 키워드 검색 엔진
- **AWS Bedrock Titan**: 텍스트 임베딩 모델
