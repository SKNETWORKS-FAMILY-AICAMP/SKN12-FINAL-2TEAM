from .tutorial_serialize import (
    TutorialStartRequest, TutorialProgressRequest, TutorialCompleteRequest, TutorialListRequest
)

class TutorialProtocol:
    def __init__(self):
        # 콜백 속성
        self.on_tutorial_start_req_callback = None
        self.on_tutorial_progress_req_callback = None
        self.on_tutorial_complete_req_callback = None
        self.on_tutorial_list_req_callback = None

    async def tutorial_start_req_controller(self, session, msg: bytes, length: int):
        request = TutorialStartRequest.model_validate_json(msg)
        if self.on_tutorial_start_req_callback:
            return await self.on_tutorial_start_req_callback(session, request)
        raise NotImplementedError('on_tutorial_start_req_callback is not set')

    async def tutorial_progress_req_controller(self, session, msg: bytes, length: int):
        request = TutorialProgressRequest.model_validate_json(msg)
        if self.on_tutorial_progress_req_callback:
            return await self.on_tutorial_progress_req_callback(session, request)
        raise NotImplementedError('on_tutorial_progress_req_callback is not set')

    async def tutorial_complete_req_controller(self, session, msg: bytes, length: int):
        request = TutorialCompleteRequest.model_validate_json(msg)
        if self.on_tutorial_complete_req_callback:
            return await self.on_tutorial_complete_req_callback(session, request)
        raise NotImplementedError('on_tutorial_complete_req_callback is not set')

    async def tutorial_list_req_controller(self, session, msg: bytes, length: int):
        request = TutorialListRequest.model_validate_json(msg)
        if self.on_tutorial_list_req_callback:
            return await self.on_tutorial_list_req_callback(session, request)
        raise NotImplementedError('on_tutorial_list_req_callback is not set')