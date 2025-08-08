-- =====================================
-- 시그널 알림 시스템 확장 (Finance Shard용)
-- 볼린저 밴드 기반 매수/매도 시그널 알림 관리
-- 
-- 기능 개요:
-- 1. 사용자가 특정 종목(TSLA, AAPL 등)에 대해 볼린저 밴드 시그널 알림을 등록
-- 2. Model Server에서 5일치 데이터를 분석하여 매수/매도 시그널 생성
-- 3. 시그널 발생 시 사용자에게 알림 전송
-- 4. 1일 후 가격 변동을 추적하여 승률/수익률 계산
-- 5. 사용자별 시그널 성과 통계 제공
-- =====================================

-- =====================================
-- 금융권 표준 DECIMAL(19,6) 적용
-- Bloomberg Terminal 표준 준수
-- 작성일: 2025-08-06
--
-- 변경사항:
-- 1. 모든 가격 필드: DECIMAL(15,4) → DECIMAL(19,6)
-- 2. 수익률 필드: DECIMAL(10,4) → DECIMAL(10,6)
-- 3. 금융권 표준 정밀도 확보
-- =====================================

-- =====================================
-- Finance Shard 1
-- =====================================
-- --------- SHARD 1 ---------
USE finance_shard_1;

-- 🔥 개발환경 - 외래키 체크 비활성화하고 테이블 재생성
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS `table_signal_history`;
DROP TABLE IF EXISTS `table_signal_alarms`;
SET FOREIGN_KEY_CHECKS = 1;
CREATE TABLE `table_signal_alarms` (
    `alarm_id` VARCHAR(128) PRIMARY KEY COMMENT '알림 고유 ID (UUID)',
    `account_db_key` BIGINT UNSIGNED NOT NULL COMMENT '사용자 계정 키',
    `symbol` VARCHAR(50) NOT NULL COMMENT '종목 코드 (TSLA, AAPL 등)',
    `company_name` VARCHAR(200) COMMENT '기업명',
    `current_price` DECIMAL(19,6) COMMENT '알림 등록 시점의 현재가 (금융권 표준)',
    `exchange` VARCHAR(50) COMMENT '거래소 (NASDAQ, NYSE 등)',
    `currency` VARCHAR(10) COMMENT '통화 (USD, KRW 등)',
    `note` VARCHAR(500) COMMENT '사용자 메모',
    `is_active` TINYINT DEFAULT 1 COMMENT '알림 수신 ON/OFF',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '삭제 여부 (soft delete)',
    `created_at` DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) COMMENT '생성 시각',
    `updated_at` DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '수정 시각',
    INDEX idx_account_symbol (account_db_key, symbol),
    INDEX idx_active (is_active, is_deleted),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='시그널 알림 등록 테이블 (금융권 표준 적용)';

DROP TABLE IF EXISTS `table_signal_history`;
CREATE TABLE `table_signal_history` (
    `signal_id` VARCHAR(128) PRIMARY KEY COMMENT '시그널 고유 ID (UUID)',
    `alarm_id` VARCHAR(128) NOT NULL COMMENT '알림 ID',
    `account_db_key` BIGINT UNSIGNED NOT NULL COMMENT '사용자 계정 키',
    `symbol` VARCHAR(50) NOT NULL COMMENT '종목 코드',
    `signal_type` VARCHAR(10) NOT NULL COMMENT '시그널 타입 (BUY/SELL)',
    `signal_price` DECIMAL(19,6) COMMENT '시그널 발생 시점의 가격 (금융권 표준)',
    `volume` BIGINT COMMENT '거래량 (참고용)',
    `triggered_at` DATETIME(6) COMMENT '시그널 발생 시각',
    `price_after_1d` DECIMAL(19,6) COMMENT '1일 후 가격 (금융권 표준)',
    `profit_rate` DECIMAL(10,6) COMMENT '수익률 (%) (정밀도 향상)',
    `is_win` TINYINT COMMENT '성공 여부 (1: 성공, 0: 실패, NULL: 미평가)',
    `evaluated_at` DATETIME(6) COMMENT '성과 평가 시각',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '삭제 여부 (soft delete)',
    `created_at` DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) COMMENT '생성 시각',
    `updated_at` DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '수정 시각',
    INDEX idx_alarm (alarm_id),
    INDEX idx_account (account_db_key),
    INDEX idx_symbol (symbol),
    INDEX idx_created (created_at),
    INDEX idx_evaluated (evaluated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='시그널 발생 히스토리 (금융권 표준 적용)';

-- =====================================
-- Finance Shard 2
-- =====================================
-- --------- SHARD 2 ---------
USE finance_shard_2;

-- 🔥 개발환경 - 외래키 체크 비활성화하고 테이블 재생성
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS `table_signal_history`;
DROP TABLE IF EXISTS `table_signal_alarms`;
SET FOREIGN_KEY_CHECKS = 1;
CREATE TABLE `table_signal_alarms` (
    `alarm_id` VARCHAR(128) PRIMARY KEY COMMENT '알림 고유 ID (UUID)',
    `account_db_key` BIGINT UNSIGNED NOT NULL COMMENT '사용자 계정 키',
    `symbol` VARCHAR(50) NOT NULL COMMENT '종목 코드 (TSLA, AAPL 등)',
    `company_name` VARCHAR(200) COMMENT '기업명',
    `current_price` DECIMAL(19,6) COMMENT '알림 등록 시점의 현재가 (금융권 표준)',
    `exchange` VARCHAR(50) COMMENT '거래소 (NASDAQ, NYSE 등)',
    `currency` VARCHAR(10) COMMENT '통화 (USD, KRW 등)',
    `note` VARCHAR(500) COMMENT '사용자 메모',
    `is_active` TINYINT DEFAULT 1 COMMENT '알림 수신 ON/OFF',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '삭제 여부 (soft delete)',
    `created_at` DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) COMMENT '생성 시각',
    `updated_at` DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '수정 시각',
    INDEX idx_account_symbol (account_db_key, symbol),
    INDEX idx_active (is_active, is_deleted),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='시그널 알림 등록 테이블 (금융권 표준 적용)';

DROP TABLE IF EXISTS `table_signal_history`;
CREATE TABLE `table_signal_history` (
    `signal_id` VARCHAR(128) PRIMARY KEY COMMENT '시그널 고유 ID (UUID)',
    `alarm_id` VARCHAR(128) NOT NULL COMMENT '알림 ID',
    `account_db_key` BIGINT UNSIGNED NOT NULL COMMENT '사용자 계정 키',
    `symbol` VARCHAR(50) NOT NULL COMMENT '종목 코드',
    `signal_type` VARCHAR(10) NOT NULL COMMENT '시그널 타입 (BUY/SELL)',
    `signal_price` DECIMAL(19,6) COMMENT '시그널 발생 시점의 가격 (금융권 표준)',
    `volume` BIGINT COMMENT '거래량 (참고용)',
    `triggered_at` DATETIME(6) COMMENT '시그널 발생 시각',
    `price_after_1d` DECIMAL(19,6) COMMENT '1일 후 가격 (금융권 표준)',
    `profit_rate` DECIMAL(10,6) COMMENT '수익률 (%) (정밀도 향상)',
    `is_win` TINYINT COMMENT '성공 여부 (1: 성공, 0: 실패, NULL: 미평가)',
    `evaluated_at` DATETIME(6) COMMENT '성과 평가 시각',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '삭제 여부 (soft delete)',
    `created_at` DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) COMMENT '생성 시각',
    `updated_at` DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '수정 시각',
    INDEX idx_alarm (alarm_id),
    INDEX idx_account (account_db_key),
    INDEX idx_symbol (symbol),
    INDEX idx_created (created_at),
    INDEX idx_evaluated (evaluated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='시그널 발생 히스토리 (금융권 표준 적용)';

-- =====================================
-- 📋 시그널 알람 등록 프로시저
-- 목적: 사용자가 특정 종목에 대한 볼린저 밴드 시그널 알림을 등록
-- 호출: autotrade_template_impl.py의 on_signal_alarm_create_req에서 사용
-- 
-- 로직:
-- 1. 같은 사용자, 같은 종목의 기존 알림 중복 체크
-- 2. 중복이 없으면 새 알림 등록 (기본값: is_active=1, is_deleted=0)
-- 3. 중복이 있으면 에러 코드 1062 반환
-- =====================================
USE finance_shard_1;

-- MySQL VARCHAR 파라미터 바인딩 이슈 해결
SET NAMES utf8mb4;

DROP PROCEDURE IF EXISTS `fp_signal_alarm_create`;
DELIMITER ;;
CREATE PROCEDURE `fp_signal_alarm_create`(
    IN p_alarm_id VARCHAR(128) CHARACTER SET utf8mb4,
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_symbol VARCHAR(50) CHARACTER SET utf8mb4,
    IN p_company_name VARCHAR(200) CHARACTER SET utf8mb4,
    IN p_current_price DECIMAL(19,6),
    IN p_exchange VARCHAR(50) CHARACTER SET utf8mb4,
    IN p_currency VARCHAR(10) CHARACTER SET utf8mb4,
    IN p_note VARCHAR(500) CHARACTER SET utf8mb4
)
BEGIN
    DECLARE v_existing_count INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000) CHARACTER SET utf8mb4;
    DECLARE dynamic_sql TEXT CHARACTER SET utf8mb4;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT('ERROR: alarm_id=', IFNULL(p_alarm_id, 'NULL'), 
                              ', account_db_key=', IFNULL(p_account_db_key, 'NULL'),
                              ', symbol=', IFNULL(p_symbol, 'NULL'));
        GET DIAGNOSTICS @cno = NUMBER;
        GET DIAGNOSTICS CONDITION @cno
        @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;

        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param, create_time)
        VALUES ('fp_signal_alarm_create', 
                IFNULL(@ErrorState, 'NULL'), 
                IFNULL(@ErrorNo, 'NULL'), 
                CONCAT('SQL_ERROR: ', IFNULL(@ErrorMessage, 'UNKNOWN')), 
                ProcParam, NOW());
        ROLLBACK;
        SELECT 1 as ErrorCode, CONCAT('SQL Error: ', IFNULL(@ErrorMessage, 'UNKNOWN ERROR')) as ErrorMessage;
    END;

    -- 단계 1: 파라미터 검증 로그
    INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param, create_time)
        VALUES ('fp_signal_alarm_create', 'DEBUG', 0, 'STEP1: Parameter validation started', CONCAT('alarm_id=', IFNULL(p_alarm_id, 'NULL'), ', account_db_key=', IFNULL(p_account_db_key, 'NULL'), ', symbol=', IFNULL(p_symbol, 'NULL')), NOW());

    -- ===============================================
    -- MySQL 8.x VARCHAR Binding Bug Complete Workaround
    -- Dynamic SQL (Prepared Statement) for Safe Processing
    -- After CONCAT, CAST, Variable Assignment All Failed
    -- Final Solution: Complete Parameter Binding Bypass
    -- ===============================================
    
    -- 단계 2: 동적 SQL로 중복 체크 (Shard1)
    INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param, create_time)
        VALUES ('fp_signal_alarm_create', 'DEBUG', 0, 'STEP2: Dynamic SQL duplicate check started', CONCAT('symbol=', p_symbol), NOW());

    -- 동적 SQL 문자열 생성 (SQL Injection 방지 처리 포함)
    SET dynamic_sql = CONCAT(
        'SELECT COUNT(*) INTO @v_existing_count ',
        'FROM table_signal_alarms ',
        'WHERE account_db_key = ', p_account_db_key, ' ',
        'AND symbol = ''', REPLACE(p_symbol, '''', ''''''), ''' ',  -- 작은따옴표 이스케이프
        'AND is_deleted = 0'
    );

    -- 디버그: 생성된 SQL 로그  
    INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param, create_time)
        VALUES ('fp_signal_alarm_create', 'DEBUG', 0, 'Generated SQL', dynamic_sql, NOW());

    -- Prepared Statement 실행 패턴
    SET @sql_stmt = dynamic_sql;              -- 세션 변수에 SQL 저장
    PREPARE stmt FROM @sql_stmt;              -- SQL 준비 (파싱 + 컴파일)
    EXECUTE stmt;                             -- SQL 실행  
    DEALLOCATE PREPARE stmt;                  -- 메모리 정리
    
    -- 글로벌 세션 변수에서 결과 가져오기
    SET v_existing_count = @v_existing_count;

    -- 단계 3: 중복 체크 완료
    INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param, create_time)
        VALUES ('fp_signal_alarm_create', 'DEBUG', 0, 'STEP3: Duplicate check completed', CONCAT('existing_count=', v_existing_count), NOW());

    IF v_existing_count > 0 THEN
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param, create_time)
            VALUES ('fp_signal_alarm_create', 'DEBUG', 0, 'STEP4: Duplicate found, returning error', '', NOW());
        ROLLBACK;
        SELECT 1062 as ErrorCode, CONCAT(p_symbol, ' 알림이 이미 등록되어 있습니다') as ErrorMessage;
    ELSE
        -- 단계 4: INSERT 시작
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param, create_time)
            VALUES ('fp_signal_alarm_create', 'DEBUG', 0, 'STEP5: INSERT started', '', NOW());
        
        START TRANSACTION;
        INSERT INTO table_signal_alarms (
            alarm_id, account_db_key, symbol, company_name, current_price,
            exchange, currency, note, is_active, is_deleted, created_at, updated_at
        ) VALUES (
            p_alarm_id, p_account_db_key, p_symbol, p_company_name, p_current_price,
            p_exchange, p_currency, p_note, 1, 0, NOW(6), NOW(6)
        );
        
        -- 단계 5: INSERT 완료
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param, create_time)
            VALUES ('fp_signal_alarm_create', 'DEBUG', 0, 'STEP6: INSERT completed', '', NOW());
        
        COMMIT;
        SELECT 0 as ErrorCode, '알림이 성공적으로 등록되었습니다' as ErrorMessage;
    END IF;
