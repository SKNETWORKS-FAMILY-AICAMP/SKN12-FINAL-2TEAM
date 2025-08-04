"""
FastAPI 기반 주식 예측 API 서버
배치 추론 및 실시간 예측 서비스 제공
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import uvicorn
import asyncio
import logging
import os
import pickle
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
from contextlib import asynccontextmanager

# 프로젝트 모듈 import
from data_collector import StockDataCollector
from data_preprocessor import StockDataPreprocessor
from pytorch_lstm_model import PyTorchStockLSTM
from config import get_model_paths

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 전역 변수
model = None
preprocessor = None
data_collector = None

class PredictionRequest(BaseModel):
    """단일 예측 요청"""
    symbol: str = Field(..., description="주식 심볼 (예: AAPL)")
    days: int = Field(60, description="사용할 과거 데이터 일수")

class BatchPredictionRequest(BaseModel):
    """배치 예측 요청"""
    symbols: List[str] = Field(..., description="주식 심볼 리스트")
    days: int = Field(60, description="사용할 과거 데이터 일수")
    batch_size: int = Field(5, description="배치 크기")

class PredictionResult(BaseModel):
    """예측 결과"""
    symbol: str
    prediction_date: str
    current_price: float
    predictions: List[Dict[str, Any]]  # 5일간의 예측 결과
    bollinger_bands: List[Dict[str, float]]  # 5일간의 볼린저 밴드
    confidence_score: float
    status: str

class BatchPredictionResult(BaseModel):
    """배치 예측 결과"""
    request_id: str
    total_symbols: int
    completed_symbols: int
    failed_symbols: int
    results: List[PredictionResult]
    processing_time: float
    status: str

class HealthResponse(BaseModel):
    """헬스 체크 응답"""
    status: str
    model_loaded: bool
    gpu_available: bool
    timestamp: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 실행되는 컨텍스트 매니저"""
    # 시작 시 모델 로드
    await load_model_and_preprocessor()
    yield
    # 종료 시 정리 작업 (필요한 경우)
    logger.info("Shutting down API server...")

