from typing import List, Optional
from pydantic import BaseModel

class FastApiConfig(BaseModel):
    """
    FastAPI 미들웨어 설정 클래스
    
    HTTP 요청 타임아웃, 크기 제한, 성능 최적화 설정을 관리합니다.
    """
    # 타임아웃 관련 설정
    request_timeout: int = 600                    # HTTP 요청 전체 처리 시간(초) - LLM API 호출 고려
    slow_request_threshold: float = 3.0           # 느린 요청 로깅 기준(초) - 성능 병목 감지
    
    # 크기 제한 설정
    max_request_size: int = 52428800              # 요청 본문 최대 크기(bytes) - 50MB
    
    # 미들웨어 활성화 설정
    enable_request_timeout: bool = True           # 요청 타임아웃 미들웨어 활성화
    enable_size_limit: bool = True                # 요청 크기 제한 미들웨어 활성화
    enable_slow_request_logging: bool = True      # 느린 요청 로깅 활성화
    enable_gzip: bool = True                      # GZIP 압축 활성화
    
    # 압축 설정
    gzip_minimum_size: int = 500                  # GZIP 압축 최소 크기(bytes)
    
    # 로깅 설정
    log_all_requests: bool = False                # 모든 요청 로깅 - 운영환경에서는 false

class NetConfig(BaseModel):
    """
    네트워크 설정 클래스
    
    기본 서버 설정과 FastAPI 미들웨어 설정을 관리합니다.
    """
    # 기본 서버 설정
    host: str = "0.0.0.0"
    port: int = 8000
    
    # FastAPI 미들웨어 설정
    fastApiConfig: Optional[FastApiConfig] = None