# React Hooks 및 유틸리티 코드 📦

> **프론트엔드 개발자를 위한 즉시 사용 가능한 React 코드**
> 
> 이 문서는 Base Server API를 React에서 쉽게 사용할 수 있는 커스텀 Hook과 유틸리티를 제공합니다.

## 🎯 목차

1. [기본 설정](#기본-설정)
2. [커스텀 Hooks](#커스텀-hooks)
3. [유틸리티 함수](#유틸리티-함수)
4. [React Context](#react-context)
5. [실제 사용 예시](#실제-사용-예시)

---

## 🔧 기본 설정

### 1. 패키지 설치

```bash
npm install axios react-query @tanstack/react-query
# 또는
yarn add axios react-query @tanstack/react-query
```

### 2. 환경 변수 설정

```typescript
// .env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_API_TIMEOUT=30000
```

### 3. API 클라이언트 (개선된 버전)

```typescript
// lib/api/client.ts
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import { BaseRequest, BaseResponse } from '../types/api';

class ApiClient {
  private client: AxiosInstance;
  private accessToken: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
      timeout: parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT || '30000'),
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // 요청 인터셉터
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getToken();
        if (token && config.data) {
          config.data = {
            ...config.data,
            accessToken: token,
            sequence: Date.now(),
          };
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // 응답 인터셉터
    this.client.interceptors.response.use(
      (response) => {
        const data = response.data as BaseResponse;
        if (data.errorCode === 1001 || data.errorCode === 1002) {
          this.clearToken();
          window.location.href = '/login';
        }
        return response;
      },
      (error) => {
        console.error('API Error:', error);
        return Promise.reject(error);
      }
    );
  }

  setToken(token: string) {
    this.accessToken = token;
    localStorage.setItem('accessToken', token);
  }

  getToken(): string | null {
    return this.accessToken || localStorage.getItem('accessToken');
  }

  clearToken() {
    this.accessToken = null;
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('userId');
  }

  async post<T extends BaseResponse>(
    url: string, 
    data: Partial<BaseRequest> = {}
  ): Promise<T> {
    const response = await this.client.post(`/api${url}`, data);
    return response.data;
  }

  async get<T extends BaseResponse>(url: string): Promise<T> {
    const response = await this.client.get(`/api${url}`);
    return response.data;
  }
}

export const apiClient = new ApiClient();
```

---

## 🎣 커스텀 Hooks

### 1. 기본 API Hook

```typescript
// hooks/useApi.ts
import { useState, useCallback } from 'react';
import { apiClient } from '../lib/api/client';
import { BaseResponse } from '../types/api';

interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

interface UseApiOptions {
  onSuccess?: (data: any) => void;
  onError?: (error: string) => void;
  showErrorToast?: boolean;
}

export function useApi<T extends BaseResponse>(
  apiCall: () => Promise<T>,
  options: UseApiOptions = {}
) {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: false,
    error: null,
  });

  const execute = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const response = await apiCall();
      
      if (response.errorCode === 0) {
        setState(prev => ({ ...prev, data: response, loading: false }));
        options.onSuccess?.(response);
      } else {
        const errorMessage = getErrorMessage(response.errorCode);
        setState(prev => ({ ...prev, error: errorMessage, loading: false }));
        options.onError?.(errorMessage);
      }
    } catch (error) {
      const errorMessage = '네트워크 오류가 발생했습니다.';
      setState(prev => ({ ...prev, error: errorMessage, loading: false }));
      options.onError?.(errorMessage);
    }
  }, [apiCall, options]);

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
  }, []);

  return {
    ...state,
    execute,
    reset,
  };
}

// 에러 메시지 변환 함수
function getErrorMessage(errorCode: number): string {
  const errorMessages: Record<number, string> = {
    1001: '인증에 실패했습니다. 다시 로그인해주세요.',
    1002: '권한이 없습니다.',
    1003: '입력 정보를 확인해주세요.',
    1004: '요청한 정보를 찾을 수 없습니다.',
    1005: '서버 오류가 발생했습니다.',
  };
  
  return errorMessages[errorCode] || `오류가 발생했습니다. (코드: ${errorCode})`;
}
```

### 2. 인증 관련 Hook

```typescript
// hooks/useAuth.ts
import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '../lib/api/client';
import { LoginRequest, LoginResponse } from '../types/api';

interface User {
  id: string;
  email: string;
  // 추가 사용자 정보
}

interface UseAuthState {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
}

export function useAuth() {
  const [state, setState] = useState<UseAuthState>({
    user: null,
    isAuthenticated: false,
    loading: true,
  });

  useEffect(() => {
    const token = apiClient.getToken();
    const userId = localStorage.getItem('userId');
    
    if (token && userId) {
      setState(prev => ({
        ...prev,
        user: { id: userId, email: '' }, // 실제로는 사용자 정보 API 호출
        isAuthenticated: true,
        loading: false,
      }));
    } else {
      setState(prev => ({ ...prev, loading: false }));
    }
  }, []);

  const login = useCallback(async (credentials: Omit<LoginRequest, 'accessToken' | 'sequence'>) => {
    setState(prev => ({ ...prev, loading: true }));
    
    try {
      const response = await apiClient.post<LoginResponse>('/account/login', credentials);
      
      if (response.errorCode === 0) {
        apiClient.setToken(response.accessToken);
        localStorage.setItem('refreshToken', response.refreshToken);
        localStorage.setItem('userId', response.user_id);
        
        setState({
          user: { id: response.user_id, email: credentials.account_id },
          isAuthenticated: true,
          loading: false,
        });
        
        return { success: true, nextStep: response.next_step };
      } else {
        setState(prev => ({ ...prev, loading: false }));
        return { success: false, error: getErrorMessage(response.errorCode) };
      }
    } catch (error) {
      setState(prev => ({ ...prev, loading: false }));
      return { success: false, error: '로그인 중 오류가 발생했습니다.' };
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiClient.post('/account/logout', {});
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      apiClient.clearToken();
      setState({
        user: null,
        isAuthenticated: false,
        loading: false,
      });
    }
  }, []);

  return {
    ...state,
    login,
    logout,
  };
}
```

### 3. 포트폴리오 Hook

```typescript
// hooks/usePortfolio.ts
import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '../lib/api/client';
import { PortfolioGetResponse } from '../types/api';

export function usePortfolio() {
  const [portfolio, setPortfolio] = useState<PortfolioGetResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPortfolio = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await apiClient.post<PortfolioGetResponse>('/portfolio/get');
      
      if (response.errorCode === 0) {
        setPortfolio(response);
      } else {
        setError(getErrorMessage(response.errorCode));
      }
    } catch (error) {
      setError('포트폴리오 정보를 불러오는 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  }, []);

  const addStock = useCallback(async (symbol: string, quantity: number, price: number) => {
    try {
      const response = await apiClient.post('/portfolio/add-stock', {
        symbol,
        quantity,
        price,
      });
      
      if (response.errorCode === 0) {
        // 포트폴리오 새로고침
        await fetchPortfolio();
        return { success: true };
      } else {
        return { success: false, error: getErrorMessage(response.errorCode) };
      }
    } catch (error) {
      return { success: false, error: '주식 추가 중 오류가 발생했습니다.' };
    }
  }, [fetchPortfolio]);

  const removeStock = useCallback(async (symbol: string, quantity: number) => {
    try {
      const response = await apiClient.post('/portfolio/remove-stock', {
        symbol,
        quantity,
      });
      
      if (response.errorCode === 0) {
        await fetchPortfolio();
        return { success: true };
      } else {
        return { success: false, error: getErrorMessage(response.errorCode) };
      }
    } catch (error) {
      return { success: false, error: '주식 제거 중 오류가 발생했습니다.' };
    }
  }, [fetchPortfolio]);

  useEffect(() => {
    fetchPortfolio();
  }, [fetchPortfolio]);

  return {
    portfolio,
    loading,
    error,
    refresh: fetchPortfolio,
    addStock,
    removeStock,
  };
}
```

### 4. 채팅 Hook

```typescript
// hooks/useChat.ts
import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '../lib/api/client';
import { 
  ChatRoomListResponse, 
  ChatMessageSendResponse, 
  ChatMessageListResponse 
} from '../types/api';

interface Message {
  id: string;
  content: string;
  sender: string;
  timestamp: string;
  isUser: boolean;
}

export function useChat(roomId?: string) {
  const [rooms, setRooms] = useState<any[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);

  const fetchRooms = useCallback(async () => {
    setLoading(true);
    try {
      const response = await apiClient.post<ChatRoomListResponse>('/chat/rooms');
      if (response.errorCode === 0) {
        setRooms(response.rooms || []);
      }
    } catch (error) {
      console.error('채팅방 목록 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchMessages = useCallback(async (targetRoomId: string) => {
    if (!targetRoomId) return;
    
    setLoading(true);
    try {
      const response = await apiClient.post<ChatMessageListResponse>('/chat/messages', {
        room_id: targetRoomId,
      });
      
      if (response.errorCode === 0) {
        setMessages(response.messages || []);
      }
    } catch (error) {
      console.error('메시지 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  const sendMessage = useCallback(async (content: string, targetRoomId?: string) => {
    if (!content.trim() || (!roomId && !targetRoomId)) return;
    
    setSending(true);
    try {
      const response = await apiClient.post<ChatMessageSendResponse>('/chat/message/send', {
        room_id: targetRoomId || roomId,
        content,
      });
      
      if (response.errorCode === 0) {
        // 메시지 목록에 추가
        const newMessage: Message = {
          id: response.message_id,
          content: response.content,
          sender: 'user',
          timestamp: response.sent_at,
          isUser: true,
        };
        setMessages(prev => [...prev, newMessage]);
        return { success: true };
      } else {
        return { success: false, error: getErrorMessage(response.errorCode) };
      }
    } catch (error) {
      return { success: false, error: '메시지 전송 중 오류가 발생했습니다.' };
    } finally {
      setSending(false);
    }
  }, [roomId]);

  const createRoom = useCallback(async () => {
    try {
      const response = await apiClient.post('/chat/room/create');
      if (response.errorCode === 0) {
        await fetchRooms();
        return { success: true, roomId: response.room_id };
      } else {
        return { success: false, error: getErrorMessage(response.errorCode) };
      }
    } catch (error) {
      return { success: false, error: '채팅방 생성 중 오류가 발생했습니다.' };
    }
  }, [fetchRooms]);

  useEffect(() => {
    fetchRooms();
  }, [fetchRooms]);

  useEffect(() => {
    if (roomId) {
      fetchMessages(roomId);
    }
  }, [roomId, fetchMessages]);

  return {
    rooms,
    messages,
    loading,
    sending,
    sendMessage,
    createRoom,
    fetchMessages,
    refreshRooms: fetchRooms,
  };
}
```

---

## 🛠️ 유틸리티 함수

### 1. 에러 처리 유틸리티

```typescript
// utils/errorHandler.ts
export const ERROR_CODES = {
  SUCCESS: 0,
  AUTHENTICATION_FAILED: 1001,
  UNAUTHORIZED: 1002,
  INVALID_PARAMETERS: 1003,
  RESOURCE_NOT_FOUND: 1004,
  SERVER_ERROR: 1005,
} as const;

export const getErrorMessage = (errorCode: number): string => {
  const messages: Record<number, string> = {
    [ERROR_CODES.SUCCESS]: '성공',
    [ERROR_CODES.AUTHENTICATION_FAILED]: '인증에 실패했습니다.',
    [ERROR_CODES.UNAUTHORIZED]: '권한이 없습니다.',
    [ERROR_CODES.INVALID_PARAMETERS]: '입력 정보를 확인해주세요.',
    [ERROR_CODES.RESOURCE_NOT_FOUND]: '요청한 정보를 찾을 수 없습니다.',
    [ERROR_CODES.SERVER_ERROR]: '서버 오류가 발생했습니다.',
  };
  
  return messages[errorCode] || `오류가 발생했습니다. (코드: ${errorCode})`;
};

export const isAuthError = (errorCode: number): boolean => {
  return errorCode === ERROR_CODES.AUTHENTICATION_FAILED || 
         errorCode === ERROR_CODES.UNAUTHORIZED;
};
```

### 2. 데이터 포맷팅 유틸리티

```typescript
// utils/formatters.ts
export const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('ko-KR', {
    style: 'currency',
    currency: 'KRW',
  }).format(value);
};

export const formatPercentage = (value: number): string => {
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
};

export const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

export const formatStockPrice = (price: number): string => {
  return price.toLocaleString('ko-KR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
};
```

### 3. 로컬 스토리지 유틸리티

```typescript
// utils/storage.ts
class Storage {
  static get(key: string): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(key);
  }

  static set(key: string, value: string): void {
    if (typeof window === 'undefined') return;
    localStorage.setItem(key, value);
  }

  static remove(key: string): void {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(key);
  }

  static clear(): void {
    if (typeof window === 'undefined') return;
    localStorage.clear();
  }

  static getObject<T>(key: string): T | null {
    const value = this.get(key);
    if (!value) return null;
    
    try {
      return JSON.parse(value);
    } catch {
      return null;
    }
  }

  static setObject<T>(key: string, value: T): void {
    this.set(key, JSON.stringify(value));
  }
}

export default Storage;
```

---

## 🎯 React Context

### 1. Auth Context

```typescript
// contexts/AuthContext.tsx
import React, { createContext, useContext, useEffect, useState } from 'react';
import { useAuth } from '../hooks/useAuth';

interface AuthContextType {
  user: any;
  isAuthenticated: boolean;
  loading: boolean;
  login: (credentials: any) => Promise<any>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const auth = useAuth();

  return (
    <AuthContext.Provider value={auth}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuthContext = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuthContext must be used within an AuthProvider');
  }
  return context;
};
```

### 2. Portfolio Context

```typescript
// contexts/PortfolioContext.tsx
import React, { createContext, useContext } from 'react';
import { usePortfolio } from '../hooks/usePortfolio';

interface PortfolioContextType {
  portfolio: any;
  loading: boolean;
  error: string | null;
  refresh: () => void;
  addStock: (symbol: string, quantity: number, price: number) => Promise<any>;
  removeStock: (symbol: string, quantity: number) => Promise<any>;
}

const PortfolioContext = createContext<PortfolioContextType | undefined>(undefined);

export const PortfolioProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const portfolio = usePortfolio();

  return (
    <PortfolioContext.Provider value={portfolio}>
      {children}
    </PortfolioContext.Provider>
  );
};

export const usePortfolioContext = () => {
  const context = useContext(PortfolioContext);
  if (context === undefined) {
    throw new Error('usePortfolioContext must be used within a PortfolioProvider');
  }
  return context;
};
```

---

## 🚀 실제 사용 예시

### 1. 로그인 컴포넌트

```typescript
// components/LoginForm.tsx
import React, { useState } from 'react';
import { useAuthContext } from '../contexts/AuthContext';
import { formatters } from '../utils/formatters';

const LoginForm: React.FC = () => {
  const { login, loading } = useAuthContext();
  const [formData, setFormData] = useState({
    platform_type: 'native',
    account_id: '',
    password: '',
  });
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    const result = await login(formData);
    
    if (result.success) {
      // 성공 처리
      if (result.nextStep === 'COMPLETE') {
        window.location.href = '/dashboard';
      } else if (result.nextStep === 'PROFILE') {
        window.location.href = '/profile/setup';
      }
    } else {
      setError(result.error);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700">
          이메일
        </label>
        <input
          type="email"
          value={formData.account_id}
          onChange={(e) => setFormData({...formData, account_id: e.target.value})}
          required
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">
          비밀번호
        </label>
        <input
          type="password"
          value={formData.password}
          onChange={(e) => setFormData({...formData, password: e.target.value})}
          required
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
        />
      </div>

      {error && (
        <div className="text-red-600 text-sm">{error}</div>
      )}

      <button
        type="submit"
        disabled={loading}
        className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
      >
        {loading ? '로그인 중...' : '로그인'}
      </button>
    </form>
  );
};

export default LoginForm;
```

### 2. 포트폴리오 컴포넌트

```typescript
// components/PortfolioView.tsx
import React from 'react';
import { usePortfolioContext } from '../contexts/PortfolioContext';
import { formatCurrency, formatPercentage } from '../utils/formatters';

const PortfolioView: React.FC = () => {
  const { portfolio, loading, error, refresh } = usePortfolioContext();

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-4">{error}</div>
        <button
          onClick={refresh}
          className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
        >
          다시 시도
        </button>
      </div>
    );
  }

  if (!portfolio?.portfolio) {
    return <div className="text-center py-12">포트폴리오 데이터가 없습니다.</div>;
  }

  return (
    <div className="space-y-6">
      {/* 포트폴리오 요약 */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4">포트폴리오 요약</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">
              {formatCurrency(portfolio.portfolio.total_value)}
            </div>
            <div className="text-sm text-gray-500">총 자산</div>
          </div>
          <div className="text-center">
            <div className={`text-2xl font-bold ${portfolio.portfolio.performance.total_return >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatPercentage(portfolio.portfolio.performance.total_return)}
            </div>
            <div className="text-sm text-gray-500">총 수익률</div>
          </div>
          <div className="text-center">
            <div className={`text-2xl font-bold ${portfolio.portfolio.performance.daily_change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
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
          <table className="min-w-full table-auto">
            <thead>
              <tr className="bg-gray-50">
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">종목</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">수량</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">평균 단가</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">현재 가격</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">손익</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {portfolio.portfolio.holdings.map((holding: any, index: number) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {holding.symbol}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {holding.quantity.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatCurrency(holding.avg_price)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatCurrency(holding.current_price)}
                  </td>
                  <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${holding.profit_loss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
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

export default PortfolioView;
```

### 3. 채팅 컴포넌트

```typescript
// components/ChatRoom.tsx
import React, { useState, useRef, useEffect } from 'react';
import { useChat } from '../hooks/useChat';
import { formatDate } from '../utils/formatters';

interface ChatRoomProps {
  roomId: string;
}

const ChatRoom: React.FC<ChatRoomProps> = ({ roomId }) => {
  const { messages, sending, sendMessage } = useChat(roomId);
  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim()) return;

    const result = await sendMessage(inputMessage);
    if (result?.success) {
      setInputMessage('');
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* 메시지 목록 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                message.isUser
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-200 text-gray-800'
              }`}
            >
              <div className="text-sm">{message.content}</div>
              <div className="text-xs mt-1 opacity-70">
                {formatDate(message.timestamp)}
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* 메시지 입력 */}
      <div className="border-t bg-white p-4">
        <form onSubmit={handleSubmit} className="flex space-x-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="메시지를 입력하세요..."
            className="flex-1 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            disabled={sending}
          />
          <button
            type="submit"
            disabled={sending || !inputMessage.trim()}
            className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 disabled:opacity-50"
          >
            {sending ? '전송 중...' : '전송'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatRoom;
```

---

## 🎉 마무리

이 Hook들과 유틸리티를 사용하면 Base Server API를 React에서 훨씬 쉽게 사용할 수 있습니다!

### 핵심 장점:
- **간단한 API**: 복잡한 로직 숨김
- **타입 안전성**: TypeScript 완전 지원
- **에러 처리**: 자동화된 에러 처리
- **로딩 상태**: 내장된 로딩 상태 관리
- **재사용성**: 모든 컴포넌트에서 재사용 가능

### 사용 방법:
1. 필요한 Hook을 import
2. 컴포넌트에서 사용
3. 로딩, 에러 상태 자동 처리
4. 성공/실패 콜백 활용

이제 백엔드 API를 React에서 정말 쉽게 사용할 수 있습니다! 🚀