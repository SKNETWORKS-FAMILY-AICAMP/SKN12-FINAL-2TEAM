from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ChatRoom(BaseModel):
    """채팅방 정보"""
    room_id: str = ""
    title: str = ""
    ai_persona: str = "GPT4O"  # GPT4O, WARREN_BUFFETT, PETER_LYNCH, GIGA_BUFFETT
    created_at: str = ""
    last_message_at: str = ""
    message_count: int = 0

class ChatMessage(BaseModel):
    """채팅 메시지"""
    message_id: str = ""
    room_id: str = ""
    sender_type: str = ""  # USER, AI
    content: str = ""
    metadata: Optional[Dict[str, Any]] = None  # 분석 데이터, 추천 등
    timestamp: str = ""
    is_streaming: bool = False

class AIPersona(BaseModel):
    """AI 페르소나 정보"""
    persona_id: str = ""
    name: str = ""
    description: str = ""
    avatar_url: str = ""
    specialty: str = ""
    greeting_message: str = ""

class AnalysisResult(BaseModel):
    """AI 분석 결과"""
    analysis_id: str = ""
    symbol: str = ""
    analysis_type: str = ""  # FUNDAMENTAL, TECHNICAL, SENTIMENT
    score: float = 0.0
    confidence: float = 0.0
    summary: str = ""
    details: Dict[str, Any] = {}
    generated_at: str = ""

class InvestmentRecommendation(BaseModel):
    """투자 추천"""
    recommendation_id: str = ""
    symbol: str = ""
    action: str = ""  # BUY, SELL, HOLD
    target_price: float = 0.0
    reasoning: str = ""
    risk_level: str = "MEDIUM"
    time_horizon: str = "MEDIUM"  # SHORT, MEDIUM, LONG