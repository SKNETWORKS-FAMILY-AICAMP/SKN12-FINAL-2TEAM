from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class LlmProviderConfig(BaseModel):
    provider: str  # openai, anthropic, etc.
    api_key: str
    base_url: Optional[str] = None
    model: str
    max_tokens: int = 1000
    temperature: float = 0.7
    timeout: int = 30
    
class LlmConfig(BaseModel):
    default_provider: str
    providers: Dict[str, LlmProviderConfig]
    
    # 채팅 관련 설정
    max_conversation_length: int = 20
    system_prompts: Dict[str, str] = {}
    
    # 분석 관련 설정
    analysis_timeout: int = 60
    max_concurrent_requests: int = 5