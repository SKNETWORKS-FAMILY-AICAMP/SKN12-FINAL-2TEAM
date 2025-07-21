-- =====================================
-- 옵션 1 프로필 데이터 마이그레이션 (기존 데이터 삭제)
-- 목표: 생년월일/성별 정보는 회원가입 시에만 수집, 프로필 설정은 투자 정보만 처리
-- =====================================

USE finance_global;

-- 1. 기존 프로필 테이블 데이터 삭제
TRUNCATE TABLE table_user_profiles;

-- 2. 프로필 테이블 구조 변경 (생년월일/성별 컬럼 제거, 오류 무시)
SET @sql = '';
SELECT IF(
    EXISTS(
        SELECT * FROM information_schema.columns 
        WHERE table_schema = 'finance_global' 
        AND table_name = 'table_user_profiles' 
        AND column_name = 'birth_year'
    ),
    'ALTER TABLE `table_user_profiles` DROP COLUMN `birth_year`;',
    'SELECT "Column birth_year does not exist" as message;'
) INTO @sql;
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SELECT IF(
    EXISTS(
        SELECT * FROM information_schema.columns 
        WHERE table_schema = 'finance_global' 
        AND table_name = 'table_user_profiles' 
        AND column_name = 'birth_month'
    ),
    'ALTER TABLE `table_user_profiles` DROP COLUMN `birth_month`;',
    'SELECT "Column birth_month does not exist" as message;'
) INTO @sql;
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SELECT IF(
    EXISTS(
        SELECT * FROM information_schema.columns 
        WHERE table_schema = 'finance_global' 
        AND table_name = 'table_user_profiles' 
        AND column_name = 'birth_day'
    ),
    'ALTER TABLE `table_user_profiles` DROP COLUMN `birth_day`;',
    'SELECT "Column birth_day does not exist" as message;'
) INTO @sql;
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SELECT IF(
    EXISTS(
        SELECT * FROM information_schema.columns 
        WHERE table_schema = 'finance_global' 
        AND table_name = 'table_user_profiles' 
        AND column_name = 'gender'
    ),
    'ALTER TABLE `table_user_profiles` DROP COLUMN `gender`;',
    'SELECT "Column gender does not exist" as message;'
) INTO @sql;
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 3. account 테이블에 생년월일/성별 컬럼 추가 (존재하지 않는 경우만)
SET @sql = '';
SELECT IF(
    NOT EXISTS(
        SELECT * FROM information_schema.columns 
        WHERE table_schema = 'finance_global' 
        AND table_name = 'table_accountid' 
        AND column_name = 'birth_year'
    ),
    'ALTER TABLE `table_accountid` ADD COLUMN `birth_year` INT DEFAULT NULL AFTER `email`;',
    'SELECT "Column birth_year already exists" as message;'
) INTO @sql;
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SELECT IF(
    NOT EXISTS(
        SELECT * FROM information_schema.columns 
        WHERE table_schema = 'finance_global' 
        AND table_name = 'table_accountid' 
        AND column_name = 'birth_month'
    ),
    'ALTER TABLE `table_accountid` ADD COLUMN `birth_month` INT DEFAULT NULL AFTER `birth_year`;',
    'SELECT "Column birth_month already exists" as message;'
) INTO @sql;
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SELECT IF(
    NOT EXISTS(
        SELECT * FROM information_schema.columns 
        WHERE table_schema = 'finance_global' 
        AND table_name = 'table_accountid' 
        AND column_name = 'birth_day'
    ),
    'ALTER TABLE `table_accountid` ADD COLUMN `birth_day` INT DEFAULT NULL AFTER `birth_month`;',
    'SELECT "Column birth_day already exists" as message;'
) INTO @sql;
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SELECT IF(
    NOT EXISTS(
        SELECT * FROM information_schema.columns 
        WHERE table_schema = 'finance_global' 
        AND table_name = 'table_accountid' 
        AND column_name = 'gender'
    ),
    'ALTER TABLE `table_accountid` ADD COLUMN `gender` ENUM("M","F","OTHER") DEFAULT NULL AFTER `birth_day`;',
    'SELECT "Column gender already exists" as message;'
) INTO @sql;
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 4. 회원가입 프로시저 수정 (생년월일, 성별 포함)
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
        SELECT 'FAILED' as result, 'Account or email already exists' as message, 0 as account_db_key;
    ELSE
        -- 계정 생성 (생년월일, 성별 포함)
        INSERT INTO table_accountid (
            platform_type, account_id, password_hash, email, nickname,
            birth_year, birth_month, birth_day, gender, account_status
        ) VALUES (
            p_platform_type, p_account_id, p_password_hash, p_email, p_nickname,
            p_birth_year, p_birth_month, p_birth_day, p_gender, 'Normal'
        );
        
        SET v_account_db_key = LAST_INSERT_ID();
        
        SELECT 'SUCCESS' as result, 'User signup completed' as message, v_account_db_key as account_db_key;
    END IF;
    