END ;;
DELIMITER ;

-- =====================================
-- 📊 시그널 알람 목록 조회 (통계 포함)
-- 목적: 사용자의 모든 알림 목록을 승률/수익률/시그널 횟수와 함께 조회
-- 호출: autotrade_template_impl.py의 on_signal_alarm_list_req에서 사용
-- 
-- 로직:
-- 1. table_signal_alarms와 table_signal_history를 LEFT JOIN
-- 2. 평가 완료된 시그널(is_win IS NOT NULL)만으로 통계 계산
-- 3. 승률 = (성공 시그널 / 전체 평가된 시그널) * 100
-- 4. 수익률 = 모든 시그널의 평균 profit_rate
-- =====================================
DROP PROCEDURE IF EXISTS `fp_signal_alarms_get_with_stats`;
DELIMITER ;;
CREATE PROCEDURE `fp_signal_alarms_get_with_stats`(
    IN p_account_db_key BIGINT UNSIGNED -- 조회할 사용자의 계정 키
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key);
        GET DIAGNOSTICS @cno = NUMBER;
        GET DIAGNOSTICS CONDITION @cno
        @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param, create_time)
            VALUES ('fp_signal_alarms_get_with_stats', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam, NOW());
        SELECT 1 as ErrorCode, COALESCE(@ErrorMessage, 'UNKNOWN ERROR') as ErrorMessage;
    END;
    
    -- 불필요한 상태 메시지 제거, 알림 데이터만 반환
    -- LEFT JOIN을 사용하여 시그널이 없는 알림도 포함
    SELECT 
        a.alarm_id,                      -- 알림 ID
        a.symbol,                        -- 종목 코드
        a.company_name,                  -- 기업명
        a.current_price,                 -- 등록 시점 가격
        a.exchange,                      -- 거래소
        a.currency,                      -- 통화
        a.note,                          -- 사용자 메모
        a.is_active,                     -- 알림 활성화 상태 (ON/OFF 스위치)
        a.created_at,                    -- 알림 등록 시간
        
        -- 시그널 통계 (평가 완료된 것만 집계)
        COALESCE(COUNT(h.signal_id), 0) as signal_count,  -- 총 시그널 발생 횟수
        COALESCE(
            ROUND(AVG(CASE WHEN h.is_win = 1 THEN 100.0 ELSE 0.0 END), 2), 
            0.0
        ) as win_rate,                   -- 승률 (%) - 1% 이상 움직임 기준
        COALESCE(ROUND(AVG(h.profit_rate), 2), 0.0) as profit_rate  -- 평균 수익률 (%)
    FROM table_signal_alarms a
    LEFT JOIN table_signal_history h ON a.alarm_id = h.alarm_id 
        AND h.is_win IS NOT NULL     -- 평가 완료된 시그널만 (1일 후 배치 처리됨)
        AND h.is_deleted = 0         -- 삭제되지 않은 시그널만
    WHERE a.account_db_key = p_account_db_key 
      AND a.is_deleted = 0           -- 삭제되지 않은 알림만
    GROUP BY a.alarm_id, a.symbol, a.company_name, a.current_price, 
             a.exchange, a.currency, a.note, a.is_active, a.created_at
    ORDER BY a.created_at DESC;      -- 최신 등록순
    
