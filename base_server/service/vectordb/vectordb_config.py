from pydantic import BaseModel
from typing import Optional, List

class VectorDbConfig(BaseModel):
    """VectorDB 서비스 설정"""
    vectordb_type: str = "bedrock"  # bedrock, pinecone, weaviate 등
    
    # AWS Bedrock 설정
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    region_name: str = "ap-northeast-2"  # 서울 리전 사용
    aws_session_token: Optional[str] = None
    
    # 모델 설정
    embedding_model: str = "amazon.titan-embed-text-v2:0"  # Titan v2 (1024 dimensions)
    text_model: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    
    # Knowledge Base 설정
    knowledge_base_id: Optional[str] = None
    data_source_id: Optional[str] = None  # Knowledge Base의 데이터 소스 ID
    
    # S3 설정 (Knowledge Base 데이터 업로드용)
    s3_bucket: Optional[str] = None  # Knowledge Base 연결된 S3 버킷
    s3_prefix: str = "knowledge-base-data/"  # S3 키 프리픽스
    
    # 연결 설정
    timeout: int = 60
    max_retries: int = 3
    
    # 벡터 검색 설정
    default_top_k: int = 10
    similarity_threshold: float = 0.7