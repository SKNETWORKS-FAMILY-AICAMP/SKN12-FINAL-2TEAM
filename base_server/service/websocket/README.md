# AI Trading Platform — WebSocket Service

> **개요**: SKN12-FINAL-2TEAM의 AI 트레이딩 플랫폼 백엔드 WebSocket 서비스입니다. 실시간 양방향 통신을 지원하며, 클라이언트 연결 관리, 채널 기반 메시지 브로드캐스트, Redis Pub/Sub 연동을 통한 다중 서버 환경 지원을 제공하는 시스템입니다.

---

## 🏗️ 프로젝트 구조

### 디렉토리 구조
```
websocket/
├── __init__.py                    # 패키지 초기화
├── README.md                      # 서비스 문서
├── websocket_config.py            # WebSocket 설정 관리
├── websocket_client.py            # 클라이언트 관리 및 메시지 처리
└── websocket_service.py           # 메인 WebSocket 서비스
```

### 핵심 컴포넌트
- **WebSocketConfig**: 연결 설정, 보안, Redis 연동 설정 관리
- **WebSocketClientManager**: 클라이언트 연결, 채널 구독, 메시지 라우팅
- **WebSocketService**: 정적 클래스 기반 메인 서비스 및 백그라운드 태스크
- **WebSocketClient**: 개별 클라이언트 정보 및 상태 관리
- **WebSocketMessage**: 메시지 구조 및 타입 정의

---

## 🔧 핵심 기능

### 1. **실시간 양방향 통신**
- **WebSocket 연결 관리**: 클라이언트 연결/해제 및 상태 추적
- **메시지 라우팅**: 타입 기반 메시지 처리 및 핸들러 등록
- **실시간 브로드캐스트**: 채널 기반 및 전체 클라이언트 대상 메시지 전송
- **연결 상태 모니터링**: 연결 상태, ping/pong, heartbeat 관리

### 2. **채널 기반 메시징 시스템**
- **동적 채널 구독**: 클라이언트별 채널 구독/해제 관리
- **채널별 브로드캐스트**: 특정 채널 구독자에게만 메시지 전송
- **사용자별 메시징**: 특정 사용자의 모든 클라이언트에게 메시지 전송
- **채널 정보 관리**: 구독자 수, 채널 목록 등 메타데이터 제공

### 3. **연결 품질 및 안정성**
- **Heartbeat 시스템**: 주기적인 연결 상태 확인 및 유지
- **Ping/Pong 메커니즘**: 클라이언트 응답성 모니터링
- **자동 연결 정리**: 비활성 연결 자동 감지 및 정리
- **연결 수 제한**: 최대 연결 수 제한으로 시스템 보호

### 4. **다중 서버 환경 지원**
- **Redis Pub/Sub 연동**: 서버 간 메시지 동기화
- **채널 기반 메시지 전파**: Redis를 통한 크로스 서버 브로드캐스트
- **설정 가능한 연동**: Redis 사용 여부 및 채널 접두사 설정
- **확장 가능한 아키텍처**: 수평적 확장 지원

### 5. **보안 및 인증**
- **Origin 검증**: 허용된 origin 목록 기반 접근 제어
- **사용자 인증**: WebSocket 연결 시 사용자 ID 검증
- **메시지 크기 제한**: 최대 메시지 크기 제한으로 DoS 방지
- **연결 타임아웃**: 비활성 연결 자동 종료

---

## 📚 사용된 라이브러리

### **Core Framework**
- **FastAPI**: 현대적인 Python 웹 프레임워크 및 WebSocket 지원
- **asyncio**: 비동기 프로그래밍 및 이벤트 루프 관리
- **uuid**: 고유 식별자 생성
- **datetime**: 시간 기반 데이터 처리 및 타임스탬프

### **WebSocket & 통신**
- **WebSocket**: 실시간 양방향 통신 프로토콜
- **JSON**: 메시지 직렬화 및 파싱
- **dataclasses**: 데이터 구조 정의
- **enum**: 연결 상태 및 메시지 타입 정의

