from template.base.template.crawler_template import CrawlerTemplate
from template.base.client_session import ClientSession
from .common.crawler_serialize import (
    CrawlerExecuteRequest, CrawlerExecuteResponse,
    CrawlerStatusRequest, CrawlerStatusResponse,
    CrawlerHealthRequest, CrawlerHealthResponse,
    CrawlerStopRequest, CrawlerStopResponse,
    CrawlerDataRequest, CrawlerDataResponse
)
from .common.crawler_model import CrawlerTask, CrawlerData
from service.lock.lock_service import LockService
from service.external.external_service import ExternalService
from service.vectordb.vectordb_service import VectorDbService
from service.search.search_service import SearchService
from service.core.logger import Logger
from datetime import datetime
import asyncio
import uuid

class CrawlerTemplateImpl(CrawlerTemplate):
    def __init__(self):
        super().__init__()
        self.active_tasks = {}  # task_id -> CrawlerTask
        
    def on_load_data(self, config):
        """크롤러 템플릿 데이터 로드"""
        try:
            Logger.info("Crawler 템플릿 데이터 로드 시작")
            # 크롤러 관련 초기화 작업이 있다면 여기서 수행
            Logger.info("Crawler 템플릿 데이터 로드 완료")
        except Exception as e:
            Logger.error(f"Crawler 템플릿 데이터 로드 실패: {e}")
            
    def on_client_create(self, db_client, client_session):
        """클라이언트 생성 시 호출"""
        pass
        
    def on_client_close(self, db_client, client_session):
        """클라이언트 종료 시 호출"""
        pass
    
    async def on_crawler_execute_req(self, client_session: ClientSession, request: CrawlerExecuteRequest) -> CrawlerExecuteResponse:
        """크롤러 작업 실행 요청 처리 - Lock 서비스로 중복 실행 방지"""
        response = CrawlerExecuteResponse()
        
        try:
            # 분산락 설정 (중복 실행 방지)
            lock_key = request.lock_key or f"crawler_task_{request.task_type}_{request.task_id}"
            lock_ttl = request.lock_ttl
            
            # 락 획득 시도
            lock_token = None
            if LockService.is_initialized():
                lock_token = await LockService.acquire(lock_key, ttl=lock_ttl, timeout=5)
                if not lock_token:
                    response.errorCode = 10001
                    response.status = "skipped"
                    response.message = "Task skipped due to lock acquisition failure"
                    response.lock_acquired = False
                    return response
                
                response.lock_acquired = True
                Logger.info(f"Lock acquired for task: {lock_key}")
            else:
                Logger.warn("LockService not initialized, proceeding without lock")
                response.lock_acquired = False
            
            # 작업 시작
            response.task_id = request.task_id
            response.status = "running"
            response.started_at = datetime.now().isoformat()
            response.message = f"Crawler task started: {request.task_type}"
            
            # 활성 작업 목록에 추가
            task = CrawlerTask(
                task_id=request.task_id,
                task_type=request.task_type,
                status="running",
                target_url=request.target_url,
                target_api=request.target_api,
                parameters=request.parameters,
                priority=request.priority,
                started_at=response.started_at,
                lock_key=lock_key,
                lock_token=lock_token
            )
            self.active_tasks[request.task_id] = task
            
            # 비동기로 실제 크롤링 작업 시작 (백그라운드)
            asyncio.create_task(self._execute_crawler_task(task))
            
            Logger.info(f"Crawler task {request.task_id} started successfully")
            
        except Exception as e:
            Logger.error(f"Crawler execute error: {e}")
            response.errorCode = 10005
            response.status = "failed"
            response.message = "Task execution failed"
        
        return response
    
    async def _execute_crawler_task(self, task: CrawlerTask):
        """실제 크롤링 작업 수행 (백그라운드)"""
        task_id = task.task_id
        
        try:
            Logger.info(f"Starting crawler task execution: {task_id}")
            
            # TODO: 실제 크롤링 로직 구현
            # 1. External API 호출 또는 웹 크롤링
            crawled_data = await self._perform_crawling(task)
            
            # 2. VectorDB에 임베딩 저장
            if crawled_data:
                await self._store_to_vectordb(crawled_data, task)
                
            # 3. OpenSearch에 검색 데이터 저장
            if crawled_data:
                await self._store_to_opensearch(crawled_data, task)
            
            # 작업 완료 처리
            task.status = "completed"
            task.completed_at = datetime.now().isoformat()
            task.data_count = len(crawled_data) if crawled_data else 0
            
            Logger.info(f"Crawler task {task_id} completed successfully")
            
        except Exception as e:
            Logger.error(f"Crawler task {task_id} failed: {e}")
            task.status = "failed"
            task.error = str(e)
            task.completed_at = datetime.now().isoformat()
        
        finally:
            # 락 해제
            if task.lock_token and LockService.is_initialized():
                try:
                    await LockService.release(task.lock_key, task.lock_token)
                    Logger.info(f"Lock released for task: {task.lock_key}")
                except Exception as e:
                    Logger.error(f"Failed to release lock {task.lock_key}: {e}")
    
    async def _perform_crawling(self, task: CrawlerTask):
        """크롤링 수행 - 구현 예정"""
        # TODO: 실제 크롤링 로직 구현
        Logger.info(f"TODO: Implement crawling for {task.task_type}")
        
        # 임시 더미 데이터
        dummy_data = [
            CrawlerData(
                data_id=str(uuid.uuid4()),
                task_id=task.task_id,
                task_type=task.task_type,
                source=task.target_url or task.target_api or "unknown",
                title=f"Sample {task.task_type} data",
                content=f"This is sample content for {task.task_type}",
                crawled_at=datetime.now().isoformat()
            )
        ]
        
        return dummy_data
    
    async def _store_to_vectordb(self, data: list, task: CrawlerTask):
        """VectorDB에 임베딩 저장 - 구현 예정"""
        try:
            if not VectorDbService.is_initialized():
                Logger.warn("VectorDbService not initialized, skipping vectordb storage")
                return
                
            Logger.info(f"TODO: Store {len(data)} items to VectorDB")
            # TODO: 실제 VectorDB 저장 로직 구현
            
        except Exception as e:
            Logger.error(f"Failed to store to VectorDB: {e}")
    
    async def _store_to_opensearch(self, data: list, task: CrawlerTask):
        """OpenSearch에 검색 데이터 저장 - 구현 예정"""
        try:
            if not SearchService.is_initialized():
                Logger.warn("SearchService not initialized, skipping opensearch storage")
                return
                
            Logger.info(f"TODO: Store {len(data)} items to OpenSearch")
            # TODO: 실제 OpenSearch 저장 로직 구현
            
        except Exception as e:
            Logger.error(f"Failed to store to OpenSearch: {e}")
    
    async def on_crawler_status_req(self, client_session: ClientSession, request: CrawlerStatusRequest) -> CrawlerStatusResponse:
        """크롤러 상태 조회 요청 처리"""
        response = CrawlerStatusResponse()
        
        try:
            # 활성 작업 목록 반환
            tasks = [task.model_dump() for task in self.active_tasks.values()]
            
            # 필터링 적용
            if request.task_id:
                tasks = [t for t in tasks if t["task_id"] == request.task_id]
            if request.status:
                tasks = [t for t in tasks if t["status"] == request.status]
            
            # 제한 적용
            if request.limit:
                tasks = tasks[:request.limit]
            
            response.tasks = tasks
            response.total_count = len(tasks)
            Logger.info(f"Crawler status returned {len(tasks)} tasks")
            
        except Exception as e:
            Logger.error(f"Crawler status error: {e}")
            response.errorCode = 10002
        
        return response
    
    async def on_crawler_health_req(self, client_session: ClientSession, request: CrawlerHealthRequest) -> CrawlerHealthResponse:
        """크롤러 헬스체크 요청 처리"""
        response = CrawlerHealthResponse()
        
        try:
            response.timestamp = datetime.now().isoformat()
            response.active_tasks = len([t for t in self.active_tasks.values() if t.status == "running"])
            
            # 오늘 완료/실패 작업 수 계산
            today = datetime.now().date()
            completed_today = 0
            failed_today = 0
            
            for task in self.active_tasks.values():
                if task.completed_at:
                    try:
                        completed_date = datetime.fromisoformat(task.completed_at).date()
                        if completed_date == today:
                            if task.status == "completed":
                                completed_today += 1
                            elif task.status == "failed":
                                failed_today += 1
                    except:
                        pass
            
            response.completed_today = completed_today
            response.failed_today = failed_today
            
            # 서비스 상태 체크
            if request.check_services:
                services = {}
                services["lock_service"] = LockService.is_initialized()
                services["external_service"] = ExternalService.is_initialized()
                services["vectordb_service"] = VectorDbService.is_initialized()
                services["search_service"] = SearchService.is_initialized()
                response.services = services
            
            # 전체 상태 결정
            if response.active_tasks == 0 and completed_today > failed_today:
                response.status = "healthy"
            elif failed_today > completed_today:
                response.status = "degraded"
            else:
                response.status = "healthy"
            
            Logger.info(f"Crawler health check: {response.status}")
            
        except Exception as e:
            Logger.error(f"Crawler health check error: {e}")
            response.errorCode = 10003
            response.status = "unhealthy"
        
        return response
    
    async def on_crawler_stop_req(self, client_session: ClientSession, request: CrawlerStopRequest) -> CrawlerStopResponse:
        """크롤러 작업 중단 요청 처리"""
        response = CrawlerStopResponse()
        
        try:
            response.task_id = request.task_id
            
            if request.task_id in self.active_tasks:
                task = self.active_tasks[request.task_id]
                
                if task.status == "running":
                    # TODO: 실제 작업 중단 로직 구현
                    task.status = "stopped"
                    task.completed_at = datetime.now().isoformat()
                    
                    response.stopped = True
                    response.message = f"Task {request.task_id} stopped successfully"
                    Logger.info(f"Task {request.task_id} stopped")
                else:
                    response.stopped = False
                    response.message = f"Task {request.task_id} is not running (status: {task.status})"
            else:
                response.stopped = False
                response.message = f"Task {request.task_id} not found"
                response.errorCode = 10004
            
        except Exception as e:
            Logger.error(f"Crawler stop error: {e}")
            response.errorCode = 10005
            response.stopped = False
            response.message = "Failed to stop task"
        
        return response
    
    async def on_crawler_data_req(self, client_session: ClientSession, request: CrawlerDataRequest) -> CrawlerDataResponse:
        """크롤러 데이터 조회 요청 처리"""
        response = CrawlerDataResponse()
        
        try:
            # TODO: 실제 데이터베이스에서 크롤링된 데이터 조회 구현
            Logger.info("TODO: Implement crawler data retrieval from database")
            
            # 임시로 활성 작업 정보 반환
            data = []
            for task_id, task in self.active_tasks.items():
                if not request.task_id or task_id == request.task_id:
                    data.append(task.model_dump())
            
            response.data = data[:request.limit] if request.limit else data
            response.total_count = len(data)
            
        except Exception as e:
            Logger.error(f"Crawler data error: {e}")
            response.errorCode = 10006
        
        return response