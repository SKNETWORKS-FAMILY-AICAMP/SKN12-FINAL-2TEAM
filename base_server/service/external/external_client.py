from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class IExternalClient(ABC):
    """External API 클라이언트 인터페이스"""
    
    @abstractmethod
    async def start(self):
        """클라이언트 시작"""
        pass
    
    @abstractmethod
    async def close(self):
        """클라이언트 종료"""
        pass
    
    @abstractmethod
    async def request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """HTTP 요청"""
        pass
    
    @abstractmethod
    async def get(self, url: str, **kwargs) -> Dict[str, Any]:
        """GET 요청"""
        pass
    
    @abstractmethod
    async def post(self, url: str, **kwargs) -> Dict[str, Any]:
        """POST 요청"""
        pass

class ExternalClient(IExternalClient):
    """기본 External 클라이언트 구현"""
    
    def __init__(self, api_name: str, config):
        self.api_name = api_name
        self.config = config
        self._session = None
    
    async def start(self):
        """클라이언트 시작"""
        pass
    
    async def close(self):
        """클라이언트 종료"""
        if self._session:
            await self._session.close()
            self._session = None
    
    async def request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """HTTP 요청 기본 구현"""
        return {
            "success": False,
            "error": "Base implementation - override required"
        }
    
    async def get(self, url: str, **kwargs) -> Dict[str, Any]:
        """GET 요청"""
        return await self.request("GET", url, **kwargs)
    
    async def post(self, url: str, **kwargs) -> Dict[str, Any]:
        """POST 요청"""
        return await self.request("POST", url, **kwargs)