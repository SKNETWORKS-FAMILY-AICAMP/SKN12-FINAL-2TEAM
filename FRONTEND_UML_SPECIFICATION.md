# SKN12-FINAL-2TEAM — Frontend UML Specification 

> **목표:** 이 문서는 SKN12-FINAL-2TEAM 프론트엔드(Next.js 15.4.2, React 18.2.0, TypeScript 5.8.3)의 구조를 **UML 중심**으로 정밀 해부한다. 설계 의도, 모듈 경계, 상호작용, 수명주기, 오류/재시도, 보안, 성능까지 **실전 배포 관점**에서 다룬다. AI가 학습해도 손색없는 수준으로 명세화한다.

---

## 0. 전제와 범위

* **대상 범위:** `base_server/frontend/ai-trading-platform/`의 `app/`(App Router), `components/`, `hooks/`, `lib/`, `providers/`, `types/` 그리고 브라우저 ↔ Edge/Node 런타임 ↔ 백엔드(API, WS, SSE) 인터랙션.
* **통신 프로토콜:** REST(axios), SSE(EventSource), WebSocket.
* **상태관리:** 로컬 상태(React), 전역(Zustand), 서버 상태(SWR/React Query 가정 가능).
* **인증:** 토큰 기반 (UUID 문자열). 토큰 저장소는 브라우저(Storage) + Context.
* **가정:** 실시간 시세는 WS로, 챗봇은 SSE로, 포트폴리오/설정은 REST로 운용. Next.js 서버 컴포넌트와 클라이언트 컴포넌트 분리를 적극 활용.

> **NOTE:** 이 문서는 **As-Is(현재 구현)**와 **To-Be(개선안)**를 명확히 구분한다.
> - **실선 + 기본색**: 현재 구현된 기능
> - **점선 + <<planned>>**: 향후 개선 계획
> - **Gap 분석**: 현재와 목표 간 차이점
> - **마이그레이션**: 개선 적용 절차

---

## 1. 유스케이스 모델 (Use‑Case)

### 1.1 액터 & 유스케이스 개요 (As-Is)

* **액터**
  * *User* (투자자, 일반 사용자)
  * *Auth Service* (토큰 발급/검증)
  * *Market WS Broker* (시세 푸시)
  * *Chat SSE Gateway* (AI 응답 스트림)
  * *Portfolio API* (자산/거래/리밸런싱)
  * *Trade Engine API* (자동매매 설정/시그널)

![유스케이스 다이어그램 (As-Is)](docs/uml/use-case-as-is.svg)

**핵심 시나리오 요약 (As-Is)**

1. 로그인 성공 → 토큰 획득 → 보호 라우트 진입.
2. 대시보드 진입 시, WS 연결 수립 → 관심 심볼 구독 → 실시간 반영.
3. 챗 입력 → SSE 스트림 수신 → requestAnimationFrame 타이핑 애니메이션.
4. 포트폴리오 CRUD → REST 교환 후 전역/서버 상태 동기화.
5. 자동매매 설정 변경 → 서버 반영 + 로컬 스냅샷.
6. 튜토리얼 진행 → 단계별 가이드 → 완료 상태 저장.

---

### 1.2 향후 개선 계획 (To-Be)

![유스케이스 다이어그램 (To-Be)](docs/uml/use-case-to-be.svg)

**향후 개선 시나리오**

1. **오프라인 모드**: 네트워크 불안정 시 캐시된 데이터로 기본 기능 제공
2. **PWA 지원**: 모바일 앱처럼 설치 및 푸시 알림
3. **고급 분석**: AI 기반 포트폴리오 최적화 및 리스크 분석
4. **소셜 트레이딩**: 다른 투자자의 전략 공유 및 팔로우

---

## 2. 패키지 다이어그램 (Package)

### 2.1 현재 구조 (As-Is)

소스 트리의 **의존 방향**과 층위를 명확히 한다. `components`는 `hooks/lib/providers/types`에 **의존**하되, 역의존을 금한다.

![패키지 구조 다이어그램](docs/uml/package-structure.svg)

**규율:** 상위 레이어는 하위 레이어로만 의존(단방향). `lib/`는 순수 유틸/클라이언트로 유지, React 의존 최소화.

---

### 2.2 향후 개선 구조 (To-Be)

```plantuml
@startuml
package "app/ (App Router)" as APP {
  [layout.tsx]
  [page.tsx]
  package "(auth)/" as AUTH
  package "dashboard/" as DASH
  package "chat/" as CHAT
  package "portfolio/" as PORT
  package "market/" as MKT
  package "autotrade/" as AT
  package "settings/" as SET
  package "tutorial/" as TUT
  package "onboarding/" as ONB
  package "reports/" as REP
  package "notifications/" as NOT
  package "realtime/" as RT
  package "websocket-test/" as WST
  package "error-test/" as ET
  
  package "offline/" as OFFLINE <<planned>>
  package "pwa/" as PWA <<planned>>
  package "analytics/" as ANALYTICS <<planned>>
  package "social/" as SOCIAL <<planned>>
}

package "components/" as C {
  package ui
  package dashboard
  package chat
  package portfolio
  package market
  package autotrade
  package layout
  package tutorial
  package landing
  package reports
  
  package offline <<planned>>
  package pwa <<planned>>
  package analytics <<planned>>
  package social <<planned>>
}

package "hooks/" as H
package "lib/" as L
package "providers/" as P
package "types/" as T

package "workers/" as WORKERS <<planned>>
package "cache/" as CACHE <<planned>>
package "analytics/" as ANALYTICS_LIB <<planned>>

APP --> C
APP --> H
APP --> L
APP --> P
C --> H
C --> L
C --> T
H --> L
P --> L
L --> T

APP ..> WORKERS <<planned>>
APP ..> CACHE <<planned>>
C ..> ANALYTICS_LIB <<planned>>

legend right
  __실선__: 현재 구현 (As-Is)
  ..점선..: 향후 계획 (To-Be)
  <<planned>>: 개선 예정 항목
endlegend
@enduml
```

**향후 추가 예정 패키지**

