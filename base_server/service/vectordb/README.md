# 📁 VectorDB Service

## 📌 개요
VectorDB 서비스는 AWS Bedrock을 기반으로 한 벡터 데이터베이스 서비스로, 텍스트 임베딩, 유사도 검색, RAG(Retrieval-Augmented Generation) 기능을 제공합니다. 정적 클래스 구조를 사용하여 서비스 생명주기를 관리합니다.

## 🏗️ 구조
```
base_server/service/vectordb/
├── __init__.py                    # 모듈 초기화
├── vectordb_service.py            # 메인 서비스 클래스 
├── vectordb_config.py             # 설정 관리 (Pydantic)
├── vectordb_client.py             # 클라이언트 인터페이스
├── vectordb_client_pool.py        # 클라이언트 풀 관리 
└── bedrock_vectordb_client.py     # AWS Bedrock 구현체
```

## 🔧 핵심 기능

### VectorDbService (정적 클래스)
- **정적 클래스**: 정적 클래스로 서비스 인스턴스 관리
- **초기화 관리**: `init()`, `shutdown()`, `is_initialized()` 메서드
- **클라이언트 풀**: `VectorDbClientPool`을 통한 연결 관리

### 주요 기능 그룹

#### 1. 임베딩 (Embedding)
```python
# 단일 텍스트 임베딩
await VectorDbService.embed_text("텍스트")

# 다중 텍스트 임베딩
await VectorDbService.embed_texts(["텍스트1", "텍스트2"])
```

#### 2. 유사도 검색 (Similarity Search)
```python
# 텍스트 기반 검색
await VectorDbService.similarity_search("쿼리", top_k=10)

# 벡터 기반 검색
await VectorDbService.similarity_search_by_vector(vector, top_k=10)
```

#### 3. 문서 관리 (Document Management)
```python
# 문서 CRUD 작업
await VectorDbService.add_documents(documents)
await VectorDbService.get_document(document_id)
await VectorDbService.update_document(document_id, document)
await VectorDbService.delete_documents(document_ids)
```

#### 4. 텍스트 생성 (Text Generation)
```python
# 프롬프트 기반 생성
await VectorDbService.generate_text("프롬프트")

# 채팅 완성
await VectorDbService.chat_completion(messages)
```

#### 5. RAG (Retrieval-Augmented Generation)
```python
# Knowledge Base 기반 답변 생성
await VectorDbService.rag_generate("질문")

# Knowledge Base 검색
await VectorDbService.retrieve_from_knowledge_base("쿼리")
```

#### 6. Knowledge Base 관리
```python
# 동기화 작업 관리
await VectorDbService.start_ingestion_job(data_source_id)
await VectorDbService.get_ingestion_job(data_source_id, ingestion_job_id)
await VectorDbService.get_knowledge_base_status()
```

#### 7. 모니터링 및 관리
```python
# 서비스 상태 확인
await VectorDbService.health_check()
VectorDbService.get_metrics()
VectorDbService.reset_metrics()
await VectorDbService.service_info()
```

## 🔄 Template-Service 연동

### 사용하는 Service
- **자체 관리**: VectorDB 클라이언트 풀을 통한 AWS Bedrock 연결
- **의존성**: `service.core.logger.Logger`를 통한 로깅

### 연동 방식
1. **초기화**: `VectorDbService.init(config)` 호출
2. **클라이언트 획득**: `cls.get_client()` (정적 메서드 내부에서 사용)
3. **작업 수행**: 임베딩, 검색, 생성 등의 비즈니스 로직
4. **정리**: `shutdown()` 호출로 리소스 해제

## 📊 데이터 흐름

### 임베딩 프로세스
```
Request → VectorDbService.embed_text() → ClientPool.get_client() → BedrockClient.embed_text() → AWS Bedrock → Response
```

### 검색 프로세스
```
Query → VectorDbService.similarity_search() → ClientPool.get_client() → BedrockClient.similarity_search() → Knowledge Base → Results
```

### RAG 프로세스
```
Query → Knowledge Base Search → Context Documents → Text Generation → RAG Response
```

