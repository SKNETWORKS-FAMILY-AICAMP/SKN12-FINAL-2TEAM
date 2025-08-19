# AI Trading Platform — Database Service

> **개요**: SKN12-FINAL-2TEAM의 AI 트레이딩 플랫폼 백엔드 Database 서비스입니다. MySQL 기반 데이터베이스 서비스로, 글로벌 DB와 샤드 DB를 지원하는 분산 데이터베이스 시스템입니다. 인스턴스 기반 클래스 시스템으로, 세션 기반 자동 라우팅을 제공합니다.

---

## 🏗️ 프로젝트 구조

### 디렉토리 구조
```
db/
├── __init__.py                    # 패키지 초기화
├── database_service.py            # 메인 Database 서비스 (샤딩 지원)
├── mysql_client.py                # MySQL 클라이언트 (연결 풀 관리)
└── database_config.py             # 데이터베이스 설정 모델
```

---

## 🔧 핵심 기능

### 1. **Database 서비스 (DatabaseService)**
- **인스턴스 기반**: 일반 클래스로 서비스 인스턴스 관리
- **샤딩 지원**: 글로벌 DB와 샤드 DB 자동 라우팅
- **세션 기반 라우팅**: 클라이언트 세션에 따른 자동 DB 선택
- **연결 풀 관리**: MySQL 연결 풀을 통한 성능 최적화

### 2. **샤딩 시스템**
- **글로벌 DB**: 사용자 인증, 설정 정보 등 공통 데이터
- **샤드 DB**: 사용자별 포트폴리오, 거래 내역 등 개인 데이터
- **동적 샤드 관리**: `table_shard_config` 테이블 기반 샤드 설정
- **자동 라우팅**: 세션 정보를 통한 적절한 샤드 선택

### 3. **고급 기능**
- **연결 재시도**: 연결 실패 시 자동 재연결 및 재시도
- **스토어드 프로시저**: MySQL 스토어드 프로시저 호출 지원
- **호환성 유지**: 기존 코드와의 호환성을 위한 레거시 메서드

---

## 📚 사용된 라이브러리

### **데이터베이스 & 비동기**
- **aiomysql**: 비동기 MySQL 드라이버
- **asyncio**: 비동기 프로그래밍 지원
- **typing**: 타입 힌트 및 타입 안전성

### **설정 & 검증**
- **pydantic**: 데이터 검증 및 설정 모델
- **service.core.logger.Logger**: 구조화된 로깅 시스템

---

## 🪝 핵심 클래스 및 메서드

### **DatabaseService - 메인 서비스 클래스**

```python
class DatabaseService:
    """샤딩을 지원하는 데이터베이스 서비스"""
    
    def __init__(self, global_config: DatabaseConfig):
        self.global_config = global_config
        self.global_client: Optional[MySQLClient] = None
        self.shard_clients: Dict[int, MySQLClient] = {}
        self.shard_configs: Dict[int, DatabaseConfig] = {}
    
    async def init_service(self):
        """데이터베이스 서비스 초기화"""
        # 글로벌 DB 및 샤드 DB 연결 초기화
    
    async def close_service(self):
        """서비스 종료 및 연결 정리"""
        # 모든 DB 연결 풀 종료
```

**동작 방식**:
- 글로벌 DB에서 샤드 설정 정보 로드
- 각 샤드별 MySQL 클라이언트 생성 및 연결 풀 초기화
- 세션 기반 자동 라우팅으로 적절한 DB 선택

### **MySQLClient - MySQL 클라이언트**

```python
class MySQLClient:
    """MySQL 연결 풀 관리 및 쿼리 실행"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool: Optional[Pool] = None
    
    async def init_pool(self):
        """연결 풀 초기화"""
        # aiomysql을 통한 연결 풀 생성
    
    async def execute_stored_procedure(self, procedure_name: str, params: Tuple = ()):
        """스토어드 프로시저 실행"""
        # 연결 풀에서 커넥션 획득하여 프로시저 호출
```

**동작 방식**:
- aiomysql을 통한 비동기 연결 풀 관리
- 연결 실패 시 자동 재연결 및 재시도
- DictCursor를 통한 딕셔너리 형태 결과 반환

### **DatabaseConfig - 설정 모델**

```python
class DatabaseConfig(BaseModel):
    """데이터베이스 연결 설정"""
    type: str
    host: str
    port: int
    database: str
    user: str
    password: str
    charset: str = "utf8mb4"
    pool_size: int = 10
    max_overflow: int = 20
```

---

## 🔄 API 연동 방식

### **서비스 초기화**
```python
# main.py에서 서비스 초기화
from service.db.database_service import DatabaseService

database_service = DatabaseService(app_config.databaseConfig)
await database_service.init_service()
```

### **글로벌 DB 사용**
```python
# 글로벌 DB 전용 메서드
result = await database_service.call_global_procedure("get_user_info", (user_id,))
result = await database_service.execute_global_query("SELECT * FROM users WHERE id = %s", (user_id,))
```

