
⸻

# AI Trading Platform — Frontend (Next.js)

> **개요**: SKN12-FINAL-2TEAM의 AI 트레이딩 플랫폼 프론트엔드입니다. Next.js 15, React 18, TypeScript를 기반으로 실시간 시세(WebSocket), AI 챗봇(SSE), 포트폴리오 관리(REST)를 통합한 현대적인 웹 애플리케이션입니다.

---

## 🏗️ 프로젝트 구조

### 디렉토리 구조
```
ai-trading-platform/
├── app/                    # Next.js App Router
│   ├── (auth)/            # 인증 페이지 (로그인/회원가입)
│   ├── dashboard/         # 대시보드 (실시간 시세)
│   ├── chat/              # AI 챗봇
│   ├── portfolio/         # 포트폴리오 관리
│   ├── autotrade/         # 자동매매 설정
│   ├── market/            # 시장 데이터
│   ├── tutorial/          # 온보딩 튜토리얼
│   ├── onboarding/        # 사용자 온보딩
│   ├── reports/           # 리포트 및 분석
│   ├── notifications/     # 알림 관리
│   ├── realtime/          # 실시간 데이터 테스트
│   ├── websocket-test/    # WebSocket 테스트
│   ├── error-test/        # 에러 처리 테스트
│   └── layout.tsx         # 루트 레이아웃
├── components/             # UI 컴포넌트
│   ├── ui/                # 기본 UI (shadcn/ui)
│   ├── dashboard/         # 대시보드 전용
│   ├── chat/              # 챗봇 관련
│   ├── portfolio/         # 포트폴리오 관련
│   ├── market/            # 시장 데이터 관련
│   ├── autotrade/         # 자동매매 관련
│   ├── layout/            # 레이아웃 컴포넌트
│   ├── landing/           # 랜딩 페이지
│   ├── reports/           # 리포트 관련
│   └── tutorial/          # 튜토리얼 관련
├── hooks/                  # 커스텀 훅
├── lib/                    # 유틸리티 및 API 클라이언트
├── providers/              # React Context Providers
├── types/                  # TypeScript 타입 정의
├── styles/                 # 글로벌 스타일
└── public/                 # 정적 리소스
```

---

## 🔧 핵심 기능

### 1. **실시간 시세 시스템 (WebSocket)**
- **NasdaqStocksStore**: Zustand 기반 실시간 주식 데이터 관리
- **자동 재연결**: 연결 끊김 시 지수 백오프로 재연결
- **멀티 심볼 구독**: 여러 주식 심볼 동시 모니터링
- **백필 데이터**: 연결 복구 시 누락된 데이터 자동 보충

### 2. **AI 챗봇 (Server-Sent Events)**
- **스트리밍 응답**: 토큰 단위 실시간 AI 응답
- **타이핑 애니메이션**: setInterval 기반 문자 단위 렌더링
- **하트비트 관리**: 15-30초 간격 연결 상태 확인
- **타임아웃 처리**: 120초 무응답 시 자동 재연결

### 3. **포트폴리오 관리**
- **실시간 업데이트**: WebSocket으로 포트폴리오 변화 감지
- **CRUD 작업**: REST API를 통한 포트폴리오 조작
- **데이터 동기화**: 로컬 상태와 서버 상태 자동 동기화

### 4. **온보딩 튜토리얼**
- **단계별 가이드**: 사용자 경험 향상을 위한 단계별 안내
- **진행 상태 저장**: 사용자별 튜토리얼 진행 상황 추적
- **적응형 콘텐츠**: 사용자 행동에 따른 맞춤형 안내

---

## 📚 사용된 라이브러리

### **Core Framework**
- **Next.js 15.4.2**: App Router, Server Components, SSR/SSG
- **React 18.2.0**: Concurrent Features, Suspense, Error Boundaries
- **TypeScript 5.8.3**: 정적 타입 검사, 타입 안전성

### **상태 관리**
- **Zustand**: 전역 상태 관리 (실시간 시세, 사용자 정보)
- **React Context**: 인증 상태, 테마, 전역 설정
- **React Query/SWR**: 서버 상태 관리 (계획)

### **UI & Styling**
- **TailwindCSS**: 유틸리티 기반 CSS 프레임워크
- **shadcn/ui**: 재사용 가능한 UI 컴포넌트 라이브러리
- **PostCSS**: CSS 후처리 및 최적화

### **네트워크 & 통신**
- **Axios**: HTTP 클라이언트 (REST API)
- **WebSocket API**: 실시간 시세 데이터
- **EventSource**: Server-Sent Events (AI 챗봇)

### **개발 도구**
- **ESLint**: 코드 품질 검사
- **Prettier**: 코드 포맷팅
- **Husky**: Git hooks 관리

