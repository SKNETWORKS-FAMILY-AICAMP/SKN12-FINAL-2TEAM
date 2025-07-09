# Finance Server API 완전 테스트 가이드 - Windows Conda + PostMan

## 📋 목차
1. [환경 설정](#1-환경-설정)
2. [서버 실행](#2-서버-실행)
3. [PostMan 설정](#3-postman-설정)
4. [API 테스트 단계별 가이드](#4-api-테스트-단계별-가이드)
5. [전체 API 명세](#5-전체-api-명세)
6. [에러 처리](#6-에러-처리)
7. [테스트 체크리스트](#7-테스트-체크리스트)

---

## 1. 환경 설정

### 1.1 Conda 환경 준비 (Windows)

**Step 1: Anaconda Prompt 관리자 권한으로 실행**
```bash
# 새 환경 생성
conda create -n finance_server python=3.9 -y

# 환경 활성화
conda activate finance_server

# 필요한 패키지 설치
pip install fastapi==0.104.1
pip install uvicorn==0.24.0
pip install redis==5.0.1
pip install mysql-connector-python==8.2.0
pip install bcrypt==4.1.2
pip install PyJWT==2.8.0
pip install python-multipart==0.0.6
```

**Step 2: 프로젝트 디렉토리로 이동**
```bash
cd C:\SKN12-FINAL-2TEAM\base_server
```

**Step 3: Python 경로 확인**
```bash
python --version
# Python 3.9.x 확인
```

---

## 2. 서버 실행

### 2.1 설정 파일 확인
```bash
# config 파일 존재 확인
dir application\base_web_server\base_web_server-config_local.json
```

### 2.2 서버 실행
```bash
# 개발 모드로 서버 실행
python -m uvicorn application.base_web_server.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug

# 또는 간단히
uvicorn application.base_web_server.main:app --reload --port 8000
```

### 2.3 서버 실행 확인
**브라우저에서 접속:** `http://localhost:8000`

**예상 응답:**
```json
{
    "message": "base_web_server 동작 중",
    "log_level": "DEBUG",
    "env": "LOCAL",
    "config_file": "..."
}
```

---

## 3. PostMan 설정

### 3.1 Collection 생성
1. PostMan 실행
2. **New Collection** 클릭
3. 이름: `Finance Server API Tests`
4. Description: `Complete API testing for Finance Server`

### 3.2 Environment 설정
1. **Environments** → **New Environment**
2. 이름: `Finance Local`
3. 변수 설정:

| Variable | Initial Value | Current Value |
|----------|---------------|---------------|
| `base_url` | `http://localhost:8000` | `http://localhost:8000` |
| `access_token` | | (로그인 후 자동 설정) |
| `account_db_key` | | (로그인 후 자동 설정) |
| `shard_id` | | (로그인 후 자동 설정) |

### 3.3 Pre-request Script (Collection 레벨)
Collection 설정 → Pre-request Scripts:
```javascript
// 공통 헤더 설정
pm.request.headers.add({
    key: 'Content-Type',
    value: 'application/json'
});

// 토큰이 있으면 Authorization 헤더 추가
const token = pm.environment.get("access_token");
if (token && !pm.request.url.path.includes('login') && !pm.request.url.path.includes('signup') && !pm.request.url.path.includes('ping')) {
    pm.request.headers.add({
        key: 'Authorization',
        value: 'Bearer ' + token
    });
}
```

---

## 4. API 테스트 단계별 가이드

### Phase 1: 기본 연결 테스트

#### Test 1-1: 서버 상태 확인
- **Method:** `GET`
- **URL:** `{{base_url}}/`
- **Headers:** 없음
- **Body:** 없음

**Tests Script:**
```javascript
pm.test("서버 정상 동작", function () {
    pm.response.to.have.status(200);
    const jsonData = pm.response.json();
    pm.expect(jsonData.message).to.include("동작 중");
});
```

#### Test 1-2: Admin Ping
- **Method:** `GET`
- **URL:** `{{base_url}}/api/admin/ping`
- **Headers:** 없음
- **Body:** 없음

**예상 응답:**
```json
{
    "status": "pong",
    "timestamp": "2025-01-09T10:00:00Z"
}
```

---

### Phase 2: 계정 관리 테스트

#### Test 2-1: 회원가입
- **Method:** `POST`
- **URL:** `{{base_url}}/api/account/signup`
- **Headers:** `Content-Type: application/json`
- **Body (JSON):**
```json
{
    "platform_type": 1,
    "account_id": "testuser123",
    "password": "password123!",
    "password_confirm": "password123!",
    "nickname": "테스트사용자",
    "email": "test@example.com",
    "name": "홍길동",
    "birth_year": 1990,
    "birth_month": 1,
    "birth_day": 1,
    "gender": "M"
}
```

**Tests Script:**
```javascript
pm.test("회원가입 성공", function () {
    pm.response.to.have.status(200);
    const jsonData = pm.response.json();
    pm.expect(jsonData.error_code).to.eql(0);
    pm.expect(jsonData).to.have.property('account_db_key');
});
```

#### Test 2-2: 로그인
- **Method:** `POST`
- **URL:** `{{base_url}}/api/account/login`
- **Headers:** `Content-Type: application/json`
- **Body (JSON):**
```json
{
    "platform_type": 1,
    "account_id": "testuser123",
    "password": "password123!"
}
```

**Tests Script:**
```javascript
pm.test("로그인 성공", function () {
    pm.response.to.have.status(200);
    const jsonData = pm.response.json();
    
    if (jsonData.error_code === 0) {
        // 토큰과 사용자 정보 저장
        pm.environment.set("access_token", jsonData.accessToken);
        pm.environment.set("account_db_key", jsonData.account_db_key);
        pm.environment.set("shard_id", jsonData.shard_id);
        
        pm.test("토큰 발급됨", function () {
            pm.expect(jsonData.accessToken).to.be.a('string');
            pm.expect(jsonData.accessToken.length).to.be.above(10);
        });
    }
});
```

#### Test 2-3: 계정 정보 조회
- **Method:** `POST`
- **URL:** `{{base_url}}/api/account/info`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{}
```

#### Test 2-4: 로그아웃
- **Method:** `POST`
- **URL:** `{{base_url}}/api/account/accountlogout`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{}
```

---

### Phase 3: 관리자 API 테스트 (로그인 필요)

#### Test 3-1: 헬스체크
- **Method:** `POST`
- **URL:** `{{base_url}}/api/admin/healthcheck`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "check_type": "all"
}
```

#### Test 3-2: 서버 상태
- **Method:** `POST`
- **URL:** `{{base_url}}/api/admin/serverstatus`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "include_metrics": true
}
```

#### Test 3-3: 세션 수 조회
- **Method:** `POST`
- **URL:** `{{base_url}}/api/admin/sessioncount`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{}
```

#### Test 3-4: 메트릭 조회
- **Method:** `GET`
- **URL:** `{{base_url}}/api/admin/metrics`
- **Headers:** `Authorization: Bearer {{access_token}}`

---

### Phase 4: 포트폴리오 API 테스트

#### Test 4-1: 포트폴리오 조회
- **Method:** `POST`
- **URL:** `{{base_url}}/api/portfolio/get`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "include_performance": true
}
```

**예상 응답:**
```json
{
    "portfolio": {
        "portfolio_id": "port_12345",
        "name": "메인 포트폴리오",
        "total_value": 10000.0,
        "cash_balance": 5000.0,
        "invested_amount": 5000.0,
        "total_return": 500.0,
        "return_rate": 5.0,
        "created_at": "2025-01-09T10:00:00"
    },
    "holdings": [],
    "performance": {
        "total_return": 500.0,
        "annualized_return": 15.0,
        "sharpe_ratio": 1.2,
        "max_drawdown": -5.0,
        "win_rate": 60.0,
        "profit_factor": 1.5
    },
    "errorCode": 0
}
```

#### Test 4-2: 종목 추가
- **Method:** `POST`
- **URL:** `{{base_url}}/api/portfolio/add-stock`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "symbol": "AAPL",
    "quantity": 10,
    "price": 150.0,
    "order_type": "MARKET"
}
```

#### Test 4-3: 종목 제거
- **Method:** `POST`
- **URL:** `{{base_url}}/api/portfolio/remove-stock`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "symbol": "AAPL",
    "quantity": 5,
    "price": 155.0
}
```

#### Test 4-4: 리밸런싱 분석
- **Method:** `POST`
- **URL:** `{{base_url}}/api/portfolio/rebalance`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "target_allocation": {
        "AAPL": 40.0,
        "GOOGL": 30.0,
        "MSFT": 30.0
    }
}
```

#### Test 4-5: 성과 분석
- **Method:** `POST`
- **URL:** `{{base_url}}/api/portfolio/performance`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "period": "1M"
}
```

---

### Phase 5: 마켓 데이터 API 테스트

#### Test 5-1: 종목 검색
- **Method:** `POST`
- **URL:** `{{base_url}}/api/market/search-securities`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "query": "Apple"
}
```

**예상 응답:**
```json
{
    "securities": [
        {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "exchange": "NASDAQ",
            "sector": "Technology"
        },
        {
            "symbol": "GOOGL",
            "name": "Alphabet Inc.",
            "exchange": "NASDAQ",
            "sector": "Technology"
        }
    ],
    "total_count": 2,
    "errorCode": 0
}
```

#### Test 5-2: 실시간 가격 조회
- **Method:** `POST`
- **URL:** `{{base_url}}/api/market/get-realtime-price`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "symbols": ["AAPL", "GOOGL"]
}
```

#### Test 5-3: 뉴스 조회
- **Method:** `POST`
- **URL:** `{{base_url}}/api/market/get-news`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "category": "TECH"
}
```

#### Test 5-4: 시장 개요
- **Method:** `POST`
- **URL:** `{{base_url}}/api/market/get-overview`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "indices": ["KOSPI", "KOSDAQ"]
}
```

---

### Phase 6: 채팅 AI API 테스트

#### Test 6-1: 채팅방 목록
- **Method:** `POST`
- **URL:** `{{base_url}}/api/chat/rooms`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "page": 1,
    "limit": 10
}
```

#### Test 6-2: 채팅방 생성
- **Method:** `POST`
- **URL:** `{{base_url}}/api/chat/room/create`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "title": "투자 상담",
    "ai_persona": "ANALYST",
    "purpose": "포트폴리오 분석"
}
```

**예상 응답:**
```json
{
    "room": {
        "room_id": "room_abc123",
        "title": "투자 상담",
        "persona_type": "ANALYST",
        "purpose": "포트폴리오 분석",
        "created_at": "2025-01-09T10:00:00",
        "last_message_time": "2025-01-09T10:00:00",
        "message_count": 0,
        "is_active": true
    },
    "errorCode": 0
}
```

#### Test 6-3: 메시지 전송
- **Method:** `POST`
- **URL:** `{{base_url}}/api/chat/message/send`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "room_id": "room_abc123",
    "message": "현재 포트폴리오 상태를 분석해주세요"
}
```

#### Test 6-4: 메시지 목록
- **Method:** `POST`
- **URL:** `{{base_url}}/api/chat/messages`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "room_id": "room_abc123",
    "page": 1,
    "limit": 50
}
```

