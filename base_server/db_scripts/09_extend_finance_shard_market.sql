-- =====================================
-- Finance Shard DB 시장 데이터 및 알림 확장
-- 패킷명세서 기반: 시장 데이터, 알림 시스템
-- =====================================

-- Shard 1에 적용
USE finance_shard_1;

-- 1. 종목 기본 정보 테이블
CREATE TABLE IF NOT EXISTS `table_securities_info` (
  `symbol` varchar(10) NOT NULL,
  `name` varchar(100) NOT NULL,
  `exchange` varchar(20) DEFAULT 'KRX',
  `sector` varchar(50) DEFAULT NULL,
  `industry` varchar(100) DEFAULT NULL,
  `market_cap` bigint DEFAULT 0,
  `currency` varchar(3) DEFAULT 'KRW',
  `description` text,
  `listing_date` date DEFAULT NULL,
  `is_active` bit(1) NOT NULL DEFAULT b'1',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`symbol`),
  INDEX `idx_exchange` (`exchange`),
  INDEX `idx_sector` (`sector`),
  INDEX `idx_market_cap` (`market_cap`),
  INDEX `idx_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 2. 가격 데이터 테이블 (일봉)
CREATE TABLE IF NOT EXISTS `table_price_data_daily` (
  `symbol` varchar(10) NOT NULL,
  `date` date NOT NULL,
  `open_price` decimal(15,4) DEFAULT 0.0000,
  `high_price` decimal(15,4) DEFAULT 0.0000,
  `low_price` decimal(15,4) DEFAULT 0.0000,
  `close_price` decimal(15,4) DEFAULT 0.0000,
  `volume` bigint DEFAULT 0,
  `adj_close_price` decimal(15,4) DEFAULT 0.0000,
  `change_amount` decimal(15,4) DEFAULT 0.0000,
  `change_rate` decimal(10,4) DEFAULT 0.0000,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`symbol`, `date`),
  INDEX `idx_date` (`date`),
  INDEX `idx_close_price` (`close_price`),
  INDEX `idx_volume` (`volume`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 3. 실시간 가격 데이터 테이블
CREATE TABLE IF NOT EXISTS `table_price_data_realtime` (
  `symbol` varchar(10) NOT NULL,
  `timestamp` datetime NOT NULL,
  `price` decimal(15,4) DEFAULT 0.0000,
  `volume` int DEFAULT 0,
  `bid_price` decimal(15,4) DEFAULT 0.0000,
  `ask_price` decimal(15,4) DEFAULT 0.0000,
  `bid_volume` int DEFAULT 0,
  `ask_volume` int DEFAULT 0,
  PRIMARY KEY (`symbol`, `timestamp`),
  INDEX `idx_timestamp` (`timestamp`),
  INDEX `idx_price` (`price`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 4. 기술적 지표 테이블
CREATE TABLE IF NOT EXISTS `table_technical_indicators` (
  `symbol` varchar(10) NOT NULL,
  `date` date NOT NULL,
  `rsi_14` decimal(10,4) DEFAULT NULL,
  `rsi_30` decimal(10,4) DEFAULT NULL,
  `macd` decimal(15,6) DEFAULT NULL,
  `macd_signal` decimal(15,6) DEFAULT NULL,
  `macd_histogram` decimal(15,6) DEFAULT NULL,
  `bollinger_upper` decimal(15,4) DEFAULT NULL,
  `bollinger_middle` decimal(15,4) DEFAULT NULL,
  `bollinger_lower` decimal(15,4) DEFAULT NULL,
  `ma5` decimal(15,4) DEFAULT NULL,
  `ma10` decimal(15,4) DEFAULT NULL,
  `ma20` decimal(15,4) DEFAULT NULL,
  `ma50` decimal(15,4) DEFAULT NULL,
  `ma60` decimal(15,4) DEFAULT NULL,
  `ma120` decimal(15,4) DEFAULT NULL,
  `stochastic_k` decimal(10,4) DEFAULT NULL,
  `stochastic_d` decimal(10,4) DEFAULT NULL,
  `williams_r` decimal(10,4) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`symbol`, `date`),
  INDEX `idx_date` (`date`),
  INDEX `idx_rsi_14` (`rsi_14`),
  INDEX `idx_macd` (`macd`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 5. 뉴스 데이터 테이블
CREATE TABLE IF NOT EXISTS `table_news_items` (
  `news_id` varchar(32) NOT NULL,
  `title` text NOT NULL,
  `content` longtext,
  `summary` text,
  `source` varchar(100) DEFAULT NULL,
  `author` varchar(100) DEFAULT NULL,
  `published_at` datetime NOT NULL,
  `url` varchar(1000) DEFAULT NULL,
  `category` enum('MARKET','ECONOMY','TECH','POLITICS','CORPORATE','EARNINGS') DEFAULT 'MARKET',
  `sentiment_score` decimal(5,2) DEFAULT 0.00,  -- -1.0 ~ 1.0
  `related_symbols` text,  -- JSON 배열로 관련 종목 저장
  `language` varchar(5) DEFAULT 'ko',
  `is_active` bit(1) NOT NULL DEFAULT b'1',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`news_id`),
  INDEX `idx_published_at` (`published_at`),
  INDEX `idx_source` (`source`),
  INDEX `idx_category` (`category`),
  INDEX `idx_sentiment_score` (`sentiment_score`),
  INDEX `idx_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 6. 가격 알림 설정 테이블