END ;;
DELIMITER ;

-- =====================================
-- 🔄 시그널 알람 활성화/비활성화 토글
-- 목적: 알림의 ON/OFF 상태를 토글 (화면에는 계속 표시되지만 시그널 수신 여부 결정)
-- 호출: autotrade_template_impl.py의 on_signal_alarm_toggle_req에서 사용
-- 
-- 로직:
-- 1. 현재 is_active 상태 조회
-- 2. NOT 연산으로 상태 토글 (1→0, 0→1)
-- 3. 변경된 상태값과 함께 성공 메시지 반환
-- =====================================
DROP PROCEDURE IF EXISTS `fp_signal_alarm_toggle`;
DELIMITER ;;
CREATE PROCEDURE `fp_signal_alarm_toggle`(
    IN p_alarm_id VARCHAR(128),      -- 토글할 알림의 ID
    IN p_account_db_key BIGINT UNSIGNED  -- 소유권 확인용 사용자 계정 키
)
BEGIN
    DECLARE v_alarm_exists INT DEFAULT 0;       -- 알림 존재 여부
    DECLARE v_current_status TINYINT(1) DEFAULT 0;  -- 현재 활성화 상태
    DECLARE v_new_status TINYINT(1) DEFAULT 0;      -- 변경될 상태
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_alarm_id, ',', p_account_db_key);
        GET DIAGNOSTICS @cno = NUMBER;
        GET DIAGNOSTICS CONDITION @cno
        @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param, create_time)
            VALUES ('fp_signal_alarm_toggle', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam, NOW());
        SELECT 1 as ErrorCode, COALESCE(@ErrorMessage, 'UNKNOWN ERROR') as ErrorMessage, 0 as new_status;
    END;
    
    START TRANSACTION;
    
    -- ===============================================
    -- MySQL 8.x VARCHAR Binding Bug Complete Workaround
    -- Dynamic SQL for p_alarm_id VARCHAR parameter
    -- ===============================================
    
    -- 동적 SQL로 알림 존재 및 현재 상태 확인 (소유권 검증 포함)
    SET @dynamic_sql = CONCAT(
        'SELECT COUNT(*), COALESCE(MAX(is_active), 0) INTO @v_alarm_exists, @v_current_status ',
        'FROM table_signal_alarms ',
        'WHERE alarm_id = ''', REPLACE(p_alarm_id, '''', ''''''), ''' ',
        'AND account_db_key = ', p_account_db_key, ' ',
        'AND is_deleted = 0'
    );
    
    PREPARE stmt FROM @dynamic_sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
    
    -- 세션 변수에서 결과 가져오기
    SET v_alarm_exists = @v_alarm_exists;
    SET v_current_status = @v_current_status;
    
    IF v_alarm_exists = 0 THEN
        ROLLBACK;
        SELECT 1002 as ErrorCode, '알림을 찾을 수 없습니다' as ErrorMessage, 0 as new_status;
    ELSE
        -- 상태 토글: 현재 상태의 반대로 설정
        SET v_new_status = NOT v_current_status;
        
        -- 동적 SQL로 UPDATE 실행 (MySQL 8.x VARCHAR 버그 우회)
        SET @update_sql = CONCAT(
            'UPDATE table_signal_alarms ',
            'SET is_active = ', v_new_status, ', ',
            'updated_at = NOW(6) ',
            'WHERE alarm_id = ''', REPLACE(p_alarm_id, '''', ''''''), ''' ',
            'AND account_db_key = ', p_account_db_key
        );
        
        PREPARE stmt FROM @update_sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
        
        COMMIT;
        SELECT 0 as ErrorCode, 
               CONCAT('알림이 ', IF(v_new_status, '활성화', '비활성화'), '되었습니다') as ErrorMessage,
               v_new_status as new_status;  -- 변경된 상태값 반환
    END IF;
    
END ;;
DELIMITER ;

-- =====================================
-- 🗑️ 시그널 알람 소프트 삭제
-- 목적: 알림을 화면에서 완전히 제거 (DB에서는 soft delete로 보존)
-- 호출: autotrade_template_impl.py의 on_signal_alarm_delete_req에서 사용
-- 
-- 차이점:
-- - 토글: is_active만 변경, 화면에 계속 표시
-- - 삭제: is_deleted=1 설정, 화면에서 완전 제거
-- =====================================
DROP PROCEDURE IF EXISTS `fp_signal_alarm_soft_delete`;
DELIMITER ;;
CREATE PROCEDURE `fp_signal_alarm_soft_delete`(
    IN p_alarm_id VARCHAR(128),      -- 삭제할 알림의 ID
    IN p_account_db_key BIGINT UNSIGNED  -- 소유권 확인용 사용자 계정 키
)
BEGIN
    DECLARE v_alarm_exists INT DEFAULT 0;  -- 알림 존재 여부
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_alarm_id, ',', p_account_db_key);
        GET DIAGNOSTICS @cno = NUMBER;
        GET DIAGNOSTICS CONDITION @cno
        @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param, create_time)
            VALUES ('fp_signal_alarm_soft_delete', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam, NOW());
        SELECT 1 as ErrorCode, COALESCE(@ErrorMessage, 'UNKNOWN ERROR') as ErrorMessage;
    END;
    
    START TRANSACTION;
    
    -- 알림 존재 및 소유권 확인
    SELECT COUNT(*) INTO v_alarm_exists
    FROM table_signal_alarms 
    WHERE CONCAT('', alarm_id) = CONCAT('', p_alarm_id) 
      AND account_db_key = p_account_db_key  -- 본인 소유 알림만
      AND is_deleted = 0;                    -- 이미 삭제된 것은 제외
    
    IF v_alarm_exists = 0 THEN
        ROLLBACK;
        SELECT 1002 as ErrorCode, '알림을 찾을 수 없습니다' as ErrorMessage;
    ELSE
        -- 소프트 삭제: 데이터는 보존하되 화면에서 제거
        UPDATE table_signal_alarms 
        SET is_deleted = 1,       -- 삭제 플래그 설정
            is_active = 0,        -- 삭제 시 비활성화도 함께 처리
            updated_at = NOW(6)   -- 수정 시간 업데이트
        WHERE CONCAT('', alarm_id) = CONCAT('', p_alarm_id) 
          AND account_db_key = p_account_db_key;
        
        COMMIT;
        SELECT 0 as ErrorCode, '알림이 삭제되었습니다' as ErrorMessage;
    END IF;
    
END ;;
DELIMITER ;

-- =====================================
-- 📈 시그널 히스토리 조회
-- 목적: 발생한 시그널들의 이력을 필터링하여 조회
-- 호출: autotrade_template_impl.py의 on_signal_history_req에서 사용
-- 
-- 기능:
-- - 특정 알림, 종목, 시그널 타입별 필터링 지원
-- - 동적 쿼리로 선택적 WHERE 조건 적용
-- - 시그널 발생 시간 역순으로 정렬
-- =====================================
DROP PROCEDURE IF EXISTS `fp_signal_history_get`;
DELIMITER ;;
CREATE PROCEDURE `fp_signal_history_get`(
    IN p_account_db_key BIGINT UNSIGNED, -- 사용자 계정 키
    IN p_alarm_id VARCHAR(128),      -- 특정 알림만 조회 (빈 문자열이면 전체)
    IN p_symbol VARCHAR(50),         -- 특정 종목만 조회 (빈 문자열이면 전체)
    IN p_signal_type VARCHAR(10),    -- BUY/SELL 필터 (빈 문자열이면 전체)
    IN p_limit INT                   -- 조회 개수 제한
)
BEGIN
    DECLARE v_sql TEXT;              -- 동적 쿼리 문자열
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', COALESCE(p_alarm_id, ''), ',', COALESCE(p_symbol, ''));
        GET DIAGNOSTICS @cno = NUMBER;
        GET DIAGNOSTICS CONDITION @cno
        @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param, create_time)
            VALUES ('fp_signal_history_get', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam, NOW());
        SELECT 1 as ErrorCode, COALESCE(@ErrorMessage, 'UNKNOWN ERROR') as ErrorMessage;
    END;
    
    -- 먼저 상태 결과를 반환
    SELECT 0 as ErrorCode, 'SUCCESS' as ErrorMessage;
    
    -- 기본 쿼리 (사용자별 삭제되지 않은 시그널만)
    SET v_sql = 'SELECT signal_id, alarm_id, symbol, signal_type, signal_price, volume, 
                        triggered_at, price_after_1d, profit_rate, is_win, evaluated_at
                 FROM table_signal_history 
                 WHERE account_db_key = ? AND is_deleted = 0';
    
    -- 선택적 필터 추가 (파라미터가 비어있지 않으면 조건 추가)
    IF p_alarm_id IS NOT NULL AND p_alarm_id != '' THEN
        SET v_sql = CONCAT(v_sql, ' AND alarm_id = "', p_alarm_id, '"');
    END IF;
    
    IF p_symbol IS NOT NULL AND p_symbol != '' THEN
        SET v_sql = CONCAT(v_sql, ' AND symbol = "', p_symbol, '"');
    END IF;
    
    IF p_signal_type IS NOT NULL AND p_signal_type != '' THEN
        SET v_sql = CONCAT(v_sql, ' AND signal_type = "', p_signal_type, '"');
    END IF;
    
    -- 정렬 및 개수 제한
    SET v_sql = CONCAT(v_sql, ' ORDER BY triggered_at DESC LIMIT ', p_limit);
    
    -- 동적 쿼리 실행 (준비된 문장 사용)
    SET @sql = v_sql;
    PREPARE stmt FROM @sql;
    SET @p_account_db_key = p_account_db_key;
    EXECUTE stmt USING @p_account_db_key;
    DEALLOCATE PREPARE stmt;
    
