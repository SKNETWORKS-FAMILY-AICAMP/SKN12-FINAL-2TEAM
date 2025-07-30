-- =====================================
-- API 키 저장 테이블 생성
-- =====================================

USE finance_global;

-- 사용자 API 키 테이블
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

-- API 키 저장 프로시저
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

-- API 키 조회 프로시저
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