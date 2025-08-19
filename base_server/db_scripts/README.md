# AI Trading Platform — Database Scripts

> **개요**: SKN12-FINAL-2TEAM의 AI 트레이딩 플랫폼 백엔드 데이터베이스 스크립트입니다. 각 SQL 파일은 특정 도메인의 테이블 구조와 프로시저를 정의하며, Redis + MySQL 하이브리드 아키텍처를 지원합니다.

---

## 🏗️ 프로젝트 구조

### 디렉토리 구조
```
db_scripts/
├── kalman_tables_extension.sql                 # 칼만 필터 이력 관리 테이블
├── extend_finance_shard_signal.sql             # 시그널 알림 시스템
├── extend_finance_shard_tutorial.sql           # 튜토리얼 시스템
├── extend_finance_shard_notifications.sql      # 알림 시스템
├── drop_all_tables_and_recreate.sql            # 전체 테이블 재생성
├── create_universal_outbox.sql                 # Universal Outbox 패턴
└── chat_tables_extension.sql                   # 채팅 시스템 테이블
```

---

## 🔧 핵심 기능

### 1. **칼만 필터 시스템 (Kalman Filter System)**
- **파일**: `kalman_tables_extension.sql`
- **대상**: `finance_shard_1`, `finance_shard_2`
- **목적**: AI 트레이딩의 핵심인 칼만 필터 알고리즘의 상태 추적 및 이력 관리

#### **주요 테이블**
- **`table_kalman_history`**: 칼만 필터 실행 이력 및 상태 벡터 저장
  - 상태 벡터: `[trend, momentum, volatility, macro_signal, tech_signal]`
  - 공분산 행렬: 5x5 행렬로 불확실성 추적
  - 트레이딩 신호: 생성된 매수/매도 시그널
  - 성능 지표: 필터 성능 메트릭

#### **주요 프로시저**
- **`fp_kalman_history_insert`**: 칼만 필터 상태 저장
  - **입력**: ticker, account_db_key, timestamp, state_vector_x, covariance_matrix_p
  - **반환**: `SUCCESS` + `LAST_INSERT_ID`
- **`fp_kalman_latest_state_get`**: 최신 상태 조회 (Redis 복원용)
  - **입력**: ticker, account_db_key
  - **반환**: 최신 상태 벡터 및 공분산 행렬

---

### 2. **시그널 알림 시스템 (Signal Alert System)**
- **파일**: `extend_finance_shard_signal.sql`
- **대상**: `finance_shard_1`, `finance_shard_2`
- **목적**: 볼린저 밴드 기반 매수/매도 시그널 알림 및 성과 추적

#### **주요 테이블**
- **`table_signal_alarms`**: 사용자별 시그널 알림 등록
  - **금융권 표준**: `DECIMAL(19,6)` 정밀도 (Bloomberg Terminal 준수)
  - **지원 종목**: TSLA, AAPL 등 글로벌 주식
  - **알림 설정**: 활성화/비활성화, 사용자 메모

- **`table_signal_history`**: 시그널 발생 히스토리 및 성과 평가
  - **시그널 타입**: BUY/SELL
  - **성과 추적**: 1일 후 가격 변동, 수익률 계산
  - **승률 분석**: `is_win` 필드로 성공/실패 판정

#### **주요 프로시저**
- **`fp_signal_alarm_insert`**: 시그널 알림 등록
- **`fp_signal_alarm_update`**: 알림 설정 수정
- **`fp_signal_history_insert`**: 시그널 발생 기록
- **`fp_signal_performance_evaluate`**: 1일 후 성과 평가
- **`fp_user_signal_statistics`**: 사용자별 시그널 통계

#### **데이터 흐름**
```
1. 사용자 알림 등록 → table_signal_alarms
2. Model Server 시그널 분석 → table_signal_history
3. 1일 후 가격 추적 → 성과 평가
4. 승률/수익률 통계 → 사용자 대시보드
```

---

### 3. **Universal Outbox 패턴 (Event Sourcing)**
- **파일**: `create_universal_outbox.sql`
- **대상**: `finance_shard_1`, `finance_shard_2`
- **목적**: 분산 시스템에서의 이벤트 순서 보장 및 트랜잭션 일관성