END ;;
DELIMITER ;

-- =====================================
-- 🤖 활성 알림 목록 조회 (추론 모델용)
-- 목적: Model Server에서 볼린저 밴드 분석할 알림 목록 제공
-- 호출: Model Server의 배치 작업에서 사용
-- 
-- 조건:
-- - is_active = 1 (사용자가 ON으로 설정한 알림만)
-- - is_deleted = 0 (삭제되지 않은 알림만)
-- - 모든 사용자의 알림을 함께 조회
-- =====================================
DROP PROCEDURE IF EXISTS `fp_signal_alarms_get_active`;
DELIMITER ;;
CREATE PROCEDURE `fp_signal_alarms_get_active`()
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        GET DIAGNOSTICS @cno = NUMBER;
        GET DIAGNOSTICS CONDITION @cno
        @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param, create_time)
            VALUES ('fp_signal_alarms_get_active', @ErrorState, @ErrorNo, @ErrorMessage, '', NOW());
        SELECT 1 as ErrorCode, COALESCE(@ErrorMessage, 'UNKNOWN ERROR') as ErrorMessage;
    END;
    
    -- 먼저 상태 결과를 반환
    SELECT 0 as ErrorCode, 'SUCCESS' as ErrorMessage;
    
    -- 추론 모델에서 분석할 활성 알림 목록 조회
    -- 등록 시간 순으로 정렬 (오래된 것부터 처리)
    SELECT 
        alarm_id,           -- 알림 ID
        account_db_key,     -- 사용자 계정 키 (시그널 발생 시 필요)
        symbol,             -- 종목 코드 (Yahoo Finance API 호출용)
        company_name,       -- 기업명
        current_price,      -- 등록 시점 가격 (참고용)
        exchange,           -- 거래소
        currency,           -- 통화
        created_at          -- 등록 시간
    FROM table_signal_alarms 
    WHERE is_active = 1     -- 활성화된 알림만
      AND is_deleted = 0    -- 삭제되지 않은 알림만
    ORDER BY created_at ASC; -- 등록 순서대로 처리
    
END ;;
DELIMITER ;

-- =====================================
-- 💾 시그널 히스토리 저장 (시그널 발생 시)
-- 목적: Model Server에서 볼린저 밴드 시그널 감지 시 히스토리 저장
-- 호출: Model Server의 시그널 생성 로직에서 사용
-- 
-- 로직:
-- 1. 시그널 발생 즉시 기본 정보 저장
-- 2. price_after_1d, profit_rate, is_win은 NULL (1일 후 배치에서 업데이트)
-- 3. triggered_at에 현재 시간 기록
-- =====================================
DROP PROCEDURE IF EXISTS `fp_signal_history_save`;
DELIMITER ;;
CREATE PROCEDURE `fp_signal_history_save`(
    IN p_signal_id VARCHAR(128),     -- UUID 형태의 시그널 고유 ID
    IN p_alarm_id VARCHAR(128),      -- 연결된 알림 ID
    IN p_account_db_key BIGINT UNSIGNED, -- 사용자 계정 키
    IN p_symbol VARCHAR(50),         -- 종목 코드
    IN p_signal_type ENUM('BUY', 'SELL'), -- 시그널 타입 (매수/매도)
    IN p_signal_price DECIMAL(19,6), -- 시그널 발생 시점의 가격 (금융권 표준)
    IN p_volume BIGINT               -- 거래량 (참고용)
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_signal_id, ',', p_alarm_id, ',', p_account_db_key, ',', p_symbol);
        GET DIAGNOSTICS @cno = NUMBER;
        GET DIAGNOSTICS CONDITION @cno
        @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param, create_time)
            VALUES ('fp_signal_history_save', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam, NOW());
        SELECT 1 as ErrorCode, COALESCE(@ErrorMessage, 'UNKNOWN ERROR') as ErrorMessage;
    END;
    
    START TRANSACTION;
    
    -- 시그널 히스토리 저장 (1일 후 평가 필드는 NULL로 저장)
    INSERT INTO table_signal_history (
        signal_id, alarm_id, account_db_key, symbol, signal_type,
        signal_price, volume, triggered_at, 
        price_after_1d, profit_rate, is_win, evaluated_at,  -- 1일 후 평가 필드 (NULL)
        is_deleted, created_at, updated_at
    ) VALUES (
        p_signal_id, p_alarm_id, p_account_db_key, p_symbol, p_signal_type,
        p_signal_price, p_volume, NOW(6),
        NULL, NULL, NULL, NULL,  -- 1일 후 배치에서 업데이트 예정
        0, NOW(6), NOW(6)
    );
    
    COMMIT;
    SELECT 0 as ErrorCode, '시그널이 저장되었습니다' as ErrorMessage;
    
END ;;
DELIMITER ;

-- =====================================
-- 📊 시그널 성과 업데이트 (1일 후 배치용)
-- 목적: 시그널 발생 1일 후 가격 변동을 추적하여 성과 평가
-- 호출: 배치 스케줄러에서 1일 후 실행
-- 
-- 평가 기준:
-- - profit_rate = (1일후가격 - 시그널가격) / 시그널가격 * 100
-- - is_win = 1% 이상 움직였는지 여부 (승률 계산에 사용)
-- =====================================
DROP PROCEDURE IF EXISTS `fp_signal_performance_update`;
DELIMITER ;;
CREATE PROCEDURE `fp_signal_performance_update`(
    IN p_signal_id VARCHAR(128),     -- 평가할 시그널 ID
    IN p_price_after_1d DECIMAL(19,6), -- 1일 후 가격 (금융권 표준)
    IN p_profit_rate DECIMAL(10,6),  -- 수익률 (%) - 외부에서 계산된 값 (정밀도 향상)
    IN p_is_win TINYINT(1)           -- 성공 여부 (1% 이상 움직임)
)
BEGIN
    DECLARE v_signal_exists INT DEFAULT 0;  -- 시그널 존재 여부
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_signal_id, ',', p_price_after_1d, ',', p_profit_rate, ',', p_is_win);
        GET DIAGNOSTICS @cno = NUMBER;
        GET DIAGNOSTICS CONDITION @cno
        @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param, create_time)
            VALUES ('fp_signal_performance_update', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam, NOW());
        SELECT 1 as ErrorCode, COALESCE(@ErrorMessage, 'UNKNOWN ERROR') as ErrorMessage;
    END;
    
    START TRANSACTION;
    
    -- 시그널 존재 확인 (삭제되지 않은 것만)
    SELECT COUNT(*) INTO v_signal_exists
    FROM table_signal_history 
    WHERE CONCAT('', signal_id) = CONCAT('', p_signal_id) 
      AND is_deleted = 0;
    
    IF v_signal_exists = 0 THEN
        ROLLBACK;
        SELECT 1002 as ErrorCode, '시그널을 찾을 수 없습니다' as ErrorMessage;
    ELSE
        -- 1일 후 성과 데이터 업데이트
        UPDATE table_signal_history 
        SET price_after_1d = p_price_after_1d,  -- 1일 후 가격
            profit_rate = p_profit_rate,         -- 수익률 (%)
            is_win = p_is_win,                   -- 성공 여부 (승률 계산용)
            evaluated_at = NOW(6),               -- 평가 완료 시간
            updated_at = NOW(6)                  -- 수정 시간
        WHERE CONCAT('', signal_id) = CONCAT('', p_signal_id);
        
        COMMIT;
        SELECT 0 as ErrorCode, '시그널 성과가 업데이트되었습니다' as ErrorMessage;
    END IF;
    
