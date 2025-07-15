from pydantic import BaseModel
from typing import Optional, List

class SearchConfig(BaseModel):
    """Search 서비스 설정"""
    search_type: str = "opensearch"  # opensearch, elasticsearch 등
    
    # OpenSearch/Elasticsearch 설정
    hosts: List[str] = []
    username: Optional[str] = None
    password: Optional[str] = None
    
    # AWS OpenSearch 설정
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    region_name: str = "ap-northeast-2"
    aws_session_token: Optional[str] = None
    
    # SSL/TLS 설정
    use_ssl: bool = True
    verify_certs: bool = True
    ca_certs: Optional[str] = None
    
    # 연결 설정
    timeout: int = 30
    max_retries: int = 3
    retry_on_timeout: bool = True
    
    # 기본 인덱스 설정
    default_index: Optional[str] = None
    index_prefix: str = ""