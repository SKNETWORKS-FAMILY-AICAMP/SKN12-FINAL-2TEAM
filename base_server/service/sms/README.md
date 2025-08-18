# 📁 SMS Service

## 📌 개요
SMS 서비스는 AWS SNS(Simple Notification Service)를 사용하여 SMS를 발송하는 정적 클래스 패턴의 서비스입니다. 주식 긴급 알림, 매매 신호, 시스템 공지 등 중요한 알림을 SMS로 발송하며, 비용 관리와 발송 제한을 통해 효율적인 SMS 서비스를 제공합니다.

## 🏗️ 구조
```
base_server/service/sms/
├── __init__.py                    # 모듈 초기화
├── sms_service.py                 # 메인 SMS 서비스 (정적 클래스)
├── sms_config.py                  # SMS 설정 및 AWS SNS 설정
└── sms_client.py                  # AWS SNS 클라이언트 구현
```

## 🔧 핵심 기능

### SmsService (정적 클래스)
- **정적 클래스**: 정적 클래스 패턴으로 서비스 인스턴스 관리
- **초기화 관리**: `init()`, `shutdown()`, `is_initialized()` 메서드
- **지연 생성**: AWS 연결은 실제 사용 시점에 생성 (Lazy Loading)
- **비용 관리**: 일일/월간 발송 제한으로 SMS 비용 통제
- **발송 제한**: `_check_send_limits()` 메서드로 발송 가능 여부 확인

### 주요 기능 그룹

#### 1. 기본 SMS 발송
```python
# 기본 SMS 발송
result = await SmsService.send_sms(
    phone_number="+82-10-1234-5678",
    message="[AI매매] 테슬라 매수 신호 발생",
    message_type="prediction_alert"
)
```

#### 2. 대량 SMS 발송
```python
# 대량 SMS 발송
users = [
    {"phone": "+82-10-1111-1111", "name": "박진양", "stock": "mcdonalds"},
    {"phone": "+82-10-2222-2222", "name": "이석원", "stock": "fox"}
]

result = await SmsService.send_bulk_sms(
    recipients=users,
    message_template="{name}님, {stock} 매수 신호입니다",
    message_type="prediction_alert"
)
```

#### 3. 편의 메서드
```python
# 긴급 주식 알림 SMS
result = await SmsService.send_urgent_alert(
    phone_number="+82-10-1234-5678",
    stock_symbol="AAPL",
    alert_type="급등",
    price_info="$155.50 (+5.2%)",
    additional_info="목표가 도달"
)

# 시스템 알림 SMS
result = await SmsService.send_system_alert(
    phone_numbers=["+82-10-1234-5678", "+82-10-5678-1234"],
    alert_message="시스템 점검 완료, 정상 서비스 재개",
    alert_priority="medium"
)

# 매매 신호 SMS
result = await SmsService.send_trading_signal(
    user_phone="+82-10-1234-5678",
    user_name="이석원",
    stock_symbol="AAPL",
    signal_type="BUY",
    target_price="$150.00",
    confidence="85%"
)
```

#### 4. 유틸리티 기능
```python
# 발송 통계 조회
stats = await SmsService.get_send_statistics()

# AWS SMS 설정 확인
aws_settings = await SmsService.check_aws_sms_settings()

# 일일/월간 카운터 리셋
SmsService.reset_daily_counter()
SmsService.reset_monthly_counter()
```

## 🔄 Template-Service 연동

### 사용하는 Service
- **`service.core.logger.Logger`**: 로깅 서비스

### 연동 방식
1. **초기화**: `SmsService.init(config)` 직접 호출로 서비스 초기화
2. **설정 저장**: AWS 인증 정보 및 SMS 발송 제한 설정 저장
3. **지연 연결**: 실제 SMS 발송 시점에 AWS SNS 연결 생성
4. **SMS 발송**: 다양한 발송 메서드를 통한 SMS 전송
5. **정리**: `shutdown()` 호출로 AWS 연결 종료

## 📊 데이터 흐름

### SMS 발송 프로세스
```
사용자 요청 → SmsService.send_*_sms() → _check_send_limits() → 발송 제한 확인
                                     ↓
                             제한 통과 시 → _get_client() → SNSClient 생성
                                     ↓
                             AWS SNS 연결 확인
                                     ↓
                             SNSClient.send_sms() → AWS SNS API 호출
                                     ↓
                             응답 처리 → 발송 카운트 증가 → 결과 반환
```

