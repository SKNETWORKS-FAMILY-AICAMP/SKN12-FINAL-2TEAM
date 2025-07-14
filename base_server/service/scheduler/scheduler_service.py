from typing import Optional, Dict, Any, List
from .base_scheduler import BaseScheduler, ScheduleJob, IScheduler
from service.core.logger import Logger

class SchedulerService:
    """111 gameserver 패턴을 따르는 스케줄러 서비스"""
    
    _scheduler: Optional[IScheduler] = None
    _lock_service = None
    _initialized: bool = False
    
    @classmethod
    def init(cls, lock_service=None) -> bool:
        """
        스케줄러 서비스 초기화
        
        Args:
            lock_service: LockService 인스턴스 (분산락 지원)
        """
        try:
            if cls._initialized:
                Logger.warn("SchedulerService가 이미 초기화되었습니다")
                return True
            
            cls._lock_service = lock_service
            cls._scheduler = BaseScheduler(lock_service)
            cls._initialized = True
            
            Logger.info("SchedulerService 초기화 완료")
            return True
            
        except Exception as e:
            Logger.error(f"SchedulerService 초기화 실패: {e}")
            return False
    
    @classmethod
    async def shutdown(cls):
        """서비스 종료"""
        try:
            if cls._scheduler:
                await cls._scheduler.stop()
            
            cls._scheduler = None
            cls._lock_service = None
            cls._initialized = False
            
            Logger.info("SchedulerService 종료 완료")
            
        except Exception as e:
            Logger.error(f"SchedulerService 종료 중 오류: {e}")
    
    @classmethod
    def is_initialized(cls) -> bool:
        """초기화 상태 확인"""
        return cls._initialized
    
    @classmethod
    def get_scheduler(cls) -> IScheduler:
        """스케줄러 인스턴스 반환"""
        if not cls._initialized or cls._scheduler is None:
            raise RuntimeError("SchedulerService가 초기화되지 않았습니다")
        
        return cls._scheduler
    
    @classmethod
    async def start(cls):
        """스케줄러 시작"""
        if not cls._initialized or cls._scheduler is None:
            raise RuntimeError("SchedulerService가 초기화되지 않았습니다")
        
        await cls._scheduler.start()
    
    @classmethod
    async def stop(cls):
        """스케줄러 중지"""
        if not cls._initialized or cls._scheduler is None:
            raise RuntimeError("SchedulerService가 초기화되지 않았습니다")
        
        await cls._scheduler.stop()
    
    @classmethod
    async def add_job(cls, job: ScheduleJob):
        """작업 추가"""
        if not cls._initialized or cls._scheduler is None:
            raise RuntimeError("SchedulerService가 초기화되지 않았습니다")
        
        await cls._scheduler.add_job(job)
    
    @classmethod
    async def remove_job(cls, job_id: str):
        """작업 제거"""
        if not cls._initialized or cls._scheduler is None:
            raise RuntimeError("SchedulerService가 초기화되지 않았습니다")
        
        await cls._scheduler.remove_job(job_id)
    
    @classmethod
    def get_job_status(cls, job_id: str) -> Optional[Dict[str, Any]]:
        """작업 상태 조회"""
        if not cls._initialized or cls._scheduler is None:
            raise RuntimeError("SchedulerService가 초기화되지 않았습니다")
        
        return cls._scheduler.get_job_status(job_id)
    
    @classmethod
    def get_all_jobs_status(cls) -> List[Dict[str, Any]]:
        """모든 작업 상태 조회"""
        if not cls._initialized or cls._scheduler is None:
            raise RuntimeError("SchedulerService가 초기화되지 않았습니다")
        
        return cls._scheduler.get_all_jobs_status()