#### **주요 테이블**
- **`universal_outbox`**: 이벤트 저장소
  - **도메인**: chat, portfolio, market
  - **파티션 키**: room_id, user_id, symbol
  - **시퀀스 번호**: 파티션 내 순서 보장
  - **상태 관리**: pending → published → failed/dead_letter

- **`outbox_sequences`**: 파티션별 시퀀스 번호 관리
  - **원자적 증가**: `INSERT ... ON DUPLICATE KEY UPDATE`
  - **동시성 제어**: 파티션별 독립적 시퀀스

#### **주요 프로시저**
- **`fn_get_next_sequence`**: 다음 시퀀스 번호 생성 (원자적)
- **`fp_universal_outbox_publish`**: 이벤트 발행
- **`fp_universal_outbox_mark_published`**: 발행 완료 표시
- **`fp_universal_outbox_mark_failed`**: 실패 처리
- **`fp_universal_outbox_cleanup`**: 완료된 이벤트 정리

#### **이벤트 순서 보장**
```
1. 이벤트 생성 → 시퀀스 번호 할당
2. 파티션별 순서 보장 → 동시성 제어
3. 발행 완료 → 상태 업데이트
4. 정리 작업 → 오래된 이벤트 삭제
```

---

### 4. **채팅 시스템 (AI Chatbot System)**
- **파일**: `chat_tables_extension.sql`
- **대상**: `finance_shard_1`, `finance_shard_2`
- **목적**: AI 챗봇과의 대화 세션 관리 및 메시지 히스토리

#### **주요 테이블**
- **`table_chat_rooms`**: 챗봇 세션 정보
  - **AI 페르소나**: 다양한 캐릭터/성격 설정
  - **세션 관리**: 활성/비활성 상태, 메시지 수 추적
  - **Redis 연동**: 세션 데이터와 MySQL 동기화

- **`table_chat_messages`**: 채팅 메시지 히스토리
  - **메시지 타입**: USER, AI, SYSTEM
  - **대화 체인**: parent_message_id로 대화 흐름 추적
  - **메타데이터**: 토큰 수, 모델 정보 등 JSON 저장

- **`table_chat_statistics`**: 사용자별 일일 통계
  - **사용량 추적**: 메시지 수, 토큰 사용량
  - **활성 세션**: 동시 활성 채팅방 수

#### **주요 프로시저**
- **`fp_chat_room_create`**: 채팅방 생성
- **`fp_chat_message_insert`**: 메시지 저장
- **`fp_chat_room_list`**: 사용자별 채팅방 목록
- **`fp_chat_message_list`**: 채팅방 메시지 히스토리
- **`fp_chat_statistics_update`**: 통계 업데이트

#### **Redis + MySQL 하이브리드**
```
1. 실시간 대화 → Redis (빠른 응답)
2. 영구 저장 → MySQL (히스토리 보존)
3. 동기화 → 주기적 데이터 동기화
4. 통계 집계 → 일일 사용량 분석
```

---

### 5. **튜토리얼 시스템 (Tutorial System)**
- **파일**: `extend_finance_shard_tutorial.sql`
- **대상**: `finance_shard_1`, `finance_shard_2`
- **목적**: 신규 사용자를 위한 단계별 학습 가이드

#### **주요 테이블**
- **`table_tutorial_progress`**: 사용자별 튜토리얼 진행 상황
  - **튜토리얼 타입**: OVERVIEW, PORTFOLIO, SIGNALS, CHAT, SETTINGS
  - **진행 단계**: 완료된 최고 스텝 번호 추적
  - **스텝 역행 방지**: UPSERT 방식으로 최대값 유지

#### **주요 프로시저**
- **`fp_tutorial_complete_step`**: 튜토리얼 스텝 완료 처리
- **`fp_tutorial_get_progress`**: 사용자별 전체 진행 상황 조회

---

### 6. **알림 시스템 (Notification System)**
- **파일**: `extend_finance_shard_notifications.sql`
- **대상**: `finance_shard_1`, `finance_shard_2`
- **목적**: 다양한 알림 채널을 통한 사용자 커뮤니케이션