# FastAPI 앱 생성
app = FastAPI(
    title="Stock Prediction API",
    description="LSTM 기반 주식 가격 및 볼린저 밴드 예측 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def load_model_and_preprocessor():
    """모델과 전처리기 로드"""
    global model, preprocessor, data_collector
    
    try:
        logger.info("Loading model and preprocessor...")
        
        # 🚀 PyTorch 모델 로드 (환경별 경로 자동 감지)
        model_path, preprocessor_path = get_model_paths()
        
        if os.path.exists(model_path):
            # PyTorch 모델 초기화 후 로드
            model = PyTorchStockLSTM(
                sequence_length=60,
                prediction_length=5,
                num_features=18,
                num_targets=3
            )
            model.load_model(model_path, hidden_size=512)  # 🔥 RTX 4090 최적화
            logger.info(f"🚀 PyTorch model loaded from: {model_path}")
        else:
            logger.warning(f"Model file not found: {model_path}")
            model = None
        
        # 전처리기 로드
        if os.path.exists(preprocessor_path):
            with open(preprocessor_path, 'rb') as f:
                preprocessor = pickle.load(f)
            logger.info("Preprocessor loaded successfully")
        else:
            logger.warning(f"Preprocessor file not found: {preprocessor_path}")
            preprocessor = StockDataPreprocessor()
        
        # 데이터 수집기 초기화
        data_collector = StockDataCollector()
        
        logger.info("All components loaded successfully")
        
    except Exception as e:
        logger.error(f"Error loading model/preprocessor: {str(e)}")
        model = None
        preprocessor = None

def format_prediction_result(symbol: str, 
                           current_data: pd.DataFrame,
                           predictions: np.ndarray,
                           confidence: float = 0.8) -> PredictionResult:
    """예측 결과를 API 응답 형식으로 변환"""
    
    current_price = float(current_data['Close'].iloc[-1])
    prediction_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 5일간의 예측 결과 포맷팅
    prediction_list = []
    bollinger_list = []
    
    for i in range(5):
        day_prediction = {
            "day": i + 1,
            "date": (datetime.now() + timedelta(days=i+1)).strftime("%Y-%m-%d"),
            "predicted_close": float(predictions[0, i, 0]),  # Close 예측
            "trend": "up" if predictions[0, i, 0] > current_price else "down"
        }
        prediction_list.append(day_prediction)
        
        bollinger_band = {
            "day": i + 1,
            "date": (datetime.now() + timedelta(days=i+1)).strftime("%Y-%m-%d"),
            "bb_upper": float(predictions[0, i, 1]),  # BB_Upper 예측
            "bb_lower": float(predictions[0, i, 2]),  # BB_Lower 예측
            "bb_middle": (float(predictions[0, i, 1]) + float(predictions[0, i, 2])) / 2
        }
        bollinger_list.append(bollinger_band)
    
    return PredictionResult(
        symbol=symbol,
        prediction_date=prediction_date,
        current_price=current_price,
        predictions=prediction_list,
        bollinger_bands=bollinger_list,
        confidence_score=confidence,
        status="success"
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스 체크 엔드포인트"""
    import tensorflow as tf
    
    gpu_available = len(tf.config.experimental.list_physical_devices('GPU')) > 0
    
    return HealthResponse(
        status="healthy",
        model_loaded=model is not None,
        gpu_available=gpu_available,
        timestamp=datetime.now().isoformat()
    )

@app.post("/predict", response_model=PredictionResult)
async def predict_single_stock(request: PredictionRequest):
    """단일 종목 예측"""
    if model is None or preprocessor is None:
        raise HTTPException(status_code=503, detail="Model or preprocessor not loaded")
    
    try:
        logger.info(f"Processing prediction request for {request.symbol}")
        
        # 최근 데이터 수집
        recent_data = data_collector.get_recent_data(request.symbol, request.days)
        if recent_data is None or len(recent_data) < request.days:
            raise HTTPException(
                status_code=404, 
                detail=f"Insufficient data for symbol {request.symbol}"
            )
        
        # 전처리 및 추론
        input_sequence = preprocessor.preprocess_for_inference(recent_data)
        predictions = model.predict(input_sequence)
        
        # 결과 포맷팅
        result = format_prediction_result(request.symbol, recent_data, predictions)
        
        logger.info(f"Prediction completed for {request.symbol}")
        return result
        
    except Exception as e:
        logger.error(f"Error predicting {request.symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/batch", response_model=BatchPredictionResult)
async def predict_batch_stocks(request: BatchPredictionRequest):
    """배치 주식 예측"""
    if model is None or preprocessor is None:
        raise HTTPException(status_code=503, detail="Model or preprocessor not loaded")
    
    request_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    start_time = datetime.now()
    
    logger.info(f"Processing batch prediction request {request_id} for {len(request.symbols)} symbols")
    
    results = []
    completed = 0
    failed = 0
    
    # 배치 크기만큼 처리
    for i in range(0, len(request.symbols), request.batch_size):
        batch_symbols = request.symbols[i:i + request.batch_size]
        
        # 병렬 처리를 위한 태스크 생성
        tasks = []
        for symbol in batch_symbols:
            task = asyncio.create_task(predict_single_symbol(symbol, request.days))
            tasks.append(task)
        
        # 배치 실행
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for symbol, result in zip(batch_symbols, batch_results):
            if isinstance(result, Exception):
                logger.error(f"Failed to predict {symbol}: {str(result)}")
                failed += 1
                # 실패한 경우에도 결과에 포함
                error_result = PredictionResult(
                    symbol=symbol,
                    prediction_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    current_price=0.0,
                    predictions=[],
                    bollinger_bands=[],
                    confidence_score=0.0,
                    status=f"failed: {str(result)}"
                )
                results.append(error_result)
            else:
                results.append(result)
                completed += 1
        
        # 배치 간 잠시 대기 (API 제한 방지)
        if i + request.batch_size < len(request.symbols):
            await asyncio.sleep(0.1)
    
    processing_time = (datetime.now() - start_time).total_seconds()
    
    logger.info(f"Batch prediction {request_id} completed: {completed} success, {failed} failed")
    
    return BatchPredictionResult(
        request_id=request_id,
        total_symbols=len(request.symbols),
        completed_symbols=completed,
        failed_symbols=failed,
        results=results,
        processing_time=processing_time,
        status="completed"
    )

async def predict_single_symbol(symbol: str, days: int) -> PredictionResult:
    """단일 심볼 예측 (내부 함수)"""
    try:
        # 최근 데이터 수집
        recent_data = data_collector.get_recent_data(symbol, days)
        if recent_data is None or len(recent_data) < days:
            raise ValueError(f"Insufficient data for symbol {symbol}")
        
        # 전처리 및 추론
        input_sequence = preprocessor.preprocess_for_inference(recent_data)
        predictions = model.predict(input_sequence)
        
        # 결과 포맷팅
        result = format_prediction_result(symbol, recent_data, predictions)
        return result
        
    except Exception as e:
        raise Exception(f"Error predicting {symbol}: {str(e)}")

@app.get("/models/info")
async def get_model_info():
    """모델 정보 조회"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        model_info = {
            "model_type": "LSTM with Attention",
            "sequence_length": 60,
            "prediction_length": 5,
            "features": [
                "Open", "High", "Low", "Close", "Volume",
                "MA_5", "MA_20", "MA_60",
                "BB_Upper", "BB_Middle", "BB_Lower", "BB_Percent", "BB_Width",
                "RSI", "MACD", "MACD_Signal", "Price_Change", "Volatility"
            ],
            "targets": ["Close", "BB_Upper", "BB_Lower"],
            "model_parameters": model.model.count_params() if model.model else 0
        }
        return model_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Stock Prediction API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "single_prediction": "/predict",
            "batch_prediction": "/predict/batch",
            "model_info": "/models/info"
        }
    }

if __name__ == "__main__":
    # 개발 환경에서 실행
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )