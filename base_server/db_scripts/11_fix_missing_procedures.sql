-- =====================================
-- 누락된 프로시저 추가 및 불일치 수정
-- API 호출과 DB 스키마 동기화
-- =====================================

-- =====================================
-- 글로벌 DB 누락 프로시저 추가
-- =====================================
USE finance_global;

-- 사용자 비밀번호 검증
DROP PROCEDURE IF EXISTS `fp_verify_user_password`;
DELIMITER ;;
CREATE PROCEDURE `fp_verify_user_password`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_current_password VARCHAR(255)
)
BEGIN
    DECLARE v_stored_password VARCHAR(255);
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', 'PASSWORD_CHECK');
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_verify_user_password', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 저장된 비밀번호 조회
    SELECT password_hash INTO v_stored_password
    FROM table_accountid 
    WHERE account_db_key = p_account_db_key;
    
    -- 비밀번호 검증 (실제로는 해시 비교)
    IF v_stored_password = SHA2(p_current_password, 256) THEN
        SELECT 'SUCCESS' as result, 'Password verified' as message;
    ELSE
        SELECT 'FAILED' as result, 'Invalid password' as message;
    END IF;
    
END ;;
DELIMITER ;

-- 사용자 비밀번호 업데이트
DROP PROCEDURE IF EXISTS `fp_update_user_password`;
DELIMITER ;;
CREATE PROCEDURE `fp_update_user_password`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_new_password VARCHAR(255)
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', 'PASSWORD_UPDATE');
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_update_user_password', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 비밀번호 업데이트
    UPDATE table_accountid 
    SET password_hash = SHA2(p_new_password, 256),
        update_time = NOW()
    WHERE account_db_key = p_account_db_key;
    
    -- 비밀번호 변경 이력 기록
    INSERT INTO table_user_profiles (account_db_key, field_name, field_value, updated_at)
    VALUES (p_account_db_key, 'last_password_change', NOW(), NOW())
    ON DUPLICATE KEY UPDATE 
        field_value = NOW(),
        updated_at = NOW();
    
    SELECT 'SUCCESS' as result, 'Password updated successfully' as message;
    
END ;;
DELIMITER ;

-- =====================================
-- Shard DB 누락 프로시저 추가
-- =====================================
USE finance_shard_1;

-- 주식 주문 생성 프로시저
DROP PROCEDURE IF EXISTS `fp_create_stock_order`;
DELIMITER ;;
CREATE PROCEDURE `fp_create_stock_order`(
    IN p_order_id VARCHAR(32),
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_symbol VARCHAR(10),
    IN p_action VARCHAR(10),
    IN p_order_type VARCHAR(20),
    IN p_quantity INT,
    IN p_price DECIMAL(15,2),
    IN p_stop_price DECIMAL(15,2),
    IN p_commission DECIMAL(10,2)
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_order_id, ',', p_account_db_key, ',', p_symbol, ',', p_action);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_create_stock_order', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 주문 생성
    INSERT INTO table_stock_orders (
        order_id, account_db_key, symbol, action, order_type, 
        quantity, price, stop_price, commission, order_status, order_time
    ) VALUES (
        p_order_id, p_account_db_key, p_symbol, p_action, p_order_type,
        p_quantity, p_price, p_stop_price, p_commission, 'PENDING', NOW()
    );
    
    SELECT 'SUCCESS' as result, p_order_id as order_id, 'PENDING' as order_status, NOW() as order_time;
    
END ;;
DELIMITER ;

-- 검색 기록 저장 프로시저
DROP PROCEDURE IF EXISTS `fp_save_search_history`;
DELIMITER ;;
CREATE PROCEDURE `fp_save_search_history`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_query VARCHAR(200),
    IN p_search_type VARCHAR(50)
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_query, ',', p_search_type);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_save_search_history', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 검색 기록 테이블이 없으므로 간단한 로그 형태로 저장
    INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
    VALUES ('search_history', 'INFO', 0, CONCAT('Search: ', p_query), CONCAT(p_account_db_key, ',', p_search_type));
    
    SELECT 'SUCCESS' as result, 'Search history saved' as message;
    
