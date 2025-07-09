from typing import Optional, List, Dict, Any
from service.net.protocol_base import BaseRequest, BaseResponse
from .chat_model import ChatRoom, ChatMessage, AIPersona, AnalysisResult, InvestmentRecommendation

# ============================================================================
# AI 채팅 기본 기능 (REQ-CHAT-001~013)
# 의거: 화면 007 (AI 채팅), REQ-CHAT-001~013
# ============================================================================

class ChatRoomListRequest(BaseRequest):
    """채팅방 목록 요청"""
    page: int = 1
    limit: int = 20

class ChatRoomListResponse(BaseResponse):
    """채팅방 목록 응답"""
    rooms: List[ChatRoom] = []
    total_count: int = 0

class ChatRoomCreateRequest(BaseRequest):
    """새 채팅방 생성"""
    ai_persona: str = "GPT4O"
    title: Optional[str] = ""

class ChatRoomCreateResponse(BaseResponse):
    """새 채팅방 생성 응답"""
    room: Optional[ChatRoom] = None
    initial_message: Optional[ChatMessage] = None

class ChatMessageSendRequest(BaseRequest):
    """메시지 전송"""
    room_id: str
    content: str
    include_portfolio: bool = True  # 포트폴리오 정보 포함 여부
    analysis_symbols: List[str] = []  # 분석할 종목 리스트

class ChatMessageSendResponse(BaseResponse):
    """메시지 전송 응답"""
    message: Optional[ChatMessage] = None
    ai_response: Optional[ChatMessage] = None
    analysis_results: List[AnalysisResult] = []
    recommendations: List[InvestmentRecommendation] = []

class ChatMessageListRequest(BaseRequest):
    """채팅 메시지 목록"""
    room_id: str
    page: int = 1
    limit: int = 50
    before_timestamp: Optional[str] = ""

class ChatMessageListResponse(BaseResponse):
    """채팅 메시지 목록 응답"""
    messages: List[ChatMessage] = []
    has_more: bool = False

class ChatSummaryRequest(BaseRequest):
    """채팅 요약 요청"""
    room_id: str
    message_count: int = 10  # 최근 N개 메시지 요약

class ChatSummaryResponse(BaseResponse):
    """채팅 요약 응답"""
    summary: str = ""
    key_points: List[str] = []
    action_items: List[str] = []

# ============================================================================
# AI 분석 기능 (REQ-CHAT-014~026)
# 의거: REQ-CHAT-014~026 (데이터 수집, AI 분석, 페르소나 적용)
# ============================================================================

class ChatAnalysisRequest(BaseRequest):
    """종목 분석 요청"""
    symbols: List[str]
    analysis_types: List[str] = ["FUNDAMENTAL", "TECHNICAL", "SENTIMENT"]
    include_news: bool = True
    time_range: str = "1M"

class ChatAnalysisResponse(BaseResponse):
    """종목 분석 응답"""
    analyses: List[AnalysisResult] = []
    market_sentiment: Dict[str, Any] = {}
    recommendations: List[InvestmentRecommendation] = []

class ChatPersonaListRequest(BaseRequest):
    """AI 페르소나 목록"""
    pass

class ChatPersonaListResponse(BaseResponse):
    """AI 페르소나 목록 응답"""
    personas: List[AIPersona] = []
    recommended_persona: str = ""

class ChatRoomDeleteRequest(BaseRequest):
    """채팅방 삭제"""
    room_id: str

class ChatRoomDeleteResponse(BaseResponse):
    """채팅방 삭제 응답"""
    message: str = ""