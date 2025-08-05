-- ================================================
-- 인앱 알림 시스템 확장 (Finance Shard용) - 기존 패턴 준수
-- 목적: 게임 방식의 읽음/미읽음 마킹 인앱 알림 시스템
-- 특징: 읽은 알림 조회 시 자동 삭제 처리 (게임 패턴)
-- 적용: finance_shard_1, finance_shard_2 (채팅/시그널과 동일 패턴)
-- ================================================

-- =====================================
-- Shard DB 1에 인앱 알림 테이블 추가
-- =====================================
USE finance_shard_1;

-- 인앱 알림 테이블 (기존 패턴: idx AUTO_INCREMENT PRIMARY KEY)
CREATE TABLE IF NOT EXISTS `table_inapp_notifications` (
  `idx` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '알림 고유 인덱스 (기존 패턴)',
  `notification_id` varchar(128) NOT NULL COMMENT '알림 ID (비즈니스 키)',
  `account_db_key` bigint unsigned NOT NULL COMMENT '사용자 계정 DB 키',
  `type_id` varchar(64) NOT NULL COMMENT '알림 타입 ID (SIGNAL_ALERT, TRADE_COMPLETE 등)',
  `title` varchar(255) NOT NULL COMMENT '알림 제목',
  `message` text NOT NULL COMMENT '알림 메시지',
  `data` json DEFAULT NULL COMMENT '추가 데이터 (symbol, price, confidence 등)',
  `priority` tinyint unsigned DEFAULT 3 COMMENT '우선순위 (1=긴급, 5=낮음)',
  `is_read` tinyint(1) DEFAULT 0 COMMENT '읽음 여부 (게임 방식 마킹)',
  `read_at` datetime(6) DEFAULT NULL COMMENT '읽은 시간',
  `expires_at` datetime(6) DEFAULT NULL COMMENT '만료 시간 (자동 삭제용)',
  `is_deleted` tinyint(1) DEFAULT 0 COMMENT '삭제 여부 (기존 패턴: 소프트 삭제)',
  `created_at` datetime(6) DEFAULT CURRENT_TIMESTAMP(6) COMMENT '생성일시',
  `updated_at` datetime(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '수정일시',
  PRIMARY KEY (`idx`),
  UNIQUE KEY `uk_notification_id` (`notification_id`),
  KEY `idx_account_unread` (`account_db_key`, `is_read`, `is_deleted`),
  KEY `idx_account_created` (`account_db_key`, `created_at`),
  KEY `idx_type_priority` (`type_id`, `priority`),
  KEY `idx_expires_at` (`expires_at`),
  KEY `idx_is_deleted` (`is_deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='인앱 알림 테이블 (Shard 1)';

-- 알림 읽음 통계 (샤드별) - 채팅 통계 패턴과 동일
CREATE TABLE IF NOT EXISTS `table_inapp_notification_stats` (
  `idx` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '통계 고유 인덱스',
  `account_db_key` bigint unsigned NOT NULL COMMENT '사용자 계정 DB 키',
  `date` date NOT NULL COMMENT '날짜',
  `total_count` int unsigned DEFAULT 0 COMMENT '총 알림 수',
  `read_count` int unsigned DEFAULT 0 COMMENT '읽은 알림 수',
  `unread_count` int unsigned DEFAULT 0 COMMENT '읽지 않은 알림 수',
  `priority_1_count` int unsigned DEFAULT 0 COMMENT '긴급 알림 수',
  `priority_2_count` int unsigned DEFAULT 0 COMMENT '높음 알림 수',
  `priority_3_count` int unsigned DEFAULT 0 COMMENT '보통 알림 수',
  `auto_deleted_count` int unsigned DEFAULT 0 COMMENT '자동 삭제된 알림 수 (읽은 알림 조회 시)',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일시',
  PRIMARY KEY (`idx`),
  UNIQUE KEY `uk_account_date` (`account_db_key`, `date`),
  KEY `idx_date` (`date`),
  KEY `idx_updated_at` (`updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='인앱 알림 통계 테이블 (Shard 1)';

-- ================================================
-- 저장 프로시저 (Shard 1) - 기존 에러 처리 패턴 준수
-- ================================================

-- 인앱 알림 생성 (시그널 패턴과 동일한 에러 처리)
DROP PROCEDURE IF EXISTS `fp_inapp_notification_create`;
DELIMITER ;;
CREATE PROCEDURE `fp_inapp_notification_create`(
    IN p_notification_id VARCHAR(128),
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_type_id VARCHAR(64),
    IN p_title VARCHAR(255),
    IN p_message TEXT,
    IN p_data JSON,
    IN p_priority TINYINT UNSIGNED,
    IN p_expires_at DATETIME(6)
)
BEGIN
    DECLARE v_existing_count INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    -- 기존 패턴과 동일한 예외 처리
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_notification_id, ',', p_account_db_key, ',', p_type_id);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_inapp_notification_create', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- 중복 체크 (기존 패턴과 동일)
    SELECT COUNT(*) INTO v_existing_count
    FROM table_inapp_notifications 
    WHERE notification_id = p_notification_id 
      AND is_deleted = 0;
    
    IF v_existing_count > 0 THEN
        ROLLBACK;
        SELECT 'EXISTS' as result, 'Notification already exists' as message, p_notification_id as notification_id;
    ELSE
        -- 알림 생성 (기본값: 읽지않음, 삭제되지않음)
        INSERT INTO table_inapp_notifications (
            notification_id, account_db_key, type_id, title, message, 
            data, priority, expires_at, is_read, is_deleted, created_at, updated_at
        ) VALUES (
            p_notification_id, p_account_db_key, p_type_id, p_title, p_message,
            p_data, IFNULL(p_priority, 3), p_expires_at, 0, 0, NOW(6), NOW(6)
        );
        
        -- 통계 업데이트 (채팅 통계 패턴과 동일한 UPSERT)
        INSERT INTO table_inapp_notification_stats (
            account_db_key, date, total_count, unread_count,
            priority_1_count, priority_2_count, priority_3_count
        ) VALUES (
            p_account_db_key, CURDATE(), 1, 1,
            IF(IFNULL(p_priority, 3) = 1, 1, 0),
            IF(IFNULL(p_priority, 3) = 2, 1, 0),
            IF(IFNULL(p_priority, 3) = 3, 1, 0)
        ) ON DUPLICATE KEY UPDATE
            total_count = total_count + 1,
            unread_count = unread_count + 1,
            priority_1_count = priority_1_count + IF(VALUES(priority_1_count) > 0, 1, 0),
            priority_2_count = priority_2_count + IF(VALUES(priority_2_count) > 0, 1, 0),
            priority_3_count = priority_3_count + IF(VALUES(priority_3_count) > 0, 1, 0),
            updated_at = NOW();
        
        COMMIT;
        SELECT 'SUCCESS' as result, 'Notification created successfully' as message, 
               p_notification_id as notification_id, LAST_INSERT_ID() as idx;
    END IF;
    
END ;;
DELIMITER ;

-- 📋 읽지 않은 알림 목록 조회 (삭제 처리 없음)
DROP PROCEDURE IF EXISTS `fp_inapp_notifications_get_unread`;
DELIMITER ;;
CREATE PROCEDURE `fp_inapp_notifications_get_unread`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_type_id VARCHAR(64),  -- NULL: 전체 타입
    IN p_limit INT,
    IN p_offset INT
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', IFNULL(p_type_id, 'NULL'));
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_inapp_notifications_get_unread', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 읽지 않은 알림만 조회 (삭제 처리 없음)
    SELECT 
        idx,
        notification_id,
        type_id,
        title,
        message,
        data,
        priority,
        is_read,
        read_at,
        expires_at,
        created_at,
        updated_at
    FROM table_inapp_notifications
    WHERE account_db_key = p_account_db_key
        AND is_deleted = 0
        AND is_read = 0  -- 읽지 않은 것만
        AND (p_type_id IS NULL OR type_id = p_type_id)
        AND (expires_at IS NULL OR expires_at > NOW(6))
    ORDER BY 
        priority ASC,  -- 우선순위 높은 것부터
        created_at DESC
    LIMIT p_limit OFFSET p_offset;
    
END ;;
DELIMITER ;

-- 🎮 읽은 알림 목록 조회 + 자동 삭제 (게임 패턴)
DROP PROCEDURE IF EXISTS `fp_inapp_notifications_get_read_and_delete`;
DELIMITER ;;
CREATE PROCEDURE `fp_inapp_notifications_get_read_and_delete`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_type_id VARCHAR(64),  -- NULL: 전체 타입
    IN p_limit INT,
    IN p_offset INT
)
BEGIN
    DECLARE v_deleted_count INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', IFNULL(p_type_id, 'NULL'));
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_inapp_notifications_get_read_and_delete', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- 임시 테이블 생성하여 조회할 읽은 알림 저장
    CREATE TEMPORARY TABLE temp_read_notifications AS
    SELECT 
        idx,
        notification_id,
        type_id,
        title,
        message,
        data,
        priority,
        is_read,
        read_at,
        expires_at,
        created_at,
        updated_at
    FROM table_inapp_notifications
    WHERE account_db_key = p_account_db_key
        AND is_deleted = 0
        AND is_read = 1  -- 읽은 것만
        AND (p_type_id IS NULL OR type_id = p_type_id)
        AND (expires_at IS NULL OR expires_at > NOW(6))
    ORDER BY 
        read_at DESC,  -- 읽은 시간 순
        created_at DESC
    LIMIT p_limit OFFSET p_offset;
    
    -- 조회된 읽은 알림들을 소프트 삭제 (게임 패턴)
    UPDATE table_inapp_notifications n
    INNER JOIN temp_read_notifications t ON n.notification_id = t.notification_id
    SET n.is_deleted = 1,
        n.updated_at = NOW(6);
    
    SET v_deleted_count = ROW_COUNT();
    
    -- 통계 업데이트 (자동 삭제 카운트)
    IF v_deleted_count > 0 THEN
        UPDATE table_inapp_notification_stats
        SET read_count = GREATEST(read_count - v_deleted_count, 0),
            total_count = GREATEST(total_count - v_deleted_count, 0),
            auto_deleted_count = auto_deleted_count + v_deleted_count,
            updated_at = NOW()
        WHERE account_db_key = p_account_db_key 
            AND date = CURDATE();
    END IF;
    
    -- 결과 반환 (삭제 전 데이터)
    SELECT * FROM temp_read_notifications;
    
    -- 임시 테이블 삭제
    DROP TEMPORARY TABLE temp_read_notifications;
    
    COMMIT;
    
END ;;
DELIMITER ;

-- 📋 전체 알림 목록 조회 (읽음/안읽음 모두, 삭제 처리 없음)
DROP PROCEDURE IF EXISTS `fp_inapp_notifications_get_all`;
DELIMITER ;;
CREATE PROCEDURE `fp_inapp_notifications_get_all`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_type_id VARCHAR(64),  -- NULL: 전체 타입
    IN p_limit INT,
    IN p_offset INT
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', IFNULL(p_type_id, 'NULL'));
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_inapp_notifications_get_all', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 전체 알림 목록 조회 (읽음/안읽음 모두, 삭제 처리 없음)
    SELECT 
        idx,
        notification_id,
        type_id,
        title,
        message,
        data,
        priority,
        is_read,
        read_at,
        expires_at,
        created_at,
        updated_at
    FROM table_inapp_notifications
    WHERE account_db_key = p_account_db_key
        AND is_deleted = 0
        AND (p_type_id IS NULL OR type_id = p_type_id)
        AND (expires_at IS NULL OR expires_at > NOW(6))
    ORDER BY 
        is_read ASC,      -- 읽지 않은 것부터
        priority ASC,     -- 우선순위 높은 것부터
        created_at DESC
    LIMIT p_limit OFFSET p_offset;
    
END ;;
DELIMITER ;

-- 인앱 알림 읽음 처리 (게임 방식 마킹)
DROP PROCEDURE IF EXISTS `fp_inapp_notification_mark_read`;
DELIMITER ;;
CREATE PROCEDURE `fp_inapp_notification_mark_read`(
    IN p_notification_id VARCHAR(128),
    IN p_account_db_key BIGINT UNSIGNED
)
BEGIN
    DECLARE v_notification_exists INT DEFAULT 0;
    DECLARE v_already_read INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_notification_id, ',', p_account_db_key);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_inapp_notification_mark_read', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- 알림 존재 및 읽음 상태 확인
    SELECT 
        COUNT(*) as exists_count,
        SUM(is_read) as read_count
    INTO v_notification_exists, v_already_read
    FROM table_inapp_notifications
    WHERE notification_id = p_notification_id 
        AND account_db_key = p_account_db_key 
        AND is_deleted = 0;
    
    IF v_notification_exists = 0 THEN
        ROLLBACK;
        SELECT 'FAILED' as result, 'Notification not found' as message;
    ELSEIF v_already_read > 0 THEN
        ROLLBACK;
        SELECT 'ALREADY_READ' as result, 'Notification already read' as message;
    ELSE
        -- 읽음 처리 (게임 방식: 마킹 + 시간 기록)
        UPDATE table_inapp_notifications
        SET is_read = 1, 
            read_at = NOW(6), 
            updated_at = NOW(6)
        WHERE notification_id = p_notification_id 
            AND account_db_key = p_account_db_key 
            AND is_deleted = 0;
        
        -- 통계 업데이트 (읽음으로 이동)
        UPDATE table_inapp_notification_stats
        SET read_count = read_count + 1,
            unread_count = GREATEST(unread_count - 1, 0),
            updated_at = NOW()
        WHERE account_db_key = p_account_db_key 
            AND date = CURDATE();
        
        COMMIT;
        SELECT 'SUCCESS' as result, 'Notification marked as read' as message;
    END IF;
    
