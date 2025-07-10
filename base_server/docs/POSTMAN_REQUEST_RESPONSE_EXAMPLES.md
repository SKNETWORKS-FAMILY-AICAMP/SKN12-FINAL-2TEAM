# 🚀 Base Web Server API Request/Response 예시 완전 가이드

## 📋 개요
이 문서는 Base Web Server의 모든 API에 대한 실제 사용 가능한 Request와 예상 Response를 제공합니다.

## 🔧 기본 설정
- **Base URL**: `http://localhost:8000`
- **Content-Type**: `application/json`
- **Authorization**: `Bearer {{access_token}}` (로그인 후 필요)

---

## 🔴 Admin APIs

### 1. 서버 상태 확인
**Request:**
```http
GET http://localhost:8000/
```

**Response:**
```json
{
  "message": "base_web_server 동작 중",
  "log_level": "INFO",
  "env": "LOCAL",
  "config_file": "config.json"
}
```

### 2. Ping 테스트
**Request:**
```http
GET http://localhost:8000/api/admin/ping
```

**Response:**
```json
{
  "status": "pong",
  "timestamp": "2024-01-15T09:30:00Z"
}
```

### 3. 헬스체크
**Request:**
```http
POST http://localhost:8000/api/admin/healthcheck
Content-Type: application/json

{
  "accessToken": "",
  "sequence": 1001,
  "check_database": true,
  "check_cache": true,
  "check_external_services": true
}
```

**Response:**
```json
{
  "errorCode": 0,
  "sequence": 1001,
  "status": "healthy",
  "database_status": "connected",
  "cache_status": "connected",
  "external_services": {
    "market_data": "connected",
    "news_service": "connected"
  },
  "response_time_ms": 150
}
```

---

## 🟢 Account APIs
# 회원가입 (REQ-AUTH-001~009)
# 의거: 화면 002-2 (회원가입 페이지), REQ-AUTH-001~009

### 1. 이메일 인증 요청
# 이메일 인증 (REQ-AUTH-008)  
# 의거: 화면 002-3 (이메일 인증), REQ-AUTH-008
**Request:**
```http
POST http://localhost:8000/api/account/email/verify
Content-Type: application/json

{
  "accessToken": "",
  "sequence": 2001,
  "email": "testuser@example.com"
}
```

**Response:**
```json
{
  "errorCode": 0,
  "sequence": 2001,
  "message": "인증 코드가 이메일로 전송되었습니다",
  "expires_in": 300,
  "retry_after": 60
}
```

### 2. 회원가입
**Request:**
```http
POST http://localhost:8000/api/account/signup
Content-Type: application/json

{
  "accessToken": "",
  "sequence": 2003,
  "platform_type": 1,
  "account_id": "testuser123",
  "password": "TestPassword123!",
  "password_confirm": "TestPassword123!",
  "nickname": "테스트유저",
  "email": "testuser@example.com",
  "name": "홍길동",
  "birth_year": 1990,
  "birth_month": 5,
  "birth_day": 15,
  "gender": "M"
}
```

**Response:**
```json
{
  "errorCode": 0,
  "sequence": 2003,
  "account_db_key": 12345,
  "platform_type": 1,
  "account_id": "testuser123",
  "nickname": "테스트유저",
  "email": "testuser@example.com",
  "account_level": 1,
  "shard_id": 1,
  "profile_completed": false,
  "created_at": "2024-01-15T09:30:00Z"
}
```

### 3. 로그인
# 로그인 (REQ-AUTH-010~016)
# 의거: 화면 002-1 (로그인 페이지), REQ-AUTH-010~016
**Request:**
```http
POST http://localhost:8000/api/account/login
Content-Type: application/json

{
  "accessToken": "",
  "sequence": 2004,
  "platform_type": 1,
  "account_id": "testuser123",
  "password": "TestPassword123!"
}
```

**Response:**
```json
{
  "errorCode": 0,
  "sequence": 2004,
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
  "refreshToken": "refresh_token_example_12345",
  "account_db_key": 12345,
  "nickname": "테스트유저",
  "account_level": 1,
  "shard_id": 1,
  "account_info": {
    "account_db_key": 12345,
    "platform_type": 1,
    "account_id": "testuser123",
    "account_level": 1,
    "shard_id": 1
  },
  "expires_in": 3600,
  "profile_completed": false,
  "requires_otp": false
}
```

### 4. 계정 정보 조회
**Request:**
```http
POST http://localhost:8000/api/account/info
Content-Type: application/json
Authorization: Bearer {{access_token}}

{
  "accessToken": "{{access_token}}",
  "sequence": 2005
}
```

**Response:**
```json
{
  "errorCode": 0,
  "sequence": 2005,
  "profile": {
    "account_db_key": 12345,
    "platform_type": 1,
    "account_id": "testuser123",
    "nickname": "테스트유저",
    "email": "testuser@example.com",
    "account_level": 1,
    "shard_id": 1,
    "investment_experience": "INTERMEDIATE",
    "risk_tolerance": "MODERATE",
    "investment_goal": "GROWTH",
    "monthly_budget": 1000000.0,
    "profile_completed": true,
    "created_at": "2024-01-15T09:30:00Z",
    "last_login": "2024-01-15T10:30:00Z"
  }
}
```

