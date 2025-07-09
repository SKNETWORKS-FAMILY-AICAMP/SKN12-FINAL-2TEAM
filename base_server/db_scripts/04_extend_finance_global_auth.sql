-- =====================================
-- Finance Global DB 인증 확장 (이메일 인증, OTP)
-- 패킷명세서 기반: REQ-AUTH-008, REQ-AUTH-013~016
-- =====================================

USE finance_global;

-- 1. 이메일 인증 테이블
CREATE TABLE IF NOT EXISTS `table_email_verification` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `email` varchar(100) NOT NULL,
  `verification_code` varchar(10) NOT NULL,
  `account_id` varchar(100) DEFAULT NULL,
  `is_verified` bit(1) NOT NULL DEFAULT b'0',
  `attempts` int DEFAULT 0,
  `max_attempts` int DEFAULT 5,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `expires_at` datetime NOT NULL,
  `verified_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_email_active` (`email`, `is_verified`),
  INDEX `idx_email` (`email`),
  INDEX `idx_expires_at` (`expires_at`),
  INDEX `idx_account_id` (`account_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 2. OTP 정보 테이블
CREATE TABLE IF NOT EXISTS `table_otp_info` (
  `account_db_key` bigint unsigned NOT NULL,
  `secret_key` varchar(255) NOT NULL,
  `backup_codes` text,  -- JSON 형태로 저장
  `is_enabled` bit(1) NOT NULL DEFAULT b'0',
  `qr_code_url` text,
  `last_used_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`account_db_key`),
  FOREIGN KEY (`account_db_key`) REFERENCES `table_accountid`(`account_db_key`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 3. 임시 토큰 테이블 (2단계 로그인용)
CREATE TABLE IF NOT EXISTS `table_temp_tokens` (
  `temp_token` varchar(255) NOT NULL,
  `account_db_key` bigint unsigned NOT NULL,
  `account_id` varchar(100) NOT NULL,
  `token_type` enum('LOGIN_OTP', 'PASSWORD_RESET', 'EMAIL_CHANGE') DEFAULT 'LOGIN_OTP',
  `is_used` bit(1) NOT NULL DEFAULT b'0',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `expires_at` datetime NOT NULL,
  `used_at` datetime DEFAULT NULL,
  PRIMARY KEY (`temp_token`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_expires_at` (`expires_at`),
  FOREIGN KEY (`account_db_key`) REFERENCES `table_accountid`(`account_db_key`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 4. 인증 시도 로그 테이블
CREATE TABLE IF NOT EXISTS `table_auth_attempts` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `account_id` varchar(100) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `attempt_type` enum('LOGIN', 'EMAIL_VERIFY', 'OTP_VERIFY', 'PASSWORD_RESET') NOT NULL,
  `ip_address` varchar(45),
  `user_agent` text,
  `is_success` bit(1) NOT NULL DEFAULT b'0',
  `failure_reason` varchar(100) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_account_id` (`account_id`),
  INDEX `idx_email` (`email`),
  INDEX `idx_attempt_type` (`attempt_type`),
  INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- =====================================
-- 이메일 인증 관련 프로시저
-- =====================================

-- 이메일 인증 코드 생성 및 전송
DROP PROCEDURE IF EXISTS `fp_email_send_verification`;
DELIMITER ;;
CREATE PROCEDURE `fp_email_send_verification`(
    IN p_email VARCHAR(100),
    IN p_account_id VARCHAR(100)
)
BEGIN
    DECLARE v_verification_code VARCHAR(10);
    DECLARE v_expires_at DATETIME;
    DECLARE v_existing_count INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_email, ',', p_account_id);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_email_send_verification', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 인증 코드 생성 (6자리 랜덤 숫자)
    SET v_verification_code = LPAD(FLOOR(RAND() * 1000000), 6, '0');
    SET v_expires_at = DATE_ADD(NOW(), INTERVAL 5 MINUTE);
    
    -- 기존 미인증 레코드 확인
    SELECT COUNT(*) INTO v_existing_count
    FROM table_email_verification 
    WHERE email = p_email AND is_verified = 0;
    
    -- 기존 미인증 레코드 삭제
    IF v_existing_count > 0 THEN
        DELETE FROM table_email_verification 
        WHERE email = p_email AND is_verified = 0;
    END IF;
    
    -- 새 인증 코드 삽입
    INSERT INTO table_email_verification (email, verification_code, account_id, expires_at)
    VALUES (p_email, v_verification_code, p_account_id, v_expires_at);
    
    SELECT 'SUCCESS' as result, v_verification_code as verification_code, 5 as expires_minutes;
    
END ;;
DELIMITER ;

-- 이메일 인증 코드 확인
DROP PROCEDURE IF EXISTS `fp_email_confirm_verification`;
DELIMITER ;;
CREATE PROCEDURE `fp_email_confirm_verification`(
    IN p_email VARCHAR(100),
    IN p_verification_code VARCHAR(10)
)
BEGIN
    DECLARE v_record_count INT DEFAULT 0;
    DECLARE v_attempts INT DEFAULT 0;
    DECLARE v_max_attempts INT DEFAULT 5;
    DECLARE v_is_verified BIT(1) DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_email, ',', p_verification_code);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_email_confirm_verification', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 인증 코드 확인
    SELECT COUNT(*), attempts, max_attempts INTO v_record_count, v_attempts, v_max_attempts
    FROM table_email_verification 
    WHERE email = p_email 
      AND verification_code = p_verification_code 
      AND expires_at > NOW() 
      AND is_verified = 0;
    
    IF v_record_count > 0 AND v_attempts < v_max_attempts THEN
        -- 인증 성공
        UPDATE table_email_verification 
        SET is_verified = 1, verified_at = NOW()
        WHERE email = p_email AND verification_code = p_verification_code;
        
        SELECT 'SUCCESS' as result, 'Email verification completed' as message;
    ELSE
        -- 인증 실패 - 시도 횟수 증가
        UPDATE table_email_verification 
        SET attempts = attempts + 1
        WHERE email = p_email AND expires_at > NOW() AND is_verified = 0;
        
        IF v_attempts >= v_max_attempts THEN
            SELECT 'FAILED' as result, 'Too many attempts' as message;
        ELSE
            SELECT 'FAILED' as result, 'Invalid verification code' as message;
        END IF;
    END IF;
    
END ;;
DELIMITER ;

-- =====================================
-- OTP 관련 프로시저
-- =====================================

-- OTP 설정 생성
DROP PROCEDURE IF EXISTS `fp_otp_setup`;
DELIMITER ;;
CREATE PROCEDURE `fp_otp_setup`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_secret_key VARCHAR(255),
    IN p_qr_code_url TEXT
)
BEGIN
    DECLARE v_existing_count INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_secret_key);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_otp_setup', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 기존 OTP 설정 확인
    SELECT COUNT(*) INTO v_existing_count
    FROM table_otp_info 
    WHERE account_db_key = p_account_db_key;
    
    IF v_existing_count > 0 THEN
        -- 기존 설정 업데이트
        UPDATE table_otp_info 
        SET secret_key = p_secret_key, 
            qr_code_url = p_qr_code_url,
            is_enabled = 0,
            updated_at = NOW()
        WHERE account_db_key = p_account_db_key;
    ELSE
        -- 새 설정 삽입
        INSERT INTO table_otp_info (account_db_key, secret_key, qr_code_url, is_enabled)
        VALUES (p_account_db_key, p_secret_key, p_qr_code_url, 0);
    END IF;
    
    SELECT 'SUCCESS' as result, 'OTP setup completed' as message;
    
