from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, BinaryIO
import asyncio

class IStorageClient(ABC):
    """Storage 클라이언트 인터페이스"""
    
    @abstractmethod
    async def upload_file(self, bucket: str, key: str, file_path: str, **kwargs) -> Dict[str, Any]:
        """파일 업로드"""
        pass
    
    @abstractmethod
    async def upload_file_obj(self, bucket: str, key: str, file_obj: BinaryIO, **kwargs) -> Dict[str, Any]:
        """파일 객체 업로드"""
        pass
    
    @abstractmethod
    async def download_file(self, bucket: str, key: str, file_path: str, **kwargs) -> Dict[str, Any]:
        """파일 다운로드"""
        pass
    
    @abstractmethod
    async def download_file_obj(self, bucket: str, key: str, **kwargs) -> Dict[str, Any]:
        """파일 객체로 다운로드"""
        pass
    
    @abstractmethod
    async def delete_file(self, bucket: str, key: str, **kwargs) -> Dict[str, Any]:
        """파일 삭제"""
        pass
    
    @abstractmethod
    async def list_files(self, bucket: str, prefix: str = "", **kwargs) -> Dict[str, Any]:
        """파일 목록 조회"""
        pass
    
    @abstractmethod
    async def get_file_info(self, bucket: str, key: str, **kwargs) -> Dict[str, Any]:
        """파일 정보 조회"""
        pass
    
    @abstractmethod
    async def generate_presigned_url(self, bucket: str, key: str, expiration: int = 3600, **kwargs) -> Dict[str, Any]:
        """사전 서명된 URL 생성"""
        pass
    
    @abstractmethod
    async def copy_file(self, source_bucket: str, source_key: str, dest_bucket: str, dest_key: str, **kwargs) -> Dict[str, Any]:
        """파일 복사"""
        pass
    
    @abstractmethod
    async def move_file(self, source_bucket: str, source_key: str, dest_bucket: str, dest_key: str, **kwargs) -> Dict[str, Any]:
        """파일 이동"""
        pass
    
    @abstractmethod
    async def close(self):
        """클라이언트 종료"""
        pass