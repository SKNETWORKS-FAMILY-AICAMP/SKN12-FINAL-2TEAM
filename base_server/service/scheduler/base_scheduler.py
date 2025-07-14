import asyncio
import threading
from datetime import datetime, timedelta
from typing import Callable, Dict, Optional, Any, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from service.core.logger import Logger

class ScheduleType(Enum):
    """스케줄 타입"""
    INTERVAL = "interval"  # 주기적 실행
    CRON = "cron"         # Cron 표현식
    ONCE = "once"         # 일회성 실행
    DAILY = "daily"       # 매일 특정 시간

@dataclass
class ScheduleJob:
    """스케줄 작업 정의"""
    job_id: str
    name: str
    schedule_type: ScheduleType
    schedule_value: Any  # interval(초), cron표현식, datetime 등
    callback: Callable
    enabled: bool = True
    use_distributed_lock: bool = False
    lock_key: Optional[str] = None
    lock_ttl: int = 300  # 5분
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    error_count: int = 0
    max_retries: int = 3

class IScheduler(ABC):
    """스케줄러 인터페이스"""
    
    @abstractmethod
    async def add_job(self, job: ScheduleJob):
        """작업 추가"""
        pass
    
    @abstractmethod
    async def remove_job(self, job_id: str):
        """작업 제거"""
        pass
    
    @abstractmethod
    async def start(self):
        """스케줄러 시작"""
        pass
    
    @abstractmethod
    async def stop(self):
        """스케줄러 중지"""
        pass
    
    @abstractmethod
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """작업 상태 조회"""
        pass

