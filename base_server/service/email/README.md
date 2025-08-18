# 📁 Email Service

## 📌 개요
Email 서비스는 AWS SES(Simple Email Service)를 사용하여 이메일을 발송하는 정적 클래스 패턴의 서비스입니다. 주식 알림, 시스템 공지, 일일 리포트 등 다양한 유형의 이메일을 지원하며, 단일 발송, 템플릿 발송, 대량 발송 등의 기능을 제공합니다.

## 🏗️ 구조
```
base_server/service/email/
├── __init__.py                    # 모듈 초기화
├── email_service.py               # 메인 이메일 서비스 (정적 클래스)
├── email_config.py                # 이메일 설정 및 AWS SES 설정
└── email_client.py                # AWS SES 클라이언트 구현
```

## 🔧 핵심 기능

### EmailService (정적 클래스)
- **정적 클래스**: 정적 클래스 패턴으로 서비스 인스턴스 관리
- **초기화 관리**: `init()`, `shutdown()`, `is_initialized()` 메서드
- **지연 생성**: AWS 연결은 실제 사용 시점에 생성 (Lazy Loading)
- **에러 처리**: AWS 에러를 친화적인 메시지로 변환

### 주요 기능 그룹

#### 1. 기본 이메일 발송
```python
# 간단한 이메일 발송
result = await EmailService.send_simple_email(
    to_emails=["user@gmail.com"],
    subject="주식 알림",
    text_body="Apple Inc.가 목표가에 도달했습니다",
    html_body="<h1>매수 신호</h1><p>Apple Inc.가 목표가에 도달했습니다.</p>",
    from_name="AI Trading Platform"
)
```

#### 2. 템플릿 이메일 발송
```python
# 템플릿 기반 이메일 발송
result = await EmailService.send_templated_email(
    to_emails=["user@gmail.com"],
    template_name="prediction_alert",
    template_data={
        "user_name": "홍길동",
        "stock_name": "Apple Inc.",
        "prediction": "상승",
        "target_price": "150.00"
    }
)
```

#### 3. 대량 이메일 발송
```python
# 대량 템플릿 이메일 발송
users = [
    {"email": "user1@gmail.com", "data": {"name": "홍길동", "portfolio_value": "1,000,000"}},
    {"email": "user2@naver.com", "data": {"name": "김영희", "portfolio_value": "2,000,000"}}
]

result = await EmailService.send_bulk_emails(
    destinations=users,
    template_name="daily_report",
    default_data={"report_date": "2024-01-15"}  # 내부적으로 default_template_data로 변환됨
)
```

#### 4. 편의 메서드
```python
# 주식 예측 알림 이메일
result = await EmailService.send_prediction_alert(
    user_email="user@gmail.com",
    user_name="홍길동",
    stock_symbol="AAPL",
    stock_name="Apple Inc.",
    prediction_type="BUY",
    target_price="150.00",
    current_price="145.50",
    confidence="85%"
)

# 실제로는 다음과 같은 내용의 이메일이 자동 생성됩니다:
# - 제목: "[매매 신호] Apple Inc.(AAPL) 매수 신호"
# - 본문: AI 분석 결과, 종목 정보, 목표가, 현재가, 신뢰도 등이 포함된 구조화된 이메일

# 시스템 공지 이메일 (편의 메서드)
result = await EmailService.send_system_notice(
    user_emails=["user1@gmail.com", "user2@naver.com"],
    notice_title="시스템 점검 예정",
    notice_content="오늘 밤 2시부터 4시까지 시스템 점검이 예정되어 있습니다."
)

# 실제로는 다음과 같은 내용의 이메일이 자동 생성됩니다:
# - 제목: "[시스템 공지] 시스템 점검 예정"
# - 본문: HTML 형식으로 포맷팅된 공지 내용
```

#### 5. 유틸리티 기능
```python
# 이메일 주소 검증
result = await EmailService.verify_email_address("your-email@company.com")
```

## 🔄 Template-Service 연동

### 사용하는 Service
- **`service.core.logger.Logger`**: 로깅 서비스
- **`service.service_container.ServiceContainer`**: 서비스 컨테이너

### 연동 방식
1. **초기화**: `EmailService.init(config)` 호출로 서비스 초기화
2. **설정 저장**: AWS 인증 정보 및 이메일 설정 저장
3. **지연 연결**: 실제 이메일 발송 시점에 AWS SES 연결 생성
4. **이메일 발송**: 다양한 발송 메서드를 통한 이메일 전송
5. **정리**: `shutdown()` 호출로 AWS 연결 종료

## 📊 데이터 흐름

### 이메일 발송 프로세스
```
사용자 요청 → EmailService.send_*_email() → _get_client() → SESClient 생성
                                    ↓
                            AWS SES 연결 확인
                                    ↓
                            SESClient.send_email() → AWS SES API 호출
                                    ↓
                            응답 처리 → 결과 반환
```

**파라미터 변환 과정:**
- `to_emails` → `to_addresses`
- `text_body` → `body_text`  
- `html_body` → `body_html`
- `from_email`, `from_name` → `source` (AWS SES 형식)