#### Test 6-5: 종목 분석
- **Method:** `POST`
- **URL:** `{{base_url}}/api/chat/analysis`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "symbols": ["AAPL"]
}
```

#### Test 6-6: AI 페르소나 목록
- **Method:** `POST`
- **URL:** `{{base_url}}/api/chat/personas`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{}
```

#### Test 6-7: 채팅 요약
- **Method:** `POST`
- **URL:** `{{base_url}}/api/chat/summary`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "room_id": "room_abc123"
}
```

#### Test 6-8: 채팅방 삭제
- **Method:** `POST`
- **URL:** `{{base_url}}/api/chat/room/delete`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "room_id": "room_abc123"
}
```

---

### Phase 7: 자동매매 API 테스트

#### Test 7-1: 전략 목록
- **Method:** `POST`
- **URL:** `{{base_url}}/api/autotrade/get-strategies`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "status_filter": "ACTIVE"
}
```

**예상 응답:**
```json
{
    "strategies": [
        {
            "strategy_id": "strat_12345_1",
            "name": "RSI 역추세 전략",
            "description": "RSI 과매수/과매도 구간에서의 역추세 매매",
            "strategy_type": "TECHNICAL",
            "target_symbols": ["AAPL", "GOOGL"],
            "status": "ACTIVE",
            "created_at": "2025-01-09T10:00:00",
            "risk_level": "MODERATE"
        }
    ],
    "performances": {
        "strat_12345_1": {
            "total_return": 12.5,
            "win_rate": 65.0,
            "sharpe_ratio": 1.2,
            "max_drawdown": -8.5
        }
    },
    "errorCode": 0
}
```

#### Test 7-2: 전략 생성
- **Method:** `POST`
- **URL:** `{{base_url}}/api/autotrade/create-strategy`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "name": "새 RSI 전략",
    "strategy_type": "TECHNICAL",
    "target_symbols": ["AAPL"],
    "parameters": {
        "rsi_period": 14,
        "oversold": 30,
        "overbought": 70
    }
}
```