### 5. 프로필 설정
# 프로필 설정 (REQ-AUTH-009)
# 의거: 화면 003 (프로필설정), REQ-AUTH-009
**Request:**
```http
POST http://localhost:8000/api/account/profile/setup
Content-Type: application/json
Authorization: Bearer {{access_token}}

{
  "accessToken": "{{access_token}}",
  "sequence": 2006,
  "investment_experience": "BEGINNER",
  "risk_tolerance": "MODERATE",
  "investment_goal": "GROWTH",
  "monthly_budget": 1000000.0
}
```

**Response:**
```json
{
  "errorCode": 0,
  "sequence": 2006,
  "profile": {
    "account_db_key": 12345,
    "platform_type": 1,
    "account_id": "testuser123",
    "nickname": "테스트유저",
    "email": "testuser@example.com",
    "account_level": 1,
    "shard_id": 1,
    "investment_experience": "BEGINNER",
    "risk_tolerance": "MODERATE",
    "investment_goal": "GROWTH",
    "monthly_budget": 1000000.0,
    "profile_completed": true,
    "created_at": "2024-01-15T09:30:00Z"
  }
}
```

---

## 🔵 Tutorial APIs
# 튜토리얼 시작 (REQ-HELP-001~004)
# 의거: 화면 004 (튜토리얼), REQ-HELP-001~004

### 1. 튜토리얼 시작
**Request:**
```http
POST http://localhost:8000/api/tutorial/start
Content-Type: application/json
Authorization: Bearer {{access_token}}

{
  "accessToken": "{{access_token}}",
  "sequence": 3002,
  "tutorial_type": "ONBOARDING",
  "user_level": "BEGINNER"
}
```

**Response:**
```json
{
  "errorCode": 0,
  "sequence": 3002,
  "session_id": "tutorial_12345_67890abcdef",
  "tutorial_type": "ONBOARDING",
  "steps": [
    {
      "step_id": "step_001",
      "step_number": 1,
      "title": "대시보드 살펴보기",
      "description": "메인 대시보드의 주요 기능들을 확인해보세요",
      "target_element": "#dashboard-main",
      "position": "BOTTOM",
      "action_required": true
    },
    {
      "step_id": "step_002",
      "step_number": 2,
      "title": "포트폴리오 만들기",
      "description": "첫 번째 포트폴리오를 생성해보세요",
      "target_element": "#portfolio-create",
      "position": "RIGHT",
      "action_required": true
    },
    {
      "step_id": "step_003",
      "step_number": 3,
      "title": "첫 투자 시작하기",
      "description": "관심 종목을 포트폴리오에 추가해보세요",
      "target_element": "#add-stock-button",
      "position": "TOP",
      "action_required": true
    }
  ],
  "total_steps": 5,
  "current_step": 1,
  "progress_rate": 0.0
}
```

### 2. 진행 상태 업데이트
**Request:**
```http
POST http://localhost:8000/api/tutorial/progress
Content-Type: application/json
Authorization: Bearer {{access_token}}

{
  "accessToken": "{{access_token}}",
  "sequence": 3003,
  "session_id": "tutorial_session_abc123",
  "current_step": 3,
  "action_completed": true,
  "time_spent": 45000
}
```

**Response:**
```json
{
  "errorCode": 0,
  "sequence": 3003,
  "session_id": "tutorial_12345_67890abcdef",
  "current_step": 3,
  "total_steps": 5,
  "progress_rate": 60.0,
  "next_step": {
    "step_id": "step_004",
    "step_number": 4,
    "title": "AI 채팅 사용하기",
    "description": "AI 투자 어드바이저와 대화해보세요",
    "target_element": "#chat-start",
    "position": "LEFT",
    "action_required": true
  },
  "completion_status": "IN_PROGRESS",
  "time_spent": 45000,
  "rewards": [
    {
      "type": "POINTS",
      "value": 100,
      "description": "튜토리얼 진행 보상"
    }
  ]
}
```

---

## 🟡 Dashboard APIs
# 대시보드 메인 데이터 (REQ-DASH-001~005)
# 의거: 화면 005 (대시보드), REQ-DASH-001~005

### 1. 메인 대시보드
**Request:**
```http
POST http://localhost:8000/api/dashboard/main
Content-Type: application/json
Authorization: Bearer {{access_token}}

{
  "accessToken": "{{access_token}}",
  "sequence": 4001,
  "include_chart": true,
  "chart_period": "1M"
}
```