CREATE TABLE IF NOT EXISTS `table_price_alerts` (
  `alert_id` varchar(32) NOT NULL,
  `account_db_key` bigint unsigned NOT NULL,
  `symbol` varchar(10) NOT NULL,
  `alert_type` enum('PRICE_ABOVE','PRICE_BELOW','CHANGE_RATE_ABOVE','CHANGE_RATE_BELOW','VOLUME_SPIKE') NOT NULL,
  `target_value` decimal(15,4) NOT NULL,
  `current_value` decimal(15,4) DEFAULT 0.0000,
  `condition_met` bit(1) NOT NULL DEFAULT b'0',
  `is_active` bit(1) NOT NULL DEFAULT b'1',
  `notification_sent` bit(1) NOT NULL DEFAULT b'0',
  `message` varchar(500) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `triggered_at` datetime DEFAULT NULL,
  `expires_at` datetime DEFAULT NULL,
  PRIMARY KEY (`alert_id`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_symbol` (`symbol`),
  INDEX `idx_alert_type` (`alert_type`),
  INDEX `idx_is_active` (`is_active`),
  INDEX `idx_condition_met` (`condition_met`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 7. 알림 규칙 테이블
CREATE TABLE IF NOT EXISTS `table_alert_rules` (
  `rule_id` varchar(32) NOT NULL,
  `account_db_key` bigint unsigned NOT NULL,
  `name` varchar(200) NOT NULL,
  `description` text,
  `rule_type` enum('PRICE','VOLUME','NEWS','PORTFOLIO','TECHNICAL') NOT NULL,
  `conditions` text NOT NULL,  -- JSON 형태로 조건 저장
  `actions` text NOT NULL,  -- JSON 배열로 액션 저장 (EMAIL, PUSH, SMS)
  `priority` enum('LOW','NORMAL','HIGH','URGENT') DEFAULT 'NORMAL',
  `is_active` bit(1) NOT NULL DEFAULT b'1',
  `last_triggered` datetime DEFAULT NULL,
  `trigger_count` int DEFAULT 0,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`rule_id`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_rule_type` (`rule_type`),
  INDEX `idx_is_active` (`is_active`),
  INDEX `idx_priority` (`priority`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 8. 알림 내역 테이블
CREATE TABLE IF NOT EXISTS `table_notifications` (
  `notification_id` varchar(32) NOT NULL,
  `account_db_key` bigint unsigned NOT NULL,
  `title` varchar(200) NOT NULL,
  `message` text NOT NULL,
  `type` enum('PRICE_ALERT','NEWS','PORTFOLIO','TRADE','SYSTEM','RECOMMENDATION') NOT NULL,
  `priority` enum('LOW','NORMAL','HIGH','URGENT') DEFAULT 'NORMAL',
  `data` text,  -- JSON 형태로 추가 데이터 저장
  `is_read` bit(1) NOT NULL DEFAULT b'0',
  `read_at` datetime DEFAULT NULL,
  `delivery_method` enum('PUSH','EMAIL','SMS','IN_APP') DEFAULT 'IN_APP',
  `delivery_status` enum('PENDING','SENT','DELIVERED','FAILED') DEFAULT 'PENDING',
  `related_alert_id` varchar(32) DEFAULT NULL,
  `related_rule_id` varchar(32) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `expires_at` datetime DEFAULT NULL,
  PRIMARY KEY (`notification_id`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_type` (`type`),
  INDEX `idx_priority` (`priority`),
  INDEX `idx_is_read` (`is_read`),
  INDEX `idx_created_at` (`created_at`),
  INDEX `idx_delivery_status` (`delivery_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- =====================================
-- 시장 데이터 관련 프로시저
-- =====================================

-- 종목 검색
DROP PROCEDURE IF EXISTS `fp_search_securities`;
DELIMITER ;;
CREATE PROCEDURE `fp_search_securities`(
    IN p_query VARCHAR(100),
    IN p_exchange VARCHAR(20),
    IN p_sector VARCHAR(50),
    IN p_limit INT
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_query, ',', COALESCE(p_exchange, 'NULL'), ',', COALESCE(p_sector, 'NULL'), ',', p_limit);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_search_securities', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 종목 검색 (심볼, 이름으로 검색)
    SELECT 
        symbol,
        name,
        exchange,
        sector,
        industry,
        market_cap,
        currency,
        description
    FROM table_securities_info 
    WHERE is_active = 1
      AND (symbol LIKE CONCAT('%', p_query, '%') OR name LIKE CONCAT('%', p_query, '%'))
      AND (p_exchange IS NULL OR exchange = p_exchange)
      AND (p_sector IS NULL OR sector = p_sector)
    ORDER BY 
        CASE WHEN symbol = p_query THEN 1
             WHEN symbol LIKE CONCAT(p_query, '%') THEN 2
             WHEN name LIKE CONCAT(p_query, '%') THEN 3
             ELSE 4 END,
        market_cap DESC
    LIMIT p_limit;
    
    -- 총 검색 결과 수
    SELECT COUNT(*) as total_count
    FROM table_securities_info 
    WHERE is_active = 1
      AND (symbol LIKE CONCAT('%', p_query, '%') OR name LIKE CONCAT('%', p_query, '%'))
      AND (p_exchange IS NULL OR exchange = p_exchange)
      AND (p_sector IS NULL OR sector = p_sector);
    
END ;;
DELIMITER ;

-- 가격 데이터 조회
DROP PROCEDURE IF EXISTS `fp_get_price_data`;
DELIMITER ;;
CREATE PROCEDURE `fp_get_price_data`(
    IN p_symbols TEXT,  -- JSON 배열 형태
    IN p_period VARCHAR(10),  -- 1D, 1W, 1M, 3M, 1Y
    IN p_interval VARCHAR(10) -- 1m, 5m, 1h, 1d
)
BEGIN
    -- 변수 선언 (먼저)
    DECLARE v_start_date DATE;
    DECLARE v_symbol VARCHAR(10);
    DECLARE v_done INT DEFAULT FALSE;
    DECLARE ProcParam VARCHAR(4000);
    
    -- 커서 선언 (두 번째)
    DECLARE v_symbols_cursor CURSOR FOR 
        SELECT JSON_UNQUOTE(JSON_EXTRACT(p_symbols, CONCAT('$[', idx, ']'))) as symbol
        FROM (
            SELECT 0 as idx UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 
            UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9
        ) numbers
        WHERE JSON_EXTRACT(p_symbols, CONCAT('$[', idx, ']')) IS NOT NULL;
    
    -- 핸들러 선언 (마지막)
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = TRUE;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_symbols, ',', p_period, ',', p_interval);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_get_price_data', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 기간에 따른 시작 날짜 설정
    CASE p_period
        WHEN '1D' THEN SET v_start_date = DATE_SUB(CURDATE(), INTERVAL 1 DAY);
        WHEN '1W' THEN SET v_start_date = DATE_SUB(CURDATE(), INTERVAL 1 WEEK);
        WHEN '1M' THEN SET v_start_date = DATE_SUB(CURDATE(), INTERVAL 1 MONTH);
        WHEN '3M' THEN SET v_start_date = DATE_SUB(CURDATE(), INTERVAL 3 MONTH);
        WHEN '1Y' THEN SET v_start_date = DATE_SUB(CURDATE(), INTERVAL 1 YEAR);
        ELSE SET v_start_date = DATE_SUB(CURDATE(), INTERVAL 1 YEAR);
    END CASE;
    
    -- 가격 데이터 조회 (일봉만 지원, 실제로는 interval에 따라 다른 테이블 조회)
    SELECT 
        pd.symbol,
        pd.date as timestamp,
        pd.open_price,
        pd.high_price,
        pd.low_price,
        pd.close_price,
        pd.volume,
        pd.change_amount,
        pd.change_rate
    FROM table_price_data_daily pd
    WHERE pd.date >= v_start_date
      AND JSON_CONTAINS(p_symbols, JSON_QUOTE(pd.symbol))
    ORDER BY pd.symbol, pd.date;
    
END ;;
DELIMITER ;

-- 기술적 지표 조회
DROP PROCEDURE IF EXISTS `fp_get_technical_indicators`;
DELIMITER ;;
CREATE PROCEDURE `fp_get_technical_indicators`(
    IN p_symbols TEXT  -- JSON 배열 형태
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_symbols);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_get_technical_indicators', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 최신 기술적 지표 조회
    SELECT 
        ti.symbol,
        ti.date,
        ti.rsi_14 as rsi,
        ti.macd,
        ti.macd_signal,
        ti.bollinger_upper,
        ti.bollinger_middle,
        ti.bollinger_lower,
        ti.ma5,
        ti.ma20,
        ti.ma60,
        ti.stochastic_k,
        ti.stochastic_d,
        ti.williams_r
    FROM table_technical_indicators ti
    INNER JOIN (
        SELECT symbol, MAX(date) as max_date
        FROM table_technical_indicators
        WHERE JSON_CONTAINS(p_symbols, JSON_QUOTE(symbol))
        GROUP BY symbol
    ) latest ON ti.symbol = latest.symbol AND ti.date = latest.max_date;
    
END ;;
DELIMITER ;

-- =====================================
-- 뉴스 관련 프로시저
-- =====================================

-- 뉴스 조회
DROP PROCEDURE IF EXISTS `fp_get_news`;
DELIMITER ;;
CREATE PROCEDURE `fp_get_news`(
    IN p_symbols TEXT,  -- JSON 배열 형태 (NULL이면 전체)
    IN p_category VARCHAR(20),
    IN p_page INT,
    IN p_limit INT
)
BEGIN
    DECLARE v_offset INT;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(COALESCE(p_symbols, 'NULL'), ',', COALESCE(p_category, 'NULL'), ',', p_page, ',', p_limit);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_get_news', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    SET v_offset = (p_page - 1) * p_limit;
    
    -- 뉴스 목록 조회
    SELECT 
        news_id,
        title,
        summary,
        source,
        published_at,
        url,
        category,
        sentiment_score,
        related_symbols
    FROM table_news_items 
    WHERE is_active = 1
      AND (p_category IS NULL OR p_category = 'ALL' OR category = p_category)
      AND (p_symbols IS NULL OR 
           EXISTS (
               SELECT 1 FROM JSON_TABLE(related_symbols, '$[*]' COLUMNS (symbol VARCHAR(10) PATH '$')) jt
               WHERE JSON_CONTAINS(p_symbols, JSON_QUOTE(jt.symbol))
           ))
    ORDER BY published_at DESC
    LIMIT p_limit OFFSET v_offset;
    
    -- 전체 개수
    SELECT COUNT(*) as total_count
    FROM table_news_items 
    WHERE is_active = 1
      AND (p_category IS NULL OR p_category = 'ALL' OR category = p_category)
      AND (p_symbols IS NULL OR 
           EXISTS (
               SELECT 1 FROM JSON_TABLE(related_symbols, '$[*]' COLUMNS (symbol VARCHAR(10) PATH '$')) jt
               WHERE JSON_CONTAINS(p_symbols, JSON_QUOTE(jt.symbol))
           ));
    
    -- 감정 분석 요약
    SELECT 
        AVG(sentiment_score) as avg_sentiment,
        COUNT(CASE WHEN sentiment_score > 0.1 THEN 1 END) as positive_count,
        COUNT(CASE WHEN sentiment_score < -0.1 THEN 1 END) as negative_count,
        COUNT(CASE WHEN sentiment_score BETWEEN -0.1 AND 0.1 THEN 1 END) as neutral_count
    FROM table_news_items 
    WHERE is_active = 1
      AND published_at >= DATE_SUB(NOW(), INTERVAL 1 DAY)
      AND (p_category IS NULL OR p_category = 'ALL' OR category = p_category)
      AND (p_symbols IS NULL OR 
           EXISTS (
               SELECT 1 FROM JSON_TABLE(related_symbols, '$[*]' COLUMNS (symbol VARCHAR(10) PATH '$')) jt
               WHERE JSON_CONTAINS(p_symbols, JSON_QUOTE(jt.symbol))
           ));
    
END ;;
DELIMITER ;

-- =====================================
-- 알림 관련 프로시저
-- =====================================

-- 가격 알림 생성
DROP PROCEDURE IF EXISTS `fp_create_price_alert`;
DELIMITER ;;
CREATE PROCEDURE `fp_create_price_alert`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_symbol VARCHAR(10),
    IN p_alert_type VARCHAR(20),
    IN p_target_value DECIMAL(15,4),
    IN p_message VARCHAR(500)
)
BEGIN
    DECLARE v_alert_id VARCHAR(32);
    DECLARE v_current_value DECIMAL(15,4) DEFAULT 0.0000;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_symbol, ',', p_alert_type, ',', p_target_value);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_create_price_alert', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 알림 ID 생성
    SET v_alert_id = CONCAT(
        'alert_',
        LPAD(HEX(p_account_db_key), 16, '0'),
        '_',
        p_symbol,
        '_',
        LPAD(HEX(UNIX_TIMESTAMP()), 8, '0')
    );
    
    -- 현재 가격 조회
    SELECT close_price INTO v_current_value
    FROM table_price_data_daily 
    WHERE symbol = p_symbol 
    ORDER BY date DESC 
    LIMIT 1;
    
    -- 가격 알림 생성
    INSERT INTO table_price_alerts (
        alert_id, account_db_key, symbol, alert_type, target_value, 
        current_value, message, expires_at
    ) VALUES (
        v_alert_id, p_account_db_key, p_symbol, p_alert_type, p_target_value,
        v_current_value, p_message, DATE_ADD(NOW(), INTERVAL 30 DAY)
    );
    
    SELECT 'SUCCESS' as result, v_alert_id as alert_id;
    
END ;;
DELIMITER ;

-- 알림 목록 조회
DROP PROCEDURE IF EXISTS `fp_get_notifications`;
DELIMITER ;;
CREATE PROCEDURE `fp_get_notifications`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_type_filter VARCHAR(20),
    IN p_read_status VARCHAR(10),
    IN p_page INT,
    IN p_limit INT
)
BEGIN
    DECLARE v_offset INT;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', COALESCE(p_type_filter, 'NULL'), ',', COALESCE(p_read_status, 'NULL'), ',', p_page, ',', p_limit);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_get_notifications', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    SET v_offset = (p_page - 1) * p_limit;
    
    -- 알림 목록 조회
    SELECT 
        notification_id,
        title,
        message,
        type,
        priority,
        data,
        is_read,
        read_at,
        delivery_method,
        delivery_status,
        created_at,
        expires_at
    FROM table_notifications 
    WHERE account_db_key = p_account_db_key
      AND (expires_at IS NULL OR expires_at > NOW())
      AND (p_type_filter IS NULL OR p_type_filter = 'ALL' OR type = p_type_filter)
      AND (p_read_status IS NULL OR p_read_status = 'ALL' OR 
           (p_read_status = 'READ' AND is_read = 1) OR 
           (p_read_status = 'unread' AND is_read = 0))
    ORDER BY 
        CASE priority 
            WHEN 'URGENT' THEN 1 
            WHEN 'HIGH' THEN 2 
            WHEN 'NORMAL' THEN 3 
            WHEN 'LOW' THEN 4 
        END,
        created_at DESC
    LIMIT p_limit OFFSET v_offset;
    
    -- 전체 개수 및 읽지 않은 개수
    SELECT 
        COUNT(*) as total_count,
        COUNT(CASE WHEN is_read = 0 THEN 1 END) as unread_count
    FROM table_notifications 
    WHERE account_db_key = p_account_db_key
      AND (expires_at IS NULL OR expires_at > NOW())
      AND (p_type_filter IS NULL OR p_type_filter = 'ALL' OR type = p_type_filter);
    
END ;;
DELIMITER ;

-- 알림 읽음 처리
DROP PROCEDURE IF EXISTS `fp_mark_notifications_read`;
DELIMITER ;;
CREATE PROCEDURE `fp_mark_notifications_read`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_notification_ids TEXT  -- JSON 배열 형태
)
BEGIN
    DECLARE v_updated_count INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_notification_ids);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_mark_notifications_read', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 알림 읽음 처리
    UPDATE table_notifications 
    SET is_read = 1, read_at = NOW()
    WHERE account_db_key = p_account_db_key
      AND JSON_CONTAINS(p_notification_ids, JSON_QUOTE(notification_id))
      AND is_read = 0;
    
    SET v_updated_count = ROW_COUNT();
    
    SELECT 'SUCCESS' as result, v_updated_count as updated_count;
    
