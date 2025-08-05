-- =====================================
-- 모든 테이블 삭제 후 재생성 (idx를 account_db_key로 통합)
-- 개발 환경용 - 주의: 모든 데이터가 삭제됩니다!
-- =====================================

-- 기존 데이터베이스 삭제
DROP DATABASE IF EXISTS finance_global;
DROP DATABASE IF EXISTS finance_shard_1;
DROP DATABASE IF EXISTS finance_shard_2;

-- =====================================
-- Finance Global DB 재생성
-- =====================================
CREATE DATABASE finance_global CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE finance_global;

-- 1. 에러 로그 테이블
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

-- 2. 계정 테이블 (개인정보 설정 필드 포함)
CREATE TABLE IF NOT EXISTS `table_accountid` (
  `account_db_key` bigint unsigned NOT NULL AUTO_INCREMENT,
  `platform_type` tinyint NOT NULL DEFAULT 1,
  `account_id` varchar(100) NOT NULL,
  `account_status` varchar(15) NOT NULL DEFAULT 'Normal',
  `block_endtime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `is_withdraw` bit(1) NOT NULL DEFAULT b'0',
  `withdraw_cancel_count` tinyint NOT NULL DEFAULT '0',
  `withdraw_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `login_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `logout_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `password_hash` varchar(255) NOT NULL,
  `nickname` varchar(50) NOT NULL,
  `email` varchar(100),
  `phone_number` varchar(20) DEFAULT NULL,
  `email_verified` bit(1) NOT NULL DEFAULT b'0',
  `phone_verified` bit(1) NOT NULL DEFAULT b'0',
  `payment_plan` enum('FREE','BASIC','PREMIUM','ENTERPRISE') DEFAULT 'FREE',
  `plan_expires_at` datetime DEFAULT NULL,
  `account_level` int DEFAULT 1,
  `login_count` int DEFAULT 0,
  `birth_year` INT DEFAULT NULL,
  `birth_month` INT DEFAULT NULL,
  `birth_day` INT DEFAULT NULL,
  `gender` ENUM('M','F','OTHER') DEFAULT NULL,
  PRIMARY KEY (`account_db_key`),
  UNIQUE KEY `ix_accountid_platform_accountid` (`platform_type`,`account_id`),
  KEY `ix_accountid_accountdbkey` (`account_db_key`),
  INDEX `idx_email` (`email`),
  INDEX `idx_phone_number` (`phone_number`),
  INDEX `idx_payment_plan` (`payment_plan`)
) ENGINE=InnoDB AUTO_INCREMENT=1000 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 3. 사용자 샤드 매핑 테이블
CREATE TABLE IF NOT EXISTS `table_user_shard_mapping` (
  `account_db_key` bigint unsigned NOT NULL,
  `shard_id` int NOT NULL,
  `assigned_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`account_db_key`),
  INDEX `idx_shard_id` (`shard_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 4. 샤드 설정 테이블
CREATE TABLE IF NOT EXISTS `table_shard_config` (
  `shard_id` int NOT NULL,
  `shard_name` varchar(50) NOT NULL,
  `host` varchar(255) NOT NULL,
  `port` int NOT NULL DEFAULT 3306,
  `database_name` varchar(100) NOT NULL,
  `username` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `max_connections` int DEFAULT 100,
  `status` enum('active','maintenance','disabled') DEFAULT 'active',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`shard_id`),
  INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 5. 샤드 통계 테이블
CREATE TABLE IF NOT EXISTS `table_shard_stats` (
  `shard_id` int NOT NULL,
  `user_count` int DEFAULT 0,
  `active_users` int DEFAULT 0,
  `last_updated` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`shard_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 6. 사용자 프로필 테이블 (알림 설정 포함)
CREATE TABLE IF NOT EXISTS `table_user_profiles` (
  `account_db_key` bigint unsigned NOT NULL,
  `investment_experience` enum('BEGINNER','INTERMEDIATE','EXPERT') DEFAULT 'BEGINNER',
  `risk_tolerance` enum('CONSERVATIVE','MODERATE','AGGRESSIVE') DEFAULT 'MODERATE',
  `investment_goal` enum('GROWTH','INCOME','PRESERVATION') DEFAULT 'GROWTH',
  `monthly_budget` decimal(15,2) DEFAULT 0.00,
  `profile_completed` tinyint(1) DEFAULT 0,
  `country` varchar(3) DEFAULT 'KOR',
  `timezone` varchar(50) DEFAULT 'Asia/Seoul',
  `email_notifications_enabled` bit(1) NOT NULL DEFAULT b'0',
  `sms_notifications_enabled` bit(1) NOT NULL DEFAULT b'0',
  `push_notifications_enabled` bit(1) NOT NULL DEFAULT b'0',
  `price_alert_enabled` bit(1) NOT NULL DEFAULT b'0',
  `news_alert_enabled` bit(1) NOT NULL DEFAULT b'0',
  `portfolio_alert_enabled` bit(1) NOT NULL DEFAULT b'0',
  `trade_alert_enabled` bit(1) NOT NULL DEFAULT b'0',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`account_db_key`),
  FOREIGN KEY (`account_db_key`) REFERENCES `table_accountid`(`account_db_key`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 7. 결제 정보 테이블
CREATE TABLE IF NOT EXISTS `table_user_payments` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `account_db_key` bigint unsigned NOT NULL,
  `payment_plan` enum('FREE','BASIC','PREMIUM','ENTERPRISE') NOT NULL DEFAULT 'FREE',
  `plan_name` varchar(50) NOT NULL,
  `plan_price` decimal(10,2) NOT NULL DEFAULT 0.00,
  `currency` varchar(3) NOT NULL DEFAULT 'KRW',
  `billing_cycle` enum('MONTHLY','YEARLY') DEFAULT 'MONTHLY',
  `starts_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `expires_at` datetime DEFAULT NULL,
  `auto_renewal` bit(1) NOT NULL DEFAULT b'0',
  `payment_method` varchar(50) DEFAULT NULL,
  `payment_status` enum('ACTIVE','EXPIRED','CANCELLED','PENDING') DEFAULT 'PENDING',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_account_payment` (`account_db_key`),
  FOREIGN KEY (`account_db_key`) REFERENCES `table_accountid`(`account_db_key`) ON DELETE CASCADE,
  INDEX `idx_payment_plan` (`payment_plan`),
  INDEX `idx_expires_at` (`expires_at`),
  INDEX `idx_payment_status` (`payment_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 8. 비밀번호 변경 이력 테이블
CREATE TABLE IF NOT EXISTS `table_password_history` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `account_db_key` bigint unsigned NOT NULL,
  `old_password_hash` varchar(255) NOT NULL,
  `new_password_hash` varchar(255) NOT NULL,
  `change_reason` varchar(100) DEFAULT 'USER_REQUESTED',
  `changed_by_ip` varchar(45) DEFAULT NULL,
  `changed_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`account_db_key`) REFERENCES `table_accountid`(`account_db_key`) ON DELETE CASCADE,
  INDEX `idx_account_changed_at` (`account_db_key`, `changed_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 9. 사용자 API 키 테이블
CREATE TABLE IF NOT EXISTS `table_user_api_keys` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `account_db_key` bigint unsigned NOT NULL,
  `korea_investment_app_key` varchar(255) DEFAULT NULL,
  `korea_investment_app_secret` varchar(255) DEFAULT NULL,
  `alpha_vantage_key` varchar(255) DEFAULT NULL,
  `polygon_key` varchar(255) DEFAULT NULL,
  `finnhub_key` varchar(255) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_account_db_key` (`account_db_key`),
  FOREIGN KEY (`account_db_key`) REFERENCES `table_accountid`(`account_db_key`) ON DELETE CASCADE,
  INDEX `idx_created_at` (`created_at`),
  INDEX `idx_updated_at` (`updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 초기 샤드 설정 데이터
INSERT INTO `table_shard_config` (shard_id, shard_name, host, port, database_name, username, password, status) 
VALUES 
(1, 'finance_shard_1', 'localhost', 3306, 'finance_shard_1', 'root', 'Wkdwkrdhkd91!', 'active'),
(2, 'finance_shard_2', 'localhost', 3306, 'finance_shard_2', 'root', 'Wkdwkrdhkd91!', 'active');

INSERT INTO `table_shard_stats` (shard_id, user_count, active_users) 
VALUES 
(1, 0, 0),
(2, 0, 0);

-- =====================================
-- 수정된 회원가입 프로시저
-- =====================================
DROP PROCEDURE IF EXISTS `fp_user_signup`;
DELIMITER ;;
CREATE PROCEDURE `fp_user_signup`(
    IN p_platform_type TINYINT,
    IN p_account_id VARCHAR(100),
    IN p_password_hash VARCHAR(255),
    IN p_email VARCHAR(100),
    IN p_nickname VARCHAR(50),
    IN p_birth_year INT,
    IN p_birth_month INT,
    IN p_birth_day INT,
    IN p_gender VARCHAR(10)
)
BEGIN
    DECLARE v_account_db_key BIGINT UNSIGNED DEFAULT 0;
    DECLARE v_existing_count INT DEFAULT 0;
    DECLARE v_shard_id INT DEFAULT 0;
    DECLARE v_active_shard_count INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_platform_type, ',', p_account_id, ',', p_email, ',', p_nickname);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_user_signup', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 중복 확인
    SELECT COUNT(*) INTO v_existing_count
    FROM table_accountid 
    WHERE platform_type = p_platform_type 
      AND (account_id = p_account_id OR email = p_email);
    
    IF v_existing_count > 0 THEN
        SELECT 'DUPLICATE_ID' as result, 'Account or email already exists' as message, 0 as account_db_key;
    ELSE
        -- 계정 생성 (account_db_key는 AUTO_INCREMENT로 자동 생성)
        INSERT INTO table_accountid (
            platform_type, account_id, password_hash, email, nickname,
            birth_year, birth_month, birth_day, gender, account_status, login_count
        ) VALUES (
            p_platform_type, p_account_id, p_password_hash, p_email, p_nickname,
            p_birth_year, p_birth_month, p_birth_day, p_gender, 'Normal', 0
        );
        
        -- 자동 생성된 account_db_key 가져오기
        SET v_account_db_key = LAST_INSERT_ID();
        
        -- 활성 샤드 수 조회
        SELECT COUNT(*) INTO v_active_shard_count 
        FROM table_shard_config 
        WHERE status = 'active';
        
        -- 활성 샤드가 없으면 기본값 1, 있으면 account_db_key 기반 할당
        IF v_active_shard_count = 0 THEN
            SET v_shard_id = 1;
        ELSE
            SET v_shard_id = (v_account_db_key % v_active_shard_count) + 1;
        END IF;
        
        -- 샤드 매핑 테이블에 삽입
        INSERT INTO table_user_shard_mapping (account_db_key, shard_id)
        VALUES (v_account_db_key, v_shard_id);
        
        -- 샤드 통계 업데이트
        UPDATE table_shard_stats 
        SET user_count = user_count + 1, last_updated = NOW()
        WHERE shard_id = v_shard_id;
        
        SELECT 'SUCCESS' as result, 'User signup completed' as message, v_account_db_key as account_db_key;
    END IF;
    
END ;;
DELIMITER ;

-- =====================================
-- 수정된 로그인 프로시저
-- =====================================
DROP PROCEDURE IF EXISTS `fp_user_login`;
DELIMITER ;;
CREATE PROCEDURE `fp_user_login`(
    IN p_platform_type TINYINT,
    IN p_account_id VARCHAR(100)
)
BEGIN
    DECLARE v_account_db_key BIGINT UNSIGNED DEFAULT 0;
    DECLARE v_account_status VARCHAR(15) DEFAULT '';
    DECLARE v_shard_id INT DEFAULT 0;
    DECLARE v_result VARCHAR(20) DEFAULT 'FAILED';
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_platform_type, ',', p_account_id);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_user_login', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 계정 정보 조회 (프로필 완료 상태 포함)
    SELECT 
        a.account_db_key, 
        a.password_hash, 
        a.nickname, 
        a.account_level, 
        a.account_status,
        COALESCE(p.profile_completed, 0) as profile_completed
    INTO v_account_db_key, @stored_hash, @nickname, @account_level, v_account_status, @profile_completed
    FROM table_accountid a
    LEFT JOIN table_user_profiles p ON a.account_db_key = p.account_db_key
    WHERE a.platform_type = p_platform_type AND a.account_id = p_account_id;
    
    -- 로그인 성공 처리
    IF v_account_db_key > 0 AND v_account_status = 'Normal' THEN
        SET v_result = 'SUCCESS';
        
        -- 로그인 시간 및 카운트 업데이트
        UPDATE table_accountid
        SET login_time = NOW(),
            login_count = login_count + 1
        WHERE account_db_key = v_account_db_key;
        
        -- 사용자 샤드 조회 (없으면 자동 할당)
        SELECT shard_id INTO v_shard_id
        FROM table_user_shard_mapping 
        WHERE account_db_key = v_account_db_key;
        
        -- 샤드가 없으면 자동 할당
        IF v_shard_id IS NULL OR v_shard_id = 0 THEN
            -- 활성 샤드 수 조회
            SELECT COUNT(*) INTO @active_shard_count 
            FROM table_shard_config 
            WHERE status = 'active';
            
            -- 활성 샤드가 없으면 기본값 1
            IF @active_shard_count = 0 THEN
                SET v_shard_id = 1;
            ELSE
                SET v_shard_id = (v_account_db_key % @active_shard_count) + 1;
            END IF;
            
            INSERT INTO table_user_shard_mapping (account_db_key, shard_id)
            VALUES (v_account_db_key, v_shard_id)
            ON DUPLICATE KEY UPDATE 
                shard_id = v_shard_id,
                updated_at = NOW();
                
            UPDATE table_shard_stats 
            SET user_count = user_count + 1, last_updated = NOW()
            WHERE shard_id = v_shard_id;
        END IF;
        
        -- 로그인 결과 반환 (비밀번호 해시와 프로필 상태 포함)
        SELECT 
            v_result as result,
            v_account_db_key as account_db_key,
            @stored_hash as password_hash,
            @nickname as nickname,
            @account_level as account_level,
            @profile_completed as profile_completed,
            v_shard_id as shard_id
        ;
        
    ELSEIF v_account_db_key > 0 AND v_account_status != 'Normal' THEN
        SELECT 'BLOCKED' as result, 0 as account_db_key, '' as password_hash, '' as nickname, 0 as account_level, 0 as profile_completed, 0 as shard_id;
    ELSE
        SELECT 'NOT_FOUND' as result, 0 as account_db_key, '' as password_hash, '' as nickname, 0 as account_level, 0 as profile_completed, 0 as shard_id;
    END IF;
    