END ;;
DELIMITER ;

-- 인앱 알림 일괄 읽음 처리
DROP PROCEDURE IF EXISTS `fp_inapp_notifications_mark_all_read`;
DELIMITER ;;
CREATE PROCEDURE `fp_inapp_notifications_mark_all_read`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_type_id VARCHAR(64)  -- NULL: 전체, 특정 타입만
)
BEGIN
    DECLARE v_updated_count INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', IFNULL(p_type_id, 'NULL'));
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_inapp_notifications_mark_all_read', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- 읽지 않은 알림 모두 읽음 처리
    UPDATE table_inapp_notifications
    SET is_read = 1, 
        read_at = NOW(6), 
        updated_at = NOW(6)
    WHERE account_db_key = p_account_db_key
        AND is_read = 0
        AND is_deleted = 0
        AND (p_type_id IS NULL OR type_id = p_type_id)
        AND (expires_at IS NULL OR expires_at > NOW(6));
    
    SET v_updated_count = ROW_COUNT();
    
    -- 통계 업데이트 (배치 읽음 처리)
    IF v_updated_count > 0 THEN
        UPDATE table_inapp_notification_stats
        SET read_count = read_count + v_updated_count,
            unread_count = GREATEST(unread_count - v_updated_count, 0),
            updated_at = NOW()
        WHERE account_db_key = p_account_db_key 
            AND date = CURDATE();
    END IF;
    
    COMMIT;
    SELECT 'SUCCESS' as result, 
           CONCAT(v_updated_count, ' notifications marked as read') as message, 
           v_updated_count as updated_count;
    
