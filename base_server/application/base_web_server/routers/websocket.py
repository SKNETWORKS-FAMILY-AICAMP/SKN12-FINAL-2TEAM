"""
WebSocket 라우터 - 안전한 비동기 패턴 적용
"""
import json
import asyncio
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from service.core.logger import Logger
from service.websocket.websocket_service import WebSocketService
from template.base.session_info import SessionInfo
from template.base.base_template import BaseTemplate
from service.external.websocket_manager import get_websocket_manager


router = APIRouter()


# 세션 검증을 위한 의존성
async def get_session_from_token(token: Optional[str] = Query(None)) -> Optional[SessionInfo]:
    """토큰으로부터 세션 정보 추출"""
    if not token:
        return None
    
    try:
        # TemplateService를 통해 세션 검증 (만료시간 갱신 포함)
        from template.base.template_service import TemplateService
        session_info = await TemplateService.check_session_info(token)
        return session_info
    except Exception as e:
        Logger.warn(f"WebSocket 세션 검증 실패: {e}")
        return None


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """웹소켓 엔드포인트"""
    await websocket.accept()
    Logger.info("웹소켓 클라이언트 연결됨")
    
    try:
        while True:
            # 클라이언트로부터 메시지 수신
            data = await websocket.receive_text()
            message = json.loads(data)
            
            Logger.info(f"웹소켓 메시지 수신: {message}")
            
            # 메시지 타입에 따른 처리
            if message.get('type') == 'subscribe':
                # 구독 요청 처리
                symbols = message.get('symbols', [])
                indices = message.get('indices', [])
                
                Logger.info(f"구독 요청: symbols={symbols}, indices={indices}")
                
                # 한국투자증권 API를 통한 실시간 데이터 조회
                websocket_manager = get_websocket_manager()
                
                # 사용자 API 키 조회
                from service.service_container import ServiceContainer
                db_service = ServiceContainer.get_database_service()
                
                # 여기서는 임시로 account_db_key를 1000으로 설정 (실제로는 세션에서 가져와야 함)
                account_db_key = 1000
                
                api_keys_result = await db_service.execute_global_query(
                    "SELECT korea_investment_app_key, korea_investment_app_secret FROM table_user_api_keys WHERE account_db_key = %s",
                    (account_db_key,)
                )
                
                if api_keys_result and api_keys_result[0].get('korea_investment_app_key'):
                    Logger.info("한국투자증권 API 키 발견, REST API로 데이터 조회")
                    
                    app_key = api_keys_result[0]['korea_investment_app_key']
                    app_secret = api_keys_result[0]['korea_investment_app_secret']
                    
                    # REST API를 통한 데이터 조회 (웹소켓 대신)
                    try:
                        from service.external.korea_investment_service import get_korea_investment_service
                        korea_service = await get_korea_investment_service()
                        
                        if await korea_service.authenticate(app_key, app_secret):
                            Logger.info("한국투자증권 REST API 인증 성공")
                            
                            # 지수 데이터 조회
                            market_data = {}
                            for index_code in indices:
                                index_data = await korea_service.get_market_index(index_code)
                                if index_data:
                                    index_name = "kospi" if index_code == "0001" else "kosdaq"
                                    market_data[index_name] = {
                                        'current_price': float(index_data.get('stck_prpr', 0)),
                                        'change_amount': float(index_data.get('prdy_vrss', 0)),
                                        'change_rate': float(index_data.get('prdy_ctrt', 0)),
                                        'volume': int(index_data.get('acml_vol', 0))
                                    }
                                # Rate limit 방지를 위한 지연
                                await asyncio.sleep(0.5)
                            
                            # 주식 데이터 조회
                            portfolio_data = []
                            for symbol in symbols:
                                stock_data = await korea_service.get_stock_price(symbol)
                                if stock_data:
                                    portfolio_data.append({
                                        'symbol': symbol,
                                        'name': symbol,  # 실제로는 종목명 조회 필요
                                        'current_price': float(stock_data.get('stck_prpr', 0)),
                                        'change_amount': float(stock_data.get('prdy_vrss', 0)),
                                        'change_rate': float(stock_data.get('prdy_ctrt', 0)),
                                        'volume': int(stock_data.get('acml_vol', 0))
                                    })
                                # Rate limit 방지를 위한 지연
                                await asyncio.sleep(0.5)
                            
                            # 데이터 전송
                            await websocket.send_text(json.dumps({
                                'type': 'market_data',
                                'market_data': market_data
                            }))
                            await websocket.send_text(json.dumps({
                                'type': 'portfolio_data',
                                'portfolio_data': portfolio_data
                            }))
                            await websocket.send_text(json.dumps({
                                'type': 'connection_status',
                                'status': 'connected',
                                'message': '한국투자증권 REST API 연결 성공'
                            }))
                            
                        else:
                            Logger.error("한국투자증권 REST API 인증 실패")
                            # 인증 실패 시 N/A 데이터 전송
                            await websocket.send_text(json.dumps({
                                'type': 'market_data',
                                'market_data': {}
                            }))
                            await websocket.send_text(json.dumps({
                                'type': 'portfolio_data',
                                'portfolio_data': []
                            }))
                            await websocket.send_text(json.dumps({
                                'type': 'connection_status',
                                'status': 'auth_failed',
                                'message': '한국투자증권 API 인증 실패'
                            }))
                            
                    except Exception as e:
                        Logger.error(f"한국투자증권 REST API 호출 에러: {e}")
                        # 에러 시 N/A 데이터 전송
                        await websocket.send_text(json.dumps({
                            'type': 'market_data',
                            'market_data': {}
                        }))
                        await websocket.send_text(json.dumps({
                            'type': 'portfolio_data',
                            'portfolio_data': []
                        }))
                        await websocket.send_text(json.dumps({
                            'type': 'connection_status',
                            'status': 'error',
                            'message': f'한국투자증권 API 에러: {str(e)}'
                        }))
                else:
                    Logger.info("한국투자증권 API 키 없음, N/A 데이터 전송")
                    # API 키가 없으면 N/A 데이터 전송
                    await websocket.send_text(json.dumps({
                        'type': 'market_data',
                        'market_data': {}
                    }))
                    await websocket.send_text(json.dumps({
                        'type': 'portfolio_data',
                        'portfolio_data': []
                    }))
                    await websocket.send_text(json.dumps({
                        'type': 'connection_status',
                        'status': 'no_api_key',
                        'message': '한국투자증권 API 키가 설정되지 않음'
                    }))
                
            elif message.get('type') == 'ping':
                # 핑 응답
                await websocket.send_text(json.dumps({
                    'type': 'pong',
                    'timestamp': message.get('timestamp')
                }))
                
    except WebSocketDisconnect:
        Logger.info("웹소켓 클라이언트 연결 해제")
    except Exception as e:
        Logger.error(f"웹소켓 에러: {e}")
        await websocket.close()


