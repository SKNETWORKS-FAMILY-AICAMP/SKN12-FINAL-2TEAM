# 🚀 AI Trading Platform Backend 발표 스크립트

## 1. 전체 시스템 아키텍처 개요 (4분)

안녕하세요. AI Trading Platform의 전체 시스템 아키텍처를 소개하겠습니다.

### 🌐 AWS 클라우드 네이티브 아키텍처

먼저 전체 시스템 구조를 보시면, 사용자부터 데이터베이스까지 완전한 엔터프라이즈급 시스템을 구축했습니다.

**외부 접근 계층**:
- 사용자는 인터넷을 통해 bullant-kr.com 도메인으로 접속
- AWS Route 53 DNS 서비스와 Certificate Manager SSL/TLS 인증서로 보안 연결

**로드 밸런싱 계층**:
- Application Load Balancer(ALB)가 트래픽을 분산
- 경로 기반 라우팅: `/*` → Frontend, `/api/*` → Backend

**Auto Scaling 인프라**:
- **Frontend Auto Scaling Group**: Next.js 14 기반 React 애플리케이션
- **Backend Auto Scaling Group**: FastAPI 기반 API 서버
- 각각 독립적인 Launch Template과 Target Group 운영

**CI/CD 파이프라인**:
- GitHub → Jenkins → Docker Hub → Auto Scaling Groups
- 완전 자동화된 무중단 배포 시스템

**데이터 계층**:
- MySQL RDS(Master-Slave): 글로벌 DB + 샤드 DB 구조
- Redis: 캐시 및 세션 관리
- AWS 서비스들: S3, OpenSearch, Bedrock, SES 등

### 🏗️ Backend Application Service Template 구조

백엔드 내부는 **Application Service Template 구조**로 설계된 FastAPI 프레임워크입니다.
이는 3계층 아키텍처로 구성되어 있습니다.

### 📋 3계층 아키텍처 구조

**1. Application Layer (웹 서버 계층)**
- FastAPI 애플리케이션 (main.py)
- 11개의 도메인별 라우터로 구성
- HTTP/WebSocket 요청 처리

**2. Template Layer (비즈니스 로직 계층)**  
- 11개의 Template 구현체
- Protocol 클래스를 통한 요청/응답 모델 관리
- 비즈니스 규칙 및 데이터 직렬화

**3. Service Layer (서비스 계층)**
- ServiceContainer를 통한 싱글톤 서비스 관리
- 13개의 핵심 서비스 구성
- 데이터베이스, 캐시, AI, 외부 API 등

## 2. Docker 컨테이너 기반 배포 전략 (2분)

### 🐳 컨테이너화된 마이크로서비스

**Frontend 컨테이너**:
- Next.js 14 애플리케이션
- Docker Hub: `ashone91/trading-frontend:latest`
- 포트 3000으로 서비스

**Backend 컨테이너**:
- FastAPI 애플리케이션
- Docker Hub: `ashone91/trading-backend:latest`
- 포트 8000으로 API 서비스

**Auto Scaling 배포 프로세스**:
1. 개발자가 코드를 GitHub에 Push
2. Jenkins가 자동으로 Docker 이미지 빌드
3. Docker Hub에 이미지 푸시
4. Auto Scaling Group이 Instance Refresh 실행
5. 새로운 EC2 인스턴스들이 최신 Docker 이미지로 교체
6. 무중단 배포 완료 (MinHealthy: 50%)

## 3. ServiceContainer 중심 서비스 관리 (4분)

### 🏗️ ServiceContainer 패턴

저희의 핵심은 **ServiceContainer**입니다. 이는 모든 서비스를 중앙에서 관리하는 싱글톤 레지스트리입니다.

### 📊 관리되는 13개 주요 서비스

**Core Services (4개)**:
- DatabaseService: MySQL 샤딩 지원
- CacheService: Redis 연결 풀 관리  
- AIChatService: OpenAI GPT 통합
- ExternalService: 외부 API 클라이언트

**Infrastructure Services (6개)**:
- StorageService: AWS S3 스토리지
- SearchService: AWS OpenSearch
- VectorDbService: AWS Bedrock 임베딩
- LockService: 분산 락 관리
- QueueService: 메시지 큐 시스템
- SchedulerService: 백그라운드 작업 스케줄링

**Communication Services (3개)**:
- WebSocketService: 실시간 통신
- NotificationService: 멀티채널 알림
- EmailService/SmsService: AWS SES/SNS

