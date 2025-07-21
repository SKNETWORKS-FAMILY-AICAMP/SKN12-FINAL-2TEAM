"""
WebSocket 클라이언트 관리
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from fastapi import WebSocket, WebSocketDisconnect
from dataclasses import dataclass
from enum import Enum

from service.core.logger import Logger


class ConnectionState(Enum):
    """연결 상태"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"


@dataclass
class WebSocketMessage:
    """WebSocket 메시지"""
    type: str
    data: Any
    timestamp: datetime
    client_id: Optional[str] = None
    channel: Optional[str] = None


@dataclass
class WebSocketClient:
    """WebSocket 클라이언트 정보"""
    client_id: str
    websocket: WebSocket
    user_id: Optional[str] = None
    channels: List[str] = None
    last_ping: Optional[datetime] = None
    last_pong: Optional[datetime] = None
    state: ConnectionState = ConnectionState.CONNECTING
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.channels is None:
            self.channels = []
        if self.metadata is None:
            self.metadata = {}


class WebSocketClientManager:
    """WebSocket 클라이언트 관리자"""
    
    def __init__(self):
        # 연결된 클라이언트들
        self.active_connections: Dict[str, WebSocketClient] = {}
        
        # 채널별 클라이언트 매핑
        self.channel_subscribers: Dict[str, List[str]] = {}
        
        # 사용자별 클라이언트 매핑
        self.user_clients: Dict[str, List[str]] = {}
        
        # 메시지 핸들러
        self.message_handlers: Dict[str, Callable] = {}
        
        # 통계
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "errors": 0
        }
    
    async def connect(self, client_id: str, websocket: WebSocket, user_id: Optional[str] = None) -> bool:
        """클라이언트 연결"""
        try:
            await websocket.accept()
            
            client = WebSocketClient(
                client_id=client_id,
                websocket=websocket,
                user_id=user_id,
                state=ConnectionState.CONNECTED
            )
            
            self.active_connections[client_id] = client
            
            # 사용자별 매핑 추가
            if user_id:
                if user_id not in self.user_clients:
                    self.user_clients[user_id] = []
                self.user_clients[user_id].append(client_id)
            
            self.stats["total_connections"] += 1
            self.stats["active_connections"] += 1
            
            Logger.info(f"WebSocket 클라이언트 연결: {client_id} (사용자: {user_id})")
            
            # 연결 확인 메시지 전송
            await self.send_to_client(client_id, {
                "type": "connection_established",
                "client_id": client_id,
                "timestamp": datetime.now().isoformat()
            })
            
            return True
            
        except Exception as e:
            Logger.error(f"WebSocket 연결 실패: {client_id} - {e}")
            self.stats["errors"] += 1
            return False
    
    async def disconnect(self, client_id: str, reason: str = "client_disconnect"):
        """클라이언트 연결 해제"""
        try:
            if client_id not in self.active_connections:
                return
            
            client = self.active_connections[client_id]
            client.state = ConnectionState.DISCONNECTING
            
            # 채널에서 제거
            for channel in client.channels:
                await self.unsubscribe_from_channel(client_id, channel)
            
            # 사용자 매핑에서 제거
            if client.user_id and client.user_id in self.user_clients:
                if client_id in self.user_clients[client.user_id]:
                    self.user_clients[client.user_id].remove(client_id)
                if not self.user_clients[client.user_id]:
                    del self.user_clients[client.user_id]
            
            # 연결 제거
            del self.active_connections[client_id]
            self.stats["active_connections"] -= 1
            
            Logger.info(f"WebSocket 클라이언트 연결 해제: {client_id} (이유: {reason})")
            
        except Exception as e:
            Logger.error(f"WebSocket 연결 해제 오류: {client_id} - {e}")
            self.stats["errors"] += 1
    
    async def send_to_client(self, client_id: str, message: Dict[str, Any]) -> bool:
        """특정 클라이언트에게 메시지 전송"""
        try:
            if client_id not in self.active_connections:
                return False
            
            client = self.active_connections[client_id]
            if client.state != ConnectionState.CONNECTED:
                return False
            
            # 메시지에 타임스탬프 추가
            if "timestamp" not in message:
                message["timestamp"] = datetime.now().isoformat()
            
            await client.websocket.send_text(json.dumps(message))
            self.stats["messages_sent"] += 1
            
            return True
            
        except WebSocketDisconnect:
            await self.disconnect(client_id, "websocket_disconnect")
            return False
        except Exception as e:
            Logger.error(f"메시지 전송 실패: {client_id} - {e}")
            self.stats["errors"] += 1
            return False
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]) -> int:
        """특정 사용자의 모든 클라이언트에게 메시지 전송"""
        sent_count = 0
        
        if user_id not in self.user_clients:
            return sent_count
        
        client_ids = self.user_clients[user_id].copy()
        for client_id in client_ids:
            if await self.send_to_client(client_id, message):
                sent_count += 1
        
        return sent_count
    
    async def broadcast_to_channel(self, channel: str, message: Dict[str, Any]) -> int:
        """채널의 모든 구독자에게 메시지 브로드캐스트"""
        sent_count = 0
        
        if channel not in self.channel_subscribers:
            return sent_count
        
        client_ids = self.channel_subscribers[channel].copy()
        for client_id in client_ids:
            if await self.send_to_client(client_id, message):
                sent_count += 1
        
        return sent_count
    
    async def broadcast_to_all(self, message: Dict[str, Any]) -> int:
        """모든 연결된 클라이언트에게 메시지 브로드캐스트"""
        sent_count = 0
        
        client_ids = list(self.active_connections.keys())
        for client_id in client_ids:
            if await self.send_to_client(client_id, message):
                sent_count += 1
        
        return sent_count
    
    async def subscribe_to_channel(self, client_id: str, channel: str) -> bool:
        """클라이언트를 채널에 구독"""
        try:
            if client_id not in self.active_connections:
                return False
            
            client = self.active_connections[client_id]
            
            # 클라이언트 채널 목록에 추가
            if channel not in client.channels:
                client.channels.append(channel)
            
            # 채널 구독자 목록에 추가
            if channel not in self.channel_subscribers:
                self.channel_subscribers[channel] = []
            
            if client_id not in self.channel_subscribers[channel]:
                self.channel_subscribers[channel].append(client_id)
            
            Logger.info(f"채널 구독: {client_id} -> {channel}")
            return True
            
        except Exception as e:
            Logger.error(f"채널 구독 실패: {client_id} -> {channel} - {e}")
            return False
    
    async def unsubscribe_from_channel(self, client_id: str, channel: str) -> bool:
        """클라이언트를 채널에서 구독 해제"""
        try:
            if client_id not in self.active_connections:
                return False
            
            client = self.active_connections[client_id]
            
            # 클라이언트 채널 목록에서 제거
            if channel in client.channels:
                client.channels.remove(channel)
            
            # 채널 구독자 목록에서 제거
            if channel in self.channel_subscribers:
                if client_id in self.channel_subscribers[channel]:
                    self.channel_subscribers[channel].remove(client_id)
                
                # 구독자가 없으면 채널 제거
                if not self.channel_subscribers[channel]:
                    del self.channel_subscribers[channel]
            
            Logger.info(f"채널 구독 해제: {client_id} -> {channel}")
            return True
            
        except Exception as e:
            Logger.error(f"채널 구독 해제 실패: {client_id} -> {channel} - {e}")
            return False
    
    async def handle_message(self, client_id: str, message: str):
        """클라이언트로부터 받은 메시지 처리"""
        try:
            self.stats["messages_received"] += 1
            
            # JSON 파싱
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                await self.send_to_client(client_id, {
                    "type": "error",
                    "message": "Invalid JSON format"
                })
                return
            
            message_type = data.get("type", "unknown")
            
            # 기본 메시지 타입 처리
            if message_type == "ping":
                await self._handle_ping(client_id, data)
            elif message_type == "subscribe":
                await self._handle_subscribe(client_id, data)
            elif message_type == "unsubscribe":
                await self._handle_unsubscribe(client_id, data)
            elif message_type in self.message_handlers:
                # 커스텀 핸들러 호출
                await self.message_handlers[message_type](client_id, data)
            else:
                Logger.warn(f"처리되지 않은 메시지 타입: {message_type} from {client_id}")
                await self.send_to_client(client_id, {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })
            
        except Exception as e:
            Logger.error(f"메시지 처리 오류: {client_id} - {e}")
            self.stats["errors"] += 1
    
    async def _handle_ping(self, client_id: str, data: Dict[str, Any]):
        """Ping 메시지 처리"""
        if client_id in self.active_connections:
            self.active_connections[client_id].last_ping = datetime.now()
            
            await self.send_to_client(client_id, {
                "type": "pong",
                "timestamp": datetime.now().isoformat()
            })
    
    async def _handle_subscribe(self, client_id: str, data: Dict[str, Any]):
        """채널 구독 요청 처리"""
        channel = data.get("channel")
        if not channel:
            await self.send_to_client(client_id, {
                "type": "error",
                "message": "Channel name required for subscription"
            })
            return
        
        success = await self.subscribe_to_channel(client_id, channel)
        await self.send_to_client(client_id, {
            "type": "subscription_result",
            "channel": channel,
            "success": success
        })
    
    async def _handle_unsubscribe(self, client_id: str, data: Dict[str, Any]):
        """채널 구독 해제 요청 처리"""
        channel = data.get("channel")
        if not channel:
            await self.send_to_client(client_id, {
                "type": "error",
                "message": "Channel name required for unsubscription"
            })
            return
        
        success = await self.unsubscribe_from_channel(client_id, channel)
        await self.send_to_client(client_id, {
            "type": "unsubscription_result",
            "channel": channel,
            "success": success
        })
    
    def register_message_handler(self, message_type: str, handler: Callable):
        """메시지 핸들러 등록"""
        self.message_handlers[message_type] = handler
        Logger.info(f"메시지 핸들러 등록: {message_type}")
    
    def get_client_info(self, client_id: str) -> Optional[Dict[str, Any]]:
        """클라이언트 정보 조회"""
        if client_id not in self.active_connections:
            return None
        
        client = self.active_connections[client_id]
        return {
            "client_id": client.client_id,
            "user_id": client.user_id,
            "channels": client.channels,
            "state": client.state.value,
            "last_ping": client.last_ping.isoformat() if client.last_ping else None,
            "last_pong": client.last_pong.isoformat() if client.last_pong else None,
            "metadata": client.metadata
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 정보 반환"""
        return {
            **self.stats,
            "channels": len(self.channel_subscribers),
            "users_with_connections": len(self.user_clients)
        }
    
    def get_channel_info(self, channel: str) -> Dict[str, Any]:
        """채널 정보 조회"""
        subscriber_count = len(self.channel_subscribers.get(channel, []))
        return {
            "channel": channel,
            "subscriber_count": subscriber_count,
            "subscribers": self.channel_subscribers.get(channel, [])
        }
    
    async def cleanup_inactive_connections(self, timeout_seconds: int = 300):
        """비활성 연결 정리"""
        current_time = datetime.now()
        inactive_clients = []
        
        for client_id, client in self.active_connections.items():
            # ping 시간 확인
            if client.last_ping:
                inactive_duration = (current_time - client.last_ping).total_seconds()
                if inactive_duration > timeout_seconds:
                    inactive_clients.append(client_id)
        
        # 비활성 클라이언트 정리
        for client_id in inactive_clients:
            await self.disconnect(client_id, "inactive_timeout")
        
        if inactive_clients:
            Logger.info(f"비활성 WebSocket 연결 {len(inactive_clients)}개 정리 완료")