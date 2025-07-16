from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
import asyncio
import aioboto3
from botocore.config import Config
from service.core.logger import Logger
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
    """Storage 클라이언트 풀 구현 - Session 재사용 패턴"""
    
    def __init__(self, config):
        self.config = config
        self._session: Optional[aioboto3.Session] = None
        self._s3_client = None
        self._client_instance: Optional[IStorageClient] = None
        self._lock = asyncio.Lock()
        self._initialized = False
    
    async def _init_session(self):
        """Session 초기화 (한 번만)"""
        if self._initialized:
            return
            
        async with self._lock:
            if self._initialized:
                return
                
            try:
                if self.config.storage_type == "s3":
                    # aioboto3 Session 생성 (재사용)
                    if isinstance(self.config, dict):
                        aws_access_key_id = self.config.get('aws_access_key_id')
                        aws_secret_access_key = self.config.get('aws_secret_access_key')
                        aws_session_token = self.config.get('aws_session_token')
                        region_name = self.config.get('region_name')
                    else:
                        aws_access_key_id = self.config.aws_access_key_id
                        aws_secret_access_key = self.config.aws_secret_access_key
                        aws_session_token = getattr(self.config, 'aws_session_token', None)
                        region_name = self.config.region_name
                    
                    self._session = aioboto3.Session(
                        aws_access_key_id=aws_access_key_id,
                        aws_secret_access_key=aws_secret_access_key,
                        aws_session_token=aws_session_token,
                        region_name=region_name
                    )
                    
                    # S3 클라이언트 생성 (Connection Pool 설정)
                    boto_config = Config(
                        retries={'max_attempts': 3, 'mode': 'adaptive'},
                        max_pool_connections=50,  # Connection Pool 크기
                        region_name=region_name
                    )
                    
                    self._s3_client = self._session.client('s3', config=boto_config)
                    
                    # 단일 클라이언트 인스턴스 생성 (Session 공유)
                    self._client_instance = S3StorageClient(
                        config=self.config,
                        session=self._session,
                        s3_client=self._s3_client
                    )
                    
                    self._initialized = True
                    Logger.info(f"S3 Storage Pool initialized with session reuse for region: {region_name}")
                else:
                    raise ValueError(f"Unsupported storage type: {self.config.storage_type}")
                    
            except Exception as e:
                Logger.error(f"Failed to initialize Storage Pool: {e}")
                raise
    
    def new(self) -> IStorageClient:
        """Storage 클라이언트 반환 (Session 재사용)"""
        if not self._initialized:
            # 동기 컨텍스트에서 비동기 초기화 실행
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 이미 실행 중인 루프가 있으면 태스크 생성
                    task = asyncio.create_task(self._init_session())
                    # 짧은 대기 후 재시도
                    import time
                    time.sleep(0.1)
                else:
                    # 루프가 실행 중이 아니면 직접 실행
                    loop.run_until_complete(self._init_session())
            except RuntimeError:
                # 새 루프 생성하여 실행
                asyncio.run(self._init_session())
            
        if not self._client_instance:
            raise RuntimeError("Storage Pool not initialized")
            
        return self._client_instance
    
    async def get_client(self) -> IStorageClient:
        """비동기 클라이언트 가져오기"""
        await self._init_session()
        return self._client_instance
    
    async def close_all(self):
        """모든 클라이언트 종료"""
        if self._client_instance:
            await self._client_instance.close()
            self._client_instance = None
            
        if self._s3_client:
            await self._s3_client.close()
            self._s3_client = None
            
        if self._session:
            await self._session.close()
            self._session = None
            
        self._initialized = False
        Logger.info("Storage Pool closed")
    
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