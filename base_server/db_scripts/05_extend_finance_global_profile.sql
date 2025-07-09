-- =====================================
-- Finance Global DB 프로필 및 세션 관리 확장
-- 패킷명세서 기반: REQ-AUTH-009, 프로필 설정
-- =====================================

USE finance_global;

-- 1. 사용자 프로필 테이블
CREATE TABLE IF NOT EXISTS `table_user_profiles` (
  `account_db_key` bigint unsigned NOT NULL,
  `investment_experience` enum('BEGINNER','INTERMEDIATE','EXPERT') DEFAULT 'BEGINNER',
  `risk_tolerance` enum('CONSERVATIVE','MODERATE','AGGRESSIVE') DEFAULT 'MODERATE',
  `investment_goal` enum('GROWTH','INCOME','PRESERVATION') DEFAULT 'GROWTH',
  `monthly_budget` decimal(15,2) DEFAULT 0.00,
  `profile_completed` bit(1) NOT NULL DEFAULT b'0',
  `birth_year` int DEFAULT NULL,
  `birth_month` int DEFAULT NULL,
  `birth_day` int DEFAULT NULL,
  `gender` enum('M','F','OTHER') DEFAULT NULL,
  `country` varchar(10) DEFAULT 'KR',
  `timezone` varchar(50) DEFAULT 'Asia/Seoul',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`account_db_key`),
  FOREIGN KEY (`account_db_key`) REFERENCES `table_accountid`(`account_db_key`) ON DELETE CASCADE,
  INDEX `idx_investment_experience` (`investment_experience`),
  INDEX `idx_risk_tolerance` (`risk_tolerance`),
  INDEX `idx_profile_completed` (`profile_completed`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 2. 세션 관리 테이블
CREATE TABLE IF NOT EXISTS `table_user_sessions` (
  `session_id` varchar(255) NOT NULL,
  `account_db_key` bigint unsigned NOT NULL,
  `access_token` varchar(512) NOT NULL,
  `refresh_token` varchar(512) DEFAULT NULL,
  `device_info` text,  -- JSON 형태로 디바이스 정보 저장
  `ip_address` varchar(45),
  `user_agent` text,
  `last_activity` datetime DEFAULT CURRENT_TIMESTAMP,
  `expires_at` datetime NOT NULL,
  `is_active` bit(1) NOT NULL DEFAULT b'1',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`session_id`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_access_token` (`access_token`(255)),
  INDEX `idx_expires_at` (`expires_at`),
  INDEX `idx_is_active` (`is_active`),
  FOREIGN KEY (`account_db_key`) REFERENCES `table_accountid`(`account_db_key`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 3. 튜토리얼 진행 상태 테이블
CREATE TABLE IF NOT EXISTS `table_tutorial_progress` (
  `account_db_key` bigint unsigned NOT NULL,
  `tutorial_type` varchar(50) NOT NULL,
  `current_step` int DEFAULT 0,
  `total_steps` int DEFAULT 0,
  `is_completed` bit(1) NOT NULL DEFAULT b'0',
  `completion_rate` decimal(5,2) DEFAULT 0.00,
  `time_spent` int DEFAULT 0,  -- 초 단위
  `started_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `completed_at` datetime DEFAULT NULL,
  `last_updated` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`account_db_key`, `tutorial_type`),
  FOREIGN KEY (`account_db_key`) REFERENCES `table_accountid`(`account_db_key`) ON DELETE CASCADE,
  INDEX `idx_tutorial_type` (`tutorial_type`),
  INDEX `idx_is_completed` (`is_completed`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 4. 사용자 설정 테이블
CREATE TABLE IF NOT EXISTS `table_user_settings` (
  `account_db_key` bigint unsigned NOT NULL,
  `setting_key` varchar(100) NOT NULL,
  `setting_value` text,
  `setting_type` enum('STRING','NUMBER','BOOLEAN','JSON') DEFAULT 'STRING',
  `is_system` bit(1) NOT NULL DEFAULT b'0',  -- 시스템 설정 여부
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`account_db_key`, `setting_key`),
  FOREIGN KEY (`account_db_key`) REFERENCES `table_accountid`(`account_db_key`) ON DELETE CASCADE,
  INDEX `idx_setting_key` (`setting_key`),
  INDEX `idx_is_system` (`is_system`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- =====================================
-- 프로필 관련 프로시저
-- =====================================

-- 프로필 설정 생성/업데이트
DROP PROCEDURE IF EXISTS `fp_profile_setup`;
DELIMITER ;;
CREATE PROCEDURE `fp_profile_setup`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_investment_experience VARCHAR(20),
    IN p_risk_tolerance VARCHAR(20),
    IN p_investment_goal VARCHAR(20),
    IN p_monthly_budget DECIMAL(15,2),
    IN p_birth_year INT,
    IN p_birth_month INT,
    IN p_birth_day INT,
    IN p_gender VARCHAR(10)
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
            birth_year = p_birth_year,
            birth_month = p_birth_month,
            birth_day = p_birth_day,
            gender = p_gender,
            profile_completed = 1,
            updated_at = NOW()
        WHERE account_db_key = p_account_db_key;
    ELSE
        -- 새 프로필 생성
        INSERT INTO table_user_profiles (
            account_db_key, investment_experience, risk_tolerance, 
            investment_goal, monthly_budget, birth_year, birth_month, 
            birth_day, gender, profile_completed
        ) VALUES (
            p_account_db_key, p_investment_experience, p_risk_tolerance,
            p_investment_goal, p_monthly_budget, p_birth_year, p_birth_month,
            p_birth_day, p_gender, 1
        );
    END IF;
    
    SELECT 'SUCCESS' as result, 'Profile setup completed' as message;
    
END ;;
DELIMITER ;

-- 프로필 조회
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
    
    SELECT 
        a.account_db_key,
        a.platform_type,
        a.account_id,
        a.nickname,
        a.email,
        a.account_level,
        COALESCE(sm.shard_id, 0) as shard_id,
        COALESCE(p.investment_experience, 'BEGINNER') as investment_experience,
        COALESCE(p.risk_tolerance, 'MODERATE') as risk_tolerance,
        COALESCE(p.investment_goal, 'GROWTH') as investment_goal,
        COALESCE(p.monthly_budget, 0.00) as monthly_budget,
        COALESCE(p.profile_completed, 0) as profile_completed,
        p.birth_year,
        p.birth_month,
        p.birth_day,
        p.gender,
        p.country,
        p.timezone
    FROM table_accountid a
    LEFT JOIN table_user_profiles p ON a.account_db_key = p.account_db_key
    LEFT JOIN table_user_shard_mapping sm ON a.account_db_key = sm.account_db_key
    WHERE a.account_db_key = p_account_db_key;
    
END ;;
DELIMITER ;

-- 프로필 부분 업데이트
DROP PROCEDURE IF EXISTS `fp_profile_update`;
DELIMITER ;;
CREATE PROCEDURE `fp_profile_update`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_field_name VARCHAR(50),
    IN p_field_value TEXT
)
BEGIN
    DECLARE v_existing_count INT DEFAULT 0;
    DECLARE v_sql_query TEXT;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_field_name, ',', p_field_value);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_profile_update', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
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
    
    -- 필드별 업데이트 처리
    update_block: BEGIN
        CASE p_field_name
            WHEN 'nickname' THEN
                UPDATE table_accountid SET nickname = p_field_value WHERE account_db_key = p_account_db_key;
            WHEN 'investment_experience' THEN
                UPDATE table_user_profiles SET investment_experience = p_field_value WHERE account_db_key = p_account_db_key;
            WHEN 'risk_tolerance' THEN
                UPDATE table_user_profiles SET risk_tolerance = p_field_value WHERE account_db_key = p_account_db_key;
            WHEN 'investment_goal' THEN
                UPDATE table_user_profiles SET investment_goal = p_field_value WHERE account_db_key = p_account_db_key;
            WHEN 'monthly_budget' THEN
                UPDATE table_user_profiles SET monthly_budget = CAST(p_field_value AS DECIMAL(15,2)) WHERE account_db_key = p_account_db_key;
            ELSE
                SELECT 'FAILED' as result, 'Invalid field name' as message;
                LEAVE update_block;
        END CASE;
        
        SELECT 'SUCCESS' as result, 'Profile updated successfully' as message;
    END update_block;
    
END ;;
DELIMITER ;

-- =====================================
-- 세션 관리 프로시저
-- =====================================

-- 세션 생성
DROP PROCEDURE IF EXISTS `fp_session_create`;
DELIMITER ;;
CREATE PROCEDURE `fp_session_create`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_access_token VARCHAR(512),
    IN p_refresh_token VARCHAR(512),
    IN p_device_info TEXT,
    IN p_ip_address VARCHAR(45),
    IN p_user_agent TEXT,
    IN p_expires_minutes INT
)
BEGIN
    DECLARE v_session_id VARCHAR(255);
    DECLARE v_expires_at DATETIME;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_access_token);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_session_create', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 세션 ID 생성
    SET v_session_id = CONCAT(
        'sess_',
        LPAD(HEX(p_account_db_key), 16, '0'),
        '_',
        LPAD(HEX(UNIX_TIMESTAMP()), 8, '0'),
        '_',
        LPAD(HEX(FLOOR(RAND() * 65535)), 4, '0')
    );
    
    SET v_expires_at = DATE_ADD(NOW(), INTERVAL p_expires_minutes MINUTE);
    
    -- 기존 활성 세션 비활성화
    UPDATE table_user_sessions 
    SET is_active = 0
    WHERE account_db_key = p_account_db_key AND is_active = 1;
    
    -- 새 세션 생성
    INSERT INTO table_user_sessions (
        session_id, account_db_key, access_token, refresh_token,
        device_info, ip_address, user_agent, expires_at
    ) VALUES (
        v_session_id, p_account_db_key, p_access_token, p_refresh_token,
        p_device_info, p_ip_address, p_user_agent, v_expires_at
    );
    
    SELECT 'SUCCESS' as result, v_session_id as session_id, v_expires_at as expires_at;
    
