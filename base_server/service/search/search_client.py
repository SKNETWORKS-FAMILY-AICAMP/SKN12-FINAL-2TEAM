from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class ISearchClient(ABC):
    """Search 클라이언트 인터페이스"""
    
    @abstractmethod
    async def create_index(self, index: str, mappings: Optional[Dict] = None, settings: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """인덱스 생성"""
        pass
    
    @abstractmethod
    async def delete_index(self, index: str, **kwargs) -> Dict[str, Any]:
        """인덱스 삭제"""
        pass
    
    @abstractmethod
    async def index_exists(self, index: str, **kwargs) -> Dict[str, Any]:
        """인덱스 존재 확인"""
        pass
    
    @abstractmethod
    async def index_document(self, index: str, document: Dict[str, Any], doc_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """문서 인덱싱"""
        pass
    
    @abstractmethod
    async def get_document(self, index: str, doc_id: str, **kwargs) -> Dict[str, Any]:
        """문서 조회"""
        pass
    
    @abstractmethod
    async def update_document(self, index: str, doc_id: str, document: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """문서 업데이트"""
        pass
    
    @abstractmethod
    async def delete_document(self, index: str, doc_id: str, **kwargs) -> Dict[str, Any]:
        """문서 삭제"""
        pass
    
    @abstractmethod
    async def search(self, index: str, query: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """검색"""
        pass
    
    @abstractmethod
    async def bulk_index(self, operations: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """벌크 인덱싱"""
        pass
    
    @abstractmethod
    async def scroll_search(self, index: str, query: Dict[str, Any], scroll_time: str = "5m", **kwargs) -> Dict[str, Any]:
        """스크롤 검색"""
        pass
    
    @abstractmethod
    async def close(self):
        """클라이언트 종료"""
        pass