**Response:**
```json
{
  "errorCode": 0,
  "sequence": 4001,
  "asset_summary": {
    "total_assets": 1000000.0,
    "cash_balance": 200000.0,
    "stock_value": 800000.0,
    "total_return": 50000.0,
    "return_rate": 5.0,
    "currency": "KRW",
    "last_updated": "2024-01-15T09:30:00Z"
  },
  "holdings": [
    {
      "symbol": "005930",
      "name": "삼성전자",
      "quantity": 10,
      "avg_price": 65000.0,
      "current_price": 68000.0,
      "market_value": 680000.0,
      "unrealized_pnl": 30000.0,
      "return_rate": 4.6
    },
    {
      "symbol": "000660",
      "name": "SK하이닉스",
      "quantity": 1,
      "avg_price": 120000.0,
      "current_price": 120000.0,
      "market_value": 120000.0,
      "unrealized_pnl": 0.0,
      "return_rate": 0.0
    }
  ],
  "recent_alerts": [
    {
      "alert_id": "alert_1",
      "type": "PRICE_CHANGE",
      "title": "삼성전자 급등",
      "message": "삼성전자가 3% 이상 상승했습니다",
      "severity": "INFO",
      "created_at": "2024-01-15T09:30:00Z",
      "symbol": "005930"
    }
  ],
  "market_overview": [
    {
      "symbol": "KOSPI",
      "name": "코스피",
      "current_price": 2580.0,
      "change_amount": 12.5,
      "change_rate": 0.48,
      "volume": 500000
    },
    {
      "symbol": "KOSDAQ",
      "name": "코스닥",
      "current_price": 850.0,
      "change_amount": -8.5,
      "change_rate": -0.99,
      "volume": 320000
    }
  ]
}
```

### 2. 성과 분석
**Request:**
```http
POST http://localhost:8000/api/dashboard/performance
Content-Type: application/json
Authorization: Bearer {{access_token}}

{
  "accessToken": "{{access_token}}",
  "sequence": 4003,
  "period": "3M",
  "benchmark": "KOSPI"
}
```

**Response:**
```json
{
  "errorCode": 0,
  "sequence": 4003,
  "performance_metrics": {
    "total_return": 8.5,
    "benchmark_return": 5.2,
    "excess_return": 3.3,
    "sharpe_ratio": 1.2,
    "max_drawdown": -8.5,
    "volatility": 15.3,
    "win_rate": 0.65,
    "profit_factor": 1.8
  },
  "monthly_returns": [
    {"month": "2023-11", "return": 2.5},
    {"month": "2023-12", "return": 3.2},
    {"month": "2024-01", "return": 2.8}
  ],
  "sector_allocation": [
    {"sector": "IT", "weight": 45.0, "return": 12.5},
    {"sector": "FINANCE", "weight": 25.0, "return": 5.8},
    {"sector": "INDUSTRIAL", "weight": 20.0, "return": 3.2},
    {"sector": "CONSUMER", "weight": 10.0, "return": 7.1}
  ]
}
```

---

## 🟣 Portfolio APIs
# 포트폴리오 조회 (REQ-PORT-001~007)
# 의거: 화면 006 (포트폴리오), REQ-PORT-001~007

### 1. 포트폴리오 조회
**Request:**
```http
POST http://localhost:8000/api/portfolio/get
Content-Type: application/json
Authorization: Bearer {{access_token}}

{
  "accessToken": "{{access_token}}",
  "sequence": 5001,
  "include_performance": true,
  "include_holdings": true
}
```

**Response:**
```json
{
  "errorCode": 0,
  "sequence": 5001,
  "portfolio": {
    "portfolio_id": "port_12345",
    "name": "메인 포트폴리오",
    "total_value": 10000.0,
    "cash_balance": 5000.0,
    "invested_amount": 5000.0,
    "total_return": 500.0,
    "return_rate": 5.0,
    "created_at": "2024-01-15T09:30:00Z",
    "last_updated": "2024-01-15T09:30:00Z"
  },
  "holdings": [],
  "performance": {
    "total_return": 500.0,
    "annualized_return": 15.0,
    "sharpe_ratio": 1.2,
    "max_drawdown": -5.0,
    "win_rate": 60.0,
    "profit_factor": 1.5
  }
}
```

### 2. 종목 추가
**Request:**
```http
POST http://localhost:8000/api/portfolio/add-stock
Content-Type: application/json
Authorization: Bearer {{access_token}}

{
  "accessToken": "{{access_token}}",
  "sequence": 5002,
  "symbol": "005930",
  "quantity": 10,
  "price": 75000.0,
  "order_type": "MARKET"
}
```

**Response:**
```json
{
  "errorCode": 0,
  "sequence": 5002,
  "trade": {
    "trade_id": "trade_12345_abcdef123456",
    "symbol": "005930",
    "name": "삼성전자",
    "action": "BUY",
    "quantity": 10,
    "price": 75000.0,
    "total_amount": 750000.0,
    "fees": 7500.0,
    "executed_at": "2024-01-15T09:30:00Z",
    "status": "COMPLETED"
  },
  "portfolio_update": {
    "portfolio_id": "port_12345",
    "updated_total_value": 10000.0,
    "updated_cash_balance": 5000.0,
    "position_added": true
  }
}
```