END ;;
DELIMITER ;

-- 세션 검증
DROP PROCEDURE IF EXISTS `fp_session_validate`;
DELIMITER ;;
CREATE PROCEDURE `fp_session_validate`(
    IN p_access_token VARCHAR(512)
)
BEGIN
    DECLARE v_account_db_key BIGINT UNSIGNED DEFAULT 0;
    DECLARE v_session_id VARCHAR(255) DEFAULT '';
    DECLARE v_is_valid BIT(1) DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_access_token);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_session_validate', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 세션 검증
    SELECT account_db_key, session_id INTO v_account_db_key, v_session_id
    FROM table_user_sessions 
    WHERE access_token = p_access_token 
      AND is_active = 1 
      AND expires_at > NOW();
    
    IF v_account_db_key > 0 THEN
        -- 세션 활동 시간 업데이트
        UPDATE table_user_sessions 
        SET last_activity = NOW()
        WHERE session_id = v_session_id;
        
        SELECT 'SUCCESS' as result, v_account_db_key as account_db_key, v_session_id as session_id;
    ELSE
        SELECT 'FAILED' as result, 0 as account_db_key, '' as session_id;
    END IF;
    
END ;;
DELIMITER ;

-- 토큰 갱신
DROP PROCEDURE IF EXISTS `fp_session_refresh`;
DELIMITER ;;
CREATE PROCEDURE `fp_session_refresh`(
    IN p_refresh_token VARCHAR(512),
    IN p_new_access_token VARCHAR(512),
    IN p_new_refresh_token VARCHAR(512),
    IN p_expires_minutes INT
)
BEGIN
    DECLARE v_account_db_key BIGINT UNSIGNED DEFAULT 0;
    DECLARE v_session_id VARCHAR(255) DEFAULT '';
    DECLARE v_expires_at DATETIME;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_refresh_token, ',', p_new_access_token);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_session_refresh', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- Refresh Token 검증
    SELECT account_db_key, session_id INTO v_account_db_key, v_session_id
    FROM table_user_sessions 
    WHERE refresh_token = p_refresh_token 
      AND is_active = 1 
      AND expires_at > NOW();
    
    IF v_account_db_key > 0 THEN
        SET v_expires_at = DATE_ADD(NOW(), INTERVAL p_expires_minutes MINUTE);
        
        -- 토큰 갱신
        UPDATE table_user_sessions 
        SET access_token = p_new_access_token,
            refresh_token = p_new_refresh_token,
            expires_at = v_expires_at,
            last_activity = NOW()
        WHERE session_id = v_session_id;
        
        SELECT 'SUCCESS' as result, v_account_db_key as account_db_key, v_expires_at as expires_at;
    ELSE
        SELECT 'FAILED' as result, 0 as account_db_key, NULL as expires_at;
    END IF;
    
