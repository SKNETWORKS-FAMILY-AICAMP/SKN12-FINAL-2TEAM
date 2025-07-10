from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class IVectorDbClient(ABC):
    """VectorDB 클라이언트 인터페이스"""
    
    @abstractmethod
    async def embed_text(self, text: str, **kwargs) -> Dict[str, Any]:
        """텍스트를 벡터로 임베딩"""
        pass
    
    @abstractmethod
    async def embed_texts(self, texts: List[str], **kwargs) -> Dict[str, Any]:
        """여러 텍스트를 벡터로 임베딩"""
        pass
    
    @abstractmethod
    async def similarity_search(self, query: str, top_k: int = 10, **kwargs) -> Dict[str, Any]:
        """유사도 검색"""
        pass
    
    @abstractmethod
    async def similarity_search_by_vector(self, vector: List[float], top_k: int = 10, **kwargs) -> Dict[str, Any]:
        """벡터로 유사도 검색"""
        pass
    
    @abstractmethod
    async def add_documents(self, documents: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """문서 추가"""
        pass
    
    @abstractmethod
    async def delete_documents(self, document_ids: List[str], **kwargs) -> Dict[str, Any]:
        """문서 삭제"""
        pass
    
    @abstractmethod
    async def update_document(self, document_id: str, document: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """문서 업데이트"""
        pass
    
    @abstractmethod
    async def get_document(self, document_id: str, **kwargs) -> Dict[str, Any]:
        """문서 조회"""
        pass
    
    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """텍스트 생성"""
        pass
    
    @abstractmethod
    async def chat_completion(self, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """채팅 완성"""
        pass
    
    @abstractmethod
    async def close(self):
        """클라이언트 종료"""
        pass