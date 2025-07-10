from template.base.base_template import BaseTemplate
from template.chat.common.chat_serialize import (
    ChatRoomListRequest, ChatRoomListResponse,
    ChatRoomCreateRequest, ChatRoomCreateResponse,
    ChatMessageSendRequest, ChatMessageSendResponse,
    ChatMessageListRequest, ChatMessageListResponse,
    ChatSummaryRequest, ChatSummaryResponse,
    ChatAnalysisRequest, ChatAnalysisResponse,
    ChatPersonaListRequest, ChatPersonaListResponse,
    ChatRoomDeleteRequest, ChatRoomDeleteResponse
)
from template.chat.common.chat_model import ChatRoom, ChatMessage, AIAnalysisResult, InvestmentRecommendation, AIPersona
from service.core.logger import Logger
from service.service_container import ServiceContainer
import json
import uuid
from datetime import datetime

class ChatTemplateImpl(BaseTemplate):
    def __init__(self):
        super().__init__()
    
    async def on_chat_room_list_req(self, client_session, request: ChatRoomListRequest):
        """채팅방 목록 요청 처리"""
        response = ChatRoomListResponse()
        
        Logger.info(f"Chat room list request: page={request.page}")
        
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            db_service = ServiceContainer.get_database_service()
            
            # 채팅방 목록 조회
            rooms_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_get_chat_rooms",
                (account_db_key, request.page, request.limit)
            )
            
            # 가데이터로 응답 생성
            response.rooms = [
                {
                    "room_id": f"room_{account_db_key}_1",
                    "title": "투자 전략 상담",
                    "persona_type": "ANALYST",
                    "last_message": "포트폴리오 분석을 완료했습니다.",
                    "last_message_time": str(datetime.now()),
                    "unread_count": 2
                },
                {
                    "room_id": f"room_{account_db_key}_2", 
                    "title": "시장 동향 분석",
                    "persona_type": "ADVISOR",
                    "last_message": "오늘 시장 상황을 요약해드릴게요.",
                    "last_message_time": str(datetime.now()),
                    "unread_count": 0
                }
            ]
            response.total_count = 2
            response.errorCode = 0
            
            Logger.info(f"Chat rooms retrieved: {len(response.rooms)}")
            
        except Exception as e:
            response.errorCode = 1000
            response.rooms = []
            response.total_count = 0
            Logger.error(f"Chat room list error: {e}")
        
        return response

    async def on_chat_room_create_req(self, client_session, request: ChatRoomCreateRequest):
        """새 채팅방 생성 요청 처리"""
        response = ChatRoomCreateResponse()
        
        Logger.info(f"Chat room create request: persona={request.ai_persona}")
        
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            db_service = ServiceContainer.get_database_service()
            
            # 채팅방 ID 생성
            room_id = f"room_{uuid.uuid4().hex[:16]}"
            
            # TODO: AI 페르소나 검증 로직
            # - 선택한 페르소나가 유효한지 확인
            # - 페르소나별 초기 설정 로드
            
            # 채팅방 생성 DB 저장
            await db_service.call_shard_procedure(
                shard_id,
                "fp_create_chat_room",
                (room_id, account_db_key, request.title, request.ai_persona, request.purpose)
            )
            
            # 가데이터로 응답 생성
            chat_room = ChatRoom(
                room_id=room_id,
                title=request.title,
                persona_type=request.ai_persona,
                purpose=request.purpose,
                created_at=str(datetime.now()),
                last_message_time=str(datetime.now()),
                message_count=0,
                is_active=True
            )
            
            response.room = chat_room
            response.errorCode = 0
            
            Logger.info(f"Chat room created: {room_id}")
            
        except Exception as e:
            response.errorCode = 1000
            Logger.error(f"Chat room create error: {e}")
        
        return response

    async def on_chat_message_send_req(self, client_session, request: ChatMessageSendRequest):
        """메시지 전송 요청 처리"""
        response = ChatMessageSendResponse()
        
        Logger.info(f"Chat message send request: room_id={request.room_id}")
        
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            db_service = ServiceContainer.get_database_service()
            
            # 메시지 ID 생성
            message_id = f"msg_{uuid.uuid4().hex[:16]}"
            
            # TODO: AI 메시지 처리 로직
            # - 사용자 메시지 분석
            # - 컨텍스트 파악 (이전 대화 기록)
            # - AI 페르소나별 응답 생성
            # - 투자 관련 분석 수행
            # - 추천 생성
            
            # 사용자 메시지 DB 저장
            await db_service.call_shard_procedure(
                shard_id,
                "fp_save_chat_message",
                (message_id, request.room_id, account_db_key, request.message, "USER")
            )
            
            # AI 응답 생성 및 DB 저장
            ai_message_id = f"msg_{uuid.uuid4().hex[:16]}"
            ai_response = "안녕하세요! 투자 관련 질문에 답변드리겠습니다."  # 가데이터
            
            await db_service.call_shard_procedure(
                shard_id,
                "fp_save_chat_message",
                (ai_message_id, request.room_id, account_db_key, ai_response, "AI")
            )
            
            # 가데이터로 응답 생성
            response.analysis_results = [
                {
                    "type": "SENTIMENT",
                    "result": "POSITIVE",
                    "confidence": 0.85,
                    "explanation": "긍정적인 투자 관점을 보여줍니다."
                }
            ]
            response.recommendations = [
                {
                    "type": "PORTFOLIO_REBALANCE",
                    "priority": "HIGH",
                    "symbol": "AAPL",
                    "action": "BUY",
                    "reason": "기술적 분석 결과 상승 신호"
                }
            ]
            response.errorCode = 0
            
            Logger.info(f"Chat message processed: {message_id}")
            
        except Exception as e:
            response.errorCode = 1000
            response.analysis_results = []
            response.recommendations = []
            Logger.error(f"Chat message send error: {e}")
        
        return response

    async def on_chat_message_list_req(self, client_session, request: ChatMessageListRequest):
        """채팅 메시지 목록 요청 처리"""
        response = ChatMessageListResponse()
        
        Logger.info(f"Chat message list request: room_id={request.room_id}")
        
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            db_service = ServiceContainer.get_database_service()
            
            # 메시지 목록 조회
            messages_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_get_chat_messages",
                (request.room_id, request.page, request.limit)
            )
            
            # 가데이터로 응답 생성
            response.messages = [
                {
                    "message_id": "msg_001",
                    "sender_type": "USER",
                    "message": "현재 포트폴리오 상태를 알려주세요.",
                    "timestamp": str(datetime.now()),
                    "is_analysis": False
                },
                {
                    "message_id": "msg_002",
                    "sender_type": "AI",
                    "message": "포트폴리오 분석 결과를 보여드리겠습니다.",
                    "timestamp": str(datetime.now()),
                    "is_analysis": True
                }
            ]
            response.has_more = False
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            response.messages = []
            response.has_more = False
            Logger.error(f"Chat message list error: {e}")
        
        return response

    async def on_chat_summary_req(self, client_session, request: ChatSummaryRequest):
        """채팅 요약 요청 처리"""
        response = ChatSummaryResponse()
        
        Logger.info(f"Chat summary request: room_id={request.room_id}")
        
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            # TODO: 채팅 요약 생성 로직 구현
            # - 대화 내용 분석
            # - 핵심 주제 추출
            # - 투자 인사이트 도출
            # - 액션 아이템 생성
            
            # 가데이터로 응답 생성
            response.summary = "최근 대화에서 포트폴리오 리밸런싱에 대한 논의가 있었습니다."
            response.key_points = ["포트폴리오 리밸런싱", "기술주 투자", "위험 관리"]
            response.action_items = ["AAPL 매도 검토", "채권 비중 증가"]
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            Logger.error(f"Chat summary error: {e}")
        
        return response

    async def on_chat_analysis_req(self, client_session, request: ChatAnalysisRequest):
        """종목 분석 요청 처리"""
        response = ChatAnalysisResponse()
        
        Logger.info(f"Chat analysis request: symbols={request.symbols}")
        
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            # TODO: 종목 분석 로직 구현
            # - 기술적 분석
            # - 펀더멘털 분석
            # - 시장 심리 분석
            # - 투자 추천 생성
            
            # 가데이터로 응답 생성
            response.analyses = [
                {
                    "symbol": "AAPL",
                    "analysis_type": "TECHNICAL",
                    "score": 75.5,
                    "recommendation": "BUY",
                    "key_points": ["RSI 과매도", "이동평균선 상향돌파"]
                }
            ]
            response.market_sentiment = {"overall": "BULLISH", "tech_sector": "POSITIVE"}
            response.recommendations = [
                {"symbol": "AAPL", "action": "BUY", "target_price": 180.0, "confidence": 0.85}
            ]
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            response.analyses = []
            response.market_sentiment = {}
            response.recommendations = []
            Logger.error(f"Chat analysis error: {e}")
        
        return response

    async def on_chat_persona_list_req(self, client_session, request: ChatPersonaListRequest):
        """AI 페르소나 목록 요청 처리"""
        response = ChatPersonaListResponse()
        
        Logger.info("Chat persona list request received")
        
        try:
            # TODO: AI 페르소나 목록 조회 로직 구현
            # - 사용 가능한 페르소나 목록 조회
            # - 페르소나별 특성 정보 로드
            # - 사용자 선호도 반영
            
            # 가데이터로 응답 생성
            response.personas = [
                {"persona_id": "ANALYST", "name": "투자 분석가", "description": "기술적 분석 전문", "specialty": "차트 분석"},
                {"persona_id": "ADVISOR", "name": "투자 상담사", "description": "포트폴리오 조언", "specialty": "자산 배분"},
                {"persona_id": "RESEARCHER", "name": "리서치 전문가", "description": "기업 분석", "specialty": "펀더멘털 분석"}
            ]
            response.recommended_persona = "ANALYST"
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            response.personas = []
            response.recommended_persona = ""
            Logger.error(f"Chat persona list error: {e}")
        
        return response

    async def on_chat_room_delete_req(self, client_session, request: ChatRoomDeleteRequest):
        """채팅방 삭제 요청 처리"""
        response = ChatRoomDeleteResponse()
        
        Logger.info(f"Chat room delete request: room_id={request.room_id}")
        
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            db_service = ServiceContainer.get_database_service()
            
            # TODO: 채팅방 삭제 권한 확인
            # - 사용자가 해당 채팅방의 소유자인지 확인
            # - 삭제 가능한 상태인지 확인
            
            # 채팅방 삭제 (소프트 삭제)
            await db_service.call_shard_procedure(
                shard_id,
                "fp_delete_chat_room",
                (request.room_id, account_db_key)
            )
            
            response.message = "채팅방이 삭제되었습니다"
            response.errorCode = 0
            
            Logger.info(f"Chat room deleted: {request.room_id}")
            
        except Exception as e:
            response.errorCode = 1000
            response.message = "채팅방 삭제 실패"
            Logger.error(f"Chat room delete error: {e}")
        
        return response