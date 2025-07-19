from typing import Dict, Any, Optional, List
from service.core.logger import Logger
from .search_config import SearchConfig
from .search_client_pool import SearchClientPool, ISearchClientPool

class SearchService:
    """Search 서비스 (정적 클래스) - 111 패턴"""
    
    _config: Optional[SearchConfig] = None
    _client_pool: Optional[ISearchClientPool] = None
    _initialized: bool = False
    
    @classmethod
    def init(cls, config: SearchConfig) -> bool:
        """서비스 초기화"""
        try:
            cls._config = config
            cls._client_pool = SearchClientPool(config)
            cls._initialized = True
            Logger.info("Search service initialized")
            return True
        except Exception as e:
            Logger.error(f"Search service init failed: {e}")
            return False
    
    @classmethod
    async def shutdown(cls):
        """서비스 종료"""
        if cls._initialized and cls._client_pool:
            await cls._client_pool.close_all()
            cls._client_pool = None
            cls._initialized = False
            Logger.info("Search service shutdown")
    
    @classmethod
    def is_initialized(cls) -> bool:
        """초기화 여부 확인"""
        return cls._initialized
    
    @classmethod
    def get_client(cls):
        """Search 클라이언트 가져오기"""
        if not cls._initialized:
            raise RuntimeError("SearchService not initialized")
        if not cls._client_pool:
            raise RuntimeError("SearchService client pool not available")
        return cls._client_pool.new()
    
    @classmethod
    async def create_test_index(cls, index: str) -> Dict[str, Any]:
        """테스트용 인덱스 생성 (유연한 매핑)"""
        try:
            client = cls.get_client()
            
            # 🔧 근본 해결: 동적 매핑 허용하는 유연한 스키마
            mappings = {
                "dynamic": True,  # 동적 필드 매핑 허용
                "properties": {
                    "content": {"type": "text", "analyzer": "standard"},
                    "message": {"type": "text", "analyzer": "standard"}, 
                    "timestamp": {"type": "long"},
                    "server_id": {"type": "keyword"}
                }
            }
            
            settings = {
                "number_of_shards": 1,
                "number_of_replicas": 0  # 테스트용이므로 복제본 없음
            }
            
            # async with 대신 직접 클라이언트 사용
            result = await client.create_index(index, mappings=mappings, settings=settings)
            Logger.info(f"테스트 인덱스 생성 성공: {index}")
            return result
                
        except Exception as e:
            Logger.error(f"테스트 인덱스 생성 실패: {e}")
            return {"success": False, "error": str(e)}
    
    # === 인덱스 관리 ===
    @classmethod
    async def create_index(cls, index: str, mappings: Optional[Dict] = None, settings: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """인덱스 생성"""
        client = cls.get_client()
        return await client.create_index(index, mappings, settings, **kwargs)
    
    @classmethod
    async def delete_index(cls, index: str, **kwargs) -> Dict[str, Any]:
        """인덱스 삭제"""
        client = cls.get_client()
        return await client.delete_index(index, **kwargs)
    
    @classmethod
    async def index_exists(cls, index: str, **kwargs) -> Dict[str, Any]:
        """인덱스 존재 확인"""
        client = cls.get_client()
        return await client.index_exists(index, **kwargs)
    
    # === 문서 관리 ===
    @classmethod
    async def index_document(cls, index: str, document: Dict[str, Any], doc_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """문서 인덱싱"""
        client = cls.get_client()
        return await client.index_document(index, document, doc_id, **kwargs)
    
    @classmethod
    async def get_document(cls, index: str, doc_id: str, **kwargs) -> Dict[str, Any]:
        """문서 조회"""
        client = cls.get_client()
        return await client.get_document(index, doc_id, **kwargs)
    
    @classmethod
    async def update_document(cls, index: str, doc_id: str, document: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """문서 업데이트"""
        client = cls.get_client()
        return await client.update_document(index, doc_id, document, **kwargs)
    
    @classmethod
    async def delete_document(cls, index: str, doc_id: str, **kwargs) -> Dict[str, Any]:
        """문서 삭제"""
        client = cls.get_client()
        return await client.delete_document(index, doc_id, **kwargs)
    
    # === 검색 ===
    @classmethod
    async def search(cls, index: str, query: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """검색"""
        client = cls.get_client()
        return await client.search(index, query, **kwargs)
    
    @classmethod
    async def bulk_index(cls, operations: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """벌크 인덱싱"""
        client = cls.get_client()
        return await client.bulk_index(operations, **kwargs)
    
    @classmethod
    async def scroll_search(cls, index: str, query: Dict[str, Any], scroll_time: str = "5m", **kwargs) -> Dict[str, Any]:
        """스크롤 검색"""
        client = cls.get_client()
        return await client.scroll_search(index, query, scroll_time, **kwargs)
    
    # === 모니터링 및 관리 메서드 ===
    @classmethod
    async def health_check(cls) -> Dict[str, Any]:
        """Search 서비스 Health Check"""
        if not cls._initialized:
            return {"healthy": False, "error": "Service not initialized"}
        
        try:
            client = cls.get_client()
            return await client.health_check()
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    @classmethod
    def get_metrics(cls) -> Dict[str, Any]:
        """Search 서비스 메트릭 조회"""
        if not cls._initialized:
            return {"error": "Service not initialized"}
        
        try:
            client = cls.get_client()
            client_metrics = client.get_metrics()
            
            return {
                "service_initialized": cls._initialized,
                "config": {
                    "hosts": cls._config.hosts if cls._config else [],
                    "default_index": getattr(cls._config, 'default_index', 'unknown')
                },
                "client_metrics": client_metrics
            }
        except Exception as e:
            return {"error": str(e)}
    
    @classmethod
    def reset_metrics(cls):
        """Search 서비스 메트릭 리셋"""
        if not cls._initialized:
            Logger.warn("Cannot reset metrics: Service not initialized")
            return
        
        try:
            client = cls.get_client()
            client.reset_metrics()
            Logger.info("Search service metrics reset")
        except Exception as e:
            Logger.error(f"Failed to reset search metrics: {e}")
    
    @classmethod
    async def cluster_info(cls) -> Dict[str, Any]:
        """OpenSearch 클러스터 정보 조회"""
        if not cls._initialized:
            return {"error": "Service not initialized"}
        
        try:
            client = cls.get_client()
            
            # 기본 인덱스 존재 확인
            default_index = getattr(cls._config, 'default_index', 'test-index')
            index_result = await client.index_exists(default_index)
            
            return {
                "service_status": "initialized",
                "default_index": default_index,
                "default_index_exists": index_result.get("exists", False),
                "hosts": cls._config.hosts if cls._config else [],
                "health_check": await cls.health_check()
            }
        except Exception as e:
            return {"error": str(e)}