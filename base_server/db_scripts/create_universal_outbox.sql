-- =====================================
-- Universal Outbox Pattern (Simplified)
-- service/lock + SchedulerService 기반 정리
-- =====================================

-- ========== Finance Shard 1 ==========
USE finance_shard_1;

-- Universal Outbox 테이블 (기존 outbox_events 대체)
CREATE TABLE IF NOT EXISTS `universal_outbox` (
  `id` varchar(36) NOT NULL COMMENT '이벤트 고유 ID (UUID)',
  `domain` varchar(50) NOT NULL COMMENT '도메인 (chat, portfolio, market)',
  `partition_key` varchar(128) NOT NULL COMMENT '파티션 키 (room_id, user_id, symbol)',
  `sequence_no` bigint NOT NULL COMMENT '파티션 내 시퀀스 번호',
  `event_type` varchar(100) NOT NULL COMMENT '이벤트 타입',
  `aggregate_id` varchar(128) NOT NULL COMMENT '집계 ID (room_id, message_id)',
  `event_data` json NOT NULL COMMENT '이벤트 데이터',
  `status` enum('pending','published','failed','dead_letter') NOT NULL DEFAULT 'pending' COMMENT '이벤트 상태',
  `retry_count` int NOT NULL DEFAULT 0 COMMENT '재시도 횟수',
  `max_retries` int NOT NULL DEFAULT 3 COMMENT '최대 재시도 횟수',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성 시간',
  `updated_at` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '수정 시간',
  `published_at` datetime DEFAULT NULL COMMENT '발행 시간',
  `error_message` text DEFAULT NULL COMMENT '에러 메시지',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_domain_partition_sequence` (`domain`, `partition_key`, `sequence_no`),
  INDEX `idx_status_created` (`status`, `created_at`),
  INDEX `idx_domain_partition` (`domain`, `partition_key`),
  INDEX `idx_published_cleanup` (`status`, `published_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci 
COMMENT='Universal Outbox - service/lock + SchedulerService 기반';

-- 파티션별 시퀀스 관리 테이블
CREATE TABLE IF NOT EXISTS `outbox_sequences` (
  `domain` varchar(50) NOT NULL COMMENT '도메인',
  `partition_key` varchar(128) NOT NULL COMMENT '파티션 키',
  `next_sequence` bigint NOT NULL DEFAULT 1 COMMENT '다음 시퀀스 번호',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`domain`, `partition_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci 
COMMENT='파티션별 시퀀스 번호 관리';

-- =====================================
-- Universal Outbox 프로시저
-- =====================================

-- 시퀀스 번호 생성 함수
DROP FUNCTION IF EXISTS `fn_get_next_sequence`;
DELIMITER ;;
CREATE FUNCTION `fn_get_next_sequence`(
    p_domain VARCHAR(50),
    p_partition_key VARCHAR(128)
) RETURNS BIGINT
READS SQL DATA
DETERMINISTIC
COMMENT '파티션별 다음 시퀀스 번호 생성 (원자적)'
BEGIN
    DECLARE v_next_sequence BIGINT DEFAULT 1;
    
    -- INSERT ... ON DUPLICATE KEY UPDATE로 원자적 시퀀스 생성
    INSERT INTO `outbox_sequences` (`domain`, `partition_key`, `next_sequence`)
    VALUES (p_domain, p_partition_key, 2)
    ON DUPLICATE KEY UPDATE 
        `next_sequence` = `next_sequence` + 1,
        `updated_at` = CURRENT_TIMESTAMP;
    
    -- 업데이트된 시퀀스 조회
    SELECT `next_sequence` - 1 INTO v_next_sequence
    FROM `outbox_sequences`
    WHERE `domain` = p_domain AND `partition_key` = p_partition_key;
    
    RETURN v_next_sequence;
END ;;
DELIMITER ;

-- Universal Outbox 이벤트 발행
DROP PROCEDURE IF EXISTS `fp_universal_outbox_publish`;
DELIMITER ;;
CREATE PROCEDURE `fp_universal_outbox_publish`(
    IN p_domain VARCHAR(50),
    IN p_partition_key VARCHAR(128),
    IN p_event_type VARCHAR(100),
    IN p_aggregate_id VARCHAR(128),
    IN p_event_data JSON
)
COMMENT 'Universal Outbox 이벤트 발행 (service/lock 기반)'
BEGIN
    DECLARE v_event_id VARCHAR(36);
    DECLARE v_sequence_no BIGINT;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_domain, ',', p_partition_key, ',', p_event_type, ',', p_aggregate_id);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_universal_outbox_publish', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- 이벤트 ID 생성
    SET v_event_id = UUID();
    
    -- 시퀀스 번호 생성 (파티션별 순서 보장)
    SET v_sequence_no = fn_get_next_sequence(p_domain, p_partition_key);
    
    -- Universal Outbox에 이벤트 삽입
    INSERT INTO `universal_outbox` (
        `id`, `domain`, `partition_key`, `sequence_no`,
        `event_type`, `aggregate_id`, `event_data`,
        `status`, `retry_count`, `max_retries`, `created_at`
    ) VALUES (
        v_event_id, p_domain, p_partition_key, v_sequence_no,
        p_event_type, p_aggregate_id, p_event_data,
        'pending', 0, 3, CURRENT_TIMESTAMP
    );
    
    COMMIT;
    
    -- SELECT로 결과 반환 (OUT 파라미터 대신)
    SELECT 'SUCCESS' as result, v_event_id as event_id, v_sequence_no as sequence_no;
END ;;
DELIMITER ;

-- 처리 가능한 이벤트 조회 (service/lock 연동)
DROP PROCEDURE IF EXISTS `fp_universal_outbox_get_pending`;
DELIMITER ;;
CREATE PROCEDURE `fp_universal_outbox_get_pending`(
    IN p_domain VARCHAR(50),
    IN p_batch_size INT
)
COMMENT 'service/lock으로 보호될 pending 이벤트 조회'
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_domain, ',', p_batch_size);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_universal_outbox_get_pending', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- pending 상태 이벤트들을 파티션별 순서대로 조회
    SELECT 
        `id`, `domain`, `partition_key`, `sequence_no`,
        `event_type`, `aggregate_id`, `event_data`,
        `retry_count`, `max_retries`, `created_at`
    FROM `universal_outbox`
    WHERE `domain` = p_domain
      AND `status` = 'pending'
      AND `retry_count` < `max_retries`
    ORDER BY `partition_key`, `sequence_no`
    LIMIT COALESCE(p_batch_size, 10);
END ;;
DELIMITER ;

-- 이벤트 상태 업데이트
DROP PROCEDURE IF EXISTS `fp_universal_outbox_update_status`;
DELIMITER ;;
CREATE PROCEDURE `fp_universal_outbox_update_status`(
    IN p_event_id VARCHAR(36),
    IN p_status ENUM('pending','published','failed','dead_letter'),
    IN p_error_message TEXT
)
COMMENT 'Universal Outbox 이벤트 상태 업데이트'
BEGIN
    DECLARE v_affected_rows INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_event_id, ',', p_status);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_universal_outbox_update_status', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    UPDATE `universal_outbox` 
    SET 
        `status` = p_status,
        `updated_at` = CURRENT_TIMESTAMP,
        `published_at` = CASE WHEN p_status = 'published' THEN CURRENT_TIMESTAMP ELSE `published_at` END,
        `error_message` = p_error_message,
        `retry_count` = CASE WHEN p_status = 'failed' THEN `retry_count` + 1 ELSE `retry_count` END
    WHERE `id` = p_event_id;
    
    SET v_affected_rows = ROW_COUNT();
    
    COMMIT;
    
    -- SELECT로 결과 반환
    IF v_affected_rows = 0 THEN
        SELECT 'NOT_FOUND' as result, 'Event not found' as message;
    ELSE
        SELECT 'SUCCESS' as result, 'Event status updated' as message;
    END IF;
END ;;
DELIMITER ;

-- =====================================
-- SchedulerService용 정리 프로시저
-- =====================================

-- Published 이벤트 정리 (7일 후)
DROP PROCEDURE IF EXISTS `fp_universal_outbox_cleanup_published`;
DELIMITER ;;
CREATE PROCEDURE `fp_universal_outbox_cleanup_published`(
    IN p_retention_days INT
)
COMMENT 'SchedulerService용 published 이벤트 정리'
BEGIN
    DECLARE v_deleted_count INT DEFAULT 0;
    DECLARE v_retention_days INT DEFAULT 7;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT('retention_days:', COALESCE(p_retention_days, v_retention_days));
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_universal_outbox_cleanup_published', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 파라미터 검증
    SET v_retention_days = COALESCE(p_retention_days, 7);
    IF v_retention_days < 1 THEN
        SET v_retention_days = 7;
    END IF;
    
    START TRANSACTION;
    
    -- Published 상태이고 보관 기간이 지난 이벤트 삭제
    DELETE FROM `universal_outbox`
    WHERE `status` = 'published'
      AND `published_at` < DATE_SUB(NOW(), INTERVAL v_retention_days DAY);
    
    SET v_deleted_count = ROW_COUNT();
    
    COMMIT;
    
    -- 삭제 결과 반환
    SELECT 'SUCCESS' as result, v_deleted_count as deleted_count, 
           CONCAT(v_retention_days, ' days') as retention_period;
END ;;
DELIMITER ;

-- Failed/Dead Letter 이벤트 정리 (30일 후)
DROP PROCEDURE IF EXISTS `fp_universal_outbox_cleanup_failed`;
DELIMITER ;;
CREATE PROCEDURE `fp_universal_outbox_cleanup_failed`(
    IN p_retention_days INT
)
COMMENT 'SchedulerService용 failed/dead_letter 이벤트 정리'
BEGIN
    DECLARE v_deleted_count INT DEFAULT 0;
    DECLARE v_retention_days INT DEFAULT 30;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT('retention_days:', COALESCE(p_retention_days, v_retention_days));
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_universal_outbox_cleanup_failed', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 파라미터 검증
    SET v_retention_days = COALESCE(p_retention_days, 30);
    IF v_retention_days < 1 THEN
        SET v_retention_days = 30;
    END IF;
    
    START TRANSACTION;
    
    -- Failed/Dead Letter 상태이고 보관 기간이 지난 이벤트 삭제
    DELETE FROM `universal_outbox`
    WHERE `status` IN ('failed', 'dead_letter')
      AND `created_at` < DATE_SUB(NOW(), INTERVAL v_retention_days DAY);
    
    SET v_deleted_count = ROW_COUNT();
    
    COMMIT;
    
    -- 삭제 결과 반환
    SELECT 'SUCCESS' as result, v_deleted_count as deleted_count,
           CONCAT(v_retention_days, ' days') as retention_period;
END ;;
DELIMITER ;

-- 시퀀스 테이블 정리 (90일간 사용되지 않은 파티션)
DROP PROCEDURE IF EXISTS `fp_universal_outbox_cleanup_sequences`;
DELIMITER ;;
CREATE PROCEDURE `fp_universal_outbox_cleanup_sequences`(
    IN p_retention_days INT
)
COMMENT 'SchedulerService용 사용되지 않는 시퀀스 정리'
BEGIN
    DECLARE v_deleted_count INT DEFAULT 0;
    DECLARE v_retention_days INT DEFAULT 90;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT('retention_days:', COALESCE(p_retention_days, v_retention_days));
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_universal_outbox_cleanup_sequences', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 파라미터 검증
    SET v_retention_days = COALESCE(p_retention_days, 90);
    IF v_retention_days < 30 THEN
        SET v_retention_days = 90;
    END IF;
    
    START TRANSACTION;
    
    -- 오래된 시퀀스 레코드 삭제 (해당 파티션에 이벤트가 없는 경우만)
    DELETE s FROM `outbox_sequences` s
    LEFT JOIN `universal_outbox` o ON s.domain = o.domain AND s.partition_key = o.partition_key
    WHERE o.id IS NULL
      AND s.updated_at < DATE_SUB(NOW(), INTERVAL v_retention_days DAY);
    
    SET v_deleted_count = ROW_COUNT();
    
    COMMIT;
    
    -- 삭제 결과 반환
    SELECT 'SUCCESS' as result, v_deleted_count as deleted_count,
           CONCAT(v_retention_days, ' days') as retention_period;
END ;;
DELIMITER ;

SELECT 'Finance Shard 1 Universal Outbox 생성 완료' as status;

-- ========== Finance Shard 2 ==========
USE finance_shard_2;

-- 동일한 구조로 Shard 2에도 생성
CREATE TABLE IF NOT EXISTS `universal_outbox` (
  `id` varchar(36) NOT NULL COMMENT '이벤트 고유 ID (UUID)',
  `domain` varchar(50) NOT NULL COMMENT '도메인 (chat, portfolio, market)',
  `partition_key` varchar(128) NOT NULL COMMENT '파티션 키 (room_id, user_id, symbol)',
  `sequence_no` bigint NOT NULL COMMENT '파티션 내 시퀀스 번호',
  `event_type` varchar(100) NOT NULL COMMENT '이벤트 타입',
  `aggregate_id` varchar(128) NOT NULL COMMENT '집계 ID (room_id, message_id)',
  `event_data` json NOT NULL COMMENT '이벤트 데이터',
  `status` enum('pending','published','failed','dead_letter') NOT NULL DEFAULT 'pending' COMMENT '이벤트 상태',
  `retry_count` int NOT NULL DEFAULT 0 COMMENT '재시도 횟수',
  `max_retries` int NOT NULL DEFAULT 3 COMMENT '최대 재시도 횟수',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성 시간',
  `updated_at` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '수정 시간',
  `published_at` datetime DEFAULT NULL COMMENT '발행 시간',
  `error_message` text DEFAULT NULL COMMENT '에러 메시지',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_domain_partition_sequence` (`domain`, `partition_key`, `sequence_no`),
  INDEX `idx_status_created` (`status`, `created_at`),
  INDEX `idx_domain_partition` (`domain`, `partition_key`),
  INDEX `idx_published_cleanup` (`status`, `published_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci 
COMMENT='Universal Outbox - service/lock + SchedulerService 기반';

CREATE TABLE IF NOT EXISTS `outbox_sequences` (
  `domain` varchar(50) NOT NULL COMMENT '도메인',
  `partition_key` varchar(128) NOT NULL COMMENT '파티션 키',
  `next_sequence` bigint NOT NULL DEFAULT 1 COMMENT '다음 시퀀스 번호',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`domain`, `partition_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci 
COMMENT='파티션별 시퀀스 번호 관리';

-- 동일한 함수/프로시저를 Shard 2에도 생성
DROP FUNCTION IF EXISTS `fn_get_next_sequence`;
DELIMITER ;;
CREATE FUNCTION `fn_get_next_sequence`(
    p_domain VARCHAR(50),
    p_partition_key VARCHAR(128)
) RETURNS BIGINT
READS SQL DATA
DETERMINISTIC
COMMENT '파티션별 다음 시퀀스 번호 생성 (원자적)'
BEGIN
    DECLARE v_next_sequence BIGINT DEFAULT 1;
    
    INSERT INTO `outbox_sequences` (`domain`, `partition_key`, `next_sequence`)
    VALUES (p_domain, p_partition_key, 2)
    ON DUPLICATE KEY UPDATE 
        `next_sequence` = `next_sequence` + 1,
        `updated_at` = CURRENT_TIMESTAMP;
    
    SELECT `next_sequence` - 1 INTO v_next_sequence
    FROM `outbox_sequences`
    WHERE `domain` = p_domain AND `partition_key` = p_partition_key;
    
    RETURN v_next_sequence;
END ;;
DELIMITER ;

DROP PROCEDURE IF EXISTS `fp_universal_outbox_publish`;
DELIMITER ;;
CREATE PROCEDURE `fp_universal_outbox_publish`(
    IN p_domain VARCHAR(50),
    IN p_partition_key VARCHAR(128),
    IN p_event_type VARCHAR(100),
    IN p_aggregate_id VARCHAR(128),
    IN p_event_data JSON
)
COMMENT 'Universal Outbox 이벤트 발행 (service/lock 기반)'
BEGIN
    DECLARE v_event_id VARCHAR(36);
    DECLARE v_sequence_no BIGINT;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_domain, ',', p_partition_key, ',', p_event_type, ',', p_aggregate_id);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_universal_outbox_publish', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    SET v_event_id = UUID();
    SET v_sequence_no = fn_get_next_sequence(p_domain, p_partition_key);
    
    INSERT INTO `universal_outbox` (
        `id`, `domain`, `partition_key`, `sequence_no`,
        `event_type`, `aggregate_id`, `event_data`,
        `status`, `retry_count`, `max_retries`, `created_at`
    ) VALUES (
        v_event_id, p_domain, p_partition_key, v_sequence_no,
        p_event_type, p_aggregate_id, p_event_data,
        'pending', 0, 3, CURRENT_TIMESTAMP
    );
    
    COMMIT;
    
    SELECT 'SUCCESS' as result, v_event_id as event_id, v_sequence_no as sequence_no;
END ;;
DELIMITER ;

DROP PROCEDURE IF EXISTS `fp_universal_outbox_get_pending`;
DELIMITER ;;
CREATE PROCEDURE `fp_universal_outbox_get_pending`(
    IN p_domain VARCHAR(50),
    IN p_batch_size INT
)
COMMENT 'service/lock으로 보호될 pending 이벤트 조회'
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_domain, ',', p_batch_size);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_universal_outbox_get_pending', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    SELECT 
        `id`, `domain`, `partition_key`, `sequence_no`,
        `event_type`, `aggregate_id`, `event_data`,
        `retry_count`, `max_retries`, `created_at`
    FROM `universal_outbox`
    WHERE `domain` = p_domain
      AND `status` = 'pending'
      AND `retry_count` < `max_retries`
    ORDER BY `partition_key`, `sequence_no`
    LIMIT COALESCE(p_batch_size, 10);
END ;;
DELIMITER ;

DROP PROCEDURE IF EXISTS `fp_universal_outbox_update_status`;
DELIMITER ;;
CREATE PROCEDURE `fp_universal_outbox_update_status`(
    IN p_event_id VARCHAR(36),
    IN p_status ENUM('pending','published','failed','dead_letter'),
    IN p_error_message TEXT
)
COMMENT 'Universal Outbox 이벤트 상태 업데이트'
BEGIN
    DECLARE v_affected_rows INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_event_id, ',', p_status);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_universal_outbox_update_status', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    UPDATE `universal_outbox` 
    SET 
        `status` = p_status,
        `updated_at` = CURRENT_TIMESTAMP,
        `published_at` = CASE WHEN p_status = 'published' THEN CURRENT_TIMESTAMP ELSE `published_at` END,
        `error_message` = p_error_message,
        `retry_count` = CASE WHEN p_status = 'failed' THEN `retry_count` + 1 ELSE `retry_count` END
    WHERE `id` = p_event_id;
    
    SET v_affected_rows = ROW_COUNT();
    
    COMMIT;
    
    IF v_affected_rows = 0 THEN
        SELECT 'NOT_FOUND' as result, 'Event not found' as message;
    ELSE
        SELECT 'SUCCESS' as result, 'Event status updated' as message;
    END IF;
