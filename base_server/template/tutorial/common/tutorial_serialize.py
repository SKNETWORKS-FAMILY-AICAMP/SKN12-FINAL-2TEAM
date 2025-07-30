from typing import Dict, List
from service.net.protocol_base import BaseRequest, BaseResponse
from .tutorial_model import TutorialProgress

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
    """진행 상태 응답 - 모든 튜토리얼 타입의 상태 반환"""
    progress_list: List[TutorialProgress] = []