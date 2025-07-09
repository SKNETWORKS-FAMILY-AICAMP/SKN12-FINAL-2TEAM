-- =====================================
-- Finance Global DB 생성 (game_server 구조 참고)
-- =====================================

-- Finance Global DB 생성
DROP DATABASE IF EXISTS finance_global;
CREATE DATABASE finance_global CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE finance_global;

-- 1. 에러 로그 테이블 (game_server 방식)
CREATE TABLE IF NOT EXISTS `table_errorlog` (
  `idx` int NOT NULL AUTO_INCREMENT,
  `procedure_name` varchar(45) DEFAULT NULL,
  `error_state` varchar(10) DEFAULT NULL,
  `error_no` varchar(10) DEFAULT NULL,
  `error_message` varchar(128) DEFAULT NULL,
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `param` varchar(4000) NOT NULL,
  PRIMARY KEY (`idx`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 2. 계정 ID 테이블 (game_server table_accountid 참고)
CREATE TABLE IF NOT EXISTS `table_accountid` (
  `idx` bigint unsigned NOT NULL AUTO_INCREMENT,
  `platform_type` tinyint NOT NULL DEFAULT 1,
  `account_id` varchar(100) NOT NULL,
  `account_db_key` bigint unsigned NOT NULL DEFAULT '0',
  `account_status` varchar(15) NOT NULL DEFAULT 'Normal',
  `block_endtime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `is_withdraw` bit(1) NOT NULL DEFAULT b'0',
  `withdraw_cancel_count` tinyint NOT NULL DEFAULT '0',
  `withdraw_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `login_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `logout_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `password_hash` varchar(255) NOT NULL,
  `nickname` varchar(50) NOT NULL,
  `email` varchar(100),
  `account_level` int DEFAULT 1,
  PRIMARY KEY (`idx`),
  UNIQUE KEY `ix_accountid_platform_accountid` (`platform_type`,`account_id`),
  KEY `ix_accountid_accountdbkey` (`account_db_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 3. 사용자 샤드 매핑 테이블
CREATE TABLE IF NOT EXISTS `table_user_shard_mapping` (
  `account_db_key` bigint unsigned NOT NULL,
  `shard_id` int NOT NULL,
  `assigned_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`account_db_key`),
  FOREIGN KEY (`account_db_key`) REFERENCES `table_accountid`(`account_db_key`) ON DELETE CASCADE,
  INDEX `idx_shard_id` (`shard_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 4. 샤드 설정 테이블
CREATE TABLE IF NOT EXISTS `table_shard_config` (
  `shard_id` int NOT NULL,
  `shard_name` varchar(50) NOT NULL,
  `host` varchar(255) NOT NULL,
  `port` int NOT NULL DEFAULT 3306,
  `database_name` varchar(100) NOT NULL,
  `username` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `max_connections` int DEFAULT 100,
  `status` enum('active','maintenance','disabled') DEFAULT 'active',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`shard_id`),
  INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 5. 샤드 통계 테이블
CREATE TABLE IF NOT EXISTS `table_shard_stats` (
  `shard_id` int NOT NULL,
  `user_count` int DEFAULT 0,
  `active_users` int DEFAULT 0,
  `last_updated` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`shard_id`),
  FOREIGN KEY (`shard_id`) REFERENCES `table_shard_config`(`shard_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 초기 샤드 설정 데이터 삽입
INSERT INTO `table_shard_config` (shard_id, shard_name, host, port, database_name, username, password, status) 
VALUES 
(1, 'finance_shard_1', 'localhost', 3306, 'finance_shard_1', 'root', 'Wkdwkrdhkd91!', 'active'),
(2, 'finance_shard_2', 'localhost', 3306, 'finance_shard_2', 'root', 'Wkdwkrdhkd91!', 'active');

-- 샤드 통계 초기화
INSERT INTO `table_shard_stats` (shard_id, user_count, active_users) 
VALUES 
(1, 0, 0),
(2, 0, 0);

SELECT 'Finance Global DB 생성 완료' as status;