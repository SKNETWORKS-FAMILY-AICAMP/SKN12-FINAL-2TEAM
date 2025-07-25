"""
채팅 메시지 DB 저장 컨슈머

MessageQueue → Scheduler → DB 아키텍처 구현
- Partition Key로 메시지 수신 순서 보장
- Lock Service로 DB 저장 순서 보장
- Scheduler를 통한 배치 처리
- ServiceContainer를 통한 전역 서비스 관리
- Session의 shard_id 활용으로 정확한 샤드 라우팅
- 멀티 프로세스 환경 대응
- 효율적인 버퍼 관리로 메모리 최적화
"""

import asyncio
import json
import uuid
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

from service.core.logger import Logger
from service.queue.message_queue import QueueMessage, MessagePriority
from service.scheduler.scheduler_service import SchedulerService
from service.scheduler.base_scheduler import ScheduleJob, ScheduleType
from service.service_container import ServiceContainer


class ChatPersistenceConsumer:
    """채팅 메시지 DB 저장 컨슈머
    
    MessageQueue → Scheduler → DB 아키텍처 구현
    - MessageQueue에서 채팅 메시지 이벤트 수신 (Partition Key로 순서 보장)
    - Lock Service로 DB 저장 순서 보장
    - SchedulerService를 통해 배치 처리
    - 매핑 테이블 기반 shard_id로 정확한 샤드 DB 접근
    - 멀티 프로세스 환경에서 고유한 컨슈머 ID 생성
    - 효율적인 버퍼 관리로 메모리 누수 방지
    """
    
    def __init__(self):
        # 멀티 프로세스 환경에서 고유한 컨슈머 ID 생성
        self.consumer_id = f"chat_persistence_{uuid.uuid4().hex[:8]}_pid_{os.getpid()}"
        
        self.batch_size = 50  # 배치당 최대 메시지 수
        self.batch_interval = 3  # 3초마다 배치 처리
        self.message_buffer: Dict[str, List[Dict]] = {}  # shard_key별 버퍼
        self._running = False
        self._lock_timeout = 10  # Lock 획득 타임아웃 (초)
        self._lock_ttl = 30  # Lock TTL (초)
        
        # 스케줄러 작업 ID도 고유하게 생성
        self.batch_job_id = f"chat_batch_save_{uuid.uuid4().hex[:8]}"
        self.cleanup_job_id = f"chat_buffer_cleanup_{uuid.uuid4().hex[:8]}"
        
        Logger.info(f"ChatPersistenceConsumer 생성: consumer_id={self.consumer_id}")
        
    async def start(self):
        """컨슈머 시작"""
        try:
            # 필요한 서비스들 초기화 확인
            if not ServiceContainer.is_scheduler_service_initialized():
                Logger.error("SchedulerService가 초기화되지 않았습니다")
                raise RuntimeError("SchedulerService not initialized")
            
            # 스케줄러에 배치 처리 작업 등록 (고유한 job_id 사용)
            batch_job = ScheduleJob(
                job_id=self.batch_job_id,  # 고유한 작업 ID
                name=f"채팅 메시지 배치 저장 ({self.consumer_id})",
                schedule_type=ScheduleType.INTERVAL,
                schedule_value=self.batch_interval,
                callback=self._process_batch,
                max_retries=3
            )
            await SchedulerService.add_job(batch_job)
            Logger.info(f"채팅 배치 저장 스케줄러 등록 완료: {self.batch_job_id}")
            
            # 버퍼 정리 스케줄러 등록 (고유한 job_id 사용)
            cleanup_job = ScheduleJob(
                job_id=self.cleanup_job_id,  # 고유한 작업 ID
                name=f"채팅 버퍼 정리 ({self.consumer_id})",
                schedule_type=ScheduleType.INTERVAL,
                schedule_value=30,
                callback=self._cleanup_empty_buffers,
                max_retries=1
            )
            await SchedulerService.add_job(cleanup_job)
            Logger.info(f"채팅 버퍼 정리 스케줄러 등록 완료: {self.cleanup_job_id}")
            
            self._running = True
            Logger.info(f"ChatPersistenceConsumer 시작: {self.consumer_id}")
            
        except Exception as e:
            Logger.error(f"ChatPersistenceConsumer 시작 실패: {e}")
            raise
    
    async def stop(self):
        """컨슈머 종료"""
        self._running = False
        
        # 남은 메시지 처리
        await self._flush_all_buffers()
        
        # 스케줄러 작업 제거 (고유한 job_id로 제거)
        if ServiceContainer.is_scheduler_service_initialized():
            await SchedulerService.remove_job(self.batch_job_id)
            await SchedulerService.remove_job(self.cleanup_job_id)
        
        Logger.info(f"ChatPersistenceConsumer 종료: {self.consumer_id}")
    
    async def handle_message(self, message: QueueMessage) -> bool:
        """메시지 처리 핸들러
        
        QueueService.register_message_consumer()에 전달될 핸들러
        Partition Key로 이미 room별 순서는 보장된 상태
        """
        try:
            # 메시지 타입별 처리
            if message.message_type == "CHAT_ROOM_CREATE":
                return await self._handle_room_create(message)
            elif message.message_type == "CHAT_MESSAGE_SAVE":
                return await self._handle_message_save(message)
            else:
                Logger.warn(f"알 수 없는 메시지 타입: {message.message_type} (consumer: {self.consumer_id})")
                return True  # 무시하고 ACK
                
        except Exception as e:
            Logger.error(f"메시지 처리 실패: {e}, message_id={message.id}, consumer={self.consumer_id}")
            return False  # NACK하여 재시도
    
    async def _handle_room_create(self, message: QueueMessage) -> bool:
        """채팅방 생성 이벤트 처리 - 즉시 DB 저장"""
        payload = message.payload
        room_id = payload.get('room_id')
        account_db_key = payload.get('account_db_key', 0)
        shard_id = payload.get('shard_id', 1)  # 매핑 테이블에서 조회된 shard_id 사용
        
        # Lock으로 중복 생성 방지 (멀티 프로세스 환경에서 중요)
        lock_key = f"chat_room_create:{room_id}"
        
        try:
            # ServiceContainer를 통한 Lock 서비스 접근
            if not ServiceContainer.is_lock_service_initialized():
                Logger.error("LockService가 초기화되지 않았습니다")
                return False
            
            lock_service = ServiceContainer.get_lock_service()
            
            # Lock 획득 시도
            token = await lock_service.acquire(lock_key, ttl=self._lock_ttl, timeout=self._lock_timeout)
            if not token:
                Logger.warn(f"채팅방 생성 Lock 획득 실패: {room_id} (consumer: {self.consumer_id})")
                return False  # 재시도
            
            try:
                # ServiceContainer를 통한 Database 서비스 접근
                database_service = ServiceContainer.get_database_service()
                
                # 프로시저 호출 (account_template_impl.py 패턴 사용)
                result = await database_service.call_shard_procedure(
                    shard_id,  # 매핑 테이블 기반 shard_id 사용
                    'fp_chat_room_create',
                    (room_id, account_db_key, payload.get('title', 'New Chat'), payload.get('ai_persona', 'default'))
                )
                
                if result and result[0].get('result') in ['SUCCESS', 'EXISTS']:
                    Logger.info(f"채팅방 생성 완료: room_id={room_id}, shard_id={shard_id}, consumer={self.consumer_id}")
                    return True
                else:
                    Logger.warn(f"채팅방 생성 결과: {result} (consumer: {self.consumer_id})")
                    return False
                    
            finally:
                # Lock 해제
                await lock_service.release(lock_key, token)
                
        except Exception as e:
            Logger.error(f"채팅방 생성 DB 저장 실패: {e} (consumer: {self.consumer_id})")
            return False
    
    async def _handle_message_save(self, message: QueueMessage) -> bool:
        """채팅 메시지 저장 이벤트 처리 - 버퍼에 추가"""
        try:
            payload = message.payload
            account_db_key = payload.get('account_db_key', 0)
            shard_id = payload.get('shard_id', 1)  # 매핑 테이블에서 조회된 shard_id 사용
            room_id = payload.get('room_id')
            
            # 메타데이터에서 sequence 번호 추출 (순서 검증용)
            metadata = json.loads(payload.get('metadata', '{}'))
            sequence = metadata.get('sequence', 0)
            
            # 샤드 키 생성 (매핑된 shard_id 사용)
            shard_key = f"shard_{shard_id}"
            
            # 버퍼에 추가 (sequence 포함)
            if shard_key not in self.message_buffer:
                self.message_buffer[shard_key] = []
            
            buffer_item = {
                **payload,
                'sequence': sequence,
                'buffer_timestamp': datetime.now().timestamp(),
                'consumer_id': self.consumer_id  # 추적용
            }
            
            self.message_buffer[shard_key].append(buffer_item)
            
            # 버퍼가 가득 찬 경우 즉시 처리
            if len(self.message_buffer[shard_key]) >= self.batch_size:
                await self._process_shard_batch(shard_key)
            
            Logger.debug(f"메시지 버퍼 추가: room_id={room_id}, shard_id={shard_id}, buffer_size={len(self.message_buffer[shard_key])}, consumer={self.consumer_id}")
            return True
            
        except Exception as e:
            Logger.error(f"메시지 버퍼 추가 실패: {e} (consumer: {self.consumer_id})")
            return False
    
    async def _process_batch(self):
        """스케줄러에 의해 호출되는 배치 처리 함수"""
        if not self._running:
            return
        
        try:
            # 모든 샤드의 버퍼 처리
            tasks = []
            for shard_key in list(self.message_buffer.keys()):
                if self.message_buffer[shard_key]:
                    tasks.append(self._process_shard_batch(shard_key))
            
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 예외 발생한 태스크 로깅
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        Logger.error(f"배치 처리 중 오류: {result} (consumer: {self.consumer_id})")
                        
        except Exception as e:
            Logger.error(f"배치 처리 중 오류: {e} (consumer: {self.consumer_id})")
    
    async def _process_shard_batch(self, shard_key: str):
        """특정 샤드의 메시지 배치 처리 (Lock으로 순서 보장)"""
        if shard_key not in self.message_buffer or not self.message_buffer[shard_key]:
            return
        
        # 버퍼에서 메시지 추출 (sequence 순서로 정렬)
        messages = self.message_buffer[shard_key][:self.batch_size]
        self.message_buffer[shard_key] = self.message_buffer[shard_key][self.batch_size:]
        
        if not messages:
            return
        
        # sequence 순서로 정렬 (혹시 모를 순서 보장)
        messages.sort(key=lambda x: x.get('sequence', 0))
        
        shard_id = int(shard_key.split('_')[1])
        
        # room별로 그룹화하여 Lock 적용
        room_groups = {}
        for msg in messages:
            room_id = msg.get('room_id')
            if room_id not in room_groups:
                room_groups[room_id] = []
            room_groups[room_id].append(msg)
        
        # room별로 순차 처리 (Lock으로 순서 보장)
        success_count = 0
        total_count = len(messages)
        
        for room_id, room_messages in room_groups.items():
            success_count += await self._process_room_messages(shard_id, room_id, room_messages)
        
        Logger.info(f"샤드 {shard_id} 배치 처리 완료: {success_count}/{total_count} 성공 (consumer: {self.consumer_id})")
    
    async def _process_room_messages(self, shard_id: int, room_id: str, messages: List[Dict]) -> int:
        """특정 채팅방의 메시지들을 Lock으로 순서 보장하며 처리"""
        # 멀티 프로세스 환경에서 room별 순서 보장을 위한 Lock
        lock_key = f"chat_db_save:{room_id}"
        success_count = 0
        
        try:
            # ServiceContainer를 통한 Lock 서비스 접근
            if not ServiceContainer.is_lock_service_initialized():
                Logger.error("LockService가 초기화되지 않았습니다")
                return 0
            
            lock_service = ServiceContainer.get_lock_service()
            database_service = ServiceContainer.get_database_service()
            
            # Lock 획득 (같은 채팅방의 메시지는 순차 처리)
            token = await lock_service.acquire(lock_key, ttl=self._lock_ttl, timeout=self._lock_timeout)
            if not token:
                Logger.warn(f"채팅방 DB 저장 Lock 획득 실패: {room_id} (consumer: {self.consumer_id})")
                return 0  # 전체 실패
            
            try:
                # 메시지들을 sequence 순서대로 DB 저장
                for msg_payload in messages:
                    try:
                        # account_template_impl.py 패턴 사용
                        # metadata를 JSON 객체로 변환 (문자열에서)
                        metadata_str = msg_payload.get('metadata', '{}')
                        try:
                            metadata_obj = json.loads(metadata_str) if isinstance(metadata_str, str) else metadata_str
                        except json.JSONDecodeError:
                            metadata_obj = {}
                        
                        result = await database_service.call_shard_procedure(
                            shard_id,  # 매핑 테이블 기반 shard_id 사용
                            'fp_chat_message_batch_save',
                            (
                                msg_payload.get('message_id', ''),  # p_message_id (추가)
                                msg_payload['room_id'],             # p_room_id
                                msg_payload['account_db_key'],      # p_account_db_key  
                                msg_payload['message_type'],        # p_message_type
                                msg_payload['content'],             # p_content
                                json.dumps(metadata_obj),          # p_metadata
                                msg_payload.get('parent_message_id', None)  # p_parent_message_id
                            )
                        )
                        
                        if result and result[0].get('result') == 'SUCCESS':
                            success_count += 1
                            Logger.debug(f"메시지 저장 성공: {msg_payload.get('message_id')}, shard_id={shard_id}, consumer={self.consumer_id}")
                        else:
                            Logger.warn(f"메시지 저장 실패: {msg_payload.get('message_id')}, result={result}, consumer={self.consumer_id}")
                            
                    except Exception as e:
                        Logger.error(f"메시지 저장 중 오류: {e}, message_id={msg_payload.get('message_id')}, consumer={self.consumer_id}")
                
            finally:
                # Lock 해제
                await lock_service.release(lock_key, token)
                
        except Exception as e:
            Logger.error(f"채팅방 메시지 처리 중 오류: {e}, room_id={room_id}, consumer={self.consumer_id}")
        
        return success_count
    
    async def _flush_all_buffers(self):
        """모든 버퍼의 메시지 처리 (종료 시 호출)"""
        try:
            tasks = []
            for shard_key in list(self.message_buffer.keys()):
                while self.message_buffer[shard_key]:
                    tasks.append(self._process_shard_batch(shard_key))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
                
            Logger.info(f"모든 버퍼 플러시 완료 (consumer: {self.consumer_id})")
            
        except Exception as e:
            Logger.error(f"버퍼 플러시 중 오류: {e} (consumer: {self.consumer_id})")
    
    async def _cleanup_empty_buffers(self):
        """빈 버퍼 정리 - 메모리 누수 방지 및 성능 최적화"""
        try:
            before_count = len(self.message_buffer)
            keys_to_remove = []
            
            for shard_key in self.message_buffer:
                if not self.message_buffer[shard_key]:  # 빈 리스트 확인
                    keys_to_remove.append(shard_key)
            
            # 빈 버퍼 제거
            for key in keys_to_remove:
                del self.message_buffer[key]
            
            if keys_to_remove:
                after_count = len(self.message_buffer)
                Logger.debug(f"버퍼 정리 완료: {before_count}개 → {after_count}개 (제거: {len(keys_to_remove)}개, consumer: {self.consumer_id})")
            
            # 전체 버퍼 상태 로깅 (디버깅용)
            if self.message_buffer:
                total_messages = sum(len(messages) for messages in self.message_buffer.values())
                Logger.debug(f"현재 버퍼 상태: {len(self.message_buffer)}개 샤드, 총 {total_messages}개 메시지 대기 중 (consumer: {self.consumer_id})")
                
        except Exception as e:
            Logger.error(f"버퍼 정리 중 오류: {e} (consumer: {self.consumer_id})")


