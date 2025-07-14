# Base Server Architecture Documentation - Part 3: 데이터베이스 시스템 & 샤딩

## 목차
1. [데이터베이스 아키텍처 개요](#데이터베이스-아키텍처-개요)
2. [글로벌 DB 시스템](#글로벌-db-시스템)
3. [샤드 DB 시스템](#샤드-db-시스템)
4. [데이터베이스 라우팅](#데이터베이스-라우팅)
5. [트랜잭션 관리](#트랜잭션-관리)
6. [연결 풀 관리](#연결-풀-관리)
7. [오류 처리 및 복구](#오류-처리-및-복구)

---

## 데이터베이스 아키텍처 개요

### 전체 아키텍처

Base Server는 **글로벌 DB + 샤드 DB** 구조로 설계된 수평 분할 데이터베이스 시스템을 사용합니다.

```
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                       │
├─────────────────────────────────────────────────────────────┤
│                    DatabaseService                          │
│  ┌─────────────────┐  ┌──────────────────────────────────┐  │
│  │   Global DB     │  │        Shard DBs                │  │
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

### 핵심 설계 원칙

1. **데이터 분산**: 사용자별 데이터를 샤드에 분산 저장
2. **자동 라우팅**: 세션 정보 기반 자동 DB 라우팅
3. **연결 관리**: 각 DB별 독립적인 연결 풀 관리
4. **오류 복구**: 연결 실패 시 자동 재연결 및 재시도
5. **트랜잭션 지원**: 글로벌 트랜잭션 및 샤드별 트랜잭션

---

## 글로벌 DB 시스템

### 글로벌 DB 역할

글로벌 DB(`finance_global`)는 시스템 전체의 메타데이터와 인증 정보를 관리합니다.

#### 주요 테이블 구조

**1. 계정 관리: `table_accountid`**
```sql
CREATE TABLE `table_accountid` (
  `idx` bigint unsigned NOT NULL AUTO_INCREMENT,
  `platform_type` tinyint NOT NULL DEFAULT 1,
  `account_id` varchar(100) NOT NULL,
  `account_db_key` bigint unsigned NOT NULL DEFAULT '0',
  `account_status` varchar(15) NOT NULL DEFAULT 'Normal',
  `password_hash` varchar(255) NOT NULL,
  `nickname` varchar(50) NOT NULL,
  `email` varchar(100),
  `account_level` int DEFAULT 1,
  `login_count` int DEFAULT 0,      -- 로그인 횟수 추가
  `login_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`idx`),
  UNIQUE KEY `ix_accountid_platform_accountid` (`platform_type`,`account_id`),
  KEY `ix_accountid_accountdbkey` (`account_db_key`)
) ENGINE=InnoDB;
```

**필드 설명:**
- `account_db_key`: 사용자 고유 식별자 (샤드 라우팅에 사용)
- `platform_type`: 플랫폼 구분 (1=웹, 2=모바일 등)
- `account_status`: 계정 상태 (Normal, Blocked, Suspended)
- `account_level`: 권한 레벨 (1=일반, 2=운영자, 3=개발자, 4=관리자)
- `login_count`: 첫 로그인 감지용 카운터

**2. 샤드 설정: `table_shard_config`**
```sql
CREATE TABLE `table_shard_config` (
  `shard_id` int NOT NULL,
  `shard_name` varchar(50) NOT NULL,
  `host` varchar(255) NOT NULL,
  `port` int NOT NULL DEFAULT 3306,
  `database_name` varchar(100) NOT NULL,
  `username` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `max_connections` int DEFAULT 100,
  `status` enum('active','maintenance','disabled') DEFAULT 'active',
  PRIMARY KEY (`shard_id`),
  INDEX `idx_status` (`status`)
) ENGINE=InnoDB;
```

**현재 샤드 설정:**
```sql
INSERT INTO `table_shard_config` VALUES 
(1, 'finance_shard_1', 'localhost', 3306, 'finance_shard_1', 'root', 'Wkdwkrdhkd91!', 100, 'active'),
(2, 'finance_shard_2', 'localhost', 3306, 'finance_shard_2', 'root', 'Wkdwkrdhkd91!', 100, 'active');
```

**3. 사용자 샤드 매핑: `table_user_shard_mapping`**
```sql
CREATE TABLE `table_user_shard_mapping` (
  `account_db_key` bigint unsigned NOT NULL,
  `shard_id` int NOT NULL,
  `assigned_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`account_db_key`),
  FOREIGN KEY (`account_db_key`) REFERENCES `table_accountid`(`account_db_key`) ON DELETE CASCADE,
  INDEX `idx_shard_id` (`shard_id`)
) ENGINE=InnoDB;
```

**4. 샤드 통계: `table_shard_stats`**
```sql
CREATE TABLE `table_shard_stats` (
  `shard_id` int NOT NULL,
  `user_count` int DEFAULT 0,
  `active_users` int DEFAULT 0,
  `last_updated` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`shard_id`)
) ENGINE=InnoDB;
```

### 글로벌 DB 운영 패턴

#### 1. 계정 생성 플로우
```python
async def create_account_flow(account_id: str, password: str, nickname: str):
    """계정 생성 및 샤드 할당 플로우"""
    global_client = database_service.get_global_client()
    
    # 1. 계정 생성
    account_db_key = await global_client.execute_stored_procedure(
        'sp_create_account', 
        (account_id, password_hash, nickname, email)
    )
    
    # 2. 샤드 할당 (라운드 로빈 또는 부하 기반)
    shard_id = await assign_shard_for_user(account_db_key)
    
    # 3. 샤드 매핑 저장
    await global_client.execute_query(
        "INSERT INTO table_user_shard_mapping (account_db_key, shard_id) VALUES (%s, %s)",
        (account_db_key, shard_id)
    )
    
    return account_db_key, shard_id
```

#### 2. 사용자 인증 및 샤드 라우팅
```python
async def authenticate_user(account_id: str, password: str):
    """사용자 인증 및 샤드 정보 조회"""
    # 글로벌 DB에서 계정 정보 조회
    query = """
    SELECT a.account_db_key, a.account_level, a.account_status, 
           m.shard_id, a.login_count
    FROM table_accountid a
    LEFT JOIN table_user_shard_mapping m ON a.account_db_key = m.account_db_key
    WHERE a.account_id = %s AND a.password_hash = %s
    """
    
    result = await database_service.execute_global_query(query, (account_id, password_hash))
    
    if result:
        account_data = result[0]
        # 로그인 카운트 증가
        await increment_login_count(account_data['account_db_key'])
        return account_data
    
    return None
```

---

## 샤드 DB 시스템

### 샤드 DB 구조

각 샤드 DB(`finance_shard_1`, `finance_shard_2`)는 사용자별 비즈니스 데이터를 저장합니다.

#### 주요 테이블 구조

**1. 사용자 계좌: `table_user_accounts`**
```sql
CREATE TABLE `table_user_accounts` (
  `account_db_key` bigint unsigned NOT NULL,
  `account_number` varchar(20) NOT NULL,
  `balance` decimal(15,2) DEFAULT 0.00,
  `account_type` enum('checking','savings','investment') DEFAULT 'checking',
  `account_status` enum('active','suspended','closed') DEFAULT 'active',
  `currency_code` varchar(3) DEFAULT 'USD',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`account_db_key`),
  UNIQUE KEY `uk_account_number` (`account_number`)
) ENGINE=InnoDB;
```

**2. 거래 내역: `table_transactions`**
```sql
CREATE TABLE `table_transactions` (
  `transaction_id` varchar(32) NOT NULL,
  `account_db_key` bigint unsigned NOT NULL,
  `account_number` varchar(20),
  `amount` decimal(15,2) NOT NULL,
  `transaction_type` enum('deposit','withdrawal','transfer_in','transfer_out','fee') NOT NULL,
  `description` text,
  `reference_id` varchar(50),
  `status` enum('pending','completed','failed','cancelled') DEFAULT 'pending',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`transaction_id`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB;
```

**3. 포트폴리오: `table_user_portfolios`**
```sql
CREATE TABLE `table_user_portfolios` (
  `portfolio_id` bigint NOT NULL AUTO_INCREMENT,
  `account_db_key` bigint unsigned NOT NULL,
  `asset_code` varchar(10) NOT NULL,
  `quantity` decimal(15,6) DEFAULT 0.000000,
  `average_cost` decimal(15,2) DEFAULT 0.00,
  `current_value` decimal(15,2) DEFAULT 0.00,
  `last_updated` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`portfolio_id`),
  UNIQUE KEY `uk_user_asset` (`account_db_key`,`asset_code`)
) ENGINE=InnoDB;
```

**4. 아웃박스 이벤트: `outbox_events`**
```sql
CREATE TABLE `outbox_events` (
  `id` varchar(36) NOT NULL,
  `event_type` varchar(100) NOT NULL,
  `aggregate_id` varchar(100) NOT NULL,
  `aggregate_type` varchar(50) NOT NULL,
  `event_data` json NOT NULL,
  `status` enum('pending','published','failed','retry') DEFAULT 'pending',
  `retry_count` int DEFAULT 0,
  `max_retries` int DEFAULT 3,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `published_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_status_created` (`status`, `created_at`)
) ENGINE=InnoDB;
```

### 샤드별 스토어드 프로시저

#### 계좌 생성 프로시저
```sql
DELIMITER ;;
CREATE PROCEDURE `fp_create_account`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_account_type VARCHAR(20)
)
BEGIN
    DECLARE v_account_number VARCHAR(20);
    DECLARE v_result VARCHAR(20) DEFAULT 'FAILED';
    DECLARE ProcParam VARCHAR(4000);
    
    -- 에러 핸들러
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_account_type);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, 
                                   @ErrorNo = MYSQL_ERRNO, 
                                   @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_create_account', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 계좌번호 생성 (shard_id + timestamp + account_db_key 조합)
    SET v_account_number = CONCAT('1', UNIX_TIMESTAMP(), LPAD(p_account_db_key % 10000, 4, '0'));
    
    INSERT INTO table_user_accounts (account_db_key, account_number, account_type)
    VALUES (p_account_db_key, v_account_number, p_account_type);
    
    IF ROW_COUNT() > 0 THEN
        SET v_result = 'SUCCESS';
    END IF;
    
    SELECT v_result as result, v_account_number as account_number;
END ;;
DELIMITER ;
```

#### 계좌 정보 조회 프로시저
```sql
DELIMITER ;;
CREATE PROCEDURE `fp_get_account_info`(
    IN p_account_db_key BIGINT UNSIGNED
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, 
                                   @ErrorNo = MYSQL_ERRNO, 
                                   @ErrorMessage = MESSAGE_TEXT;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_get_account_info', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    SELECT 
        account_number,
        balance,
        account_type,
        account_status,
        currency_code,
        created_at,
        updated_at
    FROM table_user_accounts 
    WHERE account_db_key = p_account_db_key AND account_status = 'active';
END ;;
DELIMITER ;
```

---

## 데이터베이스 라우팅

### DatabaseService 구현 분석

```python
class DatabaseService:
    def __init__(self, global_config: DatabaseConfig):
        self.global_config = global_config
        self.global_client: Optional[MySQLClient] = None
        self.shard_clients: Dict[int, MySQLClient] = {}  # shard_id -> MySQLClient
        self.shard_configs: Dict[int, DatabaseConfig] = {}  # shard_id -> DatabaseConfig
```

### 초기화 프로세스

#### 1. 서비스 초기화
```python
async def init_service(self):
    """데이터베이스 서비스 초기화"""
    # 1. 글로벌 DB 초기화
    if self.global_config.type == "mysql":
        self.global_client = MySQLClient(self.global_config)
        await self.global_client.init_pool()
        Logger.info("Global database initialized")
    
    # 2. 샤드 설정 로드
    await self.load_shard_configs()
    
    # 3. 샤드 연결 초기화
    await self.init_shard_connections()
```

#### 2. 샤드 설정 동적 로드
```python
async def load_shard_configs(self):
    """글로벌 DB에서 샤드 설정 정보 로드"""
    try:
        query = """
        SELECT shard_id, host, port, database_name, username, password, status
        FROM table_shard_config 
        WHERE status = 'active'
        ORDER BY shard_id
        """
        shard_rows = await self.global_client.execute_query(query)
        
        for row in shard_rows:
            shard_id = row['shard_id']
            shard_config = DatabaseConfig(
                type="mysql",
                host=row['host'],
                port=row['port'],
                database=row['database_name'],
                user=row['username'],
                password=row['password']
            )
            self.shard_configs[shard_id] = shard_config
            Logger.info(f"Loaded shard config for shard_id: {shard_id}")
            
    except Exception as e:
        Logger.error(f"Failed to load shard configs: {e}")
        # 샤드 설정이 없어도 글로벌 DB는 사용 가능하도록
```

### 자동 라우팅 메커니즘

#### 세션 기반 라우팅
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

#### 자동 라우팅 API
```python
async def call_procedure_by_session(self, client_session, procedure_name: str, params: Tuple = ()):
    """세션 정보를 기반으로 적절한 DB에 스토어드 프로시저 호출"""
    client = self.get_client_by_session(client_session)
    return await client.execute_stored_procedure(procedure_name, params)

async def execute_query_by_session(self, client_session, query: str, params: Tuple = ()):
    """세션 정보를 기반으로 적절한 DB에 쿼리 실행"""
    client = self.get_client_by_session(client_session)
    return await client.execute_query(query, params)
```

### 라우팅 시나리오

#### 1. 익명 사용자 (로그인, 회원가입)
```python
# client_session이 None이므로 글로벌 DB로 라우팅
result = await database_service.call_procedure_by_session(
    None,  # 세션 없음
    'sp_login_user',
    (account_id, password_hash)
)
```

#### 2. 인증된 사용자 (포트폴리오 조회)
```python
# client_session.session.shard_id에 따라 적절한 샤드로 라우팅
portfolios = await database_service.call_procedure_by_session(
    client_session,  # shard_id=1
    'fp_get_user_portfolios',
    (account_db_key,)
)
```

#### 3. 명시적 샤드 호출
```python
# 특정 샤드를 명시적으로 호출
result = await database_service.call_shard_procedure(
    shard_id=1,
    procedure_name='fp_create_account',
    params=(account_db_key, 'checking')
)
```

---

## 트랜잭션 관리

### 트랜잭션 컨텍스트 매니저

```python
async def get_transaction(self):
    """트랜잭션 컨텍스트 매니저 반환 (글로벌 DB)"""
    class TransactionContext:
        def __init__(self, client: MySQLClient):
            self.client = client
            self.connection = None
        
        async def __aenter__(self):
            self.connection = await self.client.get_connection()
            # MySQL 연결을 수동 커밋 모드로 설정
            await self.connection.autocommit(False)
            return self.connection
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            try:
                if exc_type is None:
                    await self.connection.commit()
                else:
                    await self.connection.rollback()
            finally:
                # 커넥션을 풀로 반환
                await self.connection.autocommit(True)  # 원래 상태로 복구
                self.connection.close()
    
    return TransactionContext(self.global_client)
```

### 트랜잭션 사용 예제

#### 아웃박스 패턴과 트랜잭션
```python
async def create_account_with_event(account_data: Dict[str, Any]):
    """계정 생성과 이벤트 발행을 트랜잭션으로 처리"""
    
    async with database_service.get_transaction() as transaction:
        # 1. 비즈니스 로직 실행
        account_id = await create_account(account_data)
        
        # 2. 아웃박스에 이벤트 기록 (같은 트랜잭션)
        await queue_service.publish_event_with_transaction(
            event_type="account.created",
            aggregate_id=account_id,
            aggregate_type="account",
            event_data={
                "account_id": account_id,
                "user_id": account_data["user_id"],
                "created_at": datetime.now().isoformat()
            }
        )
        
        # 3. 트랜잭션 커밋 시 둘 다 성공, 롤백 시 둘 다 실패
```

---

## 연결 풀 관리

### MySQLClient 구현 분석

```python
class MySQLClient:
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool: Optional[Pool] = None
    
    async def init_pool(self):
        """연결 풀 초기화"""
        if self.pool is None:
            self.pool = await aiomysql.create_pool(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                db=self.config.database,
                charset=self.config.charset,
                minsize=1,
                maxsize=self.config.pool_size,  # 기본값: 10
                autocommit=True
            )
```

### 연결 풀 설정

#### DatabaseConfig 구조
```python
@dataclass
class DatabaseConfig:
    type: str = "mysql"
    host: str = "localhost"
    port: int = 3306
    database: str = ""
    user: str = ""
    password: str = ""
    charset: str = "utf8mb4"
    pool_size: int = 10          # 최대 연결 수
    connect_timeout: int = 30    # 연결 타임아웃
    read_timeout: int = 30       # 읽기 타임아웃
    write_timeout: int = 30      # 쓰기 타임아웃
```

### 연결 관리 전략

#### 1. 자동 연결 확인
```python
async def _ensure_connection(self):
    """연결 풀이 존재하고 유효한지 확인"""
    if not self.pool or self.pool.closed:
        await self.init_pool()
```

#### 2. 자동 재연결
```python
async def _reconnect(self):
    """연결 풀 재생성"""
    if self.pool:
        try:
            self.pool.close()
            await self.pool.wait_closed()
        except:
            pass
    self.pool = None
    await self.init_pool()
```

#### 3. 연결 오류 감지
```python
def _is_connection_error(self, exception) -> bool:
    """연결 관련 에러인지 확인"""
    error_messages = [
        "MySQL server has gone away",
        "Lost connection to MySQL server",
        "Connection reset by peer",
        "Broken pipe",
        "Can't connect to MySQL server"
    ]
    error_str = str(exception).lower()
    return any(msg.lower() in error_str for msg in error_messages)
```

---

## 오류 처리 및 복구

### 자동 재시도 메커니즘

#### 쿼리 실행 시 재시도
```python
async def execute_query(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
    """SELECT 쿼리 실행 및 자동 재시도"""
    await self._ensure_connection()
    
    try:
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, params)
                results = await cursor.fetchall()
                return results if results else []
    except Exception as e:
        # 연결 오류 시 재연결 후 재시도
        if self._is_connection_error(e):
            await self._reconnect()
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(query, params)
                    results = await cursor.fetchall()
                    return results if results else []
        else:
            raise
```

### 오류 로깅 시스템

#### 스토어드 프로시저 오류 로깅
```sql
DECLARE EXIT HANDLER FOR SQLEXCEPTION
BEGIN
    SET ProcParam = CONCAT(p_account_db_key, ',', p_account_type);
    GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, 
                               @ErrorNo = MYSQL_ERRNO, 
                               @ErrorMessage = MESSAGE_TEXT;
    ROLLBACK;
    INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
        VALUES ('fp_create_account', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
    RESIGNAL;
END;
```

#### 오류 로그 테이블 구조
```sql
CREATE TABLE `table_errorlog` (
  `idx` int NOT NULL AUTO_INCREMENT,
  `procedure_name` varchar(45) DEFAULT NULL,
  `error_state` varchar(10) DEFAULT NULL,
  `error_no` varchar(10) DEFAULT NULL,
  `error_message` varchar(128) DEFAULT NULL,
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `param` varchar(4000) NOT NULL,
  PRIMARY KEY (`idx`)
) ENGINE=InnoDB;
```

### 서비스 종료 처리

```python
async def close_service(self):
    """데이터베이스 서비스 종료"""
    # 글로벌 DB 종료
    if self.global_client:
        await self.global_client.close_pool()
        Logger.info("Global database closed")
    
    # 모든 샤드 DB 종료
    for shard_id, shard_client in self.shard_clients.items():
        await shard_client.close_pool()
        Logger.info(f"Shard {shard_id} database closed")
    
    self.shard_clients.clear()
    self.shard_configs.clear()
```

---

## 샤딩 운영 시나리오

### 사용자 분산 전략

#### 1. 계정 생성 시 샤드 할당
```python
async def assign_shard_for_user(account_db_key: int) -> int:
    """사용자를 적절한 샤드에 할당"""
    # 방법 1: 단순 모듈로 방식
    return (account_db_key % 2) + 1
    
    # 방법 2: 샤드별 부하 기반 할당
    shard_stats = await get_shard_stats()
    return min(shard_stats, key=lambda x: x['user_count'])['shard_id']
```

#### 2. 크로스 샤드 쿼리 지원
```python
async def get_all_user_stats() -> List[Dict]:
    """모든 샤드에서 사용자 통계 수집"""
    all_stats = []
    
    for shard_id in await database_service.get_active_shard_ids():
        try:
            stats = await database_service.call_shard_procedure(
                shard_id, 'sp_get_shard_user_stats', ()
            )
            all_stats.extend(stats)
        except Exception as e:
            Logger.error(f"Failed to get stats from shard {shard_id}: {e}")
    
    return all_stats
```

### 샤드 운영 모니터링

#### 샤드 상태 체크
```python
async def check_shard_health():
    """샤드 상태 체크"""
    health_status = {}
    
    for shard_id, client in database_service.shard_clients.items():
        try:
            # 간단한 쿼리로 연결 상태 확인
            await client.execute_query("SELECT 1")
            health_status[shard_id] = "healthy"
        except Exception as e:
            health_status[shard_id] = f"unhealthy: {e}"
            Logger.error(f"Shard {shard_id} health check failed: {e}")
    
    return health_status
```

---

## 보안 고려사항

### 현재 구현된 보안 기능

1. **연결 문자열 보안**
   - 데이터베이스 비밀번호 하드코딩 (⚠️ 보안 취약)
   - 환경 변수 또는 암호화된 설정 파일 사용 권장

2. **SQL 인젝션 방지**
   - 파라미터화된 쿼리 사용
   - 스토어드 프로시저 활용

3. **연결 관리**
   - 연결 풀을 통한 연결 수 제한
   - 자동 연결 종료 및 정리

### 추후 보완 필요 사항

1. **접근 제어**
   ```python
   # TODO: 역할 기반 접근 제어 (RBAC)
   class DatabaseAccessControl:
       def check_access_permission(self, user_role: str, operation: str, table: str) -> bool:
           # 사용자 역할에 따른 DB 접근 권한 체크
           pass
   ```

2. **암호화**
   ```python
   # TODO: 민감 데이터 암호화
   class DataEncryption:
       def encrypt_sensitive_data(self, data: str) -> str:
           # 개인정보, 금융 데이터 암호화
           pass
   ```

3. **감사 로그**
   ```python
   # TODO: 데이터베이스 접근 감사
   class DatabaseAuditLog:
       def log_database_access(self, user_id: str, operation: str, table: str):
           # 모든 DB 접근 기록
           pass
   ```

---

이것으로 Part 3가 완료되었습니다. Part 4에서는 템플릿 시스템과 라우팅에 대해 상세히 다루겠습니다.