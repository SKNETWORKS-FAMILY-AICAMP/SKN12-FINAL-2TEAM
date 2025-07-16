from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
import asyncio
from service.core.logger import Logger
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
    """VectorDB 클라이언트 풀 구현 - Session 재사용 패턴"""
    
    def __init__(self, config):
        self.config = config
        self._client_instance: Optional[IVectorDbClient] = None
        self._lock = asyncio.Lock()
        self._initialized = False
    
    async def _init_client(self):
        """클라이언트 초기화 (한 번만)"""
        if self._initialized:
            return
            
        async with self._lock:
            if self._initialized:
                return
                
            try:
                if self.config.vectordb_type == "bedrock":
                    # 단일 클라이언트 인스턴스 생성 (Session 공유)
                    self._client_instance = BedrockVectorDbClient(self.config)
                else:
                    raise ValueError(f"Unsupported vectordb type: {self.config.vectordb_type}")
                
                self._initialized = True
                Logger.info(f"VectorDB Pool initialized with {self.config.vectordb_type} client")
                
            except Exception as e:
                Logger.error(f"Failed to initialize VectorDB Pool: {e}")
                raise
    
    def new(self) -> IVectorDbClient:
        """VectorDB 클라이언트 반환 (Session 재사용)"""
        if not self._initialized:
            # 동기 컨텍스트에서 비동기 초기화 실행
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 이미 실행 중인 루프가 있으면 태스크 생성
                    task = asyncio.create_task(self._init_client())
                    # 짧은 대기 후 재시도
                    import time
                    time.sleep(0.1)
                else:
                    # 루프가 실행 중이 아니면 직접 실행
                    loop.run_until_complete(self._init_client())
            except RuntimeError:
                # 새 루프 생성하여 실행
                asyncio.run(self._init_client())
            
        if not self._client_instance:
            raise RuntimeError("VectorDB Pool not initialized")
            
        return self._client_instance
    
    async def get_client(self) -> IVectorDbClient:
        """비동기 클라이언트 가져오기"""
        await self._init_client()
        return self._client_instance
    
    async def close_all(self):
        """모든 클라이언트 종료"""
        if self._client_instance:
            await self._client_instance.close()
            self._client_instance = None
            
        self._initialized = False
        Logger.info("VectorDB Pool closed")
    
    def is_initialized(self) -> bool:
        """초기화 여부 확인"""
        return self._initialized
    
    async def health_check(self) -> Dict[str, Any]:
        """Pool 상태 확인"""
        try:
            if not self._initialized:
                return {"healthy": False, "error": "Pool not initialized"}
                
            if self._client_instance:
                return await self._client_instance.health_check()
            else:
                return {"healthy": False, "error": "Client instance not available"}
                
        except Exception as e:
            return {"healthy": False, "error": str(e)}