END ;;
DELIMITER ;

-- =====================================
-- 로그아웃 프로시저
-- =====================================
DROP PROCEDURE IF EXISTS `fp_user_logout`;
DELIMITER ;;
CREATE PROCEDURE `fp_user_logout`(
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
            VALUES ('fp_user_logout', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 로그아웃 시간 업데이트
    UPDATE table_accountid
    SET logout_time = NOW()
    WHERE account_db_key = p_account_db_key;
    
    SELECT 'SUCCESS' as result;
    
END ;;
DELIMITER ;

-- =====================================
-- 프로필 설정 프로시저
-- =====================================
DROP PROCEDURE IF EXISTS `fp_profile_setup`;
DELIMITER ;;
CREATE PROCEDURE `fp_profile_setup`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_investment_experience VARCHAR(20),
    IN p_risk_tolerance VARCHAR(20),
    IN p_investment_goal VARCHAR(20),
    IN p_monthly_budget DECIMAL(15,2)
)
BEGIN
    DECLARE v_existing_count INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_investment_experience, ',', p_risk_tolerance, ',', p_investment_goal);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_profile_setup', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 기존 프로필 확인
    SELECT COUNT(*) INTO v_existing_count
    FROM table_user_profiles 
    WHERE account_db_key = p_account_db_key;
    
    IF v_existing_count > 0 THEN
        -- 기존 프로필 업데이트
        UPDATE table_user_profiles 
        SET investment_experience = p_investment_experience,
            risk_tolerance = p_risk_tolerance,
            investment_goal = p_investment_goal,
            monthly_budget = p_monthly_budget,
            profile_completed = 1,
            updated_at = NOW()
        WHERE account_db_key = p_account_db_key;
    ELSE
        -- 새 프로필 생성
        INSERT INTO table_user_profiles (
            account_db_key, investment_experience, risk_tolerance, 
            investment_goal, monthly_budget, profile_completed
        ) VALUES (
            p_account_db_key, p_investment_experience, p_risk_tolerance,
            p_investment_goal, p_monthly_budget, 1
        );
    END IF;
    
    SELECT 'SUCCESS' as result, 'Profile setup completed' as message;
    
