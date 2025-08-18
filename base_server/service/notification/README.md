# 📁 Notification Service

## 📌 개요
Notification 서비스는 정적 클래스 패턴을 사용하는 간소화된 알림 서비스로, 시그널 알림에 필요한 핵심 기능을 제공합니다. WebSocket 실시간 알림, 인앱 알림함 저장, 중복 방지, Rate Limiting 등의 기능을 지원하며, 멀티채널(WebSocket, 이메일, SMS, 인앱) 알림 발송을 관리합니다.

## 🏗️ 구조
```
base_server/service/notification/
├── __init__.py                    # 모듈 초기화
├── notification_service.py         # 메인 알림 서비스 (정적 클래스)
└── notification_config.py          # 알림 설정 및 타입 정의
```

## 🔧 핵심 기능

### NotificationService (정적 클래스)
- **정적 클래스**: 정적 클래스 패턴으로 서비스 인스턴스 관리
- **초기화 관리**: `init()`, `shutdown()`, `is_initialized()` 메서드
- **멀티채널 지원**: WebSocket, 이메일, SMS, 인앱 알림 채널
- **알림 관리**: 알림 발송, 중복 방지, Rate Limiting, 큐 처리

### 주요 기능 그룹

#### 1. 알림 발송 (Notification Sending)
```python
# 시그널 알림 발송
success = await NotificationService.send_notification(
    user_id="12345",
    shard_id=1,
    notification_type=NotificationType.PREDICTION_ALERT,
    title="매수 신호",
    message="AAPL 주식 매수 신호가 발생했습니다",
    data={"symbol": "AAPL", "signal": "BUY", "confidence": 0.85},
    priority=1
)
```

#### 2. 멀티채널 지원 (Multi-Channel Support)
```python
# 멀티채널 알림 발송 (내부적으로 채널별 핸들러 호출)
success = await NotificationService.send_notification(
    user_id="12345",
    shard_id=1,
    notification_type=NotificationType.PREDICTION_ALERT,
    title="알림 제목",
    message="알림 내용",
    data={"key": "value"},
    priority=1
)

# 내부적으로 다음 채널들이 처리됨:
# - WebSocket: 실시간 알림
# - 인앱: DB 저장
# - 이메일: 이메일 발송
# - SMS: SMS 발송
```

#### 3. 중복 방지 및 Rate Limiting
```python
# 중복 방지 및 Rate Limiting은 send_notification() 내부에서 자동으로 처리됨
# 사용자가 직접 호출할 필요 없음

success = await NotificationService.send_notification(
    user_id="12345",
    shard_id=1,
    notification_type=NotificationType.PREDICTION_ALERT,
    title="알림 제목",
    message="알림 내용",
    data={"key": "value"},
    priority=1
)

# 내부적으로 다음이 처리됨:
# - 중복 알림 체크 (24시간 윈도우)
# - Rate Limit 체크 (사용자당 시간당 제한)
```

#### 4. 큐 기반 처리 (Queue-Based Processing)
```python
# 큐 처리는 send_notification() 내부에서 자동으로 처리됨
# 사용자가 직접 호출할 필요 없음

success = await NotificationService.send_notification(
    user_id="12345",
    shard_id=1,
    notification_type=NotificationType.PREDICTION_ALERT,
    title="알림 제목",
    message="알림 내용",
    data={"key": "value"},
    priority=1
)

# 내부적으로 다음이 처리됨:
# - 알림을 큐에 추가
# - 큐 컨슈머를 통한 비동기 처리
```

#### 5. 모니터링 및 통계
```python
# 서비스 통계 조회
stats = await NotificationService.get_stats()
```

## 🔄 Template-Service 연동

