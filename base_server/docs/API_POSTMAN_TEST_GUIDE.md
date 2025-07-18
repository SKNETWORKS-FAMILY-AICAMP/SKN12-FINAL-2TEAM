# API 테스트 가이드 (Postman)

이 문서는 Base Server의 모든 API 엔드포인트에 대한 Postman 테스트 가이드입니다.

## 기본 설정

### 환경 변수 설정
```json
{
  "base_url": "http://localhost:8000",
  "access_token": "your_access_token_here",
  "admin_token": "your_admin_token_here"
}
```

### 공통 헤더
```json
{
  "Content-Type": "application/json",
  "Accept": "application/json"
}
```

## 기본 요청/응답 구조

### BaseRequest (모든 요청의 기본 구조)
```json
{
  "accessToken": "string",
  "sequence": 0
}
```

### BaseResponse (모든 응답의 기본 구조)
```json
{
  "errorCode": 0,
  "sequence": 0
}
```

---

## 1. Account API (/api/account)

### 1.1 로그인
**POST** `/api/account/login`

**요청 예시:**
```json
{
  "platform_type": "native",
  "account_id": "test@example.com",
  "password": "password123",
  "sequence": 1
}
```

**응답 예시:**
```json
{
  "errorCode": 0,
  "sequence": 1,
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "refresh_token_here",
  "user_id": "user123",
  "next_step": "COMPLETE"
}
```

### 1.2 회원가입
**POST** `/api/account/signup`

**요청 예시:**
```json
{
  "platform_type": "native",
  "account_id": "newuser@example.com",
  "password": "password123",
  "sequence": 2
}
```

**응답 예시:**
```json
{
  "errorCode": 0,
  "sequence": 2,
  "user_id": "user456",
  "next_step": "LOGIN",
  "message": "회원가입 완료"
}
```

### 1.3 로그아웃
**POST** `/api/account/logout`

**요청 예시:**
```json
{
  "accessToken": "{{access_token}}",
  "sequence": 3
}
```

**응답 예시:**
```json
{
  "errorCode": 0,
  "sequence": 3,
  "message": "로그아웃 완료"
}
```

### 1.4 계정 정보 조회
**POST** `/api/account/info`

**요청 예시:**
```json
{
  "accessToken": "{{access_token}}",
  "sequence": 4
}
```

**응답 예시:**
```json
{
  "errorCode": 0,
  "sequence": 4,
  "user_id": "user123",
  "account_id": "test@example.com",
  "platform_type": "native",
  "created_at": "2024-01-01T00:00:00Z",
  "last_login": "2024-07-16T10:30:00Z"
}
```

### 1.5 프로필 설정
**POST** `/api/account/profile/setup`

**요청 예시:**
```json
{
  "accessToken": "{{access_token}}",
  "investment_experience": "중급",
  "risk_tolerance": "보통",
  "investment_goal": "장기투자",
  "monthly_budget": 1000000,
  "sequence": 5
}
```

**응답 예시:**
```json
{
  "errorCode": 0,
  "sequence": 5,
  "message": "프로필 설정 완료",
  "profile_id": "profile123"
}
```

---

## 2. Admin API (/api/admin)

### 2.1 서버 상태 확인
**POST** `/api/admin/serverstatus`

**요청 예시:**
```json
{
  "accessToken": "{{admin_token}}",
  "sequence": 1
}
```

**응답 예시:**
```json
{
  "errorCode": 0,
  "sequence": 1,
  "services": {
    "database": true,
    "cache": true,
    "storage": true,
    "search": true,
    "vectordb": true,
    "external": true,
    "lock": true,
    "queue": true
  },
  "server_info": {
    "uptime": "2h 30m",
    "version": "1.0.0",
    "environment": "production"
  }
}
```

### 2.2 헬스체크
**POST** `/api/admin/healthcheck`

**요청 예시:**
```json
{
  "accessToken": "{{admin_token}}",
  "sequence": 2
}
```

**응답 예시:**
```json
{
  "errorCode": 0,
  "sequence": 2,
  "status": "healthy",
  "timestamp": "2024-07-16T10:30:00Z",
  "checks": {
    "database": "ok",
    "cache": "ok",
    "external_services": "ok"
  }
}
```