END ;;
DELIMITER ;

-- 시장 개요 조회 프로시저
DROP PROCEDURE IF EXISTS `fp_get_market_overview`;
DELIMITER ;;
CREATE PROCEDURE `fp_get_market_overview`(
    IN p_symbols JSON
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CAST(p_symbols AS CHAR);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_get_market_overview', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 시장 개요 데이터 조회
    SELECT 
        symbol,
        name,
        current_price,
        change_amount,
        change_rate,
        volume,
        market_cap,
        last_updated
    FROM table_market_overview 
    WHERE JSON_CONTAINS(p_symbols, JSON_QUOTE(symbol))
       OR p_symbols IS NULL
    ORDER BY market_cap DESC;
    
END ;;
DELIMITER ;

-- 시장 분석 저장 프로시저
DROP PROCEDURE IF EXISTS `fp_save_market_analysis`;
DELIMITER ;;
CREATE PROCEDURE `fp_save_market_analysis`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_analysis_type VARCHAR(50),
    IN p_analysis_data JSON
)
BEGIN
    DECLARE v_analysis_id VARCHAR(32);
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_analysis_type);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_save_market_analysis', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 분석 ID 생성
    SET v_analysis_id = CONCAT(
        'analysis_',
        LPAD(HEX(p_account_db_key), 16, '0'),
        '_',
        LPAD(HEX(UNIX_TIMESTAMP()), 8, '0')
    );
    
    -- AI 분석 결과 테이블에 저장
    INSERT INTO table_ai_analysis_results (
        analysis_id, account_db_key, symbol, analysis_type, 
        score, confidence, summary, details, created_at
    ) VALUES (
        v_analysis_id, p_account_db_key, JSON_UNQUOTE(JSON_EXTRACT(p_analysis_data, '$.symbol')),
        p_analysis_type, 
        CAST(JSON_UNQUOTE(JSON_EXTRACT(p_analysis_data, '$.score')) AS DECIMAL(5,2)),
        CAST(JSON_UNQUOTE(JSON_EXTRACT(p_analysis_data, '$.confidence')) AS DECIMAL(5,2)),
        JSON_UNQUOTE(JSON_EXTRACT(p_analysis_data, '$.summary')),
        CAST(p_analysis_data AS CHAR),
        NOW()
    );
    
    SELECT 'SUCCESS' as result, v_analysis_id as analysis_id;
    
END ;;
DELIMITER ;

-- 채팅방 삭제 프로시저
DROP PROCEDURE IF EXISTS `fp_delete_chat_room`;
DELIMITER ;;
CREATE PROCEDURE `fp_delete_chat_room`(
    IN p_room_id VARCHAR(50),
    IN p_account_db_key BIGINT UNSIGNED
)
BEGIN
    DECLARE v_room_exists INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_room_id, ',', p_account_db_key);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_delete_chat_room', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 채팅방 존재 및 소유권 확인
    SELECT COUNT(*) INTO v_room_exists
    FROM table_chat_rooms 
    WHERE room_id = p_room_id AND account_db_key = p_account_db_key;
    
    IF v_room_exists = 0 THEN
        SELECT 'FAILED' as result, 'Room not found or access denied' as message;
    ELSE
        -- 채팅 메시지 삭제
        DELETE FROM table_chat_messages WHERE room_id = p_room_id;
        
        -- 채팅방 삭제
        DELETE FROM table_chat_rooms WHERE room_id = p_room_id AND account_db_key = p_account_db_key;
        
        SELECT 'SUCCESS' as result, 'Chat room deleted successfully' as message;
    END IF;
    
END ;;
DELIMITER ;