### 🔄 서비스 초기화 라이프사이클

애플리케이션 시작 시 다음 순서로 초기화됩니다:

1. Logger 설정 (KST 타임존, 로그 로테이션)
2. 환경별 Config 로딩 (LOCAL/DEBUG/PROD)
3. Redis 캐시 초기화 및 네임스페이싱
4. MySQL 데이터베이스 샤드 연결
5. AI Chat Service (OpenAI GPT 통합)
6. AWS 서비스들 (선택적, skipAwsTests 플래그)
7. Core 서비스들 (Lock, Scheduler, Queue)
8. Consumer 등록 (채팅 저장, 알림 전송)

## 4. AWS 인프라 서비스 통합 (2분)

### ☁️ AWS 서비스 생태계 통합

**스토리지 및 검색**:
- **S3**: 파일 업로드, 문서 저장
- **OpenSearch**: 지식 검색, 로그 분석
- **Bedrock**: 벡터 임베딩, AI 모델 추론

**통신 서비스**:
- **SES**: 이메일 알림 발송
- **SNS**: SMS 알림 발송

**외부 API 통합**:
- Korea Investment API: 실시간 주식 거래
- Financial Modeling Prep: 시장 데이터
- OpenAI GPT: AI 분석 및 챗봇

**데이터베이스 아키텍처**:
- **MySQL RDS Multi-AZ**: 고가용성 데이터베이스
- **Master-Slave 구조**: 읽기/쓰기 분산
- **글로벌 DB**: 사용자 계정, 설정 정보  
- **샤드 DB**: 사용자별 거래 데이터 분산 저장

## 5. Template 구현체와 라우터 매핑 (3분)

### 🎯 11개 도메인별 Template 구현체

실제 구현된 Template들을 소개하겠습니다:

**사용자 관리**:
- AccountTemplateImpl: 회원가입, 로그인, 인증
- ProfileTemplateImpl: 사용자 프로필, 설정 관리

**거래 시스템**:
- PortfolioTemplateImpl: 포트폴리오 관리, 거래 내역
- AutoTradeTemplateImpl: 자동매매 전략 관리
- MarketTemplateImpl: 시장 데이터, 기술적 분석

**AI 시스템**:
- ChatTemplateImpl: AI 채팅, 상태 머신 관리
- DashboardTemplateImpl: 대시보드 집계 데이터

**시스템 관리**:
- AdminTemplateImpl: 시스템 모니터링, 관리자 기능
- NotificationTemplateImpl: 멀티채널 알림 시스템
- CrawlerTemplateImpl: 데이터 크롤링 관리
- TutorialTemplateImpl: 사용자 온보딩 튜토리얼

### 🛣️ API 라우터 구조

main.py에서 각 Template을 다음과 같이 라우터로 매핑합니다:

```
/api/account     → AccountTemplateImpl
/api/portfolio   → PortfolioTemplateImpl  
/api/chat        → ChatTemplateImpl
/api/autotrade   → AutoTradeTemplateImpl
/api/market      → MarketTemplateImpl
/api/dashboard   → DashboardTemplateImpl
/api/admin       → AdminTemplateImpl
/ws              → WebSocketService
```

## 6. 데이터베이스 샤딩 전략 (2분)

### 🗄️ 글로벌 + 샤드 데이터베이스 설계

**Global Database (finance_global)**:
- table_users: 사용자 계정 정보
- table_shard_config: 샤드 라우팅 규칙
- table_user_api_keys: API 인증 키 관리

**Shard Databases (finance_shard_1, finance_shard_2)**:
- table_portfolio: 사용자별 포트폴리오
- table_transactions: 거래 내역
- table_autotrade: 자동매매 전략
- table_chat_messages: 채팅 기록
- table_notifications: 사용자별 알림

**Sharding Key**: `account_db_key % shard_count`

DatabaseService가 자동으로 적절한 샤드를 선택하여 데이터를 분산 처리합니다.

## 5. AI/LLM 통합 시스템 (3분)

### 🤖 LangGraph 기반 AI Router

AI 시스템의 핵심은 **LangGraph StateGraph**를 사용한 도구 라우팅입니다.

### 📈 20+ 금융 분석 도구 통합

**Basic Financial Tools (8개)**:
- FinancialStatementTool: 기업 재무제표
- MacroEconomicTool: 거시경제 지표
- TechnicalAnalysisTool: 기술적 분석
- MarketDataTool: 실시간 시세
- NewsTool: 금융 뉴스
- SectorAnalysisTool: 섹터 분석
- IndustryAnalysisTool: 산업 분석
- RagTool: RAG 기반 검색

