# 📊 SKN12-FINAL-2TEAM 프로젝트 문서화 작업 분배 (최종)

## 🎯 프로젝트 개요
**AI-powered Financial Trading Platform**
- 실시간 금융 데이터 처리 및 AI 기반 자동매매 플랫폼
- 3계층 아키텍처: Application(Router) → Template(Business Logic) → Service(Infrastructure)

## 🏗️ 핵심 아키텍처: Template-Service 연동 구조

### 시스템 융합 포인트
```
[Router Layer]
    ↓ HTTP/WebSocket 요청
[Template Layer] 
    ↓ 비즈니스 로직 처리
[Service Layer]
    ↓ 인프라 서비스 호출
[External Systems]
```

### Template별 Service 의존성 매핑

| Template | 사용 Service | 주요 기능 | 담당자 |
|----------|-------------|-----------|---------|
| **ChatTemplateImpl** | AIChatService, QueueService, CacheService | AI 채팅, 메시지 큐잉 | **지상원** |
| **DashboardTemplateImpl** | DatabaseService, ExternalService | 대시보드 데이터 집계 | **지상원** |
| **PortfolioTemplateImpl** | DatabaseService, CacheService | 포트폴리오 관리 | **지상원** |
| **AutotradeTemplateImpl** | DatabaseService, YahooFinanceClient | 자동매매 전략 | **지상원** |
| **MarketTemplateImpl** | ExternalService, WebSocketService | 실시간 시장 데이터 | **지상원** |
| **NotificationTemplateImpl** | QueueService, SchedulerService, EmailService, SmsService | 멀티채널 알림 | **박진양** |
| **ModelTemplateImpl** | DatabaseService, ML Models | AI 모델 서빙 | **지상원** |
| **AccountTemplateImpl** | DatabaseService, CacheService | 사용자 인증 | **박진양** |
| **ProfileTemplateImpl** | DatabaseService | 프로필 관리 | **지상원** |
| **TutorialTemplateImpl** | DatabaseService | 튜토리얼 | **지상원** |
| **CrawlerTemplateImpl** | ExternalService | 데이터 크롤링 | **박진양** |
| **AdminTemplateImpl** | All Services | 시스템 관리 | **박진양** |

---

## 📂 폴더별 담당자 배정 (확정)

### 🟦 **지상원 단독 담당**

#### Frontend 전체
```
✅ base_server/frontend/ai-trading-platform/  [전체]
   ├── app/                     # Next.js 페이지
   ├── components/              # React 컴포넌트
   ├── hooks/                   # Custom Hooks
   ├── lib/                     # 유틸리티
   ├── providers/               # Context Providers
   └── types/                   # TypeScript 타입
```

#### API 라우터
```
✅ base_server/application/base_web_server/routers/  [전체]
   ├── chat.py                  # 채팅 API
   ├── dashboard.py             # 대시보드 API
   ├── market.py                # 시장 데이터 API
   ├── websocket.py             # WebSocket API
   ├── profile.py               # 프로필 API
   └── tutorial.py              # 튜토리얼 API
```

#### LLM/AI 전체 시스템
```
✅ base_server/service/llm/  [전체]
   ├── AIChat_service.py        # AI 채팅 서비스
   └── llm_config.py            # LLM 설정

✅ base_server/service/llm/AIChat/  [전체]
   ├── Router.py                # LangGraph 라우터
   ├── BaseFinanceTool.py       # 기본 도구 클래스
   ├── SessionAwareTool.py      # 세션 관리
   ├── BasicTools/              # 기본 금융 도구들 (전체)
   │   ├── FinancialStatementTool.py
   │   ├── MacroEconomicTool.py
   │   ├── MarketDataTool.py
   │   ├── NewsTool.py
   │   ├── SectorAnalysisTool.py
   │   ├── TechnicalAnalysisTool.py
   │   ├── IndustryAnalysisTool.py
   │   └── RagTool.py           # RAG 도구도 지상원
   ├── tool/                    # 고급 AI 도구들 (전체)
   │   ├── KalmanRegimeFilterTool.py
   │   ├── BlackLittermanOptimizerTool.py
   │   ├── DynamicRiskParityOptimizerTool.py
   │   ├── DynamicVaRModelTool.py
   │   ├── MLSignalEnsembleTool.py
   │   ├── MarketRegimeDetectorTool.py
   │   ├── MultiFactorSignalGenerator.py
   │   ├── StressTestingFrameworkTool.py
   │   └── FeaturePipelineTool.py
   └── manager/                 # AI 상태 관리 (전체)
       ├── KalmanInitializerTool.py
       ├── KalmanRegimeFilterCore.py
       └── KalmanStateManager.py
```