END ;;
DELIMITER ;

-- =====================================
-- 🔄 미평가 시그널 조회 (성과 업데이트용)
-- 목적: 1일 경과한 미평가 시그널 목록 조회
-- 호출: SignalMonitoringService._update_signal_performance에서 사용
-- 
-- 조회 조건:
-- - triggered_at이 지정된 날짜인 시그널
-- - evaluated_at이 NULL인 시그널 (아직 평가되지 않음)
-- - is_deleted = 0인 활성 시그널만
-- =====================================
DROP PROCEDURE IF EXISTS `fp_signal_get_pending_evaluation`;
DELIMITER ;;
CREATE PROCEDURE `fp_signal_get_pending_evaluation`(
    IN p_evaluation_date DATE  -- 평가할 날짜 (보통 어제 날짜)
)
proc_label:BEGIN
    -- 변수 선언이 먼저 와야 함
    DECLARE ProcParam VARCHAR(4000);
    
    -- 그 다음 핸들러 선언
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        GET DIAGNOSTICS @cno = NUMBER;
        GET DIAGNOSTICS CONDITION @cno
        @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param, create_time)
            VALUES ('fp_signal_get_pending_evaluation', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam, NOW());
        SELECT 1 as ErrorCode, COALESCE(@ErrorMessage, 'UNKNOWN ERROR') as ErrorMessage;
    END;
    
    -- ProcParam 설정
    SET ProcParam = CONCAT('evaluation_date=', IFNULL(p_evaluation_date, 'NULL'));
    
    -- 파라미터 검증
    IF p_evaluation_date IS NULL THEN
        SELECT 1 as ErrorCode, 'evaluation_date parameter is required' as ErrorMessage;
        LEAVE proc_label;
    END IF;
    
    -- 상태 반환
    SELECT 0 as ErrorCode, 'SUCCESS' as ErrorMessage;
    
    -- 미평가 시그널 목록 조회
    SELECT 
        signal_id,
        alarm_id,
        account_db_key,
        symbol,
        signal_type,
        signal_price,
        triggered_at
    FROM table_signal_history 
    WHERE DATE(triggered_at) = p_evaluation_date     -- 지정된 날짜에 발생한 시그널
      AND evaluated_at IS NULL                       -- 아직 평가되지 않음
      AND is_deleted = 0                             -- 활성 시그널만
    ORDER BY triggered_at ASC;                       -- 발생 시간 순
    
END ;;
DELIMITER ;

-- =====================================
-- 📈 시그널 통계 조회 (대시보드용)
-- 목적: 사용자별 전체 시그널 성과 통계 제공
-- 호출: 대시보드나 성과 분석 화면에서 사용
-- 
-- 집계 내용:
-- - 등록된 알림 수 (전체/활성)
-- - 발생한 시그널 수 (전체/매수/매도)
-- - 평가된 시그널 수와 성공 시그널 수
-- - 전체 승률과 평균 수익률
-- =====================================
DROP PROCEDURE IF EXISTS `fp_signal_statistics_get`;
DELIMITER ;;
CREATE PROCEDURE `fp_signal_statistics_get`(
    IN p_account_db_key BIGINT UNSIGNED -- 통계를 조회할 사용자 계정 키
)
BEGIN
    -- 변수 선언이 먼저 와야 함
    DECLARE ProcParam VARCHAR(4000);
    
    -- 그 다음 핸들러 선언
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        GET DIAGNOSTICS @cno = NUMBER;
        GET DIAGNOSTICS CONDITION @cno
        @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param, create_time)
            VALUES ('fp_signal_statistics_get', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam, NOW());
        SELECT 1 as ErrorCode, COALESCE(@ErrorMessage, 'UNKNOWN ERROR') as ErrorMessage;
    END;
    
    -- ProcParam 설정
    SET ProcParam = CONCAT(p_account_db_key);
    
    -- 먼저 상태 결과를 반환
    SELECT 0 as ErrorCode, 'SUCCESS' as ErrorMessage;
    
    -- 사용자별 전체 시그널 통계 조회
    -- 서브쿼리로 알림 관련 통계와 시그널 관련 통계를 함께 집계
    SELECT 
        -- 알림 관련 통계
        (SELECT COUNT(*) FROM table_signal_alarms 
         WHERE account_db_key = p_account_db_key AND is_deleted = 0) as total_alarms,    -- 전체 알림 수
        (SELECT COUNT(*) FROM table_signal_alarms 
         WHERE account_db_key = p_account_db_key AND is_active = 1 AND is_deleted = 0) as active_alarms,  -- 활성 알림 수
        
        -- 시그널 관련 통계
        COUNT(*) as total_signals,  -- 전체 시그널 수
        SUM(CASE WHEN signal_type = 'BUY' THEN 1 ELSE 0 END) as buy_signals,    -- 매수 시그널 수
        SUM(CASE WHEN signal_type = 'SELL' THEN 1 ELSE 0 END) as sell_signals,  -- 매도 시그널 수
        SUM(CASE WHEN is_win IS NOT NULL THEN 1 ELSE 0 END) as evaluated_signals, -- 평가 완료된 시그널 수
        SUM(CASE WHEN is_win = 1 THEN 1 ELSE 0 END) as win_signals,             -- 성공한 시그널 수
        
        -- 성과 통계 (평가 완료된 시그널 기준)
        COALESCE(ROUND(
            AVG(CASE WHEN is_win = 1 THEN 100.0 ELSE 0.0 END), 2  -- 승률 = (성공/전체) * 100
        ), 0.0) as overall_win_rate,                               -- 전체 승률 (%)
        COALESCE(ROUND(AVG(profit_rate), 2), 0.0) as overall_profit_rate  -- 전체 평균 수익률 (%)
    FROM table_signal_history 
    WHERE account_db_key = p_account_db_key 
      AND is_deleted = 0;  -- 삭제되지 않은 시그널만
    
END ;;
DELIMITER ;

-- =====================================
-- 🔄 Shard 2에도 동일한 프로시저 생성
-- 목적: finance_shard_1과 finance_shard_2에 동일한 프로시저 배포
-- 
-- 참고: 실제 운영에서는 스크립트 자동화 도구로 양쪽 샤드에 일괄 배포
-- =====================================

USE finance_shard_2;

