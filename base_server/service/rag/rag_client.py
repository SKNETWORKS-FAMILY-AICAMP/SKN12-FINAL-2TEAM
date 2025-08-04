import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from service.core.logger import Logger
from service.rag.rag_config import RagConfig, SearchMode
from service.rag.rag_service import RagService

class IRagClient(ABC):
    """
    RAG 클라이언트 인터페이스
    
    Tool에서 사용할 하이브리드 검색 기능의 추상 인터페이스를 정의합니다.
    SearchService와 VectorDbService를 통합한 단일 검색 API를 제공합니다.
    """
    
    @abstractmethod
    async def search(self, 
                    query: str, 
                    top_k: Optional[int] = None,
                    search_mode: Optional[SearchMode] = None,
                    **kwargs) -> List[Dict[str, Any]]:
        """
        하이브리드 문서 검색
        
        Args:
            query: 검색 질의
            top_k: 반환할 문서 수
            search_mode: 검색 모드 (hybrid/bm25_only/vector_only/auto)
            **kwargs: 추가 검색 옵션
            
        Returns:
            List[Dict]: 검색된 문서 리스트
        """
        pass
    
    @abstractmethod
    async def add_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        문서 추가 (인지션 파이프라인)
        
        Args:
            documents: 추가할 문서 리스트
            
        Returns:
            Dict: 추가 결과 통계
        """
        pass
    
    @abstractmethod
    async def get_similar(self, 
                         text: str, 
                         top_k: Optional[int] = None,
                         threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        유사 문서 검색 (벡터 검색 전용)
        
        Args:
            text: 기준 텍스트
            top_k: 반환할 문서 수
            threshold: 유사도 임계값
            
        Returns:
            List[Dict]: 유사한 문서 리스트
        """
        pass
    
    @abstractmethod
    async def keyword_search(self, 
                           query: str, 
                           top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        키워드 검색 (BM25 검색 전용)
        
        Args:
            query: 검색 질의
            top_k: 반환할 문서 수
            
        Returns:
            List[Dict]: 검색된 문서 리스트
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """클라이언트 통계 정보 반환"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """클라이언트 상태 확인"""
        pass

class RagClient(IRagClient):
    """
    RAG 클라이언트 구현체 (111 패턴)
    
    RagService를 활용하여 Tool에서 사용하기 쉬운 하이브리드 검색 인터페이스를 제공합니다.
    복잡한 하이브리드 검색 로직을 간단한 메서드로 추상화하여 개발자 친화적인 API를 제공합니다.
    """
    
    # 111 패턴 상태 관리
    _initialized: bool = False
    _config: Optional[RagConfig] = None
    _client_stats = {
        "requests_count": 0,
        "search_requests": 0,
        "document_requests": 0,
        "total_response_time": 0.0,
        "avg_response_time": 0.0,
        "error_count": 0
    }
    
    @classmethod
    def init(cls, config: Optional[RagConfig] = None) -> bool:
        """
        RAG 클라이언트 초기화 (111 패턴)
        
        Args:
            config: RAG 설정 (없으면 기본값 사용)
            
        Returns:
            bool: 초기화 성공 여부
        """
        try:
            Logger.info("🚀 RAG 클라이언트 초기화 시작...")
            
            if cls._initialized:
                Logger.warn("⚠️ RAG 클라이언트가 이미 초기화됨")
                return True
            
            # 설정 준비
            cls._config = config or RagConfig()
            
            # RagService 의존성 확인
            if not RagService.is_initialized():
                Logger.error("❌ RagService가 초기화되지 않음 - 먼저 RagService.init() 호출 필요")
                return False
            
            # 통계 초기화
            cls._reset_stats()
            
            cls._initialized = True
            Logger.info("✅ RAG 클라이언트 초기화 완료")
            Logger.info(f"   - 기본 검색 모드: {cls._config.search_mode}")
            Logger.info(f"   - 기본 반환 문서 수: {cls._config.default_k}")
            Logger.info(f"   - 하이브리드 가중치: BM25({cls._config.bm25_weight}) + Vector({cls._config.vector_weight})")
            
            return True
            
        except Exception as e:
            Logger.error(f"❌ RAG 클라이언트 초기화 실패: {e}")
            cls._initialized = False
            cls._config = None
            return False
    
    @classmethod
    def _reset_stats(cls):
        """통계 초기화"""
        cls._client_stats = {
            "requests_count": 0,
            "search_requests": 0,
            "document_requests": 0,
            "total_response_time": 0.0,
            "avg_response_time": 0.0,
            "error_count": 0
        }
    
    @classmethod
    def _update_stats(cls, request_type: str, response_time: float, success: bool = True):
        """통계 업데이트"""
        cls._client_stats["requests_count"] += 1
        cls._client_stats["total_response_time"] += response_time
        cls._client_stats["avg_response_time"] = (
            cls._client_stats["total_response_time"] / cls._client_stats["requests_count"]
        )
        
        if request_type == "search":
            cls._client_stats["search_requests"] += 1
        elif request_type == "document":
            cls._client_stats["document_requests"] += 1
        
        if not success:
            cls._client_stats["error_count"] += 1
    
    @classmethod
    async def search(cls, 
                    query: str, 
                    top_k: Optional[int] = None,
                    search_mode: Optional[SearchMode] = None,
                    bm25_weight: Optional[float] = None,
                    vector_weight: Optional[float] = None,
                    **kwargs) -> List[Dict[str, Any]]:
        """
        하이브리드 문서 검색 (메인 검색 API)
        
        Args:
            query: 검색 질의
            top_k: 반환할 문서 수 (기본값: config.default_k)
            search_mode: 검색 모드 (기본값: config.search_mode)
            bm25_weight: BM25 가중치 (기본값: config.bm25_weight)
            vector_weight: 벡터 가중치 (기본값: config.vector_weight)
            **kwargs: 추가 검색 옵션
            
        Returns:
            List[Dict]: 검색된 문서 리스트
        """
        if not cls._initialized:
            raise RuntimeError("RagClient가 초기화되지 않음 - RagClient.init() 호출 필요")
        
        start_time = time.time()
        success = True
        
        try:
            Logger.debug(f"🔍 RAG 클라이언트 검색 요청: '{query}'")
            
            # 매개변수 기본값 적용
            k = top_k or cls._config.default_k
            mode = search_mode or cls._config.search_mode
            bm25_w = bm25_weight or cls._config.bm25_weight
            vector_w = vector_weight or cls._config.vector_weight
            
            # 검색 모드에 따른 분기
            if mode == SearchMode.HYBRID:
                results = await RagService.retrieve(
                    query=query,
                    top_k=k,
                    hybrid=True,
                    bm25_weight=bm25_w,
                    vector_weight=vector_w
                )
            elif mode == SearchMode.BM25_ONLY:
                results = await cls._bm25_search_only(query, k)
            elif mode == SearchMode.VECTOR_ONLY:
                results = await cls._vector_search_only(query, k)
            elif mode == SearchMode.AUTO:
                results = await cls._auto_search(query, k, bm25_w, vector_w)
            else:
                raise ValueError(f"지원하지 않는 검색 모드: {mode}")
            
            # 결과 후처리
            processed_results = cls._post_process_results(results, query)
            
            Logger.debug(f"✅ 검색 완료: {len(processed_results)}개 결과")
            return processed_results
            
        except Exception as e:
            success = False
            Logger.error(f"❌ RAG 클라이언트 검색 실패: {e}")
            return []
        
        finally:
            response_time = time.time() - start_time
            cls._update_stats("search", response_time, success)
    
    @classmethod
    async def _auto_search(cls, query: str, k: int, bm25_weight: float, vector_weight: float) -> List[Dict[str, Any]]:
        """자동 검색 모드 - 사용 가능한 서비스에 따라 자동 선택"""
        rag_health = await RagService.health_check()
        
        search_available = rag_health.get("dependencies", {}).get("search_service", False)
        vector_available = rag_health.get("dependencies", {}).get("vector_service", False)
        
        if search_available and vector_available:
            Logger.debug("AUTO 모드: 하이브리드 검색 사용")
            return await RagService.retrieve(
                query=query,
                top_k=k,
                hybrid=True,
                bm25_weight=bm25_weight,
                vector_weight=vector_weight
            )
        elif vector_available:
            Logger.debug("AUTO 모드: 벡터 검색만 사용")
            return await cls._vector_search_only(query, k)
        elif search_available:
            Logger.debug("AUTO 모드: BM25 검색만 사용")
            return await cls._bm25_search_only(query, k)
        else:
            Logger.warn("AUTO 모드: 사용 가능한 검색 서비스 없음")
            return []
    
    @classmethod
    async def _bm25_search_only(cls, query: str, k: int) -> List[Dict[str, Any]]:
        """BM25 검색 전용"""
        return await RagService.retrieve(
            query=query,
            top_k=k,
            hybrid=False,
            bm25_weight=1.0,
            vector_weight=0.0
        )
    
    @classmethod
    async def _vector_search_only(cls, query: str, k: int) -> List[Dict[str, Any]]:
        """벡터 검색 전용"""
        return await RagService.retrieve(
            query=query,
            top_k=k,
            hybrid=False,
            bm25_weight=0.0,
            vector_weight=1.0
        )
    
    @classmethod
    def _post_process_results(cls, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """검색 결과 후처리"""
        if not results:
            return []
        
        processed = []
        
        for result in results:
            # 클라이언트용 필드 추가
            processed_result = {
                **result,
                "client_timestamp": time.time(),
                "query": query,
                "relevance_score": result.get("score", 0.0),
                "snippet": cls._generate_snippet(result.get("content", ""), query)
            }
            
            # 금융 키워드 부스팅 적용
            if cls._contains_financial_keywords(result.get("content", "")):
                processed_result["financial_relevance"] = True
                processed_result["relevance_score"] *= cls._config.financial_entity_boost
            
            processed.append(processed_result)
        
        # 점수 순으로 재정렬
        processed.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return processed
    
    @classmethod
    def _generate_snippet(cls, content: str, query: str, max_length: int = 200) -> str:
        """검색 결과 스니펫 생성"""
        if not content or not query:
            return content[:max_length] + "..." if len(content) > max_length else content
        
        # 쿼리 단어들이 포함된 부분 찾기
        query_words = query.lower().split()
        content_lower = content.lower()
        
        best_pos = 0
        max_matches = 0
        
        # 슬라이딩 윈도우로 가장 관련성 높은 부분 찾기
        for i in range(0, len(content), 50):
            window = content_lower[i:i+max_length]
            matches = sum(1 for word in query_words if word in window)
            if matches > max_matches:
                max_matches = matches
                best_pos = i
        
        snippet = content[best_pos:best_pos+max_length]
        if best_pos > 0:
            snippet = "..." + snippet
        if len(content) > best_pos + max_length:
            snippet = snippet + "..."
        
        return snippet
    
    @classmethod
    def _contains_financial_keywords(cls, content: str) -> bool:
        """금융 키워드 포함 여부 확인"""
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in cls._config.financial_keywords)
    
    @classmethod
    async def add_documents(cls, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        문서 추가 (인지션 파이프라인)
        
        Args:
            documents: 추가할 문서 리스트
                [{"id": str, "content": str, "metadata": dict}, ...]
                
        Returns:
            Dict: 추가 결과 통계
        """
        if not cls._initialized:
            raise RuntimeError("RagClient가 초기화되지 않음")
        
        start_time = time.time()
        success = True
        
        try:
            Logger.info(f"📄 RAG 클라이언트 문서 추가: {len(documents)}개")
            
            # RagService를 통한 문서 추가
            result = await RagService.add_documents(documents)
            
            Logger.info(f"✅ 문서 추가 완료: {result.get('success_count', 0)}개 성공")
            return result
            
        except Exception as e:
            success = False
            Logger.error(f"❌ RAG 클라이언트 문서 추가 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "total_documents": len(documents),
                "success_count": 0,
                "error_count": len(documents)
            }
        
        finally:
            response_time = time.time() - start_time
            cls._update_stats("document", response_time, success)
    
    @classmethod
    async def get_similar(cls, 
                         text: str, 
                         top_k: Optional[int] = None,
                         threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        유사 문서 검색 (벡터 검색 전용)
        
        Args:
            text: 기준 텍스트
            top_k: 반환할 문서 수
            threshold: 유사도 임계값
            
        Returns:
            List[Dict]: 유사한 문서 리스트
        """
        if not cls._initialized:
            raise RuntimeError("RagClient가 초기화되지 않음")
        
        Logger.debug(f"🔍 유사 문서 검색: '{text[:50]}...'")
        
        # 벡터 검색 전용으로 호출
        return await cls.search(
            query=text,
            top_k=top_k,
            search_mode=SearchMode.VECTOR_ONLY
        )
    
    @classmethod
    async def keyword_search(cls, 
                           query: str, 
                           top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        키워드 검색 (BM25 검색 전용)
        
        Args:
            query: 검색 질의
            top_k: 반환할 문서 수
            
        Returns:
            List[Dict]: 검색된 문서 리스트
        """
        if not cls._initialized:
            raise RuntimeError("RagClient가 초기화되지 않음")
        
        Logger.debug(f"🔍 키워드 검색: '{query}'")
        
        # BM25 검색 전용으로 호출
        return await cls.search(
            query=query,
            top_k=top_k,
            search_mode=SearchMode.BM25_ONLY
        )
    
    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """클라이언트 통계 정보 반환"""
        if not cls._initialized:
            return {"initialized": False}
        
        # RagService 통계와 클라이언트 통계 결합
        rag_stats = RagService.get_stats()
        
        return {
            "initialized": cls._initialized,
            "client_stats": cls._client_stats,
            "service_stats": rag_stats,
            "config": {
                "search_mode": cls._config.search_mode,
                "default_k": cls._config.default_k,
                "hybrid_weights": {
                    "bm25": cls._config.bm25_weight,
                    "vector": cls._config.vector_weight
                }
            }
        }
    
    @classmethod
    async def health_check(cls) -> Dict[str, Any]:
        """클라이언트 상태 확인"""
        if not cls._initialized:
            return {
                "status": "not_initialized",
                "message": "RagClient가 초기화되지 않음"
            }
        
        try:
            # RagService 상태 확인
            rag_health = await RagService.health_check()
            
            # 클라이언트 자체 상태
            client_status = "healthy"
            if cls._client_stats["error_count"] > cls._client_stats["requests_count"] * 0.1:
                client_status = "degraded"  # 에러율 10% 초과
            
            return {
                "status": client_status,
                "initialized": cls._initialized,
                "client_metrics": {
                    "total_requests": cls._client_stats["requests_count"],
                    "error_rate": (
                        cls._client_stats["error_count"] / max(1, cls._client_stats["requests_count"])
                    ),
                    "avg_response_time": cls._client_stats["avg_response_time"]
                },
                "service_health": rag_health,
                "capabilities": {
                    "hybrid_search": rag_health.get("capabilities", {}).get("hybrid_search", False),
                    "keyword_search": rag_health.get("capabilities", {}).get("keyword_search", False),
                    "vector_search": rag_health.get("capabilities", {}).get("vector_search", False),
                    "document_ingestion": True
                }
            }
            
        except Exception as e:
            Logger.error(f"RAG 클라이언트 상태 확인 실패: {e}")
            return {
                "status": "error",
                "message": f"상태 확인 중 오류: {e}"
            }
    
    @classmethod
    def is_initialized(cls) -> bool:
        """초기화 상태 확인 (111 패턴)"""
        return cls._initialized
    
    @classmethod
    async def shutdown(cls) -> bool:
        """클라이언트 종료 (111 패턴)"""
        try:
            if not cls._initialized:
                Logger.info("RAG 클라이언트가 초기화되지 않아 종료 스킵")
                return True
            
            Logger.info("🔄 RAG 클라이언트 종료 시작...")
            
            # 통계 로그 출력
            stats = cls.get_stats()
            client_stats = stats.get("client_stats", {})
            Logger.info(f"RAG 클라이언트 통계:")
            Logger.info(f"  - 총 요청: {client_stats.get('requests_count', 0)}개")
            Logger.info(f"  - 검색 요청: {client_stats.get('search_requests', 0)}개")
            Logger.info(f"  - 문서 요청: {client_stats.get('document_requests', 0)}개")
            Logger.info(f"  - 평균 응답 시간: {client_stats.get('avg_response_time', 0):.3f}초")
            Logger.info(f"  - 에러 수: {client_stats.get('error_count', 0)}개")
            
            # 상태 초기화
            cls._initialized = False
            cls._config = None
            cls._reset_stats()
            
            Logger.info("✅ RAG 클라이언트 종료 완료")
            return True
            
        except Exception as e:
            Logger.error(f"❌ RAG 클라이언트 종료 실패: {e}")
            return False

# 편의를 위한 인스턴스 생성 (선택적)
class RagClientInstance(RagClient):
    """
    인스턴스 기반 RAG 클라이언트 (선택적 사용)
    
    정적 메서드 대신 인스턴스 메서드를 선호하는 경우 사용할 수 있습니다.
    """
    
    def __init__(self, config: Optional[RagConfig] = None):
        if not RagClient.is_initialized():
            RagClient.init(config)
        self._config = RagClient._config
    
    async def search_async(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """인스턴스 메서드 버전의 검색"""
        return await RagClient.search(query, **kwargs)
    
    async def add_documents_async(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """인스턴스 메서드 버전의 문서 추가"""
        return await RagClient.add_documents(documents)
    
    def get_config(self) -> RagConfig:
        """현재 설정 반환"""
        return self._config
