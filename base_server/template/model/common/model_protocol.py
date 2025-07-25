from .model_serialize import (
    PredictRequest, BatchPredictRequest, ModelsListRequest
)

class ModelProtocol:
    def __init__(self):
        self.on_predict_req_callback = None
        self.on_batch_predict_req_callback = None
        self.on_models_list_req_callback = None

    async def predict_req_controller(self, session, msg: bytes, length: int):
        request = PredictRequest.model_validate_json(msg)
        if self.on_predict_req_callback:
            return await self.on_predict_req_callback(session, request)
        raise NotImplementedError('on_predict_req_callback is not set')

    async def batch_predict_req_controller(self, session, msg: bytes, length: int):
        request = BatchPredictRequest.model_validate_json(msg)
        if self.on_batch_predict_req_callback:
            return await self.on_batch_predict_req_callback(session, request)
        raise NotImplementedError('on_batch_predict_req_callback is not set')

    async def models_list_req_controller(self, session, msg: bytes, length: int):
        request = ModelsListRequest.model_validate_json(msg)
        if self.on_models_list_req_callback:
            return await self.on_models_list_req_callback(session, request)
        raise NotImplementedError('on_models_list_req_callback is not set')