-- 시그널 알림 등록 프로시저 (Shard 2용)
DROP PROCEDURE IF EXISTS `fp_signal_alarm_create`;
DELIMITER ;;
CREATE PROCEDURE `fp_signal_alarm_create`(
    IN p_alarm_id VARCHAR(128),
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_symbol VARCHAR(50),
    IN p_company_name VARCHAR(200),
    IN p_current_price DECIMAL(19,6),
    IN p_exchange VARCHAR(50),
    IN p_currency VARCHAR(10),
    IN p_note VARCHAR(500)
)
BEGIN
    DECLARE v_existing_count INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    DECLARE dynamic_sql TEXT;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_alarm_id, ',', p_account_db_key, ',', p_symbol);
        GET DIAGNOSTICS @cno = NUMBER;
        GET DIAGNOSTICS CONDITION @cno
        @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param, create_time)
            VALUES ('fp_signal_alarm_create', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam, NOW());
        SELECT 1 as ErrorCode, COALESCE(@ErrorMessage, 'UNKNOWN ERROR') as ErrorMessage;
    END;
    
    -- 단계 1: 파라미터 검증 로그 (Shard2)
    INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param, create_time)
        VALUES ('fp_signal_alarm_create_shard2', 'DEBUG', 0, 'STEP1: Parameter validation started', CONCAT('alarm_id=', IFNULL(p_alarm_id, 'NULL'), ', account_db_key=', IFNULL(p_account_db_key, 'NULL'), ', symbol=', IFNULL(p_symbol, 'NULL')), NOW());

    START TRANSACTION;
    
    -- ===============================================
    -- MySQL 8.x VARCHAR Binding Bug Complete Workaround
    -- Dynamic SQL (Prepared Statement) for Safe Processing
    -- ===============================================
    
    -- 단계 2: 동적 SQL로 중복 체크 (Shard2)
    INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param, create_time)
        VALUES ('fp_signal_alarm_create_shard2', 'DEBUG', 0, 'STEP2: Dynamic SQL duplicate check started', CONCAT('symbol=', p_symbol), NOW());

    -- 동적 SQL 문자열 생성 (SQL Injection 방지 처리 포함)
    SET dynamic_sql = CONCAT(
        'SELECT COUNT(*) INTO @v_existing_count ',
        'FROM table_signal_alarms ',
        'WHERE account_db_key = ', p_account_db_key, ' ',
        'AND symbol = ''', REPLACE(p_symbol, '''', ''''''), ''' ',  -- 작은따옴표 이스케이프
        'AND is_deleted = 0'
    );

    -- 디버그: 생성된 SQL 로그
    INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param, create_time)
        VALUES ('fp_signal_alarm_create_shard2', 'DEBUG', 0, 'Generated SQL', dynamic_sql, NOW());

    -- Prepared Statement 실행 패턴
    SET @sql_stmt = dynamic_sql;              -- 세션 변수에 SQL 저장
    PREPARE stmt FROM @sql_stmt;              -- SQL 준비 (파싱 + 컴파일)
    EXECUTE stmt;                             -- SQL 실행
    DEALLOCATE PREPARE stmt;                  -- 메모리 정리
    
    -- 글로벌 세션 변수에서 결과 가져오기
    SET v_existing_count = @v_existing_count;
    
    -- 단계 3: 중복 체크 완료 (Shard2)
    INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param, create_time)
        VALUES ('fp_signal_alarm_create_shard2', 'DEBUG', 0, 'STEP3: Duplicate check completed', CONCAT('existing_count=', v_existing_count), NOW());

    IF v_existing_count > 0 THEN
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param, create_time)
            VALUES ('fp_signal_alarm_create_shard2', 'DEBUG', 0, 'STEP4: Duplicate found, returning error', '', NOW());
        ROLLBACK;
        SELECT 1062 as ErrorCode, CONCAT(p_symbol, ' 알림이 이미 등록되어 있습니다') as ErrorMessage;
    ELSE
        -- 단계 4: INSERT 시작 (Shard2)
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param, create_time)
            VALUES ('fp_signal_alarm_create_shard2', 'DEBUG', 0, 'STEP5: INSERT started', '', NOW());

        INSERT INTO table_signal_alarms (
            alarm_id, account_db_key, symbol, company_name, current_price,
            exchange, currency, note, is_active, is_deleted, created_at, updated_at
        ) VALUES (
            p_alarm_id, p_account_db_key, p_symbol, p_company_name, p_current_price,
            p_exchange, p_currency, p_note, 1, 0, NOW(6), NOW(6)
        );
        
        -- 단계 5: INSERT 완료 (Shard2)
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param, create_time)
            VALUES ('fp_signal_alarm_create_shard2', 'DEBUG', 0, 'STEP6: INSERT completed', '', NOW());
        
        COMMIT;
        SELECT 0 as ErrorCode, '알림이 성공적으로 등록되었습니다' as ErrorMessage;
    END IF;
    
END ;;
DELIMITER ;

-- =====================================
-- 📝 나머지 프로시저들 (Shard 2용)
-- 실제 운영에서는 모든 프로시저를 복사해야 하지만 
-- 예시로 하나만 작성하고 나머지는 주석으로 표시
-- =====================================

-- TODO: 다음 프로시저들을 Shard 2에도 동일하게 생성 필요:
-- - fp_signal_alarms_get_with_stats    (알림 목록 + 통계)
-- - fp_signal_alarm_toggle             (활성화/비활성화 토글)
-- - fp_signal_alarm_soft_delete        (소프트 삭제)
-- - fp_signal_history_get              (히스토리 조회)
-- - fp_signal_alarms_get_active        (추론 모델용 활성 알림)
-- - fp_signal_history_save             (시그널 발생 시 저장)
-- - fp_signal_performance_update       (1일 후 성과 업데이트)
-- - fp_signal_statistics_get           (통계 조회)

-- ===== 완료 =====
-- 
-- 사용법 요약:
-- 1. 사용자가 알림 등록: fp_signal_alarm_create
-- 2. 알림 목록 조회: fp_signal_alarms_get_with_stats
-- 3. 알림 ON/OFF: fp_signal_alarm_toggle
-- 4. 알림 삭제: fp_signal_alarm_soft_delete
-- 5. Model Server가 활성 알림 조회: fp_signal_alarms_get_active
-- 6. 시그널 발생 시 저장: fp_signal_history_save
-- 7. 1일 후 성과 평가: fp_signal_performance_update
-- 8. 통계 조회: fp_signal_statistics_get, fp_signal_history_get

-- =====================================
-- 📈 최적화: 활성 심볼 목록만 조회 (모니터링용)
-- 목적: SignalMonitoringService에서 모니터링할 심볼 목록만 효율적으로 조회
-- 기존 문제: 모든 샤드 순회 + 전체 알림 데이터 조회로 비효율적
-- 해결책: 심볼만 중복 제거하여 반환, 샤드별 독립 실행
-- =====================================
DROP PROCEDURE IF EXISTS `fp_signal_symbols_get_active`;
DELIMITER ;;
CREATE PROCEDURE `fp_signal_symbols_get_active`()
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        GET DIAGNOSTICS @cno = NUMBER;
        GET DIAGNOSTICS CONDITION @cno
        @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param, create_time)
            VALUES ('fp_signal_symbols_get_active', @ErrorState, @ErrorNo, @ErrorMessage, '', NOW());
        SELECT 1 as ErrorCode, COALESCE(@ErrorMessage, 'UNKNOWN ERROR') as ErrorMessage;
    END;
    
    -- 상태 반환
    SELECT 0 as ErrorCode, 'SUCCESS' as ErrorMessage;
    
    -- 활성 심볼 목록만 중복 제거하여 반환 (최적화)
    -- 장점: 네트워크 트래픽 최소화, 같은 심볼 중복 모니터링 방지
    SELECT DISTINCT
        symbol,             -- 종목 코드 (모니터링 대상)
        exchange            -- 거래소 (US/KR 구분용)
    FROM table_signal_alarms 
    WHERE is_active = 1     -- 활성화된 알림만
      AND is_deleted = 0    -- 삭제되지 않은 알림만
    ORDER BY symbol ASC;    -- 알파벳 순 정렬
    
END ;;
DELIMITER ;

-- =====================================
-- 📊 최적화: 특정 심볼의 활성 알림 상세 조회
-- 목적: 시그널 발생 시 해당 심볼의 모든 활성 알림 정보 조회
-- 기존 문제: 전체 알림을 조회한 후 심볼로 필터링
-- 해결책: WHERE 절에서 심볼 직접 필터링으로 빠른 조회
-- =====================================
DROP PROCEDURE IF EXISTS `fp_signal_alarms_get_by_symbol`;
DELIMITER ;;
CREATE PROCEDURE `fp_signal_alarms_get_by_symbol`(
    IN p_symbol VARCHAR(20)
)
proc_label:BEGIN
    -- 변수 선언이 먼저 와야 함
    DECLARE ProcParam VARCHAR(4000);
    
    -- 그 다음 핸들러 선언
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        GET DIAGNOSTICS @cno = NUMBER;
        GET DIAGNOSTICS CONDITION @cno
        @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param, create_time)
            VALUES ('fp_signal_alarms_get_by_symbol', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam, NOW());
        SELECT 1 as ErrorCode, COALESCE(@ErrorMessage, 'UNKNOWN ERROR') as ErrorMessage;
    END;
    
    -- ProcParam 설정
    SET ProcParam = CONCAT('symbol=', IFNULL(p_symbol, 'NULL'));
    
    -- 파라미터 검증
    IF p_symbol IS NULL OR p_symbol = '' THEN
        SELECT 1 as ErrorCode, 'symbol parameter is required' as ErrorMessage;
        LEAVE proc_label;
    END IF;
    
    -- 상태 반환
    SELECT 0 as ErrorCode, 'SUCCESS' as ErrorMessage;
    
    -- 특정 심볼의 활성 알림 상세 정보 조회 (인덱스 최적화)
    SELECT 
        alarm_id,           -- 알림 ID (시그널 저장 시 필요)
        account_db_key,     -- 사용자 계정 키 (알림 발송 시 필요)
        symbol,             -- 종목 코드
        company_name,       -- 기업명
        current_price,      -- 등록 시점 가격
        exchange,           -- 거래소
        currency,           -- 통화
        created_at          -- 등록 시간
    FROM table_signal_alarms 
    WHERE symbol = CONVERT(p_symbol USING utf8mb4)   -- 특정 심볼만 (인덱스 활용)
      AND is_active = 1       -- 활성화된 알림만
      AND is_deleted = 0      -- 삭제되지 않은 알림만
    ORDER BY created_at ASC;  -- 등록 순서대로
    