### 3. 리밸런싱 분석
**Request:**
```http
POST http://localhost:8000/api/portfolio/rebalance
Content-Type: application/json
Authorization: Bearer {{access_token}}

{
  "accessToken": "{{access_token}}",
  "sequence": 5004,
  "target_allocation": {
    "005930": 0.4,
    "000660": 0.3,
    "035420": 0.2,
    "005380": 0.1
  },
  "min_trade_amount": 50000.0
}
```

**Response:**
```json
{
  "errorCode": 0,
  "sequence": 5004,
  "report": {
    "report_id": "rebal_abc123",
    "trigger_reason": "USER_REQUEST",
    "recommendations": [
      {
        "action": "SELL",
        "symbol": "005930",
        "quantity": 5,
        "current_weight": 60.0,
        "target_weight": 40.0,
        "reason": "목표 비중 조정"
      },
      {
        "action": "BUY",
        "symbol": "000660",
        "quantity": 2,
        "current_weight": 10.0,
        "target_weight": 30.0,
        "reason": "목표 비중 조정"
      }
    ],
    "expected_improvement": 2.5,
    "generated_at": "2024-01-15T09:30:00Z"
  },
  "trades_required": [
    {
      "symbol": "005930",
      "action": "SELL",
      "quantity": 5,
      "estimated_price": 150.0
    },
    {
      "symbol": "000660",
      "action": "BUY",
      "quantity": 2,
      "estimated_price": 100.0
    }
  ],
  "estimated_cost": 15.0
}
```

---

## 🤖 Chat APIs
# AI 채팅 기본 기능 (REQ-CHAT-001~013)
# 의거: 화면 007 (AI 채팅), REQ-CHAT-001~013

### 1. 채팅방 생성
**Request:**
```http
POST http://localhost:8000/api/chat/room/create
Content-Type: application/json
Authorization: Bearer {{access_token}}

{
  "accessToken": "{{access_token}}",
  "sequence": 6002,
  "ai_persona": "GPT4O",
  "title": "삼성전자 투자 분석"
}
```

**Response:**
```json
{
  "errorCode": 0,
  "sequence": 6002,
  "room": {
    "room_id": "room_12345_1",
    "title": "삼성전자 투자 분석",
    "ai_persona": "GPT4O",
    "created_at": "2024-01-15T09:30:00Z",
    "message_count": 1,
    "last_message_at": "2024-01-15T09:30:00Z"
  },
  "welcome_message": {
    "message_id": "msg_12345_abcdef123456",
    "sender_type": "AI",
    "content": "안녕하세요! 투자 분석 AI입니다. 어떤 종목에 대해 궁금하신가요?",
    "timestamp": "2024-01-15T09:30:00Z"
  }
}
```

### 2. 메시지 전송
**Request:**
```http
POST http://localhost:8000/api/chat/message/send
Content-Type: application/json
Authorization: Bearer {{access_token}}

{
  "accessToken": "{{access_token}}",
  "sequence": 6003,
  "room_id": "room_abc123",
  "content": "삼성전자의 최근 실적과 향후 전망을 분석해주세요",
  "include_portfolio": true,
  "analysis_symbols": ["005930"]
}
```

**Response:**
```json
{
  "errorCode": 0,
  "sequence": 6003,
  "message": {
    "message_id": "msg_12345_user001",
    "room_id": "room_12345_1",
    "sender_type": "USER",
    "content": "삼성전자의 최근 실적과 향후 전망을 분석해주세요",
    "timestamp": "2024-01-15T09:30:00Z"
  },
  "ai_response": {
    "message_id": "msg_12345_ai001",
    "sender_type": "AI",
    "content": "삼성전자(005930) 분석 결과를 말씀드리겠습니다.\n\n**최근 실적 분석**\n- 2023년 4분기 매출: 67조원 (전년 동기 대비 +3.8%)\n- 영업이익: 2.8조원 (전년 동기 대비 +164.3%)\n- 메모리 반도체 수요 회복으로 실적 개선\n\n**향후 전망**\n- AI 및 서버용 메모리 수요 증가 예상\n- 중국 시장 회복 기대\n- 목표주가: 85,000원 (현재 78,000원 대비 +9%)\n\n**투자 의견: 매수 추천**",
    "timestamp": "2024-01-15T09:30:05Z"
  },
  "analysis_results": [
    {
      "type": "SENTIMENT",
      "result": "POSITIVE",
      "confidence": 0.85,
      "explanation": "긍정적인 투자 관점을 보여줍니다."
    },
    {
      "type": "TECHNICAL",
      "result": "BULLISH",
      "confidence": 0.78,
      "explanation": "기술적 지표 상 상승 신호 확인"
    }
  ],
  "recommendations": [
    {
      "type": "PORTFOLIO_REBALANCE",
      "priority": "HIGH",
      "symbol": "005930",
      "action": "BUY",
      "reason": "기술적 분석 결과 상승 신호"
    }
  ]
}
```

