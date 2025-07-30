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
        """
        튜토리얼 스텝 완료 저장
        
        사용자별로 하나의 로우만 유지하며, tutorial_type과 step_number를 덮어씀
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
        
        사용자의 현재 튜토리얼 상태를 반환 (사용자당 하나의 로우)
        """
        response = TutorialGetProgressResponse()
        response.sequence = request.sequence
        
        try:
            account_db_key = getattr(client_session.session, 'account_db_key', 0)
            shard_id = getattr(client_session.session, 'shard_id', 1)
            
            # 사용자 검증
            if account_db_key <= 0:
                response.errorCode = 400
                response.tutorial_type = ""
                response.step_number = 0
                Logger.error(f"Invalid account_db_key: {account_db_key}")
                return response
            
            database_service = ServiceContainer.get_database_service()
            result = await database_service.call_shard_procedure(
                shard_id,
                'fp_tutorial_get_progress',
                (account_db_key,)
            )
            
            # 사용자의 현재 튜토리얼 상태 반환
            if result and len(result) > 0:
                row = result[0]
                response.tutorial_type = row.get('tutorial_type', '')
                response.step_number = row.get('completed_step', 0)
                Logger.debug(f"Tutorial progress found: user={account_db_key}, type='{response.tutorial_type}', step={response.step_number}")
            else:
                # 튜토리얼을 시작하지 않은 사용자
                response.tutorial_type = ""
                response.step_number = 0
                Logger.debug(f"No tutorial progress found for user: {account_db_key}")
            
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 500
            response.tutorial_type = ""
            response.step_number = 0
            Logger.error(f"Tutorial get progress error: {e}")
        
        return response