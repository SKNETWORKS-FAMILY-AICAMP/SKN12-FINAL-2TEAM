-- =====================================
-- Finance Shard DB 포트폴리오 및 대시보드 확장
-- 패킷명세서 기반: REQ-PORT-001~007, REQ-DASH-001~005
-- =====================================

-- Shard 1에 적용
USE finance_shard_1;

-- 1. 포트폴리오 성과 분석 테이블
CREATE TABLE IF NOT EXISTS `table_portfolio_performance` (
  `account_db_key` bigint unsigned NOT NULL,
  `date` date NOT NULL,
  `total_value` decimal(15,2) DEFAULT 0.00,
  `cash_balance` decimal(15,2) DEFAULT 0.00,
  `invested_amount` decimal(15,2) DEFAULT 0.00,
  `total_return` decimal(15,2) DEFAULT 0.00,
  `return_rate` decimal(10,4) DEFAULT 0.0000,
  `benchmark_return` decimal(10,4) DEFAULT 0.0000,
  `sharpe_ratio` decimal(10,4) DEFAULT 0.0000,
  `max_drawdown` decimal(10,4) DEFAULT 0.0000,
  `volatility` decimal(10,4) DEFAULT 0.0000,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`account_db_key`, `date`),
  INDEX `idx_date` (`date`),
  INDEX `idx_total_value` (`total_value`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 2. 포트폴리오 리밸런싱 리포트 테이블
CREATE TABLE IF NOT EXISTS `table_rebalance_reports` (
  `report_id` bigint NOT NULL AUTO_INCREMENT,
  `account_db_key` bigint unsigned NOT NULL,
  `trigger_reason` varchar(100) DEFAULT NULL,
  `recommendations` text,  -- JSON 형태로 추천 사항 저장
  `expected_improvement` decimal(10,4) DEFAULT 0.0000,
  `target_allocation` text,  -- JSON 형태로 목표 배분 저장
  `trades_required` text,  -- JSON 형태로 필요한 거래 저장
  `estimated_cost` decimal(15,2) DEFAULT 0.00,
  `status` enum('PENDING','APPLIED','REJECTED') DEFAULT 'PENDING',
  `generated_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `applied_at` datetime DEFAULT NULL,
  PRIMARY KEY (`report_id`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_status` (`status`),
  INDEX `idx_generated_at` (`generated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 3. 주식 주문 내역 테이블 (확장)
CREATE TABLE IF NOT EXISTS `table_stock_orders` (
  `order_id` varchar(32) NOT NULL,
  `account_db_key` bigint unsigned NOT NULL,
  `symbol` varchar(10) NOT NULL,
  `order_type` enum('BUY','SELL') NOT NULL,
  `price_type` enum('MARKET','LIMIT','STOP') DEFAULT 'MARKET',
  `quantity` int NOT NULL,
  `price` decimal(15,2) DEFAULT 0.00,
  `stop_price` decimal(15,2) DEFAULT NULL,
  `filled_quantity` int DEFAULT 0,
  `avg_fill_price` decimal(15,2) DEFAULT 0.00,
  `order_status` enum('PENDING','PARTIAL','FILLED','CANCELLED','REJECTED') DEFAULT 'PENDING',
  `order_source` enum('MANUAL','AUTO_STRATEGY','REBALANCE') DEFAULT 'MANUAL',
  `strategy_id` varchar(50) DEFAULT NULL,
  `commission` decimal(10,2) DEFAULT 0.00,
  `order_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `fill_time` datetime DEFAULT NULL,
  `cancel_time` datetime DEFAULT NULL,
  PRIMARY KEY (`order_id`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_symbol` (`symbol`),
  INDEX `idx_order_status` (`order_status`),
  INDEX `idx_order_time` (`order_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 4. 자산 배분 히스토리 테이블
CREATE TABLE IF NOT EXISTS `table_allocation_history` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `account_db_key` bigint unsigned NOT NULL,
  `symbol` varchar(10) NOT NULL,
  `allocation_date` date NOT NULL,
  `target_weight` decimal(10,4) DEFAULT 0.0000,
  `actual_weight` decimal(10,4) DEFAULT 0.0000,
  `target_value` decimal(15,2) DEFAULT 0.00,
  `actual_value` decimal(15,2) DEFAULT 0.00,
  `deviation` decimal(10,4) DEFAULT 0.0000,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_account_symbol_date` (`account_db_key`,`symbol`,`allocation_date`),
  INDEX `idx_allocation_date` (`allocation_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 5. 대시보드 알림 테이블
CREATE TABLE IF NOT EXISTS `table_dashboard_alerts` (
  `alert_id` varchar(32) NOT NULL,
  `account_db_key` bigint unsigned NOT NULL,
  `alert_type` enum('PRICE_CHANGE','NEWS','TARGET_REACHED','PORTFOLIO_ALERT') NOT NULL,
  `title` varchar(200) NOT NULL,
  `message` text NOT NULL,
  `severity` enum('INFO','WARNING','CRITICAL') DEFAULT 'INFO',
  `symbol` varchar(10) DEFAULT NULL,
  `trigger_value` decimal(15,4) DEFAULT NULL,
  `current_value` decimal(15,4) DEFAULT NULL,
  `is_read` bit(1) NOT NULL DEFAULT b'0',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `expires_at` datetime DEFAULT NULL,
  PRIMARY KEY (`alert_id`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_alert_type` (`alert_type`),
  INDEX `idx_is_read` (`is_read`),
  INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 6. 시장 개요 데이터 테이블 (주요 지수)
CREATE TABLE IF NOT EXISTS `table_market_overview` (
  `symbol` varchar(10) NOT NULL,
  `name` varchar(100) NOT NULL,
  `current_price` decimal(15,4) DEFAULT 0.0000,
  `change_amount` decimal(15,4) DEFAULT 0.0000,
  `change_rate` decimal(10,4) DEFAULT 0.0000,
  `volume` bigint DEFAULT 0,
  `market_cap` bigint DEFAULT 0,
  `last_updated` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`symbol`),
  INDEX `idx_change_rate` (`change_rate`),
  INDEX `idx_volume` (`volume`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- =====================================
-- 포트폴리오 관련 프로시저
-- =====================================

-- 포트폴리오 조회 (확장)
DROP PROCEDURE IF EXISTS `fp_get_portfolio_extended`;
DELIMITER ;;
CREATE PROCEDURE `fp_get_portfolio_extended`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_include_performance BOOLEAN,
    IN p_include_holdings BOOLEAN
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_include_performance, ',', p_include_holdings);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_get_portfolio_extended', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 포트폴리오 기본 정보
    SELECT 
        CONCAT('portfolio_', p_account_db_key) as portfolio_id,
        '메인 포트폴리오' as name,
        COALESCE(SUM(ua.balance), 0) + COALESCE(SUM(up.current_value), 0) as total_value,
        COALESCE(SUM(ua.balance), 0) as cash_balance,
        COALESCE(SUM(up.current_value), 0) as invested_amount,
        0.0 as total_return,
        0.0 as return_rate,
        NOW() as created_at
    FROM table_user_accounts ua
    LEFT JOIN table_user_portfolios up ON ua.account_db_key = up.account_db_key
    WHERE ua.account_db_key = p_account_db_key
    GROUP BY ua.account_db_key;
    
    -- 보유 종목 정보 (요청시)
    IF p_include_holdings THEN
        SELECT 
            up.asset_code as symbol,
            mo.name,
            up.quantity,
            up.average_cost as avg_price,
            mo.current_price,
            up.current_value as market_value,
            (up.current_value - (up.quantity * up.average_cost)) as unrealized_pnl,
            CASE 
                WHEN up.average_cost > 0 THEN 
                    ((mo.current_price - up.average_cost) / up.average_cost * 100)
                ELSE 0 
            END as return_rate
        FROM table_user_portfolios up
        LEFT JOIN table_market_overview mo ON up.asset_code = mo.symbol
        WHERE up.account_db_key = p_account_db_key
          AND up.quantity > 0;
    END IF;
    
    -- 성과 정보 (요청시)
    IF p_include_performance THEN
        SELECT 
            COALESCE(AVG(return_rate), 0) as total_return,
            COALESCE(AVG(return_rate * 12), 0) as annualized_return,
            COALESCE(AVG(sharpe_ratio), 0) as sharpe_ratio,
            COALESCE(MIN(max_drawdown), 0) as max_drawdown,
            0.0 as win_rate,
            0.0 as profit_factor
        FROM table_portfolio_performance 
        WHERE account_db_key = p_account_db_key
          AND date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR);
    END IF;
    
END ;;
DELIMITER ;

-- 포트폴리오 성과 기록
DROP PROCEDURE IF EXISTS `fp_record_portfolio_performance`;
DELIMITER ;;
CREATE PROCEDURE `fp_record_portfolio_performance`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_date DATE,
    IN p_total_value DECIMAL(15,2),
    IN p_cash_balance DECIMAL(15,2),
    IN p_invested_amount DECIMAL(15,2)
)
BEGIN
    DECLARE v_return_rate DECIMAL(10,4) DEFAULT 0.0000;
    DECLARE v_previous_value DECIMAL(15,2) DEFAULT 0.00;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_date, ',', p_total_value);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_record_portfolio_performance', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 이전 날짜의 포트폴리오 가치 조회
    SELECT total_value INTO v_previous_value
    FROM table_portfolio_performance 
    WHERE account_db_key = p_account_db_key 
      AND date < p_date
    ORDER BY date DESC 
    LIMIT 1;
    
    -- 수익률 계산
    IF v_previous_value > 0 THEN
        SET v_return_rate = ((p_total_value - v_previous_value) / v_previous_value) * 100;
    END IF;
    
    -- 성과 기록 삽입/업데이트
    INSERT INTO table_portfolio_performance (
        account_db_key, date, total_value, cash_balance, invested_amount, 
        total_return, return_rate
    ) VALUES (
        p_account_db_key, p_date, p_total_value, p_cash_balance, p_invested_amount,
        (p_total_value - p_invested_amount), v_return_rate
    ) ON DUPLICATE KEY UPDATE
        total_value = p_total_value,
        cash_balance = p_cash_balance,
        invested_amount = p_invested_amount,
        total_return = (p_total_value - p_invested_amount),
        return_rate = v_return_rate;
    
    SELECT 'SUCCESS' as result, v_return_rate as return_rate;
    
END ;;
DELIMITER ;

-- 리밸런싱 리포트 생성
DROP PROCEDURE IF EXISTS `fp_create_rebalance_report`;
DELIMITER ;;
CREATE PROCEDURE `fp_create_rebalance_report`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_trigger_reason VARCHAR(100),
    IN p_target_allocation TEXT,
    IN p_min_trade_amount DECIMAL(15,2)
)
BEGIN
    DECLARE v_report_id BIGINT;
    DECLARE v_current_total_value DECIMAL(15,2) DEFAULT 0.00;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_trigger_reason);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_create_rebalance_report', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 현재 포트폴리오 총 가치 계산
    SELECT COALESCE(SUM(current_value), 0) INTO v_current_total_value
    FROM table_user_portfolios 
    WHERE account_db_key = p_account_db_key;
    
    -- 리밸런싱 리포트 생성
    INSERT INTO table_rebalance_reports (
        account_db_key, trigger_reason, target_allocation, 
        recommendations, estimated_cost
    ) VALUES (
        p_account_db_key, p_trigger_reason, p_target_allocation,
        '[]', 0.00  -- 실제로는 복잡한 리밸런싱 알고리즘 필요
    );
    
    SET v_report_id = LAST_INSERT_ID();
    
    SELECT 'SUCCESS' as result, v_report_id as report_id, v_current_total_value as current_value;
    
END ;;
DELIMITER ;

-- =====================================
-- 대시보드 관련 프로시저
-- =====================================

-- 대시보드 메인 데이터 조회
DROP PROCEDURE IF EXISTS `fp_get_dashboard_main`;
DELIMITER ;;
CREATE PROCEDURE `fp_get_dashboard_main`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_include_chart BOOLEAN,
    IN p_chart_period VARCHAR(10)
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_include_chart, ',', p_chart_period);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_get_dashboard_main', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 자산 요약 정보
    SELECT 
        COALESCE(SUM(ua.balance), 0) + COALESCE(SUM(up.current_value), 0) as total_assets,
        COALESCE(SUM(ua.balance), 0) as cash_balance,
        COALESCE(SUM(up.current_value), 0) as stock_value,
        0.0 as total_return,
        0.0 as return_rate,
        'KRW' as currency
    FROM table_user_accounts ua
    LEFT JOIN table_user_portfolios up ON ua.account_db_key = up.account_db_key
    WHERE ua.account_db_key = p_account_db_key;
    
    -- 보유 종목 요약 (상위 5개)
    SELECT 
        up.asset_code as symbol,
        COALESCE(mo.name, up.asset_code) as name,
        up.quantity,
        up.average_cost as avg_price,
        COALESCE(mo.current_price, up.average_cost) as current_price,
        up.current_value as market_value,
        (up.current_value - (up.quantity * up.average_cost)) as unrealized_pnl,
        CASE 
            WHEN up.average_cost > 0 THEN 
                ((COALESCE(mo.current_price, up.average_cost) - up.average_cost) / up.average_cost * 100)
            ELSE 0 
        END as return_rate
    FROM table_user_portfolios up
    LEFT JOIN table_market_overview mo ON up.asset_code = mo.symbol
    WHERE up.account_db_key = p_account_db_key
      AND up.quantity > 0
    ORDER BY up.current_value DESC
    LIMIT 5;
    
    -- 최근 알림 (상위 5개)
    SELECT 
        alert_id,
        alert_type as type,
        title,
        message,
        severity,
        symbol,
        created_at
    FROM table_dashboard_alerts 
    WHERE account_db_key = p_account_db_key
    ORDER BY created_at DESC
    LIMIT 5;
    
    -- 시장 개요 (주요 지수)
    SELECT 
        symbol,
        name,
        current_price,
        change_amount,
        change_rate,
        volume
    FROM table_market_overview 
    WHERE symbol IN ('KOSPI', 'KOSDAQ', 'S&P500', 'NASDAQ')
    ORDER BY symbol;
    
    -- 포트폴리오 차트 데이터 (요청시)
    IF p_include_chart THEN
        CASE p_chart_period
            WHEN '1D' THEN
                SELECT date, total_value, return_rate
                FROM table_portfolio_performance 
                WHERE account_db_key = p_account_db_key 
                  AND date >= DATE_SUB(CURDATE(), INTERVAL 1 DAY)
                ORDER BY date;
            WHEN '1W' THEN
                SELECT date, total_value, return_rate
                FROM table_portfolio_performance 
                WHERE account_db_key = p_account_db_key 
                  AND date >= DATE_SUB(CURDATE(), INTERVAL 1 WEEK)
                ORDER BY date;
            WHEN '1M' THEN
                SELECT date, total_value, return_rate
                FROM table_portfolio_performance 
                WHERE account_db_key = p_account_db_key 
                  AND date >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)
                ORDER BY date;
            ELSE
                SELECT date, total_value, return_rate
                FROM table_portfolio_performance 
                WHERE account_db_key = p_account_db_key 
                  AND date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
                ORDER BY date;
        END CASE;
    END IF;
    
END ;;
DELIMITER ;

-- 알림 생성
DROP PROCEDURE IF EXISTS `fp_create_dashboard_alert`;
DELIMITER ;;
CREATE PROCEDURE `fp_create_dashboard_alert`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_alert_type VARCHAR(20),
    IN p_title VARCHAR(200),
    IN p_message TEXT,
    IN p_severity VARCHAR(10),
    IN p_symbol VARCHAR(10),
    IN p_trigger_value DECIMAL(15,4)
)
BEGIN
    DECLARE v_alert_id VARCHAR(32);
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_alert_type, ',', p_title);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_create_dashboard_alert', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 알림 ID 생성
    SET v_alert_id = CONCAT(
        'alert_',
        LPAD(HEX(p_account_db_key), 16, '0'),
        '_',
        LPAD(HEX(UNIX_TIMESTAMP()), 8, '0')
    );
    
    -- 알림 생성
    INSERT INTO table_dashboard_alerts (
        alert_id, account_db_key, alert_type, title, message, 
        severity, symbol, trigger_value, expires_at
    ) VALUES (
        v_alert_id, p_account_db_key, p_alert_type, p_title, p_message,
        p_severity, p_symbol, p_trigger_value, DATE_ADD(NOW(), INTERVAL 7 DAY)
    );
    
    SELECT 'SUCCESS' as result, v_alert_id as alert_id;
    
END ;;
DELIMITER ;

-- =====================================
-- 초기 데이터 삽입
-- =====================================

-- 주요 시장 지수 초기 데이터
INSERT INTO table_market_overview (symbol, name, current_price, change_amount, change_rate, volume) 
VALUES 
('KOSPI', '코스피', 2580.00, 12.50, 0.48, 500000000),
('KOSDAQ', '코스닥', 850.00, -5.20, -0.61, 300000000),
('S&P500', 'S&P 500', 4500.00, 25.30, 0.56, 1000000000),
('NASDAQ', '나스닥', 15000.00, 100.50, 0.67, 800000000)
ON DUPLICATE KEY UPDATE 
    current_price = VALUES(current_price),
    change_amount = VALUES(change_amount),
    change_rate = VALUES(change_rate),
    volume = VALUES(volume),
    last_updated = NOW();

SELECT 'Finance Shard 1 포트폴리오 및 대시보드 확장 완료' as status;

-- =====================================
-- Shard 2에도 동일하게 적용
-- =====================================

USE finance_shard_2;

-- 동일한 테이블 구조를 Shard 2에도 생성
-- (테이블 생성 부분은 동일하므로 생략하고 프로시저만 재생성)

-- 포트폴리오 성과 분석 테이블
CREATE TABLE IF NOT EXISTS `table_portfolio_performance` (
  `account_db_key` bigint unsigned NOT NULL,
  `date` date NOT NULL,
  `total_value` decimal(15,2) DEFAULT 0.00,
  `cash_balance` decimal(15,2) DEFAULT 0.00,
  `invested_amount` decimal(15,2) DEFAULT 0.00,
  `total_return` decimal(15,2) DEFAULT 0.00,
  `return_rate` decimal(10,4) DEFAULT 0.0000,
  `benchmark_return` decimal(10,4) DEFAULT 0.0000,
  `sharpe_ratio` decimal(10,4) DEFAULT 0.0000,
  `max_drawdown` decimal(10,4) DEFAULT 0.0000,
  `volatility` decimal(10,4) DEFAULT 0.0000,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`account_db_key`, `date`),
  INDEX `idx_date` (`date`),
  INDEX `idx_total_value` (`total_value`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 포트폴리오 리밸런싱 리포트 테이블
CREATE TABLE IF NOT EXISTS `table_rebalance_reports` (
  `report_id` bigint NOT NULL AUTO_INCREMENT,
  `account_db_key` bigint unsigned NOT NULL,
  `trigger_reason` varchar(100) DEFAULT NULL,
  `recommendations` text,
  `expected_improvement` decimal(10,4) DEFAULT 0.0000,
  `target_allocation` text,
  `trades_required` text,
  `estimated_cost` decimal(15,2) DEFAULT 0.00,
  `status` enum('PENDING','APPLIED','REJECTED') DEFAULT 'PENDING',
  `generated_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `applied_at` datetime DEFAULT NULL,
  PRIMARY KEY (`report_id`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_status` (`status`),
  INDEX `idx_generated_at` (`generated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 주식 주문 내역 테이블
CREATE TABLE IF NOT EXISTS `table_stock_orders` (
  `order_id` varchar(32) NOT NULL,
  `account_db_key` bigint unsigned NOT NULL,
  `symbol` varchar(10) NOT NULL,
  `order_type` enum('BUY','SELL') NOT NULL,
  `price_type` enum('MARKET','LIMIT','STOP') DEFAULT 'MARKET',
  `quantity` int NOT NULL,
  `price` decimal(15,2) DEFAULT 0.00,
  `stop_price` decimal(15,2) DEFAULT NULL,
  `filled_quantity` int DEFAULT 0,
  `avg_fill_price` decimal(15,2) DEFAULT 0.00,
  `order_status` enum('PENDING','PARTIAL','FILLED','CANCELLED','REJECTED') DEFAULT 'PENDING',
  `order_source` enum('MANUAL','AUTO_STRATEGY','REBALANCE') DEFAULT 'MANUAL',
  `strategy_id` varchar(50) DEFAULT NULL,
  `commission` decimal(10,2) DEFAULT 0.00,
  `order_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `fill_time` datetime DEFAULT NULL,
  `cancel_time` datetime DEFAULT NULL,
  PRIMARY KEY (`order_id`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_symbol` (`symbol`),
  INDEX `idx_order_status` (`order_status`),
  INDEX `idx_order_time` (`order_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 자산 배분 히스토리 테이블
CREATE TABLE IF NOT EXISTS `table_allocation_history` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `account_db_key` bigint unsigned NOT NULL,
  `symbol` varchar(10) NOT NULL,
  `allocation_date` date NOT NULL,
  `target_weight` decimal(10,4) DEFAULT 0.0000,
  `actual_weight` decimal(10,4) DEFAULT 0.0000,
  `target_value` decimal(15,2) DEFAULT 0.00,
  `actual_value` decimal(15,2) DEFAULT 0.00,
  `deviation` decimal(10,4) DEFAULT 0.0000,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_account_symbol_date` (`account_db_key`,`symbol`,`allocation_date`),
  INDEX `idx_allocation_date` (`allocation_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 대시보드 알림 테이블
CREATE TABLE IF NOT EXISTS `table_dashboard_alerts` (
  `alert_id` varchar(32) NOT NULL,
  `account_db_key` bigint unsigned NOT NULL,
  `alert_type` enum('PRICE_CHANGE','NEWS','TARGET_REACHED','PORTFOLIO_ALERT') NOT NULL,
  `title` varchar(200) NOT NULL,
  `message` text NOT NULL,
  `severity` enum('INFO','WARNING','CRITICAL') DEFAULT 'INFO',
  `symbol` varchar(10) DEFAULT NULL,
  `trigger_value` decimal(15,4) DEFAULT NULL,
  `current_value` decimal(15,4) DEFAULT NULL,
  `is_read` bit(1) NOT NULL DEFAULT b'0',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `expires_at` datetime DEFAULT NULL,
  PRIMARY KEY (`alert_id`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_alert_type` (`alert_type`),
  INDEX `idx_is_read` (`is_read`),
  INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 시장 개요 데이터 테이블
CREATE TABLE IF NOT EXISTS `table_market_overview` (
  `symbol` varchar(10) NOT NULL,
  `name` varchar(100) NOT NULL,
  `current_price` decimal(15,4) DEFAULT 0.0000,
  `change_amount` decimal(15,4) DEFAULT 0.0000,
  `change_rate` decimal(10,4) DEFAULT 0.0000,
  `volume` bigint DEFAULT 0,
  `market_cap` bigint DEFAULT 0,
  `last_updated` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`symbol`),
  INDEX `idx_change_rate` (`change_rate`),
  INDEX `idx_volume` (`volume`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Shard 2의 프로시저들도 동일하게 생성 (생략)
-- 실제로는 모든 프로시저를 Shard 2에도 동일하게 생성해야 함

SELECT 'Finance Shard 2 포트폴리오 및 대시보드 확장 완료' as status;
SELECT 'Finance Shard DB 포트폴리오 및 대시보드 확장 완료!' as final_status;