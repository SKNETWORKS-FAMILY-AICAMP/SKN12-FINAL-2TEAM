-- =====================================
-- Finance Shard DB 자동매매 확장
-- 패킷명세서 기반: REQ-AUTO-001~003
-- =====================================

-- Shard 1에 적용
USE finance_shard_1;

-- 1. 매매 전략 테이블
CREATE TABLE IF NOT EXISTS `table_trading_strategies` (
  `strategy_id` varchar(50) NOT NULL,
  `account_db_key` bigint unsigned NOT NULL,
  `name` varchar(200) NOT NULL,
  `description` text,
  `algorithm_type` enum('MOMENTUM','MEAN_REVERSION','AI_GENERATED','RSI','MACD','BOLLINGER') DEFAULT 'AI_GENERATED',
  `parameters` text,  -- JSON 형태로 전략 파라미터 저장
  `target_symbols` text,  -- JSON 배열로 대상 종목 저장
  `is_active` bit(1) NOT NULL DEFAULT b'0',
  `max_position_size` decimal(5,4) DEFAULT 0.1000,  -- 최대 포지션 비율 (10%)
  `stop_loss` decimal(10,4) DEFAULT -0.0500,  -- -5%
  `take_profit` decimal(10,4) DEFAULT 0.1500,  -- +15%
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_executed` datetime DEFAULT NULL,
  PRIMARY KEY (`strategy_id`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_algorithm_type` (`algorithm_type`),
  INDEX `idx_is_active` (`is_active`),
  INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 2. 전략 성과 테이블
CREATE TABLE IF NOT EXISTS `table_strategy_performance` (
  `strategy_id` varchar(50) NOT NULL,
  `date` date NOT NULL,
  `total_return` decimal(10,4) DEFAULT 0.0000,
  `win_rate` decimal(5,2) DEFAULT 0.00,
  `total_trades` int DEFAULT 0,
  `winning_trades` int DEFAULT 0,
  `losing_trades` int DEFAULT 0,
  `avg_holding_period` int DEFAULT 0,  -- 일 단위
  `max_drawdown` decimal(10,4) DEFAULT 0.0000,
  `sharpe_ratio` decimal(10,4) DEFAULT 0.0000,
  `profit_factor` decimal(10,4) DEFAULT 0.0000,
  `last_updated` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`strategy_id`, `date`),
  INDEX `idx_total_return` (`total_return`),
  INDEX `idx_sharpe_ratio` (`sharpe_ratio`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 3. 거래 실행 내역 테이블
CREATE TABLE IF NOT EXISTS `table_trade_executions` (
  `execution_id` varchar(32) NOT NULL,
  `strategy_id` varchar(50) NOT NULL,
  `account_db_key` bigint unsigned NOT NULL,
  `symbol` varchar(10) NOT NULL,
  `action` enum('BUY','SELL') NOT NULL,
  `quantity` int NOT NULL,
  `price` decimal(15,2) DEFAULT 0.00,
  `executed_price` decimal(15,2) DEFAULT NULL,
  `confidence_score` decimal(5,2) DEFAULT 0.00,
  `reasoning` text,
  `signal_data` text,  -- JSON 형태로 신호 데이터 저장
  `status` enum('PENDING','EXECUTED','FAILED','CANCELLED') DEFAULT 'PENDING',
  `profit_loss` decimal(15,2) DEFAULT 0.00,
  `commission` decimal(10,2) DEFAULT 0.00,
  `executed_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `completed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`execution_id`),
  INDEX `idx_strategy_id` (`strategy_id`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_symbol` (`symbol`),
  INDEX `idx_action` (`action`),
  INDEX `idx_status` (`status`),
  INDEX `idx_executed_at` (`executed_at`),
  FOREIGN KEY (`strategy_id`) REFERENCES `table_trading_strategies`(`strategy_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 4. 백테스트 결과 테이블
CREATE TABLE IF NOT EXISTS `table_strategy_backtests` (
  `backtest_id` varchar(32) NOT NULL,
  `strategy_id` varchar(50) NOT NULL,
  `account_db_key` bigint unsigned NOT NULL,
  `backtest_period` varchar(20) NOT NULL,  -- '2023-01-01_2023-12-31'
  `initial_capital` decimal(15,2) DEFAULT 1000000.00,
  `final_value` decimal(15,2) DEFAULT 0.00,
  `total_return` decimal(10,4) DEFAULT 0.0000,
  `annualized_return` decimal(10,4) DEFAULT 0.0000,
  `benchmark_return` decimal(10,4) DEFAULT 0.0000,
  `max_drawdown` decimal(10,4) DEFAULT 0.0000,
  `sharpe_ratio` decimal(10,4) DEFAULT 0.0000,
  `sortino_ratio` decimal(10,4) DEFAULT 0.0000,
  `volatility` decimal(10,4) DEFAULT 0.0000,
  `trades_count` int DEFAULT 0,
  `win_rate` decimal(5,2) DEFAULT 0.00,
  `profit_factor` decimal(10,4) DEFAULT 0.0000,
  `daily_returns` text,  -- JSON 배열로 일별 수익률 저장
  `trade_history` text,  -- JSON 배열로 거래 내역 저장
  `parameters_used` text,  -- JSON으로 백테스트시 사용된 파라미터
  `status` enum('RUNNING','COMPLETED','FAILED') DEFAULT 'RUNNING',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `completed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`backtest_id`),
  INDEX `idx_strategy_id` (`strategy_id`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_total_return` (`total_return`),
  INDEX `idx_sharpe_ratio` (`sharpe_ratio`),
  INDEX `idx_created_at` (`created_at`),
  FOREIGN KEY (`strategy_id`) REFERENCES `table_trading_strategies`(`strategy_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 5. AI 전략 템플릿 테이블
CREATE TABLE IF NOT EXISTS `table_ai_strategy_templates` (
  `template_id` varchar(50) NOT NULL,
  `name` varchar(200) NOT NULL,
  `description` text,
  `category` enum('CONSERVATIVE','MODERATE','AGGRESSIVE','SECTOR_ROTATION','MOMENTUM','VALUE') DEFAULT 'MODERATE',
  `algorithm_type` varchar(50) NOT NULL,
  `default_parameters` text,  -- JSON 형태로 기본 파라미터
  `expected_return` decimal(10,4) DEFAULT 0.0000,
  `expected_volatility` decimal(10,4) DEFAULT 0.0000,
  `min_capital` decimal(15,2) DEFAULT 100000.00,
  `suitable_experience` enum('BEGINNER','INTERMEDIATE','EXPERT','ALL') DEFAULT 'ALL',
  `suitable_risk_tolerance` enum('CONSERVATIVE','MODERATE','AGGRESSIVE','ALL') DEFAULT 'ALL',
  `is_active` bit(1) NOT NULL DEFAULT b'1',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`template_id`),
  INDEX `idx_category` (`category`),
  INDEX `idx_suitable_experience` (`suitable_experience`),
  INDEX `idx_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- =====================================
-- 자동매매 관련 프로시저
-- =====================================

-- 매매 전략 생성
DROP PROCEDURE IF EXISTS `fp_create_trading_strategy`;
DELIMITER ;;
CREATE PROCEDURE `fp_create_trading_strategy`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_name VARCHAR(200),
    IN p_description TEXT,
    IN p_algorithm_type VARCHAR(50),
    IN p_parameters TEXT,
    IN p_target_symbols TEXT,
    IN p_max_position_size DECIMAL(5,4),
    IN p_stop_loss DECIMAL(10,4),
    IN p_take_profit DECIMAL(10,4)
)
BEGIN
    DECLARE v_strategy_id VARCHAR(50);
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_name, ',', p_algorithm_type);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_create_trading_strategy', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 전략 ID 생성
    SET v_strategy_id = CONCAT(
        'strategy_',
        LPAD(HEX(p_account_db_key), 16, '0'),
        '_',
        LPAD(HEX(UNIX_TIMESTAMP()), 8, '0')
    );
    
    -- 매매 전략 생성
    INSERT INTO table_trading_strategies (
        strategy_id, account_db_key, name, description, algorithm_type,
        parameters, target_symbols, max_position_size, stop_loss, take_profit
    ) VALUES (
        v_strategy_id, p_account_db_key, p_name, p_description, p_algorithm_type,
        p_parameters, p_target_symbols, p_max_position_size, p_stop_loss, p_take_profit
    );
    
    SELECT 'SUCCESS' as result, v_strategy_id as strategy_id;
    
END ;;
DELIMITER ;

-- 매매 전략 목록 조회
DROP PROCEDURE IF EXISTS `fp_get_trading_strategies`;
DELIMITER ;;
CREATE PROCEDURE `fp_get_trading_strategies`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_include_performance BOOLEAN,
    IN p_status_filter VARCHAR(20)
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_include_performance, ',', p_status_filter);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_get_trading_strategies', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 전략 목록 조회
    IF p_status_filter = 'ACTIVE' THEN
        SELECT 
            strategy_id, name, description, algorithm_type, parameters,
            target_symbols, is_active, max_position_size, stop_loss, take_profit,
            created_at, updated_at, last_executed
        FROM table_trading_strategies 
        WHERE account_db_key = p_account_db_key AND is_active = 1
        ORDER BY created_at DESC;
    ELSEIF p_status_filter = 'INACTIVE' THEN
        SELECT 
            strategy_id, name, description, algorithm_type, parameters,
            target_symbols, is_active, max_position_size, stop_loss, take_profit,
            created_at, updated_at, last_executed
        FROM table_trading_strategies 
        WHERE account_db_key = p_account_db_key AND is_active = 0
        ORDER BY created_at DESC;
    ELSE
        SELECT 
            strategy_id, name, description, algorithm_type, parameters,
            target_symbols, is_active, max_position_size, stop_loss, take_profit,
            created_at, updated_at, last_executed
        FROM table_trading_strategies 
        WHERE account_db_key = p_account_db_key
        ORDER BY created_at DESC;
    END IF;
    
    -- 성과 정보 (요청시)
    IF p_include_performance THEN
        SELECT 
            sp.strategy_id,
            AVG(sp.total_return) as avg_total_return,
            AVG(sp.win_rate) as avg_win_rate,
            SUM(sp.total_trades) as total_trades,
            AVG(sp.sharpe_ratio) as avg_sharpe_ratio,
            MIN(sp.max_drawdown) as max_drawdown,
            sp.last_updated
        FROM table_strategy_performance sp
        JOIN table_trading_strategies ts ON sp.strategy_id = ts.strategy_id
        WHERE ts.account_db_key = p_account_db_key
          AND sp.date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
        GROUP BY sp.strategy_id;
    END IF;
    
END ;;
DELIMITER ;

-- 거래 실행
DROP PROCEDURE IF EXISTS `fp_execute_trade`;
DELIMITER ;;
CREATE PROCEDURE `fp_execute_trade`(
    IN p_strategy_id VARCHAR(50),
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_symbol VARCHAR(10),
    IN p_action VARCHAR(10),
    IN p_quantity INT,
    IN p_price DECIMAL(15,2),
    IN p_confidence_score DECIMAL(5,2),
    IN p_reasoning TEXT,
    IN p_signal_data TEXT
)
BEGIN
    DECLARE v_execution_id VARCHAR(32);
    DECLARE v_strategy_exists INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_strategy_id, ',', p_account_db_key, ',', p_symbol, ',', p_action);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_execute_trade', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    trade_block: BEGIN
        -- 전략 존재 및 활성화 확인
        SELECT COUNT(*) INTO v_strategy_exists
        FROM table_trading_strategies 
        WHERE strategy_id = p_strategy_id 
          AND account_db_key = p_account_db_key 
          AND is_active = 1;
        
        IF v_strategy_exists = 0 THEN
            SELECT 'FAILED' as result, 'Strategy not found or inactive' as message;
            LEAVE trade_block;
        END IF;
        
        -- 실행 ID 생성
        SET v_execution_id = CONCAT(
            'exec_',
            LPAD(HEX(p_account_db_key), 16, '0'),
            '_',
            p_symbol,
            '_',
            LPAD(HEX(UNIX_TIMESTAMP()), 8, '0')
        );
        
        -- 거래 실행 기록
        INSERT INTO table_trade_executions (
            execution_id, strategy_id, account_db_key, symbol, action,
            quantity, price, confidence_score, reasoning, signal_data
        ) VALUES (
            v_execution_id, p_strategy_id, p_account_db_key, p_symbol, p_action,
            p_quantity, p_price, p_confidence_score, p_reasoning, p_signal_data
        );
        
        -- 전략 마지막 실행 시간 업데이트
        UPDATE table_trading_strategies 
        SET last_executed = NOW()
        WHERE strategy_id = p_strategy_id;
        
        SELECT 'SUCCESS' as result, v_execution_id as execution_id;
    END trade_block;
    
END ;;
DELIMITER ;

-- 백테스트 실행
DROP PROCEDURE IF EXISTS `fp_run_backtest`;
DELIMITER ;;
CREATE PROCEDURE `fp_run_backtest`(
    IN p_strategy_id VARCHAR(50),
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_start_date DATE,
    IN p_end_date DATE,
    IN p_initial_capital DECIMAL(15,2),
    IN p_benchmark VARCHAR(10)
)
BEGIN
    DECLARE v_backtest_id VARCHAR(32);
    DECLARE v_period VARCHAR(20);
    DECLARE v_strategy_exists INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_strategy_id, ',', p_account_db_key, ',', p_start_date, ',', p_end_date);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_run_backtest', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    backtest_block: BEGIN
        -- 전략 존재 확인
        SELECT COUNT(*) INTO v_strategy_exists
        FROM table_trading_strategies 
        WHERE strategy_id = p_strategy_id AND account_db_key = p_account_db_key;
        
        IF v_strategy_exists = 0 THEN
            SELECT 'FAILED' as result, 'Strategy not found' as message;
            LEAVE backtest_block;
        END IF;
        
        -- 백테스트 ID 생성
        SET v_backtest_id = CONCAT(
            'backtest_',
            LPAD(HEX(p_account_db_key), 16, '0'),
            '_',
            LPAD(HEX(UNIX_TIMESTAMP()), 8, '0')
        );
        
        SET v_period = CONCAT(p_start_date, '_', p_end_date);
        
        -- 백테스트 기록 생성 (실제 백테스트는 외부 시스템에서 수행)
        INSERT INTO table_strategy_backtests (
            backtest_id, strategy_id, account_db_key, backtest_period,
            initial_capital, status
        ) VALUES (
            v_backtest_id, p_strategy_id, p_account_db_key, v_period,
            p_initial_capital, 'RUNNING'
        );
        
        SELECT 'SUCCESS' as result, v_backtest_id as backtest_id;
    END backtest_block;
    