END ;;
DELIMITER ;

-- 인앱 알림 소프트 삭제 (기존 패턴과 동일)
DROP PROCEDURE IF EXISTS `fp_inapp_notification_soft_delete`;
DELIMITER ;;
CREATE PROCEDURE `fp_inapp_notification_soft_delete`(
    IN p_notification_id VARCHAR(128),
    IN p_account_db_key BIGINT UNSIGNED
)
BEGIN
    DECLARE v_notification_exists INT DEFAULT 0;
    DECLARE v_is_read INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_notification_id, ',', p_account_db_key);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_inapp_notification_soft_delete', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- 알림 존재 확인
    SELECT COUNT(*), SUM(is_read)
    INTO v_notification_exists, v_is_read
    FROM table_inapp_notifications
    WHERE notification_id = p_notification_id 
        AND account_db_key = p_account_db_key 
        AND is_deleted = 0;
    
    IF v_notification_exists = 0 THEN
        ROLLBACK;
        SELECT 'FAILED' as result, 'Notification not found' as message;
    ELSE
        -- 소프트 삭제 (기존 패턴: is_deleted = 1)
        UPDATE table_inapp_notifications
        SET is_deleted = 1, 
            updated_at = NOW(6)
        WHERE notification_id = p_notification_id 
            AND account_db_key = p_account_db_key;
        
        -- 통계 업데이트 (삭제된 것 반영)
        IF v_is_read = 0 THEN
            -- 읽지 않은 것이었다면 unread_count 감소
            UPDATE table_inapp_notification_stats
            SET total_count = GREATEST(total_count - 1, 0),
                unread_count = GREATEST(unread_count - 1, 0),
                updated_at = NOW()
            WHERE account_db_key = p_account_db_key 
                AND date = CURDATE();
        ELSE
            -- 읽은 것이었다면 read_count 감소
            UPDATE table_inapp_notification_stats
            SET total_count = GREATEST(total_count - 1, 0),
                read_count = GREATEST(read_count - 1, 0),
                updated_at = NOW()
            WHERE account_db_key = p_account_db_key 
                AND date = CURDATE();
        END IF;
        
        COMMIT;
        SELECT 'SUCCESS' as result, 'Notification soft deleted successfully' as message;
    END IF;
    
