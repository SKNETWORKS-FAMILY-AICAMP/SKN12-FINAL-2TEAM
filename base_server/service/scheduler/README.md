# 📁 Scheduler Service

## 📌 개요
Scheduler 서비스는 111 gameserver 패턴을 따르는 스케줄러 서비스로, 주기적 작업 실행, 분산락 지원, 다양한 스케줄 타입을 제공합니다. 정적 클래스 구조를 사용하여 서비스 생명주기를 관리하며, 비동기 작업 실행과 분산 환경에서의 안전한 작업 처리를 지원합니다.

## 🏗️ 구조
```
base_server/service/scheduler/
├── __init__.py                    # 모듈 초기화
├── scheduler_service.py           # 메인 서비스 클래스 (정적 클래스)
├── base_scheduler.py              # 기본 스케줄러 구현
└── table_scheduler.py             # 테이블 생성 전용 스케줄러
```

## 🔧 핵심 기능

### SchedulerService (정적 클래스)
- **정적 클래스**: 111 gameserver 패턴으로 서비스 인스턴스 관리
- **초기화 관리**: `init()`, `shutdown()`, `is_initialized()` 메서드
- **분산락 지원**: LockService를 통한 분산 환경에서의 안전한 작업 실행
- **작업 관리**: 작업 추가, 제거, 상태 조회, 시작/중지

### 주요 기능 그룹

#### 1. 스케줄 작업 관리 (Job Management)
```python
# 작업 추가
await SchedulerService.add_job(job)

# 작업 제거
await SchedulerService.remove_job(job_id)

# 작업 상태 조회
job_status = SchedulerService.get_job_status(job_id)

# 모든 작업 상태 조회
all_jobs = SchedulerService.get_all_jobs_status()
```

#### 2. 스케줄러 제어 (Scheduler Control)
```python
# 스케줄러 시작
await SchedulerService.start()

# 스케줄러 중지
await SchedulerService.stop()

# 스케줄러 인스턴스 획득
scheduler = SchedulerService.get_scheduler()
```

#### 3. 스케줄 타입 지원 (Schedule Types)
```python
# 주기적 실행 (초 단위)
ScheduleType.INTERVAL: "30"  # 30초마다

# 매일 특정 시간
ScheduleType.DAILY: "14:30"  # 매일 오후 2시 30분

# 일회성 실행
ScheduleType.ONCE: datetime.now()

# Cron 표현식 (구현 예정)
ScheduleType.CRON: "0 0 * * *"
```

#### 4. 분산락 지원 (Distributed Lock)
```python
# 분산락을 사용한 작업 실행
job = ScheduleJob(
    job_id="unique_job_id",
    name="분산락 작업",
    use_distributed_lock=True,
    lock_key="custom_lock_key",
    lock_ttl=300  # 5분
)
```

#### 5. 테이블 스케줄러 (Table Scheduler)
```python
# 일일 테이블 생성
await TableScheduler.create_daily_tables()

# 월간 요약 테이블 생성
await TableScheduler.create_monthly_summary_tables()

# 오래된 테이블 정리
await TableScheduler.cleanup_old_tables()
```

## 🔄 Template-Service 연동

### 사용하는 Service
- **`service.core.logger.Logger`**: 로깅 서비스
- **`service.lock.lock_service.LockService`**: 분산락 서비스 (선택적)
- **`service.service_container.ServiceContainer`**: 서비스 컨테이너 (TableScheduler에서 사용)

### 연동 방식
1. **초기화**: `SchedulerService.init(lock_service)` 호출
2. **작업 등록**: `ScheduleJob` 객체를 생성하여 `add_job()` 호출
3. **스케줄러 시작**: `start()` 호출로 백그라운드 작업 실행
4. **정리**: `shutdown()` 호출로 리소스 해제

## 📊 데이터 흐름

### 스케줄 작업 실행 프로세스
```
SchedulerService.start() → BaseScheduler._scheduler_loop() → 실행 가능한 작업 검색
                                                                    ↓
                                                            작업 실행 (BaseScheduler._execute_job)
                                                                    ↓
                                                        분산락 사용 여부 확인
                                                                    ↓
                                                ├── 분산락 사용: BaseScheduler._execute_job_with_lock()
                                                └── 직접 실행: BaseScheduler._execute_job_direct()
                                                                    ↓
                                                            다음 실행 시간 계산 (BaseScheduler._calculate_next_run)
```

### 분산락 작업 실행 프로세스
```
작업 실행 요청 → 분산락 획득 시도 → 락 획득 성공 → 작업 실행 → 락 해제
                    ↓
                락 획득 실패 → 다른 인스턴스에서 실행 중으로 판단 → 작업 스킵
```

