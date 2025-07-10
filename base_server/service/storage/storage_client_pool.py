from abc import ABC, abstractmethod
from typing import Dict
from .storage_client import IStorageClient
from .s3_storage_client import S3StorageClient

class IStorageClientPool(ABC):
    """Storage 클라이언트 풀 인터페이스"""
    
    @abstractmethod
    def new(self) -> IStorageClient:
        """새 Storage 클라이언트 생성"""
        pass
    
    @abstractmethod
    async def close_all(self):
        """모든 클라이언트 종료"""
        pass

class StorageClientPool(IStorageClientPool):
    """Storage 클라이언트 풀 구현"""
    
    def __init__(self, config):
        self.config = config
        self._clients: Dict[str, IStorageClient] = {}
    
    def new(self) -> IStorageClient:
        """새 Storage 클라이언트 생성"""
        client_id = f"storage_client_{len(self._clients)}"
        
        if self.config.storage_type == "s3":
            client = S3StorageClient(self.config)
        else:
            raise ValueError(f"Unsupported storage type: {self.config.storage_type}")
        
        self._clients[client_id] = client
        return client
    
    async def close_all(self):
        """모든 클라이언트 종료"""
        for client in self._clients.values():
            await client.close()
        self._clients.clear()