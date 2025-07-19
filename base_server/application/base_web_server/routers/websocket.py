"""
WebSocket 라우터
"""
import json
from typing import Optional, Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from service.core.logger import Logger
from service.websocket.websocket_service import WebSocketService
from template.base.session_info import SessionInfo
from template.base.base_template import BaseTemplate


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


@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    client_id: Optional[str] = Query(None)
):
    """WebSocket 연결 엔드포인트"""
    
    # 서비스 초기화 확인
    if not WebSocketService.is_initialized():
        await websocket.close(code=1001, reason="WebSocket service not available")
        return
    
    # 세션 검증
    session_info = await get_session_from_token(token)
    user_id = session_info.account_id if session_info else None
    
    # 클라이언트 연결
    try:
        connected_client_id = await WebSocketService.connect_client(
            websocket=websocket,
            user_id=user_id,
            client_id=client_id
        )
        
        if not connected_client_id:
            await websocket.close(code=1008, reason="Connection failed")
            return
        
        Logger.info(f"WebSocket 연결 성공: {connected_client_id} (사용자: {user_id})")
        
        # 메시지 수신 루프
        try:
            while True:
                message = await websocket.receive_text()
                await WebSocketService.handle_client_message(connected_client_id, message)
        
        except WebSocketDisconnect:
            Logger.info(f"WebSocket 클라이언트 연결 해제: {connected_client_id}")
        
        except Exception as e:
            Logger.error(f"WebSocket 메시지 처리 오류: {connected_client_id} - {e}")
        
        finally:
            # 연결 정리
            await WebSocketService.disconnect_client(connected_client_id, "connection_closed")
    
    except Exception as e:
        Logger.error(f"WebSocket 연결 오류: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass


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