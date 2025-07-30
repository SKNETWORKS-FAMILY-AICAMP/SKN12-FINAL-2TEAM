"""
통합 알림 서비스
- 멀티채널 알림 발송 관리
- 사용자 선호도 기반 필터링
- 중복 방지 및 우선순위 처리

서비스 패턴:
- 정적 클래스 (static class) 패턴 사용
- init() → 서비스 초기화
- shutdown() → 서비스 종료
- is_initialized() → 초기화 상태 확인
"""
import json
import asyncio
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass

from service.core.logger import Logger
from service.websocket.websocket_service import WebSocketService
from service.queue.queue_service import QueueService
from service.queue.event_queue import EventType
from service.cache.cache_service import CacheService
from service.db.database_service import DatabaseService
from service.service_container import ServiceContainer

# 새로 구현한 이메일/SMS 서비스 import
from service.email.email_service import EmailService
from service.sms.sms_service import SmsService

from .notification_config import NotificationConfig, NotificationChannel, NotificationType


@dataclass
class Notification:
    """
    알림 객체
    
    Attributes:
        id: 알림 고유 ID
        user_id: 수신자 ID
        type: 알림 타입 (예측, 거래, 시스템 등)
        title: 알림 제목
        message: 알림 내용
        data: 추가 데이터 (종목 정보, 가격 등)
        priority: 우선순위 (1=긴급, 5=낮음)
        channels: 발송할 채널 목록 (None이면 모든 채널)
        created_at: 생성 시간
    """
    id: str
    user_id: str
    type: NotificationType
    title: str
    message: str
    data: Dict[str, Any]
    priority: int = 3  # 1(높음) ~ 5(낮음)
    channels: Optional[List[NotificationChannel]] = None
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
            "channels": [ch.value for ch in self.channels] if self.channels else [],
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class NotificationService:
    """
    통합 알림 서비스 (정적 클래스)
    
    기존 서비스들(CacheService, ExternalService 등)과 동일한 패턴으로 구현
    - 모든 메서드는 @classmethod
    - _initialized 플래그로 초기화 상태 관리
    - ServiceContainer에 등록하여 전역 접근 가능
    
    주요 기능:
    1. 멀티채널 알림 발송 (WebSocket, Push, Email, SMS 등)
    2. 사용자별 알림 설정 확인
    3. 중복 알림 방지
    4. Rate limiting
    5. 우선순위 기반 발송
    """
    
    _config: Optional[NotificationConfig] = None
    _initialized: bool = False
    _channel_handlers: Dict[NotificationChannel, Any] = {}
    
    @classmethod
    async def init(cls, config: NotificationConfig) -> bool:
        """
        서비스 초기화
        
        Args:
            config: NotificationConfig 객체
            
        Returns:
            bool: 초기화 성공 여부
            
        Note:
            main.py의 lifespan에서 다른 서비스들 초기화 후 호출됨
            QueueService가 초기화되어 있으면 알림 발송 컨슈머도 자동 등록
        """
        try:
            cls._config = config
            
            # 채널별 핸들러 매핑
            # 각 채널은 독립적인 발송 메서드를 가짐
            cls._channel_handlers = {
                NotificationChannel.WEBSOCKET: cls._send_websocket,
                NotificationChannel.IN_APP: cls._send_in_app,
                NotificationChannel.PUSH: cls._send_push,
                NotificationChannel.EMAIL: cls._send_email,
                NotificationChannel.SMS: cls._send_sms
            }
            
            # 큐 서비스가 활성화되어 있으면 알림 발송 컨슈머 등록
            # 이렇게 하면 대량 알림도 비동기로 처리 가능
            if QueueService._initialized:
                queue_service = QueueService.get_instance()
                await queue_service.register_message_consumer(
                    "notification_queue",
                    "notification_sender",
                    cls._process_notification_queue
                )
                Logger.info("Notification queue consumer registered")
            
            cls._initialized = True
            Logger.info("NotificationService initialized")
            return True
            
        except Exception as e:
            Logger.error(f"NotificationService initialization failed: {e}")
            return False
    
    @classmethod
    async def shutdown(cls):
        """
        서비스 종료
        
        Note:
            main.py의 lifespan 종료 시 호출됨
            특별한 정리 작업은 없고 플래그만 변경
        """
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
                               notification_type: NotificationType,
                               title: str,
                               message: str,
                               data: Dict[str, Any],
                               priority: int = 3,
                               channels: Optional[List[NotificationChannel]] = None) -> bool:
        """
        알림 발송 (메인 엔트리포인트)
        
        Args:
            user_id: 수신자 ID
            notification_type: 알림 타입 (PREDICTION_ALERT, TRADE_EXECUTED 등)
            title: 알림 제목
            message: 알림 내용
            data: 추가 데이터 (종목명, 가격, 신호 등)
            priority: 우선순위 (1~5, 낮을수록 높음)
            channels: 발송 채널 목록 (None이면 사용자 설정에 따름)
            
        Returns:
            bool: 발송 성공 여부 (큐에 추가되면 True)
            
        Example:
            await NotificationService.send_notification(
                user_id="user123",
                notification_type=NotificationType.PREDICTION_ALERT,
                title="AAPL 매수 신호",
                message="AI가 AAPL 매수를 추천합니다",
                data={
                    "symbol": "AAPL",
                    "signal": "BUY",
                    "confidence": 0.85,
                    "current_price": 150.0
                },
                priority=2
            )
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
                type=notification_type,
                title=title,
                message=message,
                data=data,
                priority=priority,
                channels=channels,
                created_at=datetime.utcnow()
            )
            
            # 1. 중복 체크 - 같은 내용의 알림이 최근에 발송되었는지 확인
            if await cls._is_duplicate(notification):
                Logger.info(f"Duplicate notification skipped: {notification.id}")
                return True  # 중복이어도 True 반환 (정상 처리로 간주)
            
            # 2. 사용자 설정 확인 - 알림 수신 여부, 채널별 설정 등
            user_preferences = await cls._get_user_preferences(user_id)
            if not user_preferences.get("enabled", True):
                Logger.info(f"User {user_id} has notifications disabled")
                return True  # 사용자가 알림을 꺼둔 경우도 정상 처리
            
            # 3. 채널 결정 - 요청된 채널 + 사용자 설정 + 시스템 설정 고려
            target_channels = await cls._determine_channels(notification, user_preferences)
            if not target_channels:
                Logger.info(f"No channels available for user {user_id}")
                return True
            
            # 4. Rate limit 체크 - 사용자별 시간당 알림 수 제한
            if not await cls._check_rate_limit(user_id):
                Logger.warn(f"Rate limit exceeded for user {user_id}")
                # Rate limit 초과 이벤트 발행
                if QueueService._initialized:
                    await QueueService.get_instance().publish_event(
                        EventType.SYSTEM_ERROR,
                        "notification_service",
                        {"user_id": user_id, "error": "rate_limit_exceeded"}
                    )
                return False
            
            # 5. 큐에 추가 - 실제 발송은 비동기로 처리
            await cls._queue_notification(notification, target_channels)
            
            # 6. 이벤트 발행 - 알림 생성 이벤트
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
        
        동일한 사용자에게 동일한 내용의 알림이 설정된 시간 내에 발송되었는지 확인
        data 필드를 해시하여 내용이 같은지 판단
        
        Args:
            notification: 체크할 알림 객체
            
        Returns:
            bool: 중복이면 True
        """
        try:
            if not CacheService.is_initialized():
                return False
            
            # 중복 체크 키: user_id:type:data_hash
            # data를 JSON으로 직렬화 후 MD5 해시 (빠른 비교를 위해)
            import hashlib
            data_str = json.dumps(notification.data, sort_keys=True)
            data_hash = hashlib.md5(data_str.encode()).hexdigest()[:8]
            
            dedup_key = f"notif:dedup:{notification.user_id}:{notification.type.value}:{data_hash}"
            
            # Redis에서 키 존재 확인
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
            return False  # 에러 시 중복 아닌 것으로 처리
    
    @classmethod
    async def _get_user_email(cls, user_id: str) -> Optional[str]:
        """
        사용자 이메일 주소 조회
        
        캐시 → DB 순서로 조회
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            str: 이메일 주소 (없으면 None)
        """
        try:
            # 1. 캐시에서 먼저 확인
            if CacheService.is_initialized():
                async with CacheService.get_client() as client:
                    cache_key = f"user:email:{user_id}"
                    cached_email = await client.get(cache_key)
                    if cached_email:
                        return cached_email.decode() if isinstance(cached_email, bytes) else cached_email
            
            # 2. DB에서 조회
            db_service = ServiceContainer.get_database_service()
            if db_service:
                # TODO: 실제 프로시저로 교체
                # result = await db_service.call_global_procedure("fp_get_user_email", (user_id,))
                # 임시 테스트용 이메일
                test_email = f"user{user_id}@test.com"
                
                # 3. 캐시에 저장 (1시간 TTL)
                if CacheService.is_initialized():
                    async with CacheService.get_client() as client:
                        await client.setex(f"user:email:{user_id}", 3600, test_email)
                
                return test_email
            
            return None
            
        except Exception as e:
            Logger.error(f"사용자 이메일 조회 실패: {e}")
            return None
    
    @classmethod
    async def _get_user_phone(cls, user_id: str) -> Optional[str]:
        """
        사용자 전화번호 조회
        
        캐시 → DB 순서로 조회
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            str: 전화번호 (국제형식, 없으면 None)
        """
        try:
            # 1. 캐시에서 먼저 확인
            if CacheService.is_initialized():
                async with CacheService.get_client() as client:
                    cache_key = f"user:phone:{user_id}"
                    cached_phone = await client.get(cache_key)
                    if cached_phone:
                        return cached_phone.decode() if isinstance(cached_phone, bytes) else cached_phone
            
            # 2. DB에서 조회
            db_service = ServiceContainer.get_database_service()
            if db_service:
                # TODO: 실제 프로시저로 교체
                # result = await db_service.call_global_procedure("fp_get_user_phone", (user_id,))
                # 임시 테스트용 전화번호 (SMS 테스트 시에는 실제 번호로 변경)
                test_phone = f"+82-10-1234-{user_id[-4:].zfill(4)}"
                
                # 3. 캐시에 저장 (1시간 TTL)
                if CacheService.is_initialized():
                    async with CacheService.get_client() as client:
                        await client.setex(f"user:phone:{user_id}", 3600, test_phone)
                
                return test_phone
            
            return None
            
        except Exception as e:
            Logger.error(f"사용자 전화번호 조회 실패: {e}")
            return None
    
    @classmethod
    async def _get_user_name(cls, user_id: str) -> str:
        """
        사용자 이름 조회
        
        캐시 → DB 순서로 조회
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            str: 사용자 이름 (없으면 기본값)
        """
        try:
            # 1. 캐시에서 먼저 확인
            if CacheService.is_initialized():
                async with CacheService.get_client() as client:
                    cache_key = f"user:name:{user_id}"
                    cached_name = await client.get(cache_key)
                    if cached_name:
                        return cached_name.decode() if isinstance(cached_name, bytes) else cached_name
            
            # 2. DB에서 조회
            db_service = ServiceContainer.get_database_service()
            if db_service:
                # TODO: 실제 프로시저로 교체
                # result = await db_service.call_global_procedure("fp_get_user_name", (user_id,))
                # 임시 기본 이름
                default_name = f"사용자{user_id}"
                
                # 3. 캐시에 저장 (1시간 TTL)
                if CacheService.is_initialized():
                    async with CacheService.get_client() as client:
                        await client.setex(f"user:name:{user_id}", 3600, default_name)
                
                return default_name
            
            return f"사용자{user_id}"  # 기본값
            
        except Exception as e:
            Logger.error(f"사용자 이름 조회 실패: {e}")
            return f"사용자{user_id}"
    
    @classmethod
    async def _get_user_preferences(cls, user_id: str) -> Dict[str, Any]:
        """
        사용자 알림 설정 조회
        
        캐시 → DB 순서로 조회
        사용자별 알림 on/off, 채널별 설정, 알림 타입별 설정 포함
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            dict: 사용자 설정 (enabled, channels, types)
        """
        try:
            # 1. 캐시에서 먼저 확인 (빠른 조회)
            if CacheService.is_initialized():
                async with CacheService.get_client() as client:
                    cache_key = f"notif:pref:{user_id}"
                    cached = await client.get(cache_key)
                    if cached:
                        return json.loads(cached)
            
            # 2. DB에서 조회
            db_service = ServiceContainer.get_database_service()
            if db_service:
                # TODO: 실제 프로시저로 교체
                # result = await db_service.call_global_procedure("fp_get_user_notification_settings", (user_id,))
                
                # 임시 기본값
                preferences = {
                    "enabled": True,  # 전체 알림 on/off
                    "channels": {     # 채널별 설정
                        "websocket": True,
                        "in_app": True,
                        "push": True,
                        "email": False,
                        "sms": False
                    },
                    "types": {        # 알림 타입별 설정
                        "prediction_alert": True,
                        "price_target_reached": True,
                        "trade_executed": True
                    }
                }
                
                # 3. 캐시에 저장 (1시간 TTL)
                if CacheService.is_initialized():
                    async with CacheService.get_client() as client:
                        await client.setex(cache_key, 3600, json.dumps(preferences))
                
                return preferences
            
            # DB 연결 실패 시 기본값
            return {"enabled": True, "channels": {}, "types": {}}
            
        except Exception as e:
            Logger.error(f"Get user preferences failed: {e}")
            return {"enabled": True, "channels": {}, "types": {}}
    
    @classmethod
    async def _determine_channels(cls, notification: Notification, 
                                user_preferences: Dict[str, Any]) -> List[NotificationChannel]:
        """
        알림 채널 결정
        
        우선순위:
        1. 요청 시 명시된 채널
        2. 시스템 설정에서 활성화된 채널
        3. 사용자가 허용한 채널
        4. 채널별 특수 조건 (예: WebSocket은 온라인일 때만)
        
        Args:
            notification: 알림 객체
            user_preferences: 사용자 설정
            
        Returns:
            list: 발송할 채널 목록 (우선순위 순)
        """
        channels = []
        
        # 1. 명시적으로 지정된 채널이 있으면 사용
        if notification.channels:
            requested_channels = notification.channels
        else:
            # 2. 지정이 없으면 모든 채널 대상
            requested_channels = list(NotificationChannel)
        
        # 3. 각 채널별 검증
        for channel in requested_channels:
            # 시스템에서 활성화되어 있는지
            if not cls._config.enabled_channels.get(channel.value, False):
                continue
                
            # 사용자가 허용했는지
            if not user_preferences.get("channels", {}).get(channel.value, True):
                continue
            
            # 채널별 특수 조건 체크
            if channel == NotificationChannel.WEBSOCKET:
                # WebSocket은 현재 연결된 사용자에게만
                if WebSocketService.is_initialized() and WebSocketService.is_user_connected(notification.user_id):
                    channels.append(channel)
            else:
                channels.append(channel)
        
        # 4. 우선순위 정렬 (설정된 우선순위에 따라)
        channels.sort(key=lambda ch: cls._config.priority_channels.get(ch.value, 99))
        
        return channels
    
    @classmethod
    async def _check_rate_limit(cls, user_id: str) -> bool:
        """
        Rate limit 체크
        
        사용자별 시간당 알림 수 제한
        Redis의 incr 명령어로 카운터 관리
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            bool: 제한 내면 True, 초과면 False
        """
        try:
            if not CacheService.is_initialized():
                return True  # 캐시 없으면 제한 없음
            
            # 시간별 키 생성 (예: notif:rate:user123:2024010114)
            rate_key = f"notif:rate:{user_id}:{datetime.utcnow().strftime('%Y%m%d%H')}"
            
            async with CacheService.get_client() as client:
                # 카운터 증가
                current = await client.incr(rate_key)
                
                # 첫 번째면 TTL 설정
                if current == 1:
                    await client.expire(rate_key, 3600)
                
                # 제한 확인
                return current <= cls._config.rate_limit_per_user_per_hour
                
        except Exception as e:
            Logger.error(f"Rate limit check failed: {e}")
            return True  # 에러 시 통과
    
    @classmethod
    async def _queue_notification(cls, notification: Notification, channels: List[NotificationChannel]):
        """
        알림을 큐에 추가
        
        각 채널별로 메시지를 큐에 추가
        큐가 없으면 직접 발송 (fallback)
        
        Args:
            notification: 알림 객체
            channels: 발송할 채널 목록
        """
        if not QueueService._initialized:
            # 큐가 없으면 직접 발송 (개발/테스트 환경)
            await cls._send_notification_direct(notification, channels)
            return
        
        queue_service = QueueService.get_instance()
        
        # 각 채널별로 큐에 추가
        for channel in channels:
            message = {
                "notification": notification.to_dict(),
                "channel": channel.value
            }
            
            # 우선순위에 따라 큐 선택
            from service.queue.message_queue import MessagePriority
            priority = MessagePriority.HIGH if notification.priority <= 2 else MessagePriority.NORMAL
            
            await queue_service.send_message(
                "notification_queue",
                message,
                f"notification_{channel.value}",  # 메시지 타입
                priority
            )
    
    @classmethod
    async def _process_notification_queue(cls, message) -> bool:
        """
        큐에서 알림 처리 (컨슈머)
        
        QueueService에서 메시지를 받아 실제 발송 수행
        발송 결과에 따라 이벤트 발행
        
        Args:
            message: QueueMessage 객체
            
        Returns:
            bool: 처리 성공 여부
        """
        try:
            data = message.payload
            notification_data = data["notification"]
            channel = NotificationChannel(data["channel"])
            
            # Notification 객체 재구성
            notification = Notification(
                id=notification_data["id"],
                user_id=notification_data["user_id"],
                type=NotificationType(notification_data["type"]),
                title=notification_data["title"],
                message=notification_data["message"],
                data=notification_data["data"],
                priority=notification_data["priority"],
                created_at=datetime.fromisoformat(notification_data["created_at"]) if notification_data.get("created_at") else None
            )
            
            # 채널별 핸들러 호출
            handler = cls._channel_handlers.get(channel)
            if handler:
                success = await handler(notification)
                
                # 발송 결과 이벤트 발행
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
        
        개발/테스트 환경에서 큐 없이 직접 발송
        모든 채널 동시 발송 (asyncio.gather)
        
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
            # 모든 채널 동시 발송, 예외 무시
            await asyncio.gather(*tasks, return_exceptions=True)
    
    # === 채널별 발송 메서드 ===
    
    @classmethod
    async def _send_websocket(cls, notification: Notification) -> bool:
        """
        WebSocket 발송
        
        현재 연결된 사용자에게 실시간으로 알림 전송
        WebSocketService.send_to_user() 사용
        
        Args:
            notification: 알림 객체
            
        Returns:
            bool: 발송 성공 여부
        """
        try:
            if not WebSocketService.is_initialized():
                return False
            
            # WebSocket 메시지 포맷
            await WebSocketService.send_to_user(
                notification.user_id,
                "notification",  # 메시지 타입
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
        
        DB에 알림을 저장하여 사용자가 나중에 확인 가능
        notifications 테이블에 저장
        
        Args:
            notification: 알림 객체
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            db_service = ServiceContainer.get_database_service()
            if not db_service:
                return False
            
            # TODO: 실제 프로시저로 교체
            # shard_id = get_shard_id(notification.user_id)
            # await db_service.call_shard_procedure(
            #     shard_id,
            #     "fp_save_notification",
            #     (notification.user_id, json.dumps(notification.to_dict()))
            # )
            
            Logger.info(f"In-app notification saved for {notification.user_id}")
            return True
            
        except Exception as e:
            Logger.error(f"In-app notification save failed: {e}")
            return False
    
    @classmethod
    async def _send_push(cls, notification: Notification) -> bool:
        """
        푸시 알림 발송 (FCM/APNS)
        
        Firebase Cloud Messaging (Android) / Apple Push Notification Service (iOS)
        
        Args:
            notification: 알림 객체
            
        Returns:
            bool: 발송 성공 여부
            
        TODO:
            - FCM/APNS 연동
            - 디바이스 토큰 관리
            - 플랫폼별 페이로드 포맷
        """
        try:
            # TODO: FCM/APNS 연동
            # 1. DB에서 사용자의 디바이스 토큰 조회
            # 2. 플랫폼별 (iOS/Android) 페이로드 생성
            # 3. FCM/APNS API 호출
            
            Logger.info(f"Push notification would be sent to {notification.user_id}")
            return True
            
        except Exception as e:
            Logger.error(f"Push send failed: {e}")
            return False
    
    @classmethod
    async def _send_email(cls, notification: Notification) -> bool:
        """
        이메일 발송 (AWS SES 연동)
        
        새로 구현한 EmailService를 사용해서 실제로 이메일을 발송합니다.
        사용자 이메일 주소를 DB에서 조회하고, 알림 타입에 따라 적절한 템플릿을 사용합니다.
        
        Args:
            notification: 알림 객체
            
        Returns:
            bool: 발송 성공 여부
        """
        try:
            # 1. EmailService 초기화 확인
            if not EmailService.is_initialized():
                Logger.error("EmailService가 초기화되지 않았습니다")
                return False
            
            # 2. DB에서 사용자 이메일 주소 조회
            user_email = await cls._get_user_email(notification.user_id)
            if not user_email:
                Logger.warn(f"사용자 {notification.user_id}의 이메일 주소를 찾을 수 없습니다")
                return False
            
            # 3. 알림 타입별 이메일 발송
            if notification.type == NotificationType.PREDICTION_ALERT:
                # 예측 알림: 전용 편의 메서드 사용
                result = await EmailService.send_prediction_alert(
                    user_email=user_email,
                    user_name=await cls._get_user_name(notification.user_id),
                    stock_symbol=notification.data.get("symbol", "Unknown"),
                    stock_name=notification.data.get("stock_name", "Unknown Stock"),
                    prediction_type=notification.data.get("signal", "UNKNOWN"),
                    target_price=str(notification.data.get("target_price", "N/A")),
                    current_price=str(notification.data.get("current_price", "N/A")),
                    confidence=f"{notification.data.get('confidence', 0)*100:.1f}%"
                )
            else:
                # 일반 알림: 기본 이메일 발송
                # HTML 본문 생성 (간단한 형태)
                html_body = f"""
                <h2>{notification.title}</h2>
                <p>{notification.message}</p>
                """
                
                # 추가 데이터가 있으면 테이블로 표시
                if notification.data:
                    html_body += "<h3>상세 정보</h3><table>"
                    for key, value in notification.data.items():
                        html_body += f"<tr><td><strong>{key}</strong></td><td>{value}</td></tr>"
                    html_body += "</table>"
                
                result = await EmailService.send_simple_email(
                    to_emails=[user_email],
                    subject=notification.title,
                    text_body=notification.message,
                    html_body=html_body,
                    from_name="AI Trading Platform"
                )
            
            # 4. 발송 결과 처리
            if result["success"]:
                Logger.info(f"이메일 발송 성공: {notification.user_id} -> {user_email}, MessageId: {result.get('message_id', 'N/A')}")
                return True
            else:
                Logger.error(f"이메일 발송 실패: {notification.user_id} -> {user_email}, Error: {result.get('error', 'Unknown')}")
                return False
            
        except Exception as e:
            Logger.error(f"이메일 발송 중 예상치 못한 에러: {e}")
            return False
    
    @classmethod
    async def _send_sms(cls, notification: Notification) -> bool:
        """
        SMS 발송 (AWS SNS 연동)
        
        새로 구현한 SmsService를 사용해서 실제로 SMS를 발송합니다.
        긴급하고 중요한 알림에만 사용합니다 (비용 고려).
        
        Args:
            notification: 알림 객체
            
        Returns:
            bool: 발송 성공 여부
        """
        try:
            # 1. SmsService 초기화 확인
            if not SmsService.is_initialized():
                Logger.error("SmsService가 초기화되지 않았습니다")
                return False
            
            # 2. 긴급 알림만 SMS 발송 (비용 절약)
            if notification.priority > 2:  # 우선순위 1,2만 SMS 발송
                Logger.info(f"우선순위가 낮아 SMS 발송을 건너뜁니다: {notification.user_id}, priority={notification.priority}")
                return True  # 건너뛰는 것도 성공으로 처리
            
            # 3. DB에서 사용자 전화번호 조회
            user_phone = await cls._get_user_phone(notification.user_id)
            if not user_phone:
                Logger.warn(f"사용자 {notification.user_id}의 전화번호를 찾을 수 없습니다")
                return False
            
            # 4. 알림 타입별 SMS 발송
            if notification.type == NotificationType.PREDICTION_ALERT:
                # 예측 알림: 매매 신호 SMS 전용 메서드 사용
                result = await SmsService.send_trading_signal(
                    user_phone=user_phone,
                    user_name=await cls._get_user_name(notification.user_id),
                    stock_symbol=notification.data.get("symbol", "Unknown"),
                    signal_type=notification.data.get("signal", "UNKNOWN"),
                    target_price=str(notification.data.get("target_price", "N/A")),
                    confidence=f"{notification.data.get('confidence', 0)*100:.0f}%"
                )
            elif notification.type in [NotificationType.PRICE_TARGET_REACHED, NotificationType.MARKET_CRASH]:
                # 급등/급락 알림: 긴급 알림 메서드 사용
                alert_type = "급등" if "상승" in notification.message or "급등" in notification.message else "급락"
                result = await SmsService.send_urgent_alert(
                    phone_number=user_phone,
                    stock_symbol=notification.data.get("symbol", "Unknown"),
                    alert_type=alert_type,
                    price_info=notification.data.get("price_change", "N/A"),
                    additional_info=notification.data.get("reason", "")
                )
            elif notification.type == NotificationType.SYSTEM_ALERT:
                # 시스템 알림: 시스템 알림 메서드 사용
                result = await SmsService.send_system_alert(
                    phone_numbers=[user_phone],
                    alert_message=notification.message,
                    alert_priority="high" if notification.priority <= 2 else "medium"
                )
            else:
                # 기타 알림: 기본 SMS 발송
                # 메시지를 160자 이내로 줄임
                short_message = notification.message
                if len(short_message) > 150:  # 제목 추가 고려
                    short_message = short_message[:147] + "..."
                
                # 제목이 있으면 앞에 추가
                if notification.title and len(notification.title) + len(short_message) <= 160:
                    full_message = f"[{notification.title}] {short_message}"
                else:
                    full_message = short_message
                
                result = await SmsService.send_sms(
                    phone_number=user_phone,
                    message=full_message,
                    message_type="system_alert"
                )
            
            # 5. 발송 결과 처리
            if result["success"]:
                Logger.info(f"SMS 발송 성공: {notification.user_id} -> {user_phone}, MessageId: {result.get('message_id', 'N/A')}")
                return True
            else:
                Logger.error(f"SMS 발송 실패: {notification.user_id} -> {user_phone}, Error: {result.get('error', 'Unknown')}")
                return False
            
        except Exception as e:
            Logger.error(f"SMS 발송 중 예상치 못한 에러: {e}")
            return False
    
    # === 배치 발송 ===
    
    @classmethod
    async def send_batch_notifications(cls, notifications: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        배치 알림 발송
        
        대량 알림을 효율적으로 발송
        배치 크기와 간격을 조절하여 시스템 부하 관리
        
        Args:
            notifications: 알림 데이터 리스트
            
        Returns:
            dict: 발송 결과 통계 (total, success, failed)
            
        Example:
            results = await NotificationService.send_batch_notifications([
                {
                    "user_id": "user1",
                    "type": "prediction_alert",
                    "title": "AAPL 매수 신호",
                    "message": "...",
                    "data": {...}
                },
                ...
            ])
        """
        if not cls._initialized:
            return {"total": 0, "success": 0, "failed": 0}
        
        results = {"total": len(notifications), "success": 0, "failed": 0}
        
        # 설정된 배치 크기로 분할
        batch_size = cls._config.batch_size
        for i in range(0, len(notifications), batch_size):
            batch = notifications[i:i + batch_size]
            
            # 배치 내 모든 알림 동시 발송
            tasks = []
            for notif_data in batch:
                task = cls.send_notification(
                    user_id=notif_data["user_id"],
                    notification_type=NotificationType(notif_data["type"]),
                    title=notif_data["title"],
                    message=notif_data["message"],
                    data=notif_data.get("data", {}),
                    priority=notif_data.get("priority", 3),
                    channels=[NotificationChannel(ch) for ch in notif_data.get("channels", [])]
                        if "channels" in notif_data else None
                )
                tasks.append(task)
            
            # 배치 실행 및 결과 수집
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    results["failed"] += 1
                elif result:
                    results["success"] += 1
                else:
                    results["failed"] += 1
            
            # 다음 배치까지 대기 (시스템 부하 관리)
            if i + batch_size < len(notifications):
                await asyncio.sleep(cls._config.batch_timeout_seconds)
        
        return results
    
    # === 통계 및 모니터링 ===
    
    @classmethod
    async def get_stats(cls) -> Dict[str, Any]:
        """
        알림 서비스 통계 조회
        
        서비스 상태, 활성 채널, 큐 상태 등
        
        Returns:
            dict: 서비스 통계
        """
        if not cls._initialized:
            return {}
        
        try:
            stats = {
                "service": "NotificationService",
                "initialized": cls._initialized,
                "enabled_channels": list(cls._config.enabled_channels.keys()),
                "queue_stats": {}
            }
            
            # 큐 통계 추가
            if QueueService._initialized:
                queue_service = QueueService.get_instance()
                queue_stats = queue_service.get_queue_stats()
                stats["queue_stats"] = queue_stats.get("notification_queue", {})
            
            return stats
            
        except Exception as e:
            Logger.error(f"Get stats failed: {e}")
            return {}