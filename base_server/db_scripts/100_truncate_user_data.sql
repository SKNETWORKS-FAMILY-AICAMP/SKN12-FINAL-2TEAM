-- =====================================
-- 유저 관련 데이터 초기화 프로시저
-- 샤딩 테이블 제외, 외래키 순서에 맞게 정리
-- =====================================

USE finance_global;

DROP PROCEDURE IF EXISTS `fp_truncate_all_user_data`;
DELIMITER ;;
CREATE PROCEDURE `fp_truncate_all_user_data`()
BEGIN
    DECLARE v_error_count INT DEFAULT 0;
    DECLARE CONTINUE HANDLER FOR SQLEXCEPTION 
    BEGIN
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        SET v_error_count = v_error_count + 1;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_truncate_all_user_data', @ErrorState, @ErrorNo, @ErrorMessage, 'TRUNCATE_OPERATION');
    END;
    
    -- 외래키 체크 비활성화
    SET FOREIGN_KEY_CHECKS = 0;
    
    -- =====================================
    -- Global DB 유저 관련 테이블 초기화
    -- =====================================
    
    -- 1. 자식 테이블부터 삭제 (외래키 참조 순서)
    TRUNCATE TABLE `finance_global`.`table_user_sessions`;
    TRUNCATE TABLE `finance_global`.`table_temp_tokens`;
    TRUNCATE TABLE `finance_global`.`table_otp_info`;
    TRUNCATE TABLE `finance_global`.`table_email_verification`;
    TRUNCATE TABLE `finance_global`.`table_auth_attempts`;
    TRUNCATE TABLE `finance_global`.`table_user_profiles`;
    
    -- 2. 유저 샤드 매핑 삭제
    TRUNCATE TABLE `finance_global`.`table_user_shard_mapping`;
    
    -- 3. 마지막으로 부모 테이블 삭제
    TRUNCATE TABLE `finance_global`.`table_accountid`;
    
    -- =====================================
    -- Shard 1 DB 유저 관련 테이블 초기화
    -- =====================================
    
    -- 포트폴리오 관련
    TRUNCATE TABLE `finance_shard_1`.`table_portfolio_holdings`;
    TRUNCATE TABLE `finance_shard_1`.`table_portfolio_transactions`;
    TRUNCATE TABLE `finance_shard_1`.`table_portfolio_history`;
    TRUNCATE TABLE `finance_shard_1`.`table_portfolios`;
    
    -- 거래 관련
    TRUNCATE TABLE `finance_shard_1`.`table_trading_strategies`;
    TRUNCATE TABLE `finance_shard_1`.`table_trading_executions`;
    TRUNCATE TABLE `finance_shard_1`.`table_trading_backtest_results`;
    
    -- 채팅 관련
    TRUNCATE TABLE `finance_shard_1`.`table_chat_messages`;
    TRUNCATE TABLE `finance_shard_1`.`table_chat_rooms`;
    
    -- 알림 관련
    TRUNCATE TABLE `finance_shard_1`.`table_price_alerts`;
    TRUNCATE TABLE `finance_shard_1`.`table_notifications`;
    
    -- 계좌 관련
    TRUNCATE TABLE `finance_shard_1`.`table_account_transactions`;
    TRUNCATE TABLE `finance_shard_1`.`table_accounts`;
    
    -- 설정 관련
    TRUNCATE TABLE `finance_shard_1`.`table_user_settings`;
    
    -- 아웃박스 패턴 관련
    TRUNCATE TABLE `finance_shard_1`.`table_outbox_events`;
    
    -- =====================================
    -- Shard 2 DB 유저 관련 테이블 초기화  
    -- =====================================
    
    -- 포트폴리오 관련
    TRUNCATE TABLE `finance_shard_2`.`table_portfolio_holdings`;
    TRUNCATE TABLE `finance_shard_2`.`table_portfolio_transactions`;
    TRUNCATE TABLE `finance_shard_2`.`table_portfolio_history`;
    TRUNCATE TABLE `finance_shard_2`.`table_portfolios`;
    
    -- 거래 관련
    TRUNCATE TABLE `finance_shard_2`.`table_trading_strategies`;
    TRUNCATE TABLE `finance_shard_2`.`table_trading_executions`;
    TRUNCATE TABLE `finance_shard_2`.`table_trading_backtest_results`;
    
    -- 채팅 관련
    TRUNCATE TABLE `finance_shard_2`.`table_chat_messages`;
    TRUNCATE TABLE `finance_shard_2`.`table_chat_rooms`;
    
    -- 알림 관련
    TRUNCATE TABLE `finance_shard_2`.`table_price_alerts`;
    TRUNCATE TABLE `finance_shard_2`.`table_notifications`;
    
    -- 계좌 관련
    TRUNCATE TABLE `finance_shard_2`.`table_account_transactions`;
    TRUNCATE TABLE `finance_shard_2`.`table_accounts`;
    
    -- 설정 관련
    TRUNCATE TABLE `finance_shard_2`.`table_user_settings`;
    
    -- 아웃박스 패턴 관련
    TRUNCATE TABLE `finance_shard_2`.`table_outbox_events`;
    
    -- =====================================
    -- 샤드 통계 초기화 (유저 수만 리셋)
    -- =====================================
    
    UPDATE `finance_global`.`table_shard_stats` SET 
        `user_count` = 0, 
        `active_users` = 0,
        `last_updated` = NOW();
    
    -- 외래키 체크 재활성화
    SET FOREIGN_KEY_CHECKS = 1;
    
    -- 결과 반환
    IF v_error_count = 0 THEN
        SELECT 'SUCCESS' as result, 'All user data truncated successfully' as message, 'Shard config preserved' as notice;
    ELSE
        SELECT 'PARTIAL_SUCCESS' as result, CONCAT('Completed with ', v_error_count, ' errors') as message, 'Check error log' as notice;
    END IF;
    
END ;;
DELIMITER ;

-- 사용법 예시:
-- CALL fp_truncate_all_user_data();