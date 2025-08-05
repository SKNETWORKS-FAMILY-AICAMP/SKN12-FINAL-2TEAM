"""
간소화된 알림 서비스 - 시그널 알림에 필요한 기능만 포함
- WebSocket 실시간 알림
- 인앱 알림함 저장
- 중복 방지 및 Rate Limiting

서비스 패턴:
- 정적 클래스 (static class) 패턴 사용
- init() → 서비스 초기화
- shutdown() → 서비스 종료
- is_initialized() → 초기화 상태 확인
"""
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass

from service.core.logger import Logger
from service.websocket.websocket_service import WebSocketService
from service.queue.queue_service import QueueService
from service.queue.event_queue import EventType
from service.cache.cache_service import CacheService
from service.service_container import ServiceContainer
from service.email.email_service import EmailService
from service.sms.sms_service import SmsService

from .notification_config import NotificationConfig, NotificationChannel, NotificationType


@dataclass
class Notification:
    """
    시그널 알림 객체 (간소화)
    
    Attributes:
        id: 알림 고유 ID
        user_id: 수신자 ID (account_db_key를 문자열로)
        shard_id: 사용자 샤드 ID (DB 저장용)
        type: 알림 타입 (PREDICTION_ALERT 등)
        title: 알림 제목
        message: 알림 내용
        data: 추가 데이터 (종목 정보, 가격 등)
        priority: 우선순위 (1=긴급, 3=보통)
        created_at: 생성 시간
    """
    id: str
    user_id: str
    shard_id: int
    type: NotificationType
    title: str
    message: str
    data: Dict[str, Any]
    priority: int = 3
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환 (직렬화용)"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type.value,
            "title": self.title,
            "message": self.message,
            "data": self.data,
            "priority": self.priority,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class NotificationService:
    """
    간소화된 알림 서비스 (정적 클래스)
    
    시그널 알림에 필요한 기능만 포함:
    1. WebSocket 실시간 알림
    2. 인앱 알림함 저장
    3. 중복 알림 방지
    4. Rate limiting
    """
    
    _config: Optional[NotificationConfig] = None
    _initialized: bool = False
    _channel_handlers: Dict[NotificationChannel, Any] = {}
    
    @classmethod
    async def init(cls, config: NotificationConfig) -> bool:
        """
        서비스 초기화 (간소화)
        
        Args:
            config: NotificationConfig 객체
            
        Returns:
            bool: 초기화 성공 여부
        """
        try:
            cls._config = config
            
            # 인앱, 이메일, SMS 채널 등록
            cls._channel_handlers = {
                NotificationChannel.WEBSOCKET: cls._send_websocket,
                NotificationChannel.IN_APP: cls._send_in_app,
                NotificationChannel.EMAIL: cls._send_email,
                NotificationChannel.SMS: cls._send_sms
            }
            
            # 큐 서비스가 활성화되어 있으면 알림 발송 컨슈머 등록
            if QueueService._initialized:
                queue_service = QueueService.get_instance()
                await queue_service.register_message_consumer(
                    "notification_queue",
                    "notification_sender",
                    cls._process_notification_queue
                )
                Logger.info("Notification queue consumer registered")
            
            cls._initialized = True
            Logger.info("NotificationService initialized (simplified)")
            return True
            
        except Exception as e:
            Logger.error(f"NotificationService initialization failed: {e}")
            return False
    
    @classmethod
    async def shutdown(cls):
        """서비스 종료"""
        if cls._initialized:
            cls._initialized = False
            Logger.info("NotificationService shutdown")
    
    @classmethod
    def is_initialized(cls) -> bool:
        """초기화 여부 확인"""
        return cls._initialized
    
    @classmethod
    async def send_notification(cls, 
                               user_id: str,
                               shard_id: int,
                               notification_type: NotificationType,
                               title: str,
                               message: str,
                               data: Dict[str, Any],
                               priority: int = 3) -> bool:
        """
        시그널 알림 발송 (간소화)
        
        Args:
            user_id: 수신자 ID (account_db_key를 문자열로)
            shard_id: 사용자 샤드 ID
            notification_type: 알림 타입 (PREDICTION_ALERT 등)
            title: 알림 제목
            message: 알림 내용
            data: 추가 데이터 (종목명, 가격, 신호 등)
            priority: 우선순위 (1=긴급, 3=보통)
            
        Returns:
            bool: 발송 성공 여부
        """
        if not cls._initialized:
            Logger.error("NotificationService not initialized")
            return False
        
        try:
            # 알림 객체 생성
            import uuid
            notification = Notification(
                id=str(uuid.uuid4()),
                user_id=user_id,
                shard_id=shard_id,
                type=notification_type,
                title=title,
                message=message,
                data=data,
                priority=priority,
                created_at=datetime.utcnow()
            )
            
            # 1. 중복 체크
            if await cls._is_duplicate(notification):
                Logger.info(f"Duplicate notification skipped: {notification.id}")
                return True
            
            # 2. Rate limit 체크
            if not await cls._check_rate_limit(user_id):
                Logger.warn(f"Rate limit exceeded for user {user_id}")
                return False
            
            # 3. 알림 발송 (config에서 활성화된 채널만)
            target_channels = []
            for channel in NotificationChannel:
                if cls._config.enabled_channels.get(channel.value, False):
                    target_channels.append(channel)
            await cls._queue_notification(notification, target_channels)
            
            # 4. 이벤트 발행
            if QueueService._initialized:
                await QueueService.get_instance().publish_event(
                    EventType.NOTIFICATION_CREATED,
                    "notification_service",
                    notification.to_dict()
                )
            
            return True
            
        except Exception as e:
            Logger.error(f"Send notification failed: {e}")
            return False
    
    @classmethod
    async def _is_duplicate(cls, notification: Notification) -> bool:
        """
        중복 알림 체크
        
        Args:
            notification: 체크할 알림 객체
            
        Returns:
            bool: 중복이면 True
        """
        try:
            # CacheService 초기화 상태 확인 (ServiceContainer 통해서 확인도 가능)
            if not CacheService.is_initialized():
                return False
            
            # 중복 체크 키: user_id:type:data_hash
            import hashlib
            data_str = json.dumps(notification.data, sort_keys=True)
            data_hash = hashlib.md5(data_str.encode()).hexdigest()[:8]
            
            dedup_key = f"notif:dedup:{notification.user_id}:{notification.type.value}:{data_hash}"
            
            async with CacheService.get_client() as client:
                exists = await client.exists(dedup_key)
                if exists:
                    return True
                
                # 키가 없으면 설정 (기본 24시간 TTL)
                ttl = cls._config.dedup_window_hours * 3600
                await client.setex(dedup_key, ttl, "1")
                
            return False
            
        except Exception as e:
            Logger.error(f"Duplicate check failed: {e}")
            return False
    
    @classmethod
    async def _check_rate_limit(cls, user_id: str) -> bool:
        """
        Rate limit 체크
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            bool: 제한 내면 True, 초과면 False
        """
        try:
            # CacheService 초기화 상태 확인
            if not CacheService.is_initialized():
                return True  # 캐시 없으면 제한 없음
            
            rate_key = f"notif:rate:{user_id}:{datetime.utcnow().strftime('%Y%m%d%H')}"
            
            async with CacheService.get_client() as client:
                current = await client.incr(rate_key)
                
                if current == 1:
                    await client.expire(rate_key, 3600)
                
                return current <= cls._config.rate_limit_per_user_per_hour
                
        except Exception as e:
            Logger.error(f"Rate limit check failed: {e}")
            return True
    
    @classmethod
    async def _queue_notification(cls, notification: Notification, channels: List[NotificationChannel]):
        """
        알림을 큐에 추가 (간소화)
        
        Args:
            notification: 알림 객체
            channels: 발송할 채널 목록
        """
        if not QueueService._initialized:
            await cls._send_notification_direct(notification, channels)
            return
        
        queue_service = QueueService.get_instance()
        
        for channel in channels:
            message = {
                "notification": notification.to_dict(),
                "channel": channel.value,
                "account_db_key": int(notification.user_id),
                "shard_id": notification.shard_id
            }
            
            from service.queue.message_queue import MessagePriority
            priority = MessagePriority.HIGH if notification.priority <= 2 else MessagePriority.NORMAL
            
            await queue_service.send_message(
                "notification_queue",
                message,
                f"notification_{channel.value}",
                priority
            )
    
    @classmethod
    async def _process_notification_queue(cls, message) -> bool:
        """
        큐에서 알림 처리 (컨슈머)
        
        Args:
            message: QueueMessage 객체
            
        Returns:
            bool: 처리 성공 여부
        """
        try:
            data = message.payload
            notification_data = data["notification"]
            channel = NotificationChannel(data["channel"])
            
            notification = Notification(
                id=notification_data["id"],
                user_id=notification_data["user_id"],
                shard_id=data["shard_id"],
                type=NotificationType(notification_data["type"]),
                title=notification_data["title"],
                message=notification_data["message"],
                data=notification_data["data"],
                priority=notification_data["priority"],
                created_at=datetime.fromisoformat(notification_data["created_at"]) if notification_data.get("created_at") else None
            )
            
            handler = cls._channel_handlers.get(channel)
            if handler:
                success = await handler(notification)
                
                if QueueService._initialized:
                    event_type = EventType.NOTIFICATION_SENT if success else EventType.NOTIFICATION_FAILED
                    await QueueService.get_instance().publish_event(
                        event_type,
                        "notification_service",
                        {
                            "notification_id": notification.id,
                            "channel": channel.value,
                            "success": success
                        }
                    )
                
                return success
            
            return False
            
        except Exception as e:
            Logger.error(f"Process notification queue failed: {e}")
            return False
    
    @classmethod
    async def _send_notification_direct(cls, notification: Notification, channels: List[NotificationChannel]):
        """
        직접 발송 (큐 없이)
        
        Args:
            notification: 알림 객체
            channels: 발송할 채널 목록
        """
        tasks = []
        for channel in channels:
            handler = cls._channel_handlers.get(channel)
            if handler:
                tasks.append(handler(notification))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    # === 채널별 발송 메서드 ===
    
    @classmethod
    async def _send_websocket(cls, notification: Notification) -> bool:
        """
        WebSocket 실시간 알림 발송
        
        Args:
            notification: 알림 객체
            
        Returns:
            bool: 발송 성공 여부
        """
        try:
            # WebSocketService 초기화 상태 확인
            if not WebSocketService.is_initialized():
                return False
            
            await WebSocketService.send_to_user(
                notification.user_id,
                "notification",
                {
                    "id": notification.id,
                    "type": notification.type.value,
                    "title": notification.title,
                    "message": notification.message,
                    "data": notification.data,
                    "priority": notification.priority,
                    "timestamp": notification.created_at.isoformat() if notification.created_at else None
                }
            )
            
            Logger.info(f"WebSocket notification sent to {notification.user_id}")
            return True
            
        except Exception as e:
            Logger.error(f"WebSocket send failed: {e}")
            return False
    
    @classmethod
    async def _send_in_app(cls, notification: Notification) -> bool:
        """
        인앱 알림함 저장
        
        Args:
            notification: 알림 객체
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            # ServiceContainer에서 DatabaseService 가져오기
            db_service = ServiceContainer.get_database_service()
            if not db_service:
                return False
            
            # 인앱 알림 저장 프로시저 호출
            result = await db_service.call_shard_procedure(
                notification.shard_id,
                "fp_inapp_notification_create",
                (
                    notification.id,
                    int(notification.user_id),
                    notification.type.value,
                    notification.title,
                    notification.message,
                    json.dumps(notification.data),
                    notification.priority
                )
            )
            
            if result and result[0].get('ErrorCode') == 0:
                Logger.info(f"In-app notification saved: {notification.user_id}")
                return True
            else:
                Logger.error(f"In-app notification save failed: {result[0] if result else 'No result'}")
                return False
            
        except Exception as e:
            Logger.error(f"In-app notification save failed: {e}")
            return False
    
    @classmethod
    async def _send_email(cls, notification: Notification) -> bool:
        """
        이메일 발송
        
        Args:
            notification: 알림 객체
            
        Returns:
            bool: 발송 성공 여부
        """
        try:
            # EmailService 초기화 상태 확인
            if not EmailService.is_initialized():
                Logger.warn("EmailService not initialized, skipping email notification")
                return False
            
            # 사용자 이메일 주소 조회 (임시로 기본값 사용)
            user_email = f"user{notification.user_id}@example.com"
            
            # 시그널 알림 이메일 발송
            if notification.type == NotificationType.PREDICTION_ALERT:
                result = await EmailService.send_prediction_alert(
                    user_email=user_email,
                    user_name=f"사용자{notification.user_id}",
                    stock_symbol=notification.data.get("symbol", "Unknown"),
                    stock_name=notification.data.get("stock_name", "Unknown Stock"),
                    prediction_type=notification.data.get("signal", "UNKNOWN"),
                    target_price=str(notification.data.get("target_price", "N/A")),
                    current_price=str(notification.data.get("current_price", "N/A")),
                    confidence=f"{notification.data.get('confidence', 0)*100:.1f}%"
                )
            else:
                # 기본 이메일 발송
                result = await EmailService.send_simple_email(
                    to_emails=[user_email],
                    subject=notification.title,
                    text_body=notification.message,
                    html_body=f"<h2>{notification.title}</h2><p>{notification.message}</p>",
                    from_name="AI Trading Platform"
                )
            
            if result["success"]:
                Logger.info(f"Email notification sent to {notification.user_id}")
                return True
            else:
                Logger.error(f"Email notification failed: {result.get('error', 'Unknown')}")
                return False
            
        except Exception as e:
            Logger.error(f"Email send failed: {e}")
            return False
    
    @classmethod
    async def _send_sms(cls, notification: Notification) -> bool:
        """
        SMS 발송
        
        Args:
            notification: 알림 객체
            
        Returns:
            bool: 발송 성공 여부
        """
        try:
            # SmsService 초기화 상태 확인
            if not SmsService.is_initialized():
                Logger.warn("SmsService not initialized, skipping SMS notification")
                return False
            
            # 긴급 알림만 SMS 발송 (비용 고려)
            if notification.priority > 2:
                Logger.info(f"Priority too low for SMS: {notification.user_id}, priority={notification.priority}")
                return True
            
            # 사용자 전화번호 조회 (임시로 기본값 사용)
            user_phone = f"+82-10-0000-{notification.user_id[-4:].zfill(4)}"
            
            # 시그널 알림 SMS 발송
            if notification.type == NotificationType.PREDICTION_ALERT:
                result = await SmsService.send_trading_signal(
                    user_phone=user_phone,
                    user_name=f"사용자{notification.user_id}",
                    stock_symbol=notification.data.get("symbol", "Unknown"),
                    signal_type=notification.data.get("signal", "UNKNOWN"),
                    target_price=str(notification.data.get("target_price", "N/A")),
                    confidence=f"{notification.data.get('confidence', 0)*100:.0f}%"
                )
            else:
                # 기본 SMS 발송 (160자 제한)
                short_message = notification.message
                if len(short_message) > 150:
                    short_message = short_message[:147] + "..."
                
                if notification.title and len(notification.title) + len(short_message) <= 160:
                    full_message = f"[{notification.title}] {short_message}"
                else:
                    full_message = short_message
                
                result = await SmsService.send_sms(
                    phone_number=user_phone,
                    message=full_message,
                    message_type="system_alert"
                )
            
            if result["success"]:
                Logger.info(f"SMS notification sent to {notification.user_id}")
                return True
            else:
                Logger.error(f"SMS notification failed: {result.get('error', 'Unknown')}")
                return False
            
        except Exception as e:
            Logger.error(f"SMS send failed: {e}")
            return False
    
    # === 모니터링 ===
    
    @classmethod
    async def get_stats(cls) -> Dict[str, Any]:
        """
        알림 서비스 통계 조회 (간소화)
        
        Returns:
            dict: 서비스 통계
        """
        if not cls._initialized:
            return {}
        
        try:
            stats = {
                "service": "NotificationService",
                "initialized": cls._initialized,
                "enabled_channels": [ch for ch, enabled in cls._config.enabled_channels.items() if enabled],
                "queue_stats": {}
            }
            
            if QueueService._initialized:
                queue_service = QueueService.get_instance()
                queue_stats = queue_service.get_queue_stats()
                stats["queue_stats"] = queue_stats.get("notification_queue", {})
            
            return stats
            
        except Exception as e:
            Logger.error(f"Get stats failed: {e}")
            return {}