#### Test 7-3: 전략 수정
- **Method:** `POST`
- **URL:** `{{base_url}}/api/autotrade/control-strategy`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "strategy_id": "strat_12345_1",
    "action": "UPDATE",
    "parameters": {
        "rsi_period": 21
    }
}
```

#### Test 7-4: 실행 내역
- **Method:** `POST`
- **URL:** `{{base_url}}/api/autotrade/get-executions`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "strategy_id": "strat_12345_1"
}
```

#### Test 7-5: 백테스트
- **Method:** `POST`
- **URL:** `{{base_url}}/api/autotrade/backtest`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "strategy_id": "strat_12345_1",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
}
```

#### Test 7-6: AI 전략 생성
- **Method:** `POST`
- **URL:** `{{base_url}}/api/autotrade/get-recommendations`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "investment_goal": "GROWTH",
    "risk_tolerance": "MODERATE"
}
```

---

### Phase 8: 설정 API 테스트

#### Test 8-1: 설정 조회
- **Method:** `POST`
- **URL:** `{{base_url}}/api/settings/get`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "section": "notifications"
}
```

**예상 응답:**
```json
{
    "settings": {
        "notifications": {
            "email_enabled": true,
            "push_enabled": true,
            "sms_enabled": false,
            "price_alerts": true
        }
    },
    "defaults": {
        "theme": "LIGHT",
        "language": "ko-KR"
    },
    "errorCode": 0
}
```

#### Test 8-2: 설정 업데이트
- **Method:** `POST`
- **URL:** `{{base_url}}/api/settings/update-notification`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "section": "notifications",
    "settings": {
        "email_enabled": false,
        "push_enabled": true,
        "price_alerts": true
    }
}
```

