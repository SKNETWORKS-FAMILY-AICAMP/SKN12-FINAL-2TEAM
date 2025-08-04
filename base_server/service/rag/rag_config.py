from pydantic import BaseModel
from typing import Optional

class RagConfig(BaseModel):
    """RAG 서비스 설정"""
    
    # 벡터 데이터베이스 설정
    vector_db_path: str = "./vector_db"
    collection_name: str = "financial_news_collection"
    
    # 임베딩 모델 설정
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # 검색 설정
    default_k: int = 5
    default_threshold: float = 0.7
    max_content_length: int = 200
    
    # 성능 설정
    enable_vector_db: bool = True
    enable_fallback_search: bool = True
    
    # 디버그 설정
    debug_mode: bool = False
    log_search_results: bool = False