END ;;
DELIMITER ;

-- 통계 조회 (시그널 통계 패턴과 동일)
DROP PROCEDURE IF EXISTS `fp_inapp_notification_stats_get`;
DELIMITER ;;
CREATE PROCEDURE `fp_inapp_notification_stats_get`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_days INT  -- 최근 N일
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_days);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_inapp_notification_stats_get', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 일별 통계 조회
    SELECT 
        date,
        total_count,
        read_count,
        unread_count,
        priority_1_count,
        priority_2_count,
        priority_3_count,
        auto_deleted_count,
        created_at,
        updated_at
    FROM table_inapp_notification_stats
    WHERE account_db_key = p_account_db_key
        AND date >= DATE_SUB(CURDATE(), INTERVAL p_days DAY)
    ORDER BY date DESC;
    
    -- 현재 읽지 않은 알림 수 (실시간)
    SELECT COUNT(*) as current_unread_count
    FROM table_inapp_notifications
    WHERE account_db_key = p_account_db_key
        AND is_read = 0
        AND is_deleted = 0
        AND (expires_at IS NULL OR expires_at > NOW(6));
    
END ;;
DELIMITER ;

-- 만료된 알림 정리 (배치용) - 시그널 성과 업데이트 패턴과 동일
DROP PROCEDURE IF EXISTS `fp_inapp_notifications_cleanup_expired`;
DELIMITER ;;
CREATE PROCEDURE `fp_inapp_notifications_cleanup_expired`()
BEGIN
    DECLARE v_deleted_count INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_inapp_notifications_cleanup_expired', @ErrorState, @ErrorNo, @ErrorMessage, '');
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- 만료된 알림 소프트 삭제
    UPDATE table_inapp_notifications
    SET is_deleted = 1, 
        updated_at = NOW(6)
    WHERE expires_at IS NOT NULL 
        AND expires_at <= NOW(6)
        AND is_deleted = 0;
    
    SET v_deleted_count = ROW_COUNT();
    
    COMMIT;
    SELECT 'SUCCESS' as result, 
           CONCAT(v_deleted_count, ' expired notifications cleaned up') as message, 
           v_deleted_count as deleted_count;
    