END ;;
DELIMITER ;

-- =====================================
-- Shard 2용 나머지 프로시저들 추가
-- =====================================

-- 알림 목록 + 통계 조회 (Shard 2용)
DROP PROCEDURE IF EXISTS `fp_signal_alarms_get_with_stats`;
DELIMITER ;;
CREATE PROCEDURE `fp_signal_alarms_get_with_stats`(
    IN p_account_db_key BIGINT UNSIGNED
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT('account_db_key=', p_account_db_key);
        GET DIAGNOSTICS @cno = NUMBER;
        GET DIAGNOSTICS CONDITION @cno
        @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param, create_time)
            VALUES ('fp_signal_alarms_get_with_stats', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam, NOW());
        SELECT 1 as ErrorCode, COALESCE(@ErrorMessage, 'UNKNOWN ERROR') as ErrorMessage;
    END;
    
    -- 불필요한 상태 메시지 제거, 알림 데이터만 반환
    SELECT 
        a.alarm_id, a.symbol, a.company_name, a.current_price,
        a.exchange, a.currency, a.note, a.is_active, a.created_at,
        COALESCE(COUNT(h.signal_id), 0) as signal_count,
        COALESCE(ROUND(AVG(CASE WHEN h.is_win = 1 THEN 100.0 ELSE 0.0 END), 2), 0.0) as win_rate,
        COALESCE(ROUND(AVG(h.profit_rate), 2), 0.0) as profit_rate
    FROM table_signal_alarms a
    LEFT JOIN table_signal_history h ON a.alarm_id = h.alarm_id 
        AND h.is_win IS NOT NULL AND h.is_deleted = 0
    WHERE a.account_db_key = p_account_db_key AND a.is_deleted = 0
    GROUP BY a.alarm_id, a.symbol, a.company_name, a.current_price, 
             a.exchange, a.currency, a.note, a.is_active, a.created_at
    ORDER BY a.created_at DESC;
END ;;
DELIMITER ;

-- 알림 토글 (Shard 2용)
DROP PROCEDURE IF EXISTS `fp_signal_alarm_toggle`;
DELIMITER ;;
CREATE PROCEDURE `fp_signal_alarm_toggle`(
    IN p_alarm_id VARCHAR(128),
    IN p_account_db_key BIGINT UNSIGNED
)
BEGIN
    DECLARE v_current_status TINYINT(1) DEFAULT 0;
    DECLARE v_new_status TINYINT(1) DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_alarm_id, ',', p_account_db_key);
        GET DIAGNOSTICS @cno = NUMBER;
        GET DIAGNOSTICS CONDITION @cno
        @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param, create_time)
            VALUES ('fp_signal_alarm_toggle', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam, NOW());
        SELECT 1 as ErrorCode, COALESCE(@ErrorMessage, 'UNKNOWN ERROR') as ErrorMessage, 0 as new_status;
    END;
    
    START TRANSACTION;
    
    -- 동적 SQL로 현재 상태 조회 (MySQL 8.x VARCHAR 버그 우회)
    SET @select_sql = CONCAT(
        'SELECT is_active INTO @v_current_status ',
        'FROM table_signal_alarms ',
        'WHERE alarm_id = ''', REPLACE(p_alarm_id, '''', ''''''), ''' ',
        'AND account_db_key = ', p_account_db_key, ' ',
        'AND is_deleted = 0'
    );
    
    PREPARE stmt FROM @select_sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
    
    SET v_current_status = @v_current_status;
    
    IF v_current_status IS NULL THEN
        ROLLBACK;
        SELECT 1002 as ErrorCode, '알림을 찾을 수 없습니다' as ErrorMessage, 0 as new_status;
    ELSE
        SET v_new_status = NOT v_current_status;
        
        -- 동적 SQL로 UPDATE (MySQL 8.x VARCHAR 버그 우회)
        SET @update_sql = CONCAT(
            'UPDATE table_signal_alarms ',
            'SET is_active = ', v_new_status, ', updated_at = NOW(6) ',
            'WHERE alarm_id = ''', REPLACE(p_alarm_id, '''', ''''''), ''' ',
            'AND account_db_key = ', p_account_db_key
        );
        
        PREPARE stmt FROM @update_sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
        
        COMMIT;
        SELECT 0 as ErrorCode, 
               CONCAT('알림 상태가 ', IF(v_new_status = 1, '활성화', '비활성화'), '되었습니다') as ErrorMessage,
               v_new_status as new_status;
    END IF;
END ;;
DELIMITER ;

-- 알림 소프트 삭제 (Shard 2용)
DROP PROCEDURE IF EXISTS `fp_signal_alarm_soft_delete`;
DELIMITER ;;
CREATE PROCEDURE `fp_signal_alarm_soft_delete`(
    IN p_alarm_id VARCHAR(128),
    IN p_account_db_key BIGINT UNSIGNED
)
BEGIN
    DECLARE v_alarm_exists INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_alarm_id, ',', p_account_db_key);
        GET DIAGNOSTICS @cno = NUMBER;
        GET DIAGNOSTICS CONDITION @cno
        @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param, create_time)
            VALUES ('fp_signal_alarm_soft_delete', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam, NOW());
        SELECT 1 as ErrorCode, COALESCE(@ErrorMessage, 'UNKNOWN ERROR') as ErrorMessage;
    END;
    
    START TRANSACTION;
    
    -- 동적 SQL로 알림 존재 확인 (MySQL 8.x VARCHAR 버그 우회)
    SET @count_sql = CONCAT(
        'SELECT COUNT(*) INTO @v_alarm_exists ',
        'FROM table_signal_alarms ',
        'WHERE alarm_id = ''', REPLACE(p_alarm_id, '''', ''''''), ''' ',
        'AND account_db_key = ', p_account_db_key, ' ',
        'AND is_deleted = 0'
    );
    
    PREPARE stmt FROM @count_sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
    
    SET v_alarm_exists = @v_alarm_exists;
    
    IF v_alarm_exists = 0 THEN
        ROLLBACK;
        SELECT 1002 as ErrorCode, '알림을 찾을 수 없습니다' as ErrorMessage;
    ELSE
        -- 동적 SQL로 소프트 삭제 (MySQL 8.x VARCHAR 버그 우회)
        SET @delete_sql = CONCAT(
            'UPDATE table_signal_alarms ',
            'SET is_deleted = 1, is_active = 0, updated_at = NOW(6) ',
            'WHERE alarm_id = ''', REPLACE(p_alarm_id, '''', ''''''), ''' ',
            'AND account_db_key = ', p_account_db_key
        );
        
        PREPARE stmt FROM @delete_sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
        
        COMMIT;
        SELECT 0 as ErrorCode, '알림이 삭제되었습니다' as ErrorMessage;
    END IF;
END ;;
DELIMITER ;

-- 시그널 히스토리 조회 (Shard 2용)
DROP PROCEDURE IF EXISTS `fp_signal_history_get`;
DELIMITER ;;
CREATE PROCEDURE `fp_signal_history_get`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_alarm_id VARCHAR(128),
    IN p_symbol VARCHAR(50),
    IN p_signal_type VARCHAR(10),
    IN p_limit INT
)
BEGIN
    DECLARE v_sql TEXT;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', COALESCE(p_alarm_id, ''), ',', COALESCE(p_symbol, ''));
        GET DIAGNOSTICS @cno = NUMBER;
        GET DIAGNOSTICS CONDITION @cno
        @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param, create_time)
            VALUES ('fp_signal_history_get', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam, NOW());
        SELECT 1 as ErrorCode, COALESCE(@ErrorMessage, 'UNKNOWN ERROR') as ErrorMessage;
    END;
    
    SET v_sql = 'SELECT signal_id, alarm_id, symbol, signal_type, signal_price, volume, 
                        triggered_at, price_after_1d, profit_rate, is_win, evaluated_at
                 FROM table_signal_history 
                 WHERE account_db_key = ? AND is_deleted = 0';
    
    IF p_alarm_id IS NOT NULL AND p_alarm_id != '' THEN
        SET v_sql = CONCAT(v_sql, ' AND alarm_id = "', p_alarm_id, '"');
    END IF;
    
    IF p_symbol IS NOT NULL AND p_symbol != '' THEN
        SET v_sql = CONCAT(v_sql, ' AND symbol = "', p_symbol, '"');
    END IF;
    
    IF p_signal_type IS NOT NULL AND p_signal_type != '' THEN
        SET v_sql = CONCAT(v_sql, ' AND signal_type = "', p_signal_type, '"');
    END IF;
    
    SET v_sql = CONCAT(v_sql, ' ORDER BY triggered_at DESC');
    
    IF p_limit IS NOT NULL AND p_limit > 0 THEN
        SET v_sql = CONCAT(v_sql, ' LIMIT ', p_limit);
    END IF;
    
    SELECT 0 as ErrorCode, 'SUCCESS' as ErrorMessage;
    
    SET @sql = v_sql;
    PREPARE stmt FROM @sql;
    SET @account_db_key = p_account_db_key;
    EXECUTE stmt USING @account_db_key;
    DEALLOCATE PREPARE stmt;
