# 🏦 SKN12-FINAL-2TEAM — AI 기반 스마트 투자 플랫폼

> **"사람 대신 판단과 실행까지 맡기는 AI 투자 비서"**  
> 개인화 포트폴리오 · 전략 기반 자동매매 · LLM 챗봇 · 대시보드

<!-- Badges: clean dark labels + logos -->
<p align="center">
  <!-- status / langs -->
  <a href="#">
    <img src="https://img.shields.io/badge/Status-Active-22c55e?style=for-the-badge&labelColor=1f2937" alt="status">
  </a>
  <a href="#">
    <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white&labelColor=1f2937" alt="python">
  </a>
  <a href="#">
    <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white&labelColor=1f2937" alt="fastapi">
  </a>
  <a href="#">
    <img src="https://img.shields.io/badge/Next.js-13%2B-000000?style=for-the-badge&logo=nextdotjs&logoColor=white&labelColor=1f2937" alt="nextjs">
  </a>
  <a href="#">
    <img src="https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white&labelColor=1f2937" alt="typescript">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-3b82f6?style=for-the-badge&labelColor=1f2937" alt="license">
  </a>
</p>

<p align="center">
  <!-- infra / ops -->
  <a href="#"><img src="https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white&labelColor=1f2937" alt="redis"></a>
  <a href="#"><img src="https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white&labelColor=1f2937" alt="mysql"></a>
  <a href="#"><img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white&labelColor=1f2937" alt="docker"></a>
  <a href="#"><img src="https://img.shields.io/badge/Jenkins-D24939?style=for-the-badge&logo=jenkins&logoColor=white&labelColor=1f2937" alt="jenkins"></a>
  <a href="#"><img src="https://img.shields.io/badge/AWS-232F3E?style=for-the-badge&logo=amazonaws&logoColor=FF9900&labelColor=1f2937" alt="aws"></a>
</p>

---

## 📌 한 줄 요약 (TL;DR)

AI가 *데이터 수집 → 신호 생성 → 리스크 통제 → 주문 실행* 을 **한 파이프라인**으로 잇는 투자 운영 시스템. “대화형 조언”에 머무르지 않고 **실행까지 책임지는** 구조.


---

## 🧠 무엇을 해결하나

- **초보~고급 투자자 공통 Pain**: 정보 과부하, 리밸런싱 타이밍 놓침, 감정적 매매  
- **솔루션**:  
  - 성향/목표/리스크 기반 **맞춤 포트폴리오**  
  - 전략 기반 **자동매매 + 백테스팅**  
  - **LLM 챗봇(SSE)**로 시장/포트 실시간 분석

---

## 🚀 주요 기능

- **대시보드**: 총자산, 수익률, 배분, 경고/알림 한눈에
- **포트폴리오**: 실시간 평가·성과 시각화, **리밸런싱 제안**
- **AI 챗봇("기가 버핏")**: 포트/시장 데이터 기반 답변, **SSE 스트리밍**
- **자동매매**: 프리셋/AI 추천 전략, **백테스트 내장**
- **알림**: 가격/뉴스/목표 도달 이벤트 푸시

---

## 🏗️ 아키텍처 개요

- **Backend**: FastAPI (Python) — SOA(Service Container), 비동기 처리  
- **Data**: MySQL(샤딩 고려), Redis(캐시/세션/MQ/EQ/분산락)  
- **Frontend**: Next.js(React, TS), React Query, Tailwind, **SSE**  
- **Ops**: Docker/Compose, Jenkins CI/CD  
- **Cloud(옵션)**: S3, OpenSearch, Bedrock 등 비용 최적화 구상

```
[Web/Next.js]  –SSE/HTTPS–>  [FastAPI]
                              ├─ Redis (Cache / MQ / EQ / Lock)
                              ├─ MySQL (Sharded-ready)
                              └─ External (Market/News/LLM/Broker)
```

> 레포 루트에 프론트 가이드, Jenkinsfile, 두 종류의 docker-compose가 포함되어 배포/운영 플로우까지 이어진다.

---

## 🧭 Architecture Diagrams

### 1) System Overview