-- 포트폴리오 성과 조회 프로시저 (매개변수 수정)
DROP PROCEDURE IF EXISTS `fp_get_portfolio_performance`;
DELIMITER ;;
CREATE PROCEDURE `fp_get_portfolio_performance`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_period VARCHAR(10)
)
BEGIN
    DECLARE v_days INT DEFAULT 365;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_period);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_get_portfolio_performance', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 기간 설정
    CASE p_period
        WHEN '1D' THEN SET v_days = 1;
        WHEN '1W' THEN SET v_days = 7;
        WHEN '1M' THEN SET v_days = 30;
        WHEN '3M' THEN SET v_days = 90;
        WHEN '6M' THEN SET v_days = 180;
        WHEN '1Y' THEN SET v_days = 365;
        ELSE SET v_days = 365;
    END CASE;
    
    -- 성과 요약 데이터
    SELECT 
        account_db_key,
        AVG(return_rate) as return_rate,
        AVG(benchmark_return) as benchmark_return,
        AVG(sharpe_ratio) as sharpe_ratio,
        MIN(max_drawdown) as max_drawdown,
        AVG(volatility) as volatility,
        MAX(total_value) as max_value,
        MIN(total_value) as min_value
    FROM table_portfolio_performance 
    WHERE account_db_key = p_account_db_key 
      AND date >= DATE_SUB(CURDATE(), INTERVAL v_days DAY)
    GROUP BY account_db_key;
    
    -- 일별 성과 데이터
    SELECT 
        date,
        total_value,
        return_rate,
        benchmark_return
    FROM table_portfolio_performance 
    WHERE account_db_key = p_account_db_key 
      AND date >= DATE_SUB(CURDATE(), INTERVAL v_days DAY)
    ORDER BY date;
    
END ;;
DELIMITER ;

-- =====================================
-- Shard 2에도 동일하게 적용
-- =====================================
USE finance_shard_2;

-- 동일한 프로시저들을 Shard 2에도 생성
DROP PROCEDURE IF EXISTS `fp_create_stock_order`;
DELIMITER ;;
CREATE PROCEDURE `fp_create_stock_order`(
    IN p_order_id VARCHAR(32),
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_symbol VARCHAR(10),
    IN p_action VARCHAR(10),
    IN p_order_type VARCHAR(20),
    IN p_quantity INT,
    IN p_price DECIMAL(15,2),
    IN p_stop_price DECIMAL(15,2),
    IN p_commission DECIMAL(10,2)
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_order_id, ',', p_account_db_key, ',', p_symbol, ',', p_action);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_create_stock_order', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    INSERT INTO table_stock_orders (
        order_id, account_db_key, symbol, action, order_type, 
        quantity, price, stop_price, commission, order_status, order_time
    ) VALUES (
        p_order_id, p_account_db_key, p_symbol, p_action, p_order_type,
        p_quantity, p_price, p_stop_price, p_commission, 'PENDING', NOW()
    );
    
    SELECT 'SUCCESS' as result, p_order_id as order_id, 'PENDING' as order_status, NOW() as order_time;
END ;;
DELIMITER ;

DROP PROCEDURE IF EXISTS `fp_save_search_history`;
DELIMITER ;;
CREATE PROCEDURE `fp_save_search_history`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_query VARCHAR(200),
    IN p_search_type VARCHAR(50)
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_query, ',', p_search_type);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_save_search_history', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
    VALUES ('search_history', 'INFO', 0, CONCAT('Search: ', p_query), CONCAT(p_account_db_key, ',', p_search_type));
    
    SELECT 'SUCCESS' as result, 'Search history saved' as message;
END ;;
DELIMITER ;