#### Test 8-3: 설정 초기화
- **Method:** `POST`
- **URL:** `{{base_url}}/api/settings/reset`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "section": "notifications"
}
```

#### Test 8-4: OTP 설정
- **Method:** `POST`
- **URL:** `{{base_url}}/api/settings/update-security`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "enable": true,
    "verification_code": "123456"
}
```

#### Test 8-5: 비밀번호 변경
- **Method:** `POST`
- **URL:** `{{base_url}}/api/settings/update-profile`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "current_password": "password123!",
    "new_password": "newpassword123!"
}
```

#### Test 8-6: 데이터 내보내기
- **Method:** `POST`
- **URL:** `{{base_url}}/api/settings/export`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "data_types": ["PORTFOLIO", "TRADES", "SETTINGS"]
}
```

---

### Phase 9: 알림 API 테스트

#### Test 9-1: 알림 목록
- **Method:** `POST`
- **URL:** `{{base_url}}/api/notification/get-list`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "type_filter": "PRICE_ALERT",
    "page": 1,
    "limit": 10,
    "include_read": false
}
```

**예상 응답:**
```json
{
    "notifications": [
        {
            "notification_id": "notif_12345_1",
            "type": "PRICE_ALERT",
            "title": "AAPL 가격 알림",
            "message": "AAPL 주가가 $150을 넘었습니다",
            "symbol": "AAPL",
            "price": 152.0,
            "is_read": false,
            "created_at": "2025-01-09T10:00:00",
            "priority": "HIGH"
        }
    ],
    "total_count": 1,
    "unread_count": 1,
    "has_more": false,
    "errorCode": 0
}
```

#### Test 9-2: 알림 읽음 처리
- **Method:** `POST`
- **URL:** `{{base_url}}/api/notification/mark-read`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "notification_ids": ["notif_12345_1", "notif_12345_2"]
}
```

