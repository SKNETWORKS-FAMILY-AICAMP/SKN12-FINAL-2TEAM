"""
RAG (Retrieval-Augmented Generation) Service Package

이 패키지는 SearchService와 VectorDbService를 조합한 하이브리드 검색 기능을 제공합니다.
단일 파사드 패턴을 통해 BM25 키워드 검색과 벡터 유사도 검색을 통합하여 
더 정확하고 포괄적인 문서 검색 서비스를 제공합니다.

주요 기능:
    - 문서 인지션: add_documents()로 문서를 OpenSearch와 VectorDB에 동시 저장
    - 하이브리드 검색: retrieve()로 BM25 + 벡터 검색 결합
    - 점수 합성: 두 검색 결과의 점수를 합쳐 최종 순위 결정
    - 통합 관리: SearchService와 VectorDbService의 기존 로직 재사용

의존성:
    - service.search.search_service.SearchService: OpenSearch 기반 BM25 검색
    - service.vectordb.vectordb_service.VectorDbService: 벡터 임베딩 및 유사도 검색
    - service.rag.rag_config.RagConfig: RAG 서비스 설정

아키텍처:
    ```
    RagService (Facade)
    ├── SearchService.get_client() → OpenSearch 클라이언트
    ├── VectorDbService.embed_text() → 임베딩 생성  
    └── Hybrid Search Pipeline → 통합 검색 결과
    ```

기본 사용법:
    ```python
    from service.rag import RagService, RagConfig
    
    # 1. 서비스 초기화
    config = RagConfig(
        vector_db_path="./vector_db",
        collection_name="documents",
        embedding_model="sentence-transformers/all-MiniLM-L6-v2"
    )
    
    # main.py에서 자동 초기화됨
    success = RagService.init(config)
    
    # 2. 문서 저장 (인지션 파이프라인)
    documents = [
        {
            "id": "doc1",
            "content": "문서 내용...",
            "metadata": {"title": "제목", "source": "출처"}
        }
    ]
    await RagService.add_documents(documents)
    
    # 3. 하이브리드 검색
    results = await RagService.retrieve(
        query="검색 질의",
        top_k=5,
        hybrid=True  # BM25 + 벡터 검색 결합
    )
    
    # 4. 서비스 종료 (main.py에서 자동 처리)
    await RagService.shutdown()
    ```

클라이언트 인터페이스:
    ```python
    from service.rag import IRagClient, RagClient
    
    # 인터페이스 기반 사용
    client: IRagClient = RagClient()
    results = await client.search(query="검색어", top_k=10)
    ```

설정 관리:
    ```python
    from service.rag import RagConfig
    
    config = RagConfig(
        # 벡터 DB 설정
        vector_db_path="./custom_vector_db",
        collection_name="my_collection",
        embedding_model="custom-model",
        
        # 검색 설정  
        default_k=10,
        default_threshold=0.8,
        max_content_length=500,
        
        # 기능 토글
        enable_vector_db=True,
        enable_fallback_search=True,
        
        # 디버그
        debug_mode=False
    )
    ```

주의사항:
    - SearchService와 VectorDbService가 먼저 초기화되어야 함
    - main.py의 lifespan에서 자동으로 init/shutdown 관리됨
    - 하이브리드 검색 시 두 서비스 중 하나라도 사용 불가하면 degraded 모드로 동작
    - 문서 ID는 OpenSearch와 VectorDB에서 통일되어야 함

Examples:
    문서 저장과 검색의 전체 워크플로우:
    
    ```python
    # 문서 준비
    documents = [
        {
            "id": "financial_news_001", 
            "content": "금리 인상으로 인한 주식시장 영향...",
            "metadata": {
                "title": "금리 정책 변화",
                "source": "경제신문",
                "date": "2024-01-15",
                "category": "금융"
            }
        }
    ]
    
    # 인지션 파이프라인 실행
    success = await RagService.add_documents(documents)
    if success:
        print("문서 저장 완료")
    
    # 하이브리드 검색 실행
    search_results = await RagService.retrieve(
        query="금리 인상 영향",
        top_k=5,
        hybrid=True
    )
    
    for result in search_results:
        print(f"제목: {result['metadata']['title']}")
        print(f"점수: {result['score']}")
        print(f"내용: {result['content'][:100]}...")
    ```
"""

# 핵심 클래스 import
from .rag_config import RagConfig
from .rag_service import RagService

# 클라이언트 인터페이스 (구현 예정)
try:
    from .rag_client import IRagClient, RagClient
except ImportError:
    # rag_client.py가 아직 구현되지 않은 경우 스킵
    IRagClient = None
    RagClient = None

# 외부에서 사용 가능한 클래스들 명시
__all__ = [
    # 핵심 서비스 클래스
    "RagService",
    
    # 설정 클래스
    "RagConfig", 
    
    # 클라이언트 인터페이스 (구현 예정)
    "IRagClient",
    "RagClient",
]

# 패키지 메타정보
__version__ = "1.0.0"
__author__ = "SKN12 Final 2Team"
__description__ = "Hybrid RAG service combining SearchService and VectorDbService"

# 패키지 레벨 상수
DEFAULT_COLLECTION_NAME = "rag_documents"
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_TOP_K = 5
DEFAULT_THRESHOLD = 0.7

# 지원되는 하이브리드 검색 모드
class SearchMode:
    """검색 모드 상수"""
    BM25_ONLY = "bm25"           # OpenSearch만 사용
    VECTOR_ONLY = "vector"       # VectorDB만 사용  
    HYBRID = "hybrid"            # BM25 + Vector 결합
    AUTO = "auto"                # 사용 가능한 서비스에 따라 자동 선택

# 점수 합성 방법
class ScoreFusion:
    """점수 합성 방법 상수"""
    WEIGHTED_SUM = "weighted_sum"      # 가중 합계
    RANK_FUSION = "rank_fusion"        # 순위 기반 융합
    MAX_SCORE = "max_score"            # 최대 점수 선택
    MIN_SCORE = "min_score"            # 최소 점수 선택

# 패키지 초기화 로그
import logging
logger = logging.getLogger(__name__)
logger.debug(f"RAG 패키지 초기화 완료 (버전: {__version__})")