#### 채팅 비즈니스 로직
```
✅ base_server/template/chat/  [전체]
   ├── chat_template_impl.py
   ├── chat_state_machine.py
   ├── chat_persistence_consumer.py  # 채팅 DB 저장
   └── common/
```

#### 대시보드/마켓 템플릿
```
✅ base_server/template/dashboard/  [전체]
✅ base_server/template/market/  [전체]
✅ base_server/template/profile/  [전체]
✅ base_server/template/tutorial/  [전체]
```

#### AI 모델 서빙
```
✅ base_server/template/model/  [전체]
   ├── model_template_impl.py
   ├── lstm_model.py
   ├── transformer_model.py
   ├── pytorch_lstm_model.py
   ├── optimized_pytorch_lstm.py
   ├── data_collector.py
   ├── data_preprocessor.py
   ├── inference_pipeline.py
   ├── train_model.py
   └── advanced_features.py
```

#### WebSocket 서비스
```
✅ base_server/service/websocket/  [전체]
✅ base_server/service/external/  [WebSocket 관련 파일만]
   ├── websocket_manager.py
   ├── iocp_websocket.py
   └── korea_investment_websocket_*.py
```

### 🟩 **박진양 단독 담당**

#### VectorDB 시스템
```
✅ base_server/service/vectordb/  [전체]
   ├── vectordb_service.py
   ├── bedrock_vectordb_client.py
   └── vectordb_config.py
```

#### OpenSearch 시스템
```
✅ base_server/service/search/  [전체]
   ├── search_service.py
   ├── opensearch_client.py
   └── search_config.py

✅ aws-setup/scripts/  [전체]
   ├── opensearch_scheduler.py
   └── opensearch_scheduler.zip
```

#### RAG 인프라 시스템
```
✅ base_server/service/rag/  [전체]
   ├── rag_service.py
   ├── rag_client.py
   └── rag_vectordb_client.py
```

#### 스케줄러 시스템
```
✅ base_server/service/scheduler/  [전체]
   ├── scheduler_service.py
   ├── base_scheduler.py
   └── table_scheduler.py
```

#### 알림 시스템
```
✅ base_server/template/notification/  [전체]
   ├── notification_template_impl.py
   ├── notification_persistence_consumer.py  # 멀티채널 발송
   └── common/

✅ base_server/service/notification/  [전체]
✅ base_server/service/email/  [전체]
✅ base_server/service/sms/  [전체]
```

#### 크롤러
```
✅ base_server/template/crawler/  [전체]
```

#### DB 스크립트 (특수)
```
✅ base_server/db_scripts/  [특정 파일들]
   ├── extend_finance_shard_signal.sql
   ├── create_universal_outbox.sql
   └── extend_finance_shard_notifications.sql
```

#### 지상원 추가 담당
```
✅ base_server/template/portfolio/  [전체]
   └── portfolio_template_impl.py

✅ base_server/template/autotrade/  [전체]
   └── autotrade_template_impl.py

✅ base_server/application/base_web_server/routers/  [추가]
   ├── portfolio.py  [포트폴리오 API]
   └── autotrade.py  [자동매매 API]

✅ base_server/service/external/  [WebSocket 외 나머지]
   ├── external_service.py
   ├── korea_investment_service.py
   ├── yahoo_finance_client.py
   └── dashboard.py

✅ base_server/service/storage/  [S3 스토리지 전체]

✅ base_server/db_scripts/  [AI 관련 스크립트]
   ├── chat_tables_extension.sql
   └── kalman_tables_extension.sql
```

### 🟩 **박진양 추가 담당**

