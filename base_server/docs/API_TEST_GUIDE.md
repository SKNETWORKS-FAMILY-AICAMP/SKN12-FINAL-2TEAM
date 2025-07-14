# 📋 **Base Web Server API 테스트 가이드**

## 🚀 **테스트 환경 설정**

### **서버 실행**
```bash
cd base_server
uvicorn application.base_web_server.main:app --reload --host 0.0.0.0 --port 8000
```

### **기본 URL**
```
http://localhost:8000
```

### **PostAPI Environment 설정**
```json
{
  "base_url": "http://localhost:8000",
  "access_token": ""
}
```

---

## 📝 **API 테스트 순서 (의존성 고려)**

### **1단계: 서버 상태 확인**

#### 1.1 서버 기본 상태
**Request:**
```http
GET {{base_url}}/
```

**Expected Response:**
```json
{
  "server": "base_web_server",
  "status": "running",
  "message": "base_web_server 동작 중",
  "log_level": "INFO",
  "env": "LOCAL",
  "config_file": "base_web_server-config_local.json",
  "services": {
    "database_initialized": true,
    "cache_service_initialized": true,
    "lock_service_initialized": true,
    "scheduler_service_initialized": true,
    "queue_service_initialized": true,
    "external": true,
    "storage": true,
    "search": true,
    "vectordb": true
  }
}
```

#### 1.2 Admin 서버 생존 확인
**Request:**
```http
GET {{base_url}}/api/admin/ping
```

**Expected Response:**
```json
{
  "status": "pong",
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

#### 1.3 Admin 헬스체크
**Request:**
```http
POST {{base_url}}/api/admin/healthcheck
Content-Type: application/json

{
  "check_type": "all"
}
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-14T12:34:56.789Z",
  "services": {
    "database": {
      "status": "healthy",
      "response_time": "45.67ms",
      "details": "Connection test successful"
    },
    "cache": {
      "status": "healthy",
      "response_time": "12.34ms",
      "details": "Redis connection successful"
    },
    "services": {
      "status": "healthy",
      "services": {
        "lock_service": "healthy",
        "scheduler_service": "healthy",
        "queue_service": "healthy",
        "cache_service": "healthy"
      },
      "details": "Services: 4 healthy, 0 unhealthy, 0 not configured"
    }
  },
  "error_code": 0
}
```

#### 1.4 Admin 빠른 테스트
**Request:**
```http
POST {{base_url}}/api/admin/quicktest
Content-Type: application/json

{
  "test_types": ["cache", "database", "queue", "lock"]
}
```

**Expected Response:**
```json
{
  "results": {
    "cache": {
      "status": "passed",
      "details": "Cache read/write successful"
    },
    "database": {
      "status": "passed",
      "details": "Database connection successful"
    },
    "queue": {
      "status": "passed",
      "details": "Queue service operational, processed: 0"
    },
    "lock": {
      "status": "passed",
      "details": "Lock service operational"
    }
  },
  "summary": {
    "total": 4,
    "passed": 4,
    "failed": 0
  },
  "timestamp": "2025-01-14T12:34:56.789Z",
  "error_code": 0
}
```

---

### **2단계: 계정 관리 (Account API)**

#### 2.1 회원가입
**Request:**
```http
POST {{base_url}}/api/account/signup
Content-Type: application/json