### 3. 종목 분석
# AI 분석 기능 (REQ-CHAT-014~026)
# 의거: REQ-CHAT-014~026 (데이터 수집, AI 분석, 페르소나 적용)
**Request:**
```http
POST http://localhost:8000/api/chat/analysis
Content-Type: application/json
Authorization: Bearer {{access_token}}

{
  "accessToken": "{{access_token}}",
  "sequence": 6006,
  "symbols": ["005930", "000660", "035420"],
  "analysis_types": ["FUNDAMENTAL", "TECHNICAL", "SENTIMENT"],
  "include_news": true,
  "time_range": "1M"
}
```

**Response:**
```json
{
  "errorCode": 0,
  "sequence": 6006,
  "analysis_results": [
    {
      "symbol": "005930",
      "name": "삼성전자",
      "fundamental_analysis": {
        "score": 8.5,
        "confidence": 0.85,
        "per": 12.5,
        "pbr": 1.2,
        "roe": 9.8,
        "debt_ratio": 15.2,
        "summary": "실적 개선 및 성장성 양호"
      },
      "technical_analysis": {
        "score": 7.2,
        "confidence": 0.78,
        "rsi": 65.5,
        "macd": "BULLISH",
        "bollinger": "MIDDLE",
        "moving_average": "ABOVE_MA20",
        "summary": "단기 상승 모멘텀 확인"
      },
      "sentiment_analysis": {
        "score": 7.8,
        "confidence": 0.80,
        "news_sentiment": "POSITIVE",
        "social_sentiment": "NEUTRAL",
        "analyst_rating": "BUY",
        "summary": "긍정적 뉴스 및 애널리스트 평가"
      },
      "overall_recommendation": {
        "action": "BUY",
        "target_price": 85000.0,
        "confidence": 0.82,
        "risk_level": "MEDIUM",
        "time_horizon": "3M"
      }
    }
  ],
  "related_news": [
    {
      "title": "삼성전자, AI 반도체 수요 증가로 실적 개선 전망",
      "source": "매일경제",
      "published_at": "2024-01-15T08:00:00Z",
      "sentiment": "POSITIVE",
      "relevance": 0.95
    }
  ]
}
```

---

## ⚡ AutoTrade APIs
# 자동매매 관리 (REQ-AUTO-001~003)
# 의거: 화면 008-1,2 (자동매매), REQ-AUTO-001~003

### 1. 전략 목록
**Request:**
```http
POST http://localhost:8000/api/autotrade/strategy/list
Content-Type: application/json
Authorization: Bearer {{access_token}}

{
  "accessToken": "{{access_token}}",
  "sequence": 7001,
  "include_performance": true,
  "status_filter": "ACTIVE"
}
```

**Response:**
```json
{
  "errorCode": 0,
  "sequence": 7001,
  "strategies": [
    {
      "strategy_id": "strat_12345_1",
      "name": "RSI 역추세 전략",
      "description": "RSI 과매수/과매도 구간에서의 역추세 매매",
      "algorithm_type": "MEAN_REVERSION",
      "target_symbols": ["005930", "000660"],
      "is_active": true,
      "created_at": "2024-01-15T09:30:00Z"
    },
    {
      "strategy_id": "strat_12345_2",
      "name": "모멘텀 전략",
      "description": "이동평균 교차 기반 모멘텀 매매",
      "algorithm_type": "MOMENTUM",
      "target_symbols": ["035420", "005380"],
      "is_active": false,
      "created_at": "2024-01-10T09:30:00Z"
    }
  ],
  "performances": {
    "strat_12345_1": {
      "strategy_id": "strat_12345_1",
      "total_return": 12.5,
      "win_rate": 65.0,
      "sharpe_ratio": 1.2,
      "max_drawdown": -8.5
    },
    "strat_12345_2": {
      "strategy_id": "strat_12345_2",
      "total_return": 8.3,
      "win_rate": 58.0,
      "sharpe_ratio": 0.9,
      "max_drawdown": -12.1
    }
  },
  "total_count": 2,
  "active_count": 1
}
```

### 2. 전략 생성
**Request:**
```http
POST http://localhost:8000/api/autotrade/strategy/create
Content-Type: application/json
Authorization: Bearer {{access_token}}

{
  "accessToken": "{{access_token}}",
  "sequence": 7002,
  "name": "이동평균 교차 전략",
  "description": "20일선과 50일선 교차를 이용한 매매 전략",
  "algorithm_type": "MOMENTUM",
  "parameters": {
    "fast_ma": 20,
    "slow_ma": 50,
    "volume_filter": true
  },
  "target_symbols": ["005930", "000660", "035420"],
  "max_position_size": 0.1,
  "stop_loss": -0.05,
  "take_profit": 0.15
}
```

**Response:**
```json
{
  "errorCode": 0,
  "sequence": 7002,
  "strategy": {
    "strategy_id": "strat_12345_3",
    "name": "이동평균 교차 전략",
    "description": "20일선과 50일선 교차를 이용한 매매 전략",
    "algorithm_type": "MOMENTUM",
    "parameters": {
      "fast_ma": 20,
      "slow_ma": 50,
      "volume_filter": true
    },
    "target_symbols": ["005930", "000660", "035420"],
    "max_position_size": 0.1,
    "stop_loss": -0.05,
    "take_profit": 0.15,
    "is_active": false,
    "created_at": "2024-01-15T09:30:00Z"
  }
}
```

