# 칼만 필터 데이터베이스 설정 가이드

## 📋 개요

칼만 필터의 Redis + SQL 하이브리드 상태 관리를 위한 데이터베이스 설정입니다.

## 🗄️ 데이터베이스 스크립트 실행

### 1. MySQL 접속
```bash
mysql -u [username] -p [database_name]
```

### 2. 스크립트 실행
```bash
# 방법 1: MySQL 클라이언트에서 직접 실행
mysql -u [username] -p [database_name] < kalman_tables_extension.sql

# 방법 2: MySQL 클라이언트 내에서 실행
source /path/to/kalman_tables_extension.sql;
```

### 3. 실행 확인
```sql
-- 테이블 생성 확인
SHOW TABLES LIKE 'table_kalman_history';

-- 프로시저 생성 확인
SHOW PROCEDURE STATUS LIKE 'fp_kalman%';
```

## 🏗️ 생성되는 구조

### 테이블
- `table_kalman_history`: 칼만 필터 이력 데이터 (분석용)

### 프로시저
- `fp_kalman_history_insert`: 이력 저장
- `fp_kalman_latest_state_get`: 최신 상태 조회 (Redis 복원용)
- `fp_kalman_history_get`: 이력 조회 (분석용)

## 🔄 Redis 키 구조

```
kalman:{ticker}:{account_db_key}:x          # 상태 벡터
kalman:{ticker}:{account_db_key}:P          # 공분산 행렬
kalman:{ticker}:{account_db_key}:step_count # 스텝 카운트
kalman:{ticker}:{account_db_key}:last_update # 마지막 업데이트
kalman:{ticker}:{account_db_key}:performance # 성능 지표
```

## ⚙️ 동작 플로우

1. **매 요청 시**: Redis에 상태 저장
2. **주기적**: SQL에 이력 저장 (step_count % 10 == 0)
3. **서버 재시작 시**: SQL → Redis 복원

## 🧪 테스트

### 1. 이력 저장 테스트
```sql
CALL fp_kalman_history_insert(
    'AAPL', 123, NOW(), 
    '[0.1, 0.2, 0.3, 0.4, 0.5]',
    '[[1,0,0,0,0],[0,1,0,0,0],[0,0,1,0,0],[0,0,0,1,0],[0,0,0,0,1]]',
    10, 'Long', '{"price": 150.0}', '{"status": "stable"}'
);
```

### 2. 최신 상태 조회 테스트
```sql
CALL fp_kalman_latest_state_get('AAPL', 123);
```

### 3. 이력 조회 테스트
```sql
CALL fp_kalman_history_get('AAPL', 123, '2024-01-01', '2024-12-31', 100, 0);
```

## 🔧 문제 해결

### 1. 권한 오류
```sql
-- 사용자 권한 확인
SHOW GRANTS FOR 'username'@'host';

-- 필요한 권한 부여
GRANT ALL PRIVILEGES ON finance_shard_1.* TO 'username'@'host';
GRANT ALL PRIVILEGES ON finance_shard_2.* TO 'username'@'host';
```

### 2. 프로시저 오류
```sql
-- 프로시저 삭제 후 재생성
DROP PROCEDURE IF EXISTS fp_kalman_history_insert;
-- 스크립트 재실행
```

### 3. JSON 컬럼 오류
```sql
-- MySQL 버전 확인 (5.7+ 필요)
SELECT VERSION();
```

## 📊 모니터링

### 1. 이력 데이터 확인
```sql
SELECT COUNT(*) as total_records FROM table_kalman_history;
SELECT ticker, COUNT(*) as records FROM table_kalman_history GROUP BY ticker;
```

### 2. 최근 활동 확인
```sql
SELECT ticker, MAX(created_at) as last_activity 
FROM table_kalman_history 
GROUP BY ticker 
ORDER BY last_activity DESC;
```

## 🚀 다음 단계

1. 데이터베이스 스크립트 실행 완료
2. KalmanStateManager 클래스 사용
3. KalmanRegimeFilterTool에서 하이브리드 상태 관리 활성화
4. Redis 연결 확인
5. 테스트 실행 