### 사용하는 Service
- **`service.core.logger.Logger`**: 로깅 서비스
- **`service.websocket.websocket_service.WebSocketService`**: WebSocket 실시간 알림
- **`service.queue.queue_service.QueueService`**: 메시지 큐 처리
- **`service.queue.event_queue.EventType`**: 이벤트 타입 정의
- **`service.cache.cache_service.CacheService`**: 중복 방지 및 Rate Limiting
- **`service.service_container.ServiceContainer`**: 서비스 컨테이너
- **`service.email.email_service.EmailService`**: 이메일 발송
- **`service.sms.sms_service.SmsService`**: SMS 발송

### 연동 방식
1. **초기화**: `NotificationService.init(config)` 호출로 서비스 초기화
2. **채널 핸들러 등록**: WebSocket, 이메일, SMS, 인앱 채널 핸들러 등록
3. **큐 컨슈머 등록**: 알림 발송을 위한 메시지 큐 컨슈머 등록
4. **알림 발송**: `send_notification()` 호출로 멀티채널 알림 발송
5. **정리**: `shutdown()` 호출로 리소스 해제

## 📊 데이터 흐름

### 알림 발송 프로세스
```
사용자 요청 → send_notification() → 중복 체크 → Rate Limit 체크
                                    ↓
                            큐 서비스 상태 확인
                                    ↓
                    ├── 큐 활성화: 큐에 알림 추가 → 이벤트 발행 → 컨슈머 처리
                    └── 큐 비활성화: 직접 채널별 핸들러 호출
                                    ↓
                    ├── WebSocket: 실시간 알림
                    ├── 인앱: DB 저장
                    ├── 이메일: 이메일 발송
                    └── SMS: SMS 발송
```

### 중복 방지 및 Rate Limiting
```
알림 생성 → 중복 체크 (CacheService) → Rate Limit 체크 (CacheService)
                ↓                              ↓
            중복이면 스킵              제한 초과면 스킵
                ↓                              ↓
            중복 키 저장 (TTL)        카운터 증가 (TTL)
```

### 큐 처리 프로세스
```
서비스 초기화 → 큐 컨슈머 등록 (init 시점)
                    ↓
알림 큐 → 메시지 수신 → 채널별 핸들러 호출
                    ↓
            결과 이벤트 발행 (성공/실패)
```

## 🚀 사용 예제

### 기본 초기화
```python
from service.notification.notification_service import NotificationService
from service.notification.notification_config import NotificationConfig

# 알림 설정 생성 (기본값 사용)
config = NotificationConfig(
    dedup_window_hours=24,
    rate_limit_per_user_per_hour=100
)

# 또는 특정 채널만 활성화하고 싶다면
config = NotificationConfig(
    enabled_channels={
        "websocket": True,
        "in_app": True,
        "push": False,
        "email": False,
        "sms": False
    },
    dedup_window_hours=24,
    rate_limit_per_user_per_hour=100
)

# 서비스 초기화
success = await NotificationService.init(config)
```

### 시그널 알림 발송
```python
# 매수 신호 알림
success = await NotificationService.send_notification(
    user_id="12345",
    shard_id=1,
    notification_type=NotificationType.PREDICTION_ALERT,
    title="매수 신호 발생",
    message="AAPL 주식에 대한 강력한 매수 신호가 발생했습니다",
    data={
        "symbol": "AAPL",
        "stock_name": "Apple Inc.",
        "signal": "BUY",
        "target_price": 150.00,
        "current_price": 145.50,
        "confidence": 0.92
    },
    priority=1  # 긴급
)
```

### 포트폴리오 알림
```python
# 리밸런싱 제안 알림
success = await NotificationService.send_notification(
    user_id="12345",
    shard_id=1,
    notification_type=NotificationType.PORTFOLIO_REBALANCE,
    title="포트폴리오 리밸런싱 제안",
    message="현재 포트폴리오 비율이 최적화되어 있습니다",
    data={
        "current_allocation": {"stocks": 0.6, "bonds": 0.4},
        "recommended_allocation": {"stocks": 0.7, "bonds": 0.3},
        "expected_return": 0.08
    },
    priority=3  # 보통
)
```