### 3. 백테스트 실행
**Request:**
```http
POST http://localhost:8000/api/autotrade/backtest
Content-Type: application/json
Authorization: Bearer {{access_token}}

{
  "accessToken": "{{access_token}}",
  "sequence": 7004,
  "strategy_id": "strategy_003",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_capital": 10000000.0,
  "benchmark": "KOSPI"
}
```

**Response:**
```json
{
  "errorCode": 0,
  "sequence": 7004,
  "backtest_result": {
    "backtest_id": "backtest_001",
    "strategy_id": "strategy_003",
    "period": {
      "start_date": "2024-01-01",
      "end_date": "2024-12-31"
    },
    "initial_capital": 10000000.0,
    "final_capital": 11250000.0,
    "total_return": 12.5,
    "benchmark_return": 8.3,
    "excess_return": 4.2,
    "sharpe_ratio": 1.4,
    "max_drawdown": -6.8,
    "volatility": 14.2,
    "win_rate": 0.68,
    "profit_factor": 1.8,
    "total_trades": 45,
    "avg_trade_return": 0.28,
    "max_winning_streak": 7,
    "max_losing_streak": 3
  },
  "trade_history": [
    {
      "date": "2024-01-15",
      "symbol": "005930",
      "action": "BUY",
      "quantity": 10,
      "price": 75000.0,
      "reason": "MA20 상향 돌파"
    },
    {
      "date": "2024-01-20",
      "symbol": "005930",
      "action": "SELL",
      "quantity": 10,
      "price": 78000.0,
      "reason": "익절 목표 달성"
    }
  ],
  "monthly_returns": [
    {"month": "2024-01", "return": 2.5},
    {"month": "2024-02", "return": 1.8}
  ]
}
```

---

## 📈 Market APIs
# 시장 데이터 조회
# 의거: 시장 데이터 도메인 (Market)

### 1. 종목 검색
**Request:**
```http
POST http://localhost:8000/api/market/security/search
Content-Type: application/json
Authorization: Bearer {{access_token}}

{
  "accessToken": "{{access_token}}",
  "sequence": 8001,
  "query": "삼성전자",
  "exchange": "KRX",
  "sector": "TECHNOLOGY",
  "limit": 10
}
```

**Response:**
```json
{
  "errorCode": 0,
  "sequence": 8001,
  "securities": [
    {
      "symbol": "005930",
      "name": "삼성전자",
      "exchange": "KRX",
      "sector": "TECHNOLOGY",
      "market_cap": 456000000000000,
      "current_price": 78000.0,
      "change": 1000.0,
      "change_percent": 1.30,
      "volume": 1500000,
      "description": "종합 전자 제품 제조업체"
    },
    {
      "symbol": "005935",
      "name": "삼성전자우",
      "exchange": "KRX",
      "sector": "TECHNOLOGY",
      "market_cap": 15000000000000,
      "current_price": 65000.0,
      "change": 500.0,
      "change_percent": 0.78,
      "volume": 45000,
      "description": "삼성전자 우선주"
    }
  ],
  "total_count": 2
}
```

### 2. 시세 조회
**Request:**
```http
POST http://localhost:8000/api/market/price
Content-Type: application/json
Authorization: Bearer {{access_token}}

{
  "accessToken": "{{access_token}}",
  "sequence": 8002,
  "symbols": ["005930", "000660", "035420"],
  "period": "1D",
  "interval": "1h"
}
```

**Response:**
```json
{
  "errorCode": 0,
  "sequence": 8002,
  "price_data": {
    "005930": [
      {
        "symbol": "005930",
        "close": 78000.0,
        "change": 1000.0,
        "change_percent": 1.30
      }
    ],
    "000660": [
      {
        "symbol": "000660",
        "close": 100000.0,
        "change": 500.0,
        "change_percent": 0.50
      }
    ],
    "035420": [
      {
        "symbol": "035420",
        "close": 320000.0,
        "change": -5000.0,
        "change_percent": -1.54
      }
    ]
  },
  "technical_indicators": {
    "005930": {
      "symbol": "005930",
      "rsi": 65.5,
      "macd": 1.2,
      "ma20": 76500.0
    },
    "000660": {
      "symbol": "000660",
      "rsi": 58.2,
      "macd": 0.8,
      "ma20": 99800.0
    },
    "035420": {
      "symbol": "035420",
      "rsi": 45.3,
      "macd": -0.5,
      "ma20": 315000.0
    }
  }
}
```

### 3. 시장 개요
**Request:**
```http
POST http://localhost:8000/api/market/overview
Content-Type: application/json
Authorization: Bearer {{access_token}}

{
  "accessToken": "{{access_token}}",
  "sequence": 8003,
  "indices": ["KOSPI", "KOSDAQ", "KRX100"],
  "include_movers": true
}
```

