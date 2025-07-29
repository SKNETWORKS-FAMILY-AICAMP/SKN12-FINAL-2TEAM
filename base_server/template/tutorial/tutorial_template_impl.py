from template.base.base_template import BaseTemplate
from template.tutorial.common.tutorial_serialize import (
    TutorialCompleteStepRequest, TutorialCompleteStepResponse,
    TutorialGetProgressRequest, TutorialGetProgressResponse
)
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
        """튜토리얼 스텝 완료 저장"""
        response = TutorialCompleteStepResponse()
        response.sequence = request.sequence
        
        try:
            account_db_key = client_session.session_info.account_db_key
            shard_id = client_session.session_info.shard_id
            
            # DB에 스텝 완료 저장
            database_service = ServiceContainer.get_database_service()
            result = await database_service.call_shard_procedure(
                shard_id,
                'fp_tutorial_complete_step',
                (account_db_key, request.tutorial_type, request.step_number)
            )
            
            if result and result[0].get('result') == 'SUCCESS':
                response.errorCode = 0
                Logger.debug(f"Tutorial step completed: user={account_db_key}, type={request.tutorial_type}, step={request.step_number}")
            else:
                response.errorCode = 500
                Logger.error(f"Tutorial step save failed: {result}")
            
        except Exception as e:
            response.errorCode = 500
            Logger.error(f"Tutorial step complete error: {e}")
        
        return response

    async def on_tutorial_get_progress_req(self, client_session, request: TutorialGetProgressRequest):
        """튜토리얼 진행 상태 조회 - 첫 번째 튜토리얼 반환"""
        response = TutorialGetProgressResponse()
        response.sequence = request.sequence
        
        try:
            account_db_key = client_session.session_info.account_db_key
            shard_id = client_session.session_info.shard_id
            
            database_service = ServiceContainer.get_database_service()
            result = await database_service.call_shard_procedure(
                shard_id,
                'fp_tutorial_get_progress',
                (account_db_key,)
            )
            
            # 첫 번째 결과만 반환 (알파벳 순으로 정렬되어 나옴)
            if result and len(result) > 0:
                first_row = result[0]
                response.tutorial_type = first_row.get('tutorial_type', '')
                response.step_number = first_row.get('completed_step', 0)
            else:
                response.tutorial_type = ""
                response.step_number = 0
            
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 500
            response.tutorial_type = ""
            response.step_number = 0
            Logger.error(f"Tutorial get progress error: {e}")
        
        return response