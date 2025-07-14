-- =====================================
-- 아웃박스 패턴용 샤딩 테이블 생성
-- (finance_shard_1, finance_shard_2에 동시 생성)
-- =====================================

-- ========== Finance Shard 1 ==========
USE finance_shard_1;

-- 아웃박스 이벤트 테이블 (Shard 1)
CREATE TABLE IF NOT EXISTS `outbox_events` (
  `id` varchar(36) NOT NULL COMMENT '이벤트 고유 ID (UUID)',
  `event_type` varchar(100) NOT NULL COMMENT '이벤트 타입',
  `aggregate_id` varchar(100) NOT NULL COMMENT '집계 ID (account_db_key 등)',
  `aggregate_type` varchar(50) NOT NULL COMMENT '집계 타입 (account, portfolio, trade 등)',
  `event_data` json NOT NULL COMMENT '이벤트 데이터',
  `status` enum('pending','published','failed','retry') NOT NULL DEFAULT 'pending' COMMENT '이벤트 상태',
  `retry_count` int NOT NULL DEFAULT 0 COMMENT '재시도 횟수',
  `max_retries` int NOT NULL DEFAULT 3 COMMENT '최대 재시도 횟수',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성 시간',
  `updated_at` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '수정 시간',
  `published_at` datetime DEFAULT NULL COMMENT '발행 시간',
  PRIMARY KEY (`id`),
  KEY `idx_status_created` (`status`, `created_at`),
  KEY `idx_event_type` (`event_type`),
  KEY `idx_aggregate` (`aggregate_type`, `aggregate_id`),
  KEY `idx_published_at` (`published_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='아웃박스 이벤트 테이블 (샤드별)';

-- Saga 상태 관리 테이블 (샤드별)
CREATE TABLE IF NOT EXISTS `saga_instances` (
  `saga_id` varchar(36) NOT NULL COMMENT 'Saga 인스턴스 ID',
  `saga_type` varchar(100) NOT NULL COMMENT 'Saga 타입',
  `initiator_id` varchar(100) NOT NULL COMMENT 'Saga 시작자 ID (account_db_key)',
  `status` enum('started','completed','failed','compensating','compensated') NOT NULL DEFAULT 'started',
  `current_step` int NOT NULL DEFAULT 0 COMMENT '현재 단계',
  `total_steps` int NOT NULL COMMENT '전체 단계 수',
  `saga_data` json DEFAULT NULL COMMENT 'Saga 상태 데이터',
  `error_message` text DEFAULT NULL COMMENT '에러 메시지',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `completed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`saga_id`),
  KEY `idx_saga_type_status` (`saga_type`, `status`),
  KEY `idx_initiator_id` (`initiator_id`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Saga 인스턴스 관리 테이블 (샤드별)';

-- Saga 단계 실행 기록 테이블 (샤드별)
CREATE TABLE IF NOT EXISTS `saga_steps` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `saga_id` varchar(36) NOT NULL COMMENT 'Saga 인스턴스 ID',
  `step_number` int NOT NULL COMMENT '단계 번호',
  `step_name` varchar(100) NOT NULL COMMENT '단계 이름',
  `status` enum('pending','completed','failed','compensated') NOT NULL DEFAULT 'pending',
  `request_data` json DEFAULT NULL COMMENT '요청 데이터',
  `response_data` json DEFAULT NULL COMMENT '응답 데이터',
  `error_message` text DEFAULT NULL COMMENT '에러 메시지',
  `started_at` datetime DEFAULT NULL,
  `completed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_saga_step` (`saga_id`, `step_number`),
  KEY `idx_saga_id` (`saga_id`),
  KEY `idx_status` (`status`),
  FOREIGN KEY (`saga_id`) REFERENCES `saga_instances`(`saga_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Saga 단계 실행 기록 테이블 (샤드별)';

-- ========== Finance Shard 2 ==========
USE finance_shard_2;

-- 아웃박스 이벤트 테이블 (Shard 2)
CREATE TABLE IF NOT EXISTS `outbox_events` (
  `id` varchar(36) NOT NULL COMMENT '이벤트 고유 ID (UUID)',
  `event_type` varchar(100) NOT NULL COMMENT '이벤트 타입',
  `aggregate_id` varchar(100) NOT NULL COMMENT '집계 ID (account_db_key 등)',
  `aggregate_type` varchar(50) NOT NULL COMMENT '집계 타입 (account, portfolio, trade 등)',
  `event_data` json NOT NULL COMMENT '이벤트 데이터',
  `status` enum('pending','published','failed','retry') NOT NULL DEFAULT 'pending' COMMENT '이벤트 상태',
  `retry_count` int NOT NULL DEFAULT 0 COMMENT '재시도 횟수',
  `max_retries` int NOT NULL DEFAULT 3 COMMENT '최대 재시도 횟수',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성 시간',
  `updated_at` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '수정 시간',
  `published_at` datetime DEFAULT NULL COMMENT '발행 시간',
  PRIMARY KEY (`id`),
  KEY `idx_status_created` (`status`, `created_at`),
  KEY `idx_event_type` (`event_type`),
  KEY `idx_aggregate` (`aggregate_type`, `aggregate_id`),
  KEY `idx_published_at` (`published_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='아웃박스 이벤트 테이블 (샤드별)';

-- Saga 상태 관리 테이블 (Shard 2)
CREATE TABLE IF NOT EXISTS `saga_instances` (
  `saga_id` varchar(36) NOT NULL COMMENT 'Saga 인스턴스 ID',
  `saga_type` varchar(100) NOT NULL COMMENT 'Saga 타입',
  `initiator_id` varchar(100) NOT NULL COMMENT 'Saga 시작자 ID (account_db_key)',
  `status` enum('started','completed','failed','compensating','compensated') NOT NULL DEFAULT 'started',
  `current_step` int NOT NULL DEFAULT 0 COMMENT '현재 단계',
  `total_steps` int NOT NULL COMMENT '전체 단계 수',
  `saga_data` json DEFAULT NULL COMMENT 'Saga 상태 데이터',
  `error_message` text DEFAULT NULL COMMENT '에러 메시지',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `completed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`saga_id`),
  KEY `idx_saga_type_status` (`saga_type`, `status`),
  KEY `idx_initiator_id` (`initiator_id`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Saga 인스턴스 관리 테이블 (샤드별)';

-- Saga 단계 실행 기록 테이블 (Shard 2)
CREATE TABLE IF NOT EXISTS `saga_steps` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `saga_id` varchar(36) NOT NULL COMMENT 'Saga 인스턴스 ID',
  `step_number` int NOT NULL COMMENT '단계 번호',
  `step_name` varchar(100) NOT NULL COMMENT '단계 이름',
  `status` enum('pending','completed','failed','compensated') NOT NULL DEFAULT 'pending',
  `request_data` json DEFAULT NULL COMMENT '요청 데이터',
  `response_data` json DEFAULT NULL COMMENT '응답 데이터',
  `error_message` text DEFAULT NULL COMMENT '에러 메시지',
  `started_at` datetime DEFAULT NULL,
  `completed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_saga_step` (`saga_id`, `step_number`),
  KEY `idx_saga_id` (`saga_id`),
  KEY `idx_status` (`status`),
  FOREIGN KEY (`saga_id`) REFERENCES `saga_instances`(`saga_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Saga 단계 실행 기록 테이블 (샤드별)';

-- 아웃박스 이벤트 발행 상태 추적 테이블 (Global DB용)
-- USE finance_global;
-- CREATE TABLE IF NOT EXISTS `outbox_publish_status` (
--   `shard_id` int NOT NULL COMMENT '샤드 ID',
--   `last_processed_event_id` varchar(36) DEFAULT NULL COMMENT '마지막 처리된 이벤트 ID',
--   `last_processed_at` datetime DEFAULT NULL COMMENT '마지막 처리 시간',
--   `events_processed` bigint DEFAULT 0 COMMENT '처리된 이벤트 수',
--   `events_failed` bigint DEFAULT 0 COMMENT '실패한 이벤트 수',
--   `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
--   PRIMARY KEY (`shard_id`)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='아웃박스 발행 상태 추적 (Global)';

SELECT 'Finance Shard 1 & 2 Outbox 테이블 생성 완료' as status;