END ;;
DELIMITER ;

-- =====================================
-- 프로필 조회 프로시저
-- =====================================
DROP PROCEDURE IF EXISTS `fp_profile_get`;
DELIMITER ;;
CREATE PROCEDURE `fp_profile_get`(
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
            VALUES ('fp_profile_get', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 프로필 정보 조회 (account 테이블과 user_profiles 테이블 조인)
    SELECT 
        a.account_db_key,
        a.platform_type,
        a.account_id,
        a.nickname,
        a.email,
        a.account_level,
        a.birth_year,
        a.birth_month,
        a.birth_day,
        a.gender,
        COALESCE(sm.shard_id, 0) as shard_id,
        COALESCE(p.investment_experience, 'BEGINNER') as investment_experience,
        COALESCE(p.risk_tolerance, 'MODERATE') as risk_tolerance,
        COALESCE(p.investment_goal, 'GROWTH') as investment_goal,
        COALESCE(p.monthly_budget, 0.00) as monthly_budget,
        COALESCE(p.profile_completed, 0) as profile_completed,
        p.country,
        p.timezone
    FROM table_accountid a
    LEFT JOIN table_user_profiles p ON a.account_db_key = p.account_db_key
    LEFT JOIN table_user_shard_mapping sm ON a.account_db_key = sm.account_db_key
    WHERE a.account_db_key = p_account_db_key;
    
END ;;
DELIMITER ;

-- =====================================
-- API 키 저장 프로시저
-- =====================================
DROP PROCEDURE IF EXISTS `fp_save_api_keys`;
DELIMITER ;;
CREATE PROCEDURE `fp_save_api_keys`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_korea_investment_app_key VARCHAR(255),
    IN p_korea_investment_app_secret VARCHAR(255),
    IN p_alpha_vantage_key VARCHAR(255),
    IN p_polygon_key VARCHAR(255),
    IN p_finnhub_key VARCHAR(255)
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_korea_investment_app_key, ',', p_alpha_vantage_key);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_save_api_keys', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- API 키 저장 또는 업데이트
    INSERT INTO table_user_api_keys (
        account_db_key, korea_investment_app_key, korea_investment_app_secret,
        alpha_vantage_key, polygon_key, finnhub_key, created_at, updated_at
    ) VALUES (
        p_account_db_key, p_korea_investment_app_key, p_korea_investment_app_secret,
        p_alpha_vantage_key, p_polygon_key, p_finnhub_key, NOW(), NOW()
    ) ON DUPLICATE KEY UPDATE
        korea_investment_app_key = VALUES(korea_investment_app_key),
        korea_investment_app_secret = VALUES(korea_investment_app_secret),
        alpha_vantage_key = VALUES(alpha_vantage_key),
        polygon_key = VALUES(polygon_key),
        finnhub_key = VALUES(finnhub_key),
        updated_at = NOW();
    
    SELECT 'SUCCESS' as result, 'API keys saved successfully' as message;
    
END ;;
DELIMITER ;

-- =====================================
-- 개인정보 설정 관련 프로시저
-- =====================================

-- 마이페이지 전체 정보 조회
DROP PROCEDURE IF EXISTS `fp_get_user_profile_settings`;
DELIMITER ;;
CREATE PROCEDURE `fp_get_user_profile_settings`(
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
            VALUES ('fp_get_user_profile_settings', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    SELECT 
        -- 기본 계정 정보
        a.account_db_key,
        a.account_id,
        a.nickname,
        a.email,
        a.phone_number,
        a.email_verified,
        a.phone_verified,
        a.payment_plan,
        a.plan_expires_at,
        a.account_level,
        a.create_time,
        a.birth_year,
        a.birth_month,
        a.birth_day,
        a.gender,
        
        -- 프로필 정보
        COALESCE(p.investment_experience, 'BEGINNER') as investment_experience,
        COALESCE(p.risk_tolerance, 'MODERATE') as risk_tolerance,
        COALESCE(p.investment_goal, 'GROWTH') as investment_goal,
        COALESCE(p.monthly_budget, 0.00) as monthly_budget,
        COALESCE(p.profile_completed, 0) as profile_completed,
        p.country,
        p.timezone,
        
        -- 알림 설정
        COALESCE(p.email_notifications_enabled, 1) as email_notifications_enabled,
        COALESCE(p.sms_notifications_enabled, 0) as sms_notifications_enabled,
        COALESCE(p.push_notifications_enabled, 1) as push_notifications_enabled,
        COALESCE(p.price_alert_enabled, 1) as price_alert_enabled,
        COALESCE(p.news_alert_enabled, 1) as news_alert_enabled,
        COALESCE(p.portfolio_alert_enabled, 0) as portfolio_alert_enabled,
        COALESCE(p.trade_alert_enabled, 1) as trade_alert_enabled,
        
        -- 결제 정보
        py.plan_name,
        py.plan_price,
        py.currency,
        py.billing_cycle,
        py.auto_renewal,
        py.payment_status
        
    FROM table_accountid a
    LEFT JOIN table_user_profiles p ON a.account_db_key = p.account_db_key
    LEFT JOIN table_user_payments py ON a.account_db_key = py.account_db_key
    WHERE a.account_db_key = p_account_db_key;
    
END ;;
DELIMITER ;

-- 기본 프로필 정보 업데이트 (이메일, 전화번호, 닉네임)
DROP PROCEDURE IF EXISTS `fp_update_basic_profile`;
DELIMITER ;;
CREATE PROCEDURE `fp_update_basic_profile`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_nickname VARCHAR(50),
    IN p_email VARCHAR(100),
    IN p_phone_number VARCHAR(20)
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_nickname, ',', p_email, ',', p_phone_number);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_update_basic_profile', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 기본 프로필 정보 업데이트
    UPDATE table_accountid 
    SET nickname = p_nickname,
        email = p_email,
        phone_number = p_phone_number
    WHERE account_db_key = p_account_db_key;
    
    SELECT 'SUCCESS' as result, 'Basic profile updated successfully' as message;
    
END ;;
DELIMITER ;

-- 알림 설정 업데이트
DROP PROCEDURE IF EXISTS `fp_update_notification_settings`;
DELIMITER ;;
CREATE PROCEDURE `fp_update_notification_settings`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_email_notifications_enabled BIT(1),
    IN p_sms_notifications_enabled BIT(1),
    IN p_push_notifications_enabled BIT(1),
    IN p_price_alert_enabled BIT(1),
    IN p_news_alert_enabled BIT(1),
    IN p_portfolio_alert_enabled BIT(1),
    IN p_trade_alert_enabled BIT(1)
)
BEGIN
    DECLARE v_existing_count INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_email_notifications_enabled);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_update_notification_settings', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 프로필 존재 확인
    SELECT COUNT(*) INTO v_existing_count
    FROM table_user_profiles 
    WHERE account_db_key = p_account_db_key;
    
    IF v_existing_count = 0 THEN
        -- 프로필이 없으면 기본 프로필 생성
        INSERT INTO table_user_profiles (account_db_key, profile_completed)
        VALUES (p_account_db_key, 0);
    END IF;
    
    -- 알림 설정 업데이트
    UPDATE table_user_profiles 
    SET email_notifications_enabled = p_email_notifications_enabled,
        sms_notifications_enabled = p_sms_notifications_enabled,
        push_notifications_enabled = p_push_notifications_enabled,
        price_alert_enabled = p_price_alert_enabled,
        news_alert_enabled = p_news_alert_enabled,
        portfolio_alert_enabled = p_portfolio_alert_enabled,
        trade_alert_enabled = p_trade_alert_enabled,
        updated_at = NOW()
    WHERE account_db_key = p_account_db_key;
    
    SELECT 'SUCCESS' as result, 'Notification settings updated successfully' as message;
    