END ;;
DELIMITER ;

-- =====================================
-- 튜토리얼 진행 상태 프로시저
-- =====================================

-- 튜토리얼 진행 상태 업데이트
DROP PROCEDURE IF EXISTS `fp_tutorial_update_progress`;
DELIMITER ;;
CREATE PROCEDURE `fp_tutorial_update_progress`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_tutorial_type VARCHAR(50),
    IN p_current_step INT,
    IN p_total_steps INT,
    IN p_time_spent INT
)
BEGIN
    DECLARE v_existing_count INT DEFAULT 0;
    DECLARE v_completion_rate DECIMAL(5,2);
    DECLARE v_is_completed BIT(1) DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_tutorial_type, ',', p_current_step);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_tutorial_update_progress', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 진행률 계산
    SET v_completion_rate = (p_current_step / p_total_steps) * 100;
    SET v_is_completed = IF(p_current_step >= p_total_steps, 1, 0);
    
    -- 기존 진행 상태 확인
    SELECT COUNT(*) INTO v_existing_count
    FROM table_tutorial_progress 
    WHERE account_db_key = p_account_db_key AND tutorial_type = p_tutorial_type;
    
    IF v_existing_count > 0 THEN
        -- 기존 진행 상태 업데이트
        UPDATE table_tutorial_progress 
        SET current_step = p_current_step,
            total_steps = p_total_steps,
            completion_rate = v_completion_rate,
            is_completed = v_is_completed,
            time_spent = time_spent + p_time_spent,
            completed_at = IF(v_is_completed = 1, NOW(), completed_at),
            last_updated = NOW()
        WHERE account_db_key = p_account_db_key AND tutorial_type = p_tutorial_type;
    ELSE
        -- 새 진행 상태 생성
        INSERT INTO table_tutorial_progress (
            account_db_key, tutorial_type, current_step, total_steps,
            completion_rate, is_completed, time_spent,
            completed_at
        ) VALUES (
            p_account_db_key, p_tutorial_type, p_current_step, p_total_steps,
            v_completion_rate, v_is_completed, p_time_spent,
            IF(v_is_completed = 1, NOW(), NULL)
        );
    END IF;
    
    SELECT 'SUCCESS' as result, v_completion_rate as completion_rate, v_is_completed as is_completed;
    