### **설정 & 유틸리티**
- **Pydantic**: 설정 검증 및 데이터 모델
- **typing**: 타입 힌트 및 타입 안전성
- **dataclasses**: 데이터 클래스 정의

### **캐시 & 인프라**
- **Redis**: 다중 서버 환경에서의 메시지 동기화
- **CacheService**: Redis 클라이언트 관리

---

## 🪝 핵심 클래스 및 메서드

### **WebSocketService - 메인 서비스 클래스**

```python
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
        # WebSocketConfig 로드 및 클라이언트 매니저 초기화
    
    @classmethod
    async def start_background_tasks(cls):
        """백그라운드 태스크 시작"""
        # Heartbeat 루프 및 정리 루프 시작
    
    @classmethod
    async def connect_client(cls, websocket: WebSocket, user_id: Optional[str] = None):
        """클라이언트 연결"""
        # 연결 수 제한 확인, 인증 검증, 클라이언트 ID 생성
    
    @classmethod
    async def broadcast_to_channel(cls, channel: str, message: Dict[str, Any]):
        """채널의 모든 구독자에게 메시지 브로드캐스트"""
        # 채널 구독자 목록 조회 및 메시지 전송
```

**동작 방식**:
- 정적 클래스 구조로 전역 WebSocket 서비스 제공
- 백그라운드 태스크를 통한 자동 연결 관리
- 클라이언트 연결 수 제한 및 인증 검증
- 채널 기반 메시지 라우팅 및 브로드캐스트

### **WebSocketClientManager - 클라이언트 관리**

```python
class WebSocketClientManager:
    """WebSocket 클라이언트 관리자"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocketClient] = {}
        self.channel_subscribers: Dict[str, List[str]] = {}
        self.user_clients: Dict[str, List[str]] = {}
        self.message_handlers: Dict[str, Callable] = {}
        self.stats = {...}
    
    async def connect(self, client_id: str, websocket: WebSocket, user_id: Optional[str] = None):
        """클라이언트 연결"""
        # WebSocket 연결 수락 및 클라이언트 정보 저장
    
    async def subscribe_to_channel(self, client_id: str, channel: str):
        """클라이언트를 채널에 구독"""
        # 채널 구독자 목록에 추가 및 양방향 매핑
    
    async def broadcast_to_channel(self, channel: str, message: Dict[str, Any]):
        """채널의 모든 구독자에게 메시지 브로드캐스트"""
        # 구독자 목록 조회 및 메시지 전송
```

**동작 방식**:
- 연결된 클라이언트의 실시간 상태 관리
- 채널별 구독자 매핑 및 메시지 라우팅
- 사용자별 클라이언트 매핑으로 다중 디바이스 지원
- 통계 정보 수집 및 모니터링

### **WebSocketClient - 개별 클라이언트**

```python
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

class ConnectionState(Enum):
    """연결 상태"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
```

**동작 방식**:
- 클라이언트별 연결 상태 및 메타데이터 관리
- 구독 중인 채널 목록 추적
- Ping/Pong 시간 기록으로 연결 품질 모니터링
- 사용자 ID와의 연결으로 인증 및 권한 관리

---

## 🌐 설정 및 구성 방식

### **WebSocketConfig - 통합 설정**

```python
class WebSocketConfig(BaseModel):
    """WebSocket 서비스 설정"""
    
    # 연결 설정
    max_connections: int = 1000                    # 최대 연결 수
    max_message_size: int = 1024 * 1024           # 최대 메시지 크기 (1MB)
    ping_interval: int = 20                       # Ping 간격 (초)
    ping_timeout: int = 10                        # Ping 응답 대기 시간 (초)
    
    # 연결 유지 설정
    heartbeat_interval: int = 30                  # Heartbeat 간격 (초)
    connection_timeout: int = 60                  # 연결 타임아웃 (초)
    
    # 메시지 관련 설정
    message_queue_size: int = 100                 # 클라이언트별 메시지 큐 크기
    broadcast_buffer_size: int = 1000             # 브로드캐스트 버퍼 크기
    
    # 보안 설정
    allowed_origins: List[str] = ["*"]           # 허용된 origin 목록
    require_auth: bool = True                     # 인증 필수 여부
    
    # Redis 설정 (다중 서버 환경)
    use_redis_pubsub: bool = False               # Redis Pub/Sub 사용 여부
    redis_channel_prefix: str = "websocket"      # Redis 채널 접두사
    
    # 재시도 설정
    max_retries: int = 3                         # 최대 재시도 횟수
    retry_timeout_seconds: int = 5               # 재시도 타임아웃 (초)
```

### **설정 파일 예시**

```python
# config.py
from service.websocket.websocket_config import WebSocketConfig

# WebSocket 설정
websocket_config = WebSocketConfig(
    max_connections=1000,              # 최대 1000개 동시 연결
    max_message_size=1024*1024,       # 1MB 최대 메시지 크기
    ping_interval=20,                 # 20초마다 ping
    heartbeat_interval=30,            # 30초마다 heartbeat
    connection_timeout=60,            # 60초 비활성 시 연결 종료
    require_auth=True,                # 인증 필수
    use_redis_pubsub=True,           # Redis Pub/Sub 활성화 (다중 서버)
    redis_channel_prefix="ai_trading" # Redis 채널 접두사
)
```

---

## 🔄 WebSocket 서비스 전체 흐름

### **1. 서비스 초기화**
```
1. WebSocketConfig 객체 생성 및 설정 로드
2. WebSocketService.init() 호출
3. WebSocketClientManager 인스턴스 생성
4. 백그라운드 태스크 시작 (heartbeat, cleanup)
5. Redis Pub/Sub 연동 설정 (선택사항)
```

### **2. 클라이언트 연결 플로우**
```
1. 클라이언트 WebSocket 연결 요청
2. 연결 수 제한 확인 (max_connections)
3. 인증 검증 (require_auth=True인 경우)
4. 고유 클라이언트 ID 생성
5. WebSocketClient 객체 생성 및 저장
6. 연결 확인 메시지 전송
7. 사용자별 클라이언트 매핑 추가
```

### **3. 메시지 처리 플로우**
```
1. 클라이언트로부터 메시지 수신
2. JSON 파싱 및 유효성 검사
3. 메시지 타입별 핸들러 호출
   - ping: pong 응답
   - subscribe: 채널 구독
   - unsubscribe: 채널 구독 해제
   - custom: 등록된 커스텀 핸들러
4. 처리 결과 클라이언트에게 응답
5. 통계 정보 업데이트
```

### **4. 채널 기반 메시징 플로우**
```
1. 클라이언트 채널 구독 요청
2. 채널 구독자 목록에 클라이언트 추가
3. 클라이언트 채널 목록에 채널 추가
4. 구독 성공/실패 응답 전송
5. 채널 브로드캐스트 시 구독자 목록 조회
6. 모든 구독자에게 메시지 전송
```

### **5. 백그라운드 태스크 플로우**
```
1. Heartbeat 루프: 주기적으로 모든 클라이언트에게 heartbeat 전송
2. 정리 루프: 비활성 연결 감지 및 자동 정리
3. Redis Pub/Sub: 다중 서버 환경에서 메시지 동기화
4. 통계 수집: 연결 수, 메시지 수, 에러 수 등 실시간 모니터링
```

---

## 🔌 WebSocket 메시지 처리 상세

### **메시지 타입 및 구조**

#### **1. 기본 메시지 타입**

```python
@dataclass
class WebSocketMessage:
    """WebSocket 메시지"""
    type: str                    # 메시지 타입
    data: Any                    # 메시지 데이터
    timestamp: datetime          # 타임스탬프
    client_id: Optional[str]    # 클라이언트 ID
    channel: Optional[str]      # 채널 정보
```

#### **2. 내장 메시지 핸들러**