### 지연 생성 (Lazy Loading) 패턴
```
서비스 초기화 → 설정만 저장 (AWS 연결 없음)
                    ↓
첫 이메일 발송 요청 → SESClient 생성 → AWS SES 연결
                    ↓
이후 요청 → 기존 연결 재사용
                    ↓
연결 끊어짐 → 새 클라이언트 생성
```

## 🚀 사용 예제

### 기본 초기화
```python
from service.email.email_service import EmailService
from service.email.email_config import EmailConfig

# 이메일 설정 생성
config = EmailConfig(
    aws_access_key_id="your_access_key",
    aws_secret_access_key="your_secret_key",
    region_name="ap-northeast-2",
    default_from_email="noreply@mail.bullant-kr.com",
    default_from_name="BullAnt Trading Platform Korea"
)

# 서비스 초기화
success = EmailService.init(config)
```

### 주식 알림 이메일
```python
# 매수 신호 알림
result = await EmailService.send_simple_email(
    to_emails=["user@gmail.com"],
    subject="[매매 신호] Apple Inc. 매수 신호 발생",
    text_body="Apple Inc.(AAPL)가 목표가 $150.00에 도달했습니다.",
    html_body="<h1>매수 신호</h1><p>Apple Inc.가 목표가에 도달했습니다.</p>",
    from_name="AI Trading Platform"
)

if result["success"]:
    print(f"이메일 발송 성공: {result['message_id']}")
else:
    print(f"이메일 발송 실패: {result['error']}")
```

### 템플릿 이메일
```python
# 예측 알림 템플릿 이메일
result = await EmailService.send_templated_email(
    to_emails=["user@gmail.com"],
    template_name="prediction_alert",
    template_data={
        "user_name": "홍길동",
        "stock_name": "Apple Inc.",
        "prediction": "상승",
        "target_price": "150.00"
    }
)
```

### 대량 발송
```python
# 1000명에게 일일 리포트 발송
users = [
    {"email": "user1@gmail.com", "data": {"name": "홍길동", "portfolio_value": "1,000,000"}},
    {"email": "user2@naver.com", "data": {"name": "김영희", "portfolio_value": "2,000,000"}}
]

result = await EmailService.send_bulk_emails(
    destinations=users,
    template_name="daily_report",
    default_data={"report_date": "2024-01-15"}  # 내부적으로 default_template_data로 변환됨
)
```

## ⚙️ 설정

### EmailConfig 주요 설정
```python
class EmailConfig(BaseModel):
    # AWS 인증 설정
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    region_name: str = "ap-northeast-2"
    aws_session_token: Optional[str] = None
    
    # SES 기본 설정
    default_from_email: str = "noreply@mail.bullant-kr.com"
    default_from_name: str = "BullAnt Trading Platform Korea"
    
    # 이메일 템플릿 설정
    template_bucket: Optional[str] = None
    template_prefix: str = "email-templates/"
    default_charset: str = "UTF-8"
    
    # 성능 설정
    send_timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # 배치 발송 설정
    batch_size: int = 50
    max_send_rate: int = 14
    
    # 검증 설정
    verify_email_addresses: bool = True
    configuration_set: Optional[str] = None
    
    # 모니터링 설정
    enable_tracking: bool = True
    enable_bounce_handling: bool = True
    enable_complaint_handling: bool = True
```

### 기본 템플릿 데이터
```python
# 기본 템플릿 데이터
default_template_data = {
    "company_name": "BullAnt Korea",
    "support_email": "support@mail.bullant-kr.com",
    "unsubscribe_url": "https://www.bullant-kr.com/unsubscribe"
}

# 이메일 타입별 설정
email_types = {
    "prediction_alert": {
        "template_name": "prediction_alert",
        "subject_prefix": "[매매 신호]",
        "priority": "high"
    },
    "price_target": {
        "template_name": "price_target",
        "subject_prefix": "[목표가 달성]",
        "priority": "high"
    },
    "daily_summary": {
        "template_name": "daily_summary",
        "subject_prefix": "[일일 리포트]",
        "priority": "normal"
    },
    "system_notice": {
        "template_name": "system_notice",
        "subject_prefix": "[시스템 공지]",
        "priority": "normal"
    }
}
```

## 🔗 연관 폴더

### 의존성 관계
- **`service.core.logger`**: 로깅 서비스
- **`service.service_container`**: 서비스 컨테이너
- **`application.base_web_server.main`**: 메인 서버에서 이메일 서비스 초기화 및 종료

### 사용하는 Template
- **`template.notification`**: 알림 시스템에서 이메일 발송 (ServiceContainer를 통해 EmailService 사용, notification_persistence_consumer에서 이메일 알림 처리)
- **`template.base`**: AppConfig에 EmailConfig 포함

### 외부 시스템
- **AWS SES**: 이메일 발송 서비스
- **AWS IAM**: 인증 및 권한 관리
- **S3**: 이메일 템플릿 저장 (선택사항)
- **CloudWatch**: 이메일 발송 모니터링 및 로그