{
  "email": "test@example.com",
  "password": "Test123!@#",
  "confirm_password": "Test123!@#",
  "username": "testuser",
  "phone": "010-1234-5678"
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "user_id": "user_123456",
    "email": "test@example.com",
    "username": "testuser",
    "status": "pending_verification",
    "created_at": "2025-01-14T12:34:56.789Z"
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

#### 2.2 이메일 인증 요청
**Request:**
```http
POST {{base_url}}/api/account/email/verify
Content-Type: application/json

{
  "email": "test@example.com"
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "email": "test@example.com",
    "verification_sent": true,
    "expires_at": "2025-01-14T12:44:56.789Z"
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

#### 2.3 이메일 인증 확인
**Request:**
```http
POST {{base_url}}/api/account/email/confirm
Content-Type: application/json

{
  "email": "test@example.com",
  "verification_code": "123456"
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "email": "test@example.com",
    "verified": true,
    "verified_at": "2025-01-14T12:34:56.789Z"
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

#### 2.4 로그인 (세션 생성) ⭐ **토큰 저장 필요**
**Request:**
```http
POST {{base_url}}/api/account/login
Content-Type: application/json

{
  "email": "test@example.com",
  "password": "Test123!@#"
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "refresh_token_here",
    "user_id": "user_123456",
    "email": "test@example.com",
    "username": "testuser",
    "expires_at": "2025-01-14T20:34:56.789Z",
    "shard_id": 1
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

**PostAPI Test Script:**
```javascript
if (pm.response.code === 200) {
    const response = pm.response.json();
    if (response.data && response.data.access_token) {
        pm.environment.set("access_token", response.data.access_token);
        console.log("Access token saved:", response.data.access_token);
    }
}
```

#### 2.5 프로필 설정
**Request:**
```http
POST {{base_url}}/api/account/profile/setup
Content-Type: application/json

{
  "access_token": "{{access_token}}",
  "first_name": "홍",
  "last_name": "길동",
  "birth_date": "1990-01-01",
  "investment_experience": "beginner",
  "risk_tolerance": "moderate",
  "annual_income": "50000000"
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "profile_id": "profile_123456",
    "user_id": "user_123456",
    "first_name": "홍",
    "last_name": "길동",
    "birth_date": "1990-01-01",
    "investment_experience": "beginner",
    "risk_tolerance": "moderate",
    "annual_income": "50000000",
    "profile_completed": true,
    "created_at": "2025-01-14T12:34:56.789Z"
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

#### 2.6 프로필 조회
**Request:**
```http
POST {{base_url}}/api/account/profile/get
Content-Type: application/json

{
  "access_token": "{{access_token}}"
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "profile_id": "profile_123456",
    "user_id": "user_123456",
    "first_name": "홍",
    "last_name": "길동",
    "birth_date": "1990-01-01",
    "investment_experience": "beginner",
    "risk_tolerance": "moderate",
    "annual_income": "50000000",
    "profile_completed": true,
    "created_at": "2025-01-14T12:34:56.789Z",
    "updated_at": "2025-01-14T12:34:56.789Z"
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

#### 2.7 사용자 정보 조회
**Request:**
```http
POST {{base_url}}/api/account/info
Content-Type: application/json

{
  "access_token": "{{access_token}}"
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "user_id": "user_123456",
    "email": "test@example.com",
    "username": "testuser",
    "phone": "010-1234-5678",
    "status": "active",
    "email_verified": true,
    "phone_verified": false,
    "otp_enabled": false,
    "profile_completed": true,
    "last_login": "2025-01-14T12:34:56.789Z",
    "created_at": "2025-01-14T12:30:00.000Z"
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

---

### **3단계: 튜토리얼 (Tutorial API)**

#### 3.1 튜토리얼 목록
**Request:**
```http
POST {{base_url}}/api/tutorial/list
Content-Type: application/json

{
  "access_token": "{{access_token}}"
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "tutorials": [
      {
        "tutorial_id": "basic_trading",
        "title": "기본 거래 방법",
        "description": "주식 거래의 기본을 배워보세요",
        "difficulty": "beginner",
        "estimated_time": 10,
        "status": "not_started",
        "progress": 0
      },
      {
        "tutorial_id": "portfolio_management",
        "title": "포트폴리오 관리",
        "description": "효과적인 포트폴리오 관리 방법",
        "difficulty": "intermediate",
        "estimated_time": 15,
        "status": "not_started",
        "progress": 0
      }
    ]
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

#### 3.2 튜토리얼 시작
**Request:**
```http
POST {{base_url}}/api/tutorial/start
Content-Type: application/json

{
  "access_token": "{{access_token}}",
  "tutorial_id": "basic_trading"
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "tutorial_id": "basic_trading",
    "status": "in_progress",
    "progress": 0,
    "current_step": 1,
    "total_steps": 5,
    "next_step": {
      "step_id": 1,
      "title": "거래 시장 이해하기",
      "content": "주식 시장의 기본 개념을 알아봅시다",
      "action_required": "read"
    },
    "started_at": "2025-01-14T12:34:56.789Z"
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

#### 3.3 튜토리얼 진행상황
**Request:**
```http
POST {{base_url}}/api/tutorial/progress
Content-Type: application/json

{
  "access_token": "{{access_token}}",
  "tutorial_id": "basic_trading"
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "tutorial_id": "basic_trading",
    "status": "in_progress",
    "progress": 40,
    "current_step": 2,
    "total_steps": 5,
    "completed_steps": [1],
    "next_step": {
      "step_id": 2,
      "title": "주문 방법 배우기",
      "content": "매수와 매도 주문을 넣는 방법",
      "action_required": "practice"
    }
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

#### 3.4 튜토리얼 완료
**Request:**
```http
POST {{base_url}}/api/tutorial/complete
Content-Type: application/json

{
  "access_token": "{{access_token}}",
  "tutorial_id": "basic_trading"
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "tutorial_id": "basic_trading",
    "status": "completed",
    "progress": 100,
    "completed_at": "2025-01-14T12:34:56.789Z",
    "reward": {
      "type": "badge",
      "name": "기본 거래 마스터",
      "points": 100
    },
    "next_recommended": "portfolio_management"
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

---

### **4단계: 시장 데이터 (Market API)**

#### 4.1 종목 검색
**Request:**
```http
POST {{base_url}}/api/market/security/search
Content-Type: application/json

{
  "access_token": "{{access_token}}",
  "query": "삼성전자",
  "limit": 10
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "query": "삼성전자",
    "results": [
      {
        "symbol": "005930",
        "name": "삼성전자",
        "market": "KOSPI",
        "sector": "기술",
        "current_price": 75000,
        "change": 1000,
        "change_percent": 1.35,
        "volume": 15234567,
        "market_cap": 450000000000000
      }
    ],
    "total_count": 1
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

#### 4.2 시장 개요
**Request:**
```http
POST {{base_url}}/api/market/overview
Content-Type: application/json

{
  "access_token": "{{access_token}}"
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "markets": {
      "KOSPI": {
        "index": 2650.45,
        "change": 15.67,
        "change_percent": 0.59,
        "volume": 456789123,
        "status": "open"
      },
      "KOSDAQ": {
        "index": 875.32,
        "change": -5.23,
        "change_percent": -0.59,
        "volume": 234567891,
        "status": "open"
      }
    },
    "top_gainers": [
      {
        "symbol": "005930",
        "name": "삼성전자",
        "change_percent": 3.45
      }
    ],
    "top_losers": [
      {
        "symbol": "000660",
        "name": "SK하이닉스",
        "change_percent": -2.15
      }
    ],
    "most_active": [
      {
        "symbol": "005930",
        "name": "삼성전자",
        "volume": 15234567
      }
    ]
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

#### 4.3 가격 정보
**Request:**
```http
POST {{base_url}}/api/market/price
Content-Type: application/json

{
  "access_token": "{{access_token}}",
  "symbol": "005930",
  "period": "1d"
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "symbol": "005930",
    "name": "삼성전자",
    "current_price": 75000,
    "open_price": 74000,
    "high_price": 75500,
    "low_price": 73500,
    "close_price": 75000,
    "volume": 15234567,
    "change": 1000,
    "change_percent": 1.35,
    "market_cap": 450000000000000,
    "pe_ratio": 15.2,
    "pb_ratio": 1.1,
    "dividend_yield": 2.5,
    "52_week_high": 82000,
    "52_week_low": 58000,
    "chart_data": [
      {
        "timestamp": "2025-01-14T09:00:00Z",
        "open": 74000,
        "high": 74200,
        "low": 73800,
        "close": 74100,
        "volume": 1000000
      }
    ]
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

#### 4.4 시장 뉴스
**Request:**
```http
POST {{base_url}}/api/market/news
Content-Type: application/json

{
  "access_token": "{{access_token}}",
  "category": "market",
  "limit": 20
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "news": [
      {
        "news_id": "news_123456",
        "title": "삼성전자, 신규 반도체 공장 건설 발표",
        "summary": "삼성전자가 평택에 새로운 반도체 공장을 건설한다고 발표했습니다",
        "url": "https://news.example.com/123456",
        "source": "경제신문",
        "published_at": "2025-01-14T10:30:00Z",
        "category": "market",
        "related_symbols": ["005930"],
        "sentiment": "positive"
      }
    ],
    "total_count": 156
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

---

### **5단계: 포트폴리오 관리 (Portfolio API)**

#### 5.1 포트폴리오 조회
**Request:**
```http
POST {{base_url}}/api/portfolio/get
Content-Type: application/json

{
  "access_token": "{{access_token}}"
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "portfolio_id": "portfolio_123456",
    "user_id": "user_123456",
    "total_value": 10000000,
    "total_cost": 9500000,
    "total_return": 500000,
    "return_percent": 5.26,
    "cash_balance": 2000000,
    "holdings": [],
    "asset_allocation": {
      "stocks": 80.0,
      "cash": 20.0
    },
    "created_at": "2025-01-14T12:34:56.789Z",
    "updated_at": "2025-01-14T12:34:56.789Z"
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

#### 5.2 종목 추가
**Request:**
```http
POST {{base_url}}/api/portfolio/add-stock
Content-Type: application/json

{
  "access_token": "{{access_token}}",
  "symbol": "005930",
  "quantity": 10,
  "price": 75000
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "transaction_id": "txn_123456",
    "portfolio_id": "portfolio_123456",
    "symbol": "005930",
    "name": "삼성전자",
    "quantity": 10,
    "price": 75000,
    "total_cost": 750000,
    "transaction_type": "buy",
    "executed_at": "2025-01-14T12:34:56.789Z",
    "portfolio_summary": {
      "total_value": 10750000,
      "cash_balance": 1250000,
      "total_return": 500000,
      "return_percent": 4.88
    }
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

#### 5.3 포트폴리오 성과 분석
**Request:**
```http
POST {{base_url}}/api/portfolio/performance
Content-Type: application/json

{
  "access_token": "{{access_token}}",
  "period": "1m"
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "portfolio_id": "portfolio_123456",
    "period": "1m",
    "start_date": "2024-12-14",
    "end_date": "2025-01-14",
    "start_value": 10000000,
    "end_value": 10750000,
    "total_return": 750000,
    "return_percent": 7.5,
    "benchmark_return": 5.2,
    "alpha": 2.3,
    "beta": 1.1,
    "sharpe_ratio": 1.2,
    "max_drawdown": -3.5,
    "volatility": 12.8,
    "performance_chart": [
      {
        "date": "2024-12-14",
        "portfolio_value": 10000000,
        "benchmark_value": 10000000
      },
      {
        "date": "2025-01-14",
        "portfolio_value": 10750000,
        "benchmark_value": 10520000
      }
    ]
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

#### 5.4 리밸런싱
**Request:**
```http
POST {{base_url}}/api/portfolio/rebalance
Content-Type: application/json

{
  "access_token": "{{access_token}}",
  "target_allocation": {
    "005930": 40,
    "000660": 30,
    "035420": 30
  }
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "rebalance_id": "rebal_123456",
    "portfolio_id": "portfolio_123456",
    "target_allocation": {
      "005930": 40,
      "000660": 30,
      "035420": 30
    },
    "current_allocation": {
      "005930": 70,
      "cash": 30
    },
    "required_trades": [
      {
        "symbol": "005930",
        "action": "sell",
        "quantity": 5,
        "estimated_value": 375000
      },
      {
        "symbol": "000660",
        "action": "buy",
        "quantity": 3,
        "estimated_value": 322500
      },
      {
        "symbol": "035420",
        "action": "buy",
        "quantity": 1,
        "estimated_value": 322500
      }
    ],
    "estimated_cost": 15000,
    "status": "pending",
    "created_at": "2025-01-14T12:34:56.789Z"
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

---

### **6단계: 대시보드 (Dashboard API)**

#### 6.1 메인 대시보드
**Request:**
```http
POST {{base_url}}/api/dashboard/main
Content-Type: application/json

{
  "access_token": "{{access_token}}"
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "user_summary": {
      "total_assets": 10750000,
      "daily_return": 50000,
      "daily_return_percent": 0.47,
      "portfolio_count": 1
    },
    "market_summary": {
      "kospi": {
        "value": 2650.45,
        "change": 15.67,
        "change_percent": 0.59
      },
      "kosdaq": {
        "value": 875.32,
        "change": -5.23,
        "change_percent": -0.59
      }
    },
    "top_holdings": [
      {
        "symbol": "005930",
        "name": "삼성전자",
        "quantity": 10,
        "current_value": 750000,
        "return_percent": 1.35
      }
    ],
    "recent_news": [
      {
        "title": "삼성전자, 신규 반도체 공장 건설 발표",
        "published_at": "2025-01-14T10:30:00Z",
        "sentiment": "positive"
      }
    ],
    "alerts": [
      {
        "type": "price_alert",
        "message": "삼성전자가 목표가 75,000원에 도달했습니다",
        "timestamp": "2025-01-14T12:30:00Z"
      }
    ]
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

#### 6.2 알림 목록
**Request:**
```http
POST {{base_url}}/api/dashboard/alerts
Content-Type: application/json

{
  "access_token": "{{access_token}}"
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "alerts": [
      {
        "alert_id": "alert_123456",
        "type": "price_alert",
        "title": "가격 알림",
        "message": "삼성전자가 목표가 75,000원에 도달했습니다",
        "symbol": "005930",
        "priority": "medium",
        "read": false,
        "created_at": "2025-01-14T12:30:00Z"
      },
      {
        "alert_id": "alert_123457",
        "type": "news_alert",
        "title": "뉴스 알림",
        "message": "관심 종목 관련 중요 뉴스가 있습니다",
        "priority": "low",
        "read": true,
        "created_at": "2025-01-14T10:30:00Z"
      }
    ],
    "unread_count": 1,
    "total_count": 2
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

#### 6.3 성과 분석
**Request:**
```http
POST {{base_url}}/api/dashboard/performance
Content-Type: application/json

{
  "access_token": "{{access_token}}",
  "period": "1m"
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "period": "1m",
    "total_return": 750000,
    "return_percent": 7.5,
    "benchmark_return": 5.2,
    "outperformance": 2.3,
    "best_performer": {
      "symbol": "005930",
      "name": "삼성전자",
      "return_percent": 15.2
    },
    "worst_performer": null,
    "sector_allocation": {
      "technology": 70,
      "finance": 0,
      "healthcare": 0,
      "cash": 30
    },
    "risk_metrics": {
      "volatility": 12.8,
      "sharpe_ratio": 1.2,
      "max_drawdown": -3.5,
      "beta": 1.1
    }
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

---

### **7단계: 알림 관리 (Notification API)**

#### 7.1 알림 목록
**Request:**
```http
POST {{base_url}}/api/notification/list
Content-Type: application/json

{
  "access_token": "{{access_token}}"
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "notifications": [
      {
        "notification_id": "notif_123456",
        "type": "price_alert",
        "title": "가격 알림",
        "message": "삼성전자가 75,000원에 도달했습니다",
        "symbol": "005930",
        "read": false,
        "priority": "medium",
        "created_at": "2025-01-14T12:30:00Z"
      },
      {
        "notification_id": "notif_123457",
        "type": "news",
        "title": "뉴스 알림",
        "message": "삼성전자 관련 중요 뉴스가 발행되었습니다",
        "read": true,
        "priority": "low",
        "created_at": "2025-01-14T10:30:00Z"
      }
    ],
    "unread_count": 1,
    "total_count": 2
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

#### 7.2 가격 알림 생성
**Request:**
```http
POST {{base_url}}/api/notification/create-alert
Content-Type: application/json

{
  "access_token": "{{access_token}}",
  "symbol": "005930",
  "condition": "above",
  "price": 80000,
  "message": "삼성전자 8만원 돌파!"
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "alert_id": "alert_789012",
    "symbol": "005930",
    "name": "삼성전자",
    "condition": "above",
    "target_price": 80000,
    "current_price": 75000,
    "message": "삼성전자 8만원 돌파!",
    "status": "active",
    "created_at": "2025-01-14T12:34:56.789Z"
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

#### 7.3 알림 설정 목록
**Request:**
```http
POST {{base_url}}/api/notification/alert/list
Content-Type: application/json

{
  "access_token": "{{access_token}}"
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "alerts": [
      {
        "alert_id": "alert_789012",
        "symbol": "005930",
        "name": "삼성전자",
        "condition": "above",
        "target_price": 80000,
        "current_price": 75000,
        "status": "active",
        "created_at": "2025-01-14T12:34:56.789Z"
      }
    ],
    "active_count": 1,
    "total_count": 1
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

#### 7.4 알림 읽음 처리
**Request:**
```http
POST {{base_url}}/api/notification/mark-read
Content-Type: application/json

{
  "access_token": "{{access_token}}",
  "notification_ids": ["notif_123456", "notif_123457"]
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "processed_count": 2,
    "notification_ids": ["notif_123456", "notif_123457"],
    "remaining_unread": 0
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

---

### **8단계: 채팅/AI 상담 (Chat API)**

#### 8.1 채팅방 목록
**Request:**
```http
POST {{base_url}}/api/chat/rooms
Content-Type: application/json

{
  "access_token": "{{access_token}}"
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "rooms": [
      {
        "room_id": "room_123456",
        "room_name": "투자 상담",
        "ai_persona": "financial_advisor",
        "last_message": "포트폴리오 분석이 완료되었습니다",
        "last_message_at": "2025-01-14T11:30:00Z",
        "unread_count": 2,
        "created_at": "2025-01-14T10:00:00Z"
      }
    ],
    "total_count": 1
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

#### 8.2 새 채팅방 생성
**Request:**
```http
POST {{base_url}}/api/chat/room/create
Content-Type: application/json

{
  "access_token": "{{access_token}}",
  "room_name": "투자 상담",
  "ai_persona": "financial_advisor"
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "room_id": "room_789012",
    "room_name": "투자 상담",
    "ai_persona": "financial_advisor",
    "persona_info": {
      "name": "김투자",
      "description": "20년 경력의 투자 전문가",
      "specialties": ["포트폴리오 관리", "리스크 분석", "시장 분석"]
    },
    "welcome_message": "안녕하세요! 투자 관련 궁금한 점이 있으시면 언제든 물어보세요.",
    "created_at": "2025-01-14T12:34:56.789Z"
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

#### 8.3 메시지 전송
**Request:**
```http
POST {{base_url}}/api/chat/message/send
Content-Type: application/json

{
  "access_token": "{{access_token}}",
  "room_id": "room_789012",
  "message": "삼성전자에 투자해도 될까요?",
  "message_type": "text"
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "message_id": "msg_123456",
    "room_id": "room_789012",
    "sender": "user",
    "message": "삼성전자에 투자해도 될까요?",
    "message_type": "text",
    "sent_at": "2025-01-14T12:34:56.789Z",
    "ai_response": {
      "message_id": "msg_123457",
      "sender": "ai",
      "message": "삼성전자는 안정적인 대형주로 평가받고 있습니다. 현재 기술주 전반의 상승세와 반도체 업황 개선 기대감이 있어 긍정적입니다. 다만 투자 전 포트폴리오 전체의 균형을 고려해보시기 바랍니다.",
      "message_type": "text",
      "sent_at": "2025-01-14T12:34:57.123Z",
      "confidence": 0.85,
      "related_data": {
        "symbol": "005930",
        "current_price": 75000,
        "analyst_rating": "buy"
      }
    }
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

#### 8.4 메시지 조회
**Request:**
```http
POST {{base_url}}/api/chat/messages
Content-Type: application/json

{
  "access_token": "{{access_token}}",
  "room_id": "room_789012",
  "limit": 50
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "room_id": "room_789012",
    "messages": [
      {
        "message_id": "msg_123456",
        "sender": "user",
        "message": "삼성전자에 투자해도 될까요?",
        "message_type": "text",
        "sent_at": "2025-01-14T12:34:56.789Z"
      },
      {
        "message_id": "msg_123457",
        "sender": "ai",
        "message": "삼성전자는 안정적인 대형주로 평가받고 있습니다...",
        "message_type": "text",
        "sent_at": "2025-01-14T12:34:57.123Z",
        "confidence": 0.85
      }
    ],
    "total_count": 2,
    "has_more": false
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

#### 8.5 대화 요약
**Request:**
```http
POST {{base_url}}/api/chat/summary
Content-Type: application/json

{
  "access_token": "{{access_token}}",
  "room_id": "room_789012"
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "room_id": "room_789012",
    "summary": {
      "total_messages": 2,
      "conversation_period": "2025-01-14T12:34:56.789Z ~ 2025-01-14T12:34:57.123Z",
      "main_topics": [
        "삼성전자 투자 문의",
        "포트폴리오 균형"
      ],
      "ai_recommendations": [
        "삼성전자는 안정적인 투자처로 추천",
        "포트폴리오 전체 균형 고려 필요"
      ],
      "mentioned_symbols": ["005930"],
      "sentiment": "positive",
      "summary_text": "사용자가 삼성전자 투자에 대해 문의했고, AI는 긍정적인 평가와 함께 포트폴리오 균형을 고려하라고 조언했습니다."
    }
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

---

### **9단계: 자동매매 (AutoTrade API)**

#### 9.1 전략 목록
**Request:**
```http
POST {{base_url}}/api/autotrade/strategy/list
Content-Type: application/json

{
  "access_token": "{{access_token}}"
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "strategies": [
      {
        "strategy_id": "strategy_123456",
        "strategy_name": "RSI 역추세 전략",
        "strategy_type": "technical",
        "status": "active",
        "total_return": 12.5,
        "win_rate": 68.5,
        "max_drawdown": -5.2,
        "created_at": "2025-01-10T10:00:00Z",
        "last_updated": "2025-01-14T12:00:00Z"
      }
    ],
    "total_count": 1,
    "active_count": 1
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

#### 9.2 새 전략 생성
**Request:**
```http
POST {{base_url}}/api/autotrade/strategy/create
Content-Type: application/json

{
  "access_token": "{{access_token}}",
  "strategy_name": "이동평균 교차 전략",
  "strategy_type": "technical",
  "parameters": {
    "short_ma": 5,
    "long_ma": 20,
    "buy_signal": "golden_cross",
    "sell_signal": "dead_cross",
    "stop_loss": 5.0,
    "take_profit": 10.0
  },
  "target_symbols": ["005930", "000660"],
  "initial_capital": 5000000
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "strategy_id": "strategy_789012",
    "strategy_name": "이동평균 교차 전략",
    "strategy_type": "technical",
    "parameters": {
      "short_ma": 5,
      "long_ma": 20,
      "buy_signal": "golden_cross",
      "sell_signal": "dead_cross",
      "stop_loss": 5.0,
      "take_profit": 10.0
    },
    "target_symbols": ["005930", "000660"],
    "initial_capital": 5000000,
    "status": "created",
    "created_at": "2025-01-14T12:34:56.789Z"
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

#### 9.3 백테스트 실행
**Request:**
```http
POST {{base_url}}/api/autotrade/backtest
Content-Type: application/json

{
  "access_token": "{{access_token}}",
  "strategy_id": "strategy_789012",
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "initial_capital": 10000000
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "backtest_id": "backtest_123456",
    "strategy_id": "strategy_789012",
    "period": {
      "start_date": "2023-01-01",
      "end_date": "2023-12-31"
    },
    "initial_capital": 10000000,
    "final_capital": 11850000,
    "total_return": 1850000,
    "return_percent": 18.5,
    "benchmark_return": 12.3,
    "alpha": 6.2,
    "beta": 1.15,
    "sharpe_ratio": 1.42,
    "max_drawdown": -8.5,
    "win_rate": 65.8,
    "total_trades": 127,
    "winning_trades": 84,
    "losing_trades": 43,
    "avg_win": 4.2,
    "avg_loss": -2.8,
    "largest_win": 15.8,
    "largest_loss": -7.2,
    "performance_chart": [
      {
        "date": "2023-01-01",
        "portfolio_value": 10000000,
        "benchmark_value": 10000000
      },
      {
        "date": "2023-12-31",
        "portfolio_value": 11850000,
        "benchmark_value": 11230000
      }
    ],
    "completed_at": "2025-01-14T12:34:56.789Z"
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

#### 9.4 AI 전략 추천
**Request:**
```http
POST {{base_url}}/api/autotrade/ai-strategy
Content-Type: application/json

{
  "access_token": "{{access_token}}",
  "risk_level": "moderate",
  "investment_goal": "growth",
  "time_horizon": "long_term",
  "preferred_sectors": ["technology", "finance"]
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "recommendations": [
      {
        "strategy_name": "AI 모멘텀 성장 전략",
        "strategy_type": "ai_hybrid",
        "description": "기술적 분석과 AI 예측을 결합한 성장주 중심 전략",
        "expected_return": "15-20%",
        "risk_level": "moderate",
        "recommended_allocation": {
          "technology": 40,
          "finance": 30,
          "healthcare": 20,
          "cash": 10
        },
        "parameters": {
          "rebalancing_frequency": "monthly",
          "momentum_threshold": 0.7,
          "ai_confidence_min": 0.8
        },
        "backtested_performance": {
          "return_3y": 18.5,
          "max_drawdown": -12.3,
          "sharpe_ratio": 1.35
        }
      }
    ],
    "market_analysis": {
      "current_trend": "bullish",
      "volatility": "moderate",
      "recommendation": "기술주와 금융주 중심의 성장 전략이 현재 시장 환경에 적합합니다"
    }
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

---

### **10단계: 설정 관리 (Settings API)**

#### 10.1 설정 조회
**Request:**
```http
POST {{base_url}}/api/settings/get
Content-Type: application/json

{
  "access_token": "{{access_token}}"
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "user_id": "user_123456",
    "settings": {
      "notifications": {
        "email_enabled": true,
        "sms_enabled": false,
        "push_enabled": true,
        "price_alerts": true,
        "news_alerts": true,
        "portfolio_alerts": true
      },
      "display": {
        "language": "ko",
        "timezone": "Asia/Seoul",
        "currency": "KRW",
        "theme": "light"
      },
      "security": {
        "otp_enabled": false,
        "login_alerts": true,
        "session_timeout": 30
      },
      "trading": {
        "auto_rebalancing": false,
        "risk_limit": 10.0,
        "stop_loss_default": 5.0
      }
    },
    "updated_at": "2025-01-14T12:34:56.789Z"
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

#### 10.2 설정 업데이트
**Request:**
```http
POST {{base_url}}/api/settings/update
Content-Type: application/json

{
  "access_token": "{{access_token}}",
  "settings": {
    "notifications": {
      "email_enabled": true,
      "sms_enabled": true,
      "push_enabled": true,
      "price_alerts": true,
      "news_alerts": false
    },
    "display": {
      "language": "ko",
      "timezone": "Asia/Seoul",
      "theme": "dark"
    }
  }
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "user_id": "user_123456",
    "updated_settings": {
      "notifications": {
        "email_enabled": true,
        "sms_enabled": true,
        "push_enabled": true,
        "price_alerts": true,
        "news_alerts": false
      },
      "display": {
        "language": "ko",
        "timezone": "Asia/Seoul",
        "theme": "dark"
      }
    },
    "updated_at": "2025-01-14T12:34:56.789Z"
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

#### 10.3 OTP 설정
**Request:**
```http
POST {{base_url}}/api/account/otp/setup
Content-Type: application/json

{
  "access_token": "{{access_token}}"
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
    "secret_key": "JBSWY3DPEHPK3PXP",
    "backup_codes": [
      "12345678",
      "23456789",
      "34567890",
      "45678901",
      "56789012"
    ],
    "setup_instructions": "Google Authenticator 앱에서 QR 코드를 스캔하거나 시크릿 키를 수동으로 입력하세요"
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

#### 10.4 OTP 인증
**Request:**
```http
POST {{base_url}}/api/account/otp/verify
Content-Type: application/json

{
  "access_token": "{{access_token}}",
  "otp_code": "123456"
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "verified": true,
    "otp_enabled": true,
    "verified_at": "2025-01-14T12:34:56.789Z"
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

#### 10.5 비밀번호 변경
**Request:**
```http
POST {{base_url}}/api/settings/password/change
Content-Type: application/json

{
  "access_token": "{{access_token}}",
  "current_password": "Test123!@#",
  "new_password": "NewTest456!@#",
  "confirm_password": "NewTest456!@#"
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "password_changed": true,
    "changed_at": "2025-01-14T12:34:56.789Z",
    "security_alert_sent": true
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

#### 10.6 데이터 내보내기
**Request:**
```http
POST {{base_url}}/api/settings/export-data
Content-Type: application/json

{
  "access_token": "{{access_token}}",
  "data_types": ["portfolio", "transactions", "settings"],
  "format": "json"
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "export_id": "export_123456",
    "download_url": "https://api.example.com/exports/export_123456.json",
    "expires_at": "2025-01-15T12:34:56.789Z",
    "file_size": 1024576,
    "data_types": ["portfolio", "transactions", "settings"],
    "format": "json"
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

---

### **11단계: 관리자 기능 테스트 (Admin API)**

#### 11.1 서버 상태 및 메트릭
**Request:**
```http
POST {{base_url}}/api/admin/serverstatus
Content-Type: application/json

{
  "include_metrics": true
}
```

**Expected Response:**
```json
{
  "server_name": "base_web_server",
  "environment": "production",
  "version": "1.0.0",
  "uptime": "2h 15m 45s",
  "status": "running",
  "metrics": {
    "cpu_usage": "45.2%",
    "memory_usage": "68.7%",
    "disk_usage": "32.1%",
    "active_connections": 127,
    "services": {
      "cache": {
        "service_initialized": true,
        "client_pool_info": {
          "host": "localhost",
          "port": 6379,
          "db": 0
        },
        "client_metrics": {
          "total_operations": 1520,
          "successful_operations": 1515,
          "failed_operations": 5,
          "success_rate": 0.997,
          "cache_hit_rate": 0.85
        }
      },
      "queue": {
        "messages_processed": 456,
        "events_published": 123,
        "active_consumers": 5
      },
      "scheduler": {
        "active_jobs": 3,
        "jobs": [
          {
            "job_id": "job_001",
            "name": "market_data_update",
            "status": "running",
            "next_run": "2025-01-14T13:00:00Z"
          }
        ]
      }
    }
  },
  "error_code": 0
}
```

#### 11.2 세션 카운트
**Request:**
```http
POST {{base_url}}/api/admin/sessioncount
Content-Type: application/json

{}
```

**Expected Response:**
```json
{
  "total_sessions": 25,
  "active_sessions": 25,
  "error_code": 0
}
```

#### 11.3 큐 통계
**Request:**
```http
POST {{base_url}}/api/admin/queuestats
Content-Type: application/json

{
  "queue_names": ["user_notifications", "trade_processing", "risk_analysis"]
}
```

**Expected Response:**
```json
{
  "service_stats": {
    "messages_processed": 1520,
    "events_published": 345,
    "errors": 12,
    "uptime": "2h 15m 45s"
  },
  "event_stats": {
    "total_events": 345,
    "subscribers": 8,
    "event_types": {
      "TRADE_EXECUTED": 120,
      "PRICE_ALERT": 89,
      "NEWS_UPDATE": 136
    }
  },
  "queue_details": {
    "user_notifications": {
      "queue_name": "user_notifications",
      "pending_by_priority": {
        "CRITICAL": 2,
        "HIGH": 5,
        "NORMAL": 23,
        "LOW": 8
      },
      "partition_pending": 12,
      "delayed_count": 3
    },
    "trade_processing": {
      "queue_name": "trade_processing",
      "pending_by_priority": {
        "CRITICAL": 0,
        "HIGH": 1,
        "NORMAL": 4,
        "LOW": 0
      },
      "partition_pending": 2,
      "delayed_count": 0
    }
  },
  "timestamp": "2025-01-14T12:34:56.789Z",
  "error_code": 0
}
```

#### 11.4 시스템 메트릭만 조회
**Request:**
```http
GET {{base_url}}/api/admin/metrics
```

**Expected Response:**
```json
{
  "server_name": "base_web_server",
  "environment": "production",
  "uptime": "2h 15m 45s",
  "metrics": {
    "cpu_usage": "45.2%",
    "memory_usage": "68.7%",
    "disk_usage": "32.1%",
    "active_connections": 127,
    "services": {
      "cache": {
        "total_operations": 1520,
        "success_rate": 0.997,
        "cache_hit_rate": 0.85
      },
      "queue": {
        "messages_processed": 456,
        "events_published": 123
      }
    }
  }
}
```

---

### **12단계: 세션 종료**

#### 12.1 토큰 갱신 (선택사항)
**Request:**
```http
POST {{base_url}}/api/account/token/refresh
Content-Type: application/json

{
  "refresh_token": "refresh_token_here"
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "access_token": "new_access_token_here",
    "refresh_token": "new_refresh_token_here",
    "expires_at": "2025-01-14T20:34:56.789Z"
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

#### 12.2 로그아웃
**Request:**
```http
POST {{base_url}}/api/account/logout
Content-Type: application/json

{
  "access_token": "{{access_token}}"
}
```

**Expected Response:**
```json
{
  "error_code": 0,
  "error_message": null,
  "data": {
    "logged_out": true,
    "logged_out_at": "2025-01-14T12:34:56.789Z",
    "session_invalidated": true
  },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

---

## 🔍 **테스트 체크리스트**

### ✅ **필수 테스트 흐름**
- [ ] **1단계**: 서버 상태 확인 (4개 API)
- [ ] **2단계**: 계정 관리 (7개 API) ⭐ **토큰 저장**
- [ ] **3단계**: 튜토리얼 (4개 API)
- [ ] **4단계**: 시장 데이터 (4개 API)
- [ ] **5단계**: 포트폴리오 관리 (4개 API)
- [ ] **6단계**: 대시보드 (3개 API)
- [ ] **7단계**: 알림 관리 (4개 API)
- [ ] **8단계**: 채팅/AI 상담 (5개 API)
- [ ] **9단계**: 자동매매 (4개 API)
- [ ] **10단계**: 설정 관리 (6개 API)
- [ ] **11단계**: 관리자 기능 (4개 API)
- [ ] **12단계**: 세션 종료 (2개 API)

### 🚨 **주의사항**
- **access_token**은 로그인 후 받은 값으로 교체
- **종목 코드**(symbol)는 실제 존재하는 값 사용
- **날짜 형식**: YYYY-MM-DD
- **에러 응답** 시 `error_code`와 `error_message` 확인
- **Admin API**는 관리자 권한 필요

### 📊 **응답 구조**
모든 API는 다음 기본 구조를 따릅니다:
```json
{
  "error_code": 0,
  "error_message": null,
  "data": { ... },
  "timestamp": "2025-01-14T12:34:56.789Z"
}
```

### 🎯 **PostAPI Collection 구성**

#### **Environment 변수**
```json
{
  "base_url": "http://localhost:8000",
  "access_token": ""
}
```

#### **Pre-request Script** (로그인 필요한 API용)
```javascript
if (!pm.environment.get("access_token")) {
    console.warn("Warning: access_token is not set. Please login first.");
}
```

#### **Tests Script** (로그인 API용)
```javascript
if (pm.response.code === 200) {
    const response = pm.response.json();
    if (response.data && response.data.access_token) {
        pm.environment.set("access_token", response.data.access_token);
        console.log("Access token saved");
    }
}

pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Response has error_code 0", function () {
    const jsonData = pm.response.json();
    pm.expect(jsonData.error_code).to.eql(0);
});
```

#### **폴더 구조**
1. 📁 **01. Server Status** (4개 API)
2. 📁 **02. Account Management** (7개 API)
3. 📁 **03. Tutorial** (4개 API)
4. 📁 **04. Market Data** (4개 API)
5. 📁 **05. Portfolio** (4개 API)
6. 📁 **06. Dashboard** (3개 API)
7. 📁 **07. Notifications** (4개 API)
8. 📁 **08. Chat & AI** (5개 API)
9. 📁 **09. AutoTrade** (4개 API)
10. 📁 **10. Settings** (6개 API)
11. 📁 **11. Admin** (4개 API)
12. 📁 **12. Session End** (2개 API)

---

## 🎉 **테스트 완료 기준**

### **성공 시나리오**
1. 모든 API가 `error_code: 0` 반환
2. 로그인 → 토큰 획득 → 비즈니스 로직 → 로그아웃 완료
3. 실제 데이터 CRUD 확인
4. Admin API로 시스템 상태 검증

### **데이터 검증 포인트**
- **회원가입/로그인**: 토큰 발급 및 세션 생성
- **프로필 설정**: 사용자 정보 저장/조회
- **포트폴리오**: 종목 추가/제거, 성과 계산
- **알림**: 가격 알림 생성/트리거
- **채팅**: AI 응답 품질 및 관련 데이터 연동
- **자동매매**: 백테스트 결과 정확성

이 가이드를 따라하면 **총 67개 API**를 체계적으로 테스트할 수 있습니다! 🚀