import asyncio
from typing import Optional, Dict, Any, List
from service.rag.rag_config import RagConfig
from service.core.logger import Logger

class RagService:
    """RAG (Retrieval-Augmented Generation) 서비스"""
    
    _instance: Optional['RagService'] = None
    _initialized: bool = False
    _config: Optional[RagConfig] = None
    
    @classmethod
    def init(cls, rag_config: RagConfig) -> bool:
        """RAG 서비스 초기화"""
        try:
            Logger.info("RAG 서비스 초기화 시작...")
            
            if cls._initialized:
                Logger.warn("RAG 서비스가 이미 초기화됨")
                return True
            
            # 설정 검증
            if not cls._validate_config(rag_config):
                Logger.error("RAG 설정 검증 실패")
                return False
            
            cls._config = rag_config
            cls._instance = cls()
            
            # 하이브리드 검색 설정 검증
            if not cls._validate_hybrid_search_setup():
                Logger.error("하이브리드 검색 설정 검증 실패")
                return False
            
            cls._initialized = True
            Logger.info(f"✅ RAG 서비스 초기화 완료 (벡터DB: {rag_config.enable_vector_db}, Fallback: {rag_config.enable_fallback_search})")
            
            return True
            
        except Exception as e:
            Logger.error(f"❌ RAG 서비스 초기화 실패: {e}")
            cls._initialized = False
            cls._instance = None
            cls._config = None
            return False
    
    @classmethod
    def _validate_config(cls, config: RagConfig) -> bool:
        """RAG 설정 검증"""
        try:
            # 필수 설정 검증
            if not config.collection_name:
                Logger.error("collection_name이 설정되지 않음")
                return False
            
            if not config.embedding_model:
                Logger.error("embedding_model이 설정되지 않음")
                return False
            
            if config.default_k <= 0:
                Logger.error(f"default_k는 0보다 커야 함: {config.default_k}")
                return False
            
            if not (0.0 <= config.default_threshold <= 1.0):
                Logger.error(f"default_threshold는 0.0~1.0 사이여야 함: {config.default_threshold}")
                return False
            
            if config.max_content_length <= 0:
                Logger.error(f"max_content_length는 0보다 커야 함: {config.max_content_length}")
                return False
            
            Logger.info("RAG 설정 검증 통과")
            return True
            
        except Exception as e:
            Logger.error(f"RAG 설정 검증 중 오류: {e}")
            return False
    
    @classmethod
    def _validate_hybrid_search_setup(cls) -> bool:
        """하이브리드 검색 설정 검증"""
        try:
            # SearchService와 VectorDbService 의존성 확인
            from service.search.search_service import SearchService
            from service.vectordb.vectordb_service import VectorDbService
            
            search_available = SearchService.is_initialized()
            vector_available = VectorDbService.is_initialized()
            
            Logger.info(f"하이브리드 검색 상태 - Search: {search_available}, Vector: {vector_available}")
            
            # 벡터 DB가 활성화되어 있으면 VectorDbService 확인
            if cls._config.enable_vector_db and not vector_available:
                Logger.warn("벡터 DB 활성화 설정이지만 VectorDbService가 초기화되지 않음")
                
            # Fallback 검색이 활성화되어 있으면 SearchService 확인
            if cls._config.enable_fallback_search and not search_available:
                Logger.warn("Fallback 검색 활성화 설정이지만 SearchService가 초기화되지 않음")
            
            # 적어도 하나의 검색 방법은 사용 가능해야 함
            if not (search_available or vector_available):
                Logger.error("Search와 Vector 서비스 모두 사용할 수 없음")
                return False
            
            Logger.info("하이브리드 검색 설정 검증 통과")
            return True
            
        except Exception as e:
            Logger.error(f"하이브리드 검색 설정 검증 중 오류: {e}")
            return False
    
    @classmethod
    def is_initialized(cls) -> bool:
        """RAG 서비스 초기화 상태 확인"""
        return cls._initialized
    
    @classmethod
    def get_instance(cls) -> Optional['RagService']:
        """RAG 서비스 인스턴스 반환"""
        return cls._instance if cls._initialized else None
    
    @classmethod
    def get_config(cls) -> Optional[RagConfig]:
        """RAG 설정 반환"""
        return cls._config if cls._initialized else None
    
    @classmethod
    async def shutdown(cls) -> bool:
        """RAG 서비스 종료"""
        try:
            if not cls._initialized:
                Logger.info("RAG 서비스가 초기화되지 않아 종료 스킵")
                return True
            
            Logger.info("RAG 서비스 종료 시작...")
            
            # 리소스 정리
            if cls._instance:
                # 벡터 DB 연결 정리 등 필요한 정리 작업
                pass
            
            cls._initialized = False
            cls._instance = None
            cls._config = None
            
            Logger.info("✅ RAG 서비스 종료 완료")
            return True
            
        except Exception as e:
            Logger.error(f"❌ RAG 서비스 종료 실패: {e}")
            return False
    
    @classmethod
    async def health_check(cls) -> Dict[str, Any]:
        """RAG 서비스 상태 확인"""
        try:
            if not cls._initialized:
                return {
                    "status": "not_initialized",
                    "message": "RAG 서비스가 초기화되지 않음"
                }
            
            from service.search.search_service import SearchService
            from service.vectordb.vectordb_service import VectorDbService
            
            search_status = SearchService.is_initialized()
            vector_status = VectorDbService.is_initialized()
            
            return {
                "status": "healthy" if (search_status or vector_status) else "degraded",
                "initialized": cls._initialized,
                "config": {
                    "vector_db_enabled": cls._config.enable_vector_db if cls._config else False,
                    "fallback_search_enabled": cls._config.enable_fallback_search if cls._config else False,
                },
                "dependencies": {
                    "search_service": search_status,
                    "vector_service": vector_status
                }
            }
            
        except Exception as e:
            Logger.error(f"RAG 서비스 상태 확인 실패: {e}")
            return {
                "status": "error",
                "message": f"상태 확인 중 오류: {e}"
            }