```mermaid
flowchart LR
  subgraph Client["Client (Browser)"]
    U[User]
  end

  subgraph FE["Next.js (React, TS)"]
    SSE[SSE Stream Handler]
    UI[Dashboard & Chat UI]
  end

  subgraph BE["FastAPI (Python) — Service Container / SOA"]
    API[(REST API)]
    SVC_Auth[Auth Service]
    SVC_Portfolio[Portfolio Service]
    SVC_Chat[LLM Chat Orchestrator]
    SVC_Signal[Signal/Strategy Engine]
    SVC_Notify[Notification Service]
  end

  subgraph Data["Data Layer"]
    MYSQL[(MySQL Cluster<br/>Sharded-Ready)]
    REDIS[(Redis<br/>Cache / Session / MQ / EQ / Lock)]
    SEARCH[(OpenSearch)]
    S3[(S3 Object Storage)]
  end

  subgraph External["External Integrations"]
    LLM[(LLM: Bedrock / OpenAI)]
    MDATA[(Market / News / Macro APIs)]
    BROKER[(Broker APIs)]
  end

  U -->|HTTPS| FE
  FE -->|REST| API
  FE -->|SSE| SVC_Chat

  API --> SVC_Auth
  API --> SVC_Portfolio
  API --> SVC_Chat
  API --> SVC_Signal
  API --> SVC_Notify

  SVC_Auth --> REDIS
  SVC_Portfolio <-->|R/W| MYSQL
  SVC_Portfolio --> S3
  SVC_Chat --> LLM
  SVC_Signal --> MDATA
  SVC_Signal --> SEARCH
  SVC_Signal --> REDIS
  SVC_Signal --> BROKER
  SVC_Notify --> REDIS

  MYSQL <--> REDIS
```

### 2) CI/CD Pipeline

```mermaid
flowchart LR
  Dev[Developer Push] --> GH[(GitHub Repo)]
  GH --> JX[Jenkins Pipeline]
  JX --> TB[Unit/Integration Tests]
  JX --> DBU[Docker Build]
  DBU --> DHP[(Docker Hub / Registry)]
  DHP --> SRV[Deploy Server]
  SRV --> DCP[Docker Compose Up/Update]
  DCP --> HC[Healthchecks / Smoke Tests]
```

### 3) Signal → Order → Portfolio Flow

```mermaid
flowchart LR
  A["Raw Data Ingestion<br/>(Market, News, Macro)"] --> B["Feature Pipeline<br/>(log1p / Z-score, Composite)"]
  B --> C["Regime Detection<br/>(Kalman Regime Filter)"]
  C --> D["Signal Generation<br/>(Value / Momentum / Custom)"]
  D --> E["Risk Management<br/>(Exposure, SL / TP, Position Size)"]
  E --> F["Order Routing<br/>(Paper / Real via Broker API)"]
  F --> G["Portfolio Update<br/>(Positions, PnL, Rebalancing)"]
  G --> H["Dashboard + Chat SSE<br/>(Real-time Feedback)"]
```



---

## 🗂️ 레포 구조

```
.
├─ base_server/                # FastAPI 백엔드 (도메인/서비스 분리)
├─ frontend/                   # Next.js + TypeScript (SSE 응답)
├─ docs/                       # 아키텍처/큐/CI·CD/AWS/패킷/요구사항 문서
├─ 산출물/                      # 결과물(리포트/데모 등)
├─ FRONTEND_MINIMAL_DEPLOY.md  # 프론트 최소 배포 가이드
├─ Jenkinsfile                 # Jenkins 파이프라인
├─ docker-compose.local.yml    # 로컬 개발 스택
├─ docker-compose.hub.yml      # 서버/허브 배포 스택
├─ app.py, CLITest.py, Test.py, models.txt, structure.txt
└─ (aws-setup/scripts)         # (있는 경우) 배포/인프라 보조 스크립트
```

---

## ⚙️ 빠른 시작 (로컬 개발)

### 요구사항
- Python 3.10+, Node 18+, Docker(선택), Git

### 1) 클론
```bash
git clone https://github.com/SKNETWORKS-FAMILY-AICAMP/SKN12-FINAL-2TEAM.git
cd SKN12-FINAL-2TEAM
```

### 2) 환경 변수 (예시)

`configs/app.env.example` 형태가 있다면 복사해서 `.env` 구성. 없다면 아래 예시 사용.

```bash
# LLM
OPENAI_API_KEY=your_openai_key

# Market / News / Macro
FMP_API_KEY=your_fmp_key
NEWSAPI_KEY=your_newsapi_key
FRED_API_KEY=your_fred_key

# DB / Cache
MYSQL_DSN=mysql+pymysql://user:pass@localhost:3306/appdb
REDIS_URL=redis://localhost:6379/0

# Feature Flags
ENABLE_AUTOTRADE=false
```

**(선택) 브로커/API 설정을 분리하고 싶으면 `configs/broker.yaml`로 관리:**

