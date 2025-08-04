-- MySQL 초기화 스크립트
-- 주식 예측 데이터 저장용 테이블 생성

USE stock_predictions;

CREATE TABLE IF NOT EXISTS stock_predictions (
    prediction_id VARCHAR(100) PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    prediction_timestamp DATETIME NOT NULL,
    current_date DATE NOT NULL,
    current_price DECIMAL(10,4) NOT NULL,
    current_volume BIGINT NOT NULL,
    current_ma_5 DECIMAL(10,4),
    current_ma_20 DECIMAL(10,4),
    current_ma_60 DECIMAL(10,4),
    current_bb_upper DECIMAL(10,4),
    current_bb_middle DECIMAL(10,4),
    current_bb_lower DECIMAL(10,4),
    current_rsi DECIMAL(5,2),
    confidence_score DECIMAL(5,4),
    model_version VARCHAR(20),
    data_quality_score DECIMAL(5,4),
    predicted_prices JSON,
    predicted_bb_upper JSON,
    predicted_bb_lower JSON,
    predicted_dates JSON,
    trend_direction VARCHAR(10),
    volatility_level VARCHAR(10),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_symbol_date (symbol, current_date),
    INDEX idx_timestamp (prediction_timestamp),
    INDEX idx_symbol_recent (symbol, prediction_timestamp DESC)
);

-- 샘플 데이터를 위한 추가 인덱스
CREATE INDEX IF NOT EXISTS idx_confidence ON stock_predictions (confidence_score);
CREATE INDEX IF NOT EXISTS idx_symbol_trend ON stock_predictions (symbol, trend_direction);

-- 권한 설정 (필요시)
GRANT ALL PRIVILEGES ON stock_predictions.* TO 'stockuser'@'%';
FLUSH PRIVILEGES;