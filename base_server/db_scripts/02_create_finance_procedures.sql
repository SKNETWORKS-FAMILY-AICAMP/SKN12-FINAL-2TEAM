-- =====================================
-- Finance Global DB 스토어드 프로시저 (game_server 방식 적용)
-- =====================================

USE finance_global;

-- 1. 사용자 로그인 프로시저 (game_server gp_auser_login 방식)
DROP PROCEDURE IF EXISTS `fp_user_login`;
DELIMITER ;;
CREATE PROCEDURE `fp_user_login`(
    IN p_platform_type TINYINT,
    IN p_account_id VARCHAR(100),
    IN p_password_hash VARCHAR(255)
)
BEGIN
    DECLARE v_account_db_key BIGINT UNSIGNED DEFAULT 0;
    DECLARE v_account_status VARCHAR(15) DEFAULT '';
    DECLARE v_shard_id INT DEFAULT 0;
    DECLARE v_result VARCHAR(20) DEFAULT 'FAILED';
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_platform_type, ',', p_account_id, ',', p_password_hash);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_user_login', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 계정 정보 조회
    SELECT account_db_key, account_status INTO v_account_db_key, v_account_status
    FROM table_accountid 
    WHERE platform_type = p_platform_type 
      AND account_id = p_account_id 
      AND password_hash = p_password_hash;
    
    -- 로그인 성공 처리
    IF v_account_db_key > 0 AND v_account_status = 'Normal' THEN
        SET v_result = 'SUCCESS';
        
        -- 로그인 시간 업데이트
        UPDATE table_accountid
        SET login_time = NOW()
        WHERE account_db_key = v_account_db_key;
        
        -- 사용자 샤드 조회 (없으면 자동 할당)
        SELECT shard_id INTO v_shard_id
        FROM table_user_shard_mapping 
        WHERE account_db_key = v_account_db_key;
        
        -- 샤드가 없으면 자동 할당
        IF v_shard_id IS NULL OR v_shard_id = 0 THEN
            SET v_shard_id = (v_account_db_key % 2) + 1;  -- 1 또는 2
            
            INSERT INTO table_user_shard_mapping (account_db_key, shard_id)
            VALUES (v_account_db_key, v_shard_id)
            ON DUPLICATE KEY UPDATE 
                shard_id = v_shard_id,
                updated_at = NOW();
                
            -- 샤드 통계 업데이트
            UPDATE table_shard_stats 
            SET user_count = user_count + 1, last_updated = NOW()
            WHERE shard_id = v_shard_id;
        END IF;
        
        -- 로그인 결과 반환
        SELECT 
            v_result as result,
            v_account_db_key as account_db_key,
            nickname,
            account_level,
            v_shard_id as shard_id
        FROM table_accountid 
        WHERE account_db_key = v_account_db_key;
        
    ELSEIF v_account_db_key > 0 AND v_account_status != 'Normal' THEN
        SELECT 'BLOCKED' as result, 0 as account_db_key, '' as nickname, 0 as account_level, 0 as shard_id;
    ELSE
        SELECT 'FAILED' as result, 0 as account_db_key, '' as nickname, 0 as account_level, 0 as shard_id;
    END IF;
    
END ;;
DELIMITER ;

-- 2. 사용자 회원가입 프로시저
DROP PROCEDURE IF EXISTS `fp_user_register`;
DELIMITER ;;
CREATE PROCEDURE `fp_user_register`(
    IN p_platform_type TINYINT,
    IN p_account_id VARCHAR(100),
    IN p_password_hash VARCHAR(255),
    IN p_nickname VARCHAR(50),
    IN p_email VARCHAR(100)
)
BEGIN
    DECLARE v_account_db_key BIGINT UNSIGNED DEFAULT 0;
    DECLARE v_duplicate_count INT DEFAULT 0;
    DECLARE v_result VARCHAR(20) DEFAULT 'FAILED';
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_platform_type, ',', p_account_id, ',', p_password_hash, ',', p_nickname, ',', p_email);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_user_register', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 중복 체크
    SELECT COUNT(*) INTO v_duplicate_count
    FROM table_accountid 
    WHERE platform_type = p_platform_type AND account_id = p_account_id;
    
    IF v_duplicate_count > 0 THEN
        SELECT 'DUPLICATE_ID' as result, 0 as account_db_key;
    ELSE
        -- account_db_key 생성 (현재 시간 기반)
        SET v_account_db_key = UNIX_TIMESTAMP() * 1000 + CONNECTION_ID() % 1000;
        
        INSERT INTO table_accountid (
            platform_type, account_id, account_db_key, password_hash, nickname, email, login_count
        ) VALUES (
            p_platform_type, p_account_id, v_account_db_key, p_password_hash, p_nickname, p_email, 0
        );
        
        IF ROW_COUNT() > 0 THEN
            SELECT 'SUCCESS' as result, v_account_db_key as account_db_key;
        ELSE
            SELECT 'FAILED' as result, 0 as account_db_key;
        END IF;
    END IF;
    
END ;;
DELIMITER ;

-- 3. 사용자 로그아웃 프로시저
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

-- 4. 사용자 샤드 조회 프로시저
DROP PROCEDURE IF EXISTS `fp_get_user_shard`;
DELIMITER ;;
CREATE PROCEDURE `fp_get_user_shard`(
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
            VALUES ('fp_get_user_shard', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    SELECT 
        m.shard_id,
        c.host,
        c.port,
        c.database_name,
        c.status
    FROM table_user_shard_mapping m
    JOIN table_shard_config c ON m.shard_id = c.shard_id
    WHERE m.account_db_key = p_account_db_key;
    
END ;;
DELIMITER ;

-- 5. 사용자 정보 조회 프로시저
DROP PROCEDURE IF EXISTS `fp_get_user_info`;
DELIMITER ;;
CREATE PROCEDURE `fp_get_user_info`(
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
            VALUES ('fp_get_user_info', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    SELECT 
        account_db_key,
        platform_type,
        account_id,
        nickname,
        email,
        account_level,
        account_status,
        create_time,
        login_time
    FROM table_accountid 
    WHERE account_db_key = p_account_db_key;
    
END ;;
DELIMITER ;

SELECT 'Finance Global DB 프로시저 생성 완료' as status;