END ;;
DELIMITER ;

-- Shard 2용 정리 프로시저들
DROP PROCEDURE IF EXISTS `fp_universal_outbox_cleanup_published`;
DELIMITER ;;
CREATE PROCEDURE `fp_universal_outbox_cleanup_published`(
    IN p_retention_days INT
)
COMMENT 'SchedulerService용 published 이벤트 정리'
BEGIN
    DECLARE v_deleted_count INT DEFAULT 0;
    DECLARE v_retention_days INT DEFAULT 7;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT('retention_days:', COALESCE(p_retention_days, v_retention_days));
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_universal_outbox_cleanup_published', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    SET v_retention_days = COALESCE(p_retention_days, 7);
    IF v_retention_days < 1 THEN
        SET v_retention_days = 7;
    END IF;
    
    START TRANSACTION;
    
    DELETE FROM `universal_outbox`
    WHERE `status` = 'published'
      AND `published_at` < DATE_SUB(NOW(), INTERVAL v_retention_days DAY);
    
    SET v_deleted_count = ROW_COUNT();
    
    COMMIT;
    
    SELECT 'SUCCESS' as result, v_deleted_count as deleted_count, 
           CONCAT(v_retention_days, ' days') as retention_period;
END ;;
DELIMITER ;

DROP PROCEDURE IF EXISTS `fp_universal_outbox_cleanup_failed`;
DELIMITER ;;
CREATE PROCEDURE `fp_universal_outbox_cleanup_failed`(
    IN p_retention_days INT
)
COMMENT 'SchedulerService용 failed/dead_letter 이벤트 정리'
BEGIN
    DECLARE v_deleted_count INT DEFAULT 0;
    DECLARE v_retention_days INT DEFAULT 30;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT('retention_days:', COALESCE(p_retention_days, v_retention_days));
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_universal_outbox_cleanup_failed', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    SET v_retention_days = COALESCE(p_retention_days, 30);
    IF v_retention_days < 1 THEN
        SET v_retention_days = 30;
    END IF;
    
    START TRANSACTION;
    
    DELETE FROM `universal_outbox`
    WHERE `status` IN ('failed', 'dead_letter')
      AND `created_at` < DATE_SUB(NOW(), INTERVAL v_retention_days DAY);
    
    SET v_deleted_count = ROW_COUNT();
    
    COMMIT;
    
    SELECT 'SUCCESS' as result, v_deleted_count as deleted_count,
           CONCAT(v_retention_days, ' days') as retention_period;
