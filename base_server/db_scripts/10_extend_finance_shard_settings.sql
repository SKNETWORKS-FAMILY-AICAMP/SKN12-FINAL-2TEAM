-- =====================================
-- Finance Shard DB 설정 관리 확장
-- 패킷명세서 기반: REQ-SET-001~006
-- =====================================

-- Shard 1에 적용
USE finance_shard_1;

-- 1. 알림 설정 테이블
CREATE TABLE IF NOT EXISTS `table_notification_settings` (
  `account_db_key` bigint unsigned NOT NULL,
  `notification_type` enum('PRICE_ALERT','NEWS','PORTFOLIO','TRADE','SYSTEM') NOT NULL,
  `channel` enum('EMAIL','PUSH','SMS','IN_APP') NOT NULL,
  `is_enabled` bit(1) NOT NULL DEFAULT b'1',
  `frequency` enum('REAL_TIME','DAILY','WEEKLY','MONTHLY') DEFAULT 'REAL_TIME',
  `quiet_hours_start` time DEFAULT NULL,
  `quiet_hours_end` time DEFAULT NULL,
  `settings` text,  -- JSON 형태로 세부 설정 저장
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`account_db_key`, `notification_type`, `channel`),
  INDEX `idx_is_enabled` (`is_enabled`),
  INDEX `idx_notification_type` (`notification_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 2. 개인화 설정 테이블
CREATE TABLE IF NOT EXISTS `table_personalization_settings` (
  `account_db_key` bigint unsigned NOT NULL,
  `theme_preference` enum('LIGHT','DARK','AUTO') DEFAULT 'DARK',
  `language` varchar(10) DEFAULT 'ko',
  `timezone` varchar(50) DEFAULT 'Asia/Seoul',
  `currency_display` varchar(10) DEFAULT 'KRW',
  `date_format` varchar(20) DEFAULT 'YYYY-MM-DD',
  `number_format` varchar(20) DEFAULT 'KR',
  `chart_style` enum('CANDLE','LINE','BAR') DEFAULT 'CANDLE',
  `default_chart_period` varchar(10) DEFAULT '1D',
  `dashboard_layout` text,  -- JSON 형태로 대시보드 레이아웃 설정 저장
  `watchlist_columns` text,  -- JSON 배열로 관심종목 표시 컬럼 설정
  `portfolio_view` enum('LIST','GRID','CARD') DEFAULT 'LIST',
  `auto_refresh_interval` int DEFAULT 30,  -- 초 단위
  `sound_effects` bit(1) NOT NULL DEFAULT b'1',
  `animation_effects` bit(1) NOT NULL DEFAULT b'1',
  `compact_mode` bit(1) NOT NULL DEFAULT b'0',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`account_db_key`),
  INDEX `idx_theme_preference` (`theme_preference`),
  INDEX `idx_language` (`language`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 3. 보안 설정 테이블
CREATE TABLE IF NOT EXISTS `table_security_settings` (
  `account_db_key` bigint unsigned NOT NULL,
  `two_factor_enabled` bit(1) NOT NULL DEFAULT b'0',
  `login_notification` bit(1) NOT NULL DEFAULT b'1',
  `session_timeout` int DEFAULT 30,  -- 분 단위
  `password_change_required` bit(1) NOT NULL DEFAULT b'0',
  `allowed_ip_ranges` text,  -- JSON 배열로 허용 IP 범위 저장
  `device_restriction` bit(1) NOT NULL DEFAULT b'0',
  `trusted_devices` text,  -- JSON 배열로 신뢰 디바이스 목록 저장
  `auto_logout_inactive` bit(1) NOT NULL DEFAULT b'1',
  `transaction_pin_required` bit(1) NOT NULL DEFAULT b'0',
  `biometric_login` bit(1) NOT NULL DEFAULT b'0',
  `security_questions` text,  -- JSON 형태로 보안 질문/답변 저장 (암호화됨)
  `last_security_review` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`account_db_key`),
  INDEX `idx_two_factor_enabled` (`two_factor_enabled`),
  INDEX `idx_device_restriction` (`device_restriction`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 4. 거래 설정 테이블
CREATE TABLE IF NOT EXISTS `table_trading_settings` (
  `account_db_key` bigint unsigned NOT NULL,
  `auto_trading_enabled` bit(1) NOT NULL DEFAULT b'0',
  `max_daily_trades` int DEFAULT 10,
  `max_position_size` decimal(5,4) DEFAULT 0.1000,  -- 포트폴리오 대비 최대 비중 (10%)
  `default_order_type` enum('MARKET','LIMIT','STOP') DEFAULT 'LIMIT',
  `default_stop_loss` decimal(10,4) DEFAULT 0.0500,  -- 5%
  `default_take_profit` decimal(10,4) DEFAULT 0.1500,  -- 15%
  `risk_management_level` enum('LOW','MEDIUM','HIGH') DEFAULT 'MEDIUM',
  `confirmation_required` bit(1) NOT NULL DEFAULT b'1',
  `pre_market_trading` bit(1) NOT NULL DEFAULT b'0',
  `after_hours_trading` bit(1) NOT NULL DEFAULT b'0',
  `fractional_shares` bit(1) NOT NULL DEFAULT b'1',
  `dividend_reinvestment` bit(1) NOT NULL DEFAULT b'0',
  `tax_optimization` bit(1) NOT NULL DEFAULT b'0',
  `commission_tier` varchar(20) DEFAULT 'STANDARD',
  `margin_trading_enabled` bit(1) NOT NULL DEFAULT b'0',
  `margin_limit` decimal(15,2) DEFAULT 0.00,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`account_db_key`),
  INDEX `idx_auto_trading_enabled` (`auto_trading_enabled`),
  INDEX `idx_risk_management_level` (`risk_management_level`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 5. 앱 설정 히스토리 테이블
CREATE TABLE IF NOT EXISTS `table_settings_history` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `account_db_key` bigint unsigned NOT NULL,
  `setting_category` enum('NOTIFICATION','PERSONALIZATION','SECURITY','TRADING') NOT NULL,
  `setting_key` varchar(100) NOT NULL,
  `old_value` text,
  `new_value` text,
  `change_reason` varchar(200) DEFAULT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  `user_agent` text DEFAULT NULL,
  `changed_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_account_db_key` (`account_db_key`),
  INDEX `idx_setting_category` (`setting_category`),
  INDEX `idx_changed_at` (`changed_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 6. 시스템 설정 템플릿 테이블
CREATE TABLE IF NOT EXISTS `table_system_setting_templates` (
  `template_id` varchar(50) NOT NULL,
  `template_name` varchar(100) NOT NULL,
  `description` text,
  `category` enum('CONSERVATIVE','MODERATE','AGGRESSIVE','BEGINNER','EXPERT') NOT NULL,
  `settings_data` text NOT NULL,  -- JSON 형태로 설정 템플릿 저장
  `is_default` bit(1) NOT NULL DEFAULT b'0',
  `is_active` bit(1) NOT NULL DEFAULT b'1',
  `usage_count` int DEFAULT 0,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`template_id`),
  INDEX `idx_category` (`category`),
  INDEX `idx_is_default` (`is_default`),
  INDEX `idx_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- =====================================
-- 설정 관리 프로시저
-- =====================================

-- 알림 설정 조회
DROP PROCEDURE IF EXISTS `fp_get_notification_settings`;
DELIMITER ;;
CREATE PROCEDURE `fp_get_notification_settings`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_notification_type VARCHAR(20)
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', COALESCE(p_notification_type, 'NULL'));
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_get_notification_settings', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 알림 설정 조회
    IF p_notification_type IS NULL OR p_notification_type = 'ALL' THEN
        SELECT 
            notification_type,
            channel,
            is_enabled,
            frequency,
            quiet_hours_start,
            quiet_hours_end,
            settings
        FROM table_notification_settings 
        WHERE account_db_key = p_account_db_key
        ORDER BY notification_type, channel;
    ELSE
        SELECT 
            notification_type,
            channel,
            is_enabled,
            frequency,
            quiet_hours_start,
            quiet_hours_end,
            settings
        FROM table_notification_settings 
        WHERE account_db_key = p_account_db_key 
          AND notification_type = p_notification_type
        ORDER BY channel;
    END IF;
    
END ;;
DELIMITER ;

-- 알림 설정 업데이트
DROP PROCEDURE IF EXISTS `fp_update_notification_settings`;
DELIMITER ;;
CREATE PROCEDURE `fp_update_notification_settings`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_notification_type VARCHAR(20),
    IN p_channel VARCHAR(20),
    IN p_is_enabled BOOLEAN,
    IN p_frequency VARCHAR(20),
    IN p_quiet_hours_start TIME,
    IN p_quiet_hours_end TIME,
    IN p_settings TEXT
)
BEGIN
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_notification_type, ',', p_channel);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_update_notification_settings', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 알림 설정 업데이트
    INSERT INTO table_notification_settings (
        account_db_key, notification_type, channel, is_enabled, frequency,
        quiet_hours_start, quiet_hours_end, settings
    ) VALUES (
        p_account_db_key, p_notification_type, p_channel, p_is_enabled, p_frequency,
        p_quiet_hours_start, p_quiet_hours_end, p_settings
    ) ON DUPLICATE KEY UPDATE
        is_enabled = p_is_enabled,
        frequency = p_frequency,
        quiet_hours_start = p_quiet_hours_start,
        quiet_hours_end = p_quiet_hours_end,
        settings = p_settings,
        updated_at = NOW();
    
    -- 변경 이력 기록
    INSERT INTO table_settings_history (
        account_db_key, setting_category, setting_key, new_value
    ) VALUES (
        p_account_db_key, 'NOTIFICATION', 
        CONCAT(p_notification_type, '_', p_channel),
        JSON_OBJECT('enabled', p_is_enabled, 'frequency', p_frequency)
    );
    
    SELECT 'SUCCESS' as result, 'Notification settings updated' as message;
    
END ;;
DELIMITER ;

-- 개인화 설정 조회
DROP PROCEDURE IF EXISTS `fp_get_personalization_settings`;
DELIMITER ;;
CREATE PROCEDURE `fp_get_personalization_settings`(
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
            VALUES ('fp_get_personalization_settings', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 개인화 설정 조회
    SELECT 
        theme_preference,
        language,
        timezone,
        currency_display,
        date_format,
        number_format,
        chart_style,
        default_chart_period,
        dashboard_layout,
        watchlist_columns,
        portfolio_view,
        auto_refresh_interval,
        sound_effects,
        animation_effects,
        compact_mode,
        updated_at
    FROM table_personalization_settings 
    WHERE account_db_key = p_account_db_key;
    
END ;;
DELIMITER ;

-- 개인화 설정 업데이트
DROP PROCEDURE IF EXISTS `fp_update_personalization_settings`;
DELIMITER ;;
CREATE PROCEDURE `fp_update_personalization_settings`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_theme_preference VARCHAR(10),
    IN p_language VARCHAR(10),
    IN p_timezone VARCHAR(50),
    IN p_currency_display VARCHAR(10),
    IN p_chart_style VARCHAR(10),
    IN p_dashboard_layout TEXT,
    IN p_sound_effects BOOLEAN,
    IN p_animation_effects BOOLEAN
)
BEGIN
    DECLARE v_old_settings TEXT;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_theme_preference, ',', p_language);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_update_personalization_settings', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 기존 설정 조회 (이력용)
    SELECT JSON_OBJECT(
        'theme', theme_preference, 
        'language', language, 
        'chart_style', chart_style
    ) INTO v_old_settings
    FROM table_personalization_settings 
    WHERE account_db_key = p_account_db_key;
    
    -- 개인화 설정 업데이트
    INSERT INTO table_personalization_settings (
        account_db_key, theme_preference, language, timezone, currency_display,
        chart_style, dashboard_layout, sound_effects, animation_effects
    ) VALUES (
        p_account_db_key, p_theme_preference, p_language, p_timezone, p_currency_display,
        p_chart_style, p_dashboard_layout, p_sound_effects, p_animation_effects
    ) ON DUPLICATE KEY UPDATE
        theme_preference = p_theme_preference,
        language = p_language,
        timezone = p_timezone,
        currency_display = p_currency_display,
        chart_style = p_chart_style,
        dashboard_layout = p_dashboard_layout,
        sound_effects = p_sound_effects,
        animation_effects = p_animation_effects,
        updated_at = NOW();
    
    -- 변경 이력 기록
    INSERT INTO table_settings_history (
        account_db_key, setting_category, setting_key, old_value, new_value
    ) VALUES (
        p_account_db_key, 'PERSONALIZATION', 'theme_and_display',
        v_old_settings,
        JSON_OBJECT(
            'theme', p_theme_preference, 
            'language', p_language, 
            'chart_style', p_chart_style
        )
    );
    
    SELECT 'SUCCESS' as result, 'Personalization settings updated' as message;
    
END ;;
DELIMITER ;

-- 거래 설정 조회
DROP PROCEDURE IF EXISTS `fp_get_trading_settings`;
DELIMITER ;;
CREATE PROCEDURE `fp_get_trading_settings`(
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
            VALUES ('fp_get_trading_settings', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 거래 설정 조회
    SELECT 
        auto_trading_enabled,
        max_daily_trades,
        max_position_size,
        default_order_type,
        default_stop_loss,
        default_take_profit,
        risk_management_level,
        confirmation_required,
        pre_market_trading,
        after_hours_trading,
        fractional_shares,
        dividend_reinvestment,
        margin_trading_enabled,
        margin_limit,
        updated_at
    FROM table_trading_settings 
    WHERE account_db_key = p_account_db_key;
    
END ;;
DELIMITER ;

-- 거래 설정 업데이트
DROP PROCEDURE IF EXISTS `fp_update_trading_settings`;
DELIMITER ;;
CREATE PROCEDURE `fp_update_trading_settings`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_auto_trading_enabled BOOLEAN,
    IN p_max_daily_trades INT,
    IN p_max_position_size DECIMAL(5,4),
    IN p_default_order_type VARCHAR(20),
    IN p_default_stop_loss DECIMAL(10,4),
    IN p_default_take_profit DECIMAL(10,4),
    IN p_risk_management_level VARCHAR(20),
    IN p_confirmation_required BOOLEAN
)
BEGIN
    DECLARE v_old_settings TEXT;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_auto_trading_enabled, ',', p_max_daily_trades);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_update_trading_settings', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    -- 기존 설정 조회 (이력용)
    SELECT JSON_OBJECT(
        'auto_trading', auto_trading_enabled,
        'max_position', max_position_size,
        'risk_level', risk_management_level
    ) INTO v_old_settings
    FROM table_trading_settings 
    WHERE account_db_key = p_account_db_key;
    
    -- 거래 설정 업데이트
    INSERT INTO table_trading_settings (
        account_db_key, auto_trading_enabled, max_daily_trades, max_position_size,
        default_order_type, default_stop_loss, default_take_profit,
        risk_management_level, confirmation_required
    ) VALUES (
        p_account_db_key, p_auto_trading_enabled, p_max_daily_trades, p_max_position_size,
        p_default_order_type, p_default_stop_loss, p_default_take_profit,
        p_risk_management_level, p_confirmation_required
    ) ON DUPLICATE KEY UPDATE
        auto_trading_enabled = p_auto_trading_enabled,
        max_daily_trades = p_max_daily_trades,
        max_position_size = p_max_position_size,
        default_order_type = p_default_order_type,
        default_stop_loss = p_default_stop_loss,
        default_take_profit = p_default_take_profit,
        risk_management_level = p_risk_management_level,
        confirmation_required = p_confirmation_required,
        updated_at = NOW();
    
    -- 변경 이력 기록
    INSERT INTO table_settings_history (
        account_db_key, setting_category, setting_key, old_value, new_value
    ) VALUES (
        p_account_db_key, 'TRADING', 'risk_and_limits',
        v_old_settings,
        JSON_OBJECT(
            'auto_trading', p_auto_trading_enabled,
            'max_position', p_max_position_size,
            'risk_level', p_risk_management_level
        )
    );
    
    SELECT 'SUCCESS' as result, 'Trading settings updated' as message;
    
END ;;
DELIMITER ;

-- 설정 템플릿 적용
DROP PROCEDURE IF EXISTS `fp_apply_setting_template`;
DELIMITER ;;
CREATE PROCEDURE `fp_apply_setting_template`(
    IN p_account_db_key BIGINT UNSIGNED,
    IN p_template_id VARCHAR(50)
)
BEGIN
    DECLARE v_settings_data TEXT;
    DECLARE v_template_exists INT DEFAULT 0;
    DECLARE ProcParam VARCHAR(4000);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET ProcParam = CONCAT(p_account_db_key, ',', p_template_id);
        GET DIAGNOSTICS CONDITION 1 @ErrorState = RETURNED_SQLSTATE, @ErrorNo = MYSQL_ERRNO, @ErrorMessage = MESSAGE_TEXT;
        ROLLBACK;
        INSERT INTO table_errorlog (procedure_name, error_state, error_no, error_message, param)
            VALUES ('fp_apply_setting_template', @ErrorState, @ErrorNo, @ErrorMessage, ProcParam);
        RESIGNAL;
    END;
    
    template_block: BEGIN
        -- 템플릿 존재 확인
        SELECT COUNT(*), settings_data INTO v_template_exists, v_settings_data
        FROM table_system_setting_templates 
        WHERE template_id = p_template_id AND is_active = 1;
        
        IF v_template_exists = 0 THEN
            SELECT 'FAILED' as result, 'Template not found' as message;
            LEAVE template_block;
        END IF;
        
        -- 템플릿 사용 횟수 증가
        UPDATE table_system_setting_templates 
        SET usage_count = usage_count + 1
        WHERE template_id = p_template_id;
        
        -- 변경 이력 기록
        INSERT INTO table_settings_history (
            account_db_key, setting_category, setting_key, new_value, change_reason
        ) VALUES (
            p_account_db_key, 'PERSONALIZATION', 'template_applied',
            v_settings_data, CONCAT('Applied template: ', p_template_id)
        );
        
        SELECT 'SUCCESS' as result, p_template_id as template_id, v_settings_data as settings_data;
    END template_block;
    
END ;;
DELIMITER ;

-- =====================================
-- 초기 데이터 삽입
-- =====================================

-- 시스템 설정 템플릿 기본 데이터
INSERT INTO table_system_setting_templates (
    template_id, template_name, description, category, settings_data, is_default
) VALUES 
('conservative_template', '보수적 투자자 설정', '안전한 투자를 선호하는 사용자를 위한 설정입니다.', 'CONSERVATIVE',
 '{"theme":"LIGHT","risk_level":"LOW","auto_trading":false,"notifications":{"price_alerts":true,"news":false},"max_position":0.05}', 1),

('moderate_template', '중도적 투자자 설정', '균형잡힌 투자를 추구하는 사용자를 위한 설정입니다.', 'MODERATE',
 '{"theme":"DARK","risk_level":"MEDIUM","auto_trading":false,"notifications":{"price_alerts":true,"news":true},"max_position":0.10}', 1),

('aggressive_template', '공격적 투자자 설정', '적극적인 투자를 추구하는 경험 있는 사용자를 위한 설정입니다.', 'AGGRESSIVE',
 '{"theme":"DARK","risk_level":"HIGH","auto_trading":true,"notifications":{"price_alerts":true,"news":true},"max_position":0.20}', 0),

('beginner_template', '초보자 설정', '투자를 처음 시작하는 사용자를 위한 안전한 설정입니다.', 'BEGINNER',
 '{"theme":"LIGHT","risk_level":"LOW","auto_trading":false,"notifications":{"price_alerts":true,"news":true},"max_position":0.03,"tutorial_mode":true}', 1)

ON DUPLICATE KEY UPDATE 
    template_name = VALUES(template_name),
    description = VALUES(description),
    settings_data = VALUES(settings_data),
    updated_at = NOW();

SELECT 'Finance Shard 1 설정 관리 확장 완료' as status;

-- =====================================
-- Shard 2에도 동일하게 적용
-- =====================================

USE finance_shard_2;

-- 동일한 테이블 구조를 Shard 2에도 생성
CREATE TABLE IF NOT EXISTS `table_notification_settings` (
  `account_db_key` bigint unsigned NOT NULL,
  `notification_type` enum('PRICE_ALERT','NEWS','PORTFOLIO','TRADE','SYSTEM') NOT NULL,
  `channel` enum('EMAIL','PUSH','SMS','IN_APP') NOT NULL,
  `is_enabled` bit(1) NOT NULL DEFAULT b'1',
  `frequency` enum('REAL_TIME','DAILY','WEEKLY','MONTHLY') DEFAULT 'REAL_TIME',
  `quiet_hours_start` time DEFAULT NULL,
  `quiet_hours_end` time DEFAULT NULL,
  `settings` text,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`account_db_key`, `notification_type`, `channel`),
  INDEX `idx_is_enabled` (`is_enabled`),
  INDEX `idx_notification_type` (`notification_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `table_personalization_settings` (
  `account_db_key` bigint unsigned NOT NULL,
  `theme_preference` enum('LIGHT','DARK','AUTO') DEFAULT 'DARK',
  `language` varchar(10) DEFAULT 'ko',
  `timezone` varchar(50) DEFAULT 'Asia/Seoul',
  `currency_display` varchar(10) DEFAULT 'KRW',
  `date_format` varchar(20) DEFAULT 'YYYY-MM-DD',
  `number_format` varchar(20) DEFAULT 'KR',
  `chart_style` enum('CANDLE','LINE','BAR') DEFAULT 'CANDLE',
  `default_chart_period` varchar(10) DEFAULT '1D',
  `dashboard_layout` text,
  `watchlist_columns` text,
  `portfolio_view` enum('LIST','GRID','CARD') DEFAULT 'LIST',
  `auto_refresh_interval` int DEFAULT 30,
  `sound_effects` bit(1) NOT NULL DEFAULT b'1',
  `animation_effects` bit(1) NOT NULL DEFAULT b'1',
  `compact_mode` bit(1) NOT NULL DEFAULT b'0',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`account_db_key`),
  INDEX `idx_theme_preference` (`theme_preference`),
  INDEX `idx_language` (`language`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `table_trading_settings` (
  `account_db_key` bigint unsigned NOT NULL,
  `auto_trading_enabled` bit(1) NOT NULL DEFAULT b'0',
  `max_daily_trades` int DEFAULT 10,
  `max_position_size` decimal(5,4) DEFAULT 0.1000,
  `default_order_type` enum('MARKET','LIMIT','STOP') DEFAULT 'LIMIT',
  `default_stop_loss` decimal(10,4) DEFAULT 0.0500,
  `default_take_profit` decimal(10,4) DEFAULT 0.1500,
  `risk_management_level` enum('LOW','MEDIUM','HIGH') DEFAULT 'MEDIUM',
  `confirmation_required` bit(1) NOT NULL DEFAULT b'1',
  `pre_market_trading` bit(1) NOT NULL DEFAULT b'0',
  `after_hours_trading` bit(1) NOT NULL DEFAULT b'0',
  `fractional_shares` bit(1) NOT NULL DEFAULT b'1',
  `dividend_reinvestment` bit(1) NOT NULL DEFAULT b'0',
  `tax_optimization` bit(1) NOT NULL DEFAULT b'0',
  `commission_tier` varchar(20) DEFAULT 'STANDARD',
  `margin_trading_enabled` bit(1) NOT NULL DEFAULT b'0',
  `margin_limit` decimal(15,2) DEFAULT 0.00,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`account_db_key`),
  INDEX `idx_auto_trading_enabled` (`auto_trading_enabled`),
  INDEX `idx_risk_management_level` (`risk_management_level`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- (나머지 테이블들과 프로시저들도 동일하게 생성...)

-- 시스템 설정 템플릿 기본 데이터 (Shard 2)
CREATE TABLE IF NOT EXISTS `table_system_setting_templates` (
  `template_id` varchar(50) NOT NULL,
  `template_name` varchar(100) NOT NULL,
  `description` text,
  `category` enum('CONSERVATIVE','MODERATE','AGGRESSIVE','BEGINNER','EXPERT') NOT NULL,
  `settings_data` text NOT NULL,
  `is_default` bit(1) NOT NULL DEFAULT b'0',
  `is_active` bit(1) NOT NULL DEFAULT b'1',
  `usage_count` int DEFAULT 0,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`template_id`),
  INDEX `idx_category` (`category`),
  INDEX `idx_is_default` (`is_default`),
  INDEX `idx_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT INTO table_system_setting_templates (
    template_id, template_name, description, category, settings_data, is_default
) VALUES 
('conservative_template', '보수적 투자자 설정', '안전한 투자를 선호하는 사용자를 위한 설정입니다.', 'CONSERVATIVE',
 '{"theme":"LIGHT","risk_level":"LOW","auto_trading":false,"notifications":{"price_alerts":true,"news":false},"max_position":0.05}', 1),

('moderate_template', '중도적 투자자 설정', '균형잡힌 투자를 추구하는 사용자를 위한 설정입니다.', 'MODERATE',
 '{"theme":"DARK","risk_level":"MEDIUM","auto_trading":false,"notifications":{"price_alerts":true,"news":true},"max_position":0.10}', 1),

('aggressive_template', '공격적 투자자 설정', '적극적인 투자를 추구하는 경험 있는 사용자를 위한 설정입니다.', 'AGGRESSIVE',
 '{"theme":"DARK","risk_level":"HIGH","auto_trading":true,"notifications":{"price_alerts":true,"news":true},"max_position":0.20}', 0),

('beginner_template', '초보자 설정', '투자를 처음 시작하는 사용자를 위한 안전한 설정입니다.', 'BEGINNER',
 '{"theme":"LIGHT","risk_level":"LOW","auto_trading":false,"notifications":{"price_alerts":true,"news":true},"max_position":0.03,"tutorial_mode":true}', 1)

ON DUPLICATE KEY UPDATE 
    template_name = VALUES(template_name),
    description = VALUES(description),
    settings_data = VALUES(settings_data),
    updated_at = NOW();

SELECT 'Finance Shard 2 설정 관리 확장 완료' as status;
SELECT 'Finance Shard DB 설정 관리 확장 완료!' as final_status;