END ;;
DELIMITER ;

-- 비밀번호 변경 (bcrypt 지원 - 검증은 Python에서)
DROP PROCEDURE IF EXISTS `fp_change_password`;
DELIMITER ;;
CREATE PROCEDURE `fp_change_password`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_new_password_hash VARCHAR(255),
    IN p_changed_by_ip VARCHAR(45)
)
BEGIN
    DECLARE v_stored_password VARCHAR(255);
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_changed_by_ip);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_change_password', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 현재 비밀번호 해시 가져오기 (이력 저장용)
    SELECT password_hash INTO v_stored_password
    FROM table_accountid 
    WHERE account_db_key = p_account_db_key;
    
    -- 비밀번호 변경 이력 저장
    INSERT INTO table_password_history (
        account_db_key, old_password_hash, new_password_hash, 
        change_reason, changed_by_ip
    ) VALUES (
        p_account_db_key, v_stored_password, p_new_password_hash,
        'USER_REQUESTED', p_changed_by_ip
    );
    
    -- 새 비밀번호로 업데이트
    UPDATE table_accountid
    SET password_hash = p_new_password_hash
    WHERE account_db_key = p_account_db_key;
    
    SELECT 'SUCCESS' as result, 'Password changed successfully' as message;
    
END ;;
DELIMITER ;