### 2.3 Ping (GET)
**GET** `/api/admin/ping`

**응답 예시:**
```json
{
  "status": "pong",
  "timestamp": "2024-07-16T10:30:00Z"
}
```

---

## 3. Chat API (/api/chat)

### 3.1 채팅방 목록 조회
**POST** `/api/chat/rooms`

**요청 예시:**
```json
{
  "accessToken": "{{access_token}}",
  "sequence": 1
}
```

**응답 예시:**
```json
{
  "errorCode": 0,
  "sequence": 1,
  "rooms": [
    {
      "room_id": "room123",
      "name": "투자 상담",
      "created_at": "2024-07-16T09:00:00Z",
      "last_message": "안녕하세요!",
      "last_message_time": "2024-07-16T10:00:00Z"
    }
  ]
}
```

### 3.2 메시지 전송
**POST** `/api/chat/message/send`

**요청 예시:**
```json
{
  "accessToken": "{{access_token}}",
  "room_id": "room123",
  "content": "안녕하세요! 투자 상담을 받고 싶습니다.",
  "sequence": 2
}
```

**응답 예시:**
```json
{
  "errorCode": 0,
  "sequence": 2,
  "message_id": "msg456",
  "room_id": "room123",
  "content": "안녕하세요! 어떤 투자 상담을 도와드릴까요?",
  "sent_at": "2024-07-16T10:30:00Z"
}
```

### 3.3 AI 분석 요청
**POST** `/api/chat/analysis`

**요청 예시:**
```json
{
  "accessToken": "{{access_token}}",
  "symbols": ["AAPL", "GOOGL", "MSFT"],
  "analysis_type": "technical",
  "sequence": 3
}
```

**응답 예시:**
```json
{
  "errorCode": 0,
  "sequence": 3,
  "analysis": {
    "summary": "현재 기술적 분석 결과...",
    "recommendations": [
      {
        "symbol": "AAPL",
        "action": "BUY",
        "reason": "상승 추세"
      }
    ]
  }
}
```

---

## 4. Portfolio API (/api/portfolio)

### 4.1 포트폴리오 조회
**POST** `/api/portfolio/get`

**요청 예시:**
```json
{
  "accessToken": "{{access_token}}",
  "sequence": 1
}
```

**응답 예시:**
```json
{
  "errorCode": 0,
  "sequence": 1,
  "portfolio": {
    "total_value": 10000000,
    "holdings": [
      {
        "symbol": "AAPL",
        "quantity": 50,
        "avg_price": 150.00,
        "current_price": 155.00,
        "profit_loss": 250.00
      }
    ],
    "performance": {
      "total_return": 5.5,
      "daily_change": 1.2
    }
  }
}
```

### 4.2 주식 추가
**POST** `/api/portfolio/add-stock`

**요청 예시:**
```json
{
  "accessToken": "{{access_token}}",
  "symbol": "TSLA",
  "quantity": 10,
  "price": 250.00,
  "sequence": 2
}
```

**응답 예시:**
```json
{
  "errorCode": 0,
  "sequence": 2,
  "message": "주식이 포트폴리오에 추가되었습니다.",
  "transaction_id": "trans123",
  "new_total_value": 10250000
}
```

### 4.3 리밸런싱
**POST** `/api/portfolio/rebalance`

**요청 예시:**
```json
{
  "accessToken": "{{access_token}}",
  "strategy": "equal_weight",
  "sequence": 3
}
```

**응답 예시:**
```json
{
  "errorCode": 0,
  "sequence": 3,
  "rebalance_plan": [
    {
      "symbol": "AAPL",
      "action": "SELL",
      "quantity": 10,
      "reason": "비중 조정"
    }
  ],
  "estimated_cost": 1500.00
}
```

---

## 5. Market API (/api/market)

### 5.1 종목 검색
**POST** `/api/market/security/search`

**요청 예시:**
```json
{
  "accessToken": "{{access_token}}",
  "query": "Apple",
  "sequence": 1
}
```