**Response:**
```json
{
  "errorCode": 0,
  "sequence": 8003,
  "market_indices": {
    "KOSPI": {
      "current": 2650.5,
      "change": 15.2,
      "change_percent": 0.58,
      "volume": 450000000,
      "high": 2655.8,
      "low": 2640.2,
      "previous_close": 2635.3
    },
    "KOSDAQ": {
      "current": 850.3,
      "change": -5.8,
      "change_percent": -0.68,
      "volume": 680000000,
      "high": 855.1,
      "low": 848.5,
      "previous_close": 856.1
    },
    "KRX100": {
      "current": 5250.8,
      "change": 25.3,
      "change_percent": 0.48,
      "volume": 120000000,
      "high": 5260.5,
      "low": 5240.2,
      "previous_close": 5225.5
    }
  },
  "top_gainers": [
    {
      "symbol": "123456",
      "name": "상승종목1",
      "current_price": 12000.0,
      "change_percent": 15.5,
      "volume": 2500000
    },
    {
      "symbol": "234567",
      "name": "상승종목2",
      "current_price": 8500.0,
      "change_percent": 12.3,
      "volume": 1800000
    }
  ],
  "top_losers": [
    {
      "symbol": "345678",
      "name": "하락종목1",
      "current_price": 5500.0,
      "change_percent": -8.2,
      "volume": 3200000
    },
    {
      "symbol": "456789",
      "name": "하락종목2",
      "current_price": 15000.0,
      "change_percent": -6.5,
      "volume": 1500000
    }
  ],
  "market_summary": {
    "total_traded_value": 12500000000000,
    "advancing_issues": 456,
    "declining_issues": 378,
    "unchanged_issues": 123,
    "new_highs": 25,
    "new_lows": 18
  }
}
```

---

## ⚙️ Settings APIs
# 설정 조회/수정 (REQ-SET-001~010)
# 의거: 화면 009-1~6 (설정), REQ-SET-001~010

### 1. 설정 조회
**Request:**
```http
POST http://localhost:8000/api/settings/get
Content-Type: application/json
Authorization: Bearer {{access_token}}

{
  "accessToken": "{{access_token}}",
  "sequence": 9001,
  "section": "NOTIFICATION"
}
```

**Response:**
```json
{
  "errorCode": 0,
  "sequence": 9001,
  "settings": {
    "general": {
      "theme": "DARK",
      "language": "KO",
      "currency": "KRW",
      "timezone": "Asia/Seoul"
    },
    "investment": {
      "investment_experience": "INTERMEDIATE",
      "risk_tolerance": "MODERATE",
      "investment_goal": "GROWTH",
      "monthly_budget": 2000000.0,
      "auto_rebalance": true
    },
    "notification": {
      "price_alerts": true,
      "news_alerts": true,
      "portfolio_alerts": true,
      "trade_alerts": false,
      "email_notifications": true,
      "push_notifications": true,
      "price_change_threshold": 0.05,
      "alert_frequency": "REALTIME"
    },
    "security": {
      "otp_enabled": true,
      "device_trust_enabled": true,
      "session_timeout": 30,
      "login_alerts": true,
      "ip_whitelist_enabled": false
    },
    "trading": {
      "auto_trading_enabled": false,
      "max_position_size": 0.1,
      "default_order_type": "LIMIT",
      "confirm_trades": true
    }
  }
}
```

### 2. 설정 업데이트
**Request:**
```http
POST http://localhost:8000/api/settings/update
Content-Type: application/json
Authorization: Bearer {{access_token}}

{
  "accessToken": "{{access_token}}",
  "sequence": 9002,
  "section": "NOTIFICATION",
  "settings": {
    "price_alerts": true,
    "news_alerts": true,
    "portfolio_alerts": true,
    "trade_alerts": false,
    "email_notifications": true,
    "push_notifications": true,
    "price_change_threshold": 0.03,
    "alert_frequency": "HOURLY"
  }
}
```

**Response:**
```json
{
  "errorCode": 0,
  "sequence": 9002,
  "message": "알림 설정이 성공적으로 업데이트되었습니다",
  "updated_settings": {
    "price_alerts": true,
    "news_alerts": true,
    "portfolio_alerts": true,
    "trade_alerts": false,
    "email_notifications": true,
    "push_notifications": true,
    "price_change_threshold": 0.03,
    "alert_frequency": "HOURLY"
  },
  "updated_at": "2024-01-15T09:30:00Z"
}
```

### 3. 비밀번호 변경
**Request:**
```http
POST http://localhost:8000/api/settings/password/change
Content-Type: application/json
Authorization: Bearer {{access_token}}

{
  "accessToken": "{{access_token}}",
  "sequence": 9005,
  "current_password": "TestPassword123!",
  "new_password": "NewPassword456!",
  "otp_code": "123456"
}
```

**Response:**
```json
{
  "errorCode": 0,
  "sequence": 9005,
  "message": "비밀번호가 성공적으로 변경되었습니다",
  "password_changed_at": "2024-01-15T09:30:00Z",
  "security_notice": "보안을 위해 모든 기기에서 다시 로그인해주세요"
}
```

