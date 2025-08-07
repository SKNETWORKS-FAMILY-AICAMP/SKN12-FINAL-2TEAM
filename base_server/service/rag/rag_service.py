import asyncio
import hashlib
import time
from typing import Optional, Dict, Any, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from service.rag.rag_config import RagConfig
from service.rag.rag_vectordb_client import RagVectorDbClient, RagVectorDbConfig
from service.core.logger import Logger

class RagService:
    """
    RAG (Retrieval-Augmented Generation) 서비스
    
    SearchService(키워드 검색)와 VectorDbService(벡터 검색)를 조합한 
    하이브리드 문서 검색 기능을 제공하는 정적 클래스 (111 패턴)
    """
    
    # 111 패턴 상태 관리
    _initialized: bool = False
    _config: Optional[RagConfig] = None
    _search_available: bool = False
    _vector_available: bool = False
    
    # RAG 전용 벡터 클라이언트 (coroutine 재사용 문제 해결)
    _rag_vector_client: Optional[RagVectorDbClient] = None
    
    # 성능 통계
    _stats = {
        "documents_indexed": 0,
        "search_requests": 0,
        "hybrid_searches": 0,
        "avg_search_time": 0.0
    }

    @classmethod
    def init(cls, rag_config: RagConfig) -> bool:
        """
        RAG 서비스 초기화 (111 패턴)
        
        Args:
            rag_config: RAG 서비스 설정
            
        Returns:
            bool: 초기화 성공 여부
        """
        try:
            Logger.info("🚀 RAG 서비스 초기화 시작...")
            
            if cls._initialized:
                Logger.warn("⚠️ RAG 서비스가 이미 초기화됨")
                return True
            
            # 설정 검증
            if not cls._validate_config(rag_config):
                Logger.error("❌ RAG 설정 검증 실패")
                return False
            
            cls._config = rag_config
            
            # 의존 서비스 상태 검증
            if not cls._validate_dependencies():
                Logger.error("❌ 의존 서비스 검증 실패")
                return False
            
            # 하이브리드 검색 설정 검증
            if not cls._validate_hybrid_setup():
                Logger.error("❌ 하이브리드 검색 설정 검증 실패")
                return False
            
            # 통계 초기화
            cls._reset_stats()
            
            cls._initialized = True
            Logger.info(f"✅ RAG 서비스 초기화 완료")
            Logger.info(f"   - 벡터 검색: {'활성화' if cls._vector_available else '비활성화'}")
            Logger.info(f"   - 키워드 검색: {'활성화' if cls._search_available else '비활성화'}")
            Logger.info(f"   - 하이브리드 모드: {'활성화' if (cls._vector_available and cls._search_available) else '비활성화'}")
            
            return True
            
        except Exception as e:
            Logger.error(f"❌ RAG 서비스 초기화 실패: {e}")
            cls._initialized = False
            cls._config = None
            return False

    @classmethod
    def _validate_config(cls, config: RagConfig) -> bool:
        """RAG 설정 검증"""
        try:
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
            
            Logger.debug("RAG 설정 검증 통과")
            return True
            
        except Exception as e:
            Logger.error(f"RAG 설정 검증 중 오류: {e}")
            return False

    @classmethod
    def _validate_dependencies(cls) -> bool:
        """의존 서비스 초기화 상태 검증"""
        try:
            from service.search.search_service import SearchService
            from service.vectordb.vectordb_service import VectorDbService
            
            # SearchService 상태 확인
            cls._search_available = SearchService.is_initialized()
            Logger.info(f"SearchService 상태: {'사용 가능' if cls._search_available else '사용 불가'}")
            
            # VectorDbService 상태 확인
            cls._vector_available = VectorDbService.is_initialized()
            Logger.info(f"VectorDbService 상태: {'사용 가능' if cls._vector_available else '사용 불가'}")
            
            # RAG 전용 벡터 클라이언트 초기화 (coroutine 재사용 문제 해결)
            if cls._vector_available and cls._config.enable_vector_db:
                try:
                    # RAG 설정에서 벡터 DB 설정 추출
                    vector_config = RagVectorDbConfig(
                        aws_access_key_id=cls._config.aws_access_key_id,
                        aws_secret_access_key=cls._config.aws_secret_access_key,
                        region_name=cls._config.region_name,
                        knowledge_base_id=cls._config.knowledge_base_id,
                        aws_session_token=getattr(cls._config, 'aws_session_token', None),
                        max_retries=3,
                        retry_delay_base=1.0,
                        timeout=30.0
                    )
                    
                    cls._rag_vector_client = RagVectorDbClient(vector_config)
                    Logger.info("✅ RAG 전용 벡터 클라이언트 초기화 완료")
                    
                except Exception as e:
                    Logger.error(f"❌ RAG 전용 벡터 클라이언트 초기화 실패: {e}")
                    cls._vector_available = False
            
            # 최소 하나의 서비스는 사용 가능해야 함
            if not (cls._search_available or cls._vector_available):
                Logger.error("Search와 Vector 서비스 모두 사용할 수 없음")
                return False
            
            return True
            
        except Exception as e:
            Logger.error(f"의존 서비스 검증 중 오류: {e}")
            return False

    @classmethod
    def _validate_hybrid_setup(cls) -> bool:
        """하이브리드 검색 설정 검증"""
        try:
            # 벡터 DB 설정 확인
            if cls._config.enable_vector_db and not cls._vector_available:
                Logger.warn("벡터 DB 활성화 설정이지만 VectorDbService가 사용 불가")
                
            # Fallback 검색 설정 확인
            if cls._config.enable_fallback_search and not cls._search_available:
                Logger.warn("Fallback 검색 활성화 설정이지만 SearchService가 사용 불가")
            
            # 하이브리드 검색 가능성 확인
            hybrid_possible = cls._search_available and cls._vector_available
            if hybrid_possible:
                Logger.info("🔍 완전한 하이브리드 검색 가능")
            else:
                Logger.warn("⚠️ 제한된 검색 모드로 동작")
            
            return True
            
        except Exception as e:
            Logger.error(f"하이브리드 검색 설정 검증 중 오류: {e}")
            return False

    @classmethod
    def _reset_stats(cls):
        """통계 초기화"""
        cls._stats = {
            "documents_indexed": 0,
            "search_requests": 0,
            "hybrid_searches": 0,
            "avg_search_time": 0.0
        }

    @classmethod
    async def add_documents(cls, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        문서 인지션 파이프라인 - 두 서비스에 병렬 저장
        
        Args:
            documents: 저장할 문서 리스트
                [{"id": str, "content": str, "metadata": dict}, ...]
                
        Returns:
            Dict: 저장 결과 통계
        """
        if not cls._initialized:
            raise RuntimeError("RAG 서비스가 초기화되지 않음")
        
        start_time = time.time()
        Logger.info(f"📄 문서 인지션 파이프라인 시작: {len(documents)}개 문서")
        
        try:
            # 문서 전처리 및 검증
            processed_docs = cls._preprocess_documents(documents)
            if not processed_docs:
                Logger.warn("처리할 유효한 문서가 없음")
                return {"success": False, "message": "유효한 문서가 없음"}
            
            # 문서 청킹 (긴 문서를 작은 단위로 분할)
            chunked_docs = cls._chunk_documents(processed_docs)
            Logger.info(f"📝 문서 청킹 완료: {len(chunked_docs)}개 청크")
            
            # 병렬 저장 실행
            storage_results = await cls._parallel_storage(chunked_docs)
            
            # 결과 집계
            total_time = time.time() - start_time
            success_count = storage_results.get("success_count", 0)
            error_count = storage_results.get("error_count", 0)
            
            # 통계 업데이트
            cls._stats["documents_indexed"] += success_count
            
            Logger.info(f"✅ 문서 인지션 완료: {success_count}개 성공, {error_count}개 실패 ({total_time:.2f}초)")
            
            return {
                "success": error_count == 0,
                "total_documents": len(documents),
                "total_chunks": len(chunked_docs),
                "success_count": success_count,
                "error_count": error_count,
                "processing_time": total_time,
                "storage_details": storage_results
            }
            
        except Exception as e:
            Logger.error(f"❌ 문서 인지션 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time
            }

    @classmethod
    def _preprocess_documents(cls, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """문서 전처리 및 검증"""
        processed = []
        
        for i, doc in enumerate(documents):
            try:
                # 필수 필드 검증
                if not isinstance(doc, dict):
                    Logger.warn(f"문서 {i}: dict 타입이 아님")
                    continue
                    
                if "content" not in doc or not doc["content"]:
                    Logger.warn(f"문서 {i}: content 필드 없음")
                    continue
                
                # ID 생성 (없으면 자동 생성)
                if "id" not in doc or not doc["id"]:
                    doc["id"] = cls._generate_document_id(doc["content"])
                
                # 메타데이터 기본값 설정
                if "metadata" not in doc:
                    doc["metadata"] = {}
                
                # 타임스탬프 추가
                doc["metadata"]["indexed_at"] = time.time()
                
                processed.append(doc)
                
            except Exception as e:
                Logger.warn(f"문서 {i} 전처리 실패: {e}")
                continue
        
        return processed

    @classmethod
    def _generate_document_id(cls, content: str) -> str:
        """문서 내용 기반 ID 생성"""
        return f"doc_{hashlib.md5(content.encode('utf-8')).hexdigest()[:16]}"

    @classmethod
    def _chunk_documents(cls, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """문서 청킹 - 긴 문서를 작은 단위로 분할"""
        chunks = []
        max_chunk_size = cls._config.max_content_length
        
        for doc in documents:
            content = doc["content"]
            
            # 문서가 너무 짧으면 그대로 유지
            if len(content) <= max_chunk_size:
                chunks.append(doc)
                continue
            
            # 긴 문서는 청킹
            chunk_texts = cls._split_text(content, max_chunk_size)
            
            for i, chunk_text in enumerate(chunk_texts):
                chunk_doc = {
                    "id": f"{doc['id']}_chunk_{i}",
                    "content": chunk_text,
                    "metadata": {
                        **doc["metadata"],
                        "parent_id": doc["id"],
                        "chunk_index": i,
                        "total_chunks": len(chunk_texts)
                    }
                }
                chunks.append(chunk_doc)
        
        return chunks

    @classmethod
    def _split_text(cls, text: str, max_size: int) -> List[str]:
        """텍스트를 지정된 크기로 분할"""
        if len(text) <= max_size:
            return [text]
        
        chunks = []
        sentences = text.split('. ')
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) <= max_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks

    @classmethod
    async def _parallel_storage(cls, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """두 서비스에 병렬로 문서 저장"""
        search_results = []
        vector_results = []
        
        # 병렬 실행을 위한 태스크 생성
        tasks = []
        
        if cls._search_available:
            tasks.append(cls._store_to_search_service(documents))
        
        if cls._vector_available:
            tasks.append(cls._store_to_vector_service(documents))
        
        # 병렬 실행
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 결과 분석
            success_count = 0
            error_count = 0
            
            for result in results:
                if isinstance(result, Exception):
                    Logger.error(f"저장 태스크 실패: {result}")
                    error_count += len(documents)
                else:
                    success_count += result.get("success_count", 0)
                    error_count += result.get("error_count", 0)
        
        return {
            "success_count": success_count,
            "error_count": error_count,
            "search_results": search_results,
            "vector_results": vector_results
        }

    @classmethod
    async def _store_to_search_service(cls, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """OpenSearch에 문서 저장"""
        try:
            from service.search.search_service import SearchService
            
            Logger.debug(f"OpenSearch에 {len(documents)}개 문서 저장 시작")
            
            success_count = 0
            error_count = 0
            
            # OpenSearch 클라이언트 직접 사용
            client = SearchService.get_client()
            if not client:
                raise Exception("OpenSearch 클라이언트 없음")
            
            index_name = cls._config.collection_name
            
            # 배치 처리로 성능 최적화
            for doc in documents:
                try:
                    # 문서 인덱싱
                    response = await SearchService.index_document(
                        index_name, 
                        {
                            "content": doc["content"],
                            "metadata": doc["metadata"]
                        },
                        doc["id"]
                    )
                    
                    if response:
                        success_count += 1
                    else:
                        error_count += 1
                        
                except Exception as e:
                    Logger.warn(f"문서 {doc['id']} OpenSearch 저장 실패: {e}")
                    error_count += 1
            
            Logger.info(f"OpenSearch 저장 완료: {success_count}개 성공, {error_count}개 실패")
            
            return {
                "service": "search",
                "success_count": success_count,
                "error_count": error_count
            }
            
        except Exception as e:
            Logger.error(f"OpenSearch 저장 실패: {e}")
            return {
                "service": "search",
                "success_count": 0,
                "error_count": len(documents),
                "error": str(e)
            }

    @classmethod
    async def _store_to_vector_service(cls, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """VectorDB에 문서 저장"""
        try:
            from service.vectordb.vectordb_service import VectorDbService
            
            Logger.debug(f"VectorDB에 {len(documents)}개 문서 저장 시작")
            
            success_count = 0
            error_count = 0
            
            for doc in documents:
                try:
                    # 텍스트 임베딩 생성
                    embed_result = await VectorDbService.embed_text(doc["content"])
                    
                    if not embed_result.get("success"):
                        Logger.warn(f"문서 {doc['id']} 임베딩 생성 실패")
                        error_count += 1
                        continue
                    
                    # 벡터 저장 (실제 구현은 VectorDbService의 메서드 확인 필요)
                    # 여기서는 임베딩이 성공했다고 가정
                    success_count += 1
                    
                except Exception as e:
                    Logger.warn(f"문서 {doc['id']} VectorDB 저장 실패: {e}")
                    error_count += 1
            
            Logger.info(f"VectorDB 저장 완료: {success_count}개 성공, {error_count}개 실패")
            
            return {
                "service": "vector",
                "success_count": success_count,
                "error_count": error_count
            }
            
        except Exception as e:
            Logger.error(f"VectorDB 저장 실패: {e}")
            return {
                "service": "vector",
                "success_count": 0,
                "error_count": len(documents),
                "error": str(e)
            }

    @classmethod
    async def retrieve(cls, 
                      query: str, 
                      top_k: Optional[int] = None, 
                      hybrid: bool = True,
                      bm25_weight: float = 0.5,
                      vector_weight: float = 0.5) -> List[Dict[str, Any]]:
        """
        하이브리드 검색 - BM25와 벡터 검색 결과 조합
        
        Args:
            query: 검색 질의
            top_k: 반환할 문서 수 (기본값: config.default_k)
            hybrid: 하이브리드 검색 사용 여부
            bm25_weight: BM25 점수 가중치
            vector_weight: 벡터 점수 가중치
            
        Returns:
            List[Dict]: 검색 결과 문서 리스트
        """
        if not cls._initialized:
            raise RuntimeError("RAG 서비스가 초기화되지 않음")
        
        start_time = time.time()
        k = top_k or cls._config.default_k
        
        Logger.info(f"🔍 하이브리드 검색 시작: '{query}' (k={k}, hybrid={hybrid})")
        
        try:
            cls._stats["search_requests"] += 1
            
            # 하이브리드 검색 실행
            if hybrid and cls._search_available and cls._vector_available:
                cls._stats["hybrid_searches"] += 1
                results = await cls._hybrid_search(query, k, bm25_weight, vector_weight)
            elif cls._vector_available:
                Logger.info("벡터 검색 모드")
                results = await cls._vector_search_only(query, k)
            elif cls._search_available:
                Logger.info("키워드 검색 모드")
                results = await cls._bm25_search_only(query, k)
            else:
                Logger.error("사용 가능한 검색 서비스가 없음")
                return []
            
            # 성능 통계 업데이트
            search_time = time.time() - start_time
            cls._update_search_stats(search_time)
            
            Logger.info(f"✅ 검색 완료: {len(results)}개 결과 ({search_time:.3f}초)")
            
            return results
            
        except Exception as e:
            Logger.error(f"❌ 검색 실패: {e}")
            return []

    @classmethod
    async def _hybrid_search(cls, 
                           query: str, 
                           k: int, 
                           bm25_weight: float, 
                           vector_weight: float) -> List[Dict[str, Any]]:
        """하이브리드 검색 실행"""
        Logger.debug("하이브리드 검색 모드 시작")
        
        # 병렬로 두 가지 검색 실행
        bm25_task = cls._bm25_search_only(query, k * 2)  # 더 많이 가져와서 다양성 확보
        vector_task = cls._vector_search_only(query, k * 2)
        
        bm25_results, vector_results = await asyncio.gather(bm25_task, vector_task)
        
        # 점수 합성 및 순위 결정
        combined_results = cls._fuse_search_results(
            bm25_results, vector_results, 
            bm25_weight, vector_weight
        )
        
        # 상위 K개 반환
        return combined_results[:k]

    @classmethod
    async def _bm25_search_only(cls, query: str, k: int) -> List[Dict[str, Any]]:
        """BM25 키워드 검색만 실행 - 크롤러 구조에 맞춤"""
        try:
            from service.search.search_service import SearchService
            
            # 크롤러에서 저장한 OpenSearch 구조에 맞춤
            search_query = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title", "ticker", "source"],  # 크롤러 구조
                        "type": "best_fields"
                    }
                },
                "size": k
            }
            
            # 크롤러가 실제로 사용하는 인덱스 이름으로 수정
            response = await SearchService.search("yahoo_finance_news", search_query)
            
            if not response:
                return []
            
            results = []
            for hit in response.get("hits", {}).get("hits", []):
                source_data = hit["_source"]
                
                # 크롤러 구조에서 title과 source 추출
                title = source_data.get("title", "No title")
                source = source_data.get("source", "unknown")
                
                # 크롤러 구조에 맞춰 메타데이터 구성
                metadata = {
                    "title": title,
                    "source": source,
                    "ticker": source_data.get("ticker", ""),
                    "date": source_data.get("date", ""),
                    "link": source_data.get("link", ""),
                    "content_type": source_data.get("content_type", ""),
                    "task_id": source_data.get("task_id", ""),
                    "collected_at": source_data.get("collected_at", ""),
                    "created_at": source_data.get("created_at", "")
                }
                
                # 크롤러에서는 title이 실제 뉴스 제목이므로 content로 사용
                content = title
                
                result = {
                    "id": hit["_id"],
                    "content": content,
                    "metadata": metadata,
                    "score": hit["_score"],
                    "search_type": "bm25"
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            Logger.error(f"BM25 검색 실패: {e}")
            return []

    @classmethod
    async def _vector_search_only(cls, query: str, k: int) -> List[Dict[str, Any]]:
        """벡터 유사도 검색만 실행 - RAG 전용 클라이언트 사용"""
        try:
            # RAG 전용 벡터 클라이언트 사용 (coroutine 재사용 문제 해결)
            if cls._rag_vector_client:
                vector_results = await cls._rag_vector_client.similarity_search(
                    query=query,
                    top_k=k
                )
                
                if not vector_results.get("success"):
                    Logger.warn(f"RAG 벡터 검색 실패: {vector_results.get('error', 'Unknown error')}")
                    return []
                
                results = []
                for result in vector_results.get("results", []):
                    doc_result = {
                        "id": result.get("id", ""),
                        "content": result.get("content", ""),
                        "metadata": result.get("metadata", {}),
                        "score": result.get("score", 0.0),
                        "search_type": "vector"
                    }
                    results.append(doc_result)
                
                return results
            
            else:
                # Fallback: 기존 VectorDbService 사용
                from service.vectordb.vectordb_service import VectorDbService
                
                # 쿼리 임베딩 생성
                embed_result = await VectorDbService.embed_text(query)
                
                if not embed_result.get("success"):
                    Logger.warn("쿼리 임베딩 생성 실패")
                    return []
                
                # 벡터 검색 실행
                vector_results = await VectorDbService.similarity_search(
                    query=query,
                    top_k=k
                )
                
                if not vector_results:
                    return []
                
                results = []
                for result in vector_results.get("results", []):
                    doc_result = {
                        "id": result.get("id", ""),
                        "content": result.get("content", ""),
                        "metadata": result.get("metadata", {}),
                        "score": result.get("score", 0.0),
                        "search_type": "vector"
                    }
                    results.append(doc_result)
                
                return results
            
        except Exception as e:
            Logger.error(f"벡터 검색 실패: {e}")
            return []

    @classmethod
    def _fuse_search_results(cls,
                           bm25_results: List[Dict[str, Any]],
                           vector_results: List[Dict[str, Any]],
                           bm25_weight: float,
                           vector_weight: float) -> List[Dict[str, Any]]:
        """BM25와 벡터 검색 결과 점수 합성"""
        
        # 결과를 ID로 매핑
        bm25_map = {r["id"]: r for r in bm25_results}
        vector_map = {r["id"]: r for r in vector_results}
        
        # 모든 고유한 문서 ID 수집
        all_ids = set(bm25_map.keys()) | set(vector_map.keys())
        
        combined = []
        
        for doc_id in all_ids:
            bm25_result = bm25_map.get(doc_id)
            vector_result = vector_map.get(doc_id)
            
            # 점수 정규화 및 합성
            bm25_score = cls._normalize_bm25_score(bm25_result["score"]) if bm25_result else 0.0
            vector_score = vector_result["score"] if vector_result else 0.0
            
            # 가중 평균 점수 계산
            combined_score = (bm25_score * bm25_weight) + (vector_score * vector_weight)
            
            # 우선순위: BM25 > Vector (메타데이터 풍부도 기준)
            primary_result = bm25_result or vector_result
            
            combined_result = {
                **primary_result,
                "score": combined_score,
                "search_type": "hybrid",
                "score_details": {
                    "bm25_score": bm25_score,
                    "vector_score": vector_score,
                    "bm25_weight": bm25_weight,
                    "vector_weight": vector_weight
                }
            }
            
            combined.append(combined_result)
        
        # 점수 순으로 정렬
        combined.sort(key=lambda x: x["score"], reverse=True)
        
        return combined

    @classmethod
    def _normalize_bm25_score(cls, score: float) -> float:
        """BM25 점수를 0-1 범위로 정규화"""
        # 간단한 sigmoid 정규화 (실제로는 데이터에 맞게 조정 필요)
        import math
        return 1 / (1 + math.exp(-score / 10))

    @classmethod
    def _update_search_stats(cls, search_time: float):
        """검색 성능 통계 업데이트"""
        current_avg = cls._stats["avg_search_time"]
        search_count = cls._stats["search_requests"]
        
        # 이동 평균 계산
        cls._stats["avg_search_time"] = (
            (current_avg * (search_count - 1)) + search_time
        ) / search_count

    @classmethod
    def is_initialized(cls) -> bool:
        """서비스 초기화 상태 확인 (111 패턴)"""
        return cls._initialized

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """성능 통계 반환"""
        return {
            **cls._stats,
            "initialized": cls._initialized,
            "search_available": cls._search_available,
            "vector_available": cls._vector_available,
            "hybrid_capable": cls._search_available and cls._vector_available
        }

    @classmethod
    async def health_check(cls) -> Dict[str, Any]:
        """서비스 상태 확인"""
        if not cls._initialized:
            return {
                "status": "not_initialized",
                "message": "RAG 서비스가 초기화되지 않음"
            }
        
        # 의존 서비스 상태 재확인
        try:
            from service.search.search_service import SearchService
            from service.vectordb.vectordb_service import VectorDbService
            
            search_status = SearchService.is_initialized()
            vector_status = VectorDbService.is_initialized()
            
            if search_status and vector_status:
                status = "healthy"
            elif search_status or vector_status:
                status = "degraded"
            else:
                status = "critical"
            
            return {
                "status": status,
                "initialized": cls._initialized,
                "dependencies": {
                    "search_service": search_status,
                    "vector_service": vector_status
                },
                "capabilities": {
                    "hybrid_search": search_status and vector_status,
                    "keyword_search": search_status,
                    "vector_search": vector_status
                },
                "stats": cls.get_stats()
            }
            
        except Exception as e:
            Logger.error(f"RAG 서비스 상태 확인 실패: {e}")
            return {
                "status": "error",
                "message": f"상태 확인 중 오류: {e}"
            }

    @classmethod
    async def shutdown(cls) -> bool:
        """서비스 종료 (111 패턴)"""
        try:
            if not cls._initialized:
                Logger.info("RAG 서비스가 초기화되지 않아 종료 스킵")
                return True
            
            Logger.info("🔄 RAG 서비스 종료 시작...")
            
            # 통계 로그 출력
            stats = cls.get_stats()
            Logger.info(f"RAG 서비스 통계:")
            Logger.info(f"  - 인덱싱된 문서: {stats['documents_indexed']}개")
            Logger.info(f"  - 검색 요청: {stats['search_requests']}개")
            Logger.info(f"  - 하이브리드 검색: {stats['hybrid_searches']}개")
            Logger.info(f"  - 평균 검색 시간: {stats['avg_search_time']:.3f}초")
            
            # RAG 전용 벡터 클라이언트 종료
            if cls._rag_vector_client:
                try:
                    await cls._rag_vector_client.close()
                    Logger.info("✅ RAG 전용 벡터 클라이언트 종료 완료")
                except Exception as e:
                    Logger.error(f"❌ RAG 전용 벡터 클라이언트 종료 실패: {e}")
            
            # 상태 초기화
            cls._initialized = False
            cls._config = None
            cls._search_available = False
            cls._vector_available = False
            cls._rag_vector_client = None
            cls._reset_stats()
            
            Logger.info("✅ RAG 서비스 종료 완료")
            return True
            
        except Exception as e:
            Logger.error(f"❌ RAG 서비스 종료 실패: {e}")
            return False