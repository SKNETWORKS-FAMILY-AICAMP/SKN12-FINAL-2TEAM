-- =====================================
-- 칼만 필터 이력 관리 테이블 확장 스크립트
-- Redis + SQL 하이브리드 아키텍처용
-- 적용 대상: finance_shard_1, finance_shard_2
-- =====================================

-- =====================================
-- Shard DB 1에 칼만 필터 테이블 추가
-- =====================================
USE finance_shard_1;

-- 칼만 필터 이력 테이블 (분석용)
CREATE TABLE IF NOT EXISTS `table_kalman_history` (
  `idx` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '이력 고유 인덱스',
  `ticker` varchar(20) NOT NULL COMMENT '종목 코드',
  `account_db_key` bigint unsigned NOT NULL COMMENT '사용자 계정 키',
  `timestamp` datetime(6) NOT NULL COMMENT '기록 시간',
  `state_vector_x` json NOT NULL COMMENT '상태 벡터 [trend, momentum, volatility, macro_signal, tech_signal]',
  `covariance_matrix_p` json NOT NULL COMMENT '공분산 행렬 (5x5)',
  `step_count` int DEFAULT 0 COMMENT '필터 실행 스텝 수',
  `trading_signal` varchar(20) DEFAULT NULL COMMENT '생성된 트레이딩 신호',
  `market_data` json DEFAULT NULL COMMENT '시장 데이터 스냅샷',
  `performance_metrics` json DEFAULT NULL COMMENT '성능 지표',
  `created_at` datetime(6) DEFAULT CURRENT_TIMESTAMP(6) COMMENT '생성 시간',
  PRIMARY KEY (`idx`),
  INDEX `idx_ticker_timestamp` (`ticker`, `timestamp`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_created_at` (`created_at`),
  INDEX `idx_ticker_account` (`ticker`, `account_db_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='칼만 필터 이력 테이블 (Shard 1)';

-- =====================================
-- 칼만 필터 관련 프로시저 (Shard 1) - 기존 패턴 준수
-- =====================================

-- 칼만 필터 이력 저장 프로시저
DROP PROCEDURE IF EXISTS `fp_kalman_history_insert`;
DELIMITER ;;
CREATE PROCEDURE `fp_kalman_history_insert`(
    IN p_ticker VARCHAR(20),
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_timestamp DATETIME(6),
    IN p_state_vector_x JSON,
    IN p_covariance_matrix_p JSON,
    IN p_step_count INT,
    IN p_trading_signal VARCHAR(20),
    IN p_market_data JSON,
    IN p_performance_metrics JSON
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_ticker, ',', p_account_db_key, ',', p_step_count);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_kalman_history_insert', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 칼만 필터 이력 저장
    INSERT INTO table_kalman_history (
        ticker, account_db_key, timestamp, state_vector_x, covariance_matrix_p,
        step_count, trading_signal, market_data, performance_metrics
    ) VALUES (
        p_ticker, p_account_db_key, p_timestamp, p_state_vector_x, p_covariance_matrix_p,
        p_step_count, p_trading_signal, p_market_data, p_performance_metrics
    );
    
    SELECT 'SUCCESS' as result, LAST_INSERT_ID() as idx;
    
END ;;
DELIMITER ;

-- 최신 칼만 필터 상태 조회 프로시저 (Redis 복원용)
DROP PROCEDURE IF EXISTS `fp_kalman_latest_state_get`;
DELIMITER ;;
CREATE PROCEDURE `fp_kalman_latest_state_get`(
    IN p_ticker VARCHAR(20),
    IN p_account_db_key BIGINT UNSIGNED
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_ticker, ',', p_account_db_key);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_kalman_latest_state_get', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 해당 ticker, account의 최신 상태 조회
    SELECT 
        ticker,
        account_db_key,
        timestamp,
        state_vector_x,
        covariance_matrix_p,
        step_count,
        trading_signal,
        market_data,
        performance_metrics,
        created_at
    FROM table_kalman_history
    WHERE ticker = p_ticker 
      AND account_db_key = p_account_db_key
    ORDER BY timestamp DESC, created_at DESC
    LIMIT 1;
    
END ;;
DELIMITER ;

-- 칼만 필터 이력 조회 프로시저 (분석용)
DROP PROCEDURE IF EXISTS `fp_kalman_history_get`;
DELIMITER ;;
CREATE PROCEDURE `fp_kalman_history_get`(
    IN p_ticker VARCHAR(20),
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_start_date DATETIME,
    IN p_end_date DATETIME,
    IN p_limit INT,
    IN p_offset INT
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_ticker, ',', p_account_db_key, ',', p_limit, ',', p_offset);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_kalman_history_get', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 칼만 필터 이력 조회 (페이징 지원)
    SELECT 
        idx,
        ticker,
        account_db_key,
        timestamp,
        state_vector_x,
        covariance_matrix_p,
        step_count,
        trading_signal,
        market_data,
        performance_metrics,
        created_at
    FROM table_kalman_history
    WHERE ticker = p_ticker 
      AND account_db_key = p_account_db_key
      AND timestamp BETWEEN p_start_date AND p_end_date
    ORDER BY timestamp ASC, created_at ASC
    LIMIT p_limit OFFSET p_offset;
    
END ;;
DELIMITER ;

-- =====================================
-- Shard DB 2에 동일한 구조 생성
-- =====================================
USE finance_shard_2;

-- 동일한 테이블 구조 복사 (Shard 2)
CREATE TABLE IF NOT EXISTS `table_kalman_history` (
  `idx` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '이력 고유 인덱스',
  `ticker` varchar(20) NOT NULL COMMENT '종목 코드',
  `account_db_key` bigint unsigned NOT NULL COMMENT '사용자 계정 키',
  `timestamp` datetime(6) NOT NULL COMMENT '기록 시간',
  `state_vector_x` json NOT NULL COMMENT '상태 벡터 [trend, momentum, volatility, macro_signal, tech_signal]',
  `covariance_matrix_p` json NOT NULL COMMENT '공분산 행렬 (5x5)',
  `step_count` int DEFAULT 0 COMMENT '필터 실행 스텝 수',
  `trading_signal` varchar(20) DEFAULT NULL COMMENT '생성된 트레이딩 신호',
  `market_data` json DEFAULT NULL COMMENT '시장 데이터 스냅샷',
  `performance_metrics` json DEFAULT NULL COMMENT '성능 지표',
  `created_at` datetime(6) DEFAULT CURRENT_TIMESTAMP(6) COMMENT '생성 시간',
  PRIMARY KEY (`idx`),
  INDEX `idx_ticker_timestamp` (`ticker`, `timestamp`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_created_at` (`created_at`),
  INDEX `idx_ticker_account` (`ticker`, `account_db_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='칼만 필터 이력 테이블 (Shard 2)';

-- =====================================
-- Shard 2 프로시저 복사
-- =====================================

DROP PROCEDURE IF EXISTS `fp_kalman_history_insert`;
DELIMITER ;;
CREATE PROCEDURE `fp_kalman_history_insert`(
    IN p_ticker VARCHAR(20),
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_timestamp DATETIME(6),
    IN p_state_vector_x JSON,
    IN p_covariance_matrix_p JSON,
    IN p_step_count INT,
    IN p_trading_signal VARCHAR(20),
    IN p_market_data JSON,
    IN p_performance_metrics JSON
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_ticker, ',', p_account_db_key, ',', p_step_count);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_kalman_history_insert', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    INSERT INTO table_kalman_history (
        ticker, account_db_key, timestamp, state_vector_x, covariance_matrix_p,
        step_count, trading_signal, market_data, performance_metrics
    ) VALUES (
        p_ticker, p_account_db_key, p_timestamp, p_state_vector_x, p_covariance_matrix_p,
        p_step_count, p_trading_signal, p_market_data, p_performance_metrics
    );
    
    SELECT 'SUCCESS' as result, LAST_INSERT_ID() as idx;
    
END ;;
DELIMITER ;

DROP PROCEDURE IF EXISTS `fp_kalman_latest_state_get`;
DELIMITER ;;
CREATE PROCEDURE `fp_kalman_latest_state_get`(
    IN p_ticker VARCHAR(20),
    IN p_account_db_key BIGINT UNSIGNED
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_ticker, ',', p_account_db_key);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_kalman_latest_state_get', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    SELECT 
        ticker,
        account_db_key,
        timestamp,
        state_vector_x,
        covariance_matrix_p,
        step_count,
        trading_signal,
        market_data,
        performance_metrics,
        created_at
    FROM table_kalman_history
    WHERE ticker = p_ticker 
      AND account_db_key = p_account_db_key
    ORDER BY timestamp DESC, created_at DESC
    LIMIT 1;
    
END ;;
DELIMITER ;

DROP PROCEDURE IF EXISTS `fp_kalman_history_get`;
DELIMITER ;;
CREATE PROCEDURE `fp_kalman_history_get`(
    IN p_ticker VARCHAR(20),
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_start_date DATETIME,
    IN p_end_date DATETIME,
    IN p_limit INT,
    IN p_offset INT
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_ticker, ',', p_account_db_key, ',', p_limit, ',', p_offset);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_kalman_history_get', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    SELECT 
        idx,
        ticker,
        account_db_key,
        timestamp,
        state_vector_x,
        covariance_matrix_p,
        step_count,
        trading_signal,
        market_data,
        performance_metrics,
        created_at
    FROM table_kalman_history
    WHERE ticker = p_ticker 
      AND account_db_key = p_account_db_key
      AND timestamp BETWEEN p_start_date AND p_end_date
    ORDER BY timestamp ASC, created_at ASC
    LIMIT p_limit OFFSET p_offset;
    
END ;;
DELIMITER ;

-- 최종 상태 확인
SELECT 'Kalman filter tables extension completed for both shards with proper base_server patterns' as status; 