**응답 예시:**
```json
{
  "errorCode": 0,
  "sequence": 1,
  "securities": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "exchange": "NASDAQ",
      "sector": "Technology",
      "current_price": 155.00
    }
  ]
}
```

### 5.2 시장 가격 조회
**POST** `/api/market/price`

**요청 예시:**
```json
{
  "accessToken": "{{access_token}}",
  "symbols": ["AAPL", "GOOGL", "MSFT"],
  "sequence": 2
}
```

**응답 예시:**
```json
{
  "errorCode": 0,
  "sequence": 2,
  "prices": [
    {
      "symbol": "AAPL",
      "price": 155.00,
      "change": 2.50,
      "change_percent": 1.64,
      "volume": 1000000,
      "timestamp": "2024-07-16T10:30:00Z"
    }
  ]
}
```

### 5.3 시장 개요
**POST** `/api/market/overview`

**요청 예시:**
```json
{
  "accessToken": "{{access_token}}",
  "sequence": 3
}
```

**응답 예시:**
```json
{
  "errorCode": 0,
  "sequence": 3,
  "market_summary": {
    "indices": [
      {
        "name": "S&P 500",
        "value": 4500.00,
        "change": 25.00,
        "change_percent": 0.56
      }
    ],
    "sectors": [
      {
        "name": "Technology",
        "change_percent": 1.2
      }
    ]
  }
}
```

---

## 6. AutoTrade API (/api/autotrade)

### 6.1 전략 목록 조회
**POST** `/api/autotrade/strategy/list`

**요청 예시:**
```json
{
  "accessToken": "{{access_token}}",
  "sequence": 1
}
```

**응답 예시:**
```json
{
  "errorCode": 0,
  "sequence": 1,
  "strategies": [
    {
      "strategy_id": "strat123",
      "name": "모멘텀 전략",
      "description": "기술적 분석 기반 모멘텀 전략",
      "algorithm_type": "momentum",
      "status": "active",
      "performance": {
        "total_return": 12.5,
        "win_rate": 65.2
      }
    }
  ]
}
```

### 6.2 백테스트 실행
**POST** `/api/autotrade/backtest`

**요청 예시:**
```json
{
  "accessToken": "{{access_token}}",
  "strategy_id": "strat123",
  "start_date": "2024-01-01",
  "end_date": "2024-07-01",
  "initial_capital": 1000000,
  "sequence": 2
}
```

**응답 예시:**
```json
{
  "errorCode": 0,
  "sequence": 2,
  "backtest_id": "bt456",
  "results": {
    "total_return": 15.2,
    "max_drawdown": -8.5,
    "sharpe_ratio": 1.35,
    "win_rate": 62.8,
    "total_trades": 156
  }
}
```

### 6.3 AI 전략 생성
**POST** `/api/autotrade/ai-strategy`

**요청 예시:**
```json
{
  "accessToken": "{{access_token}}",
  "investment_goal": "성장",
  "risk_tolerance": "보통",
  "investment_amount": 5000000,
  "time_horizon": "장기",
  "sequence": 3
}
```

**응답 예시:**
```json
{
  "errorCode": 0,
  "sequence": 3,
  "strategy": {
    "strategy_id": "ai_strat789",
    "name": "AI 성장 전략",
    "description": "AI가 생성한 개인 맞춤형 성장 전략",
    "recommended_allocation": [
      {
        "asset_class": "주식",
        "percentage": 70
      },
      {
        "asset_class": "채권",
        "percentage": 30
      }
    ]
  }
}
```

---

## 7. Settings API (/api/settings)

### 7.1 설정 조회
**POST** `/api/settings/get`

**요청 예시:**
```json
{
  "accessToken": "{{access_token}}",
  "sequence": 1
}
```

**응답 예시:**
```json
{
  "errorCode": 0,
  "sequence": 1,
  "settings": {
    "notifications": {
      "email_enabled": true,
      "push_enabled": true,
      "price_alert_enabled": true
    },
    "trading": {
      "auto_rebalance": false,
      "risk_limit": 10000
    },
    "display": {
      "theme": "dark",
      "language": "ko"
    }
  }
}
```

### 7.2 설정 업데이트
**POST** `/api/settings/update`

