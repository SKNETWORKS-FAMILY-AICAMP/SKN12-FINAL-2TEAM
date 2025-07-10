import uuid
from datetime import datetime
from template.base.template_context import TemplateContext
from template.tutorial.common.tutorial_serialize import (
    TutorialStartRequest, TutorialStartResponse,
    TutorialProgressRequest, TutorialProgressResponse,
    TutorialCompleteRequest, TutorialCompleteResponse,
    TutorialListRequest, TutorialListResponse
)
from template.tutorial.common.tutorial_model import TutorialStep, TutorialProgress, TutorialSession
from service.service_container import ServiceContainer
from service.core.logger import Logger

class TutorialTemplateImpl:
    def __init__(self):
        pass

    async def on_tutorial_start_req(self, client_session, request: TutorialStartRequest):
        """튜토리얼 시작 요청 처리"""
        response = TutorialStartResponse()
        response.sequence = request.sequence
        
        Logger.info(f"Tutorial start request: {request.tutorial_type}")
        
        try:
            # 튜토리얼 세션 생성
            session_id = str(uuid.uuid4())
            
            # 튜토리얼 타입에 따른 단계 생성
            steps = self._create_tutorial_steps(request.tutorial_type, request.user_level)
            
            response.errorCode = 0
            response.session_id = session_id
            response.steps = steps
            response.total_steps = len(steps)
            
            Logger.info(f"Tutorial started: session_id={session_id}, steps={len(steps)}")
            
        except Exception as e:
            response.errorCode = 1000
            Logger.error(f"Tutorial start error: {e}")
        
        return response

    async def on_tutorial_progress_req(self, client_session, request: TutorialProgressRequest):
        """튜토리얼 진행 상태 업데이트"""
        response = TutorialProgressResponse()
        response.sequence = request.sequence
        
        Logger.info(f"Tutorial progress: session_id={request.session_id}, step={request.current_step}")
        
        try:
            # 진행 상태 업데이트
            progress = TutorialProgress(
                tutorial_type="ONBOARDING",
                current_step=request.current_step,
                total_steps=10,  # 예시
                is_completed=False,
                completion_rate=request.current_step / 10.0,
                time_spent=request.time_spent
            )
            
            # 다음 단계 준비
            if request.current_step < 10:
                next_step = TutorialStep(
                    step_id=f"step_{request.current_step + 1}",
                    step_number=request.current_step + 1,
                    title=f"Step {request.current_step + 1}",
                    description=f"Description for step {request.current_step + 1}",
                    target_element="",
                    position="BOTTOM"
                )
                response.next_step = next_step
                response.is_final_step = False
            else:
                response.is_final_step = True
                progress.is_completed = True
            
            response.errorCode = 0
            response.progress = progress
            
        except Exception as e:
            response.errorCode = 1000
            Logger.error(f"Tutorial progress error: {e}")
        
        return response

    async def on_tutorial_complete_req(self, client_session, request: TutorialCompleteRequest):
        """튜토리얼 완료 요청 처리"""
        response = TutorialCompleteResponse()
        response.sequence = request.sequence
        
        Logger.info(f"Tutorial complete: session_id={request.session_id}")
        
        try:
            response.errorCode = 0
            response.completion_reward = 100  # 예시 보상
            response.message = "튜토리얼을 완료했습니다!"
            response.next_action = "GOTO_DASHBOARD"
            
            Logger.info(f"Tutorial completed: session_id={request.session_id}")
            
        except Exception as e:
            response.errorCode = 1000
            Logger.error(f"Tutorial complete error: {e}")
        
        return response

    async def on_tutorial_list_req(self, client_session, request: TutorialListRequest):
        """튜토리얼 목록 요청 처리"""
        response = TutorialListResponse()
        response.sequence = request.sequence
        
        Logger.info(f"Tutorial list request: category={request.category}")
        
        try:
            # 샘플 튜토리얼 목록
            tutorials = [
                {
                    "id": "onboarding",
                    "title": "기본 사용법",
                    "description": "투자 플랫폼 기본 사용법을 익혀보세요",
                    "category": "BASIC",
                    "duration": 300,
                    "steps": 10
                },
                {
                    "id": "portfolio",
                    "title": "포트폴리오 관리",
                    "description": "포트폴리오를 효율적으로 관리하는 방법",
                    "category": "BASIC",
                    "duration": 180,
                    "steps": 6
                }
            ]
            
            response.errorCode = 0
            response.tutorials = tutorials
            response.user_progress = {}
            
        except Exception as e:
            response.errorCode = 1000
            Logger.error(f"Tutorial list error: {e}")
        
        return response

    def _create_tutorial_steps(self, tutorial_type: str, user_level: str) -> list[TutorialStep]:
        """튜토리얼 타입에 따른 단계 생성"""
        steps = []
        
        if tutorial_type == "ONBOARDING":
            steps = [
                TutorialStep(
                    step_id="step_1",
                    step_number=1,
                    title="대시보드 둘러보기",
                    description="메인 대시보드의 주요 기능을 알아보세요",
                    target_element="#dashboard",
                    position="BOTTOM"
                ),
                TutorialStep(
                    step_id="step_2",
                    step_number=2,
                    title="포트폴리오 확인",
                    description="현재 포트폴리오 상태를 확인해보세요",
                    target_element="#portfolio",
                    position="RIGHT"
                ),
                TutorialStep(
                    step_id="step_3",
                    step_number=3,
                    title="AI 채팅 사용",
                    description="AI 투자 어드바이저와 대화해보세요",
                    target_element="#ai-chat",
                    position="LEFT"
                )
            ]
        
        return steps