- **workers/**: SharedWorker, ServiceWorker (오프라인 지원)
- **cache/**: IndexedDB, Cache API 래퍼
- **analytics/**: 사용자 행동 분석, 성능 모니터링
- **social/**: 소셜 기능, 커뮤니티

---

## 3. 컴포넌트 다이어그램 (Component)

### 3.1 현재 구조 (As-Is)

페이지/경계 컴포넌트가 어떤 런타임 자원(SSE/WS/REST)에 붙는지 시각화.

![컴포넌트 다이어그램](docs/uml/component-diagram.svg)

---

### 3.2 향후 개선 구조 (To-Be)

```plantuml
@startuml
component "Next.js App (Edge/Node)" as NEXT
component "Browser (React 18)" as B
component "Auth Context/Provider" as AUTHC
component "Zustand Stores" as ZS
component "Axios Client" as AX
component "WS Client" as WSC
component "SSE Client" as SSEC

component "Portfolio API" as PAPI
component "Trade Engine API" as TEAPI
component "Auth Service" as AS
component "Market WS Broker" as MWS
component "Chat SSE Gateway" as CGW
component "Tutorial API" as TutAPI
component "Notification API" as NAPI

component "SharedWorker" as SW <<planned>>
component "ServiceWorker" as SWR <<planned>>
component "IndexedDB Cache" as IDB <<planned>>
component "Analytics Engine" as AE <<planned>>

B -- AUTHC
B -- ZS
B -- AX
B -- WSC
B -- SSEC
B ..> SW <<planned>>
B ..> SWR <<planned>>
B ..> IDB <<planned>>

AX --> PAPI
AX --> TEAPI
AX --> AS
AX --> TutAPI
AX --> NAPI
WSC --> MWS
SSEC --> CGW

SW ..> MWS : proxy WS <<planned>>
SW ..> CGW : proxy SSE <<planned>>
IDB ..> PAPI : cache <<planned>>
B ..> AE : track <<planned>>

NEXT ..> PAPI
NEXT ..> TEAPI
NEXT ..> AS

legend right
  __실선__: 현재 구현 (As-Is)
  ..점선..: 향후 계획 (To-Be)
  <<planned>>: 개선 예정 항목
endlegend
@enduml
```

**향후 추가 예정 컴포넌트**

- **SharedWorker**: 멀티탭에서 WS/SSE 연결 공유
- **ServiceWorker**: 오프라인 지원, 푸시 알림
- **IndexedDB Cache**: 대용량 데이터 로컬 저장
- **Analytics Engine**: 사용자 행동 추적, 성능 모니터링
```

---

## 4. 클래스 모델 (주요 도메인 & 클라이언트)

### 4.1 인증/컨텍스트/가드

```plantuml
@startuml
class AuthProvider {
  - state: AuthState
  - refreshLock: Promise<string> | null
  + children: ReactNode
  + refreshToken(): Promise<string>
}
class AuthState {
  token: string
  user: UserProfile
  expiresAt: Date
  refreshToken: string
}
class useAuth {
  + accessTokenReady(): boolean
  + getToken(): string
  // refreshTokenIfNeeded(): Promise<string>  // <<planned>> 향후 구현 예정
}
// class RouteGuard {  // <<planned>> 향후 구현 예정
//   + requireAuth(): JSX.Element
// }

AuthProvider -> AuthState
useAuth --> AuthProvider
// RouteGuard --> useAuth  // <<planned>> 향후 구현 예정
@enduml
```

### 4.2 WS(시세) 스토어 & 클라이언트

```plantuml
@startuml
class NasdaqStocksStore {
  + initWs(): Promise<boolean>
  + addSymbol(sym: string): void
  + getStock(sym: string): Stock
  + subscribeStore(listener): Unsubscribe
  + setMissingSince(timestamp: number): void
  + backfillPrices(prices: PriceTick[]): void
}
class Stock {
  symbol: string
  price: number
  changePct: number
  ts: number
}
class WSClient {
  + connect(url): void
  + send(msg): void
  + onMessage(cb): void
  + reconnect(backoff): void
  + onClose(callback): void
  + onError(callback): void
}
class PriceBuffer {
  + addTick(tick: PriceTick): void
  + flushBatch(): PriceTick[]
  + clear(): void
}

NasdaqStocksStore --> WSClient
NasdaqStocksStore o- Stock
NasdaqStocksStore --> PriceBuffer
@enduml
```

### 4.3 챗(SSE) & UI

```plantuml
@startuml
class ChatStore {
  + startSession(): Promise<SessionId>
  + appendUser(msg: Message): void
  + appendAssistant(delta: string): void
  + history: Message[]
}
class SSEClient {
  + open(url): EventSource
  + close(): void
  + onHeartbeat(callback): void
  + setTimeout(ms: number): void
}
class TypingMessage {
  - displayed: string
  - idx: number
  + render(text: string): JSX
  - useRequestAnimationFrame(): void
}

ChatStore --> SSEClient
TypingMessage --> ChatStore
@enduml
```

### 4.4 REST API 래퍼

```plantuml
@startuml
class ApiClient {
  - axios: AxiosInstance
  + getPortfolio(): Promise<Portfolio>
  + updatePortfolio(p: Portfolio): Promise<void>
  + getSettings(): Promise<Settings>
  + getTutorialProgress(): Promise<TutorialProgress>
}
class Portfolio { positions: Position[] }
class Position { symbol: string; qty: number; avg: number }
class Settings { locale: string; theme: string }
class TutorialProgress { currentStep: number; completedSteps: string[] }

ApiClient --> Portfolio
Portfolio o- Position
ApiClient --> Settings
ApiClient --> TutorialProgress
@enduml
```

### 4.5 튜토리얼 시스템

```plantuml
@startuml
class TutorialOverlay {
  + currentStep: number
  + currentStepInfo: StepInfo
  + nextStep(): void
  + previousStep(): void
  + skipTutorial(): void
}
class useTutorial {
  + currentTutorial: Tutorial
  + currentStep: number
  + currentStepInfo: StepInfo
  + nextStep(): void
  + previousStep(): void
  + skipTutorial(): void
}
class StepInfo {
  title: string
  description: string
  target: string
  position: 'top' | 'bottom' | 'left' | 'right'
}

TutorialOverlay --> useTutorial
useTutorial --> StepInfo
@enduml
```

---

## 5. 시퀀스 다이어그램 (핵심 플로우)

### 5.1 로그인/가드/페이지 전개

![로그인 시퀀스 다이어그램](docs/uml/login-sequence.svg)

### 5.1.1 토큰 리프레시 동시성 제어 (<<planned>>)

```plantuml
@startuml
actor User
participant Browser
participant AuthProvider as AP
participant AuthService as AS

Browser -> AP: useAuth().getToken()
alt exp < t-Δ (만료 임박)
  Browser -> AP: refreshLock? (pending)
  alt 없음
    AP -> AS: POST /auth/refresh
    AS --> AP: {token, exp}
    AP -> AP: resolve refreshLock
  else 있음
    AP -> AP: await refreshLock
  end
end
@enduml
```

### 5.2 대시보드 실시간(WS)

![WebSocket 실시간 시세 시퀀스](docs/uml/websocket-sequence.svg)

### 5.2.1 WS 재연결 + 재구독 + 백필(Backfill)

```plantuml
@startuml
actor User
participant Dashboard
participant NasdaqStocksStore as Store
participant WSClient as WS
participant Broker as MWS
participant PortfolioAPI as PAPI

WS -> WS: onClose/onError
WS -> Store: connectionLost()
Store -> Store: setMissingSince(Date.now())
Store -> WS: reconnect(backoff)
WS -> MWS: WS Handshake
MWS --> WS: 101 Switching Protocols
Store -> WS: SUBSCRIBE {symbols}
Store -> PAPI: GET /portfolio/prices?since={missingSince}
PAPI --> Store: {prices: [{sym, price, ts}]}
Store -> Dashboard: backfillPrices(prices)
MWS --> WS: TICK {sym, price, ts} (stream)
WS --> Store: onmessage(TICK)
Store -> Dashboard: setState(price update)
@enduml
```

**백필 정합 규칙**: Backfill merge는 (1) ts 단조 증가 보장, (2) symbol+ts 중복 제거, (3) 서버시각과의 Δ 보정(절대시간 기준), (4) 라이브 틱과 백필의 단일 병합 패스로 완료한다. O(n log n) 정렬 1회 + O(n) 머지, 링버퍼 길이 N=1024 유지.

### 5.3 챗봇(SSE) 스트리밍 + requestAnimationFrame 타이핑

![챗봇 SSE 시퀀스](docs/uml/chat-sse-sequence.svg)

### 5.3.1 SSE 하트비트/타임아웃/조기 종료

```plantuml
@startuml
actor User
participant ChatPage as UI
participant ChatStore as CS
participant SSE as EventSource

UI -> SSE: open(streamUrl)
loop 15초마다
  SSE --> UI: :heartbeat
  UI -> UI: updateLastHeartbeat()
end
alt 120초 무응답
  UI -> UI: timeout detected
  UI -> SSE: close()
  UI -> UI: restartSSE()
else 정상 종료
  SSE --> UI: [DONE]
  UI -> SSE: close()
end
@enduml
```

### 5.3.2 SharedWorker 멀티탭 시퀀스 (To-Be)

```plantuml
@startuml
actor User1
actor User2
participant Tab1
participant Tab2
participant SharedWorker as SW
participant WS as WebSocket

User1 -> Tab1: 페이지 로드
Tab1 -> SW: register(tab1)
SW -> SW: setLeader(tab1)
SW -> WS: connect()
WS --> SW: connected

User2 -> Tab2: 페이지 로드
Tab2 -> SW: register(tab2)
SW -> Tab2: setFollower(tab2)
SW -> Tab2: broadcast(WS_OPEN)

note over Tab1, Tab2
  <<planned>>
  탭 리더 선출/브로드캐스트
  리더 다운시 재선출
  (optional) SharedWorker 대신 BroadcastChannel + WS 멀티플렉싱 우선
end note

legend right
  __실선__: 현재 구현 (As-Is)
  ..점선..: 향후 계획 (To-Be)
  <<planned>>: 개선 예정 항목
endlegend
@enduml
```

### 5.4 튜토리얼 진행 플로우

![튜토리얼 진행 플로우](docs/uml/tutorial-sequence.svg)

---

## 6. 액티비티 다이어그램 (흐름/분기)

### 6.1 자동매매 설정 저장

```plantuml
@startuml
start
:사용자 입력 검증;
if (유효?) then (예)
  :로컬 미리보기 반영;
  :변경 diff 산출;
  :REST PATCH /autotrade;
  if (200 OK) then (성공)
    :전역 상태 invalidate;
    :Toast 성공;
  else (실패)
    :로컬 롤백;
    :에러 토스트 및 재시도 버튼;
  endif
else (아니오)
  :폼 에러 강조;
endif
stop
@enduml
```

### 6.2 시세 구독 관리 (심볼 추가/삭제)

```plantuml
@startuml
start
:사용자 심볼 추가;
:Store.addSymbol(sym);
if (WS 연결됨?) then (예)
  :WS.SUBSCRIBE(sym);
else (아니오)
  :대기 -> OnOpen 후 큐 처리;
endif
stop
@enduml
```

### 6.3 튜토리얼 단계 진행

```plantuml
@startuml
start
:현재 단계 정보 로드;
:사용자 액션 감지;
if (단계 완료 조건 충족?) then (예)
  :완료 상태 저장;
  :다음 단계 정보 로드;
  if (모든 단계 완료?) then (예)
    :튜토리얼 완료 축하;
    :보상 지급;
  else (아니오)
    :다음 단계 안내;
  endif
else (아니오)
  :현재 단계 계속 진행;
endif
stop
@enduml
```

### 6.4 폴백 전략 (WS → SSE → Polling)

```plantuml
@startuml
start
:WebSocket 연결 시도;
if (연결 성공?) then (예)
  :실시간 데이터 수신;
else (아니오)
  :SSE 연결 시도;
  if (SSE 연결 성공?) then (예)
    :스트리밍 데이터 수신;
  else (아니오)
    :폴링 모드 전환;
    loop 5초마다
      :REST API 호출;
      :데이터 업데이트;
    end
  endif
endif
stop
@enduml
```

---

## 7. 상태 머신 (State Machines)

### 7.1 TypingMessage

![TypingMessage 상태 머신](docs/uml/state-machines.svg#TypingMessage)

### 7.2 WS 연결 재시도(백오프)

```plantuml
@startuml
[*] --> Connecting
Connecting --> Open: onOpen
Connecting --> Backoff: onError
Open --> Backoff: onClose
Backoff --> Connecting: timer(exp backoff)
@enduml
```

### 7.3 인증 세션

```plantuml
@startuml
[*] --> Anonymous
Anonymous --> Authenticated: login(token)
Authenticated --> Anonymous: logout/expire
Authenticated --> Refreshing: t-Δ before exp
Refreshing --> Authenticated: refresh OK
Refreshing --> Anonymous: refresh FAIL
@enduml
```

### 7.4 튜토리얼 진행 상태

```plantuml
@startuml
[*] --> NotStarted
NotStarted --> InProgress: startTutorial()
InProgress --> StepComplete: completeStep()
StepComplete --> InProgress: nextStep()
InProgress --> Completed: allStepsComplete()
Completed --> NotStarted: resetTutorial()
@enduml
```

### 7.5 WS 장애 복구 상태

```plantuml
@startuml
[*] --> Connected
Connected --> Disconnected: onClose/onError
Disconnected --> Backoff: exponential backoff
Backoff --> Reconnecting: timer
Reconnecting --> Connected: onOpen
Reconnecting --> Backoff: onError
@enduml
```

### 7.6 폴백 전략 상태 머신 (To-Be)

```plantuml
@startuml
[*] --> WS_Open
WS_Open --> WS_Fail: connection lost
WS_Fail --> SSE_Open: WS 재연결 실패
SSE_Open --> SSE_Fail: SSE 연결 실패
SSE_Fail --> Polling: SSE 재연결 실패
Polling --> Recover: 네트워크 복구
Recover --> WS_Open: WS 재시도
Recover --> SSE_Open: WS 실패 시 SSE 시도

note right of WS_Fail
  <<planned>>
  지수 백오프 + jitter
  최대 5회 시도
end note

note right of SSE_Fail
  <<planned>>
  heartbeat 15-30s
  120s 타임아웃
end note

note right of Polling
  <<planned>>
  5초 간격 REST
  배터리 절약 모드
  anti-flap: 30s 내 3회 실패 → 60s 쿨다운 후 재평가
end note

legend right
  __실선__: 현재 구현 (As-Is)
  ..점선..: 향후 계획 (To-Be)
  <<planned>>: 개선 예정 항목
endlegend
@enduml
```

---

## 8. 배포 다이어그램 (Deployment)

```plantuml
@startuml
node "User Device" as UD {
  artifact "Browser (React 18)" as BR
}
node "Edge Runtime" as EDGE {
  artifact "Next.js App Router (SSR/SSG)" as APP
  artifact "SSE Gateway (Edge)" as SSE_GW
}
node "Node Runtime" as NODE {
  artifact "WebSocket Gateway" as WS_GW
}
node "Backend" as BE {
  node "APIs" {
    component "Auth Service"
    component "Portfolio API"
    component "Trade Engine API"
    component "Tutorial API"
    component "Notification API"
  }
  node "Realtime" {
    component "Market WS Broker"
    component "Chat SSE Gateway"
  }
}

BR <--> APP : HTTP/HTTPS
BR --> WS_GW : WebSocket (Node only)
BR --> SSE_GW : SSE (Edge/Node)
APP --> "APIs" : REST
note right of WS_GW : WebSocket은 Node 런타임 필요\n서버리스면 전용 서비스로 분리
note right of SSE_GW : SSE는 Edge/Node 둘 다 가능\n플랫폼 따라 다름
@enduml
```

---

## 9. 데이터 계약(스키마) & 타입 경계

### 9.1 공통 타입 (TypeScript)

```ts
// types/
export type Symbol = string;

// 표준 API 응답 래퍼
export type ApiResult<T> =
  | { ok: true; data: T; requestId: string; traceId?: string }
  | { ok: false; error: { code: string; message: string; details?: unknown }; requestId: string; traceId?: string };

// 에러 코드 집합
export type ErrorCode = 
  | 'AUTH_EXPIRED' | 'AUTH_REVOKED' | 'RATE_LIMITED' 
  | 'WS_PROTOCOL' | 'SSE_TIMEOUT' | 'VALIDATION_FAILED'
  | 'NETWORK_ERROR' | 'SERVER_ERROR' | 'UNKNOWN_ERROR';

export interface PriceTick { 
  symbol: Symbol; 
  price: number; 
  changePct: number;
  ts: number;
}

// 런타임 스키마 검증 (Zod)
import { z } from 'zod';
export const PriceTickSchema = z.object({
  symbol: z.string(),
  price: z.number().positive(),
  changePct: z.number(),
  ts: z.number().int().positive()
});
export type ValidatedPriceTick = z.infer<typeof PriceTickSchema>;
export interface Message { 
  role: 'user'|'assistant'|'system'; 
  content: string; 
  ts: number;
  requestId: string;
}
export interface Portfolio { 
  positions: Position[];
  requestId: string;
}
export interface Position { 
  symbol: Symbol; 
  qty: number; 
  avg: number 
}
export interface Settings { 
  locale: string; 
  theme: 'light'|'dark' 
}
export interface TutorialProgress {
  currentStep: number;
  completedSteps: string[];
  totalSteps: number;
  requestId: string;
}
export interface StepInfo {
  title: string;
  description: string;
  target: string;
  position: 'top' | 'bottom' | 'left' | 'right';
}
```

### 9.2 REST 응답 계약 예시

```json
GET /api/portfolio -> {
  "ok": true,
  "data": {
    "positions": [ {"symbol": "AAPL", "qty": 10, "avg": 185.2} ]
  },
  "requestId": "req_123456789",
  "traceId": "trace_987654321"
}

POST /api/tutorial/progress -> {
  "ok": true,
  "data": {
    "currentStep": 3,
    "completedSteps": ["step1", "step2"],
    "totalSteps": 5
  },
  "requestId": "req_123456790",
  "traceId": "trace_987654322"
}

// 에러 응답 예시
{
  "ok": false,
  "error": {
    "code": "AUTH_EXPIRED",
    "message": "Authentication token has expired",
    "details": null
  },
  "requestId": "req_123456791",
  "traceId": "trace_987654323"
}
```

### 9.3 SSE 델타 계약

```json
{"type":"delta","data":" … token … ","requestId":"req_123456789","timestamp":1723800000000}
{"type":"heartbeat","timestamp":1723800000000}
{"type":"done","requestId":"req_123456789","timestamp":1723800000000}
```

### 9.4 WS 틱 계약

```json
{"type":"tick_batch","meta":{"batchRequestId":"req_123456789","ts":1723800000000},"ticks":[{"symbol":"NVDA","price":124.56,"changePct":2.34,"ts":1723800000000},{"symbol":"AAPL","price":185.20,"changePct":-0.85,"ts":1723800000000}]}
{"type":"heartbeat","timestamp":1723800000000}
```

---

### 9.5 W3C Trace Context 예시

#### REST API 헤더
```http
GET /api/portfolio
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
tracestate: skn=frontend,env=prod
```

#### WebSocket SUBSCRIBE Payload
```json
{
  "op": "SUBSCRIBE",
  "symbols": ["NVDA", "AAPL"],
  "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
  "tracestate": "skn=frontend,env=prod"
}
```

#### SSE Heartbeat Event
```http
event: heartbeat
data: {
  "ts": 1723800000000,
  "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
  "tracestate": "skn=frontend,env=prod"
}
```

---

## 10. 성능/자원 설계

* **Streaming 우선 UX:** SSE로 토큰 단위 전달 → `TypingMessage(setInterval 18ms)`로 점진적 렌더.
* **메모리 압박 완화:** `useRef` 인덱스, 언마운트 시 인터벌 정리. 메시지 히스토리 **스냅/가상화** 고려.
* **WS 백오프:** 지수 백오프 + Jitter. 최대 재시도/냉각시간 상한.
* **렌더 최적화:** `React.memo`, `useMemo`, `useCallback` 및 선택적 `zustand` selector로 **정밀 구독**.
* **코드 스플릿:** `dynamic(import, { ssr:false })`로 무거운 그래프/차트 지연 로딩.
* **튜토리얼 최적화:** 단계별 지연 로딩, 진행 상태 캐싱, 불필요한 리렌더 방지.
* **WS 스로틀/배치:** 50~100ms 단위로 틱 배치 후 상태 갱신, 렌더 폭주 방지.
* **링버퍼:** 차트용 틱은 심볼당 고정 길이(1,024) 링버퍼로 메모리 상한.
* **CI 가드:** bundlesize(라우트별 gzip 제한) + depcruiser(역의존 금지) 자동 검증.

---

## 11. 보안/권한

* **토큰 저장:** 가능하면 httpOnly 쿠키 + CSRF 토큰. 로컬스토리지는 XSS에 취약. 지금 구조 유지해도 CSP(script-src 'self' + nonce), DOMPurify로 SSE/채팅 콘텐츠 정화.
* **라우트 가드:** 현재는 직접 구현, 향후 `useAuth().accessTokenReady` 기준 보호 라우트로 전환 예정.
* **전송 보안:** HTTPS 고정, WS/WSS 업그레이드. SSE는 CORS/Origin 엄격화.
* **권한 레벨:** 토큰에 역할/스코프를 넣고, 클라에서는 UI 가드만; 진짜 권한 판정은 백엔드.
* **튜토리얼 보안:** 사용자별 진행 상태 격리, 무결성 검증.
* **에러 정보 누설 차단:** 에러 메시지에 내부 스택/쿼리 안 담기. code 기준으로 클라 매핑.

---

## 12. 장애/회복/관측성

* **로깅:** 연결 단계, 구독/해제, 오류 코드, 백오프 시간, SSE 종료 이유.
* **헬스체크:** WS 핑/퐁, SSE 하트비트(주기 메타). 타임아웃 시 재수립.
* **에러 전파:** 사용자에겐 토스트/스낵바, 개발자에겐 콘솔 + 원격 로거.
* **메트릭:** LCP/FID/CLS + WS 재연결 카운트, SSE 중단 빈도, 평균 응답 토큰 latency.
* **튜토리얼 모니터링:** 단계별 완료율, 중단 지점, 사용자 행동 패턴.
* **OpenTelemetry(OTEL) 프론트 적용:**
  * **Traces:** login, ws_connect, ws_resubscribe, sse_open, sse_timeout, portfolio_fetch.
  * **Metrics:** ws_reconnect_count, sse_drop_count, chat_token_latency_ms, fps_drops, LCP/FID/CLS.
  * **로깅 표준:** level|timestamp|event|requestId|traceId|userId(partial) 포맷. PII 마스킹.
  * **Server-Timing:** 서버 응답 헤더의 db;dur=12, api;dur=34를 RUM에 연동.

---

## 13. 코드 매핑(문서 ↔ 구현)

* `hooks/use-auth.ts` → **§4.1, §7.3**
* `hooks/use-nasdaq-stocks.ts`(Zustand) → **§4.2, §5.2, §7.2**
* `components/chat/chat-message.tsx` → **§4.3, §5.3, §7.1**
* `lib/api/` → **§4.4, §9**
* `app/dashboard/DashboardPageClient.tsx` → **§5.2**
* `app/chat/page.tsx` → **§5.3**
* `components/tutorial/tutorial-overlay.tsx` → **§4.5, §5.4, §7.4**
* `hooks/use-tutorial.ts` → **§4.5, §7.4**

---

## 14. 확장 로드맵 (프론트 관점)

* **Edge Runtime 전환 검토:** SSE/WS 프록시를 Edge에서 핸들, TTFB 단축.
* **서버 컴포넌트 확장:** 비실시간 페이지의 SSR 데이터 패치 비용 절감.
* **PWA/오프라인:** 포트폴리오 마지막 스냅샷 캐시, 연결 복구 시 동기화.
* **접근성 레벨‑AA:** 키보드 포커스, 스크린리더 레이블, 모션 감도 옵션.
* **튜토리얼 고도화:** AI 기반 개인화 가이드, 진행률 예측, 적응형 난이도.
* **Feature Flag 시스템:** tutorial v2, sse_heartbeat, ws_backfill 등 점진 배포.
* **환경 분리:** NEXT_PUBLIC_* 최소화, 비공개 값은 절대 클라에 노출 금지.

---

## 15. 품질 게이지(체크리스트)

* [ ] 보호 라우트에서 토큰 만료 edge‑case 테스트(만료 직전/직후).
* [ ] WS re‑subscribe 누락 없는지(연결 재수립 후 큐 비우기).
* [ ] SSE 종료 신호 누락 시 타임아웃/하트비트로 종료 감지.
* [ ] 대용량 메시지 히스토리 가상화로 렌더 스톨 제거.
* [ ] 메트릭/로그 상시 수집 + 대시보드화.
* [ ] 튜토리얼 진행 상태 동기화 및 복구 메커니즘 검증.
* [ ] setInterval 18ms → requestAnimationFrame 기반 타이핑 애니메이션 성능 최적화 및 프레임 드롭 방지.
* [ ] WS 스로틀/배치 처리로 렌더 폭주 방지.
* [ ] SSE 하트비트/타임아웃 메커니즘 검증.
* [ ] 폴백 전략(WS → SSE → Polling) 테스트.
* [ ] 에러 코드 표준화 및 requestId/traceId 추적.
* [ ] 접근성 테스트 (axe-core) 및 prefers-reduced-motion 대응.

---

## 16. 부록 — PlantUML 렌더 가이드

* 각 코드 블록을 PlantUML 호환 편집기에 붙여 넣으면 다이어그램 생성 가능.
* Graphviz 설치 필요할 수 있음.
* 팀 내 CI에서 `plantuml -tpng`로 PNG 산출 자동화 권장.

---

### 끝. 이 스펙은 프론트가 **무엇을, 어디서, 어떻게** 연결하고 책임지는지 딱 잘라 보여준다.

**실제 프로젝트 분석 결과 반영:**
- 튜토리얼 시스템 추가 (§4.5, §5.4, §7.4)
- 온보딩 및 에러 테스트 페이지 포함
- 실제 컴포넌트 구조 및 훅 매핑
- requestAnimationFrame 기반 타이핑 애니메이션 상세 분석
- WebSocket 실시간 시세 시스템 구체화

**실전 배포 보강 사항:**
- TAPI 네임 충돌 해결 (TEAPI, TutAPI로 분리)
- 토큰 리프레시 동시성 제어 (§5.1.1)
- WS 재연결 + 재구독 + 백필 (§5.2.1)
- SSE 하트비트/타임아웃 (§5.3.1)
- 표준 API 응답 래퍼 (requestId/traceId 포함)
- 에러 코드 집합 및 보안 강화
- OpenTelemetry 관측성 체계
- Edge/Node 런타임 제약 명시
- 폴백 전략 (WS → SSE → Polling)
- Feature Flag 시스템 및 환경 분리

---

## 17. Gap 분석 및 개선 계획

### 17.1 현재 vs 목표 비교표

| 영역 | 현재 상태 (As-Is) | 목표 상태 (To-Be) | Gap | 우선순위 | ETA |
|------|------------------|------------------|-----|----------|-----|
| **성능** | 18ms 타이핑, 기본 최적화 | rAF + 가상화, 코드 스플릿 | 높음 | P0 | Q4-2025 |
| **보안** | 토큰 localStorage | httpOnly 쿠키 + CSP | 중간 | P1 | Q1-2026 |
| **오프라인** | 없음 | PWA + ServiceWorker | 높음 | P0 | Q1-2026 |
| **관측성** | 기본 로깅 | OpenTelemetry + 메트릭 | 높음 | P1 | Q1-2026 |
| **폴백** | WS만 | WS → SSE → Polling | 중간 | P2 | Q2-2026 |
| **멀티탭** | 탭별 연결 | SharedWorker 공유 | 중간 | P2 | Q2-2026 |

### 17.2 마이그레이션 로드맵

```plantuml
@startuml
title 마이그레이션 로드맵 (2025-2026년)
!theme plain
skinparam backgroundColor #FFFFFF
skinparam activity {
  BackgroundColor<<phase1>> #E3F2FD
  BackgroundColor<<phase2>> #F3E5F5
  BackgroundColor<<phase3>> #E8F5E8
}

start
:현재 상태 (As-Is);
fork
  :Phase 1 (Q4-2025)\n성능 최적화 <<phase1>>;
  :rAF 타이핑 전환;
  :코드 스플릿 적용;
  :가상화 도입;
fork again
  :Phase 2 (Q1-2026)\n보안 강화 <<phase2>>;
  :CSP 설정;
  :DOMPurify 적용;
  :httpOnly 쿠키 전환;
fork again
  :Phase 3 (Q2-2026)\n오프라인 지원 <<phase3>>;
  :ServiceWorker 구현;
  :PWA 매니페스트;
  :IndexedDB 캐시;
end fork
:목표 상태 (To-Be);
stop
@enduml
```

### 17.3 수용 기준 및 메트릭

#### 성능 지표
- **LCP**: < 2.5초 (현재: ~3.2초)
- **FID**: < 100ms (현재: ~150ms)
- **CLS**: < 0.1 (현재: ~0.15)
- **타이핑 애니메이션**: 60fps 유지 (현재: 18ms 고정)

#### 안정성 지표
- **WS 재연결률**: < 5% (현재: ~15%)
- **SSE 타임아웃**: < 1% (현재: ~8%)
- **에러 발생률**: < 0.1% (현재: ~0.5%)

#### 사용자 경험 지표
- **오프라인 기능**: 80% 이상 (현재: 0%)
- **멀티탭 동기화**: 100% (현재: 0%)
- **PWA 설치율**: > 30% (목표)

### 17.4 리스크 및 완화 전략

| 리스크 | 확률 | 영향도 | 완화 전략 |
|--------|------|--------|-----------|
| **SharedWorker 미지원** | 낮음 | 높음 | 폴백: 탭별 연결 유지 |
| **PWA 제한 환경** | 중간 | 중간 | 점진적 기능 비활성화 |
| **성능 최적화 복잡성** | 높음 | 중간 | 단계별 적용 + A/B 테스트 |
| **브라우저 호환성** | 낮음 | 높음 | Polyfill + 기능 감지 |

---

### 17.5 Retry/Timeout 매트릭스

| 채널 | 재시도 | 백오프 | 타임아웃 | 멱등 | 메모 |
|------|--------|--------|----------|------|------|
| **REST GET** | 2회 | 200→500ms | 10s | ✅ | 캐시 가능 |
| **REST POST/PATCH** | 0~3회 | 200→500→1000ms | 15s | ⚠️ Idempotency-Key 필수 | 멱등 아니면 금지 |
| **SSE** | 재연결 | 1→2→4s | 120s 무응답 종료 | N/A | heartbeat 15–30s |
| **WS** | 5회 | 1→2→4→8→16s + jitter | 핸드셰이크 10s | N/A | 재구독+백필 |

---

### 17.6 CORS/CSP/COOP+COEP 정책

#### CORS 설정
```typescript
// next.config.mjs
const nextConfig = {
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          { key: 'Access-Control-Allow-Origin', value: process.env.NEXT_PUBLIC_FRONTEND_URL },
          { key: 'Access-Control-Allow-Credentials', value: 'true' },
          { key: 'Access-Control-Allow-Methods', value: 'GET, POST, PUT, DELETE, PATCH, OPTIONS' },
          { key: 'Access-Control-Allow-Headers', value: 'Content-Type, Authorization, Idempotency-Key, Traceparent' },
          { key: 'Access-Control-Expose-Headers', value: 'Request-Id, Trace-Id, RateLimit-Remaining' },
          { key: 'Vary', value: 'Origin' },
        ],
      },
    ];
  },
};
```

#### CSP 정책
```html
<!-- _document.tsx -->
<!-- 개발용 CSP (Next.js dev 모드용) -->
<meta httpEquiv="Content-Security-Policy" content="
  default-src 'self';
  script-src 'self' 'unsafe-inline' 'unsafe-eval';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  connect-src 'self' wss: https:;
  font-src 'self';
  object-src 'none';
  base-uri 'self';
  form-action 'self';
  frame-ancestors 'none';
" />

<!-- 운영용 CSP (프로덕션 배포시) -->
<!-- <meta httpEquiv="Content-Security-Policy" content="
  default-src 'self';
  script-src 'self' 'nonce-{{nonce}}' 'strict-dynamic';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  connect-src 'self' wss: https:;
  font-src 'self';
  object-src 'none';
  base-uri 'self';
  frame-ancestors 'none';
" /> -->
```

#### COOP + COEP
```typescript
// next.config.mjs
const nextConfig = {
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'Cross-Origin-Opener-Policy', value: 'same-origin' },
          { key: 'Cross-Origin-Embedder-Policy', value: 'require-corp' },
        ],
      },
    ];
  },
};
```

---

## 18. 구현 우선순위 매트릭스

### 18.1 ROI vs 복잡도 분석

```
복잡도 (높음)
    ↑
    │                    🚀 P0
    │              📊 P1
    │          🔧 P2
    │      💡 P3
    │
    └─────────────────────────────→ ROI (높음)
```

---

### 18.2 Idempotency & 에러 분류 표

| API 엔드포인트 | HTTP 메서드 | 멱등성 | 재시도 허용 | 에러 코드 | 처리 방식 |
|----------------|-------------|--------|-------------|-----------|-----------|
| **GET /api/portfolio** | GET | ✅ | ✅ (2회) | 401, 403, 500 | 토큰 갱신 후 재시도 |
| **POST /api/chat/start** | POST | ❌ | ❌ | 400, 401, 429 | 사용자에게 재시도 안내 |
| **POST /api/tutorial/complete/step** | POST | ✅ | ✅ (3회) | 401, 409, 500 | Idempotency-Key로 중복 방지 |
| **POST /api/auth/login** | POST | ❌ | ❌ | 400, 401, 429 | 사용자에게 재시도 안내 |
| **GET /api/dashboard/prices** | GET | ✅ | ✅ (2회) | 401, 403, 500 | 캐시 + 재시도 |

#### 에러 코드 매핑
| 에러 코드 | 의미 | 사용자 액션 | 자동 처리 |
|-----------|------|-------------|-----------|
| **401** | 인증 실패 | 로그인 페이지로 이동 | 토큰 리프레시 시도 |
| **403** | 권한 부족 | 권한 확인 안내 | 권한 스코프 검증 |
| **409** | 충돌 (멱등성) | 상태 확인 안내 | Idempotency-Key 검증 |
| **429** | Rate Limit | 잠시 후 재시도 안내 | 자동 백오프 |
| **500** | 서버 오류 | 잠시 후 재시도 안내 | 자동 재시도 (GET만) |

**P0 (즉시 구현)**
- setInterval 18ms → requestAnimationFrame 타이핑 전환
- WS 재연결 백필 로직
- SSE 하트비트/타임아웃

**P1 (Q1-2026)**
- OpenTelemetry 관측성
- CSP + DOMPurify 보안
- 코드 스플릿 최적화

**P2 (Q2-2026)**
- 폴백 전략 (WS → SSE → Polling)
- 멀티탭 SharedWorker
- 가상화 (Virtualization)

**P3 (Q3-2026)**
- PWA 오프라인 지원
- 소셜 트레이딩 기능
- 고급 분석 엔진

---

## 19. 성능/메모리 예산 및 테스트 체계

### 19.1 성능/메모리 예산 (하드 목표)

#### JavaScript 번들 크기
- **초기 JS**: ≤ 180KB gzip (Next.js 기본 + 핵심 기능)
- **코드 스플릿 후**: ≤ 120KB gzip (메인 번들)
- **총 번들 크기**: ≤ 500KB gzip (모든 기능 포함)

#### 메모리 사용량
- **메인 스레드**: ≤ 200MB (탭 기준)
- **WebSocket 연결**: ≤ 50MB (실시간 데이터)
- **캐시/IndexedDB**: ≤ 100MB (오프라인 데이터)

#### 성능 지표
- **메인 스레드 블로킹**: ≤ 50ms/interaction
- **타이핑 애니메이션**: 60fps 유지 (requestAnimationFrame)
- **WebSocket 재연결**: ≤ 3초 (백오프 포함)
- **SSE 응답 지연**: ≤ 100ms (heartbeat 기준)

---

### 19.2 테스트 시나리오 보강

#### Playwright 멀티탭 테스트
```typescript
// tests/multitab-websocket.spec.ts
test('멀티탭에서 WebSocket 공유 및 폴백 검증', async ({ browser }) => {
  const tab1 = await browser.newPage();
  const tab2 = await browser.newPage();
  
  // Tab1에서 WS 연결
  await tab1.goto('/dashboard');
  await tab1.waitForSelector('.stock-price');
  
  // Tab2에서 동일 페이지 로드
  await tab2.goto('/dashboard');
  await tab2.waitForSelector('.stock-price');
  
  // Tab1 WS 끊김 시뮬레이션
  await tab1.evaluate(() => {
    // WebSocket 연결 끊기 시뮬레이션
    window.dispatchEvent(new Event('offline'));
  });
  
  // Tab2에서 폴백 전략 확인
  await expect(tab2.locator('.fallback-indicator')).toBeVisible();
});
```

#### 네트워크 시뮬레이션 테스트
```typescript
// tests/network-conditions.spec.ts
test('네트워크 불안정 환경에서 오프라인 기능', async ({ page }) => {
  // Slow 3G 시뮬레이션
  await page.route('**/*', route => {
    route.fulfill({ status: 200, body: 'offline' });
  });
  
  await page.goto('/dashboard');
  
  // 오프라인 모드 활성화 확인
  await expect(page.locator('.offline-mode')).toBeVisible();
  
  // 캐시된 데이터 표시 확인
  await expect(page.locator('.cached-data')).toBeVisible();
});
```

#### 프로퍼티 기반 테스트 (백필 정합성)
```typescript
// tests/backfill-consistency.spec.ts
import { fc } from 'fast-check';

