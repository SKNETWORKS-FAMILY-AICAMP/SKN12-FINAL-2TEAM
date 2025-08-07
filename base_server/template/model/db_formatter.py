"""
DB 저장을 위한 데이터 포매터
예측 결과를 다양한 DB 형식으로 변환
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from dataclasses import asdict
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import sqlite3

# 추론 파이프라인에서 사용하는 데이터 클래스 import
from .inference_pipeline import PredictionOutput

class DatabaseFormatter:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def format_for_mysql(self, predictions: List[PredictionOutput]) -> List[Dict[str, Any]]:
        """
        MySQL/PostgreSQL용 포맷 변환
        
        Args:
            predictions: 예측 결과 리스트
            
        Returns:
            DB 저장용 레코드 리스트
        """
        formatted_records = []
        
        for pred in predictions:
            # 기본 예측 정보 레코드
            base_record = {
                'prediction_id': f"{pred.symbol}_{pred.prediction_timestamp.replace(':', '').replace('-', '').replace('T', '_').split('.')[0]}",
                'symbol': pred.symbol,
                'prediction_timestamp': pred.prediction_timestamp,
                'current_date': pred.current_date,
                'current_price': pred.current_price,
                'current_volume': pred.current_volume,
                
                # 현재 기술적 지표
                'current_ma_5': pred.current_ma_5,
                'current_ma_20': pred.current_ma_20,
                'current_ma_60': pred.current_ma_60,
                'current_bb_upper': pred.current_bb_upper,
                'current_bb_middle': pred.current_bb_middle,
                'current_bb_lower': pred.current_bb_lower,
                'current_rsi': pred.current_rsi,
                
                # 신호 정보
                'trend_direction': pred.trend_direction,
                'volatility_level': pred.volatility_level,
                
                # 메타데이터
                'confidence_score': pred.confidence_score,
                'model_version': pred.model_version,
                'data_quality_score': pred.data_quality_score,
                
                # JSON으로 저장할 배열 데이터
                'predicted_prices': json.dumps(pred.predicted_prices),
                'predicted_bb_upper': json.dumps(pred.predicted_bb_upper),
                'predicted_bb_lower': json.dumps(pred.predicted_bb_lower),
                'predicted_dates': json.dumps(pred.predicted_dates),
                
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            formatted_records.append(base_record)
        
        return formatted_records
    
    def format_for_mongodb(self, predictions: List[PredictionOutput]) -> List[Dict[str, Any]]:
        """
        MongoDB용 포맷 변환
        
        Args:
            predictions: 예측 결과 리스트
            
        Returns:
            MongoDB 저장용 문서 리스트
        """
        documents = []
        
        for pred in predictions:
            # PredictionOutput을 딕셔너리로 변환
            doc = asdict(pred)
            
            # MongoDB 전용 필드 추가
            doc['_id'] = f"{pred.symbol}_{pred.prediction_timestamp.replace(':', '').replace('-', '').replace('T', '_').split('.')[0]}"
            doc['created_at'] = datetime.now()
            doc['updated_at'] = datetime.now()
            
            # 5일 예측을 개별 객체로 구조화
            doc['daily_predictions'] = []
            for i in range(5):
                daily_pred = {
                    'day': i + 1,
                    'date': pred.predicted_dates[i],
                    'predicted_price': pred.predicted_prices[i],
                    'predicted_bb_upper': pred.predicted_bb_upper[i],
                    'predicted_bb_lower': pred.predicted_bb_lower[i],
                    'predicted_bb_middle': (pred.predicted_bb_upper[i] + pred.predicted_bb_lower[i]) / 2
                }
                doc['daily_predictions'].append(daily_pred)
            
            # 기술적 지표를 별도 객체로 구조화
            doc['technical_indicators'] = {
                'ma_5': pred.current_ma_5,
                'ma_20': pred.current_ma_20,
                'ma_60': pred.current_ma_60,
                'bollinger_bands': {
                    'upper': pred.current_bb_upper,
                    'middle': pred.current_bb_middle,
                    'lower': pred.current_bb_lower
                },
                'rsi': pred.current_rsi
            }

            documents.append(doc)
        
        return documents
    
    def format_for_elasticsearch(self, predictions: List[PredictionOutput]) -> List[Dict[str, Any]]:
        """
        Elasticsearch용 포맷 변환
        
        Args:
            predictions: 예측 결과 리스트
            
        Returns:
            Elasticsearch 인덱싱용 문서 리스트
        """
        documents = []
        
        for pred in predictions:
            # 기본 문서 구조
            doc = {
                'timestamp': datetime.now().isoformat(),
                'symbol': pred.symbol,
                'prediction_date': pred.current_date,
                
                # 현재 시장 데이터
                'market_data': {
                    'price': pred.current_price,
                    'volume': pred.current_volume,
                    'date': pred.current_date
                },
                
                # 기술적 지표
                'technical_indicators': {
                    'moving_averages': {
                        'ma_5': pred.current_ma_5,
                        'ma_20': pred.current_ma_20,
                        'ma_60': pred.current_ma_60
                    },
                    'bollinger_bands': {
                        'upper': pred.current_bb_upper,
                        'middle': pred.current_bb_middle,
                        'lower': pred.current_bb_lower
                    },
                    'rsi': pred.current_rsi
                },
                
                # 예측 결과
                'predictions': {
                    'prices': pred.predicted_prices,
                    'bollinger_upper': pred.predicted_bb_upper,
                    'bollinger_lower': pred.predicted_bb_lower,
                    'dates': pred.predicted_dates
                },

                # 모델 정보
                'model_info': {
                    'version': pred.model_version,
                    'confidence': pred.confidence_score,
                    'data_quality': pred.data_quality_score
                },
            }
            
            documents.append(doc)
        
        return documents
    
    def create_dataframe(self, predictions: List[PredictionOutput]) -> pd.DataFrame:
        """
        pandas DataFrame으로 변환
        
        Args:
            predictions: 예측 결과 리스트
            
        Returns:
            DataFrame
        """
        # 플랫 구조로 데이터 변환
        flat_data = []
        
        for pred in predictions:
            # 기본 정보
            base_info = {
                'symbol': pred.symbol,
                'prediction_timestamp': pred.prediction_timestamp,
                'current_date': pred.current_date,
                'current_price': pred.current_price,
                'current_volume': pred.current_volume,
                'current_ma_5': pred.current_ma_5,
                'current_ma_20': pred.current_ma_20,
                'current_ma_60': pred.current_ma_60,
                'current_bb_upper': pred.current_bb_upper,
                'current_bb_middle': pred.current_bb_middle,
                'current_bb_lower': pred.current_bb_lower,
                'current_rsi': pred.current_rsi,
                'confidence_score': pred.confidence_score,
                'model_version': pred.model_version,
                'data_quality_score': pred.data_quality_score
            }
            
            # 5일 예측을 별도 컬럼으로 추가
            for i in range(5):
                base_info[f'predicted_price_day_{i+1}'] = pred.predicted_prices[i]
                base_info[f'predicted_bb_upper_day_{i+1}'] = pred.predicted_bb_upper[i]
                base_info[f'predicted_bb_lower_day_{i+1}'] = pred.predicted_bb_lower[i]
                base_info[f'predicted_date_day_{i+1}'] = pred.predicted_dates[i]
            
            flat_data.append(base_info)
        
        return pd.DataFrame(flat_data)
    
    def create_time_series_dataframe(self, predictions: List[PredictionOutput]) -> pd.DataFrame:
        """
        시계열 분석용 DataFrame 생성
        각 예측 일자별로 레코드를 생성
        
        Args:
            predictions: 예측 결과 리스트
            
        Returns:
            시계열 DataFrame
        """
        time_series_data = []
        
        for pred in predictions:
            # 현재 데이터
            current_record = {
                'symbol': pred.symbol,
                'date': pred.current_date,
                'price': pred.current_price,
                'bb_upper': pred.current_bb_upper,
                'bb_middle': pred.current_bb_middle,
                'bb_lower': pred.current_bb_lower,
                'data_type': 'actual',
                'prediction_timestamp': pred.prediction_timestamp
            }
            time_series_data.append(current_record)
            
            # 예측 데이터
            for i in range(5):
                pred_record = {
                    'symbol': pred.symbol,
                    'date': pred.predicted_dates[i],
                    'price': pred.predicted_prices[i],
                    'bb_upper': pred.predicted_bb_upper[i],
                    'bb_middle': (pred.predicted_bb_upper[i] + pred.predicted_bb_lower[i]) / 2,
                    'bb_lower': pred.predicted_bb_lower[i],
                    'data_type': 'predicted',
                    'prediction_timestamp': pred.prediction_timestamp,
                    'prediction_day': i + 1
                }
                time_series_data.append(pred_record)
        
        df = pd.DataFrame(time_series_data)
        df['date'] = pd.to_datetime(df['date'])
        return df.sort_values(['symbol', 'date'])
    
    def save_to_csv(self, predictions: List[PredictionOutput], filepath: str):
        """CSV 파일로 저장"""
        try:
            df = self.create_dataframe(predictions)
            df.to_csv(filepath, index=False, encoding='utf-8')
            self.logger.info(f"Data saved to CSV: {filepath}")
        except Exception as e:
            self.logger.error(f"Error saving to CSV: {str(e)}")
    
    def save_to_sqlite(self, predictions: List[PredictionOutput], db_path: str, table_name: str = 'stock_predictions'):
        """SQLite 데이터베이스에 저장"""
        try:
            # DataFrame 생성
            df = self.create_dataframe(predictions)
            
            # SQLite 연결 및 저장
            with sqlite3.connect(db_path) as conn:
                df.to_sql(table_name, conn, if_exists='append', index=False)
            
            self.logger.info(f"Data saved to SQLite: {db_path}, table: {table_name}")
        except Exception as e:
            self.logger.error(f"Error saving to SQLite: {str(e)}")
    
    def save_to_mysql(self, predictions: List[PredictionOutput], 
                     connection_string: str, 
                     table_name: str = 'stock_predictions'):
        """
        MySQL 데이터베이스에 저장
        
        Args:
            predictions: 예측 결과 리스트
            connection_string: MySQL 연결 문자열 (예: mysql+pymysql://user:pass@host:port/db)
            table_name: 테이블 명
        """
        try:
            # MySQL용 포맷 변환
            formatted_records = self.format_for_mysql(predictions)
            
            if not formatted_records:
                self.logger.warning("No data to save to MySQL")
                return
            
            # SQLAlchemy를 사용한 MySQL 연결 및 저장
            engine = create_engine(connection_string)
            
            # DataFrame으로 변환하여 bulk insert
            df = pd.DataFrame(formatted_records)
            
            # JSON 문자열을 다시 딕셔너리로 변환 (pandas가 JSON을 처리하도록)
            json_columns = ['predicted_prices', 'predicted_bb_upper', 'predicted_bb_lower', 'predicted_dates']
            for col in json_columns:
                if col in df.columns:
                    df[col] = df[col].apply(lambda x: json.loads(x) if isinstance(x, str) else x)
            
            # MySQL에 저장 (replace: 중복 시 업데이트)
            df.to_sql(table_name, engine, if_exists='append', index=False, method='multi')
            
            self.logger.info(f"Data saved to MySQL: {len(formatted_records)} records, table: {table_name}")
            
        except SQLAlchemyError as e:
            self.logger.error(f"SQLAlchemy error saving to MySQL: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error saving to MySQL: {str(e)}")
    
    def generate_sql_insert_statements(self, predictions: List[PredictionOutput], table_name: str = 'stock_predictions') -> List[str]:
        """
        SQL INSERT 문 생성
        
        Args:
            predictions: 예측 결과 리스트
            table_name: 테이블 명
            
        Returns:
            SQL INSERT 문 리스트
        """
        formatted_records = self.format_for_mysql(predictions)
        sql_statements = []
        
        if not formatted_records:
            return sql_statements
        
        # 컬럼명 추출
        columns = list(formatted_records[0].keys())
        columns_str = ', '.join([f'`{col}`' for col in columns])
        
        for record in formatted_records:
            values = []
            for col in columns:
                value = record[col]
                if value is None:
                    values.append('NULL')
                elif isinstance(value, str):
                    values.append(f"'{value.replace(chr(39), chr(39)+chr(39))}'")  # 작은따옴표 이스케이프
                elif isinstance(value, bool):
                    values.append('1' if value else '0')
                else:
                    values.append(str(value))
            
            values_str = ', '.join(values)
            sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_str});"
            sql_statements.append(sql)
        
        return sql_statements
    
    def create_table_schema(self, db_type: str = 'mysql') -> str:
        """
        데이터베이스 테이블 생성 스키마 반환
        
        Args:
            db_type: 데이터베이스 타입 ('mysql', 'postgresql', 'sqlite')
            
        Returns:
            CREATE TABLE SQL 문
        """
        if db_type.lower() == 'mysql':
            return """
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
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_symbol_date (symbol, current_date),
                INDEX idx_timestamp (prediction_timestamp)
            );
            """
        
        elif db_type.lower() == 'postgresql':
            return """
            CREATE TABLE IF NOT EXISTS stock_predictions (
                prediction_id VARCHAR(100) PRIMARY KEY,
                symbol VARCHAR(10) NOT NULL,
                prediction_timestamp TIMESTAMP NOT NULL,
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
                predicted_prices JSONB,
                predicted_bb_upper JSONB,
                predicted_bb_lower JSONB,
                predicted_dates JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_symbol_date ON stock_predictions (symbol, current_date);
            CREATE INDEX IF NOT EXISTS idx_timestamp ON stock_predictions (prediction_timestamp);
            """
        
        elif db_type.lower() == 'sqlite':
            return """
            CREATE TABLE IF NOT EXISTS stock_predictions (
                prediction_id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                prediction_timestamp TEXT NOT NULL,
                current_date TEXT NOT NULL,
                current_price REAL NOT NULL,
                current_volume INTEGER NOT NULL,
                current_ma_5 REAL,
                current_ma_20 REAL,
                current_ma_60 REAL,
                current_bb_upper REAL,
                current_bb_middle REAL,
                current_bb_lower REAL,
                current_rsi REAL,
                confidence_score REAL,
                model_version TEXT,
                data_quality_score REAL,
                predicted_prices TEXT,
                predicted_bb_upper TEXT,
                predicted_bb_lower TEXT,
                predicted_dates TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_symbol_date ON stock_predictions (symbol, current_date);
            CREATE INDEX IF NOT EXISTS idx_timestamp ON stock_predictions (prediction_timestamp);
            """
        
        else:
            raise ValueError(f"Unsupported database type: {db_type}")


def main():
    """테스트 및 예제 실행"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database Formatter Test")
    parser.add_argument("--input", required=True, help="Input JSON file with predictions")
    parser.add_argument("--output-csv", help="Output CSV file")
    parser.add_argument("--output-sqlite", help="Output SQLite database file")
    parser.add_argument("--output-mysql", action="store_true", help="Save to MySQL database")
    parser.add_argument("--mysql-host", default="localhost", help="MySQL host")
    parser.add_argument("--mysql-port", default="3306", help="MySQL port")
    parser.add_argument("--mysql-user", default="stockuser", help="MySQL username")
    parser.add_argument("--mysql-password", default="stockpass", help="MySQL password")
    parser.add_argument("--mysql-database", default="stock_predictions", help="MySQL database name")
    parser.add_argument("--db-type", default="mysql", choices=["mysql", "postgresql", "sqlite"], 
                       help="Database type for schema generation")
    
    args = parser.parse_args()
    
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    
    try:
        # JSON 파일에서 예측 결과 로드
        with open(args.input, 'r', encoding='utf-8') as f:
            predictions_data = json.load(f)
        
        # PredictionOutput 객체로 변환
        predictions = [PredictionOutput(**data) for data in predictions_data]
        
        # Formatter 초기화
        formatter = DatabaseFormatter()
        
        # CSV 저장
        if args.output_csv:
            formatter.save_to_csv(predictions, args.output_csv)
        
        # SQLite 저장
        if args.output_sqlite:
            formatter.save_to_sqlite(predictions, args.output_sqlite)
        
        # MySQL 저장
        if args.output_mysql:
            mysql_connection_string = f"mysql+pymysql://{args.mysql_user}:{args.mysql_password}@{args.mysql_host}:{args.mysql_port}/{args.mysql_database}"
            formatter.save_to_mysql(predictions, mysql_connection_string)
        
        # 스키마 출력
        print(f"\n{args.db_type.upper()} Table Schema:")
        print(formatter.create_table_schema(args.db_type))
        
        # 포맷 예제 출력
        print(f"\nFormatted for {args.db_type}:")
        if args.db_type == 'mysql':
            formatted = formatter.format_for_mysql(predictions[:1])
            print(json.dumps(formatted[0], indent=2, default=str))
        
        print("Database formatting completed successfully!")
        
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()