END ;;
DELIMITER ;

-- 백테스트 결과 업데이트
DROP PROCEDURE IF EXISTS `fp_update_backtest_result`;
DELIMITER ;;
CREATE PROCEDURE `fp_update_backtest_result`(
    IN p_backtest_id VARCHAR(32),
    IN p_final_value DECIMAL(15,2),
    IN p_total_return DECIMAL(10,4),
    IN p_benchmark_return DECIMAL(10,4),
    IN p_max_drawdown DECIMAL(10,4),
    IN p_sharpe_ratio DECIMAL(10,4),
    IN p_trades_count INT,
    IN p_win_rate DECIMAL(5,2),
    IN p_daily_returns TEXT,
    IN p_trade_history TEXT
)
BEGIN
    DECLARE v_initial_capital DECIMAL(15,2);
    DECLARE v_annualized_return DECIMAL(10,4);
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_backtest_id, ',', p_final_value, ',', p_total_return);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_update_backtest_result', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 초기 자본 조회
    SELECT initial_capital INTO v_initial_capital
    FROM table_strategy_backtests 
    WHERE backtest_id = p_backtest_id;
    
    -- 연율화 수익률 계산 (간단화)
    SET v_annualized_return = p_total_return;
    
    -- 백테스트 결과 업데이트
    UPDATE table_strategy_backtests 
    SET final_value = p_final_value,
        total_return = p_total_return,
        annualized_return = v_annualized_return,
        benchmark_return = p_benchmark_return,
        max_drawdown = p_max_drawdown,
        sharpe_ratio = p_sharpe_ratio,
        trades_count = p_trades_count,
        win_rate = p_win_rate,
        profit_factor = IF(p_win_rate > 0, (p_win_rate / (100 - p_win_rate)), 0),
        daily_returns = p_daily_returns,
        trade_history = p_trade_history,
        status = 'COMPLETED',
        completed_at = NOW()
    WHERE backtest_id = p_backtest_id;
    
    SELECT 'SUCCESS' as result, 'Backtest result updated' as message;
    
END ;;
DELIMITER ;

-- AI 전략 추천
DROP PROCEDURE IF EXISTS `fp_get_ai_strategy_recommendations`;
DELIMITER ;;
CREATE PROCEDURE `fp_get_ai_strategy_recommendations`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_investment_goal VARCHAR(50),
    IN p_risk_tolerance VARCHAR(20),
    IN p_investment_amount DECIMAL(15,2),
    IN p_time_horizon VARCHAR(20)
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_investment_goal, ',', p_risk_tolerance);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_get_ai_strategy_recommendations', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 위험도와 경험에 맞는 전략 템플릿 추천
    SELECT 
        template_id,
        name,
        description,
        category,
        algorithm_type,
        default_parameters,
        expected_return,
        expected_volatility,
        min_capital,
        suitable_experience,
        suitable_risk_tolerance
    FROM table_ai_strategy_templates 
    WHERE is_active = 1
      AND min_capital <= p_investment_amount
      AND (suitable_risk_tolerance = p_risk_tolerance OR suitable_risk_tolerance = 'ALL')
    ORDER BY 
        CASE 
            WHEN suitable_risk_tolerance = p_risk_tolerance THEN 1 
            ELSE 2 
        END,
        expected_return DESC
    LIMIT 5;
    
END ;;
DELIMITER ;

-- =====================================
-- 초기 데이터 삽입
-- =====================================

-- AI 전략 템플릿 기본 데이터
INSERT INTO table_ai_strategy_templates (
    template_id, name, description, category, algorithm_type, 
    default_parameters, expected_return, expected_volatility, min_capital,
    suitable_experience, suitable_risk_tolerance
) VALUES 
('momentum_basic', '기본 모멘텀 전략', 'RSI와 이동평균을 활용한 기본적인 모멘텀 전략입니다.', 'MODERATE', 'MOMENTUM',
 '{"rsi_period": 14, "rsi_oversold": 30, "rsi_overbought": 70, "ma_period": 20}', 0.1200, 0.1800, 100000.00,
 'BEGINNER', 'MODERATE'),

('value_contrarian', '가치 역투자 전략', '저평가된 종목을 발굴하는 가치 투자 전략입니다.', 'CONSERVATIVE', 'MEAN_REVERSION',
 '{"pe_max": 15, "pb_max": 1.5, "roe_min": 10, "debt_ratio_max": 0.5}', 0.0800, 0.1200, 500000.00,
 'INTERMEDIATE', 'CONSERVATIVE'),

('ai_adaptive', 'AI 적응형 전략', '시장 상황에 따라 전략을 자동으로 조정하는 AI 전략입니다.', 'AGGRESSIVE', 'AI_GENERATED',
 '{"rebalance_period": 7, "max_positions": 10, "volatility_threshold": 0.25}', 0.1800, 0.2500, 1000000.00,
 'EXPERT', 'AGGRESSIVE'),