---

## 🪝 훅 (Hooks) 구현 방식

### **useAuth - 인증 관리**
```typescript
// hooks/use-auth.ts
export const useAuth = () => {
  const { state, login, logout, refreshToken } = useContext(AuthContext);
  
  return {
    user: state.user,
    isAuthenticated: !!state.token,
    accessTokenReady: () => !!state.token && state.expiresAt > Date.now(),
    getToken: () => state.token,
    login,
    logout,
    refreshToken
  };
};
```

**동작 방식**:
- AuthContext를 통해 전역 인증 상태 관리
- 토큰 만료 시간 체크로 자동 갱신 필요성 판단
- LocalStorage에 토큰 저장 (향후 httpOnly 쿠키 전환 예정)

### **useNasdaqStocks - 실시간 시세**
```typescript
// hooks/use-nasdaq-stocks.ts
export const useNasdaqStocks = () => {
  const store = useNasdaqStocksStore();
  
  useEffect(() => {
    store.initWs();
    return () => store.cleanup();
  }, []);
  
  return {
    stocks: store.stocks,
    addSymbol: store.addSymbol,
    removeSymbol: store.removeSymbol,
    isConnected: store.isConnected
  };
};
```

**동작 방식**:
- Zustand 스토어와 연동하여 실시간 데이터 관리
- WebSocket 연결 자동 초기화 및 정리
- 컴포넌트 언마운트 시 연결 정리

### **useChat - AI 챗봇**
```typescript
// hooks/use-chat.ts
export const useChat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  
  const sendMessage = async (content: string) => {
    // SSE 스트리밍 처리
    const eventSource = new EventSource(`/api/chat?message=${content}`);
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'delta') {
        setMessages(prev => [...prev, { role: 'assistant', content: data.content }]);
      }
    };
  };
  
  return { messages, sendMessage, isStreaming };
};
```

**동작 방식**:
- EventSource를 통한 서버-센트 이벤트 처리
- 스트리밍 데이터를 실시간으로 UI에 반영
- 메시지 히스토리 상태 관리

---

## 🌐 API 연동 방식

### **API 클라이언트 구조**
```typescript
// lib/api/client.ts
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  timeout: parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT || '10000'),
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터 - 토큰 자동 추가
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('accessToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 응답 인터셉터 - 토큰 만료 처리
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // 토큰 갱신 시도
      const newToken = await refreshToken();
      if (newToken) {
        error.config.headers.Authorization = `Bearer ${newToken}`;
        return apiClient.request(error.config);
      }
    }
    return Promise.reject(error);
  }
);
```

### **포트폴리오 API 예시**
```typescript
// lib/api/portfolio.ts
export const portfolioAPI = {
  // 포트폴리오 조회
  getPortfolio: async (): Promise<Portfolio> => {
    const response = await apiClient.get('/api/portfolio');
    return response.data;
  },
  
  // 포트폴리오 업데이트
  updatePortfolio: async (portfolio: Partial<Portfolio>): Promise<void> => {
    await apiClient.patch('/api/portfolio', portfolio);
  },
  
  // 거래 내역 조회
  getTransactions: async (params: TransactionParams): Promise<Transaction[]> => {
    const response = await apiClient.get('/api/transactions', { params });
    return response.data;
  }
};
```

---

## 🔄 프론트엔드 전체 흐름

### **1. 애플리케이션 초기화**
```
1. _app.tsx → Providers 설정
   ├── AuthProvider (인증 상태)
   ├── StoreProvider (Zustand 스토어)
   └── ThemeProvider (테마 설정)

2. layout.tsx → 전역 레이아웃 구성
   ├── Navigation 컴포넌트
   ├── Sidebar 컴포넌트
   └── Error Boundary 설정
```

### **2. 인증 플로우**
```
1. 사용자 로그인 시도
2. AuthProvider에서 토큰 저장
3. LocalStorage에 토큰 보관
4. 보호된 라우트 접근 시 토큰 검증
5. 토큰 만료 시 자동 갱신 또는 로그인 페이지 리다이렉트
```

### **3. 실시간 데이터 플로우**
```
1. 대시보드 진입
2. useNasdaqStocks 훅 초기화
3. WebSocket 연결 수립
4. 관심 심볼 구독
5. 실시간 틱 데이터 수신
6. Zustand 스토어 상태 업데이트
7. 컴포넌트 자동 리렌더링
```

### **4. AI 챗봇 플로우**
```
1. 사용자 메시지 입력
2. useChat 훅에서 EventSource 생성
3. SSE 연결으로 서버와 통신
4. 스트리밍 응답 데이터 수신
5. 타이핑 애니메이션으로 UI 업데이트
6. 메시지 히스토리 상태 관리
```

---

