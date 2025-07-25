#!/usr/bin/env python3
"""
Model Server - 시계열 모델 예측 마이크로서비스

base_web_server 패턴을 그대로 따라 구현
기존 service, template 인프라를 재사용
"""

import argparse
import asyncio
import json
import os
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 경로 설정 - base_server 루트 기준
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

from service.core.logger import Logger, ConsoleLogger
from service.core.argparse_util import parse_log_level, parse_app_env
from template.base.template_config import AppConfig

# Template import
from template.base.template_context import TemplateContext, TemplateType
from template.model.model_template_impl import ModelTemplateImpl
from template.base.template_service import TemplateService

# 라우터 import
from .routers import model


# 로그레벨, 환경 읽기
log_level = parse_log_level()
app_env = parse_app_env()

# 환경에 따라 config 파일명 결정 (base_web_server 패턴과 동일)
def get_config_filename():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    #if app_env == "LOCAL":
    #    filename = "model-server-config_local.json"
    #elif app_env == "DEBUG":
    #    filename = "model-server-config_debug.json"
    #else:
    filename = "model_server-config.json"
    
    return os.path.join(current_dir, filename)

config_file = get_config_filename()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리 - base_web_server 패턴 간소화"""
    
    # ConsoleLogger로 초기화
    console_logger = ConsoleLogger(log_level=log_level)
    Logger.init(console_logger)
    Logger.info(f"model_server 시작 (로그레벨: {log_level.name}, 환경: {app_env}, config: {config_file})")
    
    try:
        # Config 파일 로드
        with open(config_file, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        Logger.info(f"Config 파일 로드 성공: {config_file}")
        
        # AppConfig 객체 생성
        app_config = AppConfig(**config_data)
        
        # 필요한 서비스들 초기화 (base_web_server 패턴)
        # Redis 캐시 서비스 (세션 관리용)
        from service.cache.cache_service import CacheService
        from service.cache.redis_cache_client_pool import RedisCacheClientPool
        try:
            cache_client_pool = RedisCacheClientPool(
                host=app_config.cacheConfig.host,
                port=app_config.cacheConfig.port,
                session_expire_time=app_config.cacheConfig.session_expire_seconds,
                app_id=app_config.templateConfig.appId,
                env=app_config.templateConfig.env,
                db=app_config.cacheConfig.db,
                password=app_config.cacheConfig.password,
                max_retries=app_config.cacheConfig.max_retries,
                connection_timeout=app_config.cacheConfig.connection_timeout
            )
            CacheService.Init(cache_client_pool)
            Logger.info("✅ CacheService 초기화 완료")
        except Exception as e:
            Logger.error(f"❌ CacheService 초기화 실패: {e}")
            raise
        
        # Template 등록
        try:
            model_template = ModelTemplateImpl()
            TemplateContext.add_template(TemplateType.MODEL, model_template)
            Logger.info("✅ Model 템플릿 등록 성공")
        except Exception as e:
            Logger.error(f"❌ Model 템플릿 등록 실패: {e}")
            raise
        
        # TemplateService 초기화
        try:
            TemplateService.init(app_config)
            Logger.info("✅ TemplateService 초기화 완료")
        except Exception as e:
            Logger.error(f"❌ TemplateService 초기화 실패: {e}")
            raise
        
        # Protocol 콜백 설정
        try:
            model.setup_model_protocol_callbacks()
            Logger.info("✅ Model Protocol 콜백 설정 완료")
        except Exception as e:
            Logger.error(f"❌ Model Protocol 콜백 설정 실패: {e}")
            raise
        
    except Exception as e:
        Logger.error(f"❌ Config 파일 로드 실패: {config_file} - {e}")
        raise
    
    Logger.info("=== model_server 초기화 완료 ===")
    
    yield
    
    # 서비스 정리
    Logger.info("Model Server 종료 중...")
    Logger.info("Model Server 종료 완료")


# FastAPI 앱 생성
app = FastAPI(
    title="Model Server",
    description="시계열 모델을 이용한 매수/매도 신호 예측 마이크로서비스",
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

# 라우터 등록
app.include_router(model.router, prefix="/api/model", tags=["model"])


@app.get("/")
def root():
    Logger.info("model_server 동작 중")
    
    return {
        "message": "model_server 동작 중",
        "log_level": log_level.name,
        "env": app_env,
        "config_file": config_file,
        "service": "Model Server",
        "endpoints": {
            "predict": "/api/model/predict",
            "batch_predict": "/api/model/batch_predict", 
            "models": "/api/model/models"
        }
    }


@app.get("/health")
def health_check():
    """헬스체크"""
    return {
        "status": "healthy",
        "service": "model_server",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    # uvicorn base_server.application.model_server.main:app --reload --port 8001
    import uvicorn
    uvicorn.run(
        "base_server.application.model_server.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )