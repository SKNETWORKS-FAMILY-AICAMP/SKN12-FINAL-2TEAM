from template.base.base_template import BaseTemplate
from template.tutorial.common.tutorial_serialize import (
    TutorialCompleteStepRequest, TutorialCompleteStepResponse,
    TutorialGetProgressRequest, TutorialGetProgressResponse
)
from template.tutorial.common.tutorial_model import TutorialProgress
from service.service_container import ServiceContainer
from service.core.logger import Logger

class TutorialTemplateImpl(BaseTemplate):
    def __init__(self):
        super().__init__()
    
    def init(self, config):
        """튜토리얼 템플릿 초기화"""
        try:
            Logger.info("Tutorial 템플릿 초기화 완료")
        except Exception as e:
            Logger.error(f"Tutorial 템플릿 초기화 실패: {e}")
    
    def on_load_data(self, config):
        """튜토리얼 데이터 로딩"""
        pass

    async def on_tutorial_complete_step_req(self, client_session, request: TutorialCompleteStepRequest):
        """
        튜토리얼 스텝 완료 저장
        
        tutorial_type별로 개별 로우를 유지하며, GREATEST 함수로 스텝 역행 방지
        """
        response = TutorialCompleteStepResponse()
        response.sequence = request.sequence
        
        try:
            account_db_key = getattr(client_session.session, 'account_db_key', 0)
            shard_id = getattr(client_session.session, 'shard_id', 1)
            
            # 입력값 검증
            if not request.tutorial_type or request.step_number < 0:
                response.errorCode = 400
                Logger.error(f"Invalid tutorial request: type='{request.tutorial_type}', step={request.step_number}")
                return response
            
            # DB에 튜토리얼 상태 저장 (UPSERT 방식)
            database_service = ServiceContainer.get_database_service()
            result = await database_service.call_shard_procedure(
                shard_id,
                'fp_tutorial_complete_step',
                (account_db_key, request.tutorial_type, request.step_number)
            )
            
            if result and result[0].get('result') == 'SUCCESS':
                response.errorCode = 0
                Logger.info(f"Tutorial progress updated: user={account_db_key}, type='{request.tutorial_type}', step={request.step_number}")
            else:
                response.errorCode = 500
                Logger.error(f"Tutorial step save failed: {result}")
            
        except Exception as e:
            response.errorCode = 500
            Logger.error(f"Tutorial step complete error: {e}")
        
        return response

    async def on_tutorial_get_progress_req(self, client_session, request: TutorialGetProgressRequest):
        """
        튜토리얼 진행 상태 조회
        
        사용자의 모든 튜토리얼 타입별 상태를 반환 (복수 로우)
        """
        response = TutorialGetProgressResponse()
        response.sequence = request.sequence
        
        try:
            account_db_key = getattr(client_session.session, 'account_db_key', 0)
            shard_id = getattr(client_session.session, 'shard_id', 1)
            
            # 사용자 검증
            if account_db_key <= 0:
                response.errorCode = 400
                response.progress_list = []
                Logger.error(f"Invalid account_db_key: {account_db_key}")
                return response
            
            database_service = ServiceContainer.get_database_service()
            result = await database_service.call_shard_procedure(
                shard_id,
                'fp_tutorial_get_progress',
                (account_db_key,)
            )
            
            # 사용자의 모든 튜토리얼 상태 반환
            progress_list = []
            if result and len(result) > 0:
                for row in result:
                    progress = TutorialProgress(
                        tutorial_type=row.get('tutorial_type', ''),
                        completed_step=row.get('completed_step', 0),
                        updated_at=str(row.get('updated_at', ''))
                    )
                    progress_list.append(progress)
                Logger.debug(f"Tutorial progress found: user={account_db_key}, count={len(progress_list)}")
            else:
                Logger.debug(f"No tutorial progress found for user: {account_db_key}")
            
            response.progress_list = progress_list
            
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 500
            response.progress_list = []
            Logger.error(f"Tutorial get progress error: {e}")
        
        return response