**Advanced Analysis Tools (9개)**:
- KalmanRegimeFilterTool: 시장 레짐 감지
- MarketRegimeDetectorTool: 불/베어 마켓 분석
- BlackLittermanOptimizerTool: 포트폴리오 최적화
- DynamicRiskParityOptimizerTool: 리스크 패리티
- DynamicVaRModelTool: VaR 모델링
- MLSignalEnsembleTool: ML 신호 생성
- MultiFactorSignalGenerator: 멀티팩터 모델
- StressTestingFrameworkTool: 스트레스 테스트
- FeaturePipelineTool: 피처 엔지니어링

### 🔄 AI 처리 플로우

1. 사용자 채팅 요청
2. ChatTemplateImpl에서 상태 관리
3. LangGraph Router가 적절한 도구 선택
4. OpenAI GPT와 도구들의 협업
5. WebSocket을 통한 실시간 스트리밍 응답
6. 채팅 내역을 데이터베이스에 저장

## 6. 실시간 통신 시스템 (2분)

### 📡 WebSocket 기반 실시간 데이터

**WebSocket 엔드포인트**:
- `/ws`: 메인 WebSocket 연결
- `/ws/market`: 시장 데이터 스트리밍  
- `/ws/chat`: 채팅 메시지 스트리밍

**메시지 타입**:
- subscribe: 종목/지수 구독
- market: 시장 업데이트
- chat: AI 채팅 메시지
- portfolio: 포트폴리오 변경
- notification: 실시간 알림

### ⚡ 캐시 전략

Redis 네임스페이싱: `{app_id}:{env}:{service}:{key}`

예시:
- `finance_app:prod:session:token_abc123`
- `finance_app:local:lock:scheduler:job1`

## 7. 확장성과 성능 최적화 (2분)

### 🔄 무중단 배포 시스템

**CI/CD Pipeline**:
1. GitHub → Jenkins → Docker Hub
2. Auto Scaling Group Instance Refresh
3. MinHealthy: 50% (무중단 배포)
4. Health Check 통과 후 트래픽 라우팅

### 📊 모니터링 시스템

**Health Check 엔드포인트**:
- `/health`: 기본 헬스체크
- `/debug/services`: 전체 서비스 상태
- `/test/quick`: 빠른 서비스 테스트
- `/test/full`: 전체 서비스 테스트

**로깅 시스템**:
- KST 타임존 지원
- 로그 로테이션 (10MB 단위)
- 구조화된 로깅 (DEBUG/INFO/WARN/ERROR/CRITICAL)

## 8. 보안 및 에러 처리 (2분)

### 🛡️ 보안 체계

**인증/인가**:
- JWT 토큰 기반 인증
- Redis 세션 관리 (TTL: 3600초)
- API 키 관리 시스템

**입력 검증**:
- Pydantic 모델 기반 데이터 검증
- SQL Injection 방지 (Prepared Statements)
- CORS 및 Rate Limiting

### ⚠️ 에러 처리

**표준 에러 응답**:
```python
{
    "errorCode": ErrorCode.INVALID_REQUEST,
    "message": "상세 에러 메시지", 
    "sequence": request.sequence
}
```

**재시도 로직**:
- 데이터베이스 연결: 3회 재시도, 지수 백오프
- 외부 API 호출: 타임아웃 및 재시도 메커니즘

## 9. 결론 및 핵심 성과 (1분)

### ✅ 완성된 백엔드 시스템

**아키텍처 혁신**:
- Application Service Template 구조로 확장 가능한 설계
- ServiceContainer를 통한 중앙집중식 서비스 관리
- 11개 도메인별 Template 구현으로 모듈화된 비즈니스 로직

**기술적 우수성**:
- MySQL 샤딩으로 데이터 분산 처리
- 20+ AI 금융 분석 도구 통합
- WebSocket 기반 실시간 시스템
- 완전 자동화된 CI/CD 파이프라인

**운영 안정성**:
- 무중단 배포 시스템
- 종합적인 모니터링 및 로깅
- Enterprise-grade 보안 체계

이것이 저희가 완성한 **Enterprise급 AI Trading Platform Backend**입니다.

감사합니다.

---

*발표 시간: 약 22분*
*슬라이드 구성: 아키텍처 다이어그램 + 코드 예시 + 실제 동작 데모*