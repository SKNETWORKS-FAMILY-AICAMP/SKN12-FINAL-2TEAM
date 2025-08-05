from typing import Optional, List
from .protocol_base import BaseRequest, BaseResponse
from .model_model import PredictionResult, ModelInfo

# ============================================================================
# 모델 예측 요청/응답 (팀 표준 BaseRequest/BaseResponse 기반)
# ============================================================================

class PredictRequest(BaseRequest):
    """단일 예측 요청"""
    symbol: str
    days: int = 60
    model_type: str = "lstm"

class PredictResponse(BaseResponse):
    """단일 예측 응답"""  
    result: Optional[PredictionResult] = None
    message: str = ""

class BatchPredictRequest(BaseRequest):
    """배치 예측 요청"""
    symbols: List[str]
    days: int = 60
    model_type: str = "lstm"

class BatchPredictResponse(BaseResponse):
    """배치 예측 응답"""
    results: List[PredictionResult] = []
    batch_id: str = ""
    processed_count: int = 0
    success_count: int = 0
    message: str = ""

class ModelsListRequest(BaseRequest):
    """모델 목록 요청"""
    pass

class ModelsListResponse(BaseResponse):
    """모델 목록 응답"""
    models: List[ModelInfo] = []
    message: str = ""