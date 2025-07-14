-- =====================================
-- 로그인 카운트 필드 추가 (첫 로그인 판정용)
-- =====================================

USE finance_global;

-- table_accountid에 login_count 필드 추가
-- MySQL에서는 IF NOT EXISTS를 지원하지 않으므로 조건부 추가 방식 사용
SET @sql = (
    SELECT IF(
        COUNT(*) = 0,
        'ALTER TABLE `table_accountid` ADD COLUMN `login_count` int NOT NULL DEFAULT 0 COMMENT ''로그인 횟수 (첫 로그인 판정용)'';',
        'SELECT ''Column login_count already exists'' as message;'
    )
    FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = 'finance_global' 
    AND TABLE_NAME = 'table_accountid' 
    AND COLUMN_NAME = 'login_count'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 기존 계정들의 login_count를 1로 초기화 (기존 계정은 이미 로그인한 것으로 간주)
UPDATE `table_accountid` SET `login_count` = 1 WHERE `login_count` = 0;

SELECT 'Login Count 필드 추가 완료' as status;