DROP PROCEDURE IF EXISTS `fp_get_market_overview`;
DELIMITER ;;
CREATE PROCEDURE `fp_get_market_overview`(
    IN p_symbols JSON
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CAST(p_symbols AS CHAR);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_get_market_overview', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    SELECT 
        symbol, name, current_price, change_amount, change_rate, volume, market_cap, last_updated
    FROM table_market_overview 
    WHERE JSON_CONTAINS(p_symbols, JSON_QUOTE(symbol)) OR p_symbols IS NULL
    ORDER BY market_cap DESC;
END ;;
DELIMITER ;

DROP PROCEDURE IF EXISTS `fp_save_market_analysis`;
DELIMITER ;;
CREATE PROCEDURE `fp_save_market_analysis`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_analysis_type VARCHAR(50),
    IN p_analysis_data JSON
)
BEGIN
    DECLARE v_analysis_id VARCHAR(32);
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_analysis_type);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_save_market_analysis', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    SET v_analysis_id = CONCAT('analysis_', LPAD(HEX(p_account_db_key), 16, '0'), '_', LPAD(HEX(UNIX_TIMESTAMP()), 8, '0'));
    
    INSERT INTO table_ai_analysis_results (
        analysis_id, account_db_key, symbol, analysis_type, 
        score, confidence, summary, details, created_at
    ) VALUES (
        v_analysis_id, p_account_db_key, JSON_UNQUOTE(JSON_EXTRACT(p_analysis_data, '$.symbol')),
        p_analysis_type, 
        CAST(JSON_UNQUOTE(JSON_EXTRACT(p_analysis_data, '$.score')) AS DECIMAL(5,2)),
        CAST(JSON_UNQUOTE(JSON_EXTRACT(p_analysis_data, '$.confidence')) AS DECIMAL(5,2)),
        JSON_UNQUOTE(JSON_EXTRACT(p_analysis_data, '$.summary')),
        CAST(p_analysis_data AS CHAR), NOW()
    );
    
    SELECT 'SUCCESS' as result, v_analysis_id as analysis_id;
END ;;
DELIMITER ;

DROP PROCEDURE IF EXISTS `fp_delete_chat_room`;
DELIMITER ;;
CREATE PROCEDURE `fp_delete_chat_room`(
    IN p_room_id VARCHAR(50),
    IN p_account_db_key BIGINT UNSIGNED
)
BEGIN
    DECLARE v_room_exists INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_room_id, ',', p_account_db_key);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_delete_chat_room', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    SELECT COUNT(*) INTO v_room_exists
    FROM table_chat_rooms 
    WHERE room_id = p_room_id AND account_db_key = p_account_db_key;
    
    IF v_room_exists = 0 THEN
        SELECT 'FAILED' as result, 'Room not found or access denied' as message;
    ELSE
        DELETE FROM table_chat_messages WHERE room_id = p_room_id;
        DELETE FROM table_chat_rooms WHERE room_id = p_room_id AND account_db_key = p_account_db_key;
        SELECT 'SUCCESS' as result, 'Chat room deleted successfully' as message;
    END IF;
END ;;
DELIMITER ;

DROP PROCEDURE IF EXISTS `fp_get_portfolio_performance`;
DELIMITER ;;
CREATE PROCEDURE `fp_get_portfolio_performance`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_period VARCHAR(10)
)
BEGIN
    DECLARE v_days INT DEFAULT 365;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_period);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_get_portfolio_performance', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    CASE p_period
        WHEN '1D' THEN SET v_days = 1;
        WHEN '1W' THEN SET v_days = 7;
        WHEN '1M' THEN SET v_days = 30;
        WHEN '3M' THEN SET v_days = 90;
        WHEN '6M' THEN SET v_days = 180;
        WHEN '1Y' THEN SET v_days = 365;
        ELSE SET v_days = 365;
    END CASE;
    
    SELECT 
        account_db_key, AVG(return_rate) as return_rate, AVG(benchmark_return) as benchmark_return,
        AVG(sharpe_ratio) as sharpe_ratio, MIN(max_drawdown) as max_drawdown, AVG(volatility) as volatility,
        MAX(total_value) as max_value, MIN(total_value) as min_value
    FROM table_portfolio_performance 
    WHERE account_db_key = p_account_db_key AND date >= DATE_SUB(CURDATE(), INTERVAL v_days DAY)
    GROUP BY account_db_key;
    
    SELECT date, total_value, return_rate, benchmark_return
    FROM table_portfolio_performance 
    WHERE account_db_key = p_account_db_key AND date >= DATE_SUB(CURDATE(), INTERVAL v_days DAY)
    ORDER BY date;
END ;;
DELIMITER ;

SELECT '누락된 프로시저 추가 완료!' as status;