-- 결제 플랜 정보 조회
DROP PROCEDURE IF EXISTS `fp_get_payment_plan`;
DELIMITER ;;
CREATE PROCEDURE `fp_get_payment_plan`(
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
            VALUES ('fp_get_payment_plan', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    SELECT 
        a.payment_plan as current_plan,
        a.plan_expires_at,
        COALESCE(p.plan_name, 'Free Plan') as plan_name,
        COALESCE(p.plan_price, 0.00) as plan_price,
        COALESCE(p.currency, 'KRW') as currency,
        p.billing_cycle,
        p.auto_renewal,
        p.payment_status,
        p.starts_at,
        p.expires_at as payment_expires_at
    FROM table_accountid a
    LEFT JOIN table_user_payments p ON a.account_db_key = p.account_db_key
    WHERE a.account_db_key = p_account_db_key;
    
END ;;
DELIMITER ;

-- 사용자 기본 설정 초기화
DROP PROCEDURE IF EXISTS `fp_initialize_user_defaults`;
DELIMITER ;;
CREATE PROCEDURE `fp_initialize_user_defaults`(
    IN p_account_db_key BIGINT UNSIGNED
)
BEGIN
    DECLARE v_profile_exists INT DEFAULT 0;
    DECLARE v_payment_exists INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_initialize_user_defaults', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 프로필 존재 확인
    SELECT COUNT(*) INTO v_profile_exists
    FROM table_user_profiles 
    WHERE account_db_key = p_account_db_key;
    
    -- 결제 정보 존재 확인
    SELECT COUNT(*) INTO v_payment_exists
    FROM table_user_payments 
    WHERE account_db_key = p_account_db_key;
    
    -- 기본 프로필 생성
    IF v_profile_exists = 0 THEN
        INSERT INTO table_user_profiles (
            account_db_key, profile_completed,
            email_notifications_enabled, sms_notifications_enabled,
            push_notifications_enabled, price_alert_enabled,
            news_alert_enabled, portfolio_alert_enabled, trade_alert_enabled
        ) VALUES (
            p_account_db_key, 0, 1, 0, 1, 1, 1, 0, 1
        );
    END IF;
    
    -- 기본 결제 정보 생성 (FREE 플랜)
    IF v_payment_exists = 0 THEN
        INSERT INTO table_user_payments (
            account_db_key, payment_plan, plan_name, plan_price,
            currency, payment_status
        ) VALUES (
            p_account_db_key, 'FREE', 'Free Plan', 0.00,
            'KRW', 'ACTIVE'
        );
    END IF;
    
    SELECT 'SUCCESS' as result, 'User defaults initialized' as message;
    
END ;;
DELIMITER ;

-- =====================================
-- API 키 조회 프로시저
-- =====================================
DROP PROCEDURE IF EXISTS `fp_get_api_keys`;
DELIMITER ;;
CREATE PROCEDURE `fp_get_api_keys`(
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
            VALUES ('fp_get_api_keys', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- API 키 조회
    SELECT 
        korea_investment_app_key,
        korea_investment_app_secret,
        alpha_vantage_key,
        polygon_key,
        finnhub_key,
        created_at,
        updated_at
    FROM table_user_api_keys 
    WHERE account_db_key = p_account_db_key;
    
END ;;
DELIMITER ;

-- =====================================
-- 통합 프로필 업데이트 프로시저 (트랜잭션 처리)
-- =====================================

-- 모든 프로필 설정을 한번에 업데이트하는 통합 프로시저
DROP PROCEDURE IF EXISTS `fp_update_profile_all`;
DELIMITER ;;
CREATE PROCEDURE `fp_update_profile_all`(
    IN p_account_db_key BIGINT UNSIGNED,
    -- 기본 프로필
    IN p_nickname VARCHAR(50),
    IN p_email VARCHAR(100),
    IN p_phone_number VARCHAR(20),
    -- 알림 설정
    IN p_email_notifications_enabled BIT(1),
    IN p_sms_notifications_enabled BIT(1),
    IN p_push_notifications_enabled BIT(1),
    IN p_price_alert_enabled BIT(1),
    IN p_news_alert_enabled BIT(1),
    IN p_portfolio_alert_enabled BIT(1),
    IN p_trade_alert_enabled BIT(1),
    -- 비밀번호 변경 (선택사항 - NULL이면 변경 안함)
    IN p_current_password VARCHAR(255),
    IN p_new_password VARCHAR(255),
    -- API 키 (선택사항 - NULL이면 저장 안함)
    IN p_korea_investment_app_key VARCHAR(255),
    IN p_korea_investment_app_secret VARCHAR(255),
    IN p_alpha_vantage_key VARCHAR(255),
    IN p_polygon_key VARCHAR(255),
    IN p_finnhub_key VARCHAR(255)
)
sp_label:BEGIN
    DECLARE v_password_check_result VARCHAR(10) DEFAULT 'FAILED';
    DECLARE v_password_changed BIT(1) DEFAULT 0;
    DECLARE v_api_keys_saved BIT(1) DEFAULT 0;
    DECLARE v_current_account_id VARCHAR(100) DEFAULT '';
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_nickname, ',', p_email);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_update_profile_all', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- account_id 조회 (비밀번호 해싱용)
    SELECT account_id INTO v_current_account_id
    FROM table_accountid 
    WHERE account_db_key = p_account_db_key;
    
    -- 1. 기본 프로필 업데이트 (table_accountid)
    UPDATE table_accountid 
    SET nickname = p_nickname,
        email = p_email,
        phone_number = p_phone_number
    WHERE account_db_key = p_account_db_key;
    
    -- 2. 알림 설정 업데이트 (table_user_profiles - UPSERT)
    INSERT INTO table_user_profiles (
        account_db_key, email_notifications_enabled, sms_notifications_enabled,
        push_notifications_enabled, price_alert_enabled, news_alert_enabled,
        portfolio_alert_enabled, trade_alert_enabled
    ) VALUES (
        p_account_db_key, p_email_notifications_enabled, p_sms_notifications_enabled,
        p_push_notifications_enabled, p_price_alert_enabled, p_news_alert_enabled,
        p_portfolio_alert_enabled, p_trade_alert_enabled
    ) ON DUPLICATE KEY UPDATE
        email_notifications_enabled = p_email_notifications_enabled,
        sms_notifications_enabled = p_sms_notifications_enabled,
        push_notifications_enabled = p_push_notifications_enabled,
        price_alert_enabled = p_price_alert_enabled,
        news_alert_enabled = p_news_alert_enabled,
        portfolio_alert_enabled = p_portfolio_alert_enabled,
        trade_alert_enabled = p_trade_alert_enabled,
        updated_at = NOW();
    
    -- 3. 비밀번호 변경 (선택사항) - 주의: bcrypt 검증은 Python에서 수행됨
    IF p_current_password IS NOT NULL AND p_new_password IS NOT NULL THEN
        -- p_new_password는 이미 bcrypt로 해싱된 상태로 전달됨
        -- 비밀번호 변경 이력 저장
        INSERT INTO table_password_history (
            account_db_key, old_password_hash, new_password_hash, 
            change_reason, changed_by_ip
        ) VALUES (
            p_account_db_key, 
            (SELECT password_hash FROM table_accountid WHERE account_db_key = p_account_db_key),
            p_new_password,
            'USER_REQUESTED', '127.0.0.1'
        );
        
        -- 새 비밀번호로 업데이트 (이미 해싱된 상태)
        UPDATE table_accountid 
        SET password_hash = p_new_password
        WHERE account_db_key = p_account_db_key;
        
        SET v_password_changed = 1;
    END IF;
    
    -- 4. API 키 저장 (선택사항)
    IF p_korea_investment_app_key IS NOT NULL AND p_korea_investment_app_secret IS NOT NULL THEN
        INSERT INTO table_user_api_keys (
            account_db_key, korea_investment_app_key, korea_investment_app_secret,
            alpha_vantage_key, polygon_key, finnhub_key
        ) VALUES (
            p_account_db_key, p_korea_investment_app_key, p_korea_investment_app_secret,
            COALESCE(p_alpha_vantage_key, ''), COALESCE(p_polygon_key, ''), COALESCE(p_finnhub_key, '')
        ) ON DUPLICATE KEY UPDATE
            korea_investment_app_key = p_korea_investment_app_key,
            korea_investment_app_secret = p_korea_investment_app_secret,
            alpha_vantage_key = COALESCE(p_alpha_vantage_key, alpha_vantage_key),
            polygon_key = COALESCE(p_polygon_key, polygon_key),
            finnhub_key = COALESCE(p_finnhub_key, finnhub_key),
            updated_at = NOW();
        
        SET v_api_keys_saved = 1;
    END IF;
    
    -- 모든 작업 성공 시 커밋
    COMMIT;
    
    -- 성공 응답
    SELECT 'SUCCESS' as result, 'All profile settings updated successfully' as message,
           v_password_changed as password_changed, v_api_keys_saved as api_keys_saved;
    
END ;;
DELIMITER ;

-- =====================================
-- Finance Shard DB 1 재생성
-- =====================================
CREATE DATABASE finance_shard_1 CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE finance_shard_1;

-- 에러 로그 테이블
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

-- 포트폴리오 테이블
CREATE TABLE IF NOT EXISTS `table_user_portfolios` (
  `portfolio_id` bigint NOT NULL AUTO_INCREMENT,
  `account_db_key` bigint unsigned NOT NULL,
  `asset_code` varchar(10) NOT NULL,
  `asset_type` enum('STOCK','ETF','FUND','CASH','CRYPTO') DEFAULT 'STOCK',
  `quantity` decimal(15,6) DEFAULT 0.000000,
  `average_cost` decimal(15,2) DEFAULT 0.00,
  `current_value` decimal(15,2) DEFAULT 0.00,
  `last_updated` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`portfolio_id`),
  UNIQUE KEY `uk_user_asset` (`account_db_key`,`asset_code`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_asset_code` (`asset_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 아웃박스 이벤트 테이블 (Shard 1)
CREATE TABLE IF NOT EXISTS `outbox_events` (
  `id` varchar(36) NOT NULL COMMENT '이벤트 고유 ID (UUID)',
  `event_type` varchar(100) NOT NULL COMMENT '이벤트 타입',
  `aggregate_id` varchar(100) NOT NULL COMMENT '집계 ID (account_db_key 등)',
  `aggregate_type` varchar(50) NOT NULL COMMENT '집계 타입 (account, portfolio, trade 등)',
  `event_data` json NOT NULL COMMENT '이벤트 데이터',
  `status` enum('pending','published','failed','retry') NOT NULL DEFAULT 'pending' COMMENT '이벤트 상태',
  `retry_count` int NOT NULL DEFAULT 0 COMMENT '재시도 횟수',
  `max_retries` int NOT NULL DEFAULT 3 COMMENT '최대 재시도 횟수',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성 시간',
  `updated_at` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '수정 시간',
  `published_at` datetime DEFAULT NULL COMMENT '발행 시간',
  PRIMARY KEY (`id`),
  KEY `idx_status_created` (`status`, `created_at`),
  KEY `idx_event_type` (`event_type`),
  KEY `idx_aggregate` (`aggregate_type`, `aggregate_id`),
  KEY `idx_published_at` (`published_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='아웃박스 이벤트 테이블 (샤드별)';

-- Saga 상태 관리 테이블 (샤드별)
CREATE TABLE IF NOT EXISTS `saga_instances` (
  `saga_id` varchar(36) NOT NULL COMMENT 'Saga 인스턴스 ID',
  `saga_type` varchar(100) NOT NULL COMMENT 'Saga 타입',
  `initiator_id` varchar(100) NOT NULL COMMENT 'Saga 시작자 ID (account_db_key)',
  `status` enum('started','completed','failed','compensating','compensated') NOT NULL DEFAULT 'started',
  `current_step` int NOT NULL DEFAULT 0 COMMENT '현재 단계',
  `total_steps` int NOT NULL COMMENT '전체 단계 수',
  `saga_data` json DEFAULT NULL COMMENT 'Saga 상태 데이터',
  `error_message` text DEFAULT NULL COMMENT '에러 메시지',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `completed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`saga_id`),
  KEY `idx_saga_type_status` (`saga_type`, `status`),
  KEY `idx_initiator_id` (`initiator_id`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Saga 인스턴스 관리 테이블 (샤드별)';

-- Saga 단계 실행 기록 테이블 (샤드별)
CREATE TABLE IF NOT EXISTS `saga_steps` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `saga_id` varchar(36) NOT NULL COMMENT 'Saga 인스턴스 ID',
  `step_number` int NOT NULL COMMENT '단계 번호',
  `step_name` varchar(100) NOT NULL COMMENT '단계 이름',
  `status` enum('pending','completed','failed','compensated') NOT NULL DEFAULT 'pending',
  `request_data` json DEFAULT NULL COMMENT '요청 데이터',
  `response_data` json DEFAULT NULL COMMENT '응답 데이터',
  `error_message` text DEFAULT NULL COMMENT '에러 메시지',
  `started_at` datetime DEFAULT NULL,
  `completed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_saga_step` (`saga_id`, `step_number`),
  KEY `idx_saga_id` (`saga_id`),
  KEY `idx_status` (`status`),
  FOREIGN KEY (`saga_id`) REFERENCES `saga_instances`(`saga_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Saga 단계 실행 기록 테이블 (샤드별)';

-- 계좌 생성 프로시저
DROP PROCEDURE IF EXISTS `fp_create_account`;
DELIMITER ;;
CREATE PROCEDURE `fp_create_account`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_account_type VARCHAR(20)
)
BEGIN
    DECLARE v_account_number VARCHAR(20);
    DECLARE v_result VARCHAR(20) DEFAULT 'FAILED';
    DECLARE v_existing_count INT DEFAULT 0;
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
    
    -- 기존 계좌 확인 (account_db_key만으로 체크)
    SELECT COUNT(*) INTO v_existing_count
    FROM table_user_accounts 
    WHERE account_db_key = p_account_db_key;
    
    IF v_existing_count > 0 THEN
        SELECT 'EXISTS' as result, 
               account_number
        FROM table_user_accounts 
        WHERE account_db_key = p_account_db_key
        LIMIT 1;
    ELSE
        -- 계좌번호 생성 (shard_id + timestamp + account_db_key 조합)
        SET v_account_number = CONCAT('1', UNIX_TIMESTAMP(), LPAD(p_account_db_key % 10000, 4, '0'));
        
        INSERT INTO table_user_accounts (account_db_key, account_number, account_type)
        VALUES (p_account_db_key, v_account_number, p_account_type);
        
        IF ROW_COUNT() > 0 THEN
            SET v_result = 'SUCCESS';
        END IF;
        
        SELECT v_result as result, v_account_number as account_number;
    END IF;
    
END ;;
DELIMITER ;

-- 계좌 정보 조회 프로시저
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

-- =====================================
-- Finance Shard DB 2 재생성
-- =====================================
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

CREATE TABLE IF NOT EXISTS `table_user_portfolios` (
  `portfolio_id` bigint NOT NULL AUTO_INCREMENT,
  `account_db_key` bigint unsigned NOT NULL,
  `asset_code` varchar(10) NOT NULL,
  `asset_type` enum('STOCK','ETF','FUND','CASH','CRYPTO') DEFAULT 'STOCK',
  `quantity` decimal(15,6) DEFAULT 0.000000,
  `average_cost` decimal(15,2) DEFAULT 0.00,
  `current_value` decimal(15,2) DEFAULT 0.00,
  `last_updated` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`portfolio_id`),
  UNIQUE KEY `uk_user_asset` (`account_db_key`,`asset_code`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_asset_code` (`asset_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 아웃박스 이벤트 테이블 (Shard 2)
CREATE TABLE IF NOT EXISTS `outbox_events` (
  `id` varchar(36) NOT NULL COMMENT '이벤트 고유 ID (UUID)',
  `event_type` varchar(100) NOT NULL COMMENT '이벤트 타입',
  `aggregate_id` varchar(100) NOT NULL COMMENT '집계 ID (account_db_key 등)',
  `aggregate_type` varchar(50) NOT NULL COMMENT '집계 타입 (account, portfolio, trade 등)',
  `event_data` json NOT NULL COMMENT '이벤트 데이터',
  `status` enum('pending','published','failed','retry') NOT NULL DEFAULT 'pending' COMMENT '이벤트 상태',
  `retry_count` int NOT NULL DEFAULT 0 COMMENT '재시도 횟수',
  `max_retries` int NOT NULL DEFAULT 3 COMMENT '최대 재시도 횟수',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성 시간',
  `updated_at` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '수정 시간',
  `published_at` datetime DEFAULT NULL COMMENT '발행 시간',
  PRIMARY KEY (`id`),
  KEY `idx_status_created` (`status`, `created_at`),
  KEY `idx_event_type` (`event_type`),
  KEY `idx_aggregate` (`aggregate_type`, `aggregate_id`),
  KEY `idx_published_at` (`published_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='아웃박스 이벤트 테이블 (샤드별)';

-- Saga 상태 관리 테이블 (Shard 2)
CREATE TABLE IF NOT EXISTS `saga_instances` (
  `saga_id` varchar(36) NOT NULL COMMENT 'Saga 인스턴스 ID',
  `saga_type` varchar(100) NOT NULL COMMENT 'Saga 타입',
  `initiator_id` varchar(100) NOT NULL COMMENT 'Saga 시작자 ID (account_db_key)',
  `status` enum('started','completed','failed','compensating','compensated') NOT NULL DEFAULT 'started',
  `current_step` int NOT NULL DEFAULT 0 COMMENT '현재 단계',
  `total_steps` int NOT NULL COMMENT '전체 단계 수',
  `saga_data` json DEFAULT NULL COMMENT 'Saga 상태 데이터',
  `error_message` text DEFAULT NULL COMMENT '에러 메시지',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `completed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`saga_id`),
  KEY `idx_saga_type_status` (`saga_type`, `status`),
  KEY `idx_initiator_id` (`initiator_id`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Saga 인스턴스 관리 테이블 (샤드별)';

-- Saga 단계 실행 기록 테이블 (Shard 2)
CREATE TABLE IF NOT EXISTS `saga_steps` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `saga_id` varchar(36) NOT NULL COMMENT 'Saga 인스턴스 ID',
  `step_number` int NOT NULL COMMENT '단계 번호',
  `step_name` varchar(100) NOT NULL COMMENT '단계 이름',
  `status` enum('pending','completed','failed','compensated') NOT NULL DEFAULT 'pending',
  `request_data` json DEFAULT NULL COMMENT '요청 데이터',
  `response_data` json DEFAULT NULL COMMENT '응답 데이터',
  `error_message` text DEFAULT NULL COMMENT '에러 메시지',
  `started_at` datetime DEFAULT NULL,
  `completed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_saga_step` (`saga_id`, `step_number`),
  KEY `idx_saga_id` (`saga_id`),
  KEY `idx_status` (`status`),
  FOREIGN KEY (`saga_id`) REFERENCES `saga_instances`(`saga_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Saga 단계 실행 기록 테이블 (샤드별)';

-- Shard 2용 계좌 생성 프로시저
DROP PROCEDURE IF EXISTS `fp_create_account`;
DELIMITER ;;
CREATE PROCEDURE `fp_create_account`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_account_type VARCHAR(20)
)
BEGIN
    DECLARE v_account_number VARCHAR(20);
    DECLARE v_result VARCHAR(20) DEFAULT 'FAILED';
    DECLARE v_existing_count INT DEFAULT 0;
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
    
    -- 기존 계좌 확인 (account_db_key만으로 체크)
    SELECT COUNT(*) INTO v_existing_count
    FROM table_user_accounts 
    WHERE account_db_key = p_account_db_key;
    
    IF v_existing_count > 0 THEN
        SELECT 'EXISTS' as result, 
               account_number
        FROM table_user_accounts 
        WHERE account_db_key = p_account_db_key
        LIMIT 1;
    ELSE
        -- 계좌번호 생성 (shard_id + timestamp + account_db_key 조합)
        SET v_account_number = CONCAT('2', UNIX_TIMESTAMP(), LPAD(p_account_db_key % 10000, 4, '0'));
        
        INSERT INTO table_user_accounts (account_db_key, account_number, account_type)
        VALUES (p_account_db_key, v_account_number, p_account_type);
        
        IF ROW_COUNT() > 0 THEN
            SET v_result = 'SUCCESS';
        END IF;
        
        SELECT v_result as result, v_account_number as account_number;
    END IF;
    
END ;;
DELIMITER ;

-- Shard 2용 계좌 정보 조회 프로시저
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

-- =====================================
-- 사용자 알림 설정 조회 (SignalMonitoringService용)
-- 목적: 시그널 발생 시 사용자별 알림 채널 결정을 위한 설정 조회
-- =====================================
USE finance_global;
DROP PROCEDURE IF EXISTS `fp_get_user_notification_settings`;
DELIMITER ;;
CREATE PROCEDURE `fp_get_user_notification_settings`(
    IN p_account_db_key BIGINT UNSIGNED
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    SET ProcParam = CONCAT('account_db_key=', IFNULL(p_account_db_key, 'NULL'));
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_get_user_notification_settings', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        SELECT 1 as ErrorCode, @ErrorMessage as ErrorMessage;
    END;
    
    -- 파라미터 검증
    IF p_account_db_key IS NULL OR p_account_db_key = 0 THEN
        SELECT 1 as ErrorCode, 'account_db_key parameter is required' as ErrorMessage;
        LEAVE;
    END IF;
    
    -- 상태 반환
    SELECT 0 as ErrorCode, 'SUCCESS' as ErrorMessage;
    
    -- 사용자 알림 설정 조회 (기본값: 모두 OFF - 사용자가 명시적으로 켜야 함)
    SELECT 
        p_account_db_key as account_db_key,
        COALESCE(p.email_notifications_enabled, 0) as email_notifications_enabled,    -- 기본: OFF
        COALESCE(p.sms_notifications_enabled, 0) as sms_notifications_enabled,        -- 기본: OFF
        COALESCE(p.push_notifications_enabled, 0) as push_notifications_enabled,      -- 기본: OFF
        COALESCE(p.price_alert_enabled, 0) as price_alert_enabled,                    -- 기본: OFF
        COALESCE(p.trade_alert_enabled, 0) as trade_alert_enabled,                    -- 기본: OFF
        COALESCE(p.news_alert_enabled, 0) as news_alert_enabled,                      -- 기본: OFF
        COALESCE(p.portfolio_alert_enabled, 0) as portfolio_alert_enabled             -- 기본: OFF
    FROM table_user_profiles p
    WHERE p.account_db_key = p_account_db_key
    
    UNION ALL
    
    -- 프로필이 없는 경우 기본값 반환 (모두 OFF)
    SELECT 
        p_account_db_key as account_db_key,
        0 as email_notifications_enabled,    -- 기본: OFF
        0 as sms_notifications_enabled,      -- 기본: OFF  
        0 as push_notifications_enabled,     -- 기본: OFF
        0 as price_alert_enabled,            -- 기본: OFF
        0 as trade_alert_enabled,            -- 기본: OFF
        0 as news_alert_enabled,             -- 기본: OFF
        0 as portfolio_alert_enabled         -- 기본: OFF
    WHERE NOT EXISTS (
        SELECT 1 FROM table_user_profiles 
        WHERE account_db_key = p_account_db_key
    )
    LIMIT 1;  -- 중복 방지
    
END ;;
DELIMITER ;

-- =====================================
-- 사용자 연락처 정보 조회 (알림 발송용)
-- 목적: 이메일/SMS 발송을 위한 사용자 연락처 정보 조회
-- =====================================
USE finance_global;
DROP PROCEDURE IF EXISTS `fp_get_user_contact_info`;
DELIMITER ;;
CREATE PROCEDURE `fp_get_user_contact_info`(
    IN p_account_db_key BIGINT UNSIGNED
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    SET ProcParam = CONCAT('account_db_key=', IFNULL(p_account_db_key, 'NULL'));
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_get_user_contact_info', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        SELECT 1 as ErrorCode, @ErrorMessage as ErrorMessage;
    END;
    
    -- 파라미터 검증
    IF p_account_db_key IS NULL OR p_account_db_key = 0 THEN
        SELECT 1 as ErrorCode, 'account_db_key parameter is required' as ErrorMessage;
        LEAVE;
    END IF;
    
    -- 상태 반환
    SELECT 0 as ErrorCode, 'SUCCESS' as ErrorMessage;
    
    -- 사용자 연락처 정보 조회
    SELECT 
        a.account_db_key,
        a.email,
        a.phone_number,
        a.nickname,
        a.account_status
    FROM table_accountid a
    WHERE a.account_db_key = p_account_db_key
    AND a.account_status = 'Normal'
    LIMIT 1;
    
END ;;
DELIMITER ;

-- =====================================
-- 활성 샤드 목록 조회 프로시저 (SignalMonitoringService용)
-- 목적: 하드코딩된 샤드 순회 대신 동적으로 활성 샤드 목록 조회
-- =====================================
USE finance_global;
DROP PROCEDURE IF EXISTS `fp_get_active_shard_ids`;
DELIMITER ;;
CREATE PROCEDURE `fp_get_active_shard_ids`()
BEGIN
    DECLARE ProcParam VARCHAR(4000) DEFAULT '';
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_get_active_shard_ids', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        SELECT 1 as ErrorCode, @ErrorMessage as ErrorMessage;
    END;
    
    -- 상태 반환
    SELECT 0 as ErrorCode, 'SUCCESS' as ErrorMessage;
    
    -- 활성 샤드 ID 목록 조회 (status가 'active'인 샤드만)
    SELECT 
        shard_id,
        shard_name,
        host,
        port,
        database_name,
        status,
        max_connections
    FROM table_shard_config 
    WHERE status = 'active'
    ORDER BY shard_id;
    
END ;;
DELIMITER ;

-- =====================================
-- 샤드 상태 업데이트 프로시저 (운영용)
-- 목적: 샤드 상태를 동적으로 변경 (maintenance, disabled 등)
-- =====================================
USE finance_global;
DROP PROCEDURE IF EXISTS `fp_update_shard_status`;
DELIMITER ;;
CREATE PROCEDURE `fp_update_shard_status`(
    IN p_shard_id INT,
    IN p_status VARCHAR(20)
)
BEGIN
    DECLARE v_affected_rows INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    SET ProcParam = CONCAT('shard_id=', IFNULL(p_shard_id, 'NULL'), ', status=', IFNULL(p_status, 'NULL'));
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_update_shard_status', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        SELECT 1 as ErrorCode, @ErrorMessage as ErrorMessage;
    END;
    
    -- 파라미터 검증
    IF p_shard_id IS NULL OR p_shard_id <= 0 THEN
        SELECT 1 as ErrorCode, 'shard_id parameter is required and must be positive' as ErrorMessage;
        LEAVE;
    END IF;
    
    IF p_status NOT IN ('active', 'maintenance', 'disabled') THEN
        SELECT 1 as ErrorCode, 'status must be one of: active, maintenance, disabled' as ErrorMessage;
        LEAVE;
    END IF;
    
    START TRANSACTION;
    
    -- 샤드 상태 업데이트
    UPDATE table_shard_config 
    SET status = p_status,
        updated_at = NOW()
    WHERE shard_id = p_shard_id;
    
    SET v_affected_rows = ROW_COUNT();
    
    IF v_affected_rows = 0 THEN
        ROLLBACK;
        SELECT 1 as ErrorCode, CONCAT('Shard not found: ', p_shard_id) as ErrorMessage;
    ELSE
        COMMIT;
        SELECT 0 as ErrorCode, 
               CONCAT('Shard ', p_shard_id, ' status updated to: ', p_status) as ErrorMessage,
               v_affected_rows as affected_rows;
    END IF;
    
END ;;
DELIMITER ;

-- 최종 상태 확인
USE finance_global;
SELECT 'Finance DB 재생성 완료 - 샤드 동적 관리 프로시저 추가됨' as status;