### **샤드 DB 사용**
```python
# 특정 샤드 DB 사용
result = await database_service.call_shard_procedure(shard_id, "get_portfolio", (user_id,))
result = await database_service.execute_shard_query(shard_id, "SELECT * FROM portfolios WHERE user_id = %s", (user_id,))
```

### **세션 기반 자동 라우팅**
```python
# 세션 정보를 통한 자동 DB 선택
result = await database_service.call_procedure_by_session(client_session, "get_user_data", (user_id,))
result = await database_service.execute_query_by_session(client_session, "SELECT * FROM user_data WHERE id = %s", (user_id,))
```

---

## 📊 데이터베이스 서비스 전체 흐름

### **초기화 단계**
1. **글로벌 DB 연결**: 기본 설정으로 글로벌 DB 연결 풀 생성
2. **샤드 설정 로드**: `table_shard_config` 테이블에서 활성 샤드 정보 조회
3. **샤드 연결 초기화**: 각 샤드별로 MySQL 클라이언트 및 연결 풀 생성
4. **서비스 준비 완료**: 모든 DB 연결이 준비된 상태로 서비스 시작

### **요청 처리 단계**
1. **세션 분석**: 클라이언트 세션에서 `shard_id` 정보 추출
2. **DB 선택**: 세션 정보에 따라 글로벌 DB 또는 적절한 샤드 DB 선택
3. **쿼리 실행**: 선택된 DB에서 스토어드 프로시저 또는 SQL 쿼리 실행
4. **결과 반환**: aiomysql.DictCursor를 통한 딕셔너리 형태 결과 반환

### **연결 관리 단계**
1. **연결 풀 관리**: aiomysql을 통한 비동기 연결 풀 유지
2. **자동 재연결**: 연결 실패 시 자동 재연결 및 재시도
3. **리소스 정리**: 서비스 종료 시 모든 연결 풀 정리

---

## 🚀 고급 기능 심층 분석: 샤딩 시스템 아키텍처

### **샤딩 전략**
- **수평 샤딩**: 사용자별 데이터를 여러 샤드에 분산 저장
- **세션 기반 라우팅**: 로그인 시 할당된 `shard_id`를 통한 자동 라우팅
- **동적 샤드 관리**: `table_shard_config` 테이블을 통한 샤드 추가/제거/상태 관리

### **샤드 설정 테이블 구조**
```sql
CREATE TABLE table_shard_config (
    shard_id INT PRIMARY KEY,
    host VARCHAR(255),
    port INT,
    database_name VARCHAR(255),
    username VARCHAR(255),
    password VARCHAR(255),
    status ENUM('active', 'inactive', 'maintenance')
);
```

### **샤드 라우팅 로직**
```python
def get_client_by_session(self, client_session) -> MySQLClient:
    """세션 정보를 기반으로 적절한 DB 클라이언트 반환"""
    if not client_session or not hasattr(client_session, 'session') or not client_session.session:
        # 세션이 없으면 글로벌 DB 사용 (로그인, 회원가입 등)
        return self.get_global_client()
    
    shard_id = getattr(client_session.session, 'shard_id', None)
    if shard_id and shard_id in self.shard_clients:
        return self.shard_clients[shard_id]
    else:
        # 샤드 정보가 없거나 해당 샤드가 없으면 글로벌 DB 사용
        return self.get_global_client()
```

### **샤드 확장성**
- **샤드 추가**: 새로운 샤드 정보를 `table_shard_config`에 추가하면 자동으로 연결
- **샤드 제거**: 샤드 상태를 'inactive'로 변경하면 연결 해제
- **샤드 유지보수**: 상태를 'maintenance'로 변경하여 일시적 사용 중단

---

## 🔧 사용 예제

### **기본 데이터베이스 서비스 사용**
```python
from service.db.database_service import DatabaseService
from service.db.database_config import DatabaseConfig

# 설정 생성
config = DatabaseConfig(
    type="mysql",
    host="localhost",
    port=3306,
    database="finance_global",
    user="user",
    password="password"
)

# 서비스 초기화
db_service = DatabaseService(config)
await db_service.init_service()

# 글로벌 DB 사용
users = await db_service.execute_global_query("SELECT * FROM users")

# 서비스 종료
await db_service.close_service()
```

### **샤드 DB 사용**
```python
# 특정 샤드에서 포트폴리오 조회
portfolio = await db_service.call_shard_procedure(
    shard_id=1, 
    procedure_name="get_user_portfolio", 
    params=(user_id,)
)

# 샤드 DB에 직접 쿼리 실행
trades = await db_service.execute_shard_query(
    shard_id=1,
    query="SELECT * FROM trades WHERE user_id = %s ORDER BY trade_date DESC",
    params=(user_id,)
)
```

### **세션 기반 자동 라우팅**
```python
# 클라이언트 세션을 통한 자동 DB 선택
user_data = await db_service.call_procedure_by_session(
    client_session,
    "get_user_profile",
    (user_id,)
)

# 세션에 따라 적절한 샤드 DB 자동 선택
portfolio_data = await db_service.execute_query_by_session(
    client_session,
    "SELECT * FROM portfolios WHERE user_id = %s",
    (user_id,)
)
```

