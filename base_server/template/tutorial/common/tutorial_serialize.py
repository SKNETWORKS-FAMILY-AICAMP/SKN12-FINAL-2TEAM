from typing import Dict
from service.net.protocol_base import BaseRequest, BaseResponse

# ============================================================================
# 튜토리얼 저장 전용 - 초간단 API
# ============================================================================

class TutorialCompleteStepRequest(BaseRequest):
    """튜토리얼 스텝 완료 저장"""
    tutorial_type: str
    step_number: int

class TutorialCompleteStepResponse(BaseResponse):
    """응답"""
    pass

class TutorialGetProgressRequest(BaseRequest):
    """진행 상태 조회 - 세션에서 사용자 정보 가져옴"""
    pass

class TutorialGetProgressResponse(BaseResponse):
    """진행 상태 응답"""
    tutorial_type: str = ""
    step_number: int = 0  # 0이면 시작 안함, N이면 N번째 스텝까지 완료