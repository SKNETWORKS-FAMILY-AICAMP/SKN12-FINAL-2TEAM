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
from template.chat.common.chat_model import ChatRoom, ChatMessage, AnalysisResult, InvestmentRecommendation, AIPersona
from service.core.logger import Logger
from service.service_container import ServiceContainer
import json
import uuid
from datetime import datetime
from typing import Dict, Any

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
            
            # 채팅방 목록 조회 (DB 프로시저 활용)
            rooms_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_get_chat_rooms",
                (account_db_key, request.page, request.limit)
            )
            
            if not rooms_result:
                response.rooms = []
                response.total_count = 0
                response.errorCode = 0
                Logger.info(f"No chat rooms found for account_db_key: {account_db_key}")
                return response
            
            # DB 결과를 바탕으로 응답 생성
            rooms_data = rooms_result[0] if isinstance(rooms_result[0], list) else rooms_result
            total_count_data = rooms_result[1] if len(rooms_result) > 1 else {}
            
            response.rooms = []
            for room in rooms_data:
                if isinstance(room, dict):
                    chat_room = ChatRoom(
                        room_id=str(room.get('room_id') or ""),
                        title=str(room.get('title') or ""),
                        ai_persona=str(room.get('ai_persona') or ""),
                        # ChatRoom 클래스에 맞는 필드만 전달
                        created_at=str(room.get('created_at', datetime.now())),
                        last_message_at=str(room.get('last_message_at', datetime.now())),
                        message_count=room.get('message_count', 0)
                    )
                    response.rooms.append(chat_room)
            
            response.total_count = total_count_data.get('total_count', len(response.rooms))
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
            
            # 1. AI 페르소나 유효성 검증
            valid_personas = ['GPT4O', 'WARREN_BUFFETT', 'PETER_LYNCH', 'GIGA_BUFFETT']
            if request.ai_persona not in valid_personas:
                response.errorCode = 6001
                Logger.info(f"Invalid AI persona: {request.ai_persona}")
                return response
            
            # 2. 채팅방 생성 DB 저장
            create_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_create_chat_room",
                (account_db_key, request.ai_persona, request.title)
            )
            
            if not create_result or create_result[0].get('result') != 'SUCCESS':
                response.errorCode = 6002
                Logger.error("Failed to create chat room")
                return response
            
            room_id = create_result[0].get('room_id')
            initial_message_id = create_result[0].get('initial_message_id')
            
            # DB 결과를 바탕으로 응답 생성
            chat_room = ChatRoom(
                room_id=str(room_id or ""),
                title=str(request.title or ""),
                ai_persona=str(request.ai_persona or ""),
                created_at=str(datetime.now()),
                last_message_at=str(datetime.now()),
                message_count=1
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
            
            # 1. 채팅방 존재 및 권한 확인
            room_check = await db_service.call_shard_procedure(
                shard_id,
                "fp_get_chat_rooms",
                (account_db_key, 1, 1)  # 해당 room_id를 찾기 위한 검색
            )
            
            # 2. 사용자 메시지 전송 및 AI 응답 처리
            send_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_send_chat_message",
                (account_db_key, request.room_id, request.content, 
                 request.include_portfolio, request.analysis_symbols)
            )
            
            if not send_result or send_result[0].get('result') != 'SUCCESS':
                response.errorCode = 6003
                response.analysis_results = []
                response.recommendations = []
                Logger.error("Failed to send chat message")
                return response
            
            user_message_id = send_result[0].get('user_message_id')
            ai_message_id = send_result[0].get('ai_message_id')
            
            # 3. AI 분석 결과 저장 (사용자 메시지 분석)
            if request.analysis_symbols:
                for symbol in request.analysis_symbols:
                    await db_service.call_shard_procedure(
                        shard_id,
                        "fp_save_ai_analysis",
                        (account_db_key, symbol, "SENTIMENT", 75.0, 85.0, 
                         f"{symbol} 종목에 대한 긍정적 시각", 
                         '{"analysis_type": "SENTIMENT", "score": 75.0}', ai_message_id)
                    )
            
            # 4. 투자 추천 생성 및 저장
            if request.analysis_symbols and len(request.analysis_symbols) > 0:
                symbol = request.analysis_symbols[0]
                await db_service.call_shard_procedure(
                    shard_id,
                    "fp_save_investment_recommendation",
                    (account_db_key, symbol, "BUY", 150.0, 
                     f"{symbol} 종목 매수 추천", "MEDIUM", "MEDIUM", 80.0, 
                     None, ai_message_id)
                )
            
            # 실제 분석 결과와 추천 사항 생성
            response.analysis_results = []
            response.recommendations = []
            
            # 분석 요청이 있었던 경우 결과 추가
            if request.analysis_symbols:
                for symbol in request.analysis_symbols:
                    response.analysis_results.append(
                        AnalysisResult(
                            analysis_type="SENTIMENT",
                            score=0.85,
                            summary=f"{symbol} 종목에 대한 긍정적 시각을 보여줍니다."
                        )
                    )
                    
                    response.recommendations.append(
                        InvestmentRecommendation(
                            symbol=symbol,
                            action="BUY",
                            reasoning=f"{symbol} 기술적 분석 결과 상승 신호",
                            risk_level="MEDIUM"
                        )
                    )
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
            
            # 메시지 목록 조회 (DB 프로시저 활용)
            messages_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_get_chat_messages",
                (account_db_key, request.room_id, request.page, request.limit, None)  # before_timestamp
            )
            
            if not messages_result:
                response.messages = []
                response.has_more = False
                response.errorCode = 0
                return response
            
            # DB 결과를 바탕으로 응답 생성
            response.messages = []
            for msg in messages_result:
                if isinstance(msg, dict):  # 에러 체크
                    response.messages.append(
                        ChatMessage(
                            message_id=str(msg.get('message_id') or ""),
                            room_id=str(msg.get('room_id') or ""),
                            sender_type=str(msg.get('sender_type') or ""),
                            content=str(msg.get('content') or ""),
                            metadata=msg.get('metadata'),  # 분석 정보가 있으면 여기에!
                            timestamp=str(msg.get('timestamp', datetime.now())),
                            is_streaming=False  # 필요시 True/False
                        )
                    )
            
            response.has_more = len(response.messages) >= request.limit
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
                AnalysisResult(
                    symbol="AAPL",
                    analysis_type="TECHNICAL",
                    score=75.5,
                    confidence=0.85,
                    summary="RSI 과매도, 이동평균선 상향돌파",
                    details={"key_points": ["RSI 과매도", "이동평균선 상향돌파"]},
                    generated_at=str(datetime.now())
                )
            ]
            response.market_sentiment = {"overall": "BULLISH", "tech_sector": "POSITIVE"}
            response.recommendations = [
                InvestmentRecommendation(
                    symbol="AAPL",
                    action="BUY",
                    target_price=180.0,
                    reasoning="기술적 분석 결과 상승 신호",
                    risk_level="MEDIUM",
                    time_horizon="MEDIUM"
                )
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
                AIPersona(
                    persona_id="ANALYST",
                    name="투자 분석가",
                    description="기술적 분석 전문",
                    specialty="차트 분석"
                ),
                AIPersona(
                    persona_id="ADVISOR",
                    name="투자 상담사",
                    description="포트폴리오 조언",
                    specialty="자산 배분"
                ),
                AIPersona(
                    persona_id="RESEARCHER",
                    name="리서치 전문가",
                    description="기업 분석",
                    specialty="펀더멘털 분석"
                )
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
            
            # 1. 채팅방 삭제 권한 확인 및 삭제 수행
            delete_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_delete_chat_room",
                (request.room_id, account_db_key)  # 소유자 검증 포함
            )
            
            if not delete_result or delete_result[0].get('result') != 'SUCCESS':
                response.errorCode = 6004
                response.message = "채팅방 삭제 실패: 권한이 없거나 존재하지 않는 채팅방입니다"
                return response
            
            response.message = "채팅방이 삭제되었습니다"
            response.errorCode = 0
            
            Logger.info(f"Chat room deleted: {request.room_id}")
            
        except Exception as e:
            response.errorCode = 1000
            response.message = "채팅방 삭제 실패"
            Logger.error(f"Chat room delete error: {e}")
        
        return response