#### **주요 테이블**
- **`table_inapp_notifications`**: 인앱 알림 메시지 저장
  - **알림 타입**: SIGNAL_ALERT, TRADE_COMPLETE 등
  - **우선순위**: 1=긴급, 5=낮음
  - **게임 방식**: 읽음/미읽음 마킹, 읽은 알림 자동 삭제

- **`table_inapp_notification_stats`**: 알림 통계 (샤드별)
  - **일일 통계**: 총 알림 수, 읽은/읽지 않은 알림 수
  - **우선순위별**: 긴급/높음/보통 알림 수 추적
  - **자동 삭제**: 읽은 알림 조회 시 자동 정리

#### **주요 프로시저**
- **`fp_inapp_notification_create`**: 인앱 알림 생성
- **`fp_inapp_notification_mark_read`**: 알림 읽음 처리
- **`fp_inapp_notification_get_unread`**: 미읽음 알림 조회
- **`fp_inapp_notification_stats_update`**: 통계 업데이트

---

### 7. **데이터베이스 초기화 및 재생성**
- **파일**: `drop_all_tables_and_recreate.sql`
- **대상**: `finance_global`, `finance_shard_1`, `finance_shard_2`
- **목적**: 개발 환경에서 전체 데이터베이스 구조 재생성

#### **주요 기능**
- **전체 삭제**: 기존 데이터베이스 및 테이블 완전 제거
- **글로벌 DB**: 사용자 계정, 샤드 설정, 에러 로그 등
- **샤드 DB**: 사용자별 비즈니스 데이터 테이블
- **개발용**: 외래키 체크 비활성화, 테이블 재생성

---

## 🌐 데이터베이스 아키텍처

### **전체 아키텍처 개요**

Base Server는 **글로벌 DB + 샤드 DB** 구조로 설계된 수평 분할 데이터베이스 시스템을 사용합니다.

```
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                       │
├─────────────────────────────────────────────────────────────┤
│                    DatabaseService                          │
│  ┌─────────────────┐  ┌──────────────────────────────────┐  │
│  │   Global DB     │  │        Shard DBs                 │  │
│  │                 │  │  ┌────────────┐ ┌────────────┐   │  │
│  │ - User Auth     │  │  │  Shard 1   │ │  Shard 2   │   │  │
│  │ - Shard Config  │  │  │ - Accounts │ │ - Accounts │   │  │
│  │ - User Mapping  │  │  │ - Portfolio│ │ - Portfolio│   │  │
│  │ - System Meta   │  │  │ - Trading  │ │ - Trading  │   │  │
│  └─────────────────┘  │  └────────────┘ └────────────┘   │  │
└─────────────────────────────────────────────────────────────┘
           │                        │
┌─────────────────┐    ┌──────────────────────────────────┐
│  Global MySQL   │    │         Shard MySQL              │
│  finance_global │    │  finance_shard_1, finance_shard_2│
└─────────────────┘    └──────────────────────────────────┘
```

#### **실제 데이터베이스 스키마 구조**
```
📊 Database Schemas
├── finance_global          # 글로벌 DB (공통 데이터)
├── finance_shard_1        # 샤드 1 (사용자별 데이터)
├── finance_shard_2        # 샤드 2 (사용자별 데이터)
└── sys                    # MySQL 시스템 스키마
```

### **글로벌 DB 시스템 (finance_global)**

글로벌 DB는 시스템 전체의 메타데이터와 인증 정보를 관리합니다.

#### **테이블 간 관계 구조**
```
┌─────────────────────────────────────────────────────────────┐
│                    finance_global                           │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │
│  │table_account│    │table_user_  │    │table_user_  │      │
│  │     id      │◄──►│   profiles  │◄──►│  api_keys   │      │
│  └─────────────┘    └─────────────┘    └─────────────┘      │
│           │                   │                   │         │
│           ▼                   ▼                   ▼         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │
│  │table_user_  │    │table_user_  │    │table_user_  │      │
│  │  shard_     │    │  payments   │    │password_    │      │
│  │  mapping    │    │             │    │   hist      │      │
│  └─────────────┘    └─────────────┘    └─────────────┘      │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────┐    ┌─────────────┐                         │
│  │table_shard_ │    │table_shard_ │                         │
│  │   config    │◄──►│    stats    │                         │
│  └─────────────┘    └─────────────┘                         │
│                                                             │
│  ┌─────────────┐                                            │
│  │table_error  │                                            │
│  │    log      │                                            │
│  └─────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
```