END ;;
DELIMITER ;

-- OTP 인증 확인 및 활성화
DROP PROCEDURE IF EXISTS `fp_otp_verify_and_enable`;
DELIMITER ;;
CREATE PROCEDURE `fp_otp_verify_and_enable`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_otp_code VARCHAR(10)
)
BEGIN
    DECLARE v_secret_key VARCHAR(255);
    DECLARE v_is_enabled BIT(1) DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_otp_code);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_otp_verify_and_enable', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- OTP 정보 조회
    SELECT secret_key, is_enabled INTO v_secret_key, v_is_enabled
    FROM table_otp_info 
    WHERE account_db_key = p_account_db_key;
    
    -- 실제 OTP 검증은 애플리케이션에서 수행 (pyotp 등 사용)
    -- 여기서는 OTP 코드가 제공되었다면 성공으로 간주
    IF v_secret_key IS NOT NULL AND LENGTH(p_otp_code) = 6 THEN
        -- OTP 활성화
        UPDATE table_otp_info 
        SET is_enabled = 1, 
            last_used_at = NOW(),
            updated_at = NOW()
        WHERE account_db_key = p_account_db_key;
        
        SELECT 'SUCCESS' as result, 'OTP enabled successfully' as message;
    ELSE
        SELECT 'FAILED' as result, 'Invalid OTP code' as message;
    END IF;
    