class BaseScheduler(IScheduler):
    """기본 스케줄러 구현"""
    
    def __init__(self, lock_service=None):
        self.jobs: Dict[str, ScheduleJob] = {}
        self.running = False
        self.scheduler_task: Optional[asyncio.Task] = None
        self.lock_service = lock_service
        
    async def add_job(self, job: ScheduleJob):
        """작업 추가"""
        try:
            # 다음 실행 시간 계산
            job.next_run = self._calculate_next_run(job)
            
            self.jobs[job.job_id] = job
            Logger.info(f"스케줄 작업 추가: {job.name} ({job.job_id})")
            
        except Exception as e:
            Logger.error(f"스케줄 작업 추가 실패: {job.job_id} - {e}")
    
    async def remove_job(self, job_id: str):
        """작업 제거"""
        if job_id in self.jobs:
            job = self.jobs.pop(job_id)
            Logger.info(f"스케줄 작업 제거: {job.name} ({job_id})")
        else:
            Logger.warn(f"존재하지 않는 작업 ID: {job_id}")
    
    async def start(self):
        """스케줄러 시작"""
        if self.running:
            Logger.warn("스케줄러가 이미 실행 중입니다")
            return
        
        self.running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        Logger.info("스케줄러 시작")
    
    async def stop(self):
        """스케줄러 중지"""
        if not self.running:
            Logger.warn("스케줄러가 실행 중이지 않습니다")
            return
        
        self.running = False
        
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        Logger.info("스케줄러 중지")
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """작업 상태 조회"""
        if job_id not in self.jobs:
            return None
        
        job = self.jobs[job_id]
        return {
            "job_id": job.job_id,
            "name": job.name,
            "enabled": job.enabled,
            "schedule_type": job.schedule_type.value,
            "last_run": job.last_run.isoformat() if job.last_run else None,
            "next_run": job.next_run.isoformat() if job.next_run else None,
            "run_count": job.run_count,
            "error_count": job.error_count,
            "use_distributed_lock": job.use_distributed_lock
        }
    
    def get_all_jobs_status(self) -> List[Dict[str, Any]]:
        """모든 작업 상태 조회"""
        return [self.get_job_status(job_id) for job_id in self.jobs.keys()]
    
    async def _scheduler_loop(self):
        """스케줄러 메인 루프"""
        try:
            while self.running:
                now = datetime.now()
                
                # 실행 가능한 작업들 찾기
                ready_jobs = [
                    job for job in self.jobs.values()
                    if job.enabled and job.next_run and job.next_run <= now
                ]
                
                # 작업 실행
                for job in ready_jobs:
                    asyncio.create_task(self._execute_job(job))
                
                # 1초 대기
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            Logger.info("스케줄러 루프 취소됨")
        except Exception as e:
            Logger.error(f"스케줄러 루프 오류: {e}")
    
    async def _execute_job(self, job: ScheduleJob):
        """작업 실행"""
        try:
            Logger.info(f"스케줄 작업 실행 시작: {job.name}")
            
            # 분산락 사용 여부 확인
            if job.use_distributed_lock and self.lock_service:
                await self._execute_job_with_lock(job)
            else:
                await self._execute_job_direct(job)
                
        except Exception as e:
            job.error_count += 1
            Logger.error(f"스케줄 작업 실행 실패: {job.name} - {e}")
        
        finally:
            # 다음 실행 시간 계산
            job.next_run = self._calculate_next_run(job)
    
    async def _execute_job_with_lock(self, job: ScheduleJob):
        """분산락을 사용한 작업 실행"""
        lock_key = job.lock_key or f"scheduler:job:{job.job_id}"
        
        try:
            async with self.lock_service.get_manager().acquire_lock(
                lock_key, 
                ttl=job.lock_ttl, 
                timeout=5
            ):
                await self._execute_job_direct(job)
                Logger.info(f"분산락 작업 완료: {job.name}")
                
        except RuntimeError as e:
            if "분산락 획득 실패" in str(e):
                Logger.info(f"분산락 획득 실패 - 다른 인스턴스에서 실행 중: {job.name}")
            else:
                raise
    
    async def _execute_job_direct(self, job: ScheduleJob):
        """직접 작업 실행"""
        try:
            # 콜백이 코루틴인지 확인
            if asyncio.iscoroutinefunction(job.callback):
                await job.callback()
            else:
                # 동기 함수는 스레드 풀에서 실행
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, job.callback)
            
            job.last_run = datetime.now()
            job.run_count += 1
            
            Logger.info(f"스케줄 작업 완료: {job.name} (실행 횟수: {job.run_count})")
            
        except Exception as e:
            Logger.error(f"작업 콜백 실행 실패: {job.name} - {e}")
            raise
    
    def _calculate_next_run(self, job: ScheduleJob) -> Optional[datetime]:
        """다음 실행 시간 계산"""
        now = datetime.now()
        
        try:
            if job.schedule_type == ScheduleType.INTERVAL:
                # 주기적 실행 (초 단위)
                interval_seconds = int(job.schedule_value)
                return now + timedelta(seconds=interval_seconds)
            
            elif job.schedule_type == ScheduleType.DAILY:
                # 매일 특정 시간 (HH:MM 형식)
                time_str = job.schedule_value  # "14:30"
                hour, minute = map(int, time_str.split(':'))
                
                next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # 오늘 시간이 이미 지났으면 내일로
                if next_run <= now:
                    next_run += timedelta(days=1)
                
                return next_run
            
            elif job.schedule_type == ScheduleType.ONCE:
                # 일회성 실행
                if job.run_count > 0:
                    return None  # 이미 실행됨
                
                if isinstance(job.schedule_value, datetime):
                    return job.schedule_value
                else:
                    return now  # 즉시 실행
            
            elif job.schedule_type == ScheduleType.CRON:
                # Cron 표현식 (간단한 구현)
                # 실제로는 croniter 라이브러리 사용 권장
                Logger.warn(f"Cron 표현식은 아직 구현되지 않음: {job.schedule_value}")
                return None
            
            else:
                Logger.error(f"지원하지 않는 스케줄 타입: {job.schedule_type}")
                return None
                
        except Exception as e:
            Logger.error(f"다음 실행 시간 계산 실패: {job.job_id} - {e}")
            return None