#### **테이블 상세 구조**
각 테이블은 다음과 같은 내부 구조를 가집니다:
- **Columns**: 테이블의 컬럼 정의 (데이터 타입, 제약조건 등)
- **Indexes**: 성능 최적화를 위한 인덱스
- **Foreign Keys**: 테이블 간 관계 정의
- **Triggers**: 데이터 변경 시 자동 실행되는 트리거

#### **주요 테이블 구조**

**1. 계정 관리: `table_accountid`**
- **`account_db_key`**: 사용자 고유 식별자 (샤드 라우팅에 사용)
- **`platform_type`**: 플랫폼 구분 (1=웹, 2=모바일 등)
- **`account_status`**: 계정 상태 (Normal, Blocked, Suspended)
- **`account_level`**: 권한 레벨 (1=일반, 2=운영자, 3=개발자, 4=관리자)
- **`login_count`**: 첫 로그인 감지용 카운터

**2. 샤드 설정: `table_shard_config`**
- **`shard_id`**: 샤드 식별자 (1, 2)
- **`shard_name`**: 샤드 이름 (finance_shard_1, finance_shard_2)
- **`host`, `port`**: MySQL 서버 연결 정보
- **`status`**: 샤드 상태 (active, maintenance, disabled)

**3. 사용자 샤드 매핑: `table_user_shard_mapping`**
- **`account_db_key`**: 사용자 계정 키
- **`shard_id`**: 할당된 샤드 ID
- **`assigned_at`**: 샤드 할당 시간

**4. 샤드 통계: `table_shard_stats`**
- **`user_count`**: 샤드별 사용자 수
- **`active_users`**: 활성 사용자 수
- **`last_updated`**: 마지막 업데이트 시간

**5. 에러 로그: `table_errorlog`**
- **`procedure_name`**: 프로시저 이름
- **`error_state`**: 에러 상태
- **`error_no`**: 에러 번호
- **`error_message`**: 에러 메시지
- **`param`**: 프로시저 파라미터
- **`create_time`**: 생성 시간

**6. 사용자 프로필: `table_user_profiles`**
- **`account_db_key`**: 사용자 계정 키
- **`investment_experience`**: 투자 경험 수준
- **`risk_tolerance`**: 위험 감수 수준
- **`investment_goal`**: 투자 목표
- **`monthly_budget`**: 월 투자 예산
- **`country`**: 국가
- **`timezone`**: 시간대
- **`email_notifications_enabled`**: 이메일 알림 활성화
- **`sms_notifications_enabled`**: SMS 알림 활성화
- **`push_notifications_enabled`**: 푸시 알림 활성화
- **`price_alert_enabled`**: 가격 알림 활성화
- **`portfolio_alert_enabled`**: 포트폴리오 알림 활성화
- **`trade_alert_enabled`**: 거래 알림 활성화

**7. 사용자 API 키: `table_user_api_keys`**
- **`account_db_key`**: 사용자 계정 키
- **`korea_investment_app_key`**: 한국투자증권 API 키
- **`korea_investment_app_secret`**: 한국투자증권 API 시크릿

**8. 사용자 결제: `table_user_payments`**
- **`account_db_key`**: 사용자 계정 키
- **`payment_plan`**: 결제 플랜 ID
- **`plan_name`**: 플랜 이름
- **`plan_price`**: 플랜 가격
- **`currency`**: 통화
- **`billing_cycle`**: 결제 주기
- **`starts_at`**: 구독 시작일
- **`expires_at`**: 구독 만료일
- **`auto_renewal`**: 자동 갱신 여부
- **`payment_method`**: 결제 방법
- **`payment_status`**: 결제 상태

**9. 비밀번호 히스토리: `table_password_history`**
- **`account_db_key`**: 사용자 계정 키
- **`old_password_hash`**: 과거 비밀번호 해시
- **`new_password_hash`**: 새로운 비밀번호 해시
- **`changed_at`**: 변경 시간
- **`changed_by_ip`**: 변경 주체

#### **주요 스토어드 프로시저**

