-- =====================================
-- 채팅 시스템 테이블 확장 스크립트
-- 기존 game_server → base_server 패턴 준수
-- Redis + MySQL 하이브리드 아키텍처용
-- 적용 대상: finance_shard_1, finance_shard_2
-- =====================================

-- =====================================
-- Shard DB 1에 채팅 테이블 추가
-- =====================================
USE finance_shard_1;

-- 챗봇 세션 테이블 (Redis 구조와 일치, base_server 패턴 준수)
CREATE TABLE IF NOT EXISTS `table_chat_rooms` (
  `room_id` varchar(128) NOT NULL COMMENT '챗봇 세션 고유 ID (충분한 길이 확보)',
  `account_db_key` bigint unsigned NOT NULL COMMENT '세션 소유자 계정 키',
  `title` varchar(200) NOT NULL COMMENT '챗봇 세션 제목 (대화 주제)',
  `ai_persona` varchar(100) NOT NULL COMMENT '챗봇 페르소나/캐릭터',
  `last_message_id` varchar(128) DEFAULT NULL COMMENT '마지막 메시지 ID',
  `last_message_at` datetime(6) DEFAULT NULL COMMENT '마지막 메시지 시간',
  `message_count` int DEFAULT 0 COMMENT '총 메시지 수',
  `is_active` tinyint(1) DEFAULT 1 COMMENT '활성 상태 (카카오 방식: 최종 상태만 저장)',
  `created_at` datetime(6) DEFAULT CURRENT_TIMESTAMP(6) COMMENT '생성 시간',
  `updated_at` datetime(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '수정 시간',
  PRIMARY KEY (`room_id`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_last_message_at` (`last_message_at`),
  INDEX `idx_is_active_updated` (`is_active`, `updated_at`),
  INDEX `idx_ai_persona` (`ai_persona`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='챗봇 세션 정보 테이블 (Shard 1)';

-- 채팅 메시지 테이블 (기존 패턴: idx AUTO_INCREMENT PRIMARY KEY)
CREATE TABLE IF NOT EXISTS `table_chat_messages` (
  `idx` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '메시지 고유 인덱스 (기존 패턴)',
  `message_id` varchar(128) NOT NULL COMMENT '메시지 ID (비즈니스 키)',
  `room_id` varchar(128) NOT NULL COMMENT '채팅방 ID',
  `account_db_key` bigint unsigned NOT NULL COMMENT '발송자 계정 키',
  `message_type` enum('USER','AI','SYSTEM') NOT NULL DEFAULT 'USER' COMMENT '메시지 타입',
  `content` text NOT NULL COMMENT '메시지 내용',
  `metadata` json DEFAULT NULL COMMENT '메시지 메타데이터 (토큰 수, 모델 정보 등)',
  `parent_message_id` varchar(128) DEFAULT NULL COMMENT '부모 메시지 ID (대화 체인)',
  `is_deleted` tinyint(1) DEFAULT 0 COMMENT '삭제 여부 (카카오 방식: 최종 상태만 저장)',
  `created_at` datetime(6) DEFAULT CURRENT_TIMESTAMP(6) COMMENT '생성 시간',
  `updated_at` datetime(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '수정 시간',
  PRIMARY KEY (`idx`),
  UNIQUE KEY `uk_message_id` (`message_id`),
  INDEX `idx_room_id_created` (`room_id`, `created_at`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_message_type` (`message_type`),
  INDEX `idx_parent_message_id` (`parent_message_id`),
  INDEX `idx_is_deleted` (`is_deleted`),
  FOREIGN KEY (`room_id`) REFERENCES `table_chat_rooms`(`room_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='채팅 메시지 테이블 (Shard 1)';

-- 채팅 통계 테이블 (사용자별 일일 통계)
CREATE TABLE IF NOT EXISTS `table_chat_statistics` (
  `idx` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '통계 고유 인덱스',
  `account_db_key` bigint unsigned NOT NULL COMMENT '사용자 계정 키',
  `date` date NOT NULL COMMENT '통계 일자',
  `total_messages` int DEFAULT 0 COMMENT '총 메시지 수',
  `user_messages` int DEFAULT 0 COMMENT '사용자 메시지 수',
  `ai_messages` int DEFAULT 0 COMMENT 'AI 응답 수',
  `total_tokens` int DEFAULT 0 COMMENT '총 토큰 사용량',
  `active_rooms` int DEFAULT 0 COMMENT '활성 채팅방 수',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`idx`),
  UNIQUE KEY `uk_account_date` (`account_db_key`, `date`),
  INDEX `idx_date` (`date`),
  INDEX `idx_updated_at` (`updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='채팅 사용 통계 테이블 (Shard 1)';

-- =====================================
-- 채팅 관련 프로시저 (Shard 1) - 기존 패턴 준수
-- =====================================

-- 채팅방 생성 프로시저 (기존 에러 처리 패턴 준수)
DROP PROCEDURE IF EXISTS `fp_chat_room_create`;
DELIMITER ;;
CREATE PROCEDURE `fp_chat_room_create`(
    IN p_room_id VARCHAR(128),
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_title VARCHAR(200),
    IN p_ai_persona VARCHAR(100)
)
BEGIN
    DECLARE v_existing_count INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_room_id, ',', p_account_db_key, ',', p_title);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_chat_room_create', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 중복 채팅방 확인
    SELECT COUNT(*) INTO v_existing_count
    FROM table_chat_rooms 
    WHERE room_id = p_room_id;
    
    IF v_existing_count > 0 THEN
        SELECT 'EXISTS' as result, 'Chatbot session already exists' as message, p_room_id as room_id;
    ELSE
        -- 새 챗봇 세션 생성 (카카오 방식: 최종 상태만 DB 저장, State Machine은 Redis에서 관리)
        INSERT INTO table_chat_rooms (room_id, account_db_key, title, ai_persona)
        VALUES (p_room_id, p_account_db_key, p_title, p_ai_persona);
        
        SELECT 'SUCCESS' as result, 'Chatbot session created successfully' as message, p_room_id as room_id;
    END IF;
    
END ;;
DELIMITER ;

-- 채팅 메시지 배치 저장 프로시저 (메시지큐→스케줄러→DB 저장용)
DROP PROCEDURE IF EXISTS `fp_chat_message_batch_save`;
DELIMITER ;;
CREATE PROCEDURE `fp_chat_message_batch_save`(
    IN p_message_id VARCHAR(128),
    IN p_room_id VARCHAR(128),
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_message_type VARCHAR(10),
    IN p_content TEXT,
    IN p_metadata JSON,
    IN p_parent_message_id VARCHAR(128)
)
BEGIN
    DECLARE v_message_id VARCHAR(128) DEFAULT '';
    DECLARE v_idx BIGINT UNSIGNED DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_room_id, ',', p_account_db_key, ',', p_message_type);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_chat_message_batch_save', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- 전달받은 message_id 사용 (이미 생성된 값)
    SET v_message_id = p_message_id;
    
    -- 채팅 메시지 저장 (카카오 방식: 최종 상태만 DB 저장, State Machine은 Redis에서 관리)
    INSERT INTO table_chat_messages (message_id, room_id, account_db_key, message_type, content, metadata, parent_message_id)
    VALUES (v_message_id, p_room_id, p_account_db_key, p_message_type, p_content, p_metadata, p_parent_message_id);
    
    SET v_idx = LAST_INSERT_ID();
    
    -- 채팅방 정보 업데이트 (마지막 메시지 정보, 메시지 카운트)
    UPDATE table_chat_rooms 
    SET last_message_id = v_message_id,
        last_message_at = NOW(),
        message_count = message_count + 1,
        updated_at = NOW()
    WHERE room_id = p_room_id;
    
    -- 일일 통계 업데이트 (UPSERT 패턴)
    INSERT INTO table_chat_statistics (account_db_key, date, total_messages, user_messages, ai_messages)
    VALUES (p_account_db_key, CURDATE(), 1, 
           CASE WHEN p_message_type = 'USER' THEN 1 ELSE 0 END,
           CASE WHEN p_message_type = 'AI' THEN 1 ELSE 0 END)
    ON DUPLICATE KEY UPDATE
        total_messages = total_messages + 1,
        user_messages = user_messages + CASE WHEN p_message_type = 'USER' THEN 1 ELSE 0 END,
        ai_messages = ai_messages + CASE WHEN p_message_type = 'AI' THEN 1 ELSE 0 END,
        updated_at = NOW();
    
    COMMIT;
    
    SELECT 'SUCCESS' as result, v_idx as idx, v_message_id as message_id;
    
END ;;
DELIMITER ;

-- 채팅 메시지 조회 프로시저 (페이징 지원, Redis 캐시 미스 시 사용)
DROP PROCEDURE IF EXISTS `fp_chat_messages_get`;
DELIMITER ;;
CREATE PROCEDURE `fp_chat_messages_get`(
    IN p_room_id VARCHAR(128),
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_limit INT,
    IN p_offset INT
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_room_id, ',', p_account_db_key, ',', p_limit, ',', p_offset);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_chat_messages_get', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 채팅방 접근 권한 확인 후 메시지 조회
    SELECT 
        cm.idx,
        cm.message_id,
        cm.room_id,
        cm.account_db_key,
        cm.message_type,
        cm.content,
        cm.metadata,
        cm.parent_message_id,
        cm.created_at,
        cm.updated_at
    FROM table_chat_messages cm
    INNER JOIN table_chat_rooms cr ON cm.room_id = cr.room_id
    WHERE cm.room_id = p_room_id 
      AND cr.account_db_key = p_account_db_key
      AND cm.is_deleted = 0
    ORDER BY cm.created_at ASC
    LIMIT p_limit OFFSET p_offset;
    
END ;;
DELIMITER ;

-- 채팅방 목록 조회 프로시저
DROP PROCEDURE IF EXISTS `fp_chat_rooms_get`;
DELIMITER ;;
CREATE PROCEDURE `fp_chat_rooms_get`(
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
            VALUES ('fp_chat_rooms_get', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 사용자의 활성 챗봇 세션 목록 조회
    SELECT 
        room_id,
        title,
        ai_persona,
        last_message_id,
        last_message_at,
        message_count,
        created_at,
        updated_at
    FROM table_chat_rooms
    WHERE account_db_key = p_account_db_key
      AND is_active = 1
    ORDER BY last_message_at DESC, created_at DESC;
    
END ;;
DELIMITER ;

-- 채팅방 Soft Delete 프로시저 (신규 추가)
DROP PROCEDURE IF EXISTS `fp_chat_room_soft_delete`;
DELIMITER ;;
CREATE PROCEDURE `fp_chat_room_soft_delete`(
    IN p_room_id VARCHAR(128),
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
            VALUES ('fp_chat_room_soft_delete', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- 채팅방 존재 및 소유권 확인
    SELECT COUNT(*) INTO v_room_exists
    FROM table_chat_rooms 
    WHERE room_id = p_room_id 
      AND account_db_key = p_account_db_key 
      AND is_active = 1;
    
    IF v_room_exists = 0 THEN
        ROLLBACK;
        SELECT 'FAILED' as result, 'Room not found or already deleted' as message;
    ELSE
        -- 채팅방 Soft Delete (카카오 방식: 최종 상태만 DB 저장)
        UPDATE table_chat_rooms 
        SET is_active = 0,
            updated_at = NOW()
        WHERE room_id = p_room_id 
          AND account_db_key = p_account_db_key;
        
        -- 관련 메시지들도 Soft Delete (카카오 방식: 최종 상태만 DB 저장)
        UPDATE table_chat_messages 
        SET is_deleted = 1,
            updated_at = NOW()
        WHERE room_id = p_room_id;
        
        COMMIT;
        SELECT 'SUCCESS' as result, 'Chat room soft deleted successfully' as message;
    END IF;
    
END ;;
DELIMITER ;

-- 채팅방 제목 변경 프로시저 (신규 추가)
DROP PROCEDURE IF EXISTS `fp_chat_room_update_title`;
DELIMITER ;;
CREATE PROCEDURE `fp_chat_room_update_title`(
    IN p_room_id VARCHAR(128),
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_new_title VARCHAR(200)
)
BEGIN
    DECLARE v_room_exists INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_room_id, ',', p_account_db_key, ',', p_new_title);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_chat_room_update_title', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 제목 길이 검증
    IF CHAR_LENGTH(p_new_title) = 0 OR CHAR_LENGTH(p_new_title) > 200 THEN
        SELECT 'FAILED' as result, 'Invalid title length (1-200 characters required)' as message;
    ELSE
        -- 채팅방 존재 및 소유권 확인
        SELECT COUNT(*) INTO v_room_exists
        FROM table_chat_rooms 
        WHERE room_id = p_room_id 
          AND account_db_key = p_account_db_key 
          AND is_active = 1;
        
        IF v_room_exists = 0 THEN
            SELECT 'FAILED' as result, 'Room not found or access denied' as message;
        ELSE
            -- 채팅방 제목 업데이트
            UPDATE table_chat_rooms 
            SET title = p_new_title,
                updated_at = NOW()
            WHERE room_id = p_room_id 
              AND account_db_key = p_account_db_key;
            
            SELECT 'SUCCESS' as result, 'Room title updated successfully' as message, p_new_title as new_title;
        END IF;
    END IF;
    
END ;;
DELIMITER ;

-- 개별 메시지 Soft Delete 프로시저 (신규 추가)
DROP PROCEDURE IF EXISTS `fp_chat_message_soft_delete`;
DELIMITER ;;
CREATE PROCEDURE `fp_chat_message_soft_delete`(
    IN p_message_id VARCHAR(128),
    IN p_room_id VARCHAR(128),
    IN p_account_db_key BIGINT UNSIGNED
)
BEGIN
    DECLARE v_message_exists INT DEFAULT 0;
    DECLARE v_room_owner INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_message_id, ',', p_room_id, ',', p_account_db_key);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_chat_message_soft_delete', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- 채팅방 소유권 확인
    SELECT COUNT(*) INTO v_room_owner
    FROM table_chat_rooms 
    WHERE room_id = p_room_id 
      AND account_db_key = p_account_db_key 
      AND is_active = 1;
    
    IF v_room_owner = 0 THEN
        ROLLBACK;
        SELECT 'FAILED' as result, 'Room not found or access denied' as message;
    ELSE
        -- 메시지 존재 확인
        SELECT COUNT(*) INTO v_message_exists
        FROM table_chat_messages 
        WHERE message_id = p_message_id 
          AND room_id = p_room_id 
          AND is_deleted = 0;
        
        IF v_message_exists = 0 THEN
            ROLLBACK;
            SELECT 'FAILED' as result, 'Message not found or already deleted' as message;
        ELSE
            -- 메시지 Soft Delete (is_deleted = 1)
            UPDATE table_chat_messages 
            SET is_deleted = 1,
                updated_at = NOW()
            WHERE message_id = p_message_id 
              AND room_id = p_room_id;
            
            COMMIT;
            SELECT 'SUCCESS' as result, 'Message soft deleted successfully' as message;
        END IF;
    END IF;
    
END ;;
DELIMITER ;

-- =====================================
-- Shard DB 2에 동일한 구조 생성
-- =====================================
USE finance_shard_2;

-- 동일한 테이블 구조 복사 (Shard 2)
CREATE TABLE IF NOT EXISTS `table_chat_rooms` (
  `room_id` varchar(128) NOT NULL COMMENT '챗봇 세션 고유 ID (충분한 길이 확보)',
  `account_db_key` bigint unsigned NOT NULL COMMENT '세션 소유자 계정 키',
  `title` varchar(200) NOT NULL COMMENT '챗봇 세션 제목 (대화 주제)',
  `ai_persona` varchar(100) NOT NULL COMMENT '챗봇 페르소나/캐릭터',
  `last_message_id` varchar(128) DEFAULT NULL COMMENT '마지막 메시지 ID',
  `last_message_at` datetime(6) DEFAULT NULL COMMENT '마지막 메시지 시간',
  `message_count` int DEFAULT 0 COMMENT '총 메시지 수',
  `is_active` tinyint(1) DEFAULT 1 COMMENT '활성 상태 (카카오 방식: 최종 상태만 저장)',
  `created_at` datetime(6) DEFAULT CURRENT_TIMESTAMP(6) COMMENT '생성 시간',
  `updated_at` datetime(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '수정 시간',
  PRIMARY KEY (`room_id`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_last_message_at` (`last_message_at`),
  INDEX `idx_is_active_updated` (`is_active`, `updated_at`),
  INDEX `idx_ai_persona` (`ai_persona`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='챗봇 세션 정보 테이블 (Shard 2)';

CREATE TABLE IF NOT EXISTS `table_chat_messages` (
  `idx` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '메시지 고유 인덱스 (기존 패턴)',
  `message_id` varchar(128) NOT NULL COMMENT '메시지 ID (비즈니스 키)',
  `room_id` varchar(128) NOT NULL COMMENT '채팅방 ID',
  `account_db_key` bigint unsigned NOT NULL COMMENT '발송자 계정 키',
  `message_type` enum('USER','AI','SYSTEM') NOT NULL DEFAULT 'USER' COMMENT '메시지 타입',
  `content` text NOT NULL COMMENT '메시지 내용',
  `metadata` json DEFAULT NULL COMMENT '메시지 메타데이터 (토큰 수, 모델 정보 등)',
  `parent_message_id` varchar(128) DEFAULT NULL COMMENT '부모 메시지 ID (대화 체인)',
  `is_deleted` tinyint(1) DEFAULT 0 COMMENT '삭제 여부 (카카오 방식: 최종 상태만 저장)',
  `created_at` datetime(6) DEFAULT CURRENT_TIMESTAMP(6) COMMENT '생성 시간',
  `updated_at` datetime(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '수정 시간',
  PRIMARY KEY (`idx`),
  UNIQUE KEY `uk_message_id` (`message_id`),
  INDEX `idx_room_id_created` (`room_id`, `created_at`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_message_type` (`message_type`),
  INDEX `idx_parent_message_id` (`parent_message_id`),
  INDEX `idx_is_deleted` (`is_deleted`),
  FOREIGN KEY (`room_id`) REFERENCES `table_chat_rooms`(`room_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='채팅 메시지 테이블 (Shard 2)';

CREATE TABLE IF NOT EXISTS `table_chat_statistics` (
  `idx` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '통계 고유 인덱스',
  `account_db_key` bigint unsigned NOT NULL COMMENT '사용자 계정 키',
  `date` date NOT NULL COMMENT '통계 일자',
  `total_messages` int DEFAULT 0 COMMENT '총 메시지 수',
  `user_messages` int DEFAULT 0 COMMENT '사용자 메시지 수',
  `ai_messages` int DEFAULT 0 COMMENT 'AI 응답 수',
  `total_tokens` int DEFAULT 0 COMMENT '총 토큰 사용량',
  `active_rooms` int DEFAULT 0 COMMENT '활성 채팅방 수',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`idx`),
  UNIQUE KEY `uk_account_date` (`account_db_key`, `date`),
  INDEX `idx_date` (`date`),
  INDEX `idx_updated_at` (`updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='채팅 사용 통계 테이블 (Shard 2)';

-- =====================================
-- Shard 2 프로시저 복사
-- =====================================

DROP PROCEDURE IF EXISTS `fp_chat_room_create`;
DELIMITER ;;
CREATE PROCEDURE `fp_chat_room_create`(
    IN p_room_id VARCHAR(128),
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_title VARCHAR(200),
    IN p_ai_persona VARCHAR(100)
)
BEGIN
    DECLARE v_existing_count INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_room_id, ',', p_account_db_key, ',', p_title);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_chat_room_create', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    SELECT COUNT(*) INTO v_existing_count
    FROM table_chat_rooms 
    WHERE room_id = p_room_id;
    
    IF v_existing_count > 0 THEN
        SELECT 'EXISTS' as result, 'Chatbot session already exists' as message, p_room_id as room_id;
    ELSE
        INSERT INTO table_chat_rooms (room_id, account_db_key, title, ai_persona)
        VALUES (p_room_id, p_account_db_key, p_title, p_ai_persona);
        
        SELECT 'SUCCESS' as result, 'Chatbot session created successfully' as message, p_room_id as room_id;
    END IF;
    
END ;;
DELIMITER ;

DROP PROCEDURE IF EXISTS `fp_chat_message_batch_save`;
DELIMITER ;;
CREATE PROCEDURE `fp_chat_message_batch_save`(
    IN p_message_id VARCHAR(128),
    IN p_room_id VARCHAR(128),
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_message_type VARCHAR(10),
    IN p_content TEXT,
    IN p_metadata JSON,
    IN p_parent_message_id VARCHAR(128)
)
BEGIN
    DECLARE v_message_id VARCHAR(128) DEFAULT '';
    DECLARE v_idx BIGINT UNSIGNED DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_room_id, ',', p_account_db_key, ',', p_message_type);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_chat_message_batch_save', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    SET v_message_id = CONCAT(UNIX_TIMESTAMP(NOW(3)) * 1000, LPAD(p_account_db_key % 1000, 3, '0'));
    
    INSERT INTO table_chat_messages (message_id, room_id, account_db_key, message_type, content, metadata, parent_message_id)
    VALUES (v_message_id, p_room_id, p_account_db_key, p_message_type, p_content, p_metadata, p_parent_message_id);
    
    SET v_idx = LAST_INSERT_ID();
    
    UPDATE table_chat_rooms 
    SET last_message_id = v_message_id,
        last_message_at = NOW(),
        message_count = message_count + 1,
        updated_at = NOW()
    WHERE room_id = p_room_id;
    
    INSERT INTO table_chat_statistics (account_db_key, date, total_messages, user_messages, ai_messages)
    VALUES (p_account_db_key, CURDATE(), 1, 
           CASE WHEN p_message_type = 'USER' THEN 1 ELSE 0 END,
           CASE WHEN p_message_type = 'AI' THEN 1 ELSE 0 END)
    ON DUPLICATE KEY UPDATE
        total_messages = total_messages + 1,
        user_messages = user_messages + CASE WHEN p_message_type = 'USER' THEN 1 ELSE 0 END,
        ai_messages = ai_messages + CASE WHEN p_message_type = 'AI' THEN 1 ELSE 0 END,
        updated_at = NOW();
    
    COMMIT;
    
    SELECT 'SUCCESS' as result, v_idx as idx, v_message_id as message_id;
    
END ;;
DELIMITER ;

DROP PROCEDURE IF EXISTS `fp_chat_messages_get`;
DELIMITER ;;
CREATE PROCEDURE `fp_chat_messages_get`(
    IN p_room_id VARCHAR(128),
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_limit INT,
    IN p_offset INT
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_room_id, ',', p_account_db_key, ',', p_limit, ',', p_offset);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_chat_messages_get', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    SELECT 
        cm.idx,
        cm.message_id,
        cm.room_id,
        cm.account_db_key,
        cm.message_type,
        cm.content,
        cm.metadata,
        cm.parent_message_id,
        cm.created_at,
        cm.updated_at
    FROM table_chat_messages cm
    INNER JOIN table_chat_rooms cr ON cm.room_id = cr.room_id
    WHERE cm.room_id = p_room_id 
      AND cr.account_db_key = p_account_db_key
      AND cm.is_deleted = 0
    ORDER BY cm.created_at ASC
    LIMIT p_limit OFFSET p_offset;
    
END ;;
DELIMITER ;

DROP PROCEDURE IF EXISTS `fp_chat_rooms_get`;
DELIMITER ;;
CREATE PROCEDURE `fp_chat_rooms_get`(
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
            VALUES ('fp_chat_rooms_get', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    SELECT 
        room_id,
        title,
        ai_persona,
        last_message_id,
        last_message_at,
        message_count,
        created_at,
        updated_at
    FROM table_chat_rooms
    WHERE account_db_key = p_account_db_key
      AND is_active = 1
    ORDER BY last_message_at DESC, created_at DESC;
    
END ;;
DELIMITER ;

-- 채팅방 Soft Delete 프로시저 (Shard 2)
DROP PROCEDURE IF EXISTS `fp_chat_room_soft_delete`;
DELIMITER ;;
CREATE PROCEDURE `fp_chat_room_soft_delete`(
    IN p_room_id VARCHAR(128),
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
            VALUES ('fp_chat_room_soft_delete', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    SELECT COUNT(*) INTO v_room_exists
    FROM table_chat_rooms 
    WHERE room_id = p_room_id 
      AND account_db_key = p_account_db_key 
      AND is_active = 1;
    
    IF v_room_exists = 0 THEN
        ROLLBACK;
        SELECT 'FAILED' as result, 'Room not found or already deleted' as message;
    ELSE
        UPDATE table_chat_rooms 
        SET is_active = 0,
            updated_at = NOW()
        WHERE room_id = p_room_id 
          AND account_db_key = p_account_db_key;
        
        UPDATE table_chat_messages 
        SET is_deleted = 1,
            updated_at = NOW()
        WHERE room_id = p_room_id;
        
        COMMIT;
        SELECT 'SUCCESS' as result, 'Chat room soft deleted successfully' as message;
    END IF;
END ;;
DELIMITER ;

-- 채팅방 제목 변경 프로시저 (Shard 2)
DROP PROCEDURE IF EXISTS `fp_chat_room_update_title`;
DELIMITER ;;
CREATE PROCEDURE `fp_chat_room_update_title`(
    IN p_room_id VARCHAR(128),
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_new_title VARCHAR(200)
)
BEGIN
    DECLARE v_room_exists INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_room_id, ',', p_account_db_key, ',', p_new_title);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_chat_room_update_title', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    IF CHAR_LENGTH(p_new_title) = 0 OR CHAR_LENGTH(p_new_title) > 200 THEN
        SELECT 'FAILED' as result, 'Invalid title length (1-200 characters required)' as message;
    ELSE
        SELECT COUNT(*) INTO v_room_exists
        FROM table_chat_rooms 
        WHERE room_id = p_room_id 
          AND account_db_key = p_account_db_key 
          AND is_active = 1;
        
        IF v_room_exists = 0 THEN
            SELECT 'FAILED' as result, 'Room not found or access denied' as message;
        ELSE
            UPDATE table_chat_rooms 
            SET title = p_new_title,
                updated_at = NOW()
            WHERE room_id = p_room_id 
              AND account_db_key = p_account_db_key;
            
            SELECT 'SUCCESS' as result, 'Room title updated successfully' as message, p_new_title as new_title;
        END IF;
    END IF;
END ;;
DELIMITER ;

-- 개별 메시지 Soft Delete 프로시저 (Shard 2)
DROP PROCEDURE IF EXISTS `fp_chat_message_soft_delete`;
DELIMITER ;;
CREATE PROCEDURE `fp_chat_message_soft_delete`(
    IN p_message_id VARCHAR(128),
    IN p_room_id VARCHAR(128),
    IN p_account_db_key BIGINT UNSIGNED
)
BEGIN
    DECLARE v_message_exists INT DEFAULT 0;
    DECLARE v_room_owner INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_message_id, ',', p_room_id, ',', p_account_db_key);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_chat_message_soft_delete', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    SELECT COUNT(*) INTO v_room_owner
    FROM table_chat_rooms 
    WHERE room_id = p_room_id 
      AND account_db_key = p_account_db_key 
      AND is_active = 1;
    
    IF v_room_owner = 0 THEN
        ROLLBACK;
        SELECT 'FAILED' as result, 'Room not found or access denied' as message;
    ELSE
        SELECT COUNT(*) INTO v_message_exists
        FROM table_chat_messages 
        WHERE message_id = p_message_id 
          AND room_id = p_room_id 
          AND is_deleted = 0;
        
        IF v_message_exists = 0 THEN
            ROLLBACK;
            SELECT 'FAILED' as result, 'Message not found or already deleted' as message;
        ELSE
            UPDATE table_chat_messages 
            SET is_deleted = 1,
                updated_at = NOW()
            WHERE message_id = p_message_id 
              AND room_id = p_room_id;
            
            COMMIT;
            SELECT 'SUCCESS' as result, 'Message soft deleted successfully' as message;
        END IF;
    END IF;
END ;;
DELIMITER ;

-- 최종 상태 확인
SELECT 'Chat tables extension completed for both shards with proper base_server patterns' as status;