```yaml
paper:
  app_key: "your_paper_app_key"
  app_secret: "your_paper_app_secret"
  account:
    stock: "12345678"
real:
  app_key: "your_real_app_key"
  app_secret: "your_real_app_secret"
  account:
    stock: "87654321"
user_agent: "Mozilla/5.0 ..."
```

### 3) 백엔드 실행

```bash
# 옵션 A) base_server 안에 main 모듈인 경우
cd base_server
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 옵션 B) 루트 app.py가 엔트리인 경우
# uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### 4) 프론트엔드 실행

```bash
cd frontend
npm install
npm run dev   # http://localhost:3000
```

**헬스체크**
- **API**: `GET /healthz` → `{ "status": "ok" }` (구현 위치는 코드 기준)
- **시스템 상태/메트릭 엔드포인트**는 운영 설정에 따라 분리 권장

---

## 🐳 Docker Compose (로컬/서버)

레포 루트에 로컬용/서버용 Compose가 구분돼 있다.
- `docker-compose.local.yml` (로컬 개발)
- `docker-compose.hub.yml` (서버/허브)

```bash
# 로컬
docker compose -f docker-compose.local.yml up -d --build
docker compose -f docker-compose.local.yml logs -f

# 서버(예시)
docker compose -f docker-compose.hub.yml pull
docker compose -f docker-compose.hub.yml up -d
```

---

## 🌐 프론트 최소 배포

프론트만 빨리 띄워야 하면 루트의 [FRONTEND_MINIMAL_DEPLOY.md](FRONTEND_MINIMAL_DEPLOY.md) 참고.  
정적 자산/환경변수/역프록시 포인트만 맞추면 된다.

---

## 🔄 CI/CD

- **루트에 [Jenkinsfile](Jenkinsfile) 존재** → 빌드 → 테스트 → 도커 이미지 → 레지스트리 푸시 → 배포 자동화 가능.
- **서버 측은 `docker-compose.hub.yml`과 연계**한다.

---

## 🔧 개발자 가이드 (핵심 원칙)

- **도메인/서비스 분리**: Service Container 패턴으로 모듈 경계를 명확히
- **큐/비동기**: Redis MQ/EQ로 장시간 작업 분리, 분산락으로 중복 실행 방지
- **전략 파이프라인**: Signal → Position → Portfolio 단계 분리로 테스트/검증 용이
- **LLM 연동**: 호출 비용 최소화를 위한 캐시/배치 처리, SSE 스트리밍 UX
- **테스트/로깅**: 표준화된 예외/로그 포맷으로 운영 모니터링 일원화

---

## 💸 비용 최적화 팁

- **OpenSearch/S3/LLM**은 최소 사양 + 캐시/스케줄링
- **로그/스냅샷 Lifecycle**로 저장비 절감
- **LLM 호출**은 요약 캐시/배치 처리로 단가 절감

---

## 🧭 로드맵

- **1~2주**: 온보딩 튜토리얼, 대시보드 차트 마감
- **1개월**: Settings 고도화, Notification 시스템
- **2~3개월**: LLM 챗봇 고도화, 포트 고급 분석, 브로커 실거래 연동

---

## 📚 문서(일부 예시)

`/docs` 디렉토리에 아키텍처, 큐 시스템, CI/CD, AWS 셋업, 프론트 퀵스타트, 패킷 명세, 요구사항 정리 등 세부 문서가 포함됨.

---

## 🤝 기여

1. **Fork** → 2) **브랜치**(`feat/*`) → 3) **PR**

**커밋 태그**: `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`

---

## 📄 라이선스

MIT License

---

<div align="center">

**🚀 AI 기반 스마트 투자 플랫폼으로 여러분의 투자 여정을 시작하세요! 🚀**

[![Star](https://img.shields.io/github/stars/SKNETWORKS-FAMILY-AICAMP/SKN12-FINAL-2TEAM?style=social)](https://github.com/SKNETWORKS-FAMILY-AICAMP/SKN12-FINAL-2TEAM)
[![Fork](https://img.shields.io/github/forks/SKNETWORKS-FAMILY-AICAMP/SKN12-FINAL-2TEAM?style=social)](https://github.com/SKNETWORKS-FAMILY-AICAMP/SKN12-FINAL-2TEAM)
[![Issues](https://img.shields.io/github/issues/SKNETWORKS-FAMILY-AICAMP/SKN12-FINAL-2TEAM)](https://github.com/SKNETWORKS-FAMILY-AICAMP/SKN12-FINAL-2TEAM/issues)

</div>