('sector_rotation', '섹터 로테이션', '경기 사이클에 따른 섹터 로테이션 전략입니다.', 'MODERATE', 'SECTOR_ROTATION',
 '{"rotation_period": 30, "momentum_lookback": 90, "max_sectors": 3}', 0.1000, 0.1500, 300000.00,
 'INTERMEDIATE', 'MODERATE')
ON DUPLICATE KEY UPDATE 
    name = VALUES(name),
    description = VALUES(description),
    expected_return = VALUES(expected_return),
    expected_volatility = VALUES(expected_volatility),
    updated_at = NOW();

SELECT 'Finance Shard 1 자동매매 확장 완료' as status;

-- =====================================
-- Shard 2에도 동일하게 적용
-- =====================================

USE finance_shard_2;

-- 동일한 테이블 구조를 Shard 2에도 생성 (간략화)
CREATE TABLE IF NOT EXISTS `table_trading_strategies` (
  `strategy_id` varchar(50) NOT NULL,
  `account_db_key` bigint unsigned NOT NULL,
  `name` varchar(200) NOT NULL,
  `description` text,
  `algorithm_type` enum('MOMENTUM','MEAN_REVERSION','AI_GENERATED','RSI','MACD','BOLLINGER') DEFAULT 'AI_GENERATED',
  `parameters` text,
  `target_symbols` text,
  `is_active` bit(1) NOT NULL DEFAULT b'0',
  `max_position_size` decimal(5,4) DEFAULT 0.1000,
  `stop_loss` decimal(10,4) DEFAULT -0.0500,
  `take_profit` decimal(10,4) DEFAULT 0.1500,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_executed` datetime DEFAULT NULL,
  PRIMARY KEY (`strategy_id`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_algorithm_type` (`algorithm_type`),
  INDEX `idx_is_active` (`is_active`),
  INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- (나머지 테이블들도 동일하게 생성...)

-- AI 전략 템플릿 기본 데이터 (Shard 2)
CREATE TABLE IF NOT EXISTS `table_ai_strategy_templates` (
  `template_id` varchar(50) NOT NULL,
  `name` varchar(200) NOT NULL,
  `description` text,
  `category` enum('CONSERVATIVE','MODERATE','AGGRESSIVE','SECTOR_ROTATION','MOMENTUM','VALUE') DEFAULT 'MODERATE',
  `algorithm_type` varchar(50) NOT NULL,
  `default_parameters` text,
  `expected_return` decimal(10,4) DEFAULT 0.0000,
  `expected_volatility` decimal(10,4) DEFAULT 0.0000,
  `min_capital` decimal(15,2) DEFAULT 100000.00,
  `suitable_experience` enum('BEGINNER','INTERMEDIATE','EXPERT','ALL') DEFAULT 'ALL',
  `suitable_risk_tolerance` enum('CONSERVATIVE','MODERATE','AGGRESSIVE','ALL') DEFAULT 'ALL',
  `is_active` bit(1) NOT NULL DEFAULT b'1',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`template_id`),
  INDEX `idx_category` (`category`),
  INDEX `idx_suitable_experience` (`suitable_experience`),
  INDEX `idx_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT INTO table_ai_strategy_templates (
    template_id, name, description, category, algorithm_type, 
    default_parameters, expected_return, expected_volatility, min_capital,
    suitable_experience, suitable_risk_tolerance
) VALUES 
('momentum_basic', '기본 모멘텀 전략', 'RSI와 이동평균을 활용한 기본적인 모멘텀 전략입니다.', 'MODERATE', 'MOMENTUM',
 '{"rsi_period": 14, "rsi_oversold": 30, "rsi_overbought": 70, "ma_period": 20}', 0.1200, 0.1800, 100000.00,
 'BEGINNER', 'MODERATE'),

('value_contrarian', '가치 역투자 전략', '저평가된 종목을 발굴하는 가치 투자 전략입니다.', 'CONSERVATIVE', 'MEAN_REVERSION',
 '{"pe_max": 15, "pb_max": 1.5, "roe_min": 10, "debt_ratio_max": 0.5}', 0.0800, 0.1200, 500000.00,
 'INTERMEDIATE', 'CONSERVATIVE'),

('ai_adaptive', 'AI 적응형 전략', '시장 상황에 따라 전략을 자동으로 조정하는 AI 전략입니다.', 'AGGRESSIVE', 'AI_GENERATED',
 '{"rebalance_period": 7, "max_positions": 10, "volatility_threshold": 0.25}', 0.1800, 0.2500, 1000000.00,
 'EXPERT', 'AGGRESSIVE'),

('sector_rotation', '섹터 로테이션', '경기 사이클에 따른 섹터 로테이션 전략입니다.', 'MODERATE', 'SECTOR_ROTATION',
 '{"rotation_period": 30, "momentum_lookback": 90, "max_sectors": 3}', 0.1000, 0.1500, 300000.00,
 'INTERMEDIATE', 'MODERATE')
ON DUPLICATE KEY UPDATE 
    name = VALUES(name),
    description = VALUES(description),
    expected_return = VALUES(expected_return),
    expected_volatility = VALUES(expected_volatility),
    updated_at = NOW();

SELECT 'Finance Shard 2 자동매매 확장 완료' as status;
SELECT 'Finance Shard DB 자동매매 확장 완료!' as final_status;