**1. 사용자 인증 및 관리**
- **`fp_user_signup`**: 사용자 회원가입 및 샤드 할당
- **`fp_user_login`**: 사용자 로그인 및 세션 생성
- **`fp_user_logout`**: 사용자 로그아웃 및 세션 정리
- **`fp_change_password`**: 비밀번호 변경 및 히스토리 저장

**2. 프로필 관리**
- **`fp_profile_get`**: 사용자 프로필 정보 조회
- **`fp_profile_setup`**: 초기 프로필 설정
- **`fp_update_basic_profile`**: 기본 프로필 정보 업데이트
- **`fp_update_profile_all`**: 전체 프로필 정보 업데이트

**3. API 키 관리**
- **`fp_get_api_keys`**: 사용자 API 키 목록 조회
- **`fp_save_api_keys`**: 새로운 API 키 생성 및 저장

**4. 결제 및 구독**
- **`fp_get_payment_plan`**: 사용자 결제 플랜 정보 조회

**5. 알림 설정**
- **`fp_get_user_notification_settings`**: 사용자 알림 설정 조회
- **`fp_update_notification_settings`**: 알림 설정 업데이트

**6. 샤드 관리**
- **`fp_get_active_shard_ids`**: 활성 샤드 정보 조회
- **`fp_update_shard_status`**: 샤드 상태 업데이트

**7. 사용자 초기화**
- **`fp_initialize_user_defaults`**: 신규 사용자 기본 설정 초기화

**8. 연락처 정보**
- **`fp_get_user_contact_info`**: 사용자 연락처 정보 조회

#### **글로벌 DB 주요 기능**

**🔐 인증 및 권한 관리**
- 사용자 계정 생성, 로그인, 로그아웃
- 비밀번호 변경 및 보안 히스토리 관리
- 계정 상태 및 권한 레벨 관리

**👤 사용자 프로필 관리**
- 개인정보 및 기본 설정 관리
- 프로필 이미지 및 연락처 정보
- 사용자 선호도 및 커스터마이징 설정

**🔑 API 키 관리**
- 한국투자증권 API 키 생성 및 저장
- API 시크릿 암호화 및 보안 관리
- 사용자별 API 권한 설정

**💳 결제 및 구독 관리**
- 구독 플랜 및 결제 방법 관리
- 결제 주기 및 다음 결제일 추적
- 결제 상태 및 이력 관리

**🗄️ 샤드 시스템 관리**
- 샤드 설정 및 연결 정보 관리
- 사용자별 샤드 할당 및 매핑
- 샤드별 통계 및 상태 모니터링

**📊 시스템 모니터링**
- 프로시저 실행 에러 로깅
- 시스템 성능 및 상태 추적
- 디버깅 및 문제 해결 지원

**🔔 알림 설정 관리**
- 사용자별 알림 설정 저장
- 알림 유형 및 우선순위 관리
- 알림 설정 업데이트 및 동기화

### **샤드 DB 시스템**

각 샤드 DB(`finance_shard_1`, `finance_shard_2`)는 사용자별 비즈니스 데이터를 저장합니다.
finance_shard_1, finance_shard_2는 account_db_key에 따라 정해집니다.

#### **주요 테이블 구조**

**1. 아웃박스 패턴: `outbox_events`, `outbox_sequences`**
- **`outbox_events`**: 이벤트 순서 보장을 위한 아웃박스 테이블
- **`outbox_sequences`**: 아웃박스 시퀀스 관리

**2. SAGA 패턴: `saga_instances`, `saga_steps`**
- **`saga_instances`**: SAGA 트랜잭션 인스턴스 관리
- **`saga_steps`**: SAGA 트랜잭션 단계별 실행 정보

**3. 칼만 필터: `table_kalman_history`**
- **`ticker`**: 종목 코드
- **`state_vector_x`**: 상태 벡터 (JSON)
- **`covariance_matrix_p`**: 공분산 행렬 (JSON)
- **`trading_signal`**: 트레이딩 신호

**4. 시그널 시스템: `table_signal_alarms`, `table_signal_history`**
- **`table_signal_alarms`**: 매수/매도 시그널 알림
  - **`symbol`**: 종목 코드 (TSLA, AAPL 등)
  - **`current_price`**: 현재가 (DECIMAL(19,6))
  - **`is_active`**: 알림 활성화 상태
