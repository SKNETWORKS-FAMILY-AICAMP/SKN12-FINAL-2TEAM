from typing import Optional, List, Dict, Any
from pydantic import Field
from .protocol_base import BaseRequest, BaseResponse
from .model_model import PredictionResult, ModelInfo

class PredictRequest(BaseRequest):
    """단일 예측 요청"""
    symbol: str = Field(..., description="주식 심볼 (예: AAPL)")
    days: int = Field(60, description="사용할 과거 데이터 일수")
    model_type: str = Field("lstm", description="모델 타입")

class PredictResponse(BaseResponse):
    """단일 예측 응답"""  
    result: Optional[PredictionResult] = Field(None, description="예측 결과")

class BatchPredictRequest(BaseRequest):
    """배치 예측 요청"""
    symbols: List[str] = Field(..., description="주식 심볼 리스트")
    days: int = Field(60, description="사용할 과거 데이터 일수")
    model_type: str = Field("lstm", description="모델 타입")

class BatchPredictResponse(BaseResponse):
    """배치 예측 응답"""
    results: List[PredictionResult] = Field([], description="배치 예측 결과 리스트")
    batch_id: str = Field("", description="배치 ID")
    processed_count: int = Field(0, description="처리된 종목 수")
    success_count: int = Field(0, description="성공한 종목 수")

class ModelsListRequest(BaseRequest):
    """모델 목록 요청"""
    pass

class ModelsListResponse(BaseResponse):
    """모델 목록 응답"""
    models: List[ModelInfo] = Field([], description="사용 가능한 모델 리스트")