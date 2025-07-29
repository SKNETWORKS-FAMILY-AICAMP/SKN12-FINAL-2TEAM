-- =====================================
-- Finance Shard DB 튜토리얼 완료 상태 테이블
-- 클라이언트 중심, 튜토리얼별 완료된 스텝 저장
-- =====================================

-- 모든 샤드 DB에 적용
-- USE finance_shard_1;
-- USE finance_shard_2;
-- USE finance_shard_3;

-- 사용자별 튜토리얼 완료 상태 저장 테이블 (튜토리얼 타입별 단일 로우)
CREATE TABLE IF NOT EXISTS `table_tutorial_progress` (
  `account_db_key` bigint unsigned NOT NULL,
  `tutorial_type` varchar(50) NOT NULL COMMENT '튜토리얼 타입 (OVERVIEW, PORTFOLIO, SIGNALS, CHAT, SETTINGS)',
  `completed_step` int NOT NULL DEFAULT 0 COMMENT '완료된 최고 스텝 번호 (0=시작안함)',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`account_db_key`, `tutorial_type`),
  INDEX `idx_tutorial_type` (`tutorial_type`),
  INDEX `idx_updated_at` (`updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- =====================================
-- 튜토리얼 관리 프로시저
-- =====================================

-- 튜토리얼 스텝 완료 처리 (UPSERT 방식)
DROP PROCEDURE IF EXISTS `fp_tutorial_complete_step`;
DELIMITER ;;
CREATE PROCEDURE `fp_tutorial_complete_step`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_tutorial_type VARCHAR(50),
    IN p_step_number INT
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_tutorial_type, ',', p_step_number);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_tutorial_complete_step', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 튜토리얼 타입별 최고 스텝만 저장 (UPSERT)
    -- 없으면 INSERT, 있으면 더 큰 스텝으로만 UPDATE
    INSERT INTO table_tutorial_progress (account_db_key, tutorial_type, completed_step) 
    VALUES (p_account_db_key, p_tutorial_type, p_step_number)
    ON DUPLICATE KEY UPDATE 
        completed_step = GREATEST(completed_step, p_step_number),
        updated_at = NOW();
    
    SELECT 'SUCCESS' as result, 'Tutorial step completed' as message;
    
END ;;
DELIMITER ;

-- 사용자의 모든 튜토리얼 진행 상태 조회
DROP PROCEDURE IF EXISTS `fp_tutorial_get_progress`;
DELIMITER ;;
CREATE PROCEDURE `fp_tutorial_get_progress`(
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
            VALUES ('fp_tutorial_get_progress', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 모든 튜토리얼의 진행 상태 반환
    SELECT 
        tutorial_type,
        completed_step,
        updated_at
    FROM table_tutorial_progress 
    WHERE account_db_key = p_account_db_key
    ORDER BY tutorial_type;
    
END ;;
DELIMITER ;


SELECT 'Finance Shard DB 튜토리얼 스텝별 완료 상태 테이블 생성 완료' as status;