## 🚀 사용 예제

### 기본 초기화
```python
from service.scheduler.scheduler_service import SchedulerService
from service.scheduler.base_scheduler import ScheduleJob, ScheduleType

# LockService와 함께 초기화 (분산락 지원)
lock_service = ServiceContainer.get_lock_service()
SchedulerService.init(lock_service)

# 스케줄러 시작
await SchedulerService.start()
```

### 주기적 작업 등록
```python
# 30초마다 실행되는 작업
interval_job = ScheduleJob(
    job_id="periodic_task",
    name="주기적 작업",
    schedule_type=ScheduleType.INTERVAL,
    schedule_value=30,  # 30초
    callback=async def periodic_task():
        print("30초마다 실행되는 작업")
)

await SchedulerService.add_job(interval_job)
```

### 매일 특정 시간 실행 작업
```python
# 매일 오후 2시 30분에 실행되는 작업
daily_job = ScheduleJob(
    job_id="daily_report",
    name="일일 리포트 생성",
    schedule_type=ScheduleType.DAILY,
    schedule_value="14:30",
    callback=async def generate_daily_report():
        print("일일 리포트 생성")
)

await SchedulerService.add_job(daily_job)
```

### 분산락을 사용한 작업
```python
# 분산락을 사용하여 중복 실행 방지
distributed_job = ScheduleJob(
    job_id="distributed_task",
    name="분산 작업",
    schedule_type=ScheduleType.INTERVAL,
    schedule_value=60,
    use_distributed_lock=True,
    lock_key="unique_distributed_task",
    lock_ttl=300,
    callback=async def distributed_task():
        print("분산락으로 보호된 작업")
)

await SchedulerService.add_job(distributed_job)
```

### 테이블 스케줄러 사용
```python
from service.scheduler.table_scheduler import TableScheduler

# 일일 테이블 생성 작업 등록
table_job = ScheduleJob(
    job_id="daily_table_creation",
    name="일일 테이블 생성",
    schedule_type=ScheduleType.DAILY,
    schedule_value="02:00",  # 매일 오전 2시
    callback=TableScheduler.create_daily_tables,
    use_distributed_lock=True,
    lock_key="scheduler:create_daily_tables",
    lock_ttl=1800
)

await SchedulerService.add_job(table_job)
```

## ⚙️ 설정

### ScheduleJob 주요 설정
```python
@dataclass
class ScheduleJob:
    job_id: str                           # 고유 작업 ID
    name: str                             # 작업 이름
    schedule_type: ScheduleType           # 스케줄 타입
    schedule_value: Any                   # 스케줄 값
    callback: Callable                    # 실행할 콜백 함수
    enabled: bool = True                  # 작업 활성화 여부
    use_distributed_lock: bool = False    # 분산락 사용 여부
    lock_key: Optional[str] = None        # 커스텀 락 키
    lock_ttl: int = 300                  # 락 TTL (초)
    last_run: Optional[datetime] = None  # 마지막 실행 시간
    next_run: Optional[datetime] = None  # 다음 실행 시간
    run_count: int = 0                    # 실행 횟수
    error_count: int = 0                  # 오류 횟수
    max_retries: int = 3                  # 최대 재시도 횟수
```

### 스케줄 타입별 설정값
```python
# INTERVAL: 초 단위 정수
schedule_value = 30  # 30초마다

# DAILY: "HH:MM" 형식 문자열
schedule_value = "14:30"  # 매일 오후 2시 30분

# ONCE: datetime 객체 또는 즉시 실행
schedule_value = datetime(2024, 1, 1, 12, 0)  # 특정 시간
schedule_value = None  # 즉시 실행

# CRON: Cron 표현식 (구현 예정)
schedule_value = "0 0 * * *"  # 매일 자정
```

## 🔗 연관 폴더

### 의존성 관계
- **`service.core.logger`**: 로깅 서비스
- **`service.lock`**: 분산락 서비스 (선택적)
- **`service.service_container`**: 서비스 컨테이너
- **`application.base_web_server.main`**: 메인 서버에서 스케줄러 초기화 및 작업 등록 (main.py에서 SchedulerService 사용)

### 사용하는 Template
- **`template.crawler`**: 크롤링 작업 스케줄링
- **`template.notification`**: 알림 배치 처리 스케줄링
- **`template.chat`**: 채팅 데이터 배치 처리 스케줄링
- **`template.admin`**: 관리자 모니터링 작업 스케줄링

### 외부 시스템
- **데이터베이스**: 테이블 자동 생성 및 정리
- **분산 환경**: Redis 기반 분산락을 통한 중복 실행 방지
- **비동기 처리**: asyncio 기반 비동기 작업 실행