- **`table_signal_history`**: 시그널 히스토리
  - **`signal_type`**: BUY/SELL
  - **`signal_price`**: 시그널 발생 가격
  - **`profit_rate`**: 수익률 (DECIMAL(10,6))

**5. 채팅 시스템: `table_chat_rooms`, `table_chat_messages`, `table_chat_statistics`**
- **`table_chat_rooms`**: AI 챗봇 채팅방
  - **`room_id`**: 채팅방 ID
  - **`ai_persona`**: AI 페르소나
  - **`message_count`**: 메시지 수
- **`table_chat_messages`**: 채팅 메시지 내용
- **`table_chat_statistics`**: 채팅 통계 정보

**6. 사용자 데이터: `table_user_accounts`, `table_user_portfolios`**
- **`table_user_accounts`**: 사용자 계좌 정보
- **`table_user_portfolios`**: 사용자 포트폴리오 데이터

**7. 시스템 관리: `table_errorlog`, `table_inapp_notifications`**
- **`table_errorlog`**: 시스템 에러 로그
- **`table_inapp_notifications`**: 인앱 알림
  - **`type_id`**: 알림 타입
  - **`priority`**: 우선순위
  - **`is_read`**: 읽음 여부

**8. 튜토리얼: `table_tutorial_progress`**
- **`tutorial_type`**: 튜토리얼 타입
- **`completed_step`**: 완료된 스텝 번호

**9. 범용 아웃박스: `universal_outbox`**
- **이벤트 순서 보장을 위한 범용 아웃박스 테이블**

### **샤딩 전략 및 라우팅**

#### **샤드 할당 로직**
```python
# 방법 1: 단순 모듈로 방식 (현재 구현)
def assign_shard_for_user(account_db_key: int) -> int:
    return (account_db_key % 2) + 1

# 방법 2: 샤드별 부하 기반 할당 (향후 구현)
async def assign_shard_based_on_load(account_db_key: int) -> int:
    shard_stats = await get_shard_stats()
    return min(shard_stats, key=lambda x: x['user_count'])['shard_id']
```

#### **샤드 할당 예시 (실제 데이터 기반)**
```
사용자 ID: 1000 → (1000 % 2) + 1 = 1 → finance_shard_1
사용자 ID: 1001 → (1001 % 2) + 1 = 2 → finance_shard_2
사용자 ID: 1002 → (1002 % 2) + 1 = 1 → finance_shard_1
사용자 ID: 1003 → (1003 % 2) + 1 = 2 → finance_shard_2
```

#### **샤드 매핑 테이블 구조**
- **`table_user_shard_mapping`**: 사용자별 샤드 할당 정보
  - `account_db_key`: 사용자 계정 키
  - `shard_id`: 할당된 샤드 ID (1 또는 2)
  - `assigned_at`: 샤드 할당 시간
  - `updated_at`: 마지막 업데이트 시간

#### **실제 샤드 매핑 예시**
```
사용자 ID: 1001 → (1001 % 2) + 1 = 2 → finance_shard_2
사용자 ID: 1002 → (1002 % 2) + 1 = 1 → finance_shard_1
사용자 ID: 1003 → (1003 % 2) + 1 = 2 → finance_shard_2
```

#### **자동 라우팅 메커니즘**
- **세션 기반 라우팅**: `client_session.session.shard_id`에 따라 자동 DB 선택
- **익명 사용자**: 글로벌 DB로 라우팅 (로그인, 회원가입)
- **인증된 사용자**: 할당된 샤드로 자동 라우팅
- **명시적 샤드 호출**: 특정 샤드를 직접 지정하여 호출

#### **라우팅 시나리오**
```
1. 익명 사용자 (로그인, 회원가입)
   → client_session이 None이므로 글로벌 DB로 라우팅

2. 인증된 사용자 (포트폴리오 조회)
   → client_session.session.shard_id에 따라 적절한 샤드로 라우팅

3. 명시적 샤드 호출
   → call_shard_procedure(shard_id=1, ...)로 특정 샤드 직접 호출
```

### **Redis + MySQL 하이브리드**

