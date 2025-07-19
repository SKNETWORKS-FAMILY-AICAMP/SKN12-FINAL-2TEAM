from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
import asyncio
import aioboto3
from contextlib import AsyncExitStack
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
        self._exit_stack: Optional[AsyncExitStack] = None
    
    async def _init_session(self):
        """Session 초기화 (한 번만)"""
        if self._initialized:
            return
            
        async with self._lock:
            if self._initialized:
                return
                
            try:
                if self.config.storage_type == "s3":
                    # AsyncExitStack 생성 (적절한 리소스 관리)
                    self._exit_stack = AsyncExitStack()
                    
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
                    
                    # AsyncExitStack을 사용하여 클라이언트 생성 및 관리
                    self._s3_client = await self._exit_stack.enter_async_context(
                        self._session.client('s3', config=boto_config)
                    )
                    
                    # 단일 클라이언트 인스턴스 생성 (Session 공유)
                    self._client_instance = S3StorageClient(
                        config=self.config,
                        session=self._session,
                        s3_client=self._s3_client
                    )
                    
                    self._initialized = True
                    Logger.info(f"S3 Storage Pool initialized with AsyncExitStack for region: {region_name}")
                else:
                    raise ValueError(f"Unsupported storage type: {self.config.storage_type}")
                    
            except Exception as e:
                Logger.error(f"Failed to initialize Storage Pool: {e}")
                # 오류 발생 시 exit_stack 정리
                if self._exit_stack:
                    await self._exit_stack.__aexit__(None, None, None)
                    self._exit_stack = None
                raise
    
    def new(self) -> IStorageClient:
        """Storage 클라이언트 반환 (Session 재사용)"""
        if not self._initialized:
            # 🔧 근본 수정: 동기 컨텍스트에서 비동기 초기화를 완료까지 대기
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 실행 중인 루프에서는 동기적으로 대기할 수 없음
                    raise RuntimeError("Cannot initialize Storage Pool from running event loop. Use async get_client() instead.")
                else:
                    # 루프가 실행 중이 아니면 직접 실행
                    loop.run_until_complete(self._init_session())
            except RuntimeError as e:
                if "Cannot initialize" in str(e):
                    raise e
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
            
        # AsyncExitStack을 사용하여 모든 리소스 정리
        if self._exit_stack:
            try:
                await self._exit_stack.__aexit__(None, None, None)
            except Exception as e:
                Logger.warn(f"AsyncExitStack close warning: {e}")
            finally:
                self._exit_stack = None
                self._s3_client = None
            
        if self._session:
            try:
                # aioboto3 Session에는 close 메서드가 없음
                # Session 객체는 자동으로 정리됨
                Logger.debug("S3 Session cleanup (no close method needed)")
            except Exception as e:
                Logger.warn(f"Session close warning: {e}")
            finally:
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