#### 메인 서버 설정
```
✅ base_server/application/base_web_server/
   ├── main.py  [서비스 초기화 로직]
   └── base_web_server-config*.json  [설정 파일]
```

#### 핵심 인프라 서비스
```
✅ base_server/service/
   ├── service_container.py  [DI 컨테이너]
   ├── db/  [데이터베이스 서비스]
   │   ├── database_service.py  # 샤딩 로직
   │   └── mysql_client.py
   ├── cache/  [캐시 서비스]
   │   ├── cache_service.py
   │   └── redis_cache_client.py
   ├── queue/  [큐 서비스]
   │   ├── queue_service.py
   │   └── message_queue.py
   └── lock/  [분산 락]
       └── lock_service.py
```

#### 추가 템플릿
```
✅ base_server/template/
   ├── account/  [계정 관리]
   │   └── account_template_impl.py
   └── admin/  [관리자]
       └── admin_template_impl.py
```

#### 추가 라우터
```
✅ base_server/application/base_web_server/routers/
   ├── account.py  [인증 API]
   ├── securities.py  [증권사 API]
   ├── notification.py  [알림 API]
   └── admin.py  [관리 API]
```

#### DB 스크립트 (기본)
```
✅ base_server/db_scripts/  [기본 스크립트]
   ├── 01_create_finance_global_db.sql
   ├── 02_create_finance_procedures.sql
   ├── 03_create_finance_shard_dbs.sql
   └── extend_finance_shard_tutorial.sql
```

#### 프로젝트 문서
```
✅ docs/  [배포 가이드]
   ├── 01~08 Docker/Jenkins 가이드
   └── PROJECT_DOCUMENTATION_*.md

✅ 산출물/  [산출물]
   ├── 시스템 아키텍처.docx
   └── 발표자료/
```

#### 프로젝트 설정
```
✅ 프로젝트 루트
   ├── docker-compose.*.yml  [Docker 설정]
   ├── Jenkinsfile  [CI/CD]
   └── CLAUDE.md  [프로젝트 가이드]
```

---

## 📊 Template-Service 연동 관계 정리

### 지상원 주도 연동
| Template → Service | 용도 |
|-------------------|------|
| ChatTemplate → AIChatService | LLM 채팅 처리 |
| ChatTemplate → QueueService | 메시지 큐잉 |
| DashboardTemplate → DatabaseService | 대시보드 데이터 |
| MarketTemplate → WebSocketService | 실시간 시장 데이터 |
| ProfileTemplate → DatabaseService | 프로필 관리 |
| ModelTemplate → ML Models | AI 모델 서빙 |
| AIChat/BasicTools → External APIs | 금융 데이터 수집 |
| AIChat/tool → Advanced AI Analysis | 고급 AI 분석 |
| RagTool → RagService | RAG 검색 (도구는 지상원, 인프라는 박진양) |

### 박진양 주도 연동
| Template → Service | 용도 |
|-------------------|------|
| NotificationTemplate → SchedulerService | 알림 스케줄링 |
| NotificationTemplate → EmailService/SmsService | 멀티채널 발송 |
| CrawlerTemplate → ExternalService | 데이터 수집 |
| RagService → VectorDbService | 벡터 검색 |
| RagService → SearchService | 문서 검색 |
| SchedulerService → Database | 스케줄 관리 |

### 지상원 추가 연동
| Template → Service | 용도 |
|-------------------|------|
| PortfolioTemplate → DatabaseService | 포트폴리오 관리 |
| AutotradeTemplate → ExternalService | 자동매매 실행 |
| ExternalService → API Clients | 외부 데이터 수집 |
| StorageService → S3 | 파일 저장 관리 |

### 박진양 추가 연동
| Template → Service | 용도 |
|-------------------|------|
| AccountTemplate → DatabaseService/CacheService | 인증 처리 |
| AdminTemplate → All Services | 시스템 관리 |
| ServiceContainer → All Services | DI 컨테이너 관리 |
| DatabaseService → MySQL Sharding | DB 샤딩 처리 |

---

## 📝 문서화 템플릿

