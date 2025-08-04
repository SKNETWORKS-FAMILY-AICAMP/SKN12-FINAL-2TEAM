from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Dict, Any, Literal
from enum import Enum

class SearchMode(str, Enum):
    """검색 모드"""
    BM25_ONLY = "bm25_only"
    VECTOR_ONLY = "vector_only"
    HYBRID = "hybrid"
    AUTO = "auto"

class ScoreFusionMethod(str, Enum):
    """점수 합성 방법"""
    WEIGHTED_SUM = "weighted_sum"      # 가중 합계 (기본값)
    RANK_FUSION = "rank_fusion"        # Reciprocal Rank Fusion (RRF)
    DISTRIBUTIONAL = "distributional"  # 분포 기반 정규화
    CONVEX_COMBINATION = "convex"      # 볼록 결합

class ChunkingStrategy(str, Enum):
    """텍스트 청킹 전략"""
    SENTENCE = "sentence"              # 문장 단위 (기본값)
    PARAGRAPH = "paragraph"            # 문단 단위
    SEMANTIC = "semantic"              # 의미 단위
    FIXED_SIZE = "fixed_size"          # 고정 크기
    SLIDING_WINDOW = "sliding_window"  # 슬라이딩 윈도우

class RagConfig(BaseModel):
    """
    RAG (Retrieval-Augmented Generation) 서비스 설정
    
    하이브리드 검색을 위한 모든 동작 매개변수들을 타입 안전하게 정의하며,
    금융 도메인 특성과 하이브리드 검색 연구 결과를 반영한 최적화된 기본값을 제공합니다.
    """
    
    # =================== 기본 서비스 설정 ===================
    
    service_name: str = Field(
        default="rag_service",
        description="RAG 서비스 이름"
    )
    
    collection_name: str = Field(
        default="financial_documents",
        description="문서 컬렉션 이름 (OpenSearch 인덱스명과 동일)"
    )
    
    # =================== 검색 동작 설정 ===================
    
    search_mode: SearchMode = Field(
        default=SearchMode.HYBRID,
        description="기본 검색 모드"
    )
    
    default_k: int = Field(
        default=10,
        ge=1,
        le=100,
        description="기본 반환 문서 수"
    )
    
    max_k: int = Field(
        default=50,
        ge=1,
        le=200,
        description="최대 반환 문서 수"
    )
    
    similarity_threshold: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="벡터 유사도 임계값 (금융 정확성 우선)"
    )
    
    # =================== 하이브리드 검색 가중치 ===================
    
    bm25_weight: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="BM25 키워드 검색 가중치 (금융 용어 정확성 고려)"
    )
    
    vector_weight: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="벡터 유사도 검색 가중치 (의미적 유사성 우선)"
    )
    
    score_fusion_method: ScoreFusionMethod = Field(
        default=ScoreFusionMethod.WEIGHTED_SUM,
        description="점수 합성 방법"
    )
    
    # RRF(Reciprocal Rank Fusion) 전용 설정
    rrf_k: int = Field(
        default=60,
        ge=1,
        le=100,
        description="RRF 매개변수 (논문 권장값: 60)"
    )
    
    # =================== 텍스트 처리 설정 ===================
    
    chunking_strategy: ChunkingStrategy = Field(
        default=ChunkingStrategy.SENTENCE,
        description="텍스트 청킹 전략"
    )
    
    chunk_size: int = Field(
        default=512,
        ge=128,
        le=2048,
        description="청크 최대 크기 (토큰 수 기준, 금융 문서 특성 고려)"
    )
    
    chunk_overlap: int = Field(
        default=50,
        ge=0,
        le=200,
        description="청크 간 겹침 크기 (토큰 수 기준)"
    )
    
    min_chunk_size: int = Field(
        default=50,
        ge=10,
        le=500,
        description="최소 청크 크기 (너무 작은 청크 방지)"
    )
    
    # =================== 성능 및 안정성 설정 ===================
    
    # 타임아웃 설정 (기존 서비스들 참조)
    search_timeout: int = Field(
        default=30,
        ge=5,
        le=120,
        description="개별 검색 타임아웃 (초, SearchService 기준)"
    )
    
    vector_timeout: int = Field(
        default=60,
        ge=10,
        le=180,
        description="벡터 검색 타임아웃 (초, VectorDbService 기준)"
    )
    
    hybrid_timeout: int = Field(
        default=90,
        ge=15,
        le=300,
        description="하이브리드 검색 전체 타임아웃 (초)"
    )
    
    # 재시도 설정
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="최대 재시도 횟수"
    )
    
    retry_delay: float = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        description="재시도 간 지연 시간 (초)"
    )
    
    # 병렬 처리 설정
    max_concurrent_searches: int = Field(
        default=5,
        ge=1,
        le=20,
        description="최대 동시 검색 수"
    )
    
    # =================== 캐시 설정 ===================
    
    enable_result_cache: bool = Field(
        default=True,
        description="검색 결과 캐싱 활성화"
    )
    
    cache_ttl: int = Field(
        default=3600,  # 1시간
        ge=60,
        le=86400,  # 24시간
        description="캐시 TTL (초, 금융 데이터 실시간성 고려)"
    )
    
    cache_max_size: int = Field(
        default=1000,
        ge=10,
        le=10000,
        description="캐시 최대 항목 수"
    )
    
    # =================== 벡터 임베딩 설정 ===================
    
    # VectorDbConfig 기반
    embedding_model: str = Field(
        default="amazon.titan-embed-text-v2:0",
        description="임베딩 모델명 (Bedrock Titan v2, 1024차원)"
    )
    
    embedding_dimension: int = Field(
        default=1024,
        ge=128,
        le=4096,
        description="임베딩 벡터 차원수"
    )
    
    # =================== 재랭킹 설정 ===================
    
    enable_reranking: bool = Field(
        default=True,
        description="재랭킹 활성화 (금융 정확성 향상)"
    )
    
    rerank_top_k: int = Field(
        default=20,
        ge=5,
        le=100,
        description="재랭킹 대상 문서 수"
    )
    
    rerank_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="재랭킹 임계값"
    )
    
    # =================== 금융 도메인 특화 설정 ===================
    
    financial_entity_boost: float = Field(
        default=1.2,
        ge=1.0,
        le=2.0,
        description="금융 엔티티 매칭 시 점수 부스트 배율"
    )
    
    recent_news_boost: float = Field(
        default=1.1,
        ge=1.0,
        le=2.0,
        description="최신 뉴스 점수 부스트 배율"
    )
    
    financial_keywords: List[str] = Field(
        default=[
            "금리", "인플레이션", "주가", "환율", "GDP", 
            "중앙은행", "연준", "한국은행", "기준금리", "통화정책",
            "증시", "코스피", "나스닥", "S&P500", "유가",
            "달러", "원화", "유로", "엔화", "위안화"
        ],
        description="금융 도메인 핵심 키워드 (부스팅 대상)"
    )
    
    # =================== 디버깅 및 로깅 설정 ===================
    
    debug_mode: bool = Field(
        default=False,
        description="디버그 모드 활성화"
    )
    
    log_search_results: bool = Field(
        default=False,
        description="검색 결과 상세 로깅"
    )
    
    log_performance: bool = Field(
        default=True,
        description="성능 통계 로깅"
    )
    
    # =================== 실험적 기능 설정 ===================
    
    enable_query_expansion: bool = Field(
        default=False,
        description="쿼리 확장 기능 (실험적)"
    )
    
    enable_semantic_clustering: bool = Field(
        default=False,
        description="의미적 클러스터링 (실험적)"
    )
    
    # =================== 백워드 호환성 ===================
    
    # 기존 필드들 (하위 호환성)
    vector_db_path: str = Field(
        default="./vector_db",
        description="벡터 DB 저장 경로 (로컬 백업용)"
    )
    
    default_threshold: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="기본 임계값 (similarity_threshold와 동일)"
    )
    
    max_content_length: int = Field(
        default=512,
        ge=100,
        le=2048,
        description="최대 콘텐츠 길이 (chunk_size와 동일)"
    )
    
    enable_vector_db: bool = Field(
        default=True,
        description="벡터 DB 사용 활성화"
    )
    
    enable_fallback_search: bool = Field(
        default=True,
        description="폴백 검색 활성화"
    )

    @model_validator(mode='after')
    def validate_hybrid_weights(self) -> 'RagConfig':
        """하이브리드 검색 가중치 검증 및 자동 조정"""
        
        # 가중치 합계 검증 (1.0에서 0.01 오차 허용)
        weight_sum = self.bm25_weight + self.vector_weight
        if abs(weight_sum - 1.0) > 0.01:
            # 자동 정규화
            if weight_sum > 0:
                self.bm25_weight = self.bm25_weight / weight_sum
                self.vector_weight = self.vector_weight / weight_sum
            else:
                # 모든 가중치가 0인 경우 기본값 설정
                self.bm25_weight = 0.4
                self.vector_weight = 0.6
        
        return self

    @model_validator(mode='after')
    def validate_chunk_settings(self) -> 'RagConfig':
        """청킹 설정 검증 및 자동 조정"""
        
        # 청크 겹침이 청크 크기보다 클 수 없음
        if self.chunk_overlap >= self.chunk_size:
            self.chunk_overlap = max(0, self.chunk_size // 4)
        
        # 최소 청크 크기가 청크 크기보다 클 수 없음
        if self.min_chunk_size >= self.chunk_size:
            self.min_chunk_size = max(10, self.chunk_size // 10)
        
        return self

    @model_validator(mode='after')
    def validate_timeout_settings(self) -> 'RagConfig':
        """타임아웃 설정 검증 및 자동 조정"""
        
        # 하이브리드 타임아웃은 개별 타임아웃들의 합보다 커야 함
        min_hybrid_timeout = max(self.search_timeout, self.vector_timeout) + 10
        if self.hybrid_timeout < min_hybrid_timeout:
            self.hybrid_timeout = min_hybrid_timeout
        
        return self

    @model_validator(mode='after') 
    def validate_k_settings(self) -> 'RagConfig':
        """K 값 설정 검증 및 자동 조정"""
        
        # default_k가 max_k보다 클 수 없음
        if self.default_k > self.max_k:
            self.default_k = self.max_k
        
        # rerank_top_k는 max_k보다 작거나 같아야 함
        if self.rerank_top_k > self.max_k:
            self.rerank_top_k = self.max_k
        
        return self

    @model_validator(mode='after')
    def sync_backward_compatibility(self) -> 'RagConfig':
        """백워드 호환성을 위한 필드 동기화"""
        
        # 기존 필드들을 새 필드들과 동기화
        self.default_threshold = self.similarity_threshold
        self.max_content_length = self.chunk_size
        
        return self

    def get_search_weights(self) -> Dict[str, float]:
        """정규화된 검색 가중치 반환"""
        return {
            "bm25": self.bm25_weight,
            "vector": self.vector_weight
        }

    def get_timeout_config(self) -> Dict[str, int]:
        """타임아웃 설정 반환"""
        return {
            "search": self.search_timeout,
            "vector": self.vector_timeout,
            "hybrid": self.hybrid_timeout
        }

    def get_chunk_config(self) -> Dict[str, Any]:
        """청킹 설정 반환"""
        return {
            "strategy": self.chunking_strategy,
            "size": self.chunk_size,
            "overlap": self.chunk_overlap,
            "min_size": self.min_chunk_size
        }

    def get_cache_config(self) -> Dict[str, Any]:
        """캐시 설정 반환"""
        return {
            "enabled": self.enable_result_cache,
            "ttl": self.cache_ttl,
            "max_size": self.cache_max_size
        }

    def is_hybrid_capable(self) -> bool:
        """하이브리드 검색 가능 여부"""
        return (
            self.enable_vector_db and 
            self.enable_fallback_search and 
            self.search_mode in [SearchMode.HYBRID, SearchMode.AUTO]
        )

    def get_financial_config(self) -> Dict[str, Any]:
        """금융 도메인 설정 반환"""
        return {
            "entity_boost": self.financial_entity_boost,
            "recent_boost": self.recent_news_boost,
            "keywords": self.financial_keywords
        }

    class Config:
        """Pydantic 설정"""
        # JSON 스키마 생성 시 사용할 제목과 설명
        title = "RAG Service Configuration"
        description = "하이브리드 검색을 위한 RAG 서비스 설정"
        
        # 추가 필드 허용하지 않음 (타입 안전성)
        extra = "forbid"
        
        # 필드 검증 활성화
        validate_assignment = True
        
        # JSON 예제
        json_schema_extra = {
            "examples": [
                {
                    "collection_name": "financial_news",
                    "search_mode": "hybrid",
                    "default_k": 10,
                    "bm25_weight": 0.4,
                    "vector_weight": 0.6,
                    "chunk_size": 512,
                    "chunk_overlap": 50,
                    "enable_result_cache": True,
                    "cache_ttl": 3600,
                    "financial_entity_boost": 1.2
                }
            ]
        }