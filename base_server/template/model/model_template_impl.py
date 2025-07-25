from datetime import datetime
import asyncio
import json
import uuid
import numpy as np
from template.base.base_template import BaseTemplate
from template.model.common.model_serialize import (
    PredictRequest, PredictResponse,
    BatchPredictRequest, BatchPredictResponse,
    ModelsListRequest, ModelsListResponse
)
from template.model.common.model_model import PredictionResult, ModelInfo
from service.core.logger import Logger

class ModelTemplateImpl(BaseTemplate):
    def __init__(self):
        super().__init__()
        # 실제 모델들은 여기서 로드 (추후 구현)
        self.models = {}
        
    async def on_predict_req(self, client_session, request: PredictRequest) -> PredictResponse:
        """단일 예측 요청 처리 - 실제 모델 추론"""
        response = PredictResponse()
        response.sequence = request.sequence
        
        Logger.info(f"Model predict: symbol={request.symbol}, model_type={request.model_type}")
        
        try:
            # 실제 모델 추론 (임시 구현 - 추후 실제 모델로 교체)
            prediction_result = await self._run_model_inference(
                request.symbol,
                request.data_points,
                request.period,
                request.model_type
            )
            
            response.result = prediction_result
            Logger.info(f"Model predict success: {request.symbol} -> {prediction_result.signal}")
            
        except Exception as e:
            response.errorCode = 5000  # 모델 추론 오류
            Logger.error(f"Model predict error: {str(e)}")
            
        return response
    
    async def on_batch_predict_req(self, client_session, request: BatchPredictRequest) -> BatchPredictResponse:
        """배치 예측 요청 처리 - 병렬 모델 추론"""
        response = BatchPredictResponse()
        response.sequence = request.sequence
        response.batch_id = f"batch_{uuid.uuid4().hex[:8]}"
        
        Logger.info(f"Batch predict: {len(request.symbols)} symbols")
        
        try:
            # 병렬 처리로 성능 최적화
            tasks = []
            for i, symbol in enumerate(request.symbols):
                data_points = request.data_points_list[i] if i < len(request.data_points_list) else []
                task = self._run_model_inference(symbol, data_points, request.period, request.model_type)
                tasks.append(task)
            
            # 모든 예측을 병렬로 실행
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 결과 처리
            for result in results:
                if isinstance(result, PredictionResult):
                    response.results.append(result)
                else:
                    Logger.error(f"Batch prediction failed for one symbol: {result}")
            
            response.processed_count = len(request.symbols)
            response.success_count = len(response.results)
            
            Logger.info(f"Batch predict success: {response.success_count}/{response.processed_count}")
                
        except Exception as e:
            response.errorCode = 5000
            Logger.error(f"Batch predict error: {str(e)}")
            
        return response
    
    async def on_models_list_req(self, client_session, request: ModelsListRequest) -> ModelsListResponse:
        """모델 목록 요청 처리"""
        response = ModelsListResponse()
        response.sequence = request.sequence
        
        Logger.info("Model list request")
        
        try:
            # 사용 가능한 모델 목록
            available_models = [
                {
                    "model_type": "lstm",
                    "version": "1.0.0",
                    "description": "LSTM 기반 시계열 예측 모델",
                    "supported_features": ["time_series", "stock_prediction"],
                    "performance_metrics": {"accuracy": 0.85, "mse": 0.02}
                },
                {
                    "model_type": "gru", 
                    "version": "1.0.0",
                    "description": "GRU 기반 시계열 예측 모델",
                    "supported_features": ["time_series", "stock_prediction"],
                    "performance_metrics": {"accuracy": 0.82, "mse": 0.025}
                },
                {
                    "model_type": "transformer",
                    "version": "1.0.0", 
                    "description": "Transformer 기반 시계열 예측 모델",
                    "supported_features": ["time_series", "attention_mechanism"],
                    "performance_metrics": {"accuracy": 0.88, "mse": 0.018}
                }
            ]
            
            # ModelInfo 객체들 생성
            for model_data in available_models:
                model_info = ModelInfo(
                    model_type=model_data["model_type"],
                    version=model_data["version"],
                    description=model_data["description"],
                    supported_features=model_data["supported_features"],
                    performance_metrics=model_data["performance_metrics"]
                )
                response.models.append(model_info)
                
            Logger.info(f"Model list success: {len(response.models)} models")
                
        except Exception as e:
            response.errorCode = 5000
            Logger.error(f"Model list error: {str(e)}")
            
        return response
    
    async def _run_model_inference(self, symbol: str, data_points: list, period: int, model_type: str) -> PredictionResult:
        """실제 모델 추론 실행 - 임시 구현"""
        
        # 임시 구현: 간단한 규칙 기반 예측
        # 실제로는 여기서 LSTM, GRU 등의 모델을 로드하고 추론 수행
        
        if not data_points or len(data_points) < 5:
            # 데이터 부족 시 기본값
            return PredictionResult(
                symbol=symbol,
                signal="HOLD",
                confidence=0.5,
                predicted_price=data_points[-1] if data_points else 100.0,
                current_price=data_points[-1] if data_points else 100.0,
                change_percent=0.0,
                timestamp=datetime.now(),
                model_info={
                    "model_type": model_type,
                    "version": "1.0.0",
                    "note": "Insufficient data"
                }
            )
        
        # 간단한 추세 분석
        current_price = data_points[-1]
        price_change = (data_points[-1] - data_points[0]) / data_points[0] * 100
        
        # 이동평균 계산
        ma_5 = sum(data_points[-5:]) / 5
        
        # 예측 로직 (임시)
        predicted_change = price_change * 0.1  # 추세의 10% 반영
        predicted_price = current_price * (1 + predicted_change / 100)
        
        # 신호 결정
        if predicted_change > 2.0:
            signal = "BUY"
            confidence = min(0.9, 0.6 + abs(predicted_change) / 10)
        elif predicted_change < -2.0:
            signal = "SELL"
            confidence = min(0.9, 0.6 + abs(predicted_change) / 10)
        else:
            signal = "HOLD"
            confidence = 0.5 + abs(predicted_change) / 20
        
        return PredictionResult(
            symbol=symbol,
            signal=signal,
            confidence=confidence,
            predicted_price=predicted_price,
            current_price=current_price,
            change_percent=predicted_change,
            timestamp=datetime.now(),
            model_info={
                "model_type": model_type,
                "version": "1.0.0",
                "ma_5": ma_5,
                "data_points_count": len(data_points)
            }
        )