#### Test 9-3: 가격 알림 생성
- **Method:** `POST`
- **URL:** `{{base_url}}/api/notification/create-price-alert`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "symbol": "AAPL",
    "alert_type": "PRICE_ABOVE",
    "target_price": 160.0,
    "condition": "ABOVE",
    "notification_methods": ["EMAIL", "PUSH"],
    "is_repeatable": false,
    "expires_at": "2025-12-31T23:59:59"
}
```

#### Test 9-4: 가격 알림 목록
- **Method:** `POST`
- **URL:** `{{base_url}}/api/notification/get-price-alerts`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "symbol": "AAPL",
    "status": "ACTIVE",
    "page": 1,
    "limit": 10
}
```

#### Test 9-5: 가격 알림 삭제
- **Method:** `POST`
- **URL:** `{{base_url}}/api/notification/delete-price-alert`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "alert_ids": ["alert_12345_1"],
    "permanent_delete": false
}
```

---

### Phase 10: 대시보드 API 테스트

#### Test 10-1: 대시보드 메인
- **Method:** `POST`
- **URL:** `{{base_url}}/api/dashboard/main`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "include_chart": true,
    "chart_period": "1D"
}
```

#### Test 10-2: 대시보드 알림
- **Method:** `POST`
- **URL:** `{{base_url}}/api/dashboard/alerts`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "page": 1,
    "limit": 5
}
```

#### Test 10-3: 성과 분석
- **Method:** `POST`
- **URL:** `{{base_url}}/api/dashboard/performance`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "period": "1M"
}
```

#### Test 10-4: 퀵 액션
- **Method:** `POST`
- **URL:** `{{base_url}}/api/dashboard/quick-action`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "action_type": "PORTFOLIO_REBALANCE"
}
```

#### Test 10-5: 관심 종목
- **Method:** `POST`
- **URL:** `{{base_url}}/api/dashboard/watchlist`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{}
```

---

### Phase 11: 튜토리얼 API 테스트

#### Test 11-1: 튜토리얼 시작
- **Method:** `POST`
- **URL:** `{{base_url}}/api/tutorial/start`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "tutorial_type": "BASIC"
}
```

#### Test 11-2: 튜토리얼 진행
- **Method:** `POST`
- **URL:** `{{base_url}}/api/tutorial/progress`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "session_id": "tutorial_session_123",
    "step": 2,
    "action": "NEXT"
}
```