END ;;
DELIMITER ;

DROP PROCEDURE IF EXISTS `fp_universal_outbox_cleanup_sequences`;
DELIMITER ;;
CREATE PROCEDURE `fp_universal_outbox_cleanup_sequences`(
    IN p_retention_days INT
)
COMMENT 'SchedulerService용 사용되지 않는 시퀀스 정리'
BEGIN
    DECLARE v_deleted_count INT DEFAULT 0;
    DECLARE v_retention_days INT DEFAULT 90;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT('retention_days:', COALESCE(p_retention_days, v_retention_days));
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_universal_outbox_cleanup_sequences', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    SET v_retention_days = COALESCE(p_retention_days, 90);
    IF v_retention_days < 30 THEN
        SET v_retention_days = 90;
    END IF;
    
    START TRANSACTION;
    
    DELETE s FROM `outbox_sequences` s
    LEFT JOIN `universal_outbox` o ON s.domain = o.domain AND s.partition_key = o.partition_key
    WHERE o.id IS NULL
      AND s.updated_at < DATE_SUB(NOW(), INTERVAL v_retention_days DAY);
    
    SET v_deleted_count = ROW_COUNT();
    
    COMMIT;
    
    SELECT 'SUCCESS' as result, v_deleted_count as deleted_count,
           CONCAT(v_retention_days, ' days') as retention_period;
END ;;
DELIMITER ;

SELECT 'Finance Shard 2 Universal Outbox 생성 완료' as status;
SELECT 'Universal Outbox Pattern with SchedulerService Cleanup 생성 완료!' as final_status;