END ;;
DELIMITER ;

-- =====================================
-- 초기 데이터 삽입
-- =====================================

-- 주요 종목 기본 정보
INSERT INTO table_securities_info (symbol, name, exchange, sector, industry, market_cap, currency, description) 
VALUES 
('005930', '삼성전자', 'KRX', 'Technology', 'Semiconductors', 400000000000000, 'KRW', '대한민국 최대 종합 전자 기업'),
('035420', 'NAVER', 'KRX', 'Technology', 'Internet Services', 50000000000000, 'KRW', '대한민국 대표 인터넷 기업'),
('000660', 'SK하이닉스', 'KRX', 'Technology', 'Semiconductors', 80000000000000, 'KRW', '메모리 반도체 전문 기업'),
('035720', '카카오', 'KRX', 'Technology', 'Internet Services', 30000000000000, 'KRW', '모바일 플랫폼 기업'),
('207940', '삼성바이오로직스', 'KRX', 'Healthcare', 'Biotechnology', 60000000000000, 'KRW', '바이오의약품 위탁생산 기업')
ON DUPLICATE KEY UPDATE 
    name = VALUES(name),
    market_cap = VALUES(market_cap),
    description = VALUES(description),
    updated_at = NOW();

-- 샘플 가격 데이터 (최근 일주일)
INSERT INTO table_price_data_daily (symbol, date, open_price, high_price, low_price, close_price, volume, change_amount, change_rate) 
VALUES 
('005930', CURDATE(), 68000, 69500, 67500, 68500, 15000000, 500, 0.73),
('005930', DATE_SUB(CURDATE(), INTERVAL 1 DAY), 67500, 68200, 67000, 68000, 12000000, -200, -0.29),
('035420', CURDATE(), 185000, 187000, 183000, 186000, 800000, 1000, 0.54),
('035420', DATE_SUB(CURDATE(), INTERVAL 1 DAY), 184000, 186000, 183500, 185000, 750000, 500, 0.27)
ON DUPLICATE KEY UPDATE 
    close_price = VALUES(close_price),
    volume = VALUES(volume),
    change_amount = VALUES(change_amount),
    change_rate = VALUES(change_rate);

SELECT 'Finance Shard 1 시장 데이터 및 알림 확장 완료' as status;

-- =====================================
-- Shard 2에도 동일하게 적용 (간략화)
-- =====================================

USE finance_shard_2;

-- 동일한 테이블 구조 생성 (생략)

SELECT 'Finance Shard 2 시장 데이터 및 알림 확장 완료' as status;
SELECT 'Finance Shard DB 시장 데이터 및 알림 확장 완료!' as final_status;