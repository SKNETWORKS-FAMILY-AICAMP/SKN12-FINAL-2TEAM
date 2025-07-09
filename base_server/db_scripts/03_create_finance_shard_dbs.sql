-- =====================================
-- Finance Shard DB 생성 (game_server 방식 적용)
-- =====================================

-- Finance Shard DB 1 생성
DROP DATABASE IF EXISTS finance_shard_1;
CREATE DATABASE finance_shard_1 CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE finance_shard_1;

-- 에러 로그 테이블 (각 샤드별로 필요)
CREATE TABLE IF NOT EXISTS `table_errorlog` (
  `idx` int NOT NULL AUTO_INCREMENT,
  `procedure_name` varchar(45) DEFAULT NULL,
  `error_state` varchar(10) DEFAULT NULL,
  `error_no` varchar(10) DEFAULT NULL,
  `error_message` varchar(128) DEFAULT NULL,
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `param` varchar(4000) NOT NULL,
  PRIMARY KEY (`idx`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 사용자 계좌 정보 테이블
CREATE TABLE IF NOT EXISTS `table_user_accounts` (
  `account_db_key` bigint unsigned NOT NULL,
  `account_number` varchar(20) NOT NULL,
  `balance` decimal(15,2) DEFAULT 0.00,
  `account_type` enum('checking','savings','investment') DEFAULT 'checking',
  `account_status` enum('active','suspended','closed') DEFAULT 'active',
  `currency_code` varchar(3) DEFAULT 'USD',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`account_db_key`),
  UNIQUE KEY `uk_account_number` (`account_number`),
  INDEX `idx_account_status` (`account_status`),
  INDEX `idx_updated_at` (`updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 거래 내역 테이블
CREATE TABLE IF NOT EXISTS `table_transactions` (
  `transaction_id` varchar(32) NOT NULL,
  `account_db_key` bigint unsigned NOT NULL,
  `account_number` varchar(20),
  `amount` decimal(15,2) NOT NULL,
  `transaction_type` enum('deposit','withdrawal','transfer_in','transfer_out','fee') NOT NULL,
  `description` text,
  `reference_id` varchar(50),
  `status` enum('pending','completed','failed','cancelled') DEFAULT 'pending',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`transaction_id`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_account_number` (`account_number`),
  INDEX `idx_transaction_type` (`transaction_type`),
  INDEX `idx_status` (`status`),
  INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 포트폴리오 테이블
CREATE TABLE IF NOT EXISTS `table_user_portfolios` (
  `portfolio_id` bigint NOT NULL AUTO_INCREMENT,
  `account_db_key` bigint unsigned NOT NULL,
  `asset_code` varchar(10) NOT NULL,
  `quantity` decimal(15,6) DEFAULT 0.000000,
  `average_cost` decimal(15,2) DEFAULT 0.00,
  `current_value` decimal(15,2) DEFAULT 0.00,
  `last_updated` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`portfolio_id`),
  UNIQUE KEY `uk_user_asset` (`account_db_key`,`asset_code`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_asset_code` (`asset_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Shard 1 스토어드 프로시저: 계좌 생성
DROP PROCEDURE IF EXISTS `fp_create_account`;
DELIMITER ;;
CREATE PROCEDURE `fp_create_account`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_account_type VARCHAR(20)
)
BEGIN
    DECLARE v_account_number VARCHAR(20);
    DECLARE v_result VARCHAR(20) DEFAULT 'FAILED';
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_account_type);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
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

-- Shard 1 스토어드 프로시저: 계좌 정보 조회
DROP PROCEDURE IF EXISTS `fp_get_account_info`;
DELIMITER ;;
CREATE PROCEDURE `fp_get_account_info`(
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

SELECT 'Finance Shard 1 DB 생성 완료' as status;

-- =====================================
-- Finance Shard DB 2 생성
-- =====================================

DROP DATABASE IF EXISTS finance_shard_2;
CREATE DATABASE finance_shard_2 CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE finance_shard_2;

-- 동일한 테이블 구조 생성
CREATE TABLE IF NOT EXISTS `table_errorlog` (
  `idx` int NOT NULL AUTO_INCREMENT,
  `procedure_name` varchar(45) DEFAULT NULL,
  `error_state` varchar(10) DEFAULT NULL,
  `error_no` varchar(10) DEFAULT NULL,
  `error_message` varchar(128) DEFAULT NULL,
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `param` varchar(4000) NOT NULL,
  PRIMARY KEY (`idx`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `table_user_accounts` (
  `account_db_key` bigint unsigned NOT NULL,
  `account_number` varchar(20) NOT NULL,
  `balance` decimal(15,2) DEFAULT 0.00,
  `account_type` enum('checking','savings','investment') DEFAULT 'checking',
  `account_status` enum('active','suspended','closed') DEFAULT 'active',
  `currency_code` varchar(3) DEFAULT 'USD',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`account_db_key`),
  UNIQUE KEY `uk_account_number` (`account_number`),
  INDEX `idx_account_status` (`account_status`),
  INDEX `idx_updated_at` (`updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `table_transactions` (
  `transaction_id` varchar(32) NOT NULL,
  `account_db_key` bigint unsigned NOT NULL,
  `account_number` varchar(20),
  `amount` decimal(15,2) NOT NULL,
  `transaction_type` enum('deposit','withdrawal','transfer_in','transfer_out','fee') NOT NULL,
  `description` text,
  `reference_id` varchar(50),
  `status` enum('pending','completed','failed','cancelled') DEFAULT 'pending',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`transaction_id`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_account_number` (`account_number`),
  INDEX `idx_transaction_type` (`transaction_type`),
  INDEX `idx_status` (`status`),
  INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `table_user_portfolios` (
  `portfolio_id` bigint NOT NULL AUTO_INCREMENT,
  `account_db_key` bigint unsigned NOT NULL,
  `asset_code` varchar(10) NOT NULL,
  `quantity` decimal(15,6) DEFAULT 0.000000,
  `average_cost` decimal(15,2) DEFAULT 0.00,
  `current_value` decimal(15,2) DEFAULT 0.00,
  `last_updated` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`portfolio_id`),
  UNIQUE KEY `uk_user_asset` (`account_db_key`,`asset_code`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_asset_code` (`asset_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Shard 2 스토어드 프로시저: 계좌 생성
DROP PROCEDURE IF EXISTS `fp_create_account`;
DELIMITER ;;
CREATE PROCEDURE `fp_create_account`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_account_type VARCHAR(20)
)
BEGIN
    DECLARE v_account_number VARCHAR(20);
    DECLARE v_result VARCHAR(20) DEFAULT 'FAILED';
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_account_type);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_create_account', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 계좌번호 생성 (shard_id + timestamp + account_db_key 조합)
    SET v_account_number = CONCAT('2', UNIX_TIMESTAMP(), LPAD(p_account_db_key % 10000, 4, '0'));
    
    INSERT INTO table_user_accounts (account_db_key, account_number, account_type)
    VALUES (p_account_db_key, v_account_number, p_account_type);
    
    IF ROW_COUNT() > 0 THEN
        SET v_result = 'SUCCESS';
    END IF;
    
    SELECT v_result as result, v_account_number as account_number;
    
END ;;
DELIMITER ;

-- Shard 2 스토어드 프로시저: 계좌 정보 조회
DROP PROCEDURE IF EXISTS `fp_get_account_info`;
DELIMITER ;;
CREATE PROCEDURE `fp_get_account_info`(
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

SELECT 'Finance Shard 2 DB 생성 완료' as status;
SELECT 'Finance 유저 샤딩 DB 스크립트 생성 완료!' as final_status;