#### **역할 분담**
- **Redis**: 실시간 데이터, 세션, 캐시, 메시지큐, 이벤트큐
- **MySQL**: 영구 데이터, 히스토리, 분석, 사용자 데이터

#### **데이터 동기화 전략**
- **세션 데이터**: Redis에 실시간 저장, MySQL에 주기적 동기화
- **캐시 데이터**: Redis에 자주 접근하는 데이터 캐싱
- **이벤트 데이터**: Redis에서 실시간 처리, MySQL에 영구 저장
- **일관성 보장**: Outbox 패턴을 통한 트랜잭션 일관성

### **트랜잭션 관리**

#### **글로벌 DB 트랜잭션**
- **계정 생성**: 계정 생성과 샤드 할당을 원자적으로 처리
- **샤드 매핑**: 사용자-샤드 매핑 정보 저장
- **에러 처리**: 실패 시 자동 롤백 및 에러 로깅

#### **샤드별 트랜잭션**
- **비즈니스 로직**: 계좌 생성, 거래 처리, 포트폴리오 업데이트
- **아웃박스 패턴**: 이벤트 발행과 비즈니스 로직의 원자성 보장
- **에러 처리**: 모든 프로시저에 표준화된 에러 로깅

#### **크로스 샤드 트랜잭션**
- **통계 수집**: 모든 샤드에서 데이터 수집하여 집계
- **모니터링**: 샤드별 상태 체크 및 헬스 모니터링
- **데이터 마이그레이션**: 샤드 간 데이터 이동 (향후 구현)

---

## 📊 성능 최적화

### **인덱싱 전략**
- **복합 인덱스**: `(account_db_key, symbol)`, `(room_id, created_at)`
- **파티션 키**: 도메인별 파티셔닝으로 동시성 향상
- **시퀀스 번호**: 파티션 내 순서 보장으로 정렬 비용 절약

### **데이터 타입 최적화**
- **금융 데이터**: `DECIMAL(19,6)` 정밀도로 정확한 계산
- **JSON 필드**: 메타데이터, 상태 벡터 등 유연한 구조
- **UUID**: 분산 환경에서의 고유성 보장

### **쿼리 최적화**
- **프로시저**: 복잡한 로직을 데이터베이스 레벨에서 처리
- **배치 처리**: 대량 데이터 처리 시 효율적인 집계
- **정규화**: 중복 데이터 최소화 및 일관성 보장

---

## 🔗 연관 시스템

### **사용하는 Service**
- **service.lock**: 분산 락 및 동시성 제어
- **service.scheduler**: 정기적인 데이터 정리 및 동기화
- **service.cache**: Redis 기반 실시간 데이터 관리
- **service.db**: MySQL 연결 및 트랜잭션 관리

### **사용하는 Template**
- **template.account**: 사용자 계정 및 인증
- **template.finance**: 금융 데이터 및 포트폴리오
- **template.chat**: AI 챗봇 및 대화 관리

### **외부 시스템**
- **Redis**: 실시간 데이터 및 세션 관리
- **Model Server**: AI 모델 및 시그널 생성
- **Notification Service**: 이메일, SMS, 푸시 알림

---

## 🚀 배포 및 관리

### **스크립트 실행 순서**
1. **기본 구조**: `drop_all_tables_and_recreate.sql`
2. **핵심 시스템**: `create_universal_outbox.sql`
3. **도메인별 확장**: 각 도메인별 extension 스크립트
4. **데이터 마이그레이션**: 기존 데이터 이전 및 검증

### **환경별 설정**
- **개발환경**: 외래키 체크 비활성화, 테이블 재생성
- **운영환경**: 데이터 보존, 점진적 마이그레이션
- **테스트환경**: 샘플 데이터, 성능 테스트

### **모니터링 및 유지보수**
- **에러 로그**: `table_errorlog` 테이블을 통한 프로시저 에러 추적
- **성능 지표**: 쿼리 실행 시간, 인덱스 사용률 모니터링
- **정기 정리**: 오래된 데이터, 완료된 이벤트 정리

---

이 데이터베이스 스크립트들은 **AI 트레이딩 플랫폼의 핵심 인프라**를 구성하며, **고성능, 확장성, 안정성**을 모두 고려한 설계를 반영하고 있습니다.
