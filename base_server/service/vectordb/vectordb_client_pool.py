from abc import ABC, abstractmethod
from typing import Dict
from .vectordb_client import IVectorDbClient
from .bedrock_vectordb_client import BedrockVectorDbClient

class IVectorDbClientPool(ABC):
    """VectorDB 클라이언트 풀 인터페이스"""
    
    @abstractmethod
    def new(self) -> IVectorDbClient:
        """새 VectorDB 클라이언트 생성"""
        pass
    
    @abstractmethod
    async def close_all(self):
        """모든 클라이언트 종료"""
        pass

class VectorDbClientPool(IVectorDbClientPool):
    """VectorDB 클라이언트 풀 구현"""
    
    def __init__(self, config):
        self.config = config
        self._clients: Dict[str, IVectorDbClient] = {}
    
    def new(self) -> IVectorDbClient:
        """새 VectorDB 클라이언트 생성"""
        client_id = f"vectordb_client_{len(self._clients)}"
        
        if self.config.vectordb_type == "bedrock":
            client = BedrockVectorDbClient(self.config)
        else:
            raise ValueError(f"Unsupported vectordb type: {self.config.vectordb_type}")
        
        self._clients[client_id] = client
        return client
    
    async def close_all(self):
        """모든 클라이언트 종료"""
        for client in self._clients.values():
            await client.close()
        self._clients.clear()