# QueueService에 등록할 헬퍼 함수
async def register_chat_persistence_consumer():
    """채팅 영속성 컨슈머를 QueueService에 등록
    
    main.py에서 호출될 함수
    ServiceContainer를 통한 안전한 서비스 접근
    멀티 프로세스 환경에서 고유한 컨슈머 ID 자동 생성
    """
    try:
        # ServiceContainer를 통한 서비스 상태 확인
        service_status = ServiceContainer.get_service_status()
        
        required_services = ['queue', 'database', 'lock', 'scheduler']
        missing_services = []
        
        for service in required_services:
            if not service_status.get(service, False):
                missing_services.append(service)
        
        if missing_services:
            Logger.error(f"필요한 서비스가 초기화되지 않았습니다: {missing_services}")
            return False
        
        # QueueService 가져오기
        from service.queue.queue_service import get_queue_service
        queue_service = get_queue_service()
        
        # 컨슈머 생성 (고유한 ID 자동 생성)
        consumer = ChatPersistenceConsumer()
        
        # QueueService에 컨슈머 등록 (partition_key로 순서 보장)
        await queue_service.register_message_consumer(
            queue_name="chat_persistence",
            consumer_id=consumer.consumer_id,  # 고유한 컨슈머 ID 사용
            handler=consumer.handle_message
        )
        
        # 컨슈머 시작
        await consumer.start()
        
        Logger.info(f"채팅 영속성 컨슈머 등록 및 시작 완료: {consumer.consumer_id}")
        return True
        
    except Exception as e:
        Logger.error(f"채팅 영속성 컨슈머 등록 실패: {e}")
        return False