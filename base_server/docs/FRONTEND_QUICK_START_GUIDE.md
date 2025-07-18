# 프론트엔드 개발자 퀵 스타트 가이드 🚀

> **5분 안에 Base Server API 연동하기**
> 
> 이 가이드를 따라하면 React 프로젝트에서 Base Server API를 바로 사용할 수 있습니다.

## 📋 체크리스트

- [ ] 백엔드 서버 실행 확인
- [ ] React 프로젝트 설정
- [ ] 필수 파일 복사
- [ ] 로그인 기능 구현
- [ ] 포트폴리오 기능 구현
- [ ] 테스트 완료

---

## 1️⃣ 백엔드 서버 실행 확인

### 서버 상태 확인
```bash
# 브라우저에서 확인
http://localhost:8000/api/admin/ping

# 응답 예시
{
  "status": "pong",
  "timestamp": "2024-07-16T10:30:00Z"
}
```

### 서버가 실행되지 않은 경우
```bash
cd base_server
python -m uvicorn application.base_web_server.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 2️⃣ React 프로젝트 설정

### 새 프로젝트 생성
```bash
npx create-react-app my-trading-app --template typescript
cd my-trading-app
```

### 필수 패키지 설치
```bash
npm install axios @tanstack/react-query
# 또는
yarn add axios @tanstack/react-query
```

### 환경 변수 설정
```bash
# .env.local 파일 생성
echo "REACT_APP_API_BASE_URL=http://localhost:8000" > .env.local
```

---

## 3️⃣ 필수 파일 복사

### 1. 타입 정의 파일 생성
```typescript
// src/types/api.ts
export interface BaseRequest {
  accessToken?: string;
  sequence?: number;
}

export interface BaseResponse {
  errorCode: number;
  sequence: number;
}

export interface LoginRequest extends BaseRequest {
  platform_type: string;
  account_id: string;
  password: string;
}

