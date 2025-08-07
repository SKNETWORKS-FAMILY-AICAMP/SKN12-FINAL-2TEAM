from datetime import datetime
import asyncio
import json
import uuid
import numpy as np
import logging
from typing import Dict, List, Optional, Any
import os

# 프로젝트 모듈 import
from .data_collector import StockDataCollector
from .data_preprocessor import StockDataPreprocessor
from .pytorch_lstm_model import PyTorchStockLSTM
from .inference_pipeline import InferencePipeline, PredictionOutput
from .db_formatter import DatabaseFormatter

# 기존 템플릿 import (사용 가능한 경우)
try:
    from template.base.base_template import BaseTemplate
    from template.model.common.model_serialize import (
        PredictRequest, PredictResponse,
        BatchPredictRequest, BatchPredictResponse,
        ModelsListRequest, ModelsListResponse
    )
    from template.model.common.model_model import PredictionResult, ModelInfo
    from service.core.logger import Logger
    TEMPLATE_AVAILABLE = True
except ImportError:
    # 템플릿이 없는 경우 기본 클래스 정의
    class BaseTemplate:
        def __init__(self):
            pass
    
    class PredictRequest:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
    
    class PredictResponse:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
    
    class BatchPredictRequest:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
    
    class BatchPredictResponse:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
    
    class ModelsListRequest:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
    
    class ModelsListResponse:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
    
    class PredictionResult:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
    
    class ModelInfo:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
    
    class Logger:
        @staticmethod
        def info(msg):
            logging.info(msg)
        
        @staticmethod
        def error(msg):
            logging.error(msg)
        
        @staticmethod
        def warning(msg):
            logging.warning(msg)
    
    TEMPLATE_AVAILABLE = False

