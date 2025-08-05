from .model_serialize import (
    PredictRequest, BatchPredictRequest, ModelsListRequest
)

class ModelProtocol:
    """모델 프로토콜 - BaseRequest/BaseResponse 기반"""
    def __init__(self):
        self.on_predict_req_callback = None
        self.on_batch_predict_req_callback = None
        self.on_models_list_req_callback = None

    async def predict_req_controller(self, session, request: PredictRequest):
        """JSON 기반 예측 요청 처리"""
        if self.on_predict_req_callback:
            return await self.on_predict_req_callback(session, request)
        raise NotImplementedError('on_predict_req_callback is not set')

    async def batch_predict_req_controller(self, session, request: BatchPredictRequest):
        """JSON 기반 배치 예측 요청 처리"""
        if self.on_batch_predict_req_callback:
            return await self.on_batch_predict_req_callback(session, request)
        raise NotImplementedError('on_batch_predict_req_callback is not set')

    async def models_list_req_controller(self, session, request: ModelsListRequest):
        """JSON 기반 모델 목록 요청 처리"""
        if self.on_models_list_req_callback:
            return await self.on_models_list_req_callback(session, request)
        raise NotImplementedError('on_models_list_req_callback is not set')