END ;;
DELIMITER ;

-- 시그널 히스토리 저장 (Shard 2용)
DROP PROCEDURE IF EXISTS `fp_signal_history_save`;
DELIMITER ;;
CREATE PROCEDURE `fp_signal_history_save`(
    IN p_signal_id VARCHAR(128),
    IN p_alarm_id VARCHAR(128),
    IN p_signal_type VARCHAR(10),
    IN p_signal_price DECIMAL(19,6)
)
BEGIN
    DECLARE v_account_db_key BIGINT UNSIGNED;
    DECLARE v_symbol VARCHAR(50);
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_signal_id, ',', p_alarm_id, ',', p_signal_type, ',', p_signal_price);
        GET DIAGNOSTICS @cno = NUMBER;
        GET DIAGNOSTICS CONDITION @cno
        @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param, create_time)
            VALUES ('fp_signal_history_save', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam, NOW());
        SELECT 1 as ErrorCode, COALESCE(@ErrorMessage, 'UNKNOWN ERROR') as ErrorMessage;
    END;
    
    START TRANSACTION;
    
    SELECT account_db_key, symbol INTO v_account_db_key, v_symbol
    FROM table_signal_alarms 
    WHERE CONCAT('', alarm_id) = CONCAT('', p_alarm_id) AND is_deleted = 0;
    
    IF v_account_db_key IS NULL THEN
        ROLLBACK;
        SELECT 1002 as ErrorCode, '알림을 찾을 수 없습니다' as ErrorMessage;
    ELSE
        INSERT INTO table_signal_history (
            signal_id, alarm_id, account_db_key, symbol, signal_type, signal_price,
            volume, triggered_at, created_at, updated_at,
            price_after_1d, profit_rate, is_win, evaluated_at,
            is_deleted
        ) VALUES (
            p_signal_id, p_alarm_id, v_account_db_key, v_symbol, p_signal_type, p_signal_price,
            0, NOW(6), NOW(6), NOW(6),
            NULL, NULL, NULL, NULL,
            0
        );
        
        COMMIT;
        SELECT 0 as ErrorCode, '시그널이 저장되었습니다' as ErrorMessage;
    END IF;
END ;;
DELIMITER ;

-- 성과 업데이트 (Shard 2용)
DROP PROCEDURE IF EXISTS `fp_signal_performance_update`;
DELIMITER ;;
CREATE PROCEDURE `fp_signal_performance_update`(
    IN p_signal_id VARCHAR(128),
    IN p_price_after_1d DECIMAL(19,6),
    IN p_profit_rate DECIMAL(10,6),
    IN p_is_win TINYINT(1)
)
BEGIN
    DECLARE v_signal_exists INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_signal_id, ',', p_price_after_1d, ',', p_profit_rate, ',', p_is_win);
        GET DIAGNOSTICS @cno = NUMBER;
        GET DIAGNOSTICS CONDITION @cno
        @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param, create_time)
            VALUES ('fp_signal_performance_update', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam, NOW());
        SELECT 1 as ErrorCode, COALESCE(@ErrorMessage, 'UNKNOWN ERROR') as ErrorMessage;
    END;
    
    START TRANSACTION;
    
    SELECT COUNT(*) INTO v_signal_exists
    FROM table_signal_history 
    WHERE CONCAT('', signal_id) = CONCAT('', p_signal_id) AND is_deleted = 0;
    
    IF v_signal_exists = 0 THEN
        ROLLBACK;
        SELECT 1002 as ErrorCode, '시그널을 찾을 수 없습니다' as ErrorMessage;
    ELSE
        UPDATE table_signal_history 
        SET price_after_1d = p_price_after_1d,
            profit_rate = p_profit_rate,
            is_win = p_is_win,
            evaluated_at = NOW(6),
            updated_at = NOW(6)
        WHERE CONCAT('', signal_id) = CONCAT('', p_signal_id);
        
        COMMIT;
        SELECT 0 as ErrorCode, '시그널 성과가 업데이트되었습니다' as ErrorMessage;
    END IF;
END ;;
DELIMITER ;

-- 미평가 시그널 조회 (Shard 2용)
DROP PROCEDURE IF EXISTS `fp_signal_get_pending_evaluation`;
DELIMITER ;;
CREATE PROCEDURE `fp_signal_get_pending_evaluation`(
    IN p_evaluation_date DATE
)
proc_label:BEGIN
    -- 변수 선언이 먼저 와야 함
    DECLARE ProcParam VARCHAR(4000);
    
    -- 그 다음 핸들러 선언
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        GET DIAGNOSTICS @cno = NUMBER;
        GET DIAGNOSTICS CONDITION @cno
        @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param, create_time)
            VALUES ('fp_signal_get_pending_evaluation', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam, NOW());
        SELECT 1 as ErrorCode, COALESCE(@ErrorMessage, 'UNKNOWN ERROR') as ErrorMessage;
    END;
    
    -- ProcParam 설정
    SET ProcParam = CONCAT('evaluation_date=', IFNULL(p_evaluation_date, 'NULL'));
    
    IF p_evaluation_date IS NULL THEN
        SELECT 1 as ErrorCode, 'evaluation_date parameter is required' as ErrorMessage;
        LEAVE proc_label;
    END IF;
    
    SELECT 0 as ErrorCode, 'SUCCESS' as ErrorMessage;
    
    SELECT 
        signal_id, alarm_id, account_db_key, symbol, signal_type, signal_price, triggered_at
    FROM table_signal_history 
    WHERE DATE(triggered_at) = p_evaluation_date
      AND evaluated_at IS NULL
      AND is_deleted = 0
    ORDER BY triggered_at ASC;
END ;;
DELIMITER ;

-- 통계 조회 (Shard 2용)
DROP PROCEDURE IF EXISTS `fp_signal_statistics_get`;
DELIMITER ;;
CREATE PROCEDURE `fp_signal_statistics_get`(
    IN p_account_db_key BIGINT UNSIGNED
)
BEGIN
    -- 변수 선언이 먼저 와야 함
    DECLARE ProcParam VARCHAR(4000);
    
    -- 그 다음 핸들러 선언
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        GET DIAGNOSTICS @cno = NUMBER;
        GET DIAGNOSTICS CONDITION @cno
        @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param, create_time)
            VALUES ('fp_signal_statistics_get', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam, NOW());
        SELECT 1 as ErrorCode, COALESCE(@ErrorMessage, 'UNKNOWN ERROR') as ErrorMessage;
    END;
    
    -- ProcParam 설정
    SET ProcParam = CONCAT('account_db_key=', p_account_db_key);
    
    SELECT 0 as ErrorCode, 'SUCCESS' as ErrorMessage;
    
    SELECT 
        (SELECT COUNT(*) FROM table_signal_alarms WHERE account_db_key = p_account_db_key AND is_deleted = 0) as total_alarms,
        (SELECT COUNT(*) FROM table_signal_alarms WHERE account_db_key = p_account_db_key AND is_active = 1 AND is_deleted = 0) as active_alarms,
        COUNT(*) as total_signals,
        SUM(CASE WHEN signal_type = 'BUY' THEN 1 ELSE 0 END) as buy_signals,
        SUM(CASE WHEN signal_type = 'SELL' THEN 1 ELSE 0 END) as sell_signals,
        SUM(CASE WHEN is_win IS NOT NULL THEN 1 ELSE 0 END) as evaluated_signals,
        SUM(CASE WHEN is_win = 1 THEN 1 ELSE 0 END) as win_signals,
        COALESCE(ROUND(AVG(CASE WHEN is_win = 1 THEN 100.0 ELSE 0.0 END), 2), 0.0) as overall_win_rate,
        COALESCE(ROUND(AVG(profit_rate), 2), 0.0) as overall_profit_rate
    FROM table_signal_history 
    WHERE account_db_key = p_account_db_key AND is_deleted = 0;
END ;;
DELIMITER ;