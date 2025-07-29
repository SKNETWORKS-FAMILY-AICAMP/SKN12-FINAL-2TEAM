from pydantic import BaseModel

class TutorialProgress(BaseModel):
    """튜토리얼 진행 상태 - 단순 저장용"""
    tutorial_type: str = ""
    completed_step: int = 0  # 0이면 시작 안함, N이면 N번째 스텝까지 완료
    updated_at: str = ""