END ;;
DELIMITER ;

-- =====================================
-- 임시 토큰 관련 프로시저
-- =====================================

-- 임시 토큰 생성 (2단계 로그인용)
DROP PROCEDURE IF EXISTS `fp_create_temp_token`;
DELIMITER ;;
CREATE PROCEDURE `fp_create_temp_token`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_account_id VARCHAR(100),
    IN p_token_type VARCHAR(20)
)
BEGIN
    DECLARE v_temp_token VARCHAR(255);
    DECLARE v_expires_at DATETIME;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_account_id, ',', p_token_type);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_create_temp_token', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 임시 토큰 생성 (UUID 형태)
    SET v_temp_token = CONCAT(
        'temp_',
        LPAD(HEX(p_account_db_key), 16, '0'),
        '_',
        LPAD(HEX(UNIX_TIMESTAMP()), 8, '0'),
        '_',
        LPAD(HEX(FLOOR(RAND() * 65535)), 4, '0')
    );
    
    SET v_expires_at = DATE_ADD(NOW(), INTERVAL 10 MINUTE);  -- 10분 유효
    
    -- 기존 미사용 토큰 삭제
    DELETE FROM table_temp_tokens 
    WHERE account_db_key = p_account_db_key 
      AND token_type = p_token_type 
      AND is_used = 0;
    
    -- 새 토큰 삽입
    INSERT INTO table_temp_tokens (temp_token, account_db_key, account_id, token_type, expires_at)
    VALUES (v_temp_token, p_account_db_key, p_account_id, p_token_type, v_expires_at);
    
    SELECT 'SUCCESS' as result, v_temp_token as temp_token, 10 as expires_minutes;
    
END ;;
DELIMITER ;

-- 임시 토큰 검증
DROP PROCEDURE IF EXISTS `fp_verify_temp_token`;
DELIMITER ;;
CREATE PROCEDURE `fp_verify_temp_token`(
    IN p_temp_token VARCHAR(255),
    IN p_token_type VARCHAR(20)
)
BEGIN
    DECLARE v_account_db_key BIGINT UNSIGNED DEFAULT 0;
    DECLARE v_account_id VARCHAR(100) DEFAULT '';
    DECLARE v_is_valid BIT(1) DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_temp_token, ',', p_token_type);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_verify_temp_token', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 토큰 검증
    SELECT account_db_key, account_id INTO v_account_db_key, v_account_id
    FROM table_temp_tokens 
    WHERE temp_token = p_temp_token 
      AND token_type = p_token_type 
      AND is_used = 0 
      AND expires_at > NOW();
    
    IF v_account_db_key > 0 THEN
        -- 토큰 사용 처리
        UPDATE table_temp_tokens 
        SET is_used = 1, used_at = NOW()
        WHERE temp_token = p_temp_token;
        
        SELECT 'SUCCESS' as result, v_account_db_key as account_db_key, v_account_id as account_id;
    ELSE
        SELECT 'FAILED' as result, 0 as account_db_key, '' as account_id;
    END IF;
    
END ;;
DELIMITER ;

-- =====================================
-- 사용자 로그인 프로시저 업데이트 (OTP 지원)
-- =====================================

