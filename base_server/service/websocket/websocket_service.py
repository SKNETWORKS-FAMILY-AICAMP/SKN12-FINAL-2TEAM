"""
WebSocket 서비스 - 실시간 통신 관리
"""
import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from fastapi import WebSocket

from service.core.logger import Logger
from service.cache.cache_service import CacheService
from .websocket_config import WebSocketConfig
from .websocket_client import WebSocketClientManager, WebSocketClient


class WebSocketService:
    """WebSocket 서비스 - 정적 클래스로 구현"""
    
    _client_manager: Optional[WebSocketClientManager] = None
    _config: Optional[WebSocketConfig] = None
    _initialized: bool = False
    _heartbeat_task: Optional[asyncio.Task] = None
    _cleanup_task: Optional[asyncio.Task] = None
    
    @classmethod
    def init(cls, config: WebSocketConfig) -> bool:
        """WebSocket 서비스 초기화"""
        try:
            cls._config = config
            cls._client_manager = WebSocketClientManager()
            cls._initialized = True
            
            Logger.info("WebSocket 서비스 초기화 완료")
            return True
            
        except Exception as e:
            Logger.error(f"WebSocket 서비스 초기화 실패: {e}")
            return False
    
    @classmethod
    async def start_background_tasks(cls):
        """백그라운드 태스크 시작"""
        if not cls._initialized or not cls._config:
            raise RuntimeError("WebSocket service not initialized")
        
        # Heartbeat 태스크 시작
        cls._heartbeat_task = asyncio.create_task(cls._heartbeat_loop())
        
        # 정리 태스크 시작
        cls._cleanup_task = asyncio.create_task(cls._cleanup_loop())
        
        Logger.info("WebSocket 백그라운드 태스크 시작")
    
    @classmethod
    async def stop_background_tasks(cls):
        """백그라운드 태스크 중지"""
        if cls._heartbeat_task:
            cls._heartbeat_task.cancel()
            try:
                await cls._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        if cls._cleanup_task:
            cls._cleanup_task.cancel()
            try:
                await cls._cleanup_task
            except asyncio.CancelledError:
                pass
        
        Logger.info("WebSocket 백그라운드 태스크 중지")
    
    @classmethod
    async def shutdown(cls):
        """WebSocket 서비스 종료"""
        try:
            # 백그라운드 태스크 중지
            await cls.stop_background_tasks()
            
            # 모든 연결 정리
            if cls._client_manager:
                active_clients = list(cls._client_manager.active_connections.keys())
                for client_id in active_clients:
                    await cls._client_manager.disconnect(client_id, "service_shutdown")
            
            cls._initialized = False
            cls._config = None
            cls._client_manager = None
            
            Logger.info("WebSocket 서비스 종료 완료")
            
        except Exception as e:
            Logger.error(f"WebSocket 서비스 종료 오류: {e}")
    
    @classmethod
    def is_initialized(cls) -> bool:
        """초기화 상태 확인"""
        return cls._initialized
    
    @classmethod
    async def connect_client(cls, websocket: WebSocket, user_id: Optional[str] = None, 
                           client_id: Optional[str] = None) -> Optional[str]:
        """클라이언트 연결"""
        if not cls._initialized or not cls._client_manager:
            raise RuntimeError("WebSocket service not initialized")
        
        # 클라이언트 ID 생성
        if not client_id:
            client_id = f"ws_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}"
        
        # 연결 수 제한 확인
        if len(cls._client_manager.active_connections) >= cls._config.max_connections:
            Logger.warn(f"최대 연결 수 초과: {len(cls._client_manager.active_connections)}")
            return None
        
        # 인증 확인 (설정된 경우)
        if cls._config.require_auth and not user_id:
            Logger.warn(f"인증이 필요하지만 user_id가 없음: {client_id}")
            return None
        
        success = await cls._client_manager.connect(client_id, websocket, user_id)
        if success:
            return client_id
        return None
    
    @classmethod
    async def disconnect_client(cls, client_id: str, reason: str = "manual_disconnect"):
        """클라이언트 연결 해제"""
        if not cls._initialized or not cls._client_manager:
            raise RuntimeError("WebSocket service not initialized")
        
        await cls._client_manager.disconnect(client_id, reason)
    
    @classmethod
    async def handle_client_message(cls, client_id: str, message: str):
        """클라이언트 메시지 처리"""
        if not cls._initialized or not cls._client_manager:
            raise RuntimeError("WebSocket service not initialized")
        
        await cls._client_manager.handle_message(client_id, message)
    
    @classmethod
    async def send_to_client(cls, client_id: str, message: Dict[str, Any]) -> bool:
        """특정 클라이언트에게 메시지 전송"""
        if not cls._initialized or not cls._client_manager:
            raise RuntimeError("WebSocket service not initialized")
        
        return await cls._client_manager.send_to_client(client_id, message)
    
    @classmethod
    async def send_to_user(cls, user_id: str, message: Dict[str, Any]) -> int:
        """특정 사용자의 모든 클라이언트에게 메시지 전송"""
        if not cls._initialized or not cls._client_manager:
            raise RuntimeError("WebSocket service not initialized")
        
        return await cls._client_manager.send_to_user(user_id, message)
    
    @classmethod
    async def broadcast_to_channel(cls, channel: str, message: Dict[str, Any]) -> int:
        """채널의 모든 구독자에게 메시지 브로드캐스트"""
        if not cls._initialized or not cls._client_manager:
            raise RuntimeError("WebSocket service not initialized")
        
        return await cls._client_manager.broadcast_to_channel(channel, message)
    
    @classmethod
    async def broadcast_to_all(cls, message: Dict[str, Any]) -> int:
        """모든 연결된 클라이언트에게 메시지 브로드캐스트"""
        if not cls._initialized or not cls._client_manager:
            raise RuntimeError("WebSocket service not initialized")
        
        return await cls._client_manager.broadcast_to_all(message)
    
    @classmethod
    async def subscribe_to_channel(cls, client_id: str, channel: str) -> bool:
        """클라이언트를 채널에 구독"""
        if not cls._initialized or not cls._client_manager:
            raise RuntimeError("WebSocket service not initialized")
        
        return await cls._client_manager.subscribe_to_channel(client_id, channel)
    
    @classmethod
    async def unsubscribe_from_channel(cls, client_id: str, channel: str) -> bool:
        """클라이언트를 채널에서 구독 해제"""
        if not cls._initialized or not cls._client_manager:
            raise RuntimeError("WebSocket service not initialized")
        
        return await cls._client_manager.unsubscribe_from_channel(client_id, channel)
    
    @classmethod
    def register_message_handler(cls, message_type: str, handler: Callable):
        """메시지 핸들러 등록"""
        if not cls._initialized or not cls._client_manager:
            raise RuntimeError("WebSocket service not initialized")
        
        cls._client_manager.register_message_handler(message_type, handler)
    
    @classmethod
    def get_client_info(cls, client_id: str) -> Optional[Dict[str, Any]]:
        """클라이언트 정보 조회"""
        if not cls._initialized or not cls._client_manager:
            return None
        
        return cls._client_manager.get_client_info(client_id)
    
    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """통계 정보 반환"""
        if not cls._initialized or not cls._client_manager:
            return {"error": "service_not_initialized"}
        
        return cls._client_manager.get_stats()
    
    @classmethod
    def get_channel_info(cls, channel: str) -> Dict[str, Any]:
        """채널 정보 조회"""
        if not cls._initialized or not cls._client_manager:
            return {"error": "service_not_initialized"}
        
        return cls._client_manager.get_channel_info(channel)
    
    @classmethod
    def get_all_channels(cls) -> List[str]:
        """모든 채널 목록 반환"""
        if not cls._initialized or not cls._client_manager:
            return []
        
        return list(cls._client_manager.channel_subscribers.keys())
    
    @classmethod
    def get_connected_users(cls) -> List[str]:
        """연결된 사용자 목록 반환"""
        if not cls._initialized or not cls._client_manager:
            return []
        
        return list(cls._client_manager.user_clients.keys())
    
    @classmethod
    async def health_check(cls) -> Dict[str, Any]:
        """서비스 상태 확인"""
        if not cls._initialized:
            return {
                "healthy": False,
                "error": "service_not_initialized"
            }
        
        try:
            stats = cls.get_stats()
            
            return {
                "healthy": True,
                "service": "websocket",
                "active_connections": stats.get("active_connections", 0),
                "total_connections": stats.get("total_connections", 0),
                "channels": stats.get("channels", 0),
                "messages_sent": stats.get("messages_sent", 0),
                "messages_received": stats.get("messages_received", 0),
                "errors": stats.get("errors", 0),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            Logger.error(f"WebSocket health check 실패: {e}")
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    @classmethod
    async def _heartbeat_loop(cls):
        """Heartbeat 루프"""
        try:
            while cls._initialized:
                await asyncio.sleep(cls._config.heartbeat_interval)
                
                if cls._client_manager:
                    # 모든 연결된 클라이언트에게 heartbeat 전송
                    heartbeat_message = {
                        "type": "heartbeat",
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    await cls._client_manager.broadcast_to_all(heartbeat_message)
                
        except asyncio.CancelledError:
            Logger.info("WebSocket heartbeat 루프 중지")
        except Exception as e:
            Logger.error(f"WebSocket heartbeat 루프 오류: {e}")
    
    @classmethod
    async def _cleanup_loop(cls):
        """정리 루프"""
        try:
            while cls._initialized:
                await asyncio.sleep(60)  # 1분마다 정리
                
                if cls._client_manager:
                    await cls._client_manager.cleanup_inactive_connections(
                        cls._config.connection_timeout
                    )
                
        except asyncio.CancelledError:
            Logger.info("WebSocket 정리 루프 중지")
        except Exception as e:
            Logger.error(f"WebSocket 정리 루프 오류: {e}")
    
    # Redis Pub/Sub 연동 메서드들 (선택사항)
    @classmethod
    async def setup_redis_pubsub(cls):
        """Redis Pub/Sub 설정 (다중 서버 환경용)"""
        if not cls._config.use_redis_pubsub or not CacheService.is_initialized():
            return
        
        try:
            # Redis Pub/Sub 구독 설정
            redis_client = CacheService.get_redis_client()
            
            # 채널별 메시지 구독
            async def message_handler(channel, message):
                channel_name = channel.decode('utf-8').replace(f"{cls._config.redis_channel_prefix}:", "")
                await cls.broadcast_to_channel(channel_name, message)
            
            Logger.info("Redis Pub/Sub WebSocket 연동 설정 완료")
            
        except Exception as e:
            Logger.error(f"Redis Pub/Sub 설정 실패: {e}")
    
    @classmethod
    async def publish_to_redis_channel(cls, channel: str, message: Dict[str, Any]):
        """Redis 채널에 메시지 발행 (다중 서버 환경용)"""
        if not cls._config.use_redis_pubsub or not CacheService.is_initialized():
            return
        
        try:
            redis_client = CacheService.get_redis_client()
            redis_channel = f"{cls._config.redis_channel_prefix}:{channel}"
            
            import json
            await redis_client.publish(redis_channel, json.dumps(message))
            
        except Exception as e:
            Logger.error(f"Redis 채널 발행 실패: {e}")