#### Test 11-3: 튜토리얼 완료
- **Method:** `POST`
- **URL:** `{{base_url}}/api/tutorial/complete`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{
    "session_id": "tutorial_session_123",
    "rating": 5
}
```

#### Test 11-4: 튜토리얼 목록
- **Method:** `POST`
- **URL:** `{{base_url}}/api/tutorial/list`
- **Headers:** `Authorization: Bearer {{access_token}}`
- **Body (JSON):**
```json
{}
```

---

## 5. 전체 API 명세

### 5.1 인증 방식
- **Anonymous**: 인증 불필요 (로그인, 회원가입, ping)
- **User**: Bearer Token 필요
- **Admin**: 관리자 권한 토큰 필요

### 5.2 공통 응답 형식
```json
{
    "data": { /* 실제 응답 데이터 */ },
    "errorCode": 0,
    "error_message": null
}
```

### 5.3 에러 코드
- `0`: 성공
- `1000`: 일반 오류
- `1001`: 인증 실패
- `1002`: 권한 부족
- `1003`: 잘못된 요청
- `1004`: 리소스 없음
- `1005`: 서버 내부 오류

---

## 6. 에러 처리

### 6.1 공통 에러 응답
```json
{
    "errorCode": 1001,
    "error_message": "Authentication failed"
}
```

### 6.2 PostMan Tests Script (공통)
```javascript
pm.test("응답 성공", function () {
    pm.response.to.have.status(200);
});

pm.test("에러 코드 확인", function () {
    const jsonData = pm.response.json();
    if (jsonData.errorCode !== undefined) {
        pm.expect(jsonData.errorCode).to.eql(0);
    }
});

pm.test("응답 시간 확인", function () {
    pm.expect(pm.response.responseTime).to.be.below(5000);
});
```

### 6.3 디버깅 팁
1. **서버 로그 확인**: 콘솔에서 에러 메시지 확인
2. **토큰 확인**: Environment 변수에서 토큰 유효성 확인
3. **요청 헤더**: Content-Type이 application/json인지 확인
4. **JSON 형식**: 요청 Body가 올바른 JSON 형식인지 확인

---

## 7. 테스트 체크리스트

### 7.1 사전 준비
- [ ] Conda 환경 활성화
- [ ] 서버 정상 실행 (포트 8000)
- [ ] PostMan Collection 생성
- [ ] Environment 변수 설정

### 7.2 Phase별 테스트
- [ ] **Phase 1**: 기본 연결 (서버 상태, ping)
- [ ] **Phase 2**: 계정 관리 (회원가입, 로그인, 로그아웃)
- [ ] **Phase 3**: 관리자 API (헬스체크, 서버 상태, 세션)
- [ ] **Phase 4**: 포트폴리오 (조회, 종목 추가/제거, 리밸런싱, 성과)
- [ ] **Phase 5**: 마켓 데이터 (검색, 가격, 뉴스, 개요)
- [ ] **Phase 6**: 채팅 AI (방 생성, 메시지, 분석, 페르소나)
- [ ] **Phase 7**: 자동매매 (전략 관리, 백테스트, 실행)
- [ ] **Phase 8**: 설정 (조회, 업데이트, 보안, 내보내기)
- [ ] **Phase 9**: 알림 (목록, 읽음처리, 가격알림)
- [ ] **Phase 10**: 대시보드 (메인, 성과, 퀵액션)
- [ ] **Phase 11**: 튜토리얼 (시작, 진행, 완료)

### 7.3 검증 항목
- [ ] 모든 API 응답이 HTTP 200
- [ ] errorCode가 0 (성공)
- [ ] 토큰 기반 인증 정상 동작
- [ ] 더미 데이터 응답 확인
- [ ] 응답 시간 5초 이내

### 7.4 추가 테스트
- [ ] 잘못된 토큰으로 인증 실패 테스트
- [ ] 필수 필드 누락시 에러 처리
- [ ] 대용량 데이터 요청 처리
- [ ] 동시 요청 처리 능력

---

## 🎯 마지막 체크포인트

**서버 실행 명령어:**
```bash
conda activate finance_server
cd C:\SKN12-FINAL-2TEAM\base_server
python -m uvicorn application.base_web_server.main:app --reload --port 8000
```

**PostMan 기본 설정:**
- Base URL: `http://localhost:8000`
- Content-Type: `application/json`
- Authorization: `Bearer {{access_token}}` (로그인 후)

**테스트 순서:**
1. 서버 실행 확인
2. 회원가입 → 로그인 → 토큰 획득
3. 모든 API 순차 테스트
4. 에러 케이스 테스트

이 가이드를 따라 진행하시면 Finance Server의 모든 API를 완전히 테스트할 수 있습니다! 🚀