## 🚀 사용 예제

### 기본 초기화
```python
from service.vectordb.vectordb_config import VectorDbConfig
from service.vectordb.vectordb_service import VectorDbService

# 설정 구성
config = VectorDbConfig(
    vectordb_type="bedrock",
    aws_access_key_id="your_key",
    aws_secret_access_key="your_secret",
    region_name="ap-northeast-2",
    embedding_model="amazon.titan-embed-text-v2:0",
    text_model="anthropic.claude-3-sonnet-20240229-v1:0"
)

# 서비스 초기화
VectorDbService.init(config)
```

### 텍스트 임베딩
```python
# 단일 텍스트 임베딩
result = await VectorDbService.embed_text("금융 데이터 분석")
if result.get('success'):
    vector = result['embedding']
    print(f"임베딩 차원: {len(vector)}")
```

### 유사도 검색
```python
# 유사한 문서 검색
search_result = await VectorDbService.similarity_search(
    "주식 시장 분석", 
    top_k=5
)

if search_result.get('success'):
    for doc in search_result['results']:
        print(f"문서: {doc['content']}, 유사도: {doc['similarity']}")
```

### RAG 답변 생성
```python
# Knowledge Base 기반 답변
rag_result = await VectorDbService.rag_generate(
    "최근 금융 시장 동향은 어떻게 되나요?"
)

if rag_result.get('success'):
    print(f"답변: {rag_result['answer']}")
    print(f"참고 문서 수: {len(rag_result['context_documents'])}")
```

## ⚙️ 설정

### VectorDbConfig 주요 설정
```python
class VectorDbConfig(BaseModel):
    vectordb_type: str = "bedrock"                    # 벡터DB 타입
    aws_access_key_id: Optional[str] = None           # AWS 액세스 키
    aws_secret_access_key: Optional[str] = None       # AWS 시크릿 키
    region_name: str = "ap-northeast-2"               # AWS 리전
    embedding_model: str = "amazon.titan-embed-text-v2:0"  # 임베딩 모델
    text_model: str = "anthropic.claude-3-sonnet-20240229-v1:0"  # 텍스트 생성 모델
    knowledge_base_id: Optional[str] = None           # Knowledge Base ID
    timeout: int = 60                                 # 타임아웃 (초)
    max_retries: int = 3                             # 최대 재시도 횟수
    default_top_k: int = 10                          # 기본 검색 결과 수
    similarity_threshold: float = 0.7                 # 유사도 임계값
```

### 설정 파일 구성
VectorDB 설정은 `base_web_server-config.json` 파일의 `vectordbConfig` 섹션에서 관리됩니다:

```json
{
  "vectordbConfig": {
    "vectordb_type": "bedrock",
    "aws_access_key_id": "your_access_key",
    "aws_secret_access_key": "your_secret_key",
    "region_name": "ap-northeast-2",
    "embedding_model": "amazon.titan-embed-text-v2:0",
    "text_model": "anthropic.claude-3-sonnet-20240229-v1:0",
    "knowledge_base_id": "your_kb_id",
    "data_source_id": "your_data_source_id",
    "s3_bucket": "your_s3_bucket",
    "timeout": 60,
    "max_retries": 3
  }
}
```

## 🔗 연관 폴더

### 의존성 관계
- **`service.core`**: Logger 서비스, Service Monitor
- **`service.rag`**: RAG 인프라 시스템과 직접 연동 (RAG 서비스에서 VectorDB 사용)
- **`service.service_container`**: 서비스 컨테이너를 통한 의존성 주입
- **`application.base_web_server.main`**: 메인 서버에서 VectorDB 초기화 및 테스트

### 사용하는 Template
- **`template.crawler`**: 크롤링된 데이터의 벡터 임베딩 및 Knowledge Base 동기화

### 외부 시스템
- **AWS Bedrock**: 벡터 임베딩 및 텍스트 생성
- **AWS Knowledge Base**: 문서 저장 및 검색
- **AWS S3**: Knowledge Base 데이터 소스