END ;;
DELIMITER ;

-- 5. 프로필 설정 프로시저 수정 (생년월일, 성별 파라미터 제거)
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
        -- 기존 프로필 업데이트 (투자 정보만 업데이트)
        UPDATE table_user_profiles 
        SET investment_experience = p_investment_experience,
            risk_tolerance = p_risk_tolerance,
            investment_goal = p_investment_goal,
            monthly_budget = p_monthly_budget,
            profile_completed = 1,
            updated_at = NOW()
        WHERE account_db_key = p_account_db_key;
    ELSE
        -- 새 프로필 생성 (투자 정보만 설정)
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

-- 6. 프로필 조회 프로시저 수정 (account 테이블에서 생년월일/성별 조회)
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

-- 7. 프로필 부분 업데이트 프로시저 수정
DROP PROCEDURE IF EXISTS `fp_profile_update`;
DELIMITER ;;
CREATE PROCEDURE `fp_profile_update`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_field_name VARCHAR(50),
    IN p_field_value TEXT
)
BEGIN
    DECLARE v_existing_count INT DEFAULT 0;
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
            -- 생년월일/성별 업데이트는 account 테이블에서 처리
            WHEN 'birth_year' THEN
                UPDATE table_accountid SET birth_year = CAST(p_field_value AS SIGNED) WHERE account_db_key = p_account_db_key;
            WHEN 'birth_month' THEN
                UPDATE table_accountid SET birth_month = CAST(p_field_value AS SIGNED) WHERE account_db_key = p_account_db_key;
            WHEN 'birth_day' THEN
                UPDATE table_accountid SET birth_day = CAST(p_field_value AS SIGNED) WHERE account_db_key = p_account_db_key;
            WHEN 'gender' THEN
                UPDATE table_accountid SET gender = p_field_value WHERE account_db_key = p_account_db_key;
            ELSE
                SELECT 'FAILED' as result, 'Invalid field name' as message;
                LEAVE update_block;
        END CASE;
        
        SELECT 'SUCCESS' as result, 'Profile updated successfully' as message;
    END update_block;
    
END ;;
DELIMITER ;

-- 8. 인덱스 추가 (account 테이블에 새로 추가된 컬럼들에 대한 인덱스, 존재하지 않는 경우만)
SET @sql = '';
SELECT IF(
    NOT EXISTS(
        SELECT * FROM information_schema.statistics 
        WHERE table_schema = 'finance_global' 
        AND table_name = 'table_accountid' 
        AND index_name = 'idx_birth_year'
    ),
    'ALTER TABLE `table_accountid` ADD INDEX `idx_birth_year` (`birth_year`);',
    'SELECT "Index idx_birth_year already exists" as message;'
) INTO @sql;
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SELECT IF(
    NOT EXISTS(
        SELECT * FROM information_schema.statistics 
        WHERE table_schema = 'finance_global' 
        AND table_name = 'table_accountid' 
        AND index_name = 'idx_gender'
    ),
    'ALTER TABLE `table_accountid` ADD INDEX `idx_gender` (`gender`);',
    'SELECT "Index idx_gender already exists" as message;'
) INTO @sql;
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SELECT 'Option 1 Profile Migration Completed - Birth info moved to signup, profile setup only handles investment data' as status;