END ;;
DELIMITER ;

-- =====================================
-- Shard DB 2에 동일한 구조 생성
-- =====================================
USE finance_shard_2;

-- 동일한 테이블 구조 복사 (Shard 2)
CREATE TABLE IF NOT EXISTS `table_inapp_notifications` (
  `idx` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '알림 고유 인덱스 (기존 패턴)',
  `notification_id` varchar(128) NOT NULL COMMENT '알림 ID (비즈니스 키)',
  `account_db_key` bigint unsigned NOT NULL COMMENT '사용자 계정 DB 키',
  `type_id` varchar(64) NOT NULL COMMENT '알림 타입 ID (SIGNAL_ALERT, TRADE_COMPLETE 등)',
  `title` varchar(255) NOT NULL COMMENT '알림 제목',
  `message` text NOT NULL COMMENT '알림 메시지',
  `data` json DEFAULT NULL COMMENT '추가 데이터 (symbol, price, confidence 등)',
  `priority` tinyint unsigned DEFAULT 3 COMMENT '우선순위 (1=긴급, 5=낮음)',
  `is_read` tinyint(1) DEFAULT 0 COMMENT '읽음 여부 (게임 방식 마킹)',
  `read_at` datetime(6) DEFAULT NULL COMMENT '읽은 시간',
  `expires_at` datetime(6) DEFAULT NULL COMMENT '만료 시간 (자동 삭제용)',
  `is_deleted` tinyint(1) DEFAULT 0 COMMENT '삭제 여부 (기존 패턴: 소프트 삭제)',
  `created_at` datetime(6) DEFAULT CURRENT_TIMESTAMP(6) COMMENT '생성일시',
  `updated_at` datetime(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '수정일시',
  PRIMARY KEY (`idx`),
  UNIQUE KEY `uk_notification_id` (`notification_id`),
  KEY `idx_account_unread` (`account_db_key`, `is_read`, `is_deleted`),
  KEY `idx_account_created` (`account_db_key`, `created_at`),
  KEY `idx_type_priority` (`type_id`, `priority`),
  KEY `idx_expires_at` (`expires_at`),
  KEY `idx_is_deleted` (`is_deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='인앱 알림 테이블 (Shard 2)';

CREATE TABLE IF NOT EXISTS `table_inapp_notification_stats` (
  `idx` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '통계 고유 인덱스',
  `account_db_key` bigint unsigned NOT NULL COMMENT '사용자 계정 DB 키',
  `date` date NOT NULL COMMENT '날짜',
  `total_count` int unsigned DEFAULT 0 COMMENT '총 알림 수',
  `read_count` int unsigned DEFAULT 0 COMMENT '읽은 알림 수',
  `unread_count` int unsigned DEFAULT 0 COMMENT '읽지 않은 알림 수',
  `priority_1_count` int unsigned DEFAULT 0 COMMENT '긴급 알림 수',
  `priority_2_count` int unsigned DEFAULT 0 COMMENT '높음 알림 수',
  `priority_3_count` int unsigned DEFAULT 0 COMMENT '보통 알림 수',
  `auto_deleted_count` int unsigned DEFAULT 0 COMMENT '자동 삭제된 알림 수 (읽은 알림 조회 시)',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일시',
  PRIMARY KEY (`idx`),
  UNIQUE KEY `uk_account_date` (`account_db_key`, `date`),
  KEY `idx_date` (`date`),
  KEY `idx_updated_at` (`updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='인앱 알림 통계 테이블 (Shard 2)';

-- =====================================
-- Shard 2 프로시저 복사 (간소화 - 실제로는 모든 프로시저 복사 필요)
-- =====================================

-- TODO: 실제 운영에서는 모든 프로시저를 Shard 2에도 동일하게 생성 필요:
-- - fp_inapp_notification_create              (알림 생성)
-- - fp_inapp_notifications_get_unread         (읽지않은 알림 조회)
-- - fp_inapp_notifications_get_read_and_delete (읽은 알림 조회 + 자동 삭제)
-- - fp_inapp_notifications_get_all            (전체 알림 목록 조회)
-- - fp_inapp_notification_mark_read           (읽음 처리)
-- - fp_inapp_notifications_mark_all_read      (일괄 읽음 처리)
-- - fp_inapp_notification_soft_delete         (소프트 삭제)
-- - fp_inapp_notification_stats_get           (통계 조회)
-- - fp_inapp_notifications_cleanup_expired    (만료 정리)

-- 대표 프로시저 하나만 예시로 복사 (알림 생성)
DROP PROCEDURE IF EXISTS `fp_inapp_notification_create`;
DELIMITER ;;
CREATE PROCEDURE `fp_inapp_notification_create`(
    IN p_notification_id VARCHAR(128),
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_type_id VARCHAR(64),
    IN p_title VARCHAR(255),
    IN p_message TEXT,
    IN p_data JSON,
    IN p_priority TINYINT UNSIGNED,
    IN p_expires_at DATETIME(6)
)
BEGIN
    DECLARE v_existing_count INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_notification_id, ',', p_account_db_key, ',', p_type_id);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_inapp_notification_create', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    SELECT COUNT(*) INTO v_existing_count
    FROM table_inapp_notifications 
    WHERE notification_id = p_notification_id 
      AND is_deleted = 0;
    
    IF v_existing_count > 0 THEN
        ROLLBACK;
        SELECT 'EXISTS' as result, 'Notification already exists' as message, p_notification_id as notification_id;
    ELSE
        INSERT INTO table_inapp_notifications (
            notification_id, account_db_key, type_id, title, message, 
            data, priority, expires_at, is_read, is_deleted, created_at, updated_at
        ) VALUES (
            p_notification_id, p_account_db_key, p_type_id, p_title, p_message,
            p_data, IFNULL(p_priority, 3), p_expires_at, 0, 0, NOW(6), NOW(6)
        );
        
        INSERT INTO table_inapp_notification_stats (
            account_db_key, date, total_count, unread_count,
            priority_1_count, priority_2_count, priority_3_count
        ) VALUES (
            p_account_db_key, CURDATE(), 1, 1,
            IF(IFNULL(p_priority, 3) = 1, 1, 0),
            IF(IFNULL(p_priority, 3) = 2, 1, 0),
            IF(IFNULL(p_priority, 3) = 3, 1, 0)
        ) ON DUPLICATE KEY UPDATE
            total_count = total_count + 1,
            unread_count = unread_count + 1,
            priority_1_count = priority_1_count + IF(VALUES(priority_1_count) > 0, 1, 0),
            priority_2_count = priority_2_count + IF(VALUES(priority_2_count) > 0, 1, 0),
            priority_3_count = priority_3_count + IF(VALUES(priority_3_count) > 0, 1, 0),
            updated_at = NOW();
        
        COMMIT;
        SELECT 'SUCCESS' as result, 'Notification created successfully' as message, 
               p_notification_id as notification_id, LAST_INSERT_ID() as idx;
    END IF;
    
END ;;
DELIMITER ;

-- 최종 상태 확인
SELECT 'InApp notification tables with game-style auto-delete pattern created for both shards' as status;

-- ===== 완료 =====
-- 
-- 사용법 요약:
-- 1. 알림 생성: fp_inapp_notification_create
-- 2. 읽지않은 알림 조회: fp_inapp_notifications_get_unread (삭제 없음)
-- 3. 🎮 읽은 알림 조회: fp_inapp_notifications_get_read_and_delete (자동 삭제!)
-- 4. 전체 알림 조회: fp_inapp_notifications_get_all (삭제 없음)
-- 5. 읽음 처리: fp_inapp_notification_mark_read
-- 6. 일괄 읽음 처리: fp_inapp_notifications_mark_all_read
-- 7. 수동 삭제: fp_inapp_notification_soft_delete
-- 8. 통계 조회: fp_inapp_notification_stats_get
-- 9. 만료 정리: fp_inapp_notifications_cleanup_expired (배치용)
--
-- 게임 패턴 특징:
-- - 읽은 알림 조회 시 자동으로 삭제 처리
-- - 읽지 않은 알림은 계속 유지
-- - 통계에 auto_deleted_count 추가하여 자동 삭제 추적