### 폴더별 README.md 구조
```markdown
# 📁 [폴더명]

## 📌 개요
- 주요 기능과 목적

## 🏗️ 구조
- 파일/폴더 구조

## 🔧 핵심 기능
- 주요 클래스/함수

## 🔄 Template-Service 연동
- 사용하는 Service 목록
- 연동 방식 설명

## 📊 데이터 흐름
- Request → Template → Service → Response

## 🚀 사용 예제
- 코드 샘플

## ⚙️ 설정
- 환경 변수/설정 파일

## 🔗 연관 폴더
- 의존성 관계
```

---

## 🎯 작업 진행 일정

### Phase 1: 핵심 시스템 (1주차)
**지상원**
- Frontend 전체 아키텍처
- LLM/AIChat 전체 시스템
- WebSocket 실시간 통신
- AI 모델 템플릿

**박진양**
- VectorDB/OpenSearch
- RAG 인프라 시스템
- 스케줄러

**박진양**
- main.py 서비스 초기화
- DatabaseService/CacheService
- ServiceContainer DI 구조

### Phase 2: 비즈니스 로직 (2주차)
**지상원**
- Dashboard/Market Template
- Profile/Tutorial Template
- API Router 연동
- AI 도구 체인

**박진양**
- Notification 멀티채널
- Crawler 시스템
- DB 스크립트 (특수)

**지상원**
- Portfolio/Autotrade Template
- External Service 연동

**박진양**
- Account Template
- Admin Template

### Phase 3: 통합 및 최적화 (3주차)
**지상원**
- Frontend-Backend 통합 테스트
- WebSocket 성능 최적화
- AI 모델 성능 튜닝

**박진양**
- 스케줄러 최적화
- 알림 시스템 최적화

**박진양**
- Admin 시스템 완성
- Docker/Jenkins 배포
- 시스템 아키텍처 문서

---

## ✅ 작업 체크리스트

### 지상원
- [ ] Frontend 컴포넌트 문서화
- [ ] LLM Router 플로우 다이어그램
- [ ] AI 도구 체인 설명
- [ ] WebSocket 통신 프로토콜 명세
- [ ] Chat State Machine 설명
- [ ] API Router 엔드포인트 명세
- [ ] AI 모델 학습/추론 파이프라인
- [ ] Kalman Filter 구현 설명

### 박진양
- [ ] VectorDB 임베딩 프로세스
- [ ] OpenSearch 인덱싱 전략
- [ ] RAG 인프라 파이프라인
- [ ] 스케줄러 작업 관리
- [ ] 알림 멀티채널 아키텍처
- [ ] Crawler 데이터 수집 로직

### 박진양 추가
- [ ] 서비스 초기화 순서도
- [ ] DB 샤딩 전략
- [ ] 캐시 전략
- [ ] 트랜잭션 관리
- [ ] Account/Admin 시스템 문서

### 지상원 추가
- [ ] Portfolio/Autotrade 시스템 문서
- [ ] External Service 연동 가이드
- [ ] Storage Service 사용법
- [ ] 성능 최적화 가이드

---

## 📊 최종 작업량 분배

| 담당자 | 담당 폴더 | 예상 작업량 |
|--------|-----------|-------------|
| **지상원** | 39개 (AI 전체 + Frontend + Portfolio/Autotrade + External/Storage + DB AI스크립트) | 55% |
| **박진양** | 32개 (인프라 전체 + Account/Admin + 핵심 서비스 + 배포 + DB 기본스크립트) | 45% |

---

**작성일**: 2025-08-16  
**버전**: 2.1 (AI 담당 수정)  
**작성자**: Claude AI Assistant

## 📞 협업 규칙
1. Template-Service 연동 변경시 상호 검토
2. 매일 진행상황 공유
3. 주간 통합 테스트
4. 크로스 의존성 발생시 즉시 소통

## 🔑 핵심 포인트
- **지상원**: Frontend + LLM/AI 전체 + WebSocket + Portfolio/Autotrade + External/Storage
- **박진양**: VectorDB + OpenSearch + RAG 인프라 + 스케줄러 + 알림 + 핵심 서비스 + Account/Admin + 배포