from typing import Optional, List, Dict, Any
from service.net.protocol_base import BaseRequest, BaseResponse
from .model_model import PredictionResult, ModelInfo

class PredictRequest(BaseRequest):
    """단일 예측 요청"""
    symbol: str
    data_points: List[float]
    period: int = 30
    model_type: str = "lstm"

class PredictResponse(BaseResponse):
    """단일 예측 응답"""  
    result: Optional[PredictionResult] = None

class BatchPredictRequest(BaseRequest):
    """배치 예측 요청"""
    symbols: List[str]
    data_points_list: List[List[float]]
    period: int = 30
    model_type: str = "lstm"

class BatchPredictResponse(BaseResponse):
    """배치 예측 응답"""
    results: List[PredictionResult] = []
    batch_id: str = ""
    processed_count: int = 0
    success_count: int = 0

class ModelsListRequest(BaseRequest):
    """모델 목록 요청"""
    pass

class ModelsListResponse(BaseResponse):
    """모델 목록 응답"""
    models: List[ModelInfo] = []