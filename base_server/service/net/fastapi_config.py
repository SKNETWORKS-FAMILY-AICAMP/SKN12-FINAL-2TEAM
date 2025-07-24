"""
FastAPI 미들웨어 설정 클래스
- 타임아웃, 크기 제한, 성능 설정 관리
- Pydantic BaseModel을 활용한 검증
"""

from typing import Optional
from pydantic import BaseModel


class FastApiConfig(BaseModel):
    """
    FastAPI 미들웨어 설정 클래스
    
    🎯 용도:
    - HTTP 요청 타임아웃 및 크기 제한
    - 느린 요청 감지 및 로깅
    - GZIP 압축 최적화
    - 성능 모니터링 설정
    """
    
    # 타임아웃 관련 설정
    request_timeout: int = 600
    slow_request_threshold: float = 3.0
    
    # 크기 제한 설정
    max_request_size: int = 52428800  # 50MB
    
    # 미들웨어 활성화 설정
    enable_request_timeout: bool = True
    enable_size_limit: bool = True
    enable_slow_request_logging: bool = True
    enable_gzip: bool = True
    
    # 압축 설정
    gzip_minimum_size: int = 500
    
    # 로깅 설정
    log_all_requests: bool = False