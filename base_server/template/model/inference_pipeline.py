"""
추론 파이프라인
사용자 입력 종목의 최근 60일 데이터 수집 및 추론 실행
"""

import os
import logging
import pickle
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import json
from dataclasses import dataclass, asdict
import asyncio
from concurrent.futures import ThreadPoolExecutor

# 프로젝트 모듈 import
from data_collector import StockDataCollector
from data_preprocessor import StockDataPreprocessor
from pytorch_lstm_model import PyTorchStockLSTM
from config import get_model_paths

@dataclass
class PredictionOutput:
    """예측 결과 데이터 클래스"""
    symbol: str
    prediction_timestamp: str
    current_date: str
    current_price: float
    current_volume: int
    
    # 현재 기술적 지표
    current_ma_5: float
    current_ma_20: float
    current_ma_60: float
    current_bb_upper: float
    current_bb_middle: float
    current_bb_lower: float
    current_rsi: float
    
    # 5일 예측 결과
    predicted_prices: List[float]  # 5일간 종가 예측
    predicted_bb_upper: List[float]  # 5일간 볼린저 밴드 상한
    predicted_bb_lower: List[float]  # 5일간 볼린저 밴드 하한
    predicted_dates: List[str]  # 예측 날짜들
    
    # 신호 및 분석
    signal_strength: float  # 0-1 사이의 신호 강도
    trend_direction: str  # "up", "down", "sideways"
    volatility_level: str  # "low", "medium", "high"
    
    # 메타데이터
    confidence_score: float
    model_version: str
    data_quality_score: float