```python
# Ping/Pong 메시지
async def _handle_ping(self, client_id: str, data: Dict[str, Any]):
    """Ping 메시지 처리"""
    if client_id in self.active_connections:
        self.active_connections[client_id].last_ping = datetime.now()
        
        await self.send_to_client(client_id, {
            "type": "pong",
            "timestamp": datetime.now().isoformat()
        })

# 채널 구독/해제
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
```

#### **3. 커스텀 메시지 핸들러 등록**

```python
# 메시지 핸들러 등록
def register_message_handler(self, message_type: str, handler: Callable):
    """메시지 핸들러 등록"""
    self.message_handlers[message_type] = handler
    Logger.info(f"메시지 핸들러 등록: {message_type}")

# 사용 예시
async def handle_chat_message(client_id: str, data: Dict[str, Any]):
    """채팅 메시지 처리"""
    message = data.get("message", "")
    channel = data.get("channel", "general")
    
    # 채팅 메시지를 채널의 모든 구독자에게 브로드캐스트
    await websocket_manager.broadcast_to_channel(channel, {
        "type": "chat_message",
        "client_id": client_id,
        "message": message,
        "channel": channel,
        "timestamp": datetime.now().isoformat()
    })

# 핸들러 등록
websocket_manager.register_message_handler("chat_message", handle_chat_message)
```

### **메시지 라우팅 및 브로드캐스트**

#### **1. 클라이언트별 메시지 전송**

```python
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
```

#### **2. 채널 기반 브로드캐스트**

```python
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
```

#### **3. 사용자별 메시지 전송**

```python
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
```

---

## 🔄 Redis Pub/Sub 연동 상세

### **다중 서버 환경 지원**

#### **1. Redis Pub/Sub 설정**

```python
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
            channel_name = channel.decode('utf-8').replace(
                f"{cls._config.redis_channel_prefix}:", ""
            )
            await cls.broadcast_to_channel(channel_name, message)
        
        # Redis 구독자 태스크 생성 및 시작
        async def redis_subscriber():
            pubsub = redis_client.pubsub()
            await pubsub.subscribe(f"{cls._config.redis_channel_prefix}:*")
            
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    await message_handler(
                        message['channel'], 
                        json.loads(message['data'])
                    )
        
        # 백그라운드에서 Redis 구독자 실행
        asyncio.create_task(redis_subscriber())
        
        Logger.info("Redis Pub/Sub WebSocket 연동 설정 완료")
        
    except Exception as e:
        Logger.error(f"Redis Pub/Sub 설정 실패: {e}")
```

#### **2. Redis 채널 메시지 발행**

```python
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
```

#### **3. 크로스 서버 메시지 전파**

```
서버 A (WebSocket) → Redis 채널 → 서버 B (WebSocket)
     ↓                    ↓              ↓
클라이언트 A        메시지 발행      클라이언트 B
     ↓                    ↓              ↓
메시지 전송         Redis Pub/Sub    메시지 수신
```

**동작 원리**:
- 서버 A에서 채널 메시지 브로드캐스트
- Redis 채널에 메시지 발행
- 서버 B에서 Redis 구독을 통해 메시지 수신
- 서버 B의 해당 채널 구독자에게 메시지 전송

---

## 🏥 헬스체크 및 모니터링

### **서비스 상태 확인**

```python
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
```

### **통계 정보 수집**

```python
def get_stats(self) -> Dict[str, Any]:
    """통계 정보 반환"""
    return {
        **self.stats,
        "channels": len(self.channel_subscribers),
        "users_with_connections": len(self.user_clients)
    }

# 상세 통계
stats = {
    "total_connections": 1250,      # 총 연결 수
    "active_connections": 856,      # 현재 활성 연결 수
    "messages_sent": 15420,         # 전송된 메시지 수
    "messages_received": 12340,     # 수신된 메시지 수
    "errors": 23,                   # 에러 수
    "channels": 15,                 # 활성 채널 수
    "users_with_connections": 234   # 연결된 사용자 수
}
```

### **클라이언트 및 채널 정보**

