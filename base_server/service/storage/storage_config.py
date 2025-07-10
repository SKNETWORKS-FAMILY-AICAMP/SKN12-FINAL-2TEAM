from pydantic import BaseModel
from typing import Optional

class StorageConfig(BaseModel):
    """Storage 서비스 설정"""
    storage_type: str = "s3"  # s3, gcs, azure 등
    
    # AWS S3 설정
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "ap-northeast-2"
    aws_session_token: Optional[str] = None
    
    # 기본 버킷
    default_bucket: Optional[str] = None
    
    # 업로드 설정
    upload_timeout: int = 300  # 5분
    download_timeout: int = 300  # 5분
    multipart_threshold: int = 1024 * 1024 * 100  # 100MB
    max_concurrency: int = 10
    
    # 재시도 설정
    max_retries: int = 3