@router.get("/status")
async def get_websocket_status():
    """WebSocket 서비스 상태 조회"""
    try:
        if not WebSocketService.is_initialized():
            return JSONResponse(
                status_code=503,
                content={"error": "WebSocket service not initialized"}
            )
        
        health_check = await WebSocketService.health_check()
        stats = WebSocketService.get_stats()
        
        return {
            "status": "active" if health_check.get("healthy") else "inactive",
            "health_check": health_check,
            "stats": stats,
            "channels": WebSocketService.get_all_channels(),
            "connected_users": WebSocketService.get_connected_users()
        }
    
    except Exception as e:
        Logger.error(f"WebSocket 상태 조회 실패: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@router.get("/channels")
async def get_channels():
    """활성 채널 목록 조회"""
    try:
        if not WebSocketService.is_initialized():
            raise HTTPException(status_code=503, detail="WebSocket service not initialized")
        
        channels = WebSocketService.get_all_channels()
        channel_info = {}
        
        for channel in channels:
            channel_info[channel] = WebSocketService.get_channel_info(channel)
        
        return {
            "channels": channels,
            "channel_info": channel_info,
            "total_channels": len(channels)
        }
    
    except Exception as e:
        Logger.error(f"채널 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/channels/{channel_name}")
async def get_channel_info(channel_name: str):
    """특정 채널 정보 조회"""
    try:
        if not WebSocketService.is_initialized():
            raise HTTPException(status_code=503, detail="WebSocket service not initialized")
        
        channel_info = WebSocketService.get_channel_info(channel_name)
        
        return channel_info
    
    except Exception as e:
        Logger.error(f"채널 정보 조회 실패: {channel_name} - {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/broadcast")
async def broadcast_message(request: Dict[str, Any]):
    """메시지 브로드캐스트"""
    try:
        if not WebSocketService.is_initialized():
            raise HTTPException(status_code=503, detail="WebSocket service not initialized")
        
        message = request.get("message")
        target_type = request.get("target_type", "all")  # all, user, channel
        target = request.get("target")
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        sent_count = 0
        
        if target_type == "all":
            sent_count = await WebSocketService.broadcast_to_all(message)
        elif target_type == "user":
            if not target:
                raise HTTPException(status_code=400, detail="User ID is required for user broadcast")
            sent_count = await WebSocketService.send_to_user(target, message)
        elif target_type == "channel":
            if not target:
                raise HTTPException(status_code=400, detail="Channel name is required for channel broadcast")
            sent_count = await WebSocketService.broadcast_to_channel(target, message)
        else:
            raise HTTPException(status_code=400, detail="Invalid target_type")
        
        return {
            "success": True,
            "sent_count": sent_count,
            "target_type": target_type,
            "target": target
        }
    
    except HTTPException:
        raise
    except Exception as e:
        Logger.error(f"메시지 브로드캐스트 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/clients")
async def get_connected_clients():
    """연결된 클라이언트 목록 조회"""
    try:
        if not WebSocketService.is_initialized():
            raise HTTPException(status_code=503, detail="WebSocket service not initialized")
        
        connected_users = WebSocketService.get_connected_users()
        stats = WebSocketService.get_stats()
        
        return {
            "connected_users": connected_users,
            "total_users": len(connected_users),
            "active_connections": stats.get("active_connections", 0),
            "total_connections": stats.get("total_connections", 0)
        }
    
    except Exception as e:
        Logger.error(f"클라이언트 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/clients/{client_id}")
async def get_client_info(client_id: str):
    """특정 클라이언트 정보 조회"""
    try:
        if not WebSocketService.is_initialized():
            raise HTTPException(status_code=503, detail="WebSocket service not initialized")
        
        client_info = WebSocketService.get_client_info(client_id)
        
        if not client_info:
            raise HTTPException(status_code=404, detail="Client not found")
        
        return client_info
    
    except HTTPException:
        raise
    except Exception as e:
        Logger.error(f"클라이언트 정보 조회 실패: {client_id} - {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket 메시지 핸들러 등록 함수들
def setup_websocket_message_handlers():
    """WebSocket 메시지 핸들러 설정"""
    
    async def handle_chat_message(client_id: str, data: Dict[str, Any]):
        """채팅 메시지 처리"""
        try:
            channel = data.get("channel", "general")
            message_content = data.get("content", "")
            
            if not message_content:
                await WebSocketService.send_to_client(client_id, {
                    "type": "error",
                    "message": "Message content is required"
                })
                return
            
            # 클라이언트 정보 조회
            client_info = WebSocketService.get_client_info(client_id)
            if not client_info:
                return
            
            # 채팅 메시지 브로드캐스트
            chat_message = {
                "type": "chat_message",
                "channel": channel,
                "content": message_content,
                "account_id": client_info.get("user_id"),  # WebSocketService에서 user_id로 저장됨
                "client_id": client_id,
                "timestamp": data.get("timestamp")
            }
            
            await WebSocketService.broadcast_to_channel(channel, chat_message)
            
        except Exception as e:
            Logger.error(f"채팅 메시지 처리 실패: {client_id} - {e}")
    
    async def handle_typing_indicator(client_id: str, data: Dict[str, Any]):
        """타이핑 인디케이터 처리"""
        try:
            channel = data.get("channel", "general")
            is_typing = data.get("is_typing", False)
            
            # 클라이언트 정보 조회
            client_info = WebSocketService.get_client_info(client_id)
            if not client_info:
                return
            
            # 타이핑 상태 브로드캐스트
            typing_message = {
                "type": "typing_indicator",
                "channel": channel,
                "account_id": client_info.get("user_id"),  # WebSocketService에서 user_id로 저장됨
                "client_id": client_id,
                "is_typing": is_typing,
                "timestamp": data.get("timestamp")
            }
            
            await WebSocketService.broadcast_to_channel(channel, typing_message)
            
        except Exception as e:
            Logger.error(f"타이핑 인디케이터 처리 실패: {client_id} - {e}")
    
    async def handle_notification_ack(client_id: str, data: Dict[str, Any]):
        """알림 확인 처리"""
        try:
            notification_id = data.get("notification_id")
            
            if not notification_id:
                await WebSocketService.send_to_client(client_id, {
                    "type": "error",
                    "message": "Notification ID is required"
                })
                return
            
            # 알림 확인 응답
            await WebSocketService.send_to_client(client_id, {
                "type": "notification_ack_response",
                "notification_id": notification_id,
                "acknowledged": True,
                "timestamp": data.get("timestamp")
            })
            
        except Exception as e:
            Logger.error(f"알림 확인 처리 실패: {client_id} - {e}")
    
    # 메시지 핸들러 등록
    WebSocketService.register_message_handler("chat_message", handle_chat_message)
    WebSocketService.register_message_handler("typing_indicator", handle_typing_indicator)
    WebSocketService.register_message_handler("notification_ack", handle_notification_ack)
    
    Logger.info("WebSocket 메시지 핸들러 등록 완료")


# Protocol 콜백 설정 함수
def setup_websocket_protocol_callbacks():
    """WebSocket Protocol 콜백 설정"""
    try:
        # 메시지 핸들러 설정
        setup_websocket_message_handlers()
        
        Logger.info("WebSocket Protocol 콜백 설정 완료")
        
    except Exception as e:
        Logger.error(f"WebSocket Protocol 콜백 설정 실패: {e}")
        raise