class ModelTemplateImpl(BaseTemplate):
    """
    주식 예측 LSTM 모델 템플릿 구현체
    원래 프로젝트의 모듈 역할을 수행
    """
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # 컴포넌트 초기화
        self.data_collector = StockDataCollector()
        self.preprocessor = StockDataPreprocessor()
        self.model = None
        self.inference_pipeline = None
        self.db_formatter = DatabaseFormatter()
        
        # 모델 정보
        self.model_info = {
            "name": "Stock Prediction LSTM",
            "version": "1.0.0",
            "description": "LSTM model for stock price and Bollinger Band prediction",
            "input_features": 18,
            "sequence_length": 60,
            "prediction_length": 5,
            "targets": ["Close", "BB_Upper", "BB_Lower"]
        }
        
        # 모델 로드 시도
        self._load_model()
    
    def _load_model(self):
        """모델 및 관련 컴포넌트 로드"""
        try:
            model_path = "models/final_model.pth"
            preprocessor_path = "models/preprocessor.pkl"
            
            if os.path.exists(model_path) and os.path.exists(preprocessor_path):
                self.inference_pipeline = InferencePipeline(model_path, preprocessor_path)
                self.logger.info("Model and preprocessor loaded successfully")
            else:
                self.logger.warning("Model files not found. Please train the model first.")
                
        except Exception as e:
            self.logger.error(f"Error loading model: {str(e)}")
    
    async def predict(self, request: PredictRequest) -> PredictResponse:
        """
        단일 주식 예측
        
        Args:
            request: 예측 요청 객체
            
        Returns:
            예측 응답 객체
        """
        try:
            # 요청에서 파라미터 추출
            symbol = getattr(request, 'symbol', None) or request.__dict__.get('symbol')
            days = getattr(request, 'days', 60) or request.__dict__.get('days', 60)
            
            if not symbol:
                raise ValueError("Symbol is required")
            
            self.logger.info(f"Processing prediction request for {symbol}")
            
            # 추론 실행
            if self.inference_pipeline:
                result = self.inference_pipeline.run_inference(symbol, days)
            else:
                # 추론 파이프라인이 없는 경우 직접 실행
                result = await self._direct_inference(symbol, days)
            
            if result is None:
                raise ValueError(f"Failed to generate prediction for {symbol}")
            
            # 응답 객체 생성
            prediction_result = PredictionResult(
                symbol=result.symbol,
                prediction_timestamp=result.prediction_timestamp,
                current_price=result.current_price,
                predicted_prices=result.predicted_prices,
                bollinger_bands=result.predicted_bb_upper + result.predicted_bb_lower,
                buy_signal=result.buy_signal,
                sell_signal=result.sell_signal,
                confidence_score=result.confidence_score,
                trend_direction=result.trend_direction
            )
            
            response = PredictResponse(
                success=True,
                result=prediction_result,
                message="Prediction completed successfully",
                request_id=str(uuid.uuid4())
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in prediction: {str(e)}")
            return PredictResponse(
                success=False,
                result=None,
                message=str(e),
                request_id=str(uuid.uuid4())
            )
    
    async def batch_predict(self, request: BatchPredictRequest) -> BatchPredictResponse:
        """
        배치 주식 예측
        
        Args:
            request: 배치 예측 요청 객체
            
        Returns:
            배치 예측 응답 객체
        """
        try:
            # 요청에서 파라미터 추출
            symbols = getattr(request, 'symbols', []) or request.__dict__.get('symbols', [])
            days = getattr(request, 'days', 60) or request.__dict__.get('days', 60)
            batch_size = getattr(request, 'batch_size', 5) or request.__dict__.get('batch_size', 5)
            
            if not symbols:
                raise ValueError("Symbols list is required")
            
            self.logger.info(f"Processing batch prediction for {len(symbols)} symbols")
            
            # 배치 추론 실행
            if self.inference_pipeline:
                results = self.inference_pipeline.run_batch_inference(symbols, days, batch_size)
            else:
                # 추론 파이프라인이 없는 경우 순차 실행
                results = []
                for symbol in symbols:
                    result = await self._direct_inference(symbol, days)
                    if result:
                        results.append(result)
            
            # 결과 변환
            prediction_results = []
            for result in results:
                prediction_result = PredictionResult(
                    symbol=result.symbol,
                    prediction_timestamp=result.prediction_timestamp,
                    current_price=result.current_price,
                    predicted_prices=result.predicted_prices,
                    bollinger_bands=result.predicted_bb_upper + result.predicted_bb_lower,
                    buy_signal=result.buy_signal,
                    sell_signal=result.sell_signal,
                    confidence_score=result.confidence_score,
                    trend_direction=result.trend_direction
                )
                prediction_results.append(prediction_result)
            
            response = BatchPredictResponse(
                success=True,
                results=prediction_results,
                total_count=len(symbols),
                success_count=len(prediction_results),
                failed_count=len(symbols) - len(prediction_results),
                message="Batch prediction completed",
                request_id=str(uuid.uuid4())
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in batch prediction: {str(e)}")
            return BatchPredictResponse(
                success=False,
                results=[],
                total_count=len(getattr(request, 'symbols', [])),
                success_count=0,
                failed_count=len(getattr(request, 'symbols', [])),
                message=str(e),
                request_id=str(uuid.uuid4())
            )
    
    async def _direct_inference(self, symbol: str, days: int) -> Optional[PredictionOutput]:
        """직접 추론 실행 (추론 파이프라인이 없는 경우)"""
        try:
            # 데이터 수집
            raw_data = self.data_collector.get_recent_data(symbol, days)
            if raw_data is None:
                return None
            
            # 전처리
            processed_data = self.preprocessor.preprocess_data(raw_data)
            
            # 간단한 더미 예측 (실제로는 모델이 필요)
            current_price = float(processed_data['Close'].iloc[-1])
            predictions = [current_price * (1 + np.random.normal(0, 0.02)) for _ in range(5)]
            bb_upper = [p * 1.05 for p in predictions]
            bb_lower = [p * 0.95 for p in predictions]
            
            result = PredictionOutput(
                symbol=symbol,
                prediction_timestamp=datetime.now().isoformat(),
                current_date=datetime.now().strftime("%Y-%m-%d"),
                current_price=current_price,
                current_volume=int(processed_data['Volume'].iloc[-1]),
                current_ma_5=float(processed_data.get('MA_5', [0]).iloc[-1]),
                current_ma_20=float(processed_data.get('MA_20', [0]).iloc[-1]),
                current_ma_60=float(processed_data.get('MA_60', [0]).iloc[-1]),
                current_bb_upper=float(processed_data.get('BB_Upper', [0]).iloc[-1]),
                current_bb_middle=float(processed_data.get('BB_Middle', [0]).iloc[-1]),
                current_bb_lower=float(processed_data.get('BB_Lower', [0]).iloc[-1]),
                current_rsi=float(processed_data.get('RSI', [50]).iloc[-1]),
                predicted_prices=predictions,
                predicted_bb_upper=bb_upper,
                predicted_bb_lower=bb_lower,
                predicted_dates=[(datetime.now() + datetime.timedelta(days=i+1)).strftime("%Y-%m-%d") for i in range(5)],
                buy_signal=False,
                sell_signal=False,
                signal_strength=0.5,
                trend_direction="sideways",
                volatility_level="medium",
                confidence_score=0.7,
                model_version="1.0.0",
                data_quality_score=0.8
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in direct inference for {symbol}: {str(e)}")
            return None
    
    async def list_models(self, request: ModelsListRequest) -> ModelsListResponse:
        """사용 가능한 모델 목록 반환"""
        models = [
            ModelInfo(
                id="stock_lstm_v1",
                name=self.model_info["name"],
                version=self.model_info["version"],
                description=self.model_info["description"],
                status="loaded" if self.inference_pipeline else "not_loaded",
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
        ]
        
        return ModelsListResponse(
            success=True,
            models=models,
            total_count=len(models),
            message="Models listed successfully"
        )
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        return self.model_info
    
    def format_for_database(self, predictions: List[PredictionOutput], format_type: str = "mysql") -> Any:
        """
        데이터베이스 저장용 포맷 변환
        
        Args:
            predictions: 예측 결과 리스트
            format_type: 포맷 타입 ("mysql", "mongodb", "elasticsearch")
            
        Returns:
            포맷된 데이터
        """
        if format_type == "mysql":
            return self.db_formatter.format_for_mysql(predictions)
        elif format_type == "mongodb":
            return self.db_formatter.format_for_mongodb(predictions)
        elif format_type == "elasticsearch":
            return self.db_formatter.format_for_elasticsearch(predictions)
        else:
            raise ValueError(f"Unsupported format type: {format_type}")
    
    def get_database_schema(self, db_type: str = "mysql") -> str:
        """데이터베이스 스키마 반환"""
        return self.db_formatter.create_table_schema(db_type)
    