END ;;
DELIMITER ;

-- =====================================
-- 기본 설정 데이터 삽입
-- =====================================

-- 기본 사용자 설정 템플릿 생성 함수
DROP PROCEDURE IF EXISTS `fp_initialize_default_settings`;
DELIMITER ;;
CREATE PROCEDURE `fp_initialize_default_settings`(
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
            VALUES ('fp_initialize_default_settings', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 기본 설정 삽입
    INSERT INTO table_user_settings (account_db_key, setting_key, setting_value, setting_type) 
    VALUES 
    (p_account_db_key, 'theme', 'DARK', 'STRING'),
    (p_account_db_key, 'language', 'KO', 'STRING'),
    (p_account_db_key, 'currency', 'KRW', 'STRING'),
    (p_account_db_key, 'chart_style', 'CANDLE', 'STRING'),
    (p_account_db_key, 'price_alerts', 'true', 'BOOLEAN'),
    (p_account_db_key, 'news_alerts', 'true', 'BOOLEAN'),
    (p_account_db_key, 'portfolio_alerts', 'false', 'BOOLEAN'),
    (p_account_db_key, 'trade_alerts', 'true', 'BOOLEAN'),
    (p_account_db_key, 'session_timeout', '30', 'NUMBER'),
    (p_account_db_key, 'auto_trading_enabled', 'false', 'BOOLEAN')
    ON DUPLICATE KEY UPDATE 
        setting_value = VALUES(setting_value),
        updated_at = NOW();
    
    SELECT 'SUCCESS' as result, 'Default settings initialized' as message;
    
END ;;
DELIMITER ;

SELECT 'Finance Global DB 프로필 및 세션 관리 확장 완료' as status;