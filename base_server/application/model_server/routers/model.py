from fastapi import APIRouter, Request, HTTPException
from template.base.template_context import TemplateContext, TemplateType
from template.base.template_service import TemplateService
from template.model.common.model_serialize import (
    PredictRequest, BatchPredictRequest, ModelsListRequest
)
from template.model.common.model_protocol import ModelProtocol
from service.core.logger import Logger

router = APIRouter()

model_protocol = ModelProtocol()

def setup_model_protocol_callbacks():
    """Model protocol 콜백 설정 (main.py에서 한 번만 호출됨)"""
    model_template = TemplateContext.get_template(TemplateType.MODEL)
    model_protocol.on_predict_req_callback = getattr(model_template, "on_predict_req", None)
    model_protocol.on_batch_predict_req_callback = getattr(model_template, "on_batch_predict_req", None)
    model_protocol.on_models_list_req_callback = getattr(model_template, "on_models_list_req", None)

@router.post("/predict")
async def predict(request: PredictRequest, req: Request):
    """단일 심볼 예측 요청"""
    try:
        Logger.info(f"Model predict request: {request.symbol}")
        
        ip = req.headers.get("X-Forwarded-For")
        if not ip:
            ip = req.client.host
        else:
            ip = ip.split(", ")[0]
        
        return await TemplateService.run_operator(
            req.method,
            req.url.path,
            ip,
            request.model_dump_json(),
            model_protocol.predict_req_controller
        )
    except Exception as e:
        Logger.error(f"Predict error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch_predict") 
async def batch_predict(request: BatchPredictRequest, req: Request):
    """배치 예측 요청"""
    try:
        Logger.info(f"Model batch predict request: {len(request.symbols)} symbols")
        
        ip = req.headers.get("X-Forwarded-For")
        if not ip:
            ip = req.client.host
        else:
            ip = ip.split(", ")[0]
        
        return await TemplateService.run_operator(
            req.method,
            req.url.path,
            ip,
            request.model_dump_json(),
            model_protocol.batch_predict_req_controller
        )
    except Exception as e:
        Logger.error(f"Batch predict error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models")
async def models_list(request: ModelsListRequest, req: Request):
    """사용 가능한 모델 목록 조회"""
    try:
        Logger.info("Model list request")
        
        ip = req.headers.get("X-Forwarded-For")
        if not ip:
            ip = req.client.host
        else:
            ip = ip.split(", ")[0]
        
        return await TemplateService.run_operator(
            req.method,
            req.url.path,
            ip,
            request.model_dump_json(),
            model_protocol.models_list_req_controller
        )
    except Exception as e:
        Logger.error(f"Models list error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# GET 버전도 제공 (간편한 테스트용)
@router.get("/models")
async def models_list_get(req: Request):
    """사용 가능한 모델 목록 조회 (GET)"""
    try:
        Logger.info("Model list request (GET)")
        
        # 기본 요청 객체 생성
        request = ModelsListRequest()
        ip = req.headers.get("X-Forwarded-For")
        if not ip:
            ip = req.client.host
        else:
            ip = ip.split(", ")[0]
        
        return await TemplateService.run_operator(
            "GET",
            req.url.path,
            ip,
            request.model_dump_json(),
            model_protocol.models_list_req_controller
        )
    except Exception as e:
        Logger.error(f"Models list (GET) error: {e}")
        raise HTTPException(status_code=500, detail=str(e))