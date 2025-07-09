from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class TutorialStep(BaseModel):
    """튜토리얼 단계 정보"""
    step_id: str = ""
    step_number: int = 0
    title: str = ""
    description: str = ""
    target_element: str = ""
    position: str = "BOTTOM"  # TOP, BOTTOM, LEFT, RIGHT
    highlight_type: str = "BORDER"  # BORDER, OVERLAY, SPOTLIGHT
    action_required: bool = False
    expected_action: str = ""
    media_url: str = ""
    duration: int = 5000  # ms

class TutorialProgress(BaseModel):
    """튜토리얼 진행 상태"""
    tutorial_type: str = ""
    current_step: int = 0
    total_steps: int = 0
    is_completed: bool = False
    completion_rate: float = 0.0
    time_spent: int = 0

class TutorialSession(BaseModel):
    """튜토리얼 세션"""
    session_id: str = ""
    tutorial_type: str = ""
    started_at: str = ""
    last_step: int = 0
    user_feedback: Optional[Dict[str, Any]] = None