# AI Trading Advisor Platform - Frontend

## 프로젝트 개요

AI 기반 트레이딩 어드바이저 플랫폼의 프론트엔드입니다. Next.js 14, TypeScript, Tailwind CSS를 사용하여 구축되었으며, Duolingo의 직관적인 UX와 MarketMakers의 전문적인 트레이딩 인터페이스를 결합한 디자인을 제공합니다.

## 기술 스택

### 핵심 프레임워크
- **Next.js 14** (App Router)
- **React 18**
- **TypeScript**
- **Tailwind CSS**

### UI 라이브러리
- **shadcn/ui** - 모던하고 접근성이 좋은 컴포넌트
- **Lucide React** - 아이콘
- **Recharts** - 데이터 시각화

### 상태 관리
- **Redux Toolkit** - 전역 상태 관리
- **React Query** - 서버 상태 관리

### 인증 & 보안
- **NextAuth.js** - 인증
- **JWT** - 토큰 기반 인증

### 통신
- **Axios** - HTTP 클라이언트
- **WebSocket** - 실시간 데이터

## 폴더 구조

\`\`\`
frontend/
├── app/                          # Next.js App Router
│   ├── (auth)/                   # 인증 관련 페이지
│   │   ├── login/
│   │   └── register/
│   ├── dashboard/                # 대시보드
│   ├── chat/                     # AI 챗봇
│   ├── portfolio/                # 포트폴리오
│   ├── market/                   # 마켓 분석
│   ├── autotrade/                # 자동매매
│   ├── notifications/            # 알림
│   ├── settings/                 # 설정
│   ├── tutorial/                 # 튜토리얼
│   ├── layout.tsx                # 루트 레이아웃
│   ├── page.tsx                  # 홈페이지
│   └── globals.css               # 전역 스타일
├── components/                   # 재사용 가능한 컴포넌트
│   ├── ui/                       # shadcn/ui 컴포넌트
│   ├── layout/                   # 레이아웃 컴포넌트
│   ├── dashboard/                # 대시보드 컴포넌트
│   ├── chat/                     # 챗봇 컴포넌트
│   ├── portfolio/                # 포트폴리오 컴포넌트
│   ├── market/                   # 마켓 컴포넌트
│   └── common/                   # 공통 컴포넌트
├── lib/                          # 유틸리티 및 설정
│   ├── store/                    # Redux 스토어
│   │   ├── slices/               # Redux 슬라이스
│   │   └── index.ts
│   ├── api/                      # API 클라이언트
│   │   ├── client.ts
│   │   ├── endpoints.ts
│   │   └── types.ts
│   ├── hooks/                    # 커스텀 훅
│   ├── utils/                    # 유틸리티 함수
│   └── auth.ts                   # 인증 설정
├── providers/                    # Context Providers
│   ├── auth-provider.tsx
│   ├── store-provider.tsx
│   └── websocket-provider.tsx
├── types/                        # TypeScript 타입 정의
├── public/                       # 정적 파일
└── package.json
\`\`\`

## 주요 기능

### 1. 대시보드
- 실시간 시장 현황
- 포트폴리오 요약
- AI 인사이트
- 트레이딩 시그널

### 2. AI 챗봇
- 자연어 기반 질의응답
- 다양한 AI 도구 연동
- 실시간 스트리밍 응답
- 대화 히스토리 관리

### 3. 포트폴리오 관리
- 실시간 포트폴리오 현황
- 수익률 분석
- 거래 내역
- 리스크 분석

### 4. 마켓 분석
- 실시간 시장 데이터
- 기술적 분석
- 뉴스 및 이벤트
- AI 기반 시장 예측

### 5. 자동매매
- 전략 설정 및 관리
- 백테스팅
- 실시간 시그널
- 성과 분석

## 상태 관리 구조

### Redux Store 구조
\`\`\`typescript
interface RootState {
  auth: AuthState          // 사용자 인증 상태
  market: MarketState      // 시장 데이터
  portfolio: PortfolioState // 포트폴리오 상태
  chat: ChatState          // 챗봇 상태
  notification: NotificationState // 알림 상태
}
\`\`\`

### 주요 슬라이스
- **authSlice**: 로그인, 로그아웃, 사용자 정보
- **marketSlice**: 시장 데이터, 주식 정보
- **portfolioSlice**: 포트폴리오, 거래 내역
- **chatSlice**: 챗봇 대화, AI 도구
- **notificationSlice**: 알림 관리

## API 연동

### HTTP 통신
- Axios 기반 HTTP 클라이언트
- 자동 토큰 갱신
- 에러 핸들링
- 요청/응답 인터셉터

### WebSocket 통신
- 실시간 시장 데이터
- 챗봇 스트리밍
- 알림 푸시
- 포트폴리오 업데이트

## 설치 및 실행

### 환경 설정
\`\`\`bash
# 의존성 설치
npm install

# 환경 변수 설정
cp .env.example .env.local
\`\`\`

### 개발 서버 실행
\`\`\`bash
npm run dev
\`\`\`

### 빌드
\`\`\`bash
npm run build
npm start
\`\`\`

## 환경 변수

\`\`\`env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXTAUTH_SECRET=your-secret-key
NEXTAUTH_URL=http://localhost:3000
\`\`\`

## 개발 가이드라인

### 컴포넌트 작성 규칙
1. 함수형 컴포넌트 사용
2. TypeScript 타입 정의 필수
3. Props 인터페이스 정의
4. 재사용 가능한 컴포넌트 작성

### 상태 관리 규칙
1. Redux Toolkit 사용
2. 비동기 작업은 createAsyncThunk 사용
3. 불변성 유지
4. 정규화된 상태 구조

### API 호출 규칙
1. React Query 사용 권장
2. 에러 핸들링 필수
3. 로딩 상태 관리
4. 캐싱 전략 고려

## 배포

### Vercel 배포
\`\`\`bash
npm run build
vercel --prod
\`\`\`

### Docker 배포
\`\`\`bash
docker build -t ai-trading-frontend .
docker run -p 3000:3000 ai-trading-frontend
\`\`\`
\`\`\`

```mermaid title="시스템 아키텍처" type="diagram"
graph TB
    subgraph "Frontend (Next.js)"
        A[App Router] --> B[Dashboard]
        A --> C[Chat Interface]
        A --> D[Portfolio]
        A --> E[Market Analysis]
        A --> F[Auto Trading]
        
        B --> G[Market Overview]
        B --> H[AI Insights]
        B --> I[Trading Signals]
        
        C --> J[Chat Messages]
        C --> K[AI Tools Panel]
        C --> L[Chat History]
    end
    
    subgraph "State Management"
        M[Redux Store] --> N[Auth Slice]
        M --> O[Market Slice]
        M --> P[Portfolio Slice]
        M --> Q[Chat Slice]
        M --> R[Notification Slice]
    end
    
    subgraph "API Layer"
        S[HTTP Client] --> T[REST APIs]
        U[WebSocket Client] --> V[Real-time Data]
    end
    
    subgraph "Backend (FastAPI)"
        W[base_server] --> X[Routers]
        X --> Y[Dashboard API]
        X --> Z[Chat API]
        X --> AA[Portfolio API]
        X --> BB[Market API]
        X --> CC[AutoTrade API]
        
        W --> DD[AIChat Tools]
        W --> EE[Database]
        W --> FF[External APIs]
    end
    
    A --> M
    M --> S
    M --> U
    S --> W
    U --> W
    
    style A fill:#e1f5fe
    style M fill:#f3e5f5
    style W fill:#e8f5e8
