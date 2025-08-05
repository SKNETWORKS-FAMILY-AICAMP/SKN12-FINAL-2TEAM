from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel

class DailyPrediction(BaseModel):
    """일별 예측 데이터"""
    day: int
    date: str
    predicted_close: float
    trend: str  # up, down

class BollingerBand(BaseModel):
    """볼린저 밴드 데이터"""
    day: int
    date: str
    bb_upper: float
    bb_lower: float
    bb_middle: Optional[float] = None

class PredictionResult(BaseModel):
    """예측 결과 모델 (5일간 상세 예측)"""
    symbol: str
    prediction_date: str
    current_price: float
    predictions: List[DailyPrediction]
    bollinger_bands: List[BollingerBand]
    confidence_score: float
    status: str = "success"

class ModelInfo(BaseModel):
    """모델 정보"""
    model_type: str
    version: str
    description: str
    supported_features: List[str] = []
    performance_metrics: Dict[str, float] = {}