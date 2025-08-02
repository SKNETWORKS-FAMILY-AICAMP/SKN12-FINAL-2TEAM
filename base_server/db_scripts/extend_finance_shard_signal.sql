-- =====================================
-- 시그널 알림 시스템 테이블 확장 스크립트
-- 기존 base_server 패턴 준수
-- 외래키 없음, soft delete 지향
-- 적용 대상: finance_shard_1, finance_shard_2
-- =====================================

-- =====================================
-- Shard DB 1에 시그널 테이블 추가
-- =====================================
USE finance_shard_1;

-- 시그널 알람 테이블 (사용자별 종목 알림 설정)
CREATE TABLE IF NOT EXISTS `table_signal_alarms` (
  `idx` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '알람 고유 인덱스 (기존 패턴)',
  `alarm_id` varchar(128) NOT NULL COMMENT '알람 ID (비즈니스 키)',
  `account_db_key` bigint unsigned NOT NULL COMMENT '사용자 계정 키',
  `symbol` varchar(50) NOT NULL COMMENT '종목 코드 (TSLA, AAPL 등)',
  `company_name` varchar(200) DEFAULT NULL COMMENT '기업명 (Tesla, Inc.)',
  `current_price` decimal(15,4) DEFAULT NULL COMMENT '알람 설정 시점 가격',
  `exchange` varchar(50) DEFAULT 'NASDAQ' COMMENT '거래소',
  `currency` varchar(10) DEFAULT 'USD' COMMENT '통화',
  `note` varchar(500) DEFAULT NULL COMMENT '사용자 메모',
  `is_active` tinyint(1) DEFAULT 1 COMMENT '알람 활성화 여부 (1=추론모델 동작, 0=일시정지)',
  `is_deleted` tinyint(1) DEFAULT 0 COMMENT '삭제 여부 (soft delete, 1=화면에서 완전 제거)',
  `created_at` datetime(6) DEFAULT CURRENT_TIMESTAMP(6) COMMENT '생성 시간',
  `updated_at` datetime(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '수정 시간',
  PRIMARY KEY (`idx`),
  UNIQUE KEY `uk_alarm_id` (`alarm_id`),
  UNIQUE KEY `uk_account_symbol` (`account_db_key`, `symbol`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_symbol` (`symbol`),
  INDEX `idx_is_active` (`is_active`),
  INDEX `idx_is_deleted` (`is_deleted`),
  INDEX `idx_active_not_deleted` (`is_active`, `is_deleted`),
  INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='시그널 알람 설정 테이블 (Shard 1)';

-- 시그널 히스토리 테이블 (매수/매도 시그널 발생 기록 및 성과)
CREATE TABLE IF NOT EXISTS `table_signal_history` (
  `idx` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '시그널 고유 인덱스 (기존 패턴)',
  `signal_id` varchar(128) NOT NULL COMMENT '시그널 ID (비즈니스 키)',
  `alarm_id` varchar(128) NOT NULL COMMENT '알람 ID (참조용, FK 없음)',
  `account_db_key` bigint unsigned NOT NULL COMMENT '사용자 계정 키',
  `symbol` varchar(50) NOT NULL COMMENT '종목 코드',
  `signal_type` enum('BUY','SELL') NOT NULL COMMENT '시그널 타입',
  `signal_price` decimal(15,4) NOT NULL COMMENT '시그널 발생 시점 가격',
  `volume` bigint DEFAULT 0 COMMENT '거래량',
  `triggered_at` datetime(6) DEFAULT CURRENT_TIMESTAMP(6) COMMENT '시그널 발생 시간',
  
  -- 성과 평가 필드 (1일 후 배치로 계산)
  `price_after_1d` decimal(15,4) DEFAULT NULL COMMENT '1일 후 가격',
  `profit_rate` decimal(10,4) DEFAULT NULL COMMENT '수익률 (%)',
  `is_win` tinyint(1) DEFAULT NULL COMMENT '1% 이상 움직임 여부 (승률 계산용)',
  `evaluated_at` datetime(6) DEFAULT NULL COMMENT '성과 평가 완료 시간',
  
  `is_deleted` tinyint(1) DEFAULT 0 COMMENT '삭제 여부 (soft delete, 1=화면에서 완전 제거)',
  `created_at` datetime(6) DEFAULT CURRENT_TIMESTAMP(6) COMMENT '생성 시간',
  `updated_at` datetime(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '수정 시간',
  PRIMARY KEY (`idx`),
  UNIQUE KEY `uk_signal_id` (`signal_id`),
  INDEX `idx_alarm_id` (`alarm_id`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_symbol` (`symbol`),
  INDEX `idx_signal_type` (`signal_type`),
  INDEX `idx_triggered_at` (`triggered_at`),
  INDEX `idx_is_win` (`is_win`),
  INDEX `idx_evaluated_at` (`evaluated_at`),
  INDEX `idx_is_deleted` (`is_deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='시그널 히스토리 테이블 (Shard 1)';

-- =====================================
-- 시그널 관련 프로시저 (Shard 1) - 기존 패턴 준수
-- =====================================

-- 시그널 알람 생성 프로시저
DROP PROCEDURE IF EXISTS `fp_signal_alarm_create`;
DELIMITER ;;
CREATE PROCEDURE `fp_signal_alarm_create`(
    IN p_alarm_id VARCHAR(128),
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_symbol VARCHAR(50),
    IN p_company_name VARCHAR(200),
    IN p_current_price DECIMAL(15,4),
    IN p_exchange VARCHAR(50),
    IN p_currency VARCHAR(10),
    IN p_note VARCHAR(500)
)
BEGIN
    DECLARE v_existing_count INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_alarm_id, ',', p_account_db_key, ',', p_symbol);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_signal_alarm_create', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 중복 알람 확인 (삭제되지 않은 것만)
    SELECT COUNT(*) INTO v_existing_count
    FROM table_signal_alarms 
    WHERE account_db_key = p_account_db_key 
      AND symbol = p_symbol 
      AND is_deleted = 0;
    
    IF v_existing_count > 0 THEN
        SELECT 'EXISTS' as result, 'Signal alarm already exists for this symbol' as message, p_alarm_id as alarm_id;
    ELSE
        -- 새 시그널 알람 생성 (기본적으로 활성화 상태)
        INSERT INTO table_signal_alarms (
            alarm_id, account_db_key, symbol, company_name, 
            current_price, exchange, currency, note, is_active
        ) VALUES (
            p_alarm_id, p_account_db_key, p_symbol, p_company_name,
            p_current_price, COALESCE(p_exchange, 'NASDAQ'), 
            COALESCE(p_currency, 'USD'), p_note, 1
        );
        
        SELECT 'SUCCESS' as result, 'Signal alarm created successfully' as message, p_alarm_id as alarm_id;
    END IF;
    
END ;;
DELIMITER ;

-- 시그널 알람 목록 조회 프로시저 (삭제되지 않은 것만)
DROP PROCEDURE IF EXISTS `fp_signal_alarms_get`;
DELIMITER ;;
CREATE PROCEDURE `fp_signal_alarms_get`(
    IN p_account_db_key BIGINT UNSIGNED
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_signal_alarms_get', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 사용자의 시그널 알람 목록 조회 (삭제되지 않은 것만)
    SELECT 
        alarm_id, symbol, company_name, current_price,
        exchange, currency, note, is_active, created_at, updated_at
    FROM table_signal_alarms
    WHERE account_db_key = p_account_db_key
      AND is_deleted = 0
    ORDER BY created_at DESC;
    
END ;;
DELIMITER ;

-- 추론 모델용 활성 알람 목록 조회 프로시저
DROP PROCEDURE IF EXISTS `fp_signal_alarms_get_active`;
DELIMITER ;;
CREATE PROCEDURE `fp_signal_alarms_get_active`()
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = 'get_active_alarms';
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_signal_alarms_get_active', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 추론 모델이 모니터링할 활성 알람만 조회
    SELECT 
        alarm_id, account_db_key, symbol, company_name, current_price,
        exchange, currency, created_at
    FROM table_signal_alarms
    WHERE is_active = 1
      AND is_deleted = 0
    ORDER BY symbol, created_at;
    
END ;;
DELIMITER ;

-- 시그널 히스토리 저장 프로시저
DROP PROCEDURE IF EXISTS `fp_signal_history_save`;
DELIMITER ;;
CREATE PROCEDURE `fp_signal_history_save`(
    IN p_signal_id VARCHAR(128),
    IN p_alarm_id VARCHAR(128),
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_symbol VARCHAR(50),
    IN p_signal_type VARCHAR(10),
    IN p_signal_price DECIMAL(15,4),
    IN p_volume BIGINT
)
BEGIN
    DECLARE v_alarm_active INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_signal_id, ',', p_alarm_id, ',', p_account_db_key, ',', p_symbol);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_signal_history_save', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 활성 알람 확인 (is_active=1 이고 is_deleted=0 인 것만)
    SELECT COUNT(*) INTO v_alarm_active
    FROM table_signal_alarms 
    WHERE alarm_id = p_alarm_id 
      AND account_db_key = p_account_db_key 
      AND is_active = 1 
      AND is_deleted = 0;
    
    IF v_alarm_active = 0 THEN
        SELECT 'FAILED' as result, 'Signal alarm not found or inactive' as message;
    ELSE
        -- 시그널 히스토리 저장
        INSERT INTO table_signal_history (
            signal_id, alarm_id, account_db_key, symbol, 
            signal_type, signal_price, volume
        ) VALUES (
            p_signal_id, p_alarm_id, p_account_db_key, p_symbol,
            p_signal_type, p_signal_price, COALESCE(p_volume, 0)
        );
        
        SELECT 'SUCCESS' as result, 'Signal history saved successfully' as message, p_signal_id as signal_id;
    END IF;
    
END ;;
DELIMITER ;

-- 시그널 히스토리 조회 프로시저 (삭제되지 않은 것만)
DROP PROCEDURE IF EXISTS `fp_signal_history_get`;
DELIMITER ;;
CREATE PROCEDURE `fp_signal_history_get`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_symbol VARCHAR(50),
    IN p_limit INT,
    IN p_offset INT
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_symbol, ',', p_limit, ',', p_offset);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_signal_history_get', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 시그널 히스토리 조회 (삭제되지 않은 것만)
    IF p_symbol IS NOT NULL AND p_symbol != '' THEN
        SELECT 
            signal_id, alarm_id, symbol, signal_type,
            signal_price, volume, triggered_at,
            price_after_1d, profit_rate, is_win, evaluated_at,
            created_at, updated_at
        FROM table_signal_history
        WHERE account_db_key = p_account_db_key 
          AND symbol = p_symbol 
          AND is_deleted = 0
        ORDER BY triggered_at DESC
        LIMIT p_limit OFFSET p_offset;
    ELSE
        SELECT 
            signal_id, alarm_id, symbol, signal_type,
            signal_price, volume, triggered_at,
            price_after_1d, profit_rate, is_win, evaluated_at,
            created_at, updated_at
        FROM table_signal_history
        WHERE account_db_key = p_account_db_key 
          AND is_deleted = 0
        ORDER BY triggered_at DESC
        LIMIT p_limit OFFSET p_offset;
    END IF;
    
    -- 전체 개수 (삭제되지 않은 것만)
    IF p_symbol IS NOT NULL AND p_symbol != '' THEN
        SELECT COUNT(*) as total_count
        FROM table_signal_history 
        WHERE account_db_key = p_account_db_key 
          AND symbol = p_symbol 
          AND is_deleted = 0;
    ELSE
        SELECT COUNT(*) as total_count
        FROM table_signal_history 
        WHERE account_db_key = p_account_db_key 
          AND is_deleted = 0;
    END IF;
    
END ;;
DELIMITER ;

-- 시그널 성과 업데이트 프로시저 (배치 작업용)
DROP PROCEDURE IF EXISTS `fp_signal_performance_update`;
DELIMITER ;;
CREATE PROCEDURE `fp_signal_performance_update`(
    IN p_signal_id VARCHAR(128),
    IN p_price_after_1d DECIMAL(15,4),
    IN p_profit_rate DECIMAL(10,4),
    IN p_is_win TINYINT(1)
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_signal_id, ',', p_price_after_1d, ',', p_profit_rate);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_signal_performance_update', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 시그널 성과 업데이트 (삭제되지 않은 것만)
    UPDATE table_signal_history 
    SET price_after_1d = p_price_after_1d,
        profit_rate = p_profit_rate,
        is_win = p_is_win,
        evaluated_at = NOW(6),
        updated_at = NOW(6)
    WHERE signal_id = p_signal_id
      AND is_deleted = 0;
    
    SELECT 'SUCCESS' as result, 'Signal performance updated successfully' as message;
    
END ;;
DELIMITER ;

-- 시그널 알람 활성화/비활성화 토글 프로시저
DROP PROCEDURE IF EXISTS `fp_signal_alarm_toggle`;
DELIMITER ;;
CREATE PROCEDURE `fp_signal_alarm_toggle`(
    IN p_alarm_id VARCHAR(128),
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_is_active TINYINT(1)
)
BEGIN
    DECLARE v_alarm_exists INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_alarm_id, ',', p_account_db_key, ',', p_is_active);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_signal_alarm_toggle', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 알람 존재 및 소유권 확인 (삭제되지 않은 것만)
    SELECT COUNT(*) INTO v_alarm_exists
    FROM table_signal_alarms 
    WHERE alarm_id = p_alarm_id 
      AND account_db_key = p_account_db_key 
      AND is_deleted = 0;
    
    IF v_alarm_exists = 0 THEN
        SELECT 'FAILED' as result, 'Signal alarm not found' as message;
    ELSE
        -- 활성화 상태 토글
        UPDATE table_signal_alarms 
        SET is_active = p_is_active,
            updated_at = NOW(6)
        WHERE alarm_id = p_alarm_id 
          AND account_db_key = p_account_db_key;
        
        SELECT 'SUCCESS' as result, 
               CONCAT('Signal alarm ', IF(p_is_active, 'activated', 'deactivated'), ' successfully') as message;
    END IF;
    
END ;;
DELIMITER ;

-- 시그널 알람 Soft Delete 프로시저
DROP PROCEDURE IF EXISTS `fp_signal_alarm_soft_delete`;
DELIMITER ;;
CREATE PROCEDURE `fp_signal_alarm_soft_delete`(
    IN p_alarm_id VARCHAR(128),
    IN p_account_db_key BIGINT UNSIGNED
)
BEGIN
    DECLARE v_alarm_exists INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_alarm_id, ',', p_account_db_key);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_signal_alarm_soft_delete', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- 알람 존재 및 소유권 확인 (삭제되지 않은 것만)
    SELECT COUNT(*) INTO v_alarm_exists
    FROM table_signal_alarms 
    WHERE alarm_id = p_alarm_id 
      AND account_db_key = p_account_db_key 
      AND is_deleted = 0;
    
    IF v_alarm_exists = 0 THEN
        ROLLBACK;
        SELECT 'FAILED' as result, 'Signal alarm not found or already deleted' as message;
    ELSE
        -- 시그널 알람 Soft Delete (화면에서 완전 제거)
        UPDATE table_signal_alarms 
        SET is_deleted = 1,
            is_active = 0,  -- 삭제 시 비활성화도 함께
            updated_at = NOW(6)
        WHERE alarm_id = p_alarm_id 
          AND account_db_key = p_account_db_key;
        
        -- 관련 시그널 히스토리도 Soft Delete (선택적)
        UPDATE table_signal_history 
        SET is_deleted = 1,
            updated_at = NOW(6)
        WHERE alarm_id = p_alarm_id 
          AND account_db_key = p_account_db_key;
        
        COMMIT;
        SELECT 'SUCCESS' as result, 'Signal alarm soft deleted successfully' as message;
    END IF;
    
END ;;
DELIMITER ;

-- 승률/수익률 통계 조회 프로시저 (활성 알람에서 발생한 시그널만)
DROP PROCEDURE IF EXISTS `fp_signal_statistics_get`;
DELIMITER ;;
CREATE PROCEDURE `fp_signal_statistics_get`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_symbol VARCHAR(50)
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_symbol);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_signal_statistics_get', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 승률/수익률 통계 계산 (삭제되지 않은 시그널만, 평가 완료된 것만)
    IF p_symbol IS NOT NULL AND p_symbol != '' THEN
        SELECT 
            symbol,
            COUNT(*) as total_signals,
            SUM(CASE WHEN is_win = 1 THEN 1 ELSE 0 END) as win_count,
            AVG(profit_rate) as avg_profit_rate,
            (SUM(CASE WHEN is_win = 1 THEN 1 ELSE 0 END) / COUNT(*)) * 100 as win_rate_percent,
            MAX(profit_rate) as max_profit_rate,
            MIN(profit_rate) as min_profit_rate
        FROM table_signal_history 
        WHERE account_db_key = p_account_db_key 
          AND symbol = p_symbol
          AND is_deleted = 0 
          AND evaluated_at IS NOT NULL
        GROUP BY symbol;
    ELSE
        SELECT 
            symbol,
            COUNT(*) as total_signals,
            SUM(CASE WHEN is_win = 1 THEN 1 ELSE 0 END) as win_count,
            AVG(profit_rate) as avg_profit_rate,
            (SUM(CASE WHEN is_win = 1 THEN 1 ELSE 0 END) / COUNT(*)) * 100 as win_rate_percent,
            MAX(profit_rate) as max_profit_rate,
            MIN(profit_rate) as min_profit_rate
        FROM table_signal_history 
        WHERE account_db_key = p_account_db_key 
          AND is_deleted = 0 
          AND evaluated_at IS NOT NULL
        GROUP BY symbol
        ORDER BY total_signals DESC;
    END IF;
    
END ;;
DELIMITER ;

-- =====================================
-- Shard DB 2에 동일한 구조 생성
-- =====================================
USE finance_shard_2;

-- 동일한 테이블 구조 복사 (Shard 2)
CREATE TABLE IF NOT EXISTS `table_signal_alarms` (
  `idx` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '알람 고유 인덱스 (기존 패턴)',
  `alarm_id` varchar(128) NOT NULL COMMENT '알람 ID (비즈니스 키)',
  `account_db_key` bigint unsigned NOT NULL COMMENT '사용자 계정 키',
  `symbol` varchar(50) NOT NULL COMMENT '종목 코드 (TSLA, AAPL 등)',
  `company_name` varchar(200) DEFAULT NULL COMMENT '기업명 (Tesla, Inc.)',
  `current_price` decimal(15,4) DEFAULT NULL COMMENT '알람 설정 시점 가격',
  `exchange` varchar(50) DEFAULT 'NASDAQ' COMMENT '거래소',
  `currency` varchar(10) DEFAULT 'USD' COMMENT '통화',
  `note` varchar(500) DEFAULT NULL COMMENT '사용자 메모',
  `is_active` tinyint(1) DEFAULT 1 COMMENT '알람 활성화 여부 (1=추론모델 동작, 0=일시정지)',
  `is_deleted` tinyint(1) DEFAULT 0 COMMENT '삭제 여부 (soft delete, 1=화면에서 완전 제거)',
  `created_at` datetime(6) DEFAULT CURRENT_TIMESTAMP(6) COMMENT '생성 시간',
  `updated_at` datetime(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '수정 시간',
  PRIMARY KEY (`idx`),
  UNIQUE KEY `uk_alarm_id` (`alarm_id`),
  UNIQUE KEY `uk_account_symbol` (`account_db_key`, `symbol`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_symbol` (`symbol`),
  INDEX `idx_is_active` (`is_active`),
  INDEX `idx_is_deleted` (`is_deleted`),
  INDEX `idx_active_not_deleted` (`is_active`, `is_deleted`),
  INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='시그널 알람 설정 테이블 (Shard 2)';

CREATE TABLE IF NOT EXISTS `table_signal_history` (
  `idx` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '시그널 고유 인덱스 (기존 패턴)',
  `signal_id` varchar(128) NOT NULL COMMENT '시그널 ID (비즈니스 키)',
  `alarm_id` varchar(128) NOT NULL COMMENT '알람 ID (참조용, FK 없음)',
  `account_db_key` bigint unsigned NOT NULL COMMENT '사용자 계정 키',
  `symbol` varchar(50) NOT NULL COMMENT '종목 코드',
  `signal_type` enum('BUY','SELL') NOT NULL COMMENT '시그널 타입',
  `signal_price` decimal(15,4) NOT NULL COMMENT '시그널 발생 시점 가격',
  `volume` bigint DEFAULT 0 COMMENT '거래량',
  `triggered_at` datetime(6) DEFAULT CURRENT_TIMESTAMP(6) COMMENT '시그널 발생 시간',
  
  -- 성과 평가 필드 (1일 후 배치로 계산)
  `price_after_1d` decimal(15,4) DEFAULT NULL COMMENT '1일 후 가격',
  `profit_rate` decimal(10,4) DEFAULT NULL COMMENT '수익률 (%)',
  `is_win` tinyint(1) DEFAULT NULL COMMENT '1% 이상 움직임 여부 (승률 계산용)',
  `evaluated_at` datetime(6) DEFAULT NULL COMMENT '성과 평가 완료 시간',
  
  `is_deleted` tinyint(1) DEFAULT 0 COMMENT '삭제 여부 (soft delete, 1=화면에서 완전 제거)',
  `created_at` datetime(6) DEFAULT CURRENT_TIMESTAMP(6) COMMENT '생성 시간',
  `updated_at` datetime(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '수정 시간',
  PRIMARY KEY (`idx`),
  UNIQUE KEY `uk_signal_id` (`signal_id`),
  INDEX `idx_alarm_id` (`alarm_id`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_symbol` (`symbol`),
  INDEX `idx_signal_type` (`signal_type`),
  INDEX `idx_triggered_at` (`triggered_at`),
  INDEX `idx_is_win` (`is_win`),
  INDEX `idx_evaluated_at` (`evaluated_at`),
  INDEX `idx_is_deleted` (`is_deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='시그널 히스토리 테이블 (Shard 2)';

-- =====================================
-- Shard 2 주요 프로시저 복사
-- =====================================

-- 시그널 알람 생성 프로시저 (Shard 2)
DROP PROCEDURE IF EXISTS `fp_signal_alarm_create`;
DELIMITER ;;
CREATE PROCEDURE `fp_signal_alarm_create`(
    IN p_alarm_id VARCHAR(128),
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_symbol VARCHAR(50),
    IN p_company_name VARCHAR(200),
    IN p_current_price DECIMAL(15,4),
    IN p_exchange VARCHAR(50),
    IN p_currency VARCHAR(10),
    IN p_note VARCHAR(500)
)
BEGIN
    DECLARE v_existing_count INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_alarm_id, ',', p_account_db_key, ',', p_symbol);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_signal_alarm_create', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    SELECT COUNT(*) INTO v_existing_count
    FROM table_signal_alarms 
    WHERE account_db_key = p_account_db_key 
      AND symbol = p_symbol 
      AND is_deleted = 0;
    
    IF v_existing_count > 0 THEN
        SELECT 'EXISTS' as result, 'Signal alarm already exists for this symbol' as message, p_alarm_id as alarm_id;
    ELSE
        INSERT INTO table_signal_alarms (
            alarm_id, account_db_key, symbol, company_name, 
            current_price, exchange, currency, note, is_active
        ) VALUES (
            p_alarm_id, p_account_db_key, p_symbol, p_company_name,
            p_current_price, COALESCE(p_exchange, 'NASDAQ'), 
            COALESCE(p_currency, 'USD'), p_note, 1
        );
        
        SELECT 'SUCCESS' as result, 'Signal alarm created successfully' as message, p_alarm_id as alarm_id;
    END IF;
    
END ;;
DELIMITER ;

-- 추론 모델용 활성 알람 목록 조회 프로시저 (Shard 2)
DROP PROCEDURE IF EXISTS `fp_signal_alarms_get_active`;
DELIMITER ;;
CREATE PROCEDURE `fp_signal_alarms_get_active`()
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = 'get_active_alarms';
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_signal_alarms_get_active', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    SELECT 
        alarm_id, account_db_key, symbol, company_name, current_price,
        exchange, currency, created_at
    FROM table_signal_alarms
    WHERE is_active = 1
      AND is_deleted = 0
    ORDER BY symbol, created_at;
    
END ;;
DELIMITER ;

-- 최종 상태 확인
SELECT 'Signal alarm system extension completed for both shards with proper base_server patterns' as status;