```python
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

def get_channel_info(self, channel: str) -> Dict[str, Any]:
    """채널 정보 조회"""
    subscriber_count = len(self.channel_subscribers.get(channel, []))
    return {
        "channel": channel,
        "subscriber_count": subscriber_count,
        "subscribers": self.channel_subscribers.get(channel, [])
    }
```

---

## 🎯 코드 철학

### **1. 정적 클래스 기반 서비스**
- **전역 접근성**: 어디서든 WebSocketService를 통해 서비스 접근
- **상태 관리**: 서비스 초기화 상태 및 클라이언트 매니저 관리
- **백그라운드 태스크**: heartbeat 및 cleanup 루프를 통한 자동 관리
- **안전한 종료**: 서비스 종료 시 모든 연결 정리 및 리소스 해제

### **2. 비동기 처리 및 성능**
- **asyncio 기반**: 비동기 WebSocket 연결 및 메시지 처리
- **연결 풀 관리**: 최대 연결 수 제한 및 자동 정리
- **메시지 버퍼링**: 클라이언트별 메시지 큐 및 브로드캐스트 버퍼
- **효율적인 라우팅**: 채널 기반 메시지 라우팅으로 불필요한 전송 방지

### **3. 확장 가능한 아키텍처**
- **플러그인 방식**: 메시지 타입별 커스텀 핸들러 등록
- **Redis 연동**: 다중 서버 환경에서의 메시지 동기화
- **설정 기반**: 환경별 설정을 통한 유연한 동작
- **모듈화**: 클라이언트 관리, 메시지 처리, 설정 관리의 명확한 분리

### **4. 안정성 및 모니터링**
- **연결 상태 추적**: 각 클라이언트의 연결 상태 및 품질 모니터링
- **자동 복구**: 비활성 연결 자동 감지 및 정리
- **상세한 로깅**: 연결, 메시지, 에러에 대한 구조화된 로깅
- **헬스체크**: 서비스 상태 및 통계 정보 제공

---

## 🚀 개선할 점

### **1. 성능 최적화**
- [ ] **메시지 압축**: 대용량 메시지 압축을 통한 대역폭 절약
- [ ] **연결 풀링**: WebSocket 연결 재사용 및 풀링
- [ ] **메시지 배치**: 여러 메시지를 묶어서 전송하는 배치 처리
- [ ] **비동기 큐**: Redis 기반 비동기 메시지 큐 시스템

### **2. 기능 확장**
- [ ] **메시지 우선순위**: 중요도에 따른 메시지 전송 우선순위**
- [ ] **메시지 지속성**: Redis를 통한 메시지 영속성 및 재전송
- [ ] **그룹 메시징**: 사용자 그룹 기반 메시지 전송
- [ ] **파일 전송**: WebSocket을 통한 파일 업로드/다운로드

### **3. 보안 강화**
- [ ] **메시지 암호화**: WebSocket 메시지 암호화 및 보안
- [ ] **Rate Limiting**: 클라이언트별 메시지 전송 속도 제한
- [ ] **입력 검증**: 메시지 내용의 유효성 검증 강화
- [ ] **접근 제어**: 채널별 접근 권한 및 역할 기반 제어

### **4. 모니터링 및 관측성**
- [ ] **Prometheus 메트릭**: 표준 메트릭 형식으로 내보내기
- [ ] **분산 추적**: OpenTelemetry를 통한 메시지 흐름 추적
- [ ] **실시간 대시보드**: WebSocket 연결 및 메시지 실시간 모니터링
- [ ] **알림 시스템**: 연결 수 급증, 에러율 증가 시 자동 알림

### **5. 테스트 및 품질**
- [ ] **단위 테스트**: 각 컴포넌트별 단위 테스트 작성
- [ ] **통합 테스트**: 전체 WebSocket 서비스 통합 테스트
- [ ] **부하 테스트**: 대량 연결 및 메시지 처리 성능 테스트
- [ ] **보안 테스트**: WebSocket 보안 취약점 검사