### 발송 제한 확인 과정
```
발송 요청 → _check_send_limits() → 일일 제한 확인
                              ↓
                        월간 제한 확인
                              ↓
                        잔여 발송량 계산
                              ↓
                        발송 허용/거부 결정
```

### 지연 생성 (Lazy Loading) 패턴
```
서비스 초기화 → 설정만 저장 (AWS 연결 없음)
                     ↓
첫 SMS 발송 요청 → SNSClient 생성 → AWS SNS 연결
                     ↓
이후 요청 → 기존 연결 재사용
                     ↓
연결 끊어짐 → 새 클라이언트 생성
```

## 🚀 사용 예제

### 기본 초기화
```python
from service.sms.sms_service import SmsService
from service.sms.sms_config import SmsConfig

# SMS 설정 생성
config = SmsConfig(
    aws_access_key_id="your_access_key",
    aws_secret_access_key="your_secret_key",
    region_name="ap-northeast-2",
    default_sender_id="AITrade",
    daily_send_limit=100,
    monthly_send_limit=1000
)

# 서비스 초기화
success = SmsService.init(config)
```

### 긴급 주식 알림
```python
# 긴급 알림 SMS 발송
result = await SmsService.send_urgent_alert(
    phone_number="+82-10-1234-5678",
    stock_symbol="삼성전자",
    alert_type="급락",
    price_info="50,000원 (-5%)",
    additional_info="손절선 도달"
)

if result["success"]:
    print(f"SMS 발송 성공: {result['message_id']}")
    print(f"일일 잔여: {result['daily_remaining']}건")
else:
    print(f"SMS 발송 실패: {result['error']}")
```

### 대량 발송
```python
# 100명에게 일일 리포트 발송
users = [
    {"phone": "+82-10-1111-1111", "name": "홍길동", "portfolio_value": "1,000,000"},
    {"phone": "+82-10-2222-2222", "name": "김영희", "portfolio_value": "2,000,000"}
]

result = await SmsService.send_bulk_sms(
    recipients=users,
    message_template="{name}님, 오늘 포트폴리오 수익률: {portfolio_value}원",
    message_type="daily_summary",
    max_recipients=50  # 비용 제한
)
```

### 매매 신호 발송
```python
# AI 매매 신호 SMS
result = await SmsService.send_trading_signal(
    user_phone="+82-10-1234-5678",
    user_name="홍길동",
    stock_symbol="AAPL",
    signal_type="BUY",
    target_price="$150.00",
    confidence="85%"
)
```

## ⚙️ 설정

### SmsConfig 주요 설정
```python
class SmsConfig(BaseModel):
    # AWS 인증 설정
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    region_name: str = "ap-northeast-2"
    aws_session_token: Optional[str] = None
    
    # SNS 기본 설정
    default_sender_id: str = "FinanceApp"
    default_message_type: str = "Transactional"
    
    # SMS 발송 설정
    default_country_code: str = "+82"
    max_message_length: int = 160
    enable_delivery_receipt: bool = True
    
    # 발송 제한 설정 (비용 절약)
    daily_send_limit: int = 100
    monthly_send_limit: int = 1000
    
    # 비용 관리 설정
    cost_management: Dict[str, Any] = {
        "enable_cost_limit": True,
        "monthly_budget_usd": 50.0,
        "cost_per_sms_usd": 0.05,
        "alert_threshold": 0.8
    }
```

### 실제 설정 파일 예시
```json
{
  "smsConfig": {
    "aws_access_key_id": "your_access_key",
    "aws_secret_access_key": "your_secret_key",
    "region_name": "ap-northeast-1",
    "default_sender_id": "AITrade",
    "default_message_type": "Transactional",
    "default_country_code": "+82",
    "daily_send_limit": 100,
    "monthly_send_limit": 1000,
    "monthly_budget_usd": 10.0,
    "cost_per_sms_usd": 0.05
  }
}
```

## 🔗 연관 폴더

### 의존성 관계
- **`service.core.logger`**: 로깅 서비스
- **`application.base_web_server.main`**: 메인 서버에서 SMS 서비스 초기화 및 종료

### 사용하는 Template
- **`template.base`**: AppConfig에 SmsConfig 포함

### 사용하는 Service
- **`service.notification`**: NotificationService에서 SMS 발송 (NotificationService._send_sms에서 SmsService 직접 사용)

### 외부 시스템
- **AWS SNS**: SMS 발송 서비스
- **AWS IAM**: 인증 및 권한 관리
