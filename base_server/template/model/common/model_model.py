from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel

class PredictionResult(BaseModel):
    """예측 결과 모델"""
    symbol: str
    signal: str  # BUY, SELL, HOLD
    confidence: float
    predicted_price: float
    current_price: float
    change_percent: float
    timestamp: datetime
    model_info: Dict[str, Any] = {}

class ModelInfo(BaseModel):
    """모델 정보"""
    model_type: str
    version: str
    description: str
    supported_features: List[str] = []
    performance_metrics: Dict[str, float] = {}