---

## 🛠️ 개발 환경 설정

### **환경 변수**
```bash
# .env
WEBSOCKET_MAX_CONNECTIONS=1000
WEBSOCKET_MAX_MESSAGE_SIZE=1048576
WEBSOCKET_PING_INTERVAL=20
WEBSOCKET_HEARTBEAT_INTERVAL=30
WEBSOCKET_CONNECTION_TIMEOUT=60
WEBSOCKET_REQUIRE_AUTH=true
WEBSOCKET_USE_REDIS_PUBSUB=true
WEBSOCKET_REDIS_CHANNEL_PREFIX=ai_trading
```

### **의존성 설치**
```bash
# requirements.txt 기반 설치
pip install -r requirements.txt

# 또는 개별 설치
pip install fastapi websockets redis asyncio
```

### **FastAPI 앱 설정 예시**
```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from service.websocket.websocket_config import WebSocketConfig
from service.websocket.websocket_service import WebSocketService

# FastAPI 앱 생성
app = FastAPI(title="AI Trading Platform API")

# WebSocket 설정
websocket_config = WebSocketConfig(
    max_connections=1000,
    max_message_size=1024*1024,
    ping_interval=20,
    heartbeat_interval=30,
    connection_timeout=60,
    require_auth=True,
    use_redis_pubsub=True,
    redis_channel_prefix="ai_trading"
)

# WebSocket 서비스 초기화
WebSocketService.init(websocket_config)

# 백그라운드 태스크 시작
@app.on_event("startup")
async def startup_event():
    await WebSocketService.start_background_tasks()

# 백그라운드 태스크 중지
@app.on_event("shutdown")
async def shutdown_event():
    await WebSocketService.shutdown()

# WebSocket 엔드포인트
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await WebSocketService.connect_client(websocket, client_id=client_id)
    
    try:
        while True:
            # 메시지 수신
            message = await websocket.receive_text()
            await WebSocketService.handle_client_message(client_id, message)
            
    except WebSocketDisconnect:
        await WebSocketService.disconnect_client(client_id, "client_disconnect")
```

---

## 🧪 WebSocket 테스트 가이드

### **Postman WebSocket 테스트**

#### **1. Postman WebSocket 탭 활용법**

1. **새 WebSocket 요청 생성**
   - Postman에서 "New" → "WebSocket Request" 선택
   - URL 입력: `ws://localhost:8000/ws/{client_id}`
   - 예시: `ws://localhost:8000/ws/test_client_001`

2. **연결 및 메시지 전송**
   - "Connect" 버튼 클릭하여 WebSocket 연결
   - "Message" 탭에서 메시지 입력 및 전송
   - "Send" 버튼으로 메시지 전송

3. **메시지 타입별 테스트**

```json
// Ping 메시지
{
  "type": "ping",
  "timestamp": "2025-01-20T10:30:00Z"
}

// 채널 구독
{
  "type": "subscribe",
  "channel": "stock_updates"
}

// 채팅 메시지
{
  "type": "chat_message",
  "message": "테슬라 주식 분석 요청",
  "channel": "general"
}

// 채널 구독 해제
{
  "type": "unsubscribe",
  "channel": "stock_updates"
}
```

#### **2. Postman 환경 변수 설정**

```json
// Postman Environment Variables
{
  "websocket_url": "ws://localhost:8000",
  "client_id": "test_client_001",
  "user_id": "test_user_001",
  "test_channel": "test_channel"
}
```

### **명령행 도구를 이용한 테스트**

#### **1. wscat (Node.js 기반)**

```bash
# wscat 설치
npm install -g wscat

# WebSocket 연결
wscat -c ws://localhost:8000/ws/test_client_001

# 메시지 전송
{"type": "ping", "timestamp": "2025-01-20T10:30:00Z"}
{"type": "subscribe", "channel": "stock_updates"}
{"type": "chat_message", "message": "Hello WebSocket!", "channel": "general"}
```

#### **2. websocat (Rust 기반)**