class InferencePipeline:
    def __init__(self, 
                 model_path: str = None,
                 preprocessor_path: str = None):
        """
        추론 파이프라인 초기화
        
        Args:
            model_path: 학습된 모델 경로 (None시 환경에 따라 자동 설정)
            preprocessor_path: 전처리기 경로 (None시 환경에 따라 자동 설정)
        """
        # 경로 자동 설정 (RunPod 환경 고려)
        if model_path is None or preprocessor_path is None:
            auto_model_path, auto_preprocessor_path = get_model_paths()
            self.model_path = model_path or auto_model_path
            self.preprocessor_path = preprocessor_path or auto_preprocessor_path
        else:
            self.model_path = model_path
            self.preprocessor_path = preprocessor_path
        self.logger = logging.getLogger(__name__)
        
        # 컴포넌트 초기화
        self.model = None
        self.preprocessor = None
        self.data_collector = StockDataCollector()
        
        # 모델 버전 정보
        self.model_version = "v1.0.0"
        
        # 로드
        self.load_components()
    
    def load_components(self):
        """모델과 전처리기 로드"""
        try:
            # 🚀 PyTorch 모델 로드
            if os.path.exists(self.model_path):
                self.model = PyTorchStockLSTM(
                    sequence_length=60,
                    prediction_length=5,
                    num_features=18,
                    num_targets=3
                )
                self.model.load_model(self.model_path, hidden_size=512)  # 🔥 RTX 4090 최적화
                self.logger.info("🚀 PyTorch model loaded successfully")
            else:
                raise FileNotFoundError(f"Model file not found: {self.model_path}")
            
            # 전처리기 로드
            if os.path.exists(self.preprocessor_path):
                with open(self.preprocessor_path, 'rb') as f:
                    self.preprocessor = pickle.load(f)
                self.logger.info("Preprocessor loaded successfully")
            else:
                raise FileNotFoundError(f"Preprocessor file not found: {self.preprocessor_path}")
                
        except Exception as e:
            self.logger.error(f"Error loading components: {str(e)}")
            raise
    
    def collect_stock_data(self, symbol: str, days: int = 60) -> Optional[pd.DataFrame]:
        """
        종목 데이터 수집
        
        Args:
            symbol: 주식 심볼
            days: 수집할 일수
            
        Returns:
            수집된 데이터프레임
        """
        try:
            data = self.data_collector.get_recent_data(symbol, days)
            if data is None or len(data) < days:
                self.logger.warning(f"Insufficient data for {symbol}: got {len(data) if data is not None else 0} days, need {days}")
                return None
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error collecting data for {symbol}: {str(e)}")
            return None
    
    def calculate_data_quality_score(self, data: pd.DataFrame) -> float:
        """
        데이터 품질 점수 계산
        
        Args:
            data: 주식 데이터프레임
            
        Returns:
            품질 점수 (0-1)
        """
        quality_score = 1.0
        
        # 결측값 확인
        missing_ratio = data.isnull().sum().sum() / (len(data) * len(data.columns))
        quality_score *= (1 - missing_ratio)
        
        # 데이터 길이 확인
        expected_length = 60
        length_ratio = min(len(data) / expected_length, 1.0)
        quality_score *= length_ratio
        
        # 가격 데이터의 일관성 확인
        price_consistency = 1.0
        if 'High' in data.columns and 'Low' in data.columns and 'Close' in data.columns:
            # High >= Low, High >= Close, Low <= Close 확인
            inconsistent_count = ((data['High'] < data['Low']) | 
                                (data['High'] < data['Close']) | 
                                (data['Low'] > data['Close'])).sum()
            price_consistency = 1 - (inconsistent_count / len(data))
        
        quality_score *= price_consistency
        
        return max(0.0, min(1.0, quality_score))
    
    
    def calculate_volatility_level(self, data: pd.DataFrame) -> str:
        """
        변동성 수준 계산
        
        Args:
            data: 주식 데이터프레임
            
        Returns:
            변동성 수준 ("low", "medium", "high")
        """
        if 'Volatility' in data.columns:
            current_volatility = data['Volatility'].iloc[-1]
            volatility_percentile = data['Volatility'].rank(pct=True).iloc[-1]
            
            if volatility_percentile < 0.33:
                return "low"
            elif volatility_percentile < 0.67:
                return "medium"
            else:
                return "high"
        
        # Volatility 컬럼이 없는 경우 가격 변동률로 계산
        price_changes = data['Close'].pct_change().abs()
        avg_volatility = price_changes.mean()
        
        if avg_volatility < 0.02:  # 2% 미만
            return "low"
        elif avg_volatility < 0.04:  # 4% 미만
            return "medium"
        else:
            return "high"
    
    def run_inference(self, symbol: str, days: int = 60) -> Optional[PredictionOutput]:
        """
        단일 종목에 대한 추론 실행
        
        Args:
            symbol: 주식 심볼
            days: 사용할 과거 데이터 일수
            
        Returns:
            예측 결과
        """
        try:
            self.logger.info(f"Running inference for {symbol}")
            
            # 1. 데이터 수집
            raw_data = self.collect_stock_data(symbol, days)
            if raw_data is None:
                return None
            
            # 2. 데이터 품질 점수 계산
            data_quality_score = self.calculate_data_quality_score(raw_data)
            
            # 3. 전처리
            processed_data = self.preprocessor.preprocess_data(raw_data)
            
            # 4. 추론용 시퀀스 생성
            input_sequence = self.preprocessor.preprocess_for_inference(processed_data)
            
            # 5. 모델 추론
            predictions = self.model.predict(input_sequence)
            
         
            
            # 7. 변동성 수준 계산
            volatility_level = self.calculate_volatility_level(processed_data)
            
            # 8. 현재 데이터 추출
            current_row = processed_data.iloc[-1]
            
            # 9. 예측 날짜 생성
            base_date = datetime.now()
            predicted_dates = [(base_date + timedelta(days=i+1)).strftime("%Y-%m-%d") for i in range(5)]
            
            # 10. 신뢰도 점수 계산 (데이터 품질과 모델 성능 기반)
            confidence_score = data_quality_score * 0.8  # 기본 신뢰도
            
            # 11. 결과 객체 생성
            result = PredictionOutput(
                symbol=symbol,
                prediction_timestamp=datetime.now().isoformat(),
                current_date=base_date.strftime("%Y-%m-%d"),
                current_price=float(current_row['Close']),
                current_volume=int(current_row['Volume']),
                
                # 현재 기술적 지표
                current_ma_5=float(current_row.get('MA_5', 0)),
                current_ma_20=float(current_row.get('MA_20', 0)),
                current_ma_60=float(current_row.get('MA_60', 0)),
                current_bb_upper=float(current_row.get('BB_Upper', 0)),
                current_bb_middle=float(current_row.get('BB_Middle', 0)),
                current_bb_lower=float(current_row.get('BB_Lower', 0)),
                current_rsi=float(current_row.get('RSI', 50)),
                
                # 5일 예측 결과
                predicted_prices=predictions[0, :, 0].tolist(),
                predicted_bb_upper=predictions[0, :, 1].tolist(),
                predicted_bb_lower=predictions[0, :, 2].tolist(),
                predicted_dates=predicted_dates,
                
                # 메타데이터
                confidence_score=float(confidence_score),
                model_version=self.model_version,
                data_quality_score=float(data_quality_score)
            )
            
            
        except Exception as e:
            self.logger.error(f"Error during inference for {symbol}: {str(e)}")
            return None
    
    def run_batch_inference(self, symbols: List[str], days: int = 60, max_workers: int = 5) -> List[PredictionOutput]:
        """
        여러 종목에 대한 배치 추론 실행
        
        Args:
            symbols: 주식 심볼 리스트
            days: 사용할 과거 데이터 일수
            max_workers: 병렬 처리 워커 수
            
        Returns:
            예측 결과 리스트
        """
        self.logger.info(f"Running batch inference for {len(symbols)} symbols")
        
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 작업 제출
            future_to_symbol = {
                executor.submit(self.run_inference, symbol, days): symbol 
                for symbol in symbols
            }
            
            # 결과 수집
            from concurrent.futures import as_completed
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    result = future.result()
                    if result is not None:
                        results.append(result)
                except Exception as e:
                    self.logger.error(f"Error in batch inference for {symbol}: {str(e)}")
        
        self.logger.info(f"Batch inference completed: {len(results)}/{len(symbols)} successful")
        return results
    
    def save_results_to_json(self, results: List[PredictionOutput], filepath: str):
        """예측 결과를 JSON 파일로 저장"""
        try:
            results_dict = [asdict(result) for result in results]
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results_dict, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Results saved to {filepath}")
        except Exception as e:
            self.logger.error(f"Error saving results: {str(e)}")


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Stock Inference Pipeline")
    parser.add_argument("--symbols", nargs="+", required=True, help="Stock symbols to predict")
    parser.add_argument("--days", type=int, default=60, help="Days of historical data to use")
    parser.add_argument("--output", default="predictions.json", help="Output JSON file")
    parser.add_argument("--batch-size", type=int, default=5, help="Batch size for parallel processing")
    
    args = parser.parse_args()
    
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    
    # 추론 파이프라인 실행
    pipeline = InferencePipeline()
    
    if len(args.symbols) == 1:
        # 단일 추론
        result = pipeline.run_inference(args.symbols[0], args.days)
        if result:
            pipeline.save_results_to_json([result], args.output)
            print(f"Prediction completed for {args.symbols[0]}")
        else:
            print(f"Failed to generate prediction for {args.symbols[0]}")
    else:
        # 배치 추론
        results = pipeline.run_batch_inference(args.symbols, args.days, args.batch_size)
        if results:
            pipeline.save_results_to_json(results, args.output)
            print(f"Batch prediction completed: {len(results)}/{len(args.symbols)} successful")
            
            # 신호 요약

        else:
            print("No successful predictions")


if __name__ == "__main__":
    main()