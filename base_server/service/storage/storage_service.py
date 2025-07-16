from typing import Dict, Any, Optional, BinaryIO
from service.core.logger import Logger
from .storage_config import StorageConfig
from .storage_client_pool import StorageClientPool, IStorageClientPool

class StorageService:
    """Storage 서비스 (정적 클래스) - 111 패턴"""
    
    _config: Optional[StorageConfig] = None
    _client_pool: Optional[IStorageClientPool] = None
    _initialized: bool = False
    
    @classmethod
    def init(cls, config: StorageConfig) -> bool:
        """서비스 초기화"""
        try:
            cls._config = config
            cls._client_pool = StorageClientPool(config)
            cls._initialized = True
            Logger.info("Storage service initialized")
            return True
        except Exception as e:
            Logger.error(f"Storage service init failed: {e}")
            return False
    
    @classmethod
    async def shutdown(cls):
        """서비스 종료"""
        if cls._initialized and cls._client_pool:
            await cls._client_pool.close_all()
            cls._client_pool = None
            cls._initialized = False
            Logger.info("Storage service shutdown")
    
    @classmethod
    def is_initialized(cls) -> bool:
        """초기화 여부 확인"""
        return cls._initialized
    
    @classmethod
    def get_client(cls):
        """Storage 클라이언트 가져오기"""
        if not cls._initialized:
            raise RuntimeError("StorageService not initialized")
        if not cls._client_pool:
            raise RuntimeError("StorageService client pool not available")
        return cls._client_pool.new()
    
    # === 파일 업로드 ===
    @classmethod
    async def upload_file(cls, bucket: str, key: str, file_path: str, **kwargs) -> Dict[str, Any]:
        """파일 업로드"""
        if hasattr(cls._client_pool, 'get_client'):
            client = await cls._client_pool.get_client()
        else:
            client = cls.get_client()
        return await client.upload_file(bucket, key, file_path, **kwargs)
    
    @classmethod
    async def upload_file_obj(cls, bucket: str, key: str, file_obj: BinaryIO, **kwargs) -> Dict[str, Any]:
        """파일 객체 업로드"""
        client = cls.get_client()
        return await client.upload_file_obj(bucket, key, file_obj, **kwargs)
    
    # === 파일 다운로드 ===
    @classmethod
    async def download_file(cls, bucket: str, key: str, file_path: str, **kwargs) -> Dict[str, Any]:
        """파일 다운로드"""
        client = cls.get_client()
        return await client.download_file(bucket, key, file_path, **kwargs)
    
    @classmethod
    async def download_file_obj(cls, bucket: str, key: str, **kwargs) -> Dict[str, Any]:
        """파일 객체로 다운로드"""
        client = cls.get_client()
        return await client.download_file_obj(bucket, key, **kwargs)
    
    # === 파일 관리 ===
    @classmethod
    async def delete_file(cls, bucket: str, key: str, **kwargs) -> Dict[str, Any]:
        """파일 삭제"""
        client = cls.get_client()
        return await client.delete_file(bucket, key, **kwargs)
    
    @classmethod
    async def list_files(cls, bucket: str, prefix: str = "", **kwargs) -> Dict[str, Any]:
        """파일 목록 조회"""
        if hasattr(cls._client_pool, 'get_client'):
            client = await cls._client_pool.get_client()
        else:
            client = cls.get_client()
        return await client.list_files(bucket, prefix, **kwargs)
    
    @classmethod
    async def get_file_info(cls, bucket: str, key: str, **kwargs) -> Dict[str, Any]:
        """파일 정보 조회"""
        client = cls.get_client()
        return await client.get_file_info(bucket, key, **kwargs)
    
    @classmethod
    async def copy_file(cls, source_bucket: str, source_key: str, dest_bucket: str, dest_key: str, **kwargs) -> Dict[str, Any]:
        """파일 복사"""
        client = cls.get_client()
        return await client.copy_file(source_bucket, source_key, dest_bucket, dest_key, **kwargs)
    
    @classmethod
    async def move_file(cls, source_bucket: str, source_key: str, dest_bucket: str, dest_key: str, **kwargs) -> Dict[str, Any]:
        """파일 이동"""
        client = cls.get_client()
        return await client.move_file(source_bucket, source_key, dest_bucket, dest_key, **kwargs)
    
    # === 유틸리티 ===
    @classmethod
    async def generate_presigned_url(cls, bucket: str, key: str, expiration: int = 3600, **kwargs) -> Dict[str, Any]:
        """사전 서명된 URL 생성"""
        client = cls.get_client()
        return await client.generate_presigned_url(bucket, key, expiration, **kwargs)