```bash
# websocat 설치 (macOS)
brew install websocat

# WebSocket 연결
websocat ws://localhost:8000/ws/test_client_001

# 메시지 전송 (JSON 형식)
{"type": "ping", "timestamp": "2025-01-20T10:30:00Z"}
```

#### **3. Python 테스트 스크립트**

```python
# test_websocket.py
import asyncio
import websockets
import json
import uuid

async def test_websocket():
    uri = "ws://localhost:8000/ws/test_client_001"
    
    async with websockets.connect(uri) as websocket:
        print("WebSocket 연결됨")
        
        # Ping 메시지 전송
        ping_message = {
            "type": "ping",
            "timestamp": "2025-01-20T10:30:00Z"
        }
        await websocket.send(json.dumps(ping_message))
        print(f"전송: {ping_message}")
        
        # 응답 수신
        response = await websocket.recv()
        print(f"수신: {response}")
        
        # 채널 구독
        subscribe_message = {
            "type": "subscribe",
            "channel": "test_channel"
        }
        await websocket.send(json.dumps(subscribe_message))
        print(f"전송: {subscribe_message}")
        
        # 구독 결과 수신
        response = await websocket.recv()
        print(f"수신: {response}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
```

### **테스트 시나리오**

#### **1. 기본 연결 테스트**
- [ ] WebSocket 연결 성공/실패 확인
- [ ] 연결 후 자동 연결 확인 메시지 수신
- [ ] 연결 해제 시 정상 처리 확인

#### **2. 메시지 처리 테스트**
- [ ] Ping/Pong 메시지 정상 처리
- [ ] 채널 구독/해제 정상 처리
- [ ] 커스텀 메시지 타입 처리
- [ ] 잘못된 JSON 형식 에러 처리

#### **3. 채널 브로드캐스트 테스트**
- [ ] 채널 구독 후 메시지 수신
- [ ] 채널 구독 해제 후 메시지 미수신
- [ ] 다중 클라이언트 동시 구독 테스트

#### **4. Redis Pub/Sub 테스트 (다중 서버)**
- [ ] 서버 A에서 메시지 발행
- [ ] 서버 B의 클라이언트가 메시지 수신
- [ ] Redis 연결 실패 시 폴백 동작 확인

#### **5. 성능 및 부하 테스트**
- [ ] 최대 연결 수 제한 확인
- [ ] 대량 메시지 처리 성능
- [ ] 연결 타임아웃 및 자동 정리 동작

### **디버깅 팁**

#### **1. 로그 확인**
```bash
# WebSocket 서비스 로그 확인
tail -f logs/websocket_service.log

# Redis 연결 상태 확인
redis-cli ping
redis-cli pubsub channels
```

#### **2. 네트워크 상태 확인**
```bash
# WebSocket 포트 연결 상태
netstat -an | grep :8000

# WebSocket 연결 수 확인
curl http://localhost:8000/healthz/detailed
```

#### **3. 메시지 흐름 추적**
- 클라이언트 ID와 메시지 타입을 로그에 포함
- Redis Pub/Sub 채널별 메시지 전파 확인
- 연결 상태 변화 추적

---

## 📚 추가 리소스

- **FastAPI WebSocket 문서**: https://fastapi.tiangolo.com/advanced/websockets/
- **WebSocket 프로토콜**: https://tools.ietf.org/html/rfc6455
- **Redis Pub/Sub 문서**: https://redis.io/topics/pubsub
- **asyncio 문서**: https://docs.python.org/3/library/asyncio.html
- **WebSocket 클라이언트 테스트**: https://websocket.org/echo.html
- **Postman WebSocket 가이드**: https://learning.postman.com/docs/sending-requests/websocket/
- **wscat 문서**: https://github.com/websockets/wscat
- **websocat 문서**: https://github.com/vi/websocat

---

> **문서 버전**: v1.0 (LLM 서비스 README 구조 기반으로 작성)
> **최종 업데이트**: 2025년 1월  
> **담당자**: WebSocket Service Development Team