**요청 예시:**
```json
{
  "accessToken": "{{access_token}}",
  "section": "notifications",
  "settings": {
    "email_enabled": false,
    "push_enabled": true
  },
  "sequence": 2
}
```

**응답 예시:**
```json
{
  "errorCode": 0,
  "sequence": 2,
  "message": "설정이 업데이트되었습니다.",
  "updated_settings": {
    "email_enabled": false,
    "push_enabled": true
  }
}
```

### 7.3 비밀번호 변경
**POST** `/api/settings/password/change`

**요청 예시:**
```json
{
  "accessToken": "{{access_token}}",
  "current_password": "oldpassword123",
  "new_password": "newpassword456",
  "sequence": 3
}
```

**응답 예시:**
```json
{
  "errorCode": 0,
  "sequence": 3,
  "message": "비밀번호가 성공적으로 변경되었습니다."
}
```

---

## 8. Notification API (/api/notification)

### 8.1 알림 목록 조회
**POST** `/api/notification/list`

**요청 예시:**
```json
{
  "accessToken": "{{access_token}}",
  "page": 1,
  "limit": 20,
  "sequence": 1
}
```

**응답 예시:**
```json
{
  "errorCode": 0,
  "sequence": 1,
  "notifications": [
    {
      "notification_id": "notif123",
      "type": "price_alert",
      "title": "가격 알림",
      "message": "AAPL이 목표 가격에 도달했습니다.",
      "is_read": false,
      "created_at": "2024-07-16T10:00:00Z"
    }
  ],
  "total_count": 50,
  "unread_count": 5
}
```

### 8.2 알림 읽음 처리
**POST** `/api/notification/mark-read`

**요청 예시:**
```json
{
  "accessToken": "{{access_token}}",
  "notification_ids": ["notif123", "notif456"],
  "sequence": 2
}
```

**응답 예시:**
```json
{
  "errorCode": 0,
  "sequence": 2,
  "message": "알림이 읽음 처리되었습니다.",
  "updated_count": 2
}
```

### 8.3 가격 알림 생성
**POST** `/api/notification/create-alert`

**요청 예시:**
```json
{
  "accessToken": "{{access_token}}",
  "symbol": "AAPL",
  "alert_type": "price_above",
  "target_value": 160.00,
  "sequence": 3
}
```

**응답 예시:**
```json
{
  "errorCode": 0,
  "sequence": 3,
  "alert_id": "alert789",
  "message": "가격 알림이 생성되었습니다.",
  "alert_details": {
    "symbol": "AAPL",
    "type": "price_above",
    "target": 160.00,
    "current_price": 155.00
  }
}
```

---

## 9. Crawler API (/api/crawler)

### 9.1 크롤러 작업 실행
**POST** `/api/crawler/execute`

**요청 예시:**
```json
{
  "accessToken": "{{access_token}}",
  "task_id": "task123",
  "task_type": "news_crawl",
  "target_url": "https://news.example.com",
  "parameters": {
    "keywords": ["stock", "market"],
    "max_articles": 100
  },
  "priority": 1,
  "lock_ttl": 3600,
  "sequence": 1
}
```

**응답 예시:**
```json
{
  "errorCode": 0,
  "sequence": 1,
  "task_id": "task123",
  "status": "running",
  "message": "Crawler task started: news_crawl",
  "started_at": "2024-07-16T10:30:00Z",
  "lock_acquired": true
}
```

### 9.2 크롤러 상태 조회
**POST** `/api/crawler/status`

**요청 예시:**
```json
{
  "accessToken": "{{access_token}}",
  "task_id": "task123",
  "status": "running",
  "limit": 10,
  "sequence": 2
}
```

**응답 예시:**
```json
{
  "errorCode": 0,
  "sequence": 2,
  "tasks": [
    {
      "task_id": "task123",
      "task_type": "news_crawl",
      "status": "running",
      "started_at": "2024-07-16T10:30:00Z",
      "data_count": 0,
      "priority": 1
    }
  ],
  "total_count": 1
}
```

### 9.3 크롤러 헬스체크
**POST** `/api/crawler/health`

**요청 예시:**
```json
{
  "accessToken": "{{access_token}}",
  "check_services": true,
  "sequence": 3
}
```

