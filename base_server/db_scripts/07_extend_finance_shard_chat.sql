-- =====================================
-- Finance Shard DB AI 채팅 확장
-- 패킷명세서 기반: REQ-CHAT-001~026
-- =====================================

-- Shard 1에 적용
USE finance_shard_1;

-- 1. AI 채팅방 테이블
CREATE TABLE IF NOT EXISTS `table_chat_rooms` (
  `room_id` varchar(32) NOT NULL,
  `account_db_key` bigint unsigned NOT NULL,
  `title` varchar(200) DEFAULT NULL,
  `ai_persona` enum('GPT4O','WARREN_BUFFETT','PETER_LYNCH','GIGA_BUFFETT') DEFAULT 'GPT4O',
  `message_count` int DEFAULT 0,
  `last_message_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`room_id`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_ai_persona` (`ai_persona`),
  INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 2. 채팅 메시지 테이블
CREATE TABLE IF NOT EXISTS `table_chat_messages` (
  `message_id` varchar(32) NOT NULL,
  `room_id` varchar(32) NOT NULL,
  `sender_type` enum('USER','AI') NOT NULL,
  `content` text NOT NULL,
  `metadata` text,  -- JSON 형태로 분석 데이터, 추천 등 저장
  `is_streaming` bit(1) NOT NULL DEFAULT b'0',
  `timestamp` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`message_id`),
  INDEX `idx_room_id` (`room_id`),
  INDEX `idx_sender_type` (`sender_type`),
  INDEX `idx_timestamp` (`timestamp`),
  FOREIGN KEY (`room_id`) REFERENCES `table_chat_rooms`(`room_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 3. AI 분석 결과 테이블
CREATE TABLE IF NOT EXISTS `table_ai_analysis_results` (
  `analysis_id` varchar(32) NOT NULL,
  `account_db_key` bigint unsigned NOT NULL,
  `symbol` varchar(10) NOT NULL,
  `analysis_type` enum('FUNDAMENTAL','TECHNICAL','SENTIMENT') NOT NULL,
  `score` decimal(5,2) DEFAULT 0.00,
  `confidence` decimal(5,2) DEFAULT 0.00,
  `summary` text,
  `details` text,  -- JSON 형태로 상세 분석 데이터 저장
  `related_message_id` varchar(32) DEFAULT NULL,
  `generated_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `expires_at` datetime DEFAULT NULL,
  PRIMARY KEY (`analysis_id`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_symbol` (`symbol`),
  INDEX `idx_analysis_type` (`analysis_type`),
  INDEX `idx_generated_at` (`generated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 4. 투자 추천 테이블
CREATE TABLE IF NOT EXISTS `table_investment_recommendations` (
  `recommendation_id` varchar(32) NOT NULL,
  `account_db_key` bigint unsigned NOT NULL,
  `symbol` varchar(10) NOT NULL,
  `action` enum('BUY','SELL','HOLD') NOT NULL,
  `target_price` decimal(15,2) DEFAULT 0.00,
  `reasoning` text,
  `risk_level` enum('LOW','MEDIUM','HIGH') DEFAULT 'MEDIUM',
  `time_horizon` enum('SHORT','MEDIUM','LONG') DEFAULT 'MEDIUM',
  `confidence_score` decimal(5,2) DEFAULT 0.00,
  `related_analysis_id` varchar(32) DEFAULT NULL,
  `related_message_id` varchar(32) DEFAULT NULL,
  `status` enum('ACTIVE','EXECUTED','EXPIRED','CANCELLED') DEFAULT 'ACTIVE',
  `generated_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `expires_at` datetime DEFAULT NULL,
  PRIMARY KEY (`recommendation_id`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_symbol` (`symbol`),
  INDEX `idx_action` (`action`),
  INDEX `idx_status` (`status`),
  INDEX `idx_generated_at` (`generated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 5. AI 페르소나 정보 테이블
CREATE TABLE IF NOT EXISTS `table_ai_personas` (
  `persona_id` varchar(50) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` text,
  `avatar_url` varchar(500) DEFAULT NULL,
  `specialty` varchar(200) DEFAULT NULL,
  `greeting_message` text,
  `system_prompt` text,  -- AI 모델에게 전달할 시스템 프롬프트
  `is_active` bit(1) NOT NULL DEFAULT b'1',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`persona_id`),
  INDEX `idx_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- =====================================
-- 채팅 관련 프로시저
-- =====================================

-- 채팅방 생성
DROP PROCEDURE IF EXISTS `fp_create_chat_room`;
DELIMITER ;;
CREATE PROCEDURE `fp_create_chat_room`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_ai_persona VARCHAR(50),
    IN p_title VARCHAR(200)
)
BEGIN
    DECLARE v_room_id VARCHAR(32);
    DECLARE v_message_id VARCHAR(32);
    DECLARE v_greeting_message TEXT;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_ai_persona, ',', p_title);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_create_chat_room', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 채팅방 ID 생성
    SET v_room_id = CONCAT(
        'room_',
        LPAD(HEX(p_account_db_key), 16, '0'),
        '_',
        LPAD(HEX(UNIX_TIMESTAMP()), 8, '0')
    );
    
    -- 메시지 ID 생성
    SET v_message_id = CONCAT(
        'msg_',
        LPAD(HEX(p_account_db_key), 16, '0'),
        '_',
        LPAD(HEX(UNIX_TIMESTAMP()), 8, '0'),
        '_01'
    );
    
    -- 페르소나별 인사말 조회
    SELECT COALESCE(greeting_message, '안녕하세요! 투자 관련 질문이 있으시면 언제든 물어보세요.') 
    INTO v_greeting_message
    FROM table_ai_personas 
    WHERE persona_id = p_ai_persona;
    
    -- 채팅방 생성
    INSERT INTO table_chat_rooms (room_id, account_db_key, title, ai_persona, message_count, last_message_at)
    VALUES (v_room_id, p_account_db_key, COALESCE(p_title, '새 대화'), p_ai_persona, 1, NOW());
    
    -- 초기 AI 인사말 메시지 생성
    INSERT INTO table_chat_messages (message_id, room_id, sender_type, content)
    VALUES (v_message_id, v_room_id, 'AI', v_greeting_message);
    
    SELECT 'SUCCESS' as result, v_room_id as room_id, v_message_id as initial_message_id;
    
END ;;
DELIMITER ;

-- 메시지 전송
DROP PROCEDURE IF EXISTS `fp_send_chat_message`;
DELIMITER ;;
CREATE PROCEDURE `fp_send_chat_message`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_room_id VARCHAR(32),
    IN p_content TEXT,
    IN p_include_portfolio BOOLEAN,
    IN p_analysis_symbols TEXT
)
BEGIN
    DECLARE v_message_id VARCHAR(32);
    DECLARE v_ai_response_id VARCHAR(32);
    DECLARE v_room_exists INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_room_id, ',', LEFT(p_content, 100));
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_send_chat_message', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    message_block: BEGIN
        -- 채팅방 존재 및 권한 확인
        SELECT COUNT(*) INTO v_room_exists
        FROM table_chat_rooms 
        WHERE room_id = p_room_id AND account_db_key = p_account_db_key;
        
        IF v_room_exists = 0 THEN
            SELECT 'FAILED' as result, 'Room not found or access denied' as message;
            LEAVE message_block;
        END IF;
        
        -- 사용자 메시지 ID 생성
        SET v_message_id = CONCAT(
            'msg_',
            LPAD(HEX(p_account_db_key), 16, '0'),
            '_',
            LPAD(HEX(UNIX_TIMESTAMP()), 8, '0'),
            '_',
            LPAD(FLOOR(RAND() * 999), 3, '0')
        );
        
        -- AI 응답 메시지 ID 생성
        SET v_ai_response_id = CONCAT(
            'msg_',
            LPAD(HEX(p_account_db_key), 16, '0'),
            '_',
            LPAD(HEX(UNIX_TIMESTAMP()), 8, '0'),
            '_',
            LPAD(FLOOR(RAND() * 999), 3, '0')
        );
        
        -- 사용자 메시지 저장
        INSERT INTO table_chat_messages (message_id, room_id, sender_type, content)
        VALUES (v_message_id, p_room_id, 'USER', p_content);
        
        -- AI 응답 메시지 저장 (실제로는 외부 AI 서비스 호출 필요)
        INSERT INTO table_chat_messages (message_id, room_id, sender_type, content, metadata)
        VALUES (v_ai_response_id, p_room_id, 'AI', 
                '귀하의 질문을 분석했습니다. 더 구체적인 투자 조언을 원하시면 종목명을 알려주세요.',
                JSON_OBJECT('include_portfolio', p_include_portfolio, 'analysis_symbols', p_analysis_symbols));
        
        -- 채팅방 정보 업데이트
        UPDATE table_chat_rooms 
        SET message_count = message_count + 2,
            last_message_at = NOW()
        WHERE room_id = p_room_id;
        
        SELECT 'SUCCESS' as result, v_message_id as user_message_id, v_ai_response_id as ai_message_id;
    END message_block;
    
END ;;
DELIMITER ;

-- 채팅방 목록 조회
DROP PROCEDURE IF EXISTS `fp_get_chat_rooms`;
DELIMITER ;;
CREATE PROCEDURE `fp_get_chat_rooms`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_page INT,
    IN p_limit INT
)
BEGIN
    DECLARE v_offset INT;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_page, ',', p_limit);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_get_chat_rooms', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    SET v_offset = (p_page - 1) * p_limit;
    
    -- 채팅방 목록 조회
    SELECT 
        room_id,
        title,
        ai_persona,
        message_count,
        last_message_at,
        created_at
    FROM table_chat_rooms 
    WHERE account_db_key = p_account_db_key
    ORDER BY last_message_at DESC
    LIMIT p_limit OFFSET v_offset;
    
    -- 전체 개수
    SELECT COUNT(*) as total_count
    FROM table_chat_rooms 
    WHERE account_db_key = p_account_db_key;
    
END ;;
DELIMITER ;

-- 채팅 메시지 목록 조회
DROP PROCEDURE IF EXISTS `fp_get_chat_messages`;
DELIMITER ;;
CREATE PROCEDURE `fp_get_chat_messages`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_room_id VARCHAR(32),
    IN p_page INT,
    IN p_limit INT,
    IN p_before_timestamp DATETIME
)
BEGIN
    DECLARE v_offset INT;
    DECLARE v_room_exists INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_room_id, ',', p_page, ',', p_limit);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_get_chat_messages', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    message_check_block: BEGIN
        -- 채팅방 권한 확인
        SELECT COUNT(*) INTO v_room_exists
        FROM table_chat_rooms 
        WHERE room_id = p_room_id AND account_db_key = p_account_db_key;
        
        IF v_room_exists = 0 THEN
            SELECT 'Room not found or access denied' as error;
            LEAVE message_check_block;
        END IF;
        
        SET v_offset = (p_page - 1) * p_limit;
        
        -- 메시지 목록 조회
        IF p_before_timestamp IS NOT NULL THEN
            SELECT 
                message_id,
                sender_type,
                content,
                metadata,
                is_streaming,
                timestamp
            FROM table_chat_messages 
            WHERE room_id = p_room_id 
              AND timestamp < p_before_timestamp
            ORDER BY timestamp DESC
            LIMIT p_limit;
        ELSE
            SELECT 
                message_id,
                sender_type,
                content,
                metadata,
                is_streaming,
                timestamp
            FROM table_chat_messages 
            WHERE room_id = p_room_id
            ORDER BY timestamp DESC
            LIMIT p_limit OFFSET v_offset;
        END IF;
    END message_check_block;
    
END ;;
DELIMITER ;

-- =====================================
-- AI 분석 관련 프로시저
-- =====================================

-- AI 분석 결과 저장
DROP PROCEDURE IF EXISTS `fp_save_ai_analysis`;
DELIMITER ;;
CREATE PROCEDURE `fp_save_ai_analysis`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_symbol VARCHAR(10),
    IN p_analysis_type VARCHAR(20),
    IN p_score DECIMAL(5,2),
    IN p_confidence DECIMAL(5,2),
    IN p_summary TEXT,
    IN p_details TEXT,
    IN p_related_message_id VARCHAR(32)
)
BEGIN
    DECLARE v_analysis_id VARCHAR(32);
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_symbol, ',', p_analysis_type);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_save_ai_analysis', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 분석 ID 생성
    SET v_analysis_id = CONCAT(
        'analysis_',
        LPAD(HEX(p_account_db_key), 16, '0'),
        '_',
        p_symbol,
        '_',
        LPAD(HEX(UNIX_TIMESTAMP()), 8, '0')
    );
    
    -- 분석 결과 저장
    INSERT INTO table_ai_analysis_results (
        analysis_id, account_db_key, symbol, analysis_type, score, confidence,
        summary, details, related_message_id, expires_at
    ) VALUES (
        v_analysis_id, p_account_db_key, p_symbol, p_analysis_type, p_score, p_confidence,
        p_summary, p_details, p_related_message_id, DATE_ADD(NOW(), INTERVAL 7 DAY)
    );
    
    SELECT 'SUCCESS' as result, v_analysis_id as analysis_id;
    
END ;;
DELIMITER ;

-- 투자 추천 저장
DROP PROCEDURE IF EXISTS `fp_save_investment_recommendation`;
DELIMITER ;;
CREATE PROCEDURE `fp_save_investment_recommendation`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_symbol VARCHAR(10),
    IN p_action VARCHAR(10),
    IN p_target_price DECIMAL(15,2),
    IN p_reasoning TEXT,
    IN p_risk_level VARCHAR(10),
    IN p_time_horizon VARCHAR(10),
    IN p_confidence_score DECIMAL(5,2),
    IN p_related_analysis_id VARCHAR(32),
    IN p_related_message_id VARCHAR(32)
)
BEGIN
    DECLARE v_recommendation_id VARCHAR(32);
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_symbol, ',', p_action);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_save_investment_recommendation', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 추천 ID 생성
    SET v_recommendation_id = CONCAT(
        'rec_',
        LPAD(HEX(p_account_db_key), 16, '0'),
        '_',
        p_symbol,
        '_',
        LPAD(HEX(UNIX_TIMESTAMP()), 8, '0')
    );
    
    -- 투자 추천 저장
    INSERT INTO table_investment_recommendations (
        recommendation_id, account_db_key, symbol, action, target_price,
        reasoning, risk_level, time_horizon, confidence_score,
        related_analysis_id, related_message_id, expires_at
    ) VALUES (
        v_recommendation_id, p_account_db_key, p_symbol, p_action, p_target_price,
        p_reasoning, p_risk_level, p_time_horizon, p_confidence_score,
        p_related_analysis_id, p_related_message_id, DATE_ADD(NOW(), INTERVAL 30 DAY)
    );
    
    SELECT 'SUCCESS' as result, v_recommendation_id as recommendation_id;
    
END ;;
DELIMITER ;

-- =====================================
-- 초기 데이터 삽입
-- =====================================

-- AI 페르소나 기본 데이터
INSERT INTO table_ai_personas (persona_id, name, description, specialty, greeting_message, system_prompt) 
VALUES 
('GPT4O', 'GPT-4O 어드바이저', '최신 AI 기술을 활용한 종합 투자 어드바이저입니다.', '종합 투자 분석', 
 '안녕하세요! 저는 GPT-4O 투자 어드바이저입니다. 투자 관련 질문이 있으시면 언제든 물어보세요.',
 'You are a professional investment advisor. Provide helpful and accurate investment advice based on market data and analysis.'),

('WARREN_BUFFETT', '워렌 버핏 스타일', '가치 투자의 거장 워렌 버핏의 투자 철학을 따르는 AI입니다.', '가치 투자', 
 '안녕하세요! 저는 워렌 버핏의 가치 투자 철학을 따르는 AI 어드바이저입니다. 장기적 관점에서 조언드리겠습니다.',
 'You are an AI advisor following Warren Buffett investment philosophy. Focus on value investing, long-term growth, and fundamental analysis.'),

('PETER_LYNCH', '피터 린치 스타일', '성장주 투자의 대가 피터 린치의 투자 스타일을 구현한 AI입니다.', '성장주 투자', 
 '안녕하세요! 저는 피터 린치의 성장주 투자 철학을 따르는 AI입니다. 숨겨진 성장 기회를 찾아드리겠습니다.',
 'You are an AI advisor following Peter Lynch investment philosophy. Focus on growth investing, discovering undervalued growth stocks.'),

('GIGA_BUFFETT', '기가 버핏', '초고성능 AI 투자 전문가로, 모든 투자 스타일을 망라하는 종합 어드바이저입니다.', '종합 투자 전략', 
 '안녕하세요! 저는 기가 버핏입니다. 모든 투자 전략과 최신 시장 동향을 종합하여 최적의 조언을 드리겠습니다.',
 'You are Giga Buffett, an advanced AI combining all investment strategies. Provide comprehensive investment advice using various methodologies.')
ON DUPLICATE KEY UPDATE 
    name = VALUES(name),
    description = VALUES(description),
    specialty = VALUES(specialty),
    greeting_message = VALUES(greeting_message),
    system_prompt = VALUES(system_prompt),
    updated_at = NOW();

SELECT 'Finance Shard 1 AI 채팅 확장 완료' as status;

-- =====================================
-- Shard 2에도 동일하게 적용
-- =====================================

USE finance_shard_2;

-- 동일한 테이블 구조를 Shard 2에도 생성 (간략화)
CREATE TABLE IF NOT EXISTS `table_chat_rooms` (
  `room_id` varchar(32) NOT NULL,
  `account_db_key` bigint unsigned NOT NULL,
  `title` varchar(200) DEFAULT NULL,
  `ai_persona` enum('GPT4O','WARREN_BUFFETT','PETER_LYNCH','GIGA_BUFFETT') DEFAULT 'GPT4O',
  `message_count` int DEFAULT 0,
  `last_message_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`room_id`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_ai_persona` (`ai_persona`),
  INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `table_chat_messages` (
  `message_id` varchar(32) NOT NULL,
  `room_id` varchar(32) NOT NULL,
  `sender_type` enum('USER','AI') NOT NULL,
  `content` text NOT NULL,
  `metadata` text,
  `is_streaming` bit(1) NOT NULL DEFAULT b'0',
  `timestamp` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`message_id`),
  INDEX `idx_room_id` (`room_id`),
  INDEX `idx_sender_type` (`sender_type`),
  INDEX `idx_timestamp` (`timestamp`),
  FOREIGN KEY (`room_id`) REFERENCES `table_chat_rooms`(`room_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `table_ai_analysis_results` (
  `analysis_id` varchar(32) NOT NULL,
  `account_db_key` bigint unsigned NOT NULL,
  `symbol` varchar(10) NOT NULL,
  `analysis_type` enum('FUNDAMENTAL','TECHNICAL','SENTIMENT') NOT NULL,
  `score` decimal(5,2) DEFAULT 0.00,
  `confidence` decimal(5,2) DEFAULT 0.00,
  `summary` text,
  `details` text,
  `related_message_id` varchar(32) DEFAULT NULL,
  `generated_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `expires_at` datetime DEFAULT NULL,
  PRIMARY KEY (`analysis_id`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_symbol` (`symbol`),
  INDEX `idx_analysis_type` (`analysis_type`),
  INDEX `idx_generated_at` (`generated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `table_investment_recommendations` (
  `recommendation_id` varchar(32) NOT NULL,
  `account_db_key` bigint unsigned NOT NULL,
  `symbol` varchar(10) NOT NULL,
  `action` enum('BUY','SELL','HOLD') NOT NULL,
  `target_price` decimal(15,2) DEFAULT 0.00,
  `reasoning` text,
  `risk_level` enum('LOW','MEDIUM','HIGH') DEFAULT 'MEDIUM',
  `time_horizon` enum('SHORT','MEDIUM','LONG') DEFAULT 'MEDIUM',
  `confidence_score` decimal(5,2) DEFAULT 0.00,
  `related_analysis_id` varchar(32) DEFAULT NULL,
  `related_message_id` varchar(32) DEFAULT NULL,
  `status` enum('ACTIVE','EXECUTED','EXPIRED','CANCELLED') DEFAULT 'ACTIVE',
  `generated_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `expires_at` datetime DEFAULT NULL,
  PRIMARY KEY (`recommendation_id`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_symbol` (`symbol`),
  INDEX `idx_action` (`action`),
  INDEX `idx_status` (`status`),
  INDEX `idx_generated_at` (`generated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `table_ai_personas` (
  `persona_id` varchar(50) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` text,
  `avatar_url` varchar(500) DEFAULT NULL,
  `specialty` varchar(200) DEFAULT NULL,
  `greeting_message` text,
  `system_prompt` text,
  `is_active` bit(1) NOT NULL DEFAULT b'1',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`persona_id`),
  INDEX `idx_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- AI 페르소나 기본 데이터 (Shard 2)
INSERT INTO table_ai_personas (persona_id, name, description, specialty, greeting_message, system_prompt) 
VALUES 
('GPT4O', 'GPT-4O 어드바이저', '최신 AI 기술을 활용한 종합 투자 어드바이저입니다.', '종합 투자 분석', 
 '안녕하세요! 저는 GPT-4O 투자 어드바이저입니다. 투자 관련 질문이 있으시면 언제든 물어보세요.',
 'You are a professional investment advisor. Provide helpful and accurate investment advice based on market data and analysis.'),

('WARREN_BUFFETT', '워렌 버핏 스타일', '가치 투자의 거장 워렌 버핏의 투자 철학을 따르는 AI입니다.', '가치 투자', 
 '안녕하세요! 저는 워렌 버핏의 가치 투자 철학을 따르는 AI 어드바이저입니다. 장기적 관점에서 조언드리겠습니다.',
 'You are an AI advisor following Warren Buffett investment philosophy. Focus on value investing, long-term growth, and fundamental analysis.'),

('PETER_LYNCH', '피터 린치 스타일', '성장주 투자의 대가 피터 린치의 투자 스타일을 구현한 AI입니다.', '성장주 투자', 
 '안녕하세요! 저는 피터 린치의 성장주 투자 철학을 따르는 AI입니다. 숨겨진 성장 기회를 찾아드리겠습니다.',
 'You are an AI advisor following Peter Lynch investment philosophy. Focus on growth investing, discovering undervalued growth stocks.'),

('GIGA_BUFFETT', '기가 버핏', '초고성능 AI 투자 전문가로, 모든 투자 스타일을 망라하는 종합 어드바이저입니다.', '종합 투자 전략', 
 '안녕하세요! 저는 기가 버핏입니다. 모든 투자 전략과 최신 시장 동향을 종합하여 최적의 조언을 드리겠습니다.',
 'You are Giga Buffett, an advanced AI combining all investment strategies. Provide comprehensive investment advice using various methodologies.')
ON DUPLICATE KEY UPDATE 
    name = VALUES(name),
    description = VALUES(description),
    specialty = VALUES(specialty),
    greeting_message = VALUES(greeting_message),
    system_prompt = VALUES(system_prompt),
    updated_at = NOW();

SELECT 'Finance Shard 2 AI 채팅 확장 완료' as status;
SELECT 'Finance Shard DB AI 채팅 확장 완료!' as final_status;