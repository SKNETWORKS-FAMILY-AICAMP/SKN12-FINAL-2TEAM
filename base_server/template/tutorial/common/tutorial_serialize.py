from typing import Optional, List, Dict, Any
from service.net.protocol_base import BaseRequest, BaseResponse
from .tutorial_model import TutorialStep, TutorialProgress, TutorialSession

# ============================================================================
# 튜토리얼 시작 (REQ-HELP-001~004)
# 의거: 화면 004 (튜토리얼), REQ-HELP-001~004
# ============================================================================

class TutorialStartRequest(BaseRequest):
    """튜토리얼 시작 요청"""
    tutorial_type: str = "ONBOARDING"  # ONBOARDING, FEATURE_SPECIFIC
    user_level: str = "BEGINNER"

class TutorialStartResponse(BaseResponse):
    """튜토리얼 시작 응답"""
    session_id: str = ""
    steps: List[TutorialStep] = []
    total_steps: int = 0

class TutorialProgressRequest(BaseRequest):
    """튜토리얼 진행 상태 업데이트"""
    session_id: str
    current_step: int
    action_completed: bool = False
    time_spent: int = 0

class TutorialProgressResponse(BaseResponse):
    """튜토리얼 진행 상태 응답"""
    progress: Optional[TutorialProgress] = None
    next_step: Optional[TutorialStep] = None
    is_final_step: bool = False

class TutorialCompleteRequest(BaseRequest):
    """튜토리얼 완료 요청"""
    session_id: str
    feedback: Optional[str] = ""
    rating: int = 5

class TutorialCompleteResponse(BaseResponse):
    """튜토리얼 완료 응답"""
    completion_reward: int = 0
    message: str = ""
    next_action: str = "GOTO_DASHBOARD"

class TutorialListRequest(BaseRequest):
    """이용 가능한 튜토리얼 목록 요청"""
    category: str = "ALL"  # ALL, BASIC, ADVANCED

class TutorialListResponse(BaseResponse):
    """튜토리얼 목록 응답"""
    tutorials: List[Dict[str, Any]] = []
    user_progress: Dict[str, TutorialProgress] = {}