---

## 🔔 Notification APIs
# 알림 관리
# 의거: 알림 도메인 (Notification)

### 1. 알림 목록
**Request:**
```http
POST http://localhost:8000/api/notification/list
Content-Type: application/json
Authorization: Bearer {{access_token}}

{
  "accessToken": "{{access_token}}",
  "sequence": 10001,
  "type_filter": "PRICE_ALERT",
  "read_status": "UNREAD",
  "page": 1,
  "limit": 20
}
```

**Response:**
```json
{
  "errorCode": 0,
  "sequence": 10001,
  "notifications": [
    {
      "notification_id": "notif_12345_1",
      "type": "PRICE_ALERT",
      "title": "005930 가격 알림",
      "message": "005930 주가가 $150을 넘었습니다",
      "symbol": "005930",
      "price": 152.0,
      "is_read": false,
      "created_at": "2024-01-15T09:30:00Z",
      "priority": "HIGH"
    },
    {
      "notification_id": "notif_12345_2",
      "type": "NEWS_ALERT",
      "title": "뉴스 알림",
      "message": "삼성전자 관련 중요 뉴스가 등록되었습니다",
      "symbol": "005930",
      "price": 78000.0,
      "is_read": false,
      "created_at": "2024-01-15T09:25:00Z",
      "priority": "MEDIUM"
    }
  ],
  "total_count": 2,
  "unread_count": 2,
  "has_more": false
}
```

### 2. 알림 생성
**Request:**
```http
POST http://localhost:8000/api/notification/create-alert
Content-Type: application/json
Authorization: Bearer {{access_token}}

{
  "accessToken": "{{access_token}}",
  "sequence": 10003,
  "symbol": "005930",
  "alert_type": "PRICE_ABOVE",
  "target_value": 80000.0,
  "message": "삼성전자 주가가 목표가 80,000원을 돌파했습니다!"
}
```

**Response:**
```json
{
  "errorCode": 0,
  "sequence": 10003,
  "alert": {
    "alert_id": "alert_12345_abcdef123456",
    "symbol": "005930",
    "alert_type": "PRICE_ABOVE",
    "target_value": 80000.0,
    "current_value": 78000.0,
    "message": "삼성전자 주가가 목표가 80,000원을 돌파했습니다!",
    "is_active": true,
    "created_at": "2024-01-15T09:30:00Z"
  }
}
```

### 3. 알림 읽음 처리
**Request:**
```http
POST http://localhost:8000/api/notification/mark-read
Content-Type: application/json
Authorization: Bearer {{access_token}}

{
  "accessToken": "{{access_token}}",
  "sequence": 10002,
  "notification_ids": ["notif_001", "notif_002", "notif_003"]
}
```

**Response:**
```json
{
  "errorCode": 0,
  "sequence": 10002,
  "updated_count": 3,
  "updated_notifications": [
    "notif_12345_1",
    "notif_12345_2", 
    "notif_12345_3"
  ]
}
```

---

## 🎯 공통 에러 응답

### 인증 실패 (401)
```json
{
  "errorCode": 1001,
  "sequence": 1001,
  "message": "인증 토큰이 만료되었습니다",
  "error_details": {
    "error_type": "TOKEN_EXPIRED",
    "retry_after": 0,
    "requires_login": true
  }
}
```

### 권한 부족 (403)
```json
{
  "errorCode": 1003,
  "sequence": 1002,
  "message": "해당 기능에 대한 권한이 없습니다",
  "error_details": {
    "error_type": "ACCESS_DENIED",
    "required_level": "PREMIUM"
  }
}
```

### 잘못된 요청 (400)
```json
{
  "errorCode": 1005,
  "sequence": 1003,
  "message": "필수 파라미터가 누락되었습니다",
  "error_details": {
    "error_type": "INVALID_PARAMETER",
    "missing_fields": ["symbol", "quantity"]
  }
}
```

### 서버 오류 (500)
```json
{
  "errorCode": 5001,
  "sequence": 1004,
  "message": "일시적인 서버 오류가 발생했습니다",
  "error_details": {
    "error_type": "INTERNAL_SERVER_ERROR",
    "retry_after": 30
  }
}
```

---

## 🎯 Postman 환경 변수 설정

### Environment Variables
```json
{
  "base_url": "http://localhost:8000",
  "access_token": "",
  "refresh_token": "",
  "user_id": "",
  "session_id": "",
  "room_id": "",
  "strategy_id": "",
  "sequence": 1000
}
```

### 사용 팁
1. **토큰 관리**: 로그인 후 받은 토큰을 환경변수에 저장하여 재사용
2. **시퀀스 관리**: 각 요청마다 sequence 값을 증가시켜 사용
3. **에러 처리**: errorCode가 0이 아닌 경우 에러 메시지 확인
4. **페이지네이션**: 목록 조회 시 page와 limit 파라미터 활용

이 문서의 모든 예시는 복사해서 Postman에서 바로 사용할 수 있습니다!