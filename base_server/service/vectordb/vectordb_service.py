from typing import Dict, Any, Optional, List
from service.core.logger import Logger
from .vectordb_config import VectorDbConfig
from .vectordb_client_pool import VectorDbClientPool, IVectorDbClientPool

class VectorDbService:
    """VectorDB 서비스 (정적 클래스) - 111 패턴"""
    
    _config: Optional[VectorDbConfig] = None
    _client_pool: Optional[IVectorDbClientPool] = None
    _initialized: bool = False
    
    @classmethod
    def init(cls, config: VectorDbConfig) -> bool:
        """서비스 초기화"""
        try:
            cls._config = config
            cls._client_pool = VectorDbClientPool(config)
            cls._initialized = True
            Logger.info("VectorDB service initialized")
            return True
        except Exception as e:
            Logger.error(f"VectorDB service init failed: {e}")
            return False
    
    @classmethod
    async def shutdown(cls):
        """서비스 종료"""
        if cls._initialized and cls._client_pool:
            await cls._client_pool.close_all()
            cls._client_pool = None
            cls._initialized = False
            Logger.info("VectorDB service shutdown")
    
    @classmethod
    def is_initialized(cls) -> bool:
        """초기화 여부 확인"""
        return cls._initialized
    
    @classmethod
    def get_client(cls):
        """VectorDB 클라이언트 가져오기"""
        if not cls._initialized:
            raise RuntimeError("VectorDbService not initialized")
        if not cls._client_pool:
            raise RuntimeError("VectorDbService client pool not available")
        return cls._client_pool.new()
    
    # === 임베딩 ===
    @classmethod
    async def embed_text(cls, text: str, **kwargs) -> Dict[str, Any]:
        """텍스트를 벡터로 임베딩"""
        if not cls._initialized:
            raise RuntimeError("VectorDbService not initialized")
        if not cls._client_pool:
            raise RuntimeError("VectorDbService client pool not available")
        
        # 항상 비동기 방식으로 클라이언트 가져오기
        client = await cls._client_pool.get_client()
        return await client.embed_text(text, **kwargs)
    
    @classmethod
    async def embed_texts(cls, texts: List[str], **kwargs) -> Dict[str, Any]:
        """여러 텍스트를 벡터로 임베딩"""
        if not cls._initialized:
            raise RuntimeError("VectorDbService not initialized")
        if not cls._client_pool:
            raise RuntimeError("VectorDbService client pool not available")
        client = await cls._client_pool.get_client()
        return await client.embed_texts(texts, **kwargs)
    
    # === 검색 ===
    @classmethod
    async def similarity_search(cls, query: str, top_k: int = 10, **kwargs) -> Dict[str, Any]:
        """유사도 검색"""
        if not cls._initialized:
            raise RuntimeError("VectorDbService not initialized")
        if not cls._client_pool:
            raise RuntimeError("VectorDbService client pool not available")
        client = await cls._client_pool.get_client()
        return await client.similarity_search(query, top_k, **kwargs)
    
    @classmethod
    async def similarity_search_by_vector(cls, vector: List[float], top_k: int = 10, **kwargs) -> Dict[str, Any]:
        """벡터로 유사도 검색"""
        if not cls._initialized:
            raise RuntimeError("VectorDbService not initialized")
        if not cls._client_pool:
            raise RuntimeError("VectorDbService client pool not available")
        client = await cls._client_pool.get_client()
        return await client.similarity_search_by_vector(vector, top_k, **kwargs)
    
    # === 문서 관리 ===
    @classmethod
    async def add_documents(cls, documents: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """문서 추가"""
        if not cls._initialized:
            raise RuntimeError("VectorDbService not initialized")
        if not cls._client_pool:
            raise RuntimeError("VectorDbService client pool not available")
        client = await cls._client_pool.get_client()
        return await client.add_documents(documents, **kwargs)
    
    @classmethod
    async def delete_documents(cls, document_ids: List[str], **kwargs) -> Dict[str, Any]:
        """문서 삭제"""
        if not cls._initialized:
            raise RuntimeError("VectorDbService not initialized")
        if not cls._client_pool:
            raise RuntimeError("VectorDbService client pool not available")
        client = await cls._client_pool.get_client()
        return await client.delete_documents(document_ids, **kwargs)
    
    @classmethod
    async def update_document(cls, document_id: str, document: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """문서 업데이트"""
        if not cls._initialized:
            raise RuntimeError("VectorDbService not initialized")
        if not cls._client_pool:
            raise RuntimeError("VectorDbService client pool not available")
        client = await cls._client_pool.get_client()
        return await client.update_document(document_id, document, **kwargs)
    
    @classmethod
    async def get_document(cls, document_id: str, **kwargs) -> Dict[str, Any]:
        """문서 조회"""
        if not cls._initialized:
            raise RuntimeError("VectorDbService not initialized")
        if not cls._client_pool:
            raise RuntimeError("VectorDbService client pool not available")
        client = await cls._client_pool.get_client()
        return await client.get_document(document_id, **kwargs)
    
    # === 텍스트 생성 ===
    @classmethod
    async def generate_text(cls, prompt: str, **kwargs) -> Dict[str, Any]:
        """텍스트 생성"""
        if not cls._initialized:
            raise RuntimeError("VectorDbService not initialized")
        if not cls._client_pool:
            raise RuntimeError("VectorDbService client pool not available")
        client = await cls._client_pool.get_client()
        return await client.generate_text(prompt, **kwargs)
    
    @classmethod
    async def chat_completion(cls, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """채팅 완성"""
        if not cls._initialized:
            raise RuntimeError("VectorDbService not initialized")
        if not cls._client_pool:
            raise RuntimeError("VectorDbService client pool not available")
        client = await cls._client_pool.get_client()
        return await client.chat_completion(messages, **kwargs)
    
    # === Knowledge Base 전용 메서드 ===
    @classmethod
    async def retrieve_from_knowledge_base(cls, query: str, top_k: int = 10, **kwargs) -> Dict[str, Any]:
        """Knowledge Base에서 문서 검색"""
        if not cls._initialized:
            raise RuntimeError("VectorDbService not initialized")
        if not cls._client_pool:
            raise RuntimeError("VectorDbService client pool not available")
        client = await cls._client_pool.get_client()
        return await client.similarity_search(query, top_k, **kwargs)
    
    @classmethod
    async def rag_generate(cls, query: str, **kwargs) -> Dict[str, Any]:
        """RAG 기반 답변 생성 (Knowledge Base + Text Generation)"""
        if not cls._initialized:
            raise RuntimeError("VectorDbService not initialized")
        
        try:
            # Knowledge Base에서 관련 문서 검색
            search_result = await cls.retrieve_from_knowledge_base(query, **kwargs)
            
            if not search_result.get('success', False):
                return {
                    "success": False,
                    "error": "Knowledge base search failed",
                    "search_error": search_result.get('error', 'Unknown error')
                }
            
            # 검색 결과를 컨텍스트로 사용하여 답변 생성
            context_docs = search_result.get('results', [])
            if not context_docs:
                return {
                    "success": False,
                    "error": "No relevant documents found in knowledge base"
                }
            
            # 컨텍스트 구성
            context = "\n\n".join([f"Document {i+1}: {doc['content']}" for i, doc in enumerate(context_docs)])
            
            # RAG 프롬프트 생성
            rag_prompt = f"""Based on the following context documents, please answer the question.

Context:
{context}

Question: {query}

Answer:"""
            
            # 답변 생성
            generation_result = await cls.generate_text(rag_prompt, **kwargs)
            
            if generation_result.get('success', False):
                return {
                    "success": True,
                    "query": query,
                    "answer": generation_result['generated_text'],
                    "context_documents": context_docs,
                    "search_time": search_result.get('search_time', 0),
                    "generation_time": generation_result.get('generation_time', 0)
                }
            else:
                return {
                    "success": False,
                    "error": "Text generation failed",
                    "generation_error": generation_result.get('error', 'Unknown error'),
                    "context_documents": context_docs
                }
                
        except Exception as e:
            Logger.error(f"RAG generation failed: {e}")
            return {
                "success": False,
                "error": f"RAG generation failed: {str(e)}"
            }
    
    @classmethod
    async def knowledge_base_sync_status(cls) -> Dict[str, Any]:
        """Knowledge Base 동기화 상태 확인"""
        if not cls._initialized:
            return {"error": "Service not initialized"}
        
        try:
            # Knowledge Base 상태 확인 (구현 필요)
            return {
                "knowledge_base_id": getattr(cls._config, 'knowledge_base_id', None),
                "status": "active",  # 실제 구현 시 API 호출 필요
                "last_sync_time": None  # 실제 구현 시 API 호출 필요
            }
        except Exception as e:
            return {"error": str(e)}

    # === Knowledge Base 관리 ===
    @classmethod
    async def start_ingestion_job(cls, data_source_id: str, **kwargs) -> Dict[str, Any]:
        """Knowledge Base 동기화 작업 시작"""
        if not cls._initialized:
            raise RuntimeError("VectorDbService not initialized")
        if not cls._client_pool:
            raise RuntimeError("VectorDbService client pool not available")
        client = await cls._client_pool.get_client()
        return await client.start_ingestion_job(data_source_id, **kwargs)

    @classmethod
    async def get_ingestion_job(cls, data_source_id: str, ingestion_job_id: str, **kwargs) -> Dict[str, Any]:
        """Knowledge Base 동기화 작업 상태 조회"""
        if not cls._initialized:
            raise RuntimeError("VectorDbService not initialized")
        if not cls._client_pool:
            raise RuntimeError("VectorDbService client pool not available")
        client = await cls._client_pool.get_client()
        return await client.get_ingestion_job(data_source_id, ingestion_job_id, **kwargs)

    @classmethod
    async def get_knowledge_base_status(cls, **kwargs) -> Dict[str, Any]:
        """Knowledge Base 상태 조회"""
        if not cls._initialized:
            raise RuntimeError("VectorDbService not initialized")
        if not cls._client_pool:
            raise RuntimeError("VectorDbService client pool not available")
        client = await cls._client_pool.get_client()
        return await client.get_knowledge_base_status(**kwargs)

    @classmethod
    async def search_similar(cls, query_text: str, filter: Dict[str, Any] = None, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """유사도 검색 (호환성을 위한 별칭)"""
        return await cls.similarity_search(query_text, limit, **kwargs)

    @classmethod
    async def retrieve_from_knowledge_base(cls, query: str, **kwargs) -> Dict[str, Any]:
        """Knowledge Base에서 문서 검색 (호환성을 위한 별칭)"""
        search_result = await cls.similarity_search(query, **kwargs)
        if search_result.get('success'):
            return {
                "success": True,
                "results": search_result.get('results', []),
                "search_time": search_result.get('search_time', 0)
            }
        else:
            return search_result
    
    # === 모니터링 및 관리 메서드 ===
    @classmethod
    async def health_check(cls) -> Dict[str, Any]:
        """VectorDB 서비스 Health Check"""
        if not cls._initialized:
            return {"healthy": False, "error": "Service not initialized"}
        
        try:
            client = cls.get_client()
            return await client.health_check()
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    @classmethod
    def get_metrics(cls) -> Dict[str, Any]:
        """VectorDB 서비스 메트릭 조회"""
        if not cls._initialized:
            return {"error": "Service not initialized"}
        
        try:
            client = cls.get_client()
            client_metrics = client.get_metrics()
            
            return {
                "service_initialized": cls._initialized,
                "config": {
                    "aws_region": cls._config.region_name if cls._config else 'unknown',
                    "embedding_model": getattr(cls._config, 'embedding_model', 'unknown'),
                    "text_model": getattr(cls._config, 'text_model', 'unknown'),
                    "knowledge_base_id": getattr(cls._config, 'knowledge_base_id', None)
                },
                "client_metrics": client_metrics
            }
        except Exception as e:
            return {"error": str(e)}
    
    @classmethod
    def reset_metrics(cls):
        """VectorDB 서비스 메트릭 리셋"""
        if not cls._initialized:
            Logger.warn("Cannot reset metrics: Service not initialized")
            return
        
        try:
            client = cls.get_client()
            client.reset_metrics()
            Logger.info("VectorDB service metrics reset")
        except Exception as e:
            Logger.error(f"Failed to reset VectorDB metrics: {e}")
    
    @classmethod
    async def service_info(cls) -> Dict[str, Any]:
        """VectorDB 서비스 정보 조회"""
        if not cls._initialized:
            return {"error": "Service not initialized"}
        
        try:
            # 기본 임베딩 테스트
            test_result = await cls.embed_text("test embedding")
            
            return {
                "service_status": "initialized",
                "aws_region": cls._config.region_name if cls._config else 'unknown',
                "embedding_model": getattr(cls._config, 'embedding_model', 'unknown'),
                "text_model": getattr(cls._config, 'text_model', 'unknown'),
                "knowledge_base_id": getattr(cls._config, 'knowledge_base_id', None),
                "test_embedding_success": test_result.get("success", False),
                "health_check": await cls.health_check()
            }
        except Exception as e:
            return {"error": str(e)}