### **샤드 관리**
```python
# 활성 샤드 ID 목록 조회
active_shards = await db_service.get_active_shard_ids()

# 특정 샤드 상태 확인
shard_client = db_service.get_shard_client(shard_id=1)
if shard_client:
    print(f"Shard {shard_id} is available")
```

---

## ⚙️ 설정

### **데이터베이스 연결 설정**
```python
# database_config.py
class DatabaseConfig(BaseModel):
    type: str = "mysql"           # 데이터베이스 타입
    host: str = "localhost"       # 호스트 주소
    port: int = 3306             # 포트 번호
    database: str                 # 데이터베이스 이름
    user: str                     # 사용자명
    password: str                 # 비밀번호
    charset: str = "utf8mb4"     # 문자셋
    pool_size: int = 10          # 기본 연결 풀 크기
    max_overflow: int = 20       # 최대 오버플로우 연결 수
```

### **연결 풀 설정**
```python
# mysql_client.py
self.pool = await aiomysql.create_pool(
    host=self.config.host,
    port=self.config.port,
    user=self.config.user,
    password=self.config.password,
    db=self.config.database,
    charset=self.config.charset,
    minsize=1,                    # 최소 연결 수
    maxsize=self.config.pool_size, # 최대 연결 수
    autocommit=True               # 자동 커밋
)
```

### **샤드 설정 테이블**
```sql
-- 글로벌 DB에 샤드 설정 테이블 생성
CREATE TABLE table_shard_config (
    shard_id INT PRIMARY KEY,
    host VARCHAR(255) NOT NULL,
    port INT NOT NULL DEFAULT 3306,
    database_name VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    status ENUM('active', 'inactive', 'maintenance') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 샤드 정보 삽입 예시
INSERT INTO table_shard_config (shard_id, host, port, database_name, username, password, status)
VALUES 
(1, 'shard1.example.com', 3306, 'finance_shard_1', 'shard_user', 'shard_password', 'active'),
(2, 'shard2.example.com', 3306, 'finance_shard_2', 'shard_user', 'shard_password', 'active');
```

---

## 🔗 연관 폴더

### **사용하는 Service**
- **service.core.logger.Logger**: 로깅 시스템
- **service.db.database_config.DatabaseConfig**: 설정 모델
- **service.db.mysql_client.MySQLClient**: MySQL 클라이언트

### **사용하는 Template**
- **template.admin.admin_template_impl**: 관리자 템플릿 (DatabaseService 직접 사용)
- **template.base.template_config**: 기본 템플릿 설정 (DatabaseConfig 사용)
- **template.account.account_template_impl**: 계정 관리 (ServiceContainer를 통한 DatabaseService 사용)
- **template.profile.profile_template_impl**: 프로필 관리 (ServiceContainer를 통한 DatabaseService 사용)
- **template.market.market_template_impl**: 시장 데이터 (ServiceContainer를 통한 DatabaseService 사용)
- **template.chat.chat_template_impl**: 채팅 시스템 (ServiceContainer를 통한 DatabaseService 사용)
- **template.portfolio.portfolio_template_impl**: 포트폴리오 관리 (ServiceContainer를 통한 DatabaseService 사용)
- **template.dashboard.dashboard_template_impl**: 대시보드 (ServiceContainer를 통한 DatabaseService 사용)
- **template.notification.notification_template_impl**: 알림 시스템 (ServiceContainer를 통한 DatabaseService 사용)
- **template.autotrade.autotrade_template_impl**: 자동 거래 (ServiceContainer를 통한 DatabaseService 사용)
- **template.tutorial.tutorial_template_impl**: 튜토리얼 (ServiceContainer를 통한 DatabaseService 사용)

### **외부 의존성**
- **aiomysql**: 비동기 MySQL 드라이버
- **asyncio**: 비동기 프로그래밍
- **pydantic**: 데이터 검증
- **typing**: 타입 힌트

---

## 🌐 외부 시스템

### **MySQL 데이터베이스**
- **글로벌 DB**: 사용자 인증, 설정 정보, 샤드 설정 등 공통 데이터 저장
- **샤드 DB**: 사용자별 포트폴리오, 거래 내역, 개인 데이터 저장
- **연결 풀**: aiomysql을 통한 비동기 연결 풀 관리


### **샤딩 시스템**
- **수평 샤딩**: 사용자별 데이터를 여러 물리적 DB에 분산
- **동적 샤드 관리**: 런타임에 샤드 추가/제거/상태 변경 가능
- **자동 라우팅**: 세션 정보를 통한 적절한 샤드 자동 선택
- **확장성**: 트래픽 증가에 따른 샤드 추가로 성능 향상

### **성능 최적화**
- **비동기 처리**: aiomysql을 통한 비동기 쿼리 실행
- **연결 풀**: 데이터베이스 연결 재사용으로 오버헤드 감소
- **자동 재연결**: 연결 실패 시 자동 재연결 및 재시도
