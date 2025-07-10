from pydantic import BaseModel
from typing import Dict, Optional

class ApiEndpointConfig(BaseModel):
    """API 엔드포인트 설정"""
    base_url: str
    api_key: Optional[str] = None
    headers: Dict[str, str] = {}
    timeout: int = 30
    retry_count: int = 3
    retry_delay: float = 1.0

class ProxyConfig(BaseModel):
    """프록시 설정"""
    url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None

class ExternalConfig(BaseModel):
    """External API 서비스 설정"""
    # 기본 설정
    timeout: int = 30
    max_retries: int = 3
    
    # 프록시 설정
    proxy: Optional[ProxyConfig] = None
    
    # API 엔드포인트 설정
    apis: Dict[str, ApiEndpointConfig] = {
        "stock_market": ApiEndpointConfig(
            base_url="https://api.stock-market.com/v1",
            timeout=10,
            retry_count=2
        ),
        "news": ApiEndpointConfig(
            base_url="https://api.news-service.com/v1",
            timeout=15,
            retry_count=3
        ),
        "exchange_rate": ApiEndpointConfig(
            base_url="https://api.exchange-rates.com/v1",
            timeout=10,
            retry_count=2
        )
    }