# 프론트엔드 개발자를 위한 백엔드 워크플로우 가이드 📚

> **React 개발자를 위한 Base Server API 사용 가이드**
> 
> 이 문서는 백엔드 구조를 이해하고 React에서 API를 효과적으로 사용하는 방법을 단계별로 설명합니다.

## 🎯 목차

1. [백엔드 구조 이해하기](#백엔드-구조-이해하기)
2. [API 호출 흐름](#api-호출-흐름)
3. [Request/Response 구조](#requestresponse-구조)
4. [React에서 API 사용하기](#react에서-api-사용하기)
5. [실제 예시 코드](#실제-예시-코드)
6. [에러 처리](#에러-처리)
7. [자주 묻는 질문](#자주-묻는-질문)

---

## 📁 백엔드 구조 이해하기

### 핵심 디렉토리 구조
```
base_server/
├── application/base_web_server/
│   ├── routers/           # 🌐 FastAPI 라우터 (API 엔드포인트)
│   │   ├── account.py     # 계정 관련 API
│   │   ├── portfolio.py   # 포트폴리오 API
│   │   └── chat.py        # 채팅 API
│   └── main.py           # 서버 메인 파일
├── template/             # 📋 비즈니스 로직 처리
│   ├── account/
│   │   ├── account_template_impl.py    # 실제 처리 로직
│   │   └── common/
│   │       ├── account_serialize.py    # 📝 Request/Response 클래스
│   │       └── account_model.py        # 데이터 모델
│   ├── portfolio/
│   └── chat/
└── service/              # 🔧 서비스 계층 (DB, Cache, External API)
    ├── db/
    ├── cache/
    └── external/
```

### 🎯 프론트엔드 개발자가 알아야 할 핵심 파일들

1. **Router 파일** (`application/base_web_server/routers/*.py`)
   - 실제 API 엔드포인트가 정의된 곳
   - HTTP 메서드와 URL 경로 확인

2. **Serialize 파일** (`template/*/common/*_serialize.py`)
   - Request/Response JSON 구조 정의
   - **가장 중요한 파일! 여기서 JSON 구조를 확인하세요**

3. **Template Implementation** (`template/*_template_impl.py`)
   - 실제 비즈니스 로직 처리
   - 데이터 검증 및 처리 과정

---

## 🔄 API 호출 흐름

### 전체 흐름도
```
React Frontend → FastAPI Router → Template Implementation → Service Layer → Database
      ↓               ↓                    ↓                      ↓            ↓
1. JSON 요청      2. 라우팅         3. 비즈니스 로직      4. 데이터 처리   5. 저장/조회
      ↑               ↑                    ↑                      ↑            ↑
JSON 응답 ← Router Response ← Template Response ← Service Response ← Database Response
```

### 상세 처리 단계

#### 1. 요청 받기 (Router)
```python
# application/base_web_server/routers/account.py
@router.post("/login")
async def login(request: AccountLoginRequest, req: Request):
    # 1. Request 클래스로 JSON 파싱
    # 2. IP 주소 추출
    # 3. TemplateService로 전달
```

#### 2. 비즈니스 로직 처리 (Template)
```python
# template/account/account_template_impl.py
async def on_account_login_req(self, client_session, request):
    # 1. 요청 데이터 검증
    # 2. 데이터베이스 조회
    # 3. 비즈니스 로직 수행
    # 4. 응답 데이터 생성
```

#### 3. 응답 반환
```python
# 응답 객체 생성 후 JSON으로 변환하여 반환
response = AccountLoginResponse()
response.accessToken = "jwt_token_here"
return response
```

---

## 📝 Request/Response 구조

### 기본 구조 이해

#### BaseRequest (모든 요청의 기본)
```python
# service/net/protocol_base.py
class BaseRequest(BaseModel):
    accessToken: str = ""    # 인증 토큰
    sequence: int = 0        # 요청 순서
```

#### BaseResponse (모든 응답의 기본)
```python
# service/net/protocol_base.py
class BaseResponse(BaseModel):
    errorCode: int = 0       # 0: 성공, 그외: 에러
    sequence: int = 0        # 응답 순서
```

### 구체적인 예시: 로그인 API

#### Request 클래스 위치
```python
# template/account/common/account_serialize.py
class AccountLoginRequest(BaseRequest):
    platform_type: str      # "native", "google", "apple"
    account_id: str         # 이메일 또는 사용자 ID
    password: str           # 비밀번호
    device_info: Optional[str] = None
```

#### Response 클래스 위치
```python
# template/account/common/account_serialize.py
class AccountLoginResponse(BaseResponse):
    accessToken: str = ""    # JWT 토큰
    refreshToken: str = ""   # 리프레시 토큰
    user_id: str = ""       # 사용자 ID
    next_step: str = ""     # 다음 단계 ("COMPLETE", "OTP", "PROFILE")
```

---

## ⚛️ React에서 API 사용하기

### 1. 기본 API 클라이언트 설정

```typescript
// lib/api/client.ts
import axios, { AxiosInstance } from 'axios';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: 'http://localhost:8000/api',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 요청 인터셉터 - 토큰 자동 추가
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('accessToken');
      if (token) {
        config.data = {
          ...config.data,
          accessToken: token,
          sequence: Date.now() // 간단한 시퀀스 번호
        };
      }
      return config;
    });

    // 응답 인터셉터 - 에러 처리
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // 토큰 만료 처리
          localStorage.removeItem('accessToken');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  async post<T>(url: string, data: any): Promise<T> {
    const response = await this.client.post(url, data);
    return response.data;
  }

  async get<T>(url: string): Promise<T> {
    const response = await this.client.get(url);
    return response.data;
  }
}

export const apiClient = new ApiClient();
```

### 2. 타입 정의

```typescript
// types/api.ts
export interface BaseRequest {
  accessToken?: string;
  sequence?: number;
}

export interface BaseResponse {
  errorCode: number;
  sequence: number;
}

// 로그인 관련 타입
export interface LoginRequest extends BaseRequest {
  platform_type: string;
  account_id: string;
  password: string;
  device_info?: string;
}

export interface LoginResponse extends BaseResponse {
  accessToken: string;
  refreshToken: string;
  user_id: string;
  next_step: string;
}

// 포트폴리오 관련 타입
export interface PortfolioGetRequest extends BaseRequest {
  // 추가 필드 없음
}

export interface PortfolioGetResponse extends BaseResponse {
  portfolio: {
    total_value: number;
    holdings: Array<{
      symbol: string;
      quantity: number;
      avg_price: number;
      current_price: number;
      profit_loss: number;
    }>;
    performance: {
      total_return: number;
      daily_change: number;
    };
  };
}
```

### 3. API 서비스 함수

```typescript
// services/authService.ts
import { apiClient } from '../lib/api/client';
import { LoginRequest, LoginResponse } from '../types/api';

export const authService = {
  async login(loginData: Omit<LoginRequest, 'accessToken' | 'sequence'>): Promise<LoginResponse> {
    try {
      const response = await apiClient.post<LoginResponse>('/account/login', loginData);
      
      // 성공 시 토큰 저장
      if (response.errorCode === 0) {
        localStorage.setItem('accessToken', response.accessToken);
        localStorage.setItem('refreshToken', response.refreshToken);
        localStorage.setItem('userId', response.user_id);
      }
      
      return response;
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  },

  async logout(): Promise<void> {
    try {
      await apiClient.post('/account/logout', {});
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('userId');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  }
};
```

```typescript
// services/portfolioService.ts
import { apiClient } from '../lib/api/client';
import { PortfolioGetRequest, PortfolioGetResponse } from '../types/api';

export const portfolioService = {
  async getPortfolio(): Promise<PortfolioGetResponse> {
    return await apiClient.post<PortfolioGetResponse>('/portfolio/get', {});
  },

  async addStock(symbol: string, quantity: number, price: number) {
    return await apiClient.post('/portfolio/add-stock', {
      symbol,
      quantity,
      price
    });
  }
};
```

### 4. React 컴포넌트에서 사용

```typescript
// components/LoginForm.tsx
import React, { useState } from 'react';
import { authService } from '../services/authService';
import { LoginRequest } from '../types/api';

const LoginForm: React.FC = () => {
  const [formData, setFormData] = useState({
    platform_type: 'native',
    account_id: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await authService.login(formData);
      
      // 백엔드 응답 확인
      if (response.errorCode === 0) {
        // 성공 처리
        console.log('로그인 성공:', response);
        
        // 다음 단계 처리
        if (response.next_step === 'COMPLETE') {
          // 메인 페이지로 이동
          window.location.href = '/dashboard';
        } else if (response.next_step === 'PROFILE') {
          // 프로필 설정 페이지로 이동
          window.location.href = '/profile/setup';
        }
      } else {
        // 백엔드에서 반환한 에러 처리
        setError(`로그인 실패: 에러코드 ${response.errorCode}`);
      }
    } catch (error) {
      console.error('로그인 에러:', error);
      setError('네트워크 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label>이메일:</label>
        <input
          type="email"
          value={formData.account_id}
          onChange={(e) => setFormData({...formData, account_id: e.target.value})}
          required
        />
      </div>
      <div>
        <label>비밀번호:</label>
        <input
          type="password"
          value={formData.password}
          onChange={(e) => setFormData({...formData, password: e.target.value})}
          required
        />
      </div>
      {error && <div style={{color: 'red'}}>{error}</div>}
      <button type="submit" disabled={loading}>
        {loading ? '로그인 중...' : '로그인'}
      </button>
    </form>
  );
};

export default LoginForm;
```

### 5. 포트폴리오 컴포넌트 예시

```typescript
// components/Portfolio.tsx
import React, { useState, useEffect } from 'react';
import { portfolioService } from '../services/portfolioService';
import { PortfolioGetResponse } from '../types/api';

const Portfolio: React.FC = () => {
  const [portfolio, setPortfolio] = useState<PortfolioGetResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadPortfolio();
  }, []);

  const loadPortfolio = async () => {
    try {
      const response = await portfolioService.getPortfolio();
      
      if (response.errorCode === 0) {
        setPortfolio(response);
      } else {
        setError(`포트폴리오 조회 실패: 에러코드 ${response.errorCode}`);
      }
    } catch (error) {
      console.error('포트폴리오 조회 에러:', error);
      setError('데이터를 불러오는 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>로딩 중...</div>;
  if (error) return <div>에러: {error}</div>;
  if (!portfolio) return <div>데이터 없음</div>;

  return (
    <div>
      <h2>포트폴리오</h2>
      <div>
        <h3>총 가치: ${portfolio.portfolio.total_value.toLocaleString()}</h3>
        <p>총 수익률: {portfolio.portfolio.performance.total_return}%</p>
        <p>일일 변동: {portfolio.portfolio.performance.daily_change}%</p>
      </div>
      
      <h3>보유 종목</h3>
      <table>
        <thead>
          <tr>
            <th>종목</th>
            <th>수량</th>
            <th>평균 단가</th>
            <th>현재 가격</th>
            <th>손익</th>
          </tr>
        </thead>
        <tbody>
          {portfolio.portfolio.holdings.map((holding, index) => (
            <tr key={index}>
              <td>{holding.symbol}</td>
              <td>{holding.quantity}</td>
              <td>${holding.avg_price}</td>
              <td>${holding.current_price}</td>
              <td style={{color: holding.profit_loss >= 0 ? 'green' : 'red'}}>
                ${holding.profit_loss}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default Portfolio;
```

---

## 🚨 에러 처리

### 백엔드 에러 코드 체계

```typescript
// constants/errorCodes.ts
export const ERROR_CODES = {
  SUCCESS: 0,
  AUTHENTICATION_FAILED: 1001,
  UNAUTHORIZED: 1002,
  INVALID_PARAMETERS: 1003,
  RESOURCE_NOT_FOUND: 1004,
  SERVER_ERROR: 1005,
  
  // 크롤러 관련
  CRAWLER_LOCK_FAILED: 10001,
  CRAWLER_STATUS_FAILED: 10002,
  CRAWLER_HEALTH_FAILED: 10003,
} as const;

export const ERROR_MESSAGES = {
  [ERROR_CODES.SUCCESS]: '성공',
  [ERROR_CODES.AUTHENTICATION_FAILED]: '인증에 실패했습니다.',
  [ERROR_CODES.UNAUTHORIZED]: '권한이 없습니다.',
  [ERROR_CODES.INVALID_PARAMETERS]: '잘못된 파라미터입니다.',
  [ERROR_CODES.RESOURCE_NOT_FOUND]: '리소스를 찾을 수 없습니다.',
  [ERROR_CODES.SERVER_ERROR]: '서버 오류가 발생했습니다.',
} as const;
```

### 에러 처리 유틸리티

```typescript
// utils/errorHandler.ts
import { ERROR_CODES, ERROR_MESSAGES } from '../constants/errorCodes';

export const handleApiError = (errorCode: number): string => {
  return ERROR_MESSAGES[errorCode] || '알 수 없는 오류가 발생했습니다.';
};

export const isAuthenticationError = (errorCode: number): boolean => {
  return errorCode === ERROR_CODES.AUTHENTICATION_FAILED || 
         errorCode === ERROR_CODES.UNAUTHORIZED;
};
```

---

## 🔍 디버깅 가이드

### 1. Request/Response 클래스 찾기

특정 API의 Request/Response 구조를 확인하려면:

```bash
# 예: 로그인 API 구조 확인
cat template/account/common/account_serialize.py

# 예: 포트폴리오 API 구조 확인
cat template/portfolio/common/portfolio_serialize.py
```

### 2. API 엔드포인트 확인

```bash
# 예: 계정 관련 API 엔드포인트 확인
cat application/base_web_server/routers/account.py
```

### 3. 실제 처리 로직 확인

```bash
# 예: 로그인 처리 로직 확인
cat template/account/account_template_impl.py
```

---

## 🎯 실제 개발 워크플로우

### 1. 새로운 API 사용 시 체크리스트

- [ ] 1. Router 파일에서 엔드포인트 확인 (`routers/*.py`)
- [ ] 2. Serialize 파일에서 Request/Response 구조 확인 (`*/common/*_serialize.py`)
- [ ] 3. TypeScript 타입 정의 작성
- [ ] 4. API 서비스 함수 작성
- [ ] 5. React 컴포넌트에서 사용
- [ ] 6. 에러 처리 추가
- [ ] 7. 로딩 상태 처리

### 2. 예시: 새로운 채팅 API 사용하기

#### Step 1: Request/Response 구조 확인
```python
# template/chat/common/chat_serialize.py 파일 확인
class ChatMessageSendRequest(BaseRequest):
    room_id: str
    content: str
    
class ChatMessageSendResponse(BaseResponse):
    message_id: str
    room_id: str
    content: str
    sent_at: str
```

#### Step 2: TypeScript 타입 정의
```typescript
// types/chat.ts
export interface ChatMessageSendRequest extends BaseRequest {
  room_id: string;
  content: string;
}

export interface ChatMessageSendResponse extends BaseResponse {
  message_id: string;
  room_id: string;
  content: string;
  sent_at: string;
}
```

#### Step 3: API 서비스 함수 작성
```typescript
// services/chatService.ts
export const chatService = {
  async sendMessage(roomId: string, content: string): Promise<ChatMessageSendResponse> {
    return await apiClient.post('/chat/message/send', {
      room_id: roomId,
      content: content
    });
  }
};
```

#### Step 4: React 컴포넌트에서 사용
```typescript
// components/ChatRoom.tsx
const ChatRoom: React.FC = () => {
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);

  const handleSendMessage = async () => {
    if (!message.trim()) return;
    
    setSending(true);
    try {
      const response = await chatService.sendMessage('room123', message);
      
      if (response.errorCode === 0) {
        console.log('메시지 전송 성공:', response);
        setMessage(''); // 입력 필드 초기화
        // 채팅 목록 업데이트 로직
      } else {
        console.error('메시지 전송 실패:', response.errorCode);
      }
    } catch (error) {
      console.error('메시지 전송 에러:', error);
    } finally {
      setSending(false);
    }
  };

  return (
    <div>
      <input
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
        placeholder="메시지를 입력하세요..."
      />
      <button onClick={handleSendMessage} disabled={sending}>
        {sending ? '전송 중...' : '전송'}
      </button>
    </div>
  );
};
```

---

## 🔥 자주 묻는 질문

### Q1: Request에 accessToken을 매번 넣어야 하나요?
A: 네, 대부분의 API는 accessToken이 필요합니다. API 클라이언트의 인터셉터에서 자동으로 추가하도록 설정하면 편리합니다.

### Q2: sequence 필드는 무엇인가요?
A: 요청의 순서를 나타내는 필드입니다. 보통 현재 시간(타임스탬프)을 사용합니다.

### Q3: errorCode가 0이 아닐 때 어떻게 처리하나요?
A: errorCode가 0이 아니면 에러 상황입니다. 각 에러 코드에 맞는 사용자 친화적인 메시지를 보여주세요.

### Q4: API 응답이 없을 때는 어떻게 하나요?
A: 네트워크 오류나 서버 오류 시에는 try-catch로 처리하고, 사용자에게 적절한 에러 메시지를 보여주세요.

### Q5: 토큰이 만료되었을 때는 어떻게 하나요?
A: 401 에러나 인증 관련 에러 코드가 오면 토큰을 삭제하고 로그인 페이지로 리다이렉트합니다.

---

## 🎉 마무리

이 가이드를 통해 백엔드 구조를 이해하고 React에서 API를 효과적으로 사용할 수 있게 되었습니다!

### 핵심 포인트 정리:
1. **Request/Response 구조**: `template/*/common/*_serialize.py` 파일 확인
2. **API 엔드포인트**: `application/base_web_server/routers/*.py` 파일 확인
3. **모든 응답은 errorCode 확인**: 0이면 성공, 그외는 에러
4. **토큰 자동 관리**: API 클라이언트 인터셉터 활용
5. **에러 처리**: 백엔드 에러 코드와 네트워크 에러 모두 처리

궁금한 점이 있으면 언제든지 이 가이드를 참고하거나 백엔드 개발자에게 문의하세요! 🚀

---

## 📚 추가 자료

- [API 테스트 가이드](./API_POSTMAN_TEST_GUIDE.md)
- [Postman 테스트 시나리오](./POSTMAN_TEST_SCENARIO_GUIDE.md)
- [서버 아키텍처 문서](./BASE_SERVER_ARCHITECTURE_PART1.md)