**응답 예시:**
```json
{
  "errorCode": 0,
  "sequence": 3,
  "status": "healthy",
  "timestamp": "2024-07-16T10:30:00Z",
  "active_tasks": 2,
  "completed_today": 15,
  "failed_today": 1,
  "services": {
    "lock_service": true,
    "external_service": true,
    "vectordb_service": true,
    "search_service": true
  }
}
```

---

## 10. Tutorial API (/api/tutorial)

### 10.1 튜토리얼 시작
**POST** `/api/tutorial/start`

**요청 예시:**
```json
{
  "accessToken": "{{access_token}}",
  "sequence": 1
}
```

**응답 예시:**
```json
{
  "errorCode": 0,
  "sequence": 1,
  "session_id": "tutorial123",
  "current_step": 1,
  "total_steps": 5,
  "step_content": {
    "title": "포트폴리오 기초",
    "description": "포트폴리오 관리의 기본 개념을 배워보세요",
    "instructions": ["첫 번째 단계입니다..."]
  }
}
```

### 10.2 튜토리얼 진행
**POST** `/api/tutorial/progress`

**요청 예시:**
```json
{
  "accessToken": "{{access_token}}",
  "session_id": "tutorial123",
  "current_step": 2,
  "sequence": 2
}
```

**응답 예시:**
```json
{
  "errorCode": 0,
  "sequence": 2,
  "next_step": 3,
  "progress_percentage": 40,
  "step_content": {
    "title": "리스크 관리",
    "description": "투자 리스크를 관리하는 방법",
    "instructions": ["두 번째 단계입니다..."]
  }
}
```

---

## 11. Dashboard API (/api/dashboard)

### 11.1 대시보드 메인 정보
**POST** `/api/dashboard/main`

**요청 예시:**
```json
{
  "accessToken": "{{access_token}}",
  "sequence": 1
}
```

**응답 예시:**
```json
{
  "errorCode": 0,
  "sequence": 1,
  "dashboard": {
    "portfolio_summary": {
      "total_value": 10000000,
      "daily_change": 125000,
      "daily_change_percent": 1.25
    },
    "market_summary": {
      "kospi": {
        "value": 2650.5,
        "change": 15.2,
        "change_percent": 0.58
      }
    },
    "recent_activities": [
      {
        "type": "trade",
        "description": "AAPL 10주 매수",
        "timestamp": "2024-07-16T09:30:00Z"
      }
    ]
  }
}
```

### 11.2 대시보드 알림
**POST** `/api/dashboard/alerts`

**요청 예시:**
```json
{
  "accessToken": "{{access_token}}",
  "sequence": 2
}
```

**응답 예시:**
```json
{
  "errorCode": 0,
  "sequence": 2,
  "alerts": [
    {
      "type": "price_alert",
      "symbol": "AAPL",
      "message": "목표 가격 도달",
      "severity": "high",
      "created_at": "2024-07-16T10:00:00Z"
    }
  ]
}
```

---

## 테스트 시나리오

### 기본 플로우 테스트
1. **회원가입** → **로그인** → **프로필 설정** → **포트폴리오 조회**
2. **시장 데이터 조회** → **주식 추가** → **포트폴리오 성과 확인**
3. **설정 변경** → **알림 설정** → **로그아웃**

### 에러 케이스 테스트
- 잘못된 accessToken
- 필수 파라미터 누락
- 권한 없는 접근
- 서버 오류 시뮬레이션

### 성능 테스트
- 동시 다중 요청
- 대용량 데이터 처리
- 응답 시간 측정

---

## 에러 코드 참조

| 코드 | 의미 |
|------|------|
| 0 | 성공 |
| 1001 | 인증 실패 |
| 1002 | 권한 없음 |
| 1003 | 잘못된 파라미터 |
| 1004 | 리소스 없음 |
| 1005 | 서버 에러 |
| 10001 | 크롤러 락 획득 실패 |
| 10002 | 크롤러 상태 조회 실패 |
| 10003 | 크롤러 헬스체크 실패 |

이 문서를 참고하여 각 API 엔드포인트를 체계적으로 테스트할 수 있습니다.