### 시스템 알림
```python
# 시스템 점검 알림
success = await NotificationService.send_notification(
    user_id="12345",
    shard_id=1,
    notification_type=NotificationType.SYSTEM_MAINTENANCE,
    title="시스템 점검 예정",
    message="오늘 밤 2시부터 4시까지 시스템 점검이 예정되어 있습니다",
    data={
        "maintenance_start": "2024-01-15T02:00:00Z",
        "maintenance_end": "2024-01-15T04:00:00Z",
        "affected_services": ["trading", "notifications"]
    },
    priority=2  # 중요
)
```

## ⚙️ 설정

### NotificationConfig 주요 설정
```python
class NotificationConfig(BaseModel):
    # 채널별 활성화 여부 (None이면 model_post_init에서 자동으로 기본값 설정)
    enabled_channels: Optional[Dict[str, bool]] = None
    
    # 배치 설정
    batch_size: int = 100
    batch_timeout_seconds: float = 5.0
    
    # 중복 방지 설정
    dedup_window_hours: int = 24
    
    # 우선순위 설정 (None이면 model_post_init에서 자동으로 기본값 설정)
    priority_channels: Optional[Dict[str, int]] = None
    
    # Rate Limiting 설정
    rate_limit_per_user_per_hour: int = 100
```

### 기본 채널 설정
```python
# NotificationConfig에서 자동으로 설정되는 기본값
enabled_channels = {
    "websocket": True,    # WebSocket 실시간 알림
    "in_app": True,       # 인앱 알림함
    "push": False,        # 모바일 푸시 (비활성화)
    "email": False,       # 이메일 (비활성화)
    "sms": False          # SMS (비활성화)
}

priority_channels = {
    "websocket": 1,       # 최고 우선순위
    "push": 2,            # 높은 우선순위
    "in_app": 3,          # 보통 우선순위
    "email": 4,           # 낮은 우선순위
    "sms": 5              # 최저 우선순위
}
```

### 알림 타입
```python
class NotificationType(Enum):
    # 예측 관련
    PREDICTION_ALERT = "prediction_alert"           # 매수/매도 신호
    PRICE_TARGET_REACHED = "price_target_reached"   # 목표가 도달
    STOP_LOSS_TRIGGERED = "stop_loss_triggered"     # 손절 알림
    
    # 포트폴리오 관련
    PORTFOLIO_REBALANCE = "portfolio_rebalance"     # 리밸런싱 제안
    TRADE_EXECUTED = "trade_executed"               # 거래 체결
    DAILY_SUMMARY = "daily_summary"                 # 일일 요약
    
    # 시스템 관련
    SYSTEM_MAINTENANCE = "system_maintenance"       # 시스템 점검
    FEATURE_UPDATE = "feature_update"               # 기능 업데이트
    ACCOUNT_SECURITY = "account_security"           # 계정 보안
```

## 🔗 연관 폴더

### 의존성 관계
- **`service.core.logger`**: 로깅 서비스
- **`service.websocket`**: WebSocket 실시간 알림
- **`service.queue`**: 메시지 큐 및 이벤트 처리
- **`service.cache`**: 중복 방지 및 Rate Limiting
- **`service.service_container`**: 서비스 컨테이너
- **`service.email`**: 이메일 발송 서비스
- **`service.sms`**: SMS 발송 서비스
- **`application.base_web_server.main`**: 메인 서버에서 알림 서비스 초기화 및 종료

### 사용하는 Template
- **`template.notification`**: 알림 템플릿 구현 및 API 엔드포인트
- **`template.base`**: AppConfig에 NotificationConfig 포함

### 외부 시스템
- **데이터베이스**: 인앱 알림함 저장 (샤드 DB)
- **캐시 서비스**: 중복 방지 및 Rate Limiting (CacheService)
- **메시지 큐**: 알림 발송 비동기 처리
- **WebSocket**: 실시간 알림 전송
- **이메일 서비스**: 이메일 알림 발송
- **SMS 서비스**: SMS 알림 발송