## 🔌 WebSocket 구현 상세

### **연결 관리**
```typescript
// lib/websocket.ts
class WebSocketManager {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  connect(url: string) {
    this.ws = new WebSocket(url);
    
    this.ws.onopen = () => {
      console.log('WebSocket 연결됨');
      this.reconnectAttempts = 0;
      this.subscribeToSymbols();
    };
    
    this.ws.onclose = () => {
      console.log('WebSocket 연결 끊김');
      this.handleReconnect();
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket 에러:', error);
    };
  }

  private handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
      
      setTimeout(() => {
        console.log(`재연결 시도 ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
        this.connect(this.ws?.url || '');
      }, delay);
    }
  }
}
```

### **데이터 처리**
```typescript
// Zustand 스토어에서 WebSocket 데이터 처리
const useNasdaqStocksStore = create<NasdaqStocksState>((set, get) => ({
  stocks: {},
  isConnected: false,
  
  initWs: async () => {
    const ws = new WebSocket(process.env.NEXT_PUBLIC_WS_URL!);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'tick') {
        set((state) => ({
          stocks: {
            ...state.stocks,
            [data.symbol]: {
              price: data.price,
              change: data.change,
              timestamp: Date.now()
            }
          }
        }));
      }
    };
  }
}));
```

---

## 🎯 코드 철학

### **1. 단방향 데이터 흐름**
- **상태 → UI**: Zustand 스토어에서 컴포넌트로 단방향 데이터 전달
- **Props → Children**: 부모에서 자식으로 명확한 데이터 전달
- **이벤트 → 핸들러**: 사용자 액션을 명확한 이벤트 핸들러로 처리

### **2. 관심사 분리**
- **비즈니스 로직**: 훅과 스토어에 집중
- **UI 렌더링**: 컴포넌트는 순수 함수로 유지
- **데이터 관리**: API 클라이언트와 상태 관리 분리

### **3. 성능 최적화 우선**
- **React.memo**: 불필요한 리렌더링 방지
- **useMemo/useCallback**: 의존성 배열 최적화
- **코드 스플릿**: 동적 임포트로 번들 크기 최적화

### **4. 개발자 경험**
- **TypeScript**: 타입 안전성과 자동완성
- **일관된 네이밍**: 명확하고 예측 가능한 함수/변수명
- **에러 바운더리**: 컴포넌트별 에러 처리

---

## 🚀 개선할 점

### **1. 성능 최적화**
- [ ] **타이핑 애니메이션**: setInterval → requestAnimationFrame 전환
- [ ] **가상화**: 대용량 리스트 렌더링 최적화
- [ ] **메모리 관리**: WebSocket 연결 풀링 및 메시지 버퍼링

### **2. 보안 강화**
- [ ] **토큰 저장**: LocalStorage → httpOnly 쿠키 전환
- [ ] **CSP 설정**: Content Security Policy 적용
- [ ] **XSS 방지**: DOMPurify를 통한 콘텐츠 정화

### **3. 사용자 경험**
- [ ] **오프라인 지원**: Service Worker 및 캐시 전략
- [ ] **로딩 상태**: 스켈레톤 UI 및 스피너 개선
- [ ] **에러 처리**: 사용자 친화적인 에러 메시지

### **4. 코드 품질**
- [ ] **테스트 커버리지**: Jest + React Testing Library
- [ ] **E2E 테스트**: Playwright를 통한 사용자 시나리오 테스트
- [ ] **정적 분석**: ESLint 규칙 강화 및 자동화

### **5. 모니터링 및 관측성**
- [ ] **성능 메트릭**: Core Web Vitals 측정
- [ ] **에러 추적**: Sentry 또는 유사 도구 연동
- [ ] **사용자 행동**: Google Analytics 4 연동

---

## 🛠️ 개발 환경 설정

### **환경 변수**
```bash
# .env.local
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_WS_URL=ws://127.0.0.1:8000
NEXT_PUBLIC_SSE_URL=http://127.0.0.1:8000
NEXT_PUBLIC_API_TIMEOUT=10000
```

### **개발 명령어**
```bash
npm run dev          # 개발 서버 실행
npm run build        # 프로덕션 빌드
npm run start        # 프로덕션 서버 시작
npm run lint         # 코드 품질 검사
npm run type-check   # TypeScript 타입 체크
```

---

## 📚 추가 리소스

- **API 문서**: `/docs/api.md`
- **컴포넌트 가이드**: `/docs/components.md`
- **상태 관리 가이드**: `/docs/state-management.md`
- **테스트 가이드**: `/docs/testing.md`

---

> **문서 버전**: v1.0 (실제 구현 기반)  
> **최종 업데이트**: 2025년 1월  
> **담당자**: Frontend Development Team

