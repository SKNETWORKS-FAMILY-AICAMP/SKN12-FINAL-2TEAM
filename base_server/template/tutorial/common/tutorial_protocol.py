from .tutorial_serialize import (
    TutorialCompleteStepRequest, TutorialGetProgressRequest
)
from typing import Optional, Callable, Awaitable

class TutorialProtocol:
    def __init__(self):
        # 튜토리얼 관련 콜백
        self.on_tutorial_complete_step_req_callback: Optional[Callable[..., Awaitable]] = None
        self.on_tutorial_get_progress_req_callback: Optional[Callable[..., Awaitable]] = None

    async def tutorial_complete_step_req_controller(self, session, msg: bytes, length: int):
        request = TutorialCompleteStepRequest.model_validate_json(msg)
        if self.on_tutorial_complete_step_req_callback:
            return await self.on_tutorial_complete_step_req_callback(session, request)
        raise NotImplementedError("on_tutorial_complete_step_req_callback is not set")

    async def tutorial_get_progress_req_controller(self, session, msg: bytes, length: int):
        request = TutorialGetProgressRequest.model_validate_json(msg)
        if self.on_tutorial_get_progress_req_callback:
            return await self.on_tutorial_get_progress_req_callback(session, request)
        raise NotImplementedError("on_tutorial_get_progress_req_callback is not set")