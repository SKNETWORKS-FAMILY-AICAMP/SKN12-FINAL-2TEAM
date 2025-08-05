"""
알림 메시지 DB 저장 및 멀티채널 발송 컨슈머

NotificationService Queue → Consumer → DB/SMS/Email/WebSocket 아키텍처 구현
- Partition Key로 메시지 수신 순서 보장
- Lock Service로 DB 저장 순서 보장
- Scheduler를 통한 배치 처리
- ServiceContainer를 통한 전역 서비스 관리
- shard_id 활용으로 정확한 샤드 라우팅
- 멀티 프로세스 환경 대응
- 효율적인 버퍼 관리로 메모리 최적화
- 멀티채널 알림 발송 (인앱, SMS, 이메일, WebSocket)
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
from service.notification.notification_config import NotificationChannel


class NotificationPersistenceConsumer:
    """알림 메시지 DB 저장 및 멀티채널 발송 컨슈머
    
    NotificationService Queue → Consumer → DB/SMS/Email/WebSocket 아키텍처 구현
    - NotificationService 큐에서 알림 메시지 이벤트 수신 (Partition Key로 순서 보장)
    - Lock Service로 DB 저장 순서 보장
    - SchedulerService를 통해 배치 처리
    - shard_id 기반 정확한 샤드 DB 접근
    - 멀티 프로세스 환경에서 고유한 컨슈머 ID 생성
    - 효율적인 버퍼 관리로 메모리 누수 방지
    - 멀티채널 알림 발송 (인앱, SMS, 이메일, WebSocket)
    """
    
    def __init__(self):
        # 멀티 프로세스 환경에서 고유한 컨슈머 ID 생성
        self.consumer_id = f"notification_persistence_{uuid.uuid4().hex[:8]}_pid_{os.getpid()}"
        
        self.batch_size = 50  # 배치당 최대 메시지 수
        self.batch_interval = 3  # 3초마다 배치 처리
        self.message_buffer: Dict[str, List[Dict]] = {}  # shard_key별 버퍼
        self._running = False
        self._lock_timeout = 10  # Lock 획득 타임아웃 (초)
        self._lock_ttl = 30  # Lock TTL (초)
        
        # 스케줄러 작업 ID도 고유하게 생성
        self.batch_job_id = f"notification_batch_save_{uuid.uuid4().hex[:8]}"
        self.cleanup_job_id = f"notification_buffer_cleanup_{uuid.uuid4().hex[:8]}"
        
        Logger.info(f"NotificationPersistenceConsumer 생성: consumer_id={self.consumer_id}")
        
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
                name=f"알림 메시지 배치 저장 ({self.consumer_id})",
                schedule_type=ScheduleType.INTERVAL,
                schedule_value=self.batch_interval,
                callback=self._process_batch,
                max_retries=3
            )
            await SchedulerService.add_job(batch_job)
            Logger.info(f"알림 배치 저장 스케줄러 등록 완료: {self.batch_job_id}")
            
            # 버퍼 정리 스케줄러 등록 (고유한 job_id 사용)
            cleanup_job = ScheduleJob(
                job_id=self.cleanup_job_id,  # 고유한 작업 ID
                name=f"알림 버퍼 정리 ({self.consumer_id})",
                schedule_type=ScheduleType.INTERVAL,
                schedule_value=30,
                callback=self._cleanup_empty_buffers,
                max_retries=1
            )
            await SchedulerService.add_job(cleanup_job)
            Logger.info(f"알림 버퍼 정리 스케줄러 등록 완료: {self.cleanup_job_id}")
            
            self._running = True
            Logger.info(f"NotificationPersistenceConsumer 시작: {self.consumer_id}")
            
        except Exception as e:
            Logger.error(f"NotificationPersistenceConsumer 시작 실패: {e}")
            raise
    
    async def stop(self):
        """컨슈머 종료"""
        try:
            self._running = False
            
            # 스케줄러 작업 제거
            if ServiceContainer.is_scheduler_service_initialized():
                try:
                    await SchedulerService.remove_job(self.batch_job_id)
                    Logger.info(f"알림 배치 스케줄러 제거 완료: {self.batch_job_id}")
                except Exception as e:
                    Logger.warn(f"알림 배치 스케줄러 제거 실패: {e}")
                
                try:
                    await SchedulerService.remove_job(self.cleanup_job_id)
                    Logger.info(f"알림 정리 스케줄러 제거 완료: {self.cleanup_job_id}")
                except Exception as e:
                    Logger.warn(f"알림 정리 스케줄러 제거 실패: {e}")
            
            # 남은 버퍼 데이터 처리
            if self.message_buffer:
                Logger.info(f"남은 버퍼 데이터 처리 중: {len(self.message_buffer)}개 샤드")
                await self._process_batch()
            
            self.message_buffer.clear()
            Logger.info(f"NotificationPersistenceConsumer 종료: {self.consumer_id}")
            
        except Exception as e:
            Logger.error(f"NotificationPersistenceConsumer 종료 실패: {e}")
    
    async def handle_message(self, message: QueueMessage):
        """알림 메시지 처리"""
        if not self._running:
            Logger.warn("컨슈머가 실행 중이 아님, 메시지 무시")
            return
        
        try:
            # 메시지 파싱
            data = json.loads(message.body) if isinstance(message.body, str) else message.body
            notification_data = data.get('notification', {})
            channel = data.get('channel', NotificationChannel.IN_APP.value)
            account_db_key = data.get('account_db_key')
            shard_id = data.get('shard_id')
            
            if not account_db_key or not shard_id:
                Logger.error(f"필수 파라미터 누락: account_db_key={account_db_key}, shard_id={shard_id}")
                return
            
            # 샤드별 버퍼에 추가
            shard_key = f"shard_{shard_id}"
            if shard_key not in self.message_buffer:
                self.message_buffer[shard_key] = []
            
            # 메시지 데이터 구성
            message_data = {
                'notification': notification_data,
                'channel': channel,
                'account_db_key': account_db_key,
                'shard_id': shard_id,
                'timestamp': datetime.now().isoformat(),
                'message_id': message.message_id,
                'partition_key': message.partition_key
            }
            
            self.message_buffer[shard_key].append(message_data)
            
            # 배치 크기 도달 시 즉시 처리
            if len(self.message_buffer[shard_key]) >= self.batch_size:
                await self._process_shard_batch(shard_key, shard_id)
            
            Logger.debug(f"알림 메시지 버퍼 추가: shard={shard_id}, user={account_db_key}, channel={channel}")
            
        except Exception as e:
            Logger.error(f"알림 메시지 처리 실패: {e}")
            import traceback
            Logger.error(f"Traceback: {traceback.format_exc()}")
    
    async def _process_batch(self):
        """모든 샤드의 배치 처리"""
        if not self.message_buffer:
            return
        
        try:
            # 각 샤드별로 처리
            for shard_key in list(self.message_buffer.keys()):
                if self.message_buffer[shard_key]:
                    shard_id = int(shard_key.replace('shard_', ''))
                    await self._process_shard_batch(shard_key, shard_id)
            
        except Exception as e:
            Logger.error(f"배치 처리 실패: {e}")
    
    async def _process_shard_batch(self, shard_key: str, shard_id: int):
        """특정 샤드의 배치 처리"""
        if not self.message_buffer.get(shard_key):
            return
        
        # 분산 락 키 설정
        lock_key = f"notification_save_shard_{shard_id}"
        
        try:
            # 분산 락 획득
            lock_service = ServiceContainer.get_lock_service()
            async with lock_service.acquire_lock(
                lock_key, 
                timeout=self._lock_timeout, 
                ttl=self._lock_ttl
            ) as acquired:
                
                if not acquired:
                    Logger.warn(f"분산 락 획득 실패: {lock_key}")
                    return
                
                # 현재 배치 복사 후 버퍼 클리어
                current_batch = self.message_buffer[shard_key][:]
                self.message_buffer[shard_key].clear()
                
                if not current_batch:
                    return
                
                Logger.info(f"알림 배치 처리 시작: shard={shard_id}, count={len(current_batch)}")
                
                # 채널별로 그룹화
                channel_groups = {}
                for msg_data in current_batch:
                    channel = msg_data['channel']
                    if channel not in channel_groups:
                        channel_groups[channel] = []
                    channel_groups[channel].append(msg_data)
                
                # 각 채널별 처리
                success_count = 0
                for channel, messages in channel_groups.items():
                    try:
                        if channel == NotificationChannel.IN_APP.value:
                            # 인앱 알림 - DB 저장
                            db_success = await self._save_inapp_notifications(shard_id, messages)
                            if db_success:
                                success_count += len(messages)
                        
                        elif channel == NotificationChannel.EMAIL.value:
                            # 이메일 발송
                            email_success = await self._send_email_notifications(messages)
                            if email_success:
                                success_count += len(messages)
                        
                        elif channel == NotificationChannel.SMS.value:
                            # SMS 발송
                            sms_success = await self._send_sms_notifications(messages)
                            if sms_success:
                                success_count += len(messages)
                        
                        elif channel == NotificationChannel.PUSH.value:
                            # Push 알림 (향후 구현)
                            Logger.info(f"Push 알림 처리 (미구현): {len(messages)}개 메시지")
                            success_count += len(messages)  # 임시로 성공 처리
                        
                        elif channel == NotificationChannel.WEBSOCKET.value:
                            # WebSocket 실시간 알림
                            websocket_success = await self._send_websocket_notifications(messages)
                            if websocket_success:
                                success_count += len(messages)
                        
                        else:
                            Logger.warn(f"알 수 없는 채널: {channel}")
                    
                    except Exception as e:
                        Logger.error(f"채널 {channel} 처리 실패: {e}")
                        continue
                
                Logger.info(f"알림 배치 처리 완료: shard={shard_id}, success={success_count}/{len(current_batch)}")
                
        except Exception as e:
            Logger.error(f"샤드 {shard_id} 배치 처리 실패: {e}")
            # 실패한 메시지들을 다시 버퍼에 추가 (재처리용)
            if shard_key in self.message_buffer:
                self.message_buffer[shard_key].extend(current_batch)
    
    async def _save_inapp_notifications(self, shard_id: int, messages: List[Dict]) -> bool:
        """인앱 알림 DB 저장"""
        try:
            database_service = ServiceContainer.get_database_service()
            success_count = 0
            
            for msg_data in messages:
                try:
                    notification = msg_data['notification']
                    account_db_key = msg_data['account_db_key']
                    
                    # 알림 ID 생성
                    notification_id = str(uuid.uuid4())
                    
                    # 알림 저장 프로시저 호출
                    result = await database_service.execute_shard_procedure_by_shard_id(
                        shard_id,
                        "fp_notification_save",
                        (
                            notification_id,
                            account_db_key,
                            notification.get('type', 'PREDICTION_ALERT'),
                            notification.get('title', ''),
                            notification.get('message', ''),
                            json.dumps(notification.get('data', {})),
                            notification.get('priority', 3),
                            0,  # is_read = 0 (읽지 않음)
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        )
                    )
                    
                    if result and result[0].get('ErrorCode') == 0:
                        success_count += 1
                        Logger.debug(f"인앱 알림 저장 성공: user={account_db_key}, id={notification_id}")
                    else:
                        error_msg = result[0].get('ErrorMessage', 'Unknown error') if result else 'No result'
                        Logger.error(f"인앱 알림 저장 실패: user={account_db_key}, error={error_msg}")
                
                except Exception as e:
                    Logger.error(f"개별 인앱 알림 저장 실패: {e}")
                    continue
            
            Logger.info(f"인앱 알림 저장 완료: shard={shard_id}, success={success_count}/{len(messages)}")
            return success_count > 0
            
        except Exception as e:
            Logger.error(f"인앱 알림 배치 저장 실패: {e}")
            return False
    
    async def _send_email_notifications(self, messages: List[Dict]) -> bool:
        """이메일 알림 발송"""
        try:
            email_service = ServiceContainer.get_email_service()
            if not email_service.is_initialized():
                Logger.warn("EmailService가 초기화되지 않음, 이메일 발송 건너뜀")
                return True  # 서비스 없음으로 인한 실패는 성공으로 처리
            
            database_service = ServiceContainer.get_database_service()
            success_count = 0
            
            for msg_data in messages:
                try:
                    notification = msg_data['notification']
                    account_db_key = msg_data['account_db_key']
                    
                    # 사용자 연락처 정보 조회
                    contact_result = await database_service.execute_global_procedure(
                        "fp_get_user_contact_info",
                        (account_db_key,)
                    )
                    
                    if not contact_result or len(contact_result) < 2:
                        Logger.warn(f"사용자 연락처 조회 실패: account_db_key={account_db_key}")
                        continue
                    
                    contact_info = contact_result[1]
                    email = contact_info.get('email')
                    nickname = contact_info.get('nickname', '고객')
                    
                    if not email:
                        Logger.warn(f"이메일 주소 없음: account_db_key={account_db_key}")
                        continue
                    
                    # 이메일 발송
                    success = await email_service.send_email(
                        to_email=email,
                        subject=notification.get('title', '알림'),
                        content=f"안녕하세요 {nickname}님,\n\n{notification.get('message', '')}\n\n감사합니다.",
                        content_type='text/plain'
                    )
                    
                    if success:
                        success_count += 1
                        Logger.debug(f"이메일 발송 성공: {email}")
                    else:
                        Logger.error(f"이메일 발송 실패: {email}")
                
                except Exception as e:
                    Logger.error(f"개별 이메일 발송 실패: {e}")
                    continue
            
            Logger.info(f"이메일 발송 완료: success={success_count}/{len(messages)}")
            return success_count > 0
            
        except Exception as e:
            Logger.error(f"이메일 배치 발송 실패: {e}")
            return False
    
    async def _send_sms_notifications(self, messages: List[Dict]) -> bool:
        """SMS 알림 발송"""
        try:
            sms_service = ServiceContainer.get_sms_service()
            if not sms_service.is_initialized():
                Logger.warn("SMSService가 초기화되지 않음, SMS 발송 건너뜀")
                return True  # 서비스 없음으로 인한 실패는 성공으로 처리
            
            database_service = ServiceContainer.get_database_service()
            success_count = 0
            
            for msg_data in messages:
                try:
                    notification = msg_data['notification']
                    account_db_key = msg_data['account_db_key']
                    
                    # 사용자 연락처 정보 조회
                    contact_result = await database_service.execute_global_procedure(
                        "fp_get_user_contact_info",
                        (account_db_key,)
                    )
                    
                    if not contact_result or len(contact_result) < 2:
                        Logger.warn(f"사용자 연락처 조회 실패: account_db_key={account_db_key}")
                        continue
                    
                    contact_info = contact_result[1]
                    phone_number = contact_info.get('phone_number')
                    
                    if not phone_number:
                        Logger.warn(f"전화번호 없음: account_db_key={account_db_key}")
                        continue
                    
                    # SMS 발송 (메시지 길이 제한)
                    sms_message = notification.get('message', '')[:100]  # 100자 제한
                    success = await sms_service.send_sms(
                        to_phone=phone_number,
                        message=sms_message
                    )
                    
                    if success:
                        success_count += 1
                        Logger.debug(f"SMS 발송 성공: {phone_number}")
                    else:
                        Logger.error(f"SMS 발송 실패: {phone_number}")
                
                except Exception as e:
                    Logger.error(f"개별 SMS 발송 실패: {e}")
                    continue
            
            Logger.info(f"SMS 발송 완료: success={success_count}/{len(messages)}")
            return success_count > 0
            
        except Exception as e:
            Logger.error(f"SMS 배치 발송 실패: {e}")
            return False
    
    async def _send_websocket_notifications(self, messages: List[Dict]) -> bool:
        """WebSocket 실시간 알림 발송"""
        try:
            websocket_service = ServiceContainer.get_websocket_service()
            if not websocket_service.is_initialized():
                Logger.warn("WebSocketService가 초기화되지 않음, WebSocket 발송 건너뜀")
                return True  # 서비스 없음으로 인한 실패는 성공으로 처리
            
            success_count = 0
            
            for msg_data in messages:
                try:
                    notification = msg_data['notification']
                    account_db_key = msg_data['account_db_key']
                    
                    # WebSocket 메시지 구성
                    websocket_message = {
                        'type': 'notification',
                        'data': {
                            'id': str(uuid.uuid4()),
                            'title': notification.get('title', ''),
                            'message': notification.get('message', ''),
                            'type': notification.get('type', 'PREDICTION_ALERT'),
                            'priority': notification.get('priority', 3),
                            'data': notification.get('data', {}),
                            'timestamp': datetime.now().isoformat()
                        }
                    }
                    
                    # 사용자별 WebSocket 연결에 메시지 전송
                    success = await websocket_service.send_to_user(
                        user_id=str(account_db_key),
                        message=websocket_message
                    )
                    
                    if success:
                        success_count += 1
                        Logger.debug(f"WebSocket 발송 성공: user={account_db_key}")
                    else:
                        Logger.debug(f"WebSocket 발송 실패 (연결 없음): user={account_db_key}")
                
                except Exception as e:
                    Logger.error(f"개별 WebSocket 발송 실패: {e}")
                    continue
            
            Logger.info(f"WebSocket 발송 완료: success={success_count}/{len(messages)}")
            return success_count > 0
            
        except Exception as e:
            Logger.error(f"WebSocket 배치 발송 실패: {e}")
            return False
    
    async def _cleanup_empty_buffers(self):
        """빈 버퍼 정리"""
        try:
            empty_keys = [key for key, buffer in self.message_buffer.items() if not buffer]
            for key in empty_keys:
                del self.message_buffer[key]
            
            if empty_keys:
                Logger.debug(f"빈 버퍼 정리 완료: {len(empty_keys)}개")
                
        except Exception as e:
            Logger.error(f"버퍼 정리 실패: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """컨슈머 상태 조회"""
        return {
            'consumer_id': self.consumer_id,
            'running': self._running,
            'batch_size': self.batch_size,
            'batch_interval': self.batch_interval,
            'buffer_shards': len(self.message_buffer),
            'total_buffered_messages': sum(len(buffer) for buffer in self.message_buffer.values()),
            'buffer_details': {
                shard_key: len(buffer) 
                for shard_key, buffer in self.message_buffer.items()
            }
        }


# QueueService에 등록할 헬퍼 함수
async def register_notification_persistence_consumer():
    """알림 영속성 컨슈머를 QueueService에 등록
    
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
        consumer = NotificationPersistenceConsumer()
        
        # QueueService에 컨슈머 등록 (partition_key로 순서 보장)
        await queue_service.register_message_consumer(
            queue_name="notification_persistence",
            consumer_id=consumer.consumer_id,  # 고유한 컨슈머 ID 사용
            handler=consumer.handle_message
        )
        
        # 컨슈머 시작
        await consumer.start()
        
        Logger.info(f"알림 영속성 컨슈머 등록 및 시작 완료: {consumer.consumer_id}")
        return True
        
    except Exception as e:
        Logger.error(f"알림 영속성 컨슈머 등록 실패: {e}")
        import traceback
        Logger.error(f"Traceback: {traceback.format_exc()}")
        return False