from abc import ABC, abstractmethod
from typing import Dict
from .search_client import ISearchClient
from .opensearch_client import OpenSearchClient

class ISearchClientPool(ABC):
    """Search 클라이언트 풀 인터페이스"""
    
    @abstractmethod
    def new(self) -> ISearchClient:
        """새 Search 클라이언트 생성"""
        pass
    
    @abstractmethod
    async def close_all(self):
        """모든 클라이언트 종료"""
        pass

class SearchClientPool(ISearchClientPool):
    """Search 클라이언트 풀 구현"""
    
    def __init__(self, config):
        self.config = config
        self._clients: Dict[str, ISearchClient] = {}
    
    def new(self) -> ISearchClient:
        """새 Search 클라이언트 생성"""
        client_id = f"search_client_{len(self._clients)}"
        
        if self.config.search_type == "opensearch":
            client = OpenSearchClient(self.config)
        else:
            raise ValueError(f"Unsupported search type: {self.config.search_type}")
        
        self._clients[client_id] = client
        return client
    
    async def close_all(self):
        """모든 클라이언트 종료"""
        for client in self._clients.values():
            await client.close()
        self._clients.clear()