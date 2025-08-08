from template.base.base_template import BaseTemplate
from template.notification.common.notification_serialize import (
    NotificationListRequest, NotificationListResponse,
    NotificationMarkReadRequest, NotificationMarkReadResponse,
    NotificationMarkAllReadRequest, NotificationMarkAllReadResponse,
    NotificationDeleteRequest, NotificationDeleteResponse,
    NotificationStatsRequest, NotificationStatsResponse,
    NotificationCreateRequest, NotificationCreateResponse
)
from template.notification.common.notification_model import (
    InAppNotification, NotificationStats, NotificationType, NotificationPriority
)
from service.core.logger import Logger
from service.service_container import ServiceContainer
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

class NotificationTemplateImpl(BaseTemplate):
    def __init__(self):
        super().__init__()
    
    # ========================================
    # 알림 목록 조회 (게임 패턴 - 읽은 알림 조회 시 자동 삭제)
    # ========================================
    async def on_notification_list_req(self, client_session, request: NotificationListRequest):
        """인앱 알림 목록 조회 요청 처리"""
        response = NotificationListResponse()
        response.sequence = request.sequence
        
        try:
            account_db_key = getattr(client_session.session, 'account_db_key', 0)
            shard_id = getattr(client_session.session, 'shard_id', 1)
            
            Logger.info(f"인앱 알림 목록 조회: account={account_db_key}, filter={request.read_filter}, type={request.type_id}")
            
            database_service = ServiceContainer.get_database_service()
            
            # 페이징 처리
            limit = request.limit if request.limit > 0 else 20
            offset = (request.page - 1) * limit if request.page > 0 else 0
            
            # 1. 적절한 프로시저 선택 (읽음 상태에 따라)
            if request.read_filter == "read_only":
                # 읽은 알림만 조회 + 자동 삭제 (게임 패턴)
                procedure_name = "fp_inapp_notifications_get_read_and_delete"
                Logger.info(f"게임 패턴: 읽은 알림 조회 + 자동 삭제")
            elif request.read_filter == "unread_only":
                # 읽지 않은 알림만 조회 (기본값)
                procedure_name = "fp_inapp_notifications_get_unread"
            else:  # "all"
                # 전체 알림 조회 (읽음/안읽음 모두)
                procedure_name = "fp_inapp_notifications_get_all"
            
            # 2. 알림 목록 조회
            db_result = await database_service.call_shard_procedure(
                shard_id,
                procedure_name,
                (account_db_key, request.type_id, limit, offset)
            )
            
            if not db_result:
                response.notifications = []
                response.total_count = 0
                response.unread_count = 0
                response.has_more = False
                response.errorCode = 0
                return response
            
            # 3. 결과 처리 (채팅 패턴과 동일)
            notifications = []
            for row in db_result:
                try:
                    data_json = json.loads(row.get('data', '{}')) if row.get('data') else {}
                    
                    notification = InAppNotification(
                        idx=int(row.get('idx', 0)),
                        notification_id=str(row.get('notification_id', '')),
                        account_db_key=int(row.get('account_db_key', 0)),
                        type_id=str(row.get('type_id', '')),
                        title=str(row.get('title', '')),
                        message=str(row.get('message', '')),
                        data=data_json,
                        priority=int(row.get('priority', 3)),
                        is_read=bool(row.get('is_read', 0)),
                        read_at=row.get('read_at').isoformat() if row.get('read_at') else None,
                        expires_at=row.get('expires_at').isoformat() if row.get('expires_at') else None,
                        created_at=row.get('created_at').isoformat() if row.get('created_at') else '',
                        updated_at=row.get('updated_at').isoformat() if row.get('updated_at') else ''
                    )
                    
                    notifications.append(notification)
                    
                except Exception as parse_error:
                    Logger.warn(f"알림 파싱 오류 (건너뜀): {parse_error}")
                    continue
            
            # 4. 통계 조회 (현재 미읽은 알림 수)
            unread_count = 0
            if request.read_filter != "read_only":  # 읽은 알림 조회가 아닐 때만
                try:
                    stats_result = await database_service.call_shard_procedure(
                        shard_id,
                        "fp_inapp_notification_stats_get",
                        (account_db_key, 1)  # 최근 1일
                    )
                    
                    if stats_result:
                        # 마지막 행에서 current_unread_count 찾기
                        for row in stats_result:
                            if 'current_unread_count' in row:
                                unread_count = int(row.get('current_unread_count', 0))
                                break
                                
                except Exception as stats_error:
                    Logger.warn(f"통계 조회 실패: {stats_error}")
            
            response.notifications = notifications
            response.total_count = len(notifications)
            response.unread_count = unread_count
            response.has_more = len(notifications) >= limit
            response.errorCode = 0
            
            # 읽은 알림 자동 삭제 시 로그
            if request.read_filter == "read_only" and response.total_count > 0:
                Logger.info(f"게임 패턴: {response.total_count}개 읽은 알림 자동 삭제 완료 (user={account_db_key})")
            
        except Exception as e:
            response.errorCode = 1000
            response.notifications = []
            response.total_count = 0
            response.unread_count = 0
            response.has_more = False
            Logger.error(f"인앱 알림 목록 조회 오류: {e}")
        
        return response
    
    # ========================================
    # 알림 읽음 처리
    # ========================================
    async def on_notification_mark_read_req(self, client_session, request: NotificationMarkReadRequest):
        """알림 읽음 처리 요청"""
        response = NotificationMarkReadResponse()
        response.sequence = request.sequence
        
        try:
            account_db_key = getattr(client_session.session, 'account_db_key', 0)
            shard_id = getattr(client_session.session, 'shard_id', 1)
            
            Logger.info(f"알림 읽음 처리: account={account_db_key}, notification_id={request.notification_id}")
            
            database_service = ServiceContainer.get_database_service()
            
            # 알림 읽음 처리
            db_result = await database_service.call_shard_procedure(
                shard_id,
                "fp_inapp_notification_mark_read",
                (request.notification_id, account_db_key)
            )
            
            if not db_result:
                response.result = "FAILED"
                response.message = "알림 읽음 처리 실패"
                response.errorCode = 8001
                return response
            
            # 첫 번째 행의 결과 확인
            result_row = db_result[0] if db_result else {}
            db_result_status = result_row.get('result', 'FAILED')
            
            if db_result_status == 'SUCCESS':
                response.result = "SUCCESS"
                response.message = "알림이 읽음 처리되었습니다"
                response.errorCode = 0
            elif db_result_status == 'ALREADY_READ':
                response.result = "ALREADY_READ"
                response.message = "이미 읽은 알림입니다"
                response.errorCode = 0
            else:
                response.result = "FAILED"
                response.message = result_row.get('message', '알림 읽음 처리 실패')
                response.errorCode = 8002
            
        except Exception as e:
            response.result = "FAILED"
            response.message = "알림 읽음 처리 중 오류 발생"
            response.errorCode = 1000
            Logger.error(f"알림 읽음 처리 오류: {e}")
        
        return response
    
    # ========================================
    # 알림 일괄 읽음 처리
    # ========================================
    async def on_notification_mark_all_read_req(self, client_session, request: NotificationMarkAllReadRequest):
        """알림 일괄 읽음 처리 요청"""
        response = NotificationMarkAllReadResponse()
        response.sequence = request.sequence
        
        try:
            account_db_key = getattr(client_session.session, 'account_db_key', 0)
            shard_id = getattr(client_session.session, 'shard_id', 1)
            
            Logger.info(f"알림 일괄 읽음 처리: account={account_db_key}, type_id={request.type_id}")
            
            database_service = ServiceContainer.get_database_service()
            
            # 일괄 읽음 처리
            db_result = await database_service.call_shard_procedure(
                shard_id,
                "fp_inapp_notifications_mark_all_read",
                (account_db_key, request.type_id)
            )
            
            if not db_result:
                response.result = "FAILED"
                response.message = "일괄 읽음 처리 실패"
                response.updated_count = 0
                response.errorCode = 8003
                return response
            
            # 결과 처리
            result_row = db_result[0] if db_result else {}
            db_result_status = result_row.get('result', 'FAILED')
            
            if db_result_status == 'SUCCESS':
                updated_count = int(result_row.get('updated_count', 0))
                response.result = "SUCCESS"
                response.message = f"{updated_count}개 알림이 읽음 처리되었습니다"
                response.updated_count = updated_count
                response.errorCode = 0
            else:
                response.result = "FAILED"
                response.message = result_row.get('message', '일괄 읽음 처리 실패')
                response.updated_count = 0
                response.errorCode = 8004
            
        except Exception as e:
            response.result = "FAILED"
            response.message = "일괄 읽음 처리 중 오류 발생"
            response.updated_count = 0
            response.errorCode = 1000
            Logger.error(f"알림 일괄 읽음 처리 오류: {e}")
        
        return response
    
    # ========================================
    # 알림 삭제 (소프트 삭제)
    # ========================================
    async def on_notification_delete_req(self, client_session, request: NotificationDeleteRequest):
        """알림 삭제 요청"""
        response = NotificationDeleteResponse()
        response.sequence = request.sequence
        
        try:
            account_db_key = getattr(client_session.session, 'account_db_key', 0)
            shard_id = getattr(client_session.session, 'shard_id', 1)
            
            Logger.info(f"알림 삭제: account={account_db_key}, notification_id={request.notification_id}")
            
            database_service = ServiceContainer.get_database_service()
            
            # 알림 소프트 삭제
            db_result = await database_service.call_shard_procedure(
                shard_id,
                "fp_inapp_notification_soft_delete",
                (request.notification_id, account_db_key)
            )
            
            if not db_result:
                response.result = "FAILED"
                response.message = "알림 삭제 실패"
                response.errorCode = 8005
                return response
            
            # 결과 처리
            result_row = db_result[0] if db_result else {}
            db_result_status = result_row.get('result', 'FAILED')
            
            if db_result_status == 'SUCCESS':
                response.result = "SUCCESS"
                response.message = "알림이 삭제되었습니다"
                response.errorCode = 0
            else:
                response.result = "FAILED"
                response.message = result_row.get('message', '알림 삭제 실패')
                response.errorCode = 8006
            
        except Exception as e:
            response.result = "FAILED"
            response.message = "알림 삭제 중 오류 발생"
            response.errorCode = 1000
            Logger.error(f"알림 삭제 오류: {e}")
        
        return response
    
    # ========================================
    # 알림 통계 조회
    # ========================================
    async def on_notification_stats_req(self, client_session, request: NotificationStatsRequest):
        """알림 통계 조회 요청"""
        response = NotificationStatsResponse()
        response.sequence = request.sequence
        
        try:
            account_db_key = getattr(client_session.session, 'account_db_key', 0)
            shard_id = getattr(client_session.session, 'shard_id', 1)
            
            Logger.info(f"알림 통계 조회: account={account_db_key}, days={request.days}")
            
            database_service = ServiceContainer.get_database_service()
            
            # 통계 조회
            db_result = await database_service.call_shard_procedure(
                shard_id,
                "fp_inapp_notification_stats_get",
                (account_db_key, request.days)
            )
            
            if not db_result:
                response.daily_stats = []
                response.current_unread_count = 0
                response.errorCode = 0
                return response
            
            # 결과 처리 - 두 개의 결과셋
            daily_stats = []
            current_unread_count = 0
            
            # 첫 번째 결과셋: 일별 통계
            daily_result_found = False
            for row in db_result:
                if 'date' in row:  # 일별 통계 데이터
                    daily_result_found = True
                    try:
                        stat = NotificationStats(
                            date=str(row.get('date', '')),
                            total_count=int(row.get('total_count', 0)),
                            read_count=int(row.get('read_count', 0)),
                            unread_count=int(row.get('unread_count', 0)),
                            priority_1_count=int(row.get('priority_1_count', 0)),
                            priority_2_count=int(row.get('priority_2_count', 0)),
                            priority_3_count=int(row.get('priority_3_count', 0)),
                            auto_deleted_count=int(row.get('auto_deleted_count', 0))
                        )
                        daily_stats.append(stat)
                    except Exception as stat_error:
                        Logger.warn(f"통계 파싱 오류 (건너뜀): {stat_error}")
                        continue
                        
                elif 'current_unread_count' in row:  # 현재 미읽음 수
                    current_unread_count = int(row.get('current_unread_count', 0))
            
            response.daily_stats = daily_stats
            response.current_unread_count = current_unread_count
            response.errorCode = 0
            
        except Exception as e:
            response.daily_stats = []
            response.current_unread_count = 0
            response.errorCode = 1000
            Logger.error(f"알림 통계 조회 오류: {e}")
        
        return response
    
    # ========================================
    # 운영자 알림 생성 (OPERATOR 권한 필요)
    # ========================================
    async def on_notification_create_req(self, client_session, request: NotificationCreateRequest):
        """운영자 알림 생성 요청 (운영진용)"""
        response = NotificationCreateResponse()
        response.sequence = request.sequence
        
        try:
            # 운영자 권한 확인은 TemplateService.run_operator에서 이미 처리됨
            operator_account_key = getattr(client_session.session, 'account_db_key', 0)
            
            Logger.info(f"운영자 알림 생성: operator={operator_account_key}, target={request.target_type}, title={request.title}")
            
            database_service = ServiceContainer.get_database_service()
            
            # 대상 사용자 목록 결정
            target_users = []
            if request.target_type == "ALL":
                # 전체 사용자 - 프로시저에서 처리
                target_users = None
            elif request.target_type == "SPECIFIC_USER":
                target_users = request.target_users or []
                if not target_users:
                    response.notification_ids = []
                    response.created_count = 0
                    response.message = "특정 사용자 지정 시 target_users가 필요합니다"
                    response.errorCode = 9001
                    return response
            elif request.target_type == "USER_GROUP":
                # 사용자 그룹 (PREMIUM, FREE 등) - 프로시저에서 처리
                if not request.user_group:
                    response.notification_ids = []
                    response.created_count = 0
                    response.message = "사용자 그룹 지정 시 user_group이 필요합니다"
                    response.errorCode = 9002
                    return response
            
            # JSON 데이터 직렬화
            data_json = json.dumps(request.data) if request.data else None
            
            # 알림 생성 프로시저 호출
            db_result = await database_service.call_procedure(
                "fp_operator_notification_create",
                (
                    request.target_type,
                    json.dumps(target_users) if target_users else None,
                    request.user_group,
                    request.type_id,
                    request.title,
                    request.message,
                    data_json,
                    request.priority,
                    request.expires_at,
                    operator_account_key  # 생성자 기록용
                )
            )
            
            if not db_result:
                response.notification_ids = []
                response.created_count = 0
                response.message = "알림 생성 실패"
                response.errorCode = 9003
                return response
            
            # 결과 처리
            result_row = db_result[0] if db_result else {}
            db_result_status = result_row.get('result', 'FAILED')
            
            if db_result_status == 'SUCCESS':
                created_count = int(result_row.get('created_count', 0))
                notification_ids_str = result_row.get('notification_ids', '')
                
                # 생성된 알림 ID 목록 파싱
                notification_ids = []
                if notification_ids_str:
                    try:
                        notification_ids = json.loads(notification_ids_str)
                    except json.JSONDecodeError:
                        # JSON 파싱 실패 시 문자열 분리
                        notification_ids = [id.strip() for id in notification_ids_str.split(',') if id.strip()]
                
                response.notification_ids = notification_ids
                response.created_count = created_count
                response.message = f"{created_count}개 알림이 생성되었습니다"
                response.errorCode = 0
                
                Logger.info(f"운영자 알림 생성 성공: {created_count}개 생성")
                
            else:
                response.notification_ids = []
                response.created_count = 0
                response.message = result_row.get('message', '알림 생성 실패')
                response.errorCode = 9004
            
        except Exception as e:
            response.notification_ids = []
            response.created_count = 0
            response.message = "알림 생성 중 오류 발생"
            response.errorCode = 1000
            Logger.error(f"운영자 알림 생성 오류: {e}")
        
        return response
    
    # ========================================