test('백필 merge 정합성 유지', () => {
  fc.assert(
    fc.property(
      fc.array(fc.record({
        symbol: fc.string(),
        price: fc.float(),
        ts: fc.integer({ min: 0, max: Date.now() })
      })),
      fc.array(fc.record({
        symbol: fc.string(),
        price: fc.float(),
        ts: fc.integer({ min: 0, max: Date.now() })
      })),
      (liveTicks, backfillData) => {
        // 순서 섞인 임의 시퀀스로 테스트
        const shuffled = [...liveTicks, ...backfillData]
          .sort(() => Math.random() - 0.5);
        
        const result = mergeBackfillData(liveTicks, backfillData);
        
        // 정합성 검증
        expect(result).toHaveLength(liveTicks.length + backfillData.length);
        expect(isTimeOrdered(result)).toBe(true);
        expect(hasNoDuplicates(result)).toBe(true);
      }
    )
  );
});
```

---

### 19.3 데이터 보존/프라이버시 정책

#### IndexedDB/Cache TTL
| 데이터 타입 | TTL | 보존 정책 | 자동 정리 |
|-------------|-----|-----------|-----------|
| **포트폴리오 스냅샷** | 7일 | 오프라인 지원 | 7일 후 자동 삭제 |
| **채팅 히스토리** | 30일 | 사용자 경험 | 30일 후 자동 삭제 |
| **시세 캐시** | 1시간 | 실시간성 | 1시간 후 자동 삭제 |
| **사용자 설정** | 무제한 | 개인화 | 사용자 삭제 시에만 |

#### PII 마스킹 규칙
| 데이터 필드 | 마스킹 규칙 | 예시 |
|-------------|-------------|------|
| **사용자 ID** | 마지막 4자리만 표시 | `user_****1234` |
| **이메일** | @ 앞 3자리 + 도메인 | `abc***@example.com` |
| **계좌번호** | 마지막 4자리만 표시 | `****-****-1234` |
| **API 키** | 첫 6자리 + 마지막 4자리 | `sk_1234...abcd` |

---

### 19.4 다이어그램 드리프트 방지

#### PlantUML 공통 스킨
```plantuml
!include common.puml

' 모든 다이어그램 상단에 추가
skinparam component {
  BackgroundColor<<planned>> #FFF8E1
  BorderColor<<planned>> #F4B400
  FontColor<<planned>> #8A6D00
}
skinparam stereotype {
  CBackgroundColor<<planned>> #FFF8E1
  CBorderColor<<planned>> #F4B400
}

legend right
  __실선__ = As-Is (현재)
  ..점선.. = To-Be (개선안)
  <<planned>> = 계획 항목
endlegend
```

#### CI 린트 규칙
```yaml
# .github/workflows/uml-lint.yml
name: UML Lint Check
on: [push, pull_request]
jobs:
  uml-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Check UML conventions
        run: |
          # <<planned>> 누락 검출
          if grep -r "\.\.\." docs/ --include="*.md" | grep -v "<<planned>>"; then
            echo "❌ To-Be 요소에 <<planned>> 스테레오타입 누락"
            exit 1
          fi
          
          # 범례 누락 검출
          if grep -r "@startuml" docs/ --include="*.md" | grep -v "legend"; then
            echo "❌ PlantUML 다이어그램에 범례 누락"
            exit 1
          fi
          
          echo "✅ UML 컨벤션 검증 완료"
