from typing import Dict, Optional, Any
from pydantic import BaseModel, Field

class LlmProviderConfig(BaseModel):
    provider: str            # openai, anthropic, etc.
    api_key: str
    base_url: Optional[str] = None
    model: str
    max_tokens: int = 1000
    temperature: float = 0.7
    timeout: int = 30

class ApiKeys(BaseModel):
    FMP_API_KEY: str
    NEWSAPI_KEY: str
    OPENAI_API_KEY: str
    FRED_API_KEY: str

class LlmConfig(BaseModel):
    default_provider: str
    providers: Dict[str, LlmProviderConfig]
    api_keys: ApiKeys = Field(..., alias="API_Key")    # JSON의 "API_Key" 섹션을 이 필드에 매핑

    # 채팅 관련 설정
    max_conversation_length: int = 20
    system_prompts: Dict[str, str] = {}

    # 분석 관련 설정
    analysis_timeout: int = 60
    max_concurrent_requests: int = 5

    class Config:
        allow_population_by_field_name = True  # alias("API_Key")로 파싱 허용
