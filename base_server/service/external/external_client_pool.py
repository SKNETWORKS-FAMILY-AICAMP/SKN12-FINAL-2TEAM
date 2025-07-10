from abc import ABC, abstractmethod
from typing import Dict, Any
from .external_client import IExternalClient
from .http_external_client import HttpExternalClient

class IExternalClientPool(ABC):
    """External 클라이언트 풀 인터페이스"""
    
    @abstractmethod
    def new(self, api_name: str) -> IExternalClient:
        """새 클라이언트 생성"""
        pass
    
    @abstractmethod
    async def close_all(self):
        """모든 클라이언트 종료"""
        pass

class ExternalClientPool(IExternalClientPool):
    """External 클라이언트 풀 구현"""
    
    def __init__(self, config):
        self.config = config
        self._clients: Dict[str, IExternalClient] = {}
    
    def new(self, api_name: str) -> IExternalClient:
        """새 클라이언트 생성 또는 기존 클라이언트 반환"""
        if api_name not in self._clients:
            if api_name in self.config.apis:
                api_config = self.config.apis[api_name]
                # HTTP 클라이언트 생성
                client = HttpExternalClient(
                    api_name=api_name,
                    api_config=api_config,
                    proxy_config=self.config.proxy
                )
                self._clients[api_name] = client
            else:
                raise ValueError(f"Unknown API: {api_name}")
        
        return self._clients[api_name]
    
    async def close_all(self):
        """모든 클라이언트 종료"""
        for client in self._clients.values():
            await client.close()
        self._clients.clear()