DROP PROCEDURE IF EXISTS `fp_user_login_with_otp`;
DELIMITER ;;
CREATE PROCEDURE `fp_user_login_with_otp`(
    IN p_platform_type TINYINT,
    IN p_account_id VARCHAR(100),
    IN p_password_hash VARCHAR(255)
)
BEGIN
    DECLARE v_account_db_key BIGINT UNSIGNED DEFAULT 0;
    DECLARE v_account_status VARCHAR(15) DEFAULT '';
    DECLARE v_shard_id INT DEFAULT 0;
    DECLARE v_nickname VARCHAR(50) DEFAULT '';
    DECLARE v_account_level INT DEFAULT 1;
    DECLARE v_otp_enabled BIT(1) DEFAULT 0;
    DECLARE v_temp_token VARCHAR(255) DEFAULT '';
    DECLARE v_result VARCHAR(20) DEFAULT 'FAILED';
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_platform_type, ',', p_account_id, ',', p_password_hash);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_user_login_with_otp', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 계정 정보 조회
    SELECT a.account_db_key, a.account_status, a.nickname, a.account_level
    INTO v_account_db_key, v_account_status, v_nickname, v_account_level
    FROM table_accountid a
    WHERE a.platform_type = p_platform_type 
      AND a.account_id = p_account_id 
      AND a.password_hash = p_password_hash;
    
    -- 로그인 성공 처리
    IF v_account_db_key > 0 AND v_account_status = 'Normal' THEN
        -- OTP 활성화 여부 확인
        SELECT COALESCE(is_enabled, 0) INTO v_otp_enabled
        FROM table_otp_info 
        WHERE account_db_key = v_account_db_key;
        
        -- 로그인 시간 업데이트
        UPDATE table_accountid
        SET login_time = NOW()
        WHERE account_db_key = v_account_db_key;
        
        -- 사용자 샤드 조회/할당
        SELECT shard_id INTO v_shard_id
        FROM table_user_shard_mapping 
        WHERE account_db_key = v_account_db_key;
        
        IF v_shard_id IS NULL OR v_shard_id = 0 THEN
            SET v_shard_id = (v_account_db_key % 2) + 1;
            
            INSERT INTO table_user_shard_mapping (account_db_key, shard_id)
            VALUES (v_account_db_key, v_shard_id)
            ON DUPLICATE KEY UPDATE 
                shard_id = v_shard_id,
                updated_at = NOW();
        END IF;
        
        IF v_otp_enabled = 1 THEN
            -- OTP 활성화된 경우 - 임시 토큰 생성
            CALL fp_create_temp_token(v_account_db_key, p_account_id, 'LOGIN_OTP');
            
            -- 마지막 결과에서 temp_token 가져오기
            SELECT temp_token INTO v_temp_token 
            FROM table_temp_tokens 
            WHERE account_db_key = v_account_db_key 
              AND token_type = 'LOGIN_OTP' 
              AND is_used = 0 
            ORDER BY created_at DESC 
            LIMIT 1;
            
            SELECT 
                'OTP_REQUIRED' as result,
                v_account_db_key as account_db_key,
                v_nickname as nickname,
                v_account_level as account_level,
                v_shard_id as shard_id,
                v_temp_token as temp_token,
                TRUE as requires_otp;
        ELSE
            -- OTP 미활성화 - 바로 로그인 완료
            SELECT 
                'SUCCESS' as result,
                v_account_db_key as account_db_key,
                v_nickname as nickname,
                v_account_level as account_level,
                v_shard_id as shard_id,
                '' as temp_token,
                FALSE as requires_otp;
        END IF;
        
    ELSEIF v_account_db_key > 0 AND v_account_status != 'Normal' THEN
        SELECT 'BLOCKED' as result, 0 as account_db_key, '' as nickname, 0 as account_level, 0 as shard_id, '' as temp_token, FALSE as requires_otp;
    ELSE
        SELECT 'FAILED' as result, 0 as account_db_key, '' as nickname, 0 as account_level, 0 as shard_id, '' as temp_token, FALSE as requires_otp;
    END IF;
    
END ;;
DELIMITER ;

SELECT 'Finance Global DB 인증 확장 완료' as status;