export interface LoginResponse extends BaseResponse {
  accessToken: string;
  refreshToken: string;
  user_id: string;
  next_step: string;
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

### 2. API 클라이언트 생성
```typescript
// src/lib/api.ts
import axios, { AxiosInstance } from 'axios';
import { BaseRequest, BaseResponse } from '../types/api';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000',
      headers: { 'Content-Type': 'application/json' },
    });

    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('accessToken');
      if (token && config.data) {
        config.data = {
          ...config.data,
          accessToken: token,
          sequence: Date.now(),
        };
      }
      return config;
    });

    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.clear();
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  async post<T extends BaseResponse>(url: string, data: Partial<BaseRequest> = {}): Promise<T> {
    const response = await this.client.post(`/api${url}`, data);
    return response.data;
  }
}

export const api = new ApiClient();
```

---

## 4️⃣ 로그인 기능 구현

### 로그인 컴포넌트
```typescript
// src/components/LoginForm.tsx
import React, { useState } from 'react';
import { api } from '../lib/api';
import { LoginRequest, LoginResponse } from '../types/api';

const LoginForm: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await api.post<LoginResponse>('/account/login', {
        platform_type: 'native',
        account_id: email,
        password: password,
      });

      if (response.errorCode === 0) {
        localStorage.setItem('accessToken', response.accessToken);
        localStorage.setItem('userId', response.user_id);
        window.location.href = '/dashboard';
      } else {
        setError(`로그인 실패: 에러코드 ${response.errorCode}`);
      }
    } catch (error) {
      setError('네트워크 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-8 p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-6 text-center">로그인</h2>
      
      <form onSubmit={handleLogin} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            이메일
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            비밀번호
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>

        {error && (
          <div className="text-red-600 text-sm text-center">{error}</div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {loading ? '로그인 중...' : '로그인'}
        </button>
      </form>
    </div>
  );
};

export default LoginForm;
```

---

## 5️⃣ 포트폴리오 기능 구현

### 포트폴리오 컴포넌트
```typescript
// src/components/Portfolio.tsx
import React, { useState, useEffect } from 'react';
import { api } from '../lib/api';
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
      const response = await api.post<PortfolioGetResponse>('/portfolio/get');
      
      if (response.errorCode === 0) {
        setPortfolio(response);
      } else {
        setError(`포트폴리오 조회 실패: 에러코드 ${response.errorCode}`);
      }
    } catch (error) {
      setError('데이터를 불러오는 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <div className="text-red-600 mb-4">{error}</div>
        <button
          onClick={loadPortfolio}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
        >
          다시 시도
        </button>
      </div>
    );
  }

  if (!portfolio?.portfolio) {
    return <div className="text-center py-8">포트폴리오 데이터가 없습니다.</div>;
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-6">포트폴리오</h2>
      
      {/* 포트폴리오 요약 */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">
              {formatCurrency(portfolio.portfolio.total_value)}
            </div>
            <div className="text-sm text-gray-500">총 자산</div>
          </div>
          <div className="text-center">
            <div className={`text-2xl font-bold ${
              portfolio.portfolio.performance.total_return >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {formatPercentage(portfolio.portfolio.performance.total_return)}
            </div>
            <div className="text-sm text-gray-500">총 수익률</div>
          </div>
          <div className="text-center">
            <div className={`text-2xl font-bold ${
              portfolio.portfolio.performance.daily_change >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {formatPercentage(portfolio.portfolio.performance.daily_change)}
            </div>
            <div className="text-sm text-gray-500">일일 변동</div>
          </div>
        </div>
      </div>

      {/* 보유 종목 */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold mb-4">보유 종목</h3>
        <div className="overflow-x-auto">
          <table className="w-full table-auto">
            <thead>
              <tr className="bg-gray-50">
                <th className="px-4 py-2 text-left">종목</th>
                <th className="px-4 py-2 text-left">수량</th>
                <th className="px-4 py-2 text-left">평균 단가</th>
                <th className="px-4 py-2 text-left">현재 가격</th>
                <th className="px-4 py-2 text-left">손익</th>
              </tr>
            </thead>
            <tbody>
              {portfolio.portfolio.holdings.map((holding, index) => (
                <tr key={index} className="border-b">
                  <td className="px-4 py-2 font-medium">{holding.symbol}</td>
                  <td className="px-4 py-2">{holding.quantity.toLocaleString()}</td>
                  <td className="px-4 py-2">{formatCurrency(holding.avg_price)}</td>
                  <td className="px-4 py-2">{formatCurrency(holding.current_price)}</td>
                  <td className={`px-4 py-2 font-medium ${
                    holding.profit_loss >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {formatCurrency(holding.profit_loss)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Portfolio;
```

---

## 6️⃣ 앱 라우팅 설정

### 메인 App 컴포넌트
```typescript
// src/App.tsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LoginForm from './components/LoginForm';
import Portfolio from './components/Portfolio';
import './App.css';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const token = localStorage.getItem('accessToken');
  return token ? <>{children}</> : <Navigate to="/login" replace />;
};

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/login" element={<LoginForm />} />
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <Portfolio />
              </ProtectedRoute>
            } 
          />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
```

### 필수 패키지 설치 (라우팅용)
```bash
npm install react-router-dom
npm install --save-dev @types/react-router-dom
```

---

## 7️⃣ 스타일링 설정

### Tailwind CSS 설치 (선택사항)
```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### 기본 CSS 스타일 (Tailwind 없이)
```css
/* src/App.css */
.App {
  min-height: 100vh;
  background-color: #f3f4f6;
}

.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

table {
  border-collapse: collapse;
}

th, td {
  border: 1px solid #e5e7eb;
  padding: 8px 12px;
  text-align: left;
}

th {
  background-color: #f9fafb;
  font-weight: 600;
}

.text-green-600 {
  color: #059669;
}

.text-red-600 {
  color: #dc2626;
}

.bg-blue-600 {
  background-color: #2563eb;
}

.bg-blue-600:hover {
  background-color: #1d4ed8;
}

.shadow-md {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.rounded-lg {
  border-radius: 0.5rem;
}

.rounded-md {
  border-radius: 0.375rem;
}
```

---

## 8️⃣ 테스트 실행

### 1. 개발 서버 실행
```bash
npm start
```

### 2. 테스트 시나리오
1. **로그인 테스트**
   - 브라우저에서 `http://localhost:3000/login` 접속
   - 이메일: `test@example.com`, 비밀번호: `password123` 입력
   - 로그인 성공 시 대시보드로 이동

2. **포트폴리오 테스트**
   - 대시보드에서 포트폴리오 데이터 확인
   - 로딩 상태 확인
   - 에러 처리 확인

3. **인증 테스트**
   - 로그인 없이 `/dashboard` 접속 시 로그인 페이지로 리다이렉트
   - 토큰 만료 시 자동 로그아웃

---

## 🎉 완료!

### 구현된 기능
- ✅ 로그인/로그아웃
- ✅ 포트폴리오 조회
- ✅ 자동 토큰 관리
- ✅ 에러 처리
- ✅ 로딩 상태
- ✅ 반응형 디자인

### 다음 단계
1. **추가 기능 구현**: 채팅, 알림, 자동거래 등
2. **상태 관리**: Redux 또는 Zustand 도입
3. **최적화**: React Query로 캐싱 및 동기화
4. **테스트**: Jest와 React Testing Library 추가

### 참고 문서
- [프론트엔드 개발자 워크플로우 가이드](./FRONTEND_DEVELOPER_WORKFLOW_GUIDE.md)
- [React Hooks 및 유틸리티](./REACT_HOOKS_AND_UTILITIES.md)
- [API 테스트 가이드](./API_POSTMAN_TEST_GUIDE.md)

축하합니다! 🎊 Base Server API가 React 앱에 성공적으로 연동되었습니다!