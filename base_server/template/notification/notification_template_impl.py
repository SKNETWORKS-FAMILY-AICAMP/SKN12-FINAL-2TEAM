from template.base.base_template import BaseTemplate
from template.notification.common.notification_serialize import (
    NotificationListRequest, NotificationListResponse,
    NotificationMarkReadRequest, NotificationMarkReadResponse,
    NotificationCreateAlertRequest, NotificationCreateAlertResponse,
    NotificationAlertListRequest, NotificationAlertListResponse,
    NotificationDeleteAlertRequest, NotificationDeleteAlertResponse
)
from service.core.logger import Logger
from service.service_container import ServiceContainer
import json
import uuid
from datetime import datetime, timedelta

class NotificationTemplateImpl(BaseTemplate):
    def __init__(self):
        super().__init__()
    
    async def on_notification_list_req(self, client_session, request: NotificationListRequest):
        """알림 목록 조회 요청 처리"""
        response = NotificationListResponse()
        
        Logger.info(f"Notification list request: type_filter={request.type_filter}")
        
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            db_service = ServiceContainer.get_database_service()
            
            # TODO: 알림 목록 조회 로직 구현
            # - 사용자별 알림 데이터 조회
            # - 타입별 필터링
            # - 읽음/안읽음 상태 관리
            # - 페이지네이션
            
            # 알림 목록 조회
            notifications_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_get_user_notifications",
                (account_db_key, request.type_filter, request.page, request.limit, request.include_read)
            )
            
            # 알림 가데이터 응답
            response.notifications = [
                {
                    "notification_id": f"notif_{account_db_key}_1",
                    "type": "PRICE_ALERT",
                    "title": "AAPL 가격 알림",
                    "message": "AAPL 주가가 $150을 넘었습니다",
                    "symbol": "AAPL",
                    "price": 152.0,
                    "is_read": False,
                    "created_at": str(datetime.now()),
                    "priority": "HIGH"
                },
                {
                    "notification_id": f"notif_{account_db_key}_2",
                    "type": "NEWS",
                    "title": "뉴스 알림",
                    "message": "Apple이 새로운 제품을 발표했습니다",
                    "symbol": "AAPL",
                    "price": None,
                    "is_read": True,
                    "created_at": str(datetime.now() - timedelta(hours=2)),
                    "priority": "MEDIUM"
                }
            ]
            response.total_count = 2
            response.unread_count = 1
            response.has_more = False
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            response.notifications = []
            response.total_count = 0
            response.unread_count = 0
            response.has_more = False
            Logger.error(f"Notification list error: {e}")
        
        return response

    async def on_notification_mark_read_req(self, client_session, request: NotificationMarkReadRequest):
        """알림 읽음 처리 요청 처리"""
        response = NotificationMarkReadResponse()
        
        Logger.info(f"Notification mark read request: count={len(request.notification_ids)}")
        
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            db_service = ServiceContainer.get_database_service()
            
            # TODO: 알림 읽음 처리 로직 구현
            # - 대량 업데이트 처리
            # - 읽음 시간 기록
            # - 알림 카운터 업데이트
            
            # 알림 읽음 처리
            updated_count = 0
            for notification_id in request.notification_ids:
                result = await db_service.call_shard_procedure(
                    shard_id,
                    "fp_mark_notification_read",
                    (notification_id, account_db_key)
                )
                if result:
                    updated_count += 1
            
            # 읽음 처리 이력 저장
            await db_service.call_shard_procedure(
                shard_id,
                "fp_save_notification_read_log",
                (account_db_key, json.dumps(request.notification_ids), updated_count)
            )
            
            response.updated_count = updated_count
            response.remaining_unread = 5  # 가데이터
            response.message = "알림이 읽음 처리되었습니다"
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            response.updated_count = 0
            response.remaining_unread = 0
            response.message = "알림 읽음 처리 실패"
            Logger.error(f"Notification mark read error: {e}")
        
        return response

    async def on_notification_create_alert_req(self, client_session, request: NotificationCreateAlertRequest):
        """가격 알림 생성 요청 처리"""
        response = NotificationCreateAlertResponse()
        
        Logger.info(f"Notification create alert request: symbol={request.symbol}")
        
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            db_service = ServiceContainer.get_database_service()
            
            # TODO: 가격 알림 생성 로직 구현
            # - 알림 조건 검증
            # - 중복 알림 방지
            # - 알림 트리거 설정
            # - 알림 방식 설정
            
            # 알림 ID 생성
            alert_id = f"alert_{uuid.uuid4().hex[:16]}"
            
            # 가격 알림 생성
            await db_service.call_shard_procedure(
                shard_id,
                "fp_create_price_alert",
                (
                    alert_id, account_db_key, request.symbol, request.alert_type,
                    request.target_price, request.condition, request.notification_methods,
                    request.is_repeatable, request.expires_at
                )
            )
            
            # 알림 생성 이력 저장
            await db_service.call_shard_procedure(
                shard_id,
                "fp_save_alert_creation_log",
                (account_db_key, alert_id, request.symbol, request.target_price)
            )
            
            response.alert_id = alert_id
            response.estimated_trigger_time = str(datetime.now() + timedelta(hours=1))  # 가데이터
            response.current_price = 150.0  # 가데이터
            response.price_difference = abs(request.target_price - 150.0) if request.target_price else 0.0
            response.message = "가격 알림이 생성되었습니다"
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            response.alert_id = ""
            response.estimated_trigger_time = ""
            response.current_price = 0.0
            response.price_difference = 0.0
            response.message = "가격 알림 생성 실패"
            Logger.error(f"Notification create alert error: {e}")
        
        return response

    async def on_notification_alert_list_req(self, client_session, request: NotificationAlertListRequest):
        """알림 설정 목록 요청 처리"""
        response = NotificationAlertListResponse()
        
        Logger.info(f"Notification alert list request: symbol={request.symbol}")
        
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            db_service = ServiceContainer.get_database_service()
            
            # TODO: 알림 설정 목록 조회 로직 구현
            # - 사용자별 알림 설정 조회
            # - 종목별 필터링
            # - 상태별 정렬
            # - 알림 트리거 상태 확인
            
            # 알림 설정 목록 조회
            alerts_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_get_user_alerts",
                (account_db_key, request.symbol, request.status, request.page, request.limit)
            )
            
            # 알림 설정 가데이터 응답
            response.alerts = [
                {
                    "alert_id": f"alert_{account_db_key}_1",
                    "symbol": "AAPL",
                    "alert_type": "PRICE_ABOVE",
                    "target_price": 160.0,
                    "current_price": 152.0,
                    "condition": "ABOVE",
                    "status": "ACTIVE",
                    "notification_methods": ["EMAIL", "PUSH"],
                    "is_repeatable": False,
                    "created_at": str(datetime.now() - timedelta(days=1)),
                    "triggered_count": 0,
                    "last_triggered_at": None
                },
                {
                    "alert_id": f"alert_{account_db_key}_2",
                    "symbol": "GOOGL",
                    "alert_type": "PRICE_BELOW",
                    "target_price": 230.0,
                    "current_price": 240.0,
                    "condition": "BELOW",
                    "status": "ACTIVE",
                    "notification_methods": ["PUSH"],
                    "is_repeatable": True,
                    "created_at": str(datetime.now() - timedelta(days=3)),
                    "triggered_count": 2,
                    "last_triggered_at": str(datetime.now() - timedelta(hours=6))
                }
            ]
            response.total_count = 2
            response.active_count = 2
            response.triggered_count = 0
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            response.alerts = []
            response.total_count = 0
            response.active_count = 0
            response.triggered_count = 0
            Logger.error(f"Notification alert list error: {e}")
        
        return response

    async def on_notification_delete_alert_req(self, client_session, request: NotificationDeleteAlertRequest):
        """알림 삭제 요청 처리"""
        response = NotificationDeleteAlertResponse()
        
        Logger.info(f"Notification delete alert request: count={len(request.alert_ids)}")
        
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            db_service = ServiceContainer.get_database_service()
            
            # TODO: 알림 삭제 로직 구현
            # - 삭제 권한 확인
            # - 삭제 가능 상태 확인
            # - 소프트 삭제 (이력 보존)
            # - 관련 알림 데이터 정리
            
            # 알림 삭제 처리
            deleted_count = 0
            failed_alerts = []
            
            for alert_id in request.alert_ids:
                try:
                    result = await db_service.call_shard_procedure(
                        shard_id,
                        "fp_delete_user_alert",
                        (alert_id, account_db_key, request.permanent_delete or False)
                    )
                    if result:
                        deleted_count += 1
                    else:
                        failed_alerts.append(alert_id)
                except Exception as e:
                    failed_alerts.append(alert_id)
                    Logger.warning(f"Failed to delete alert {alert_id}: {e}")
            
            # 삭제 이력 저장
            await db_service.call_shard_procedure(
                shard_id,
                "fp_save_alert_deletion_log",
                (account_db_key, json.dumps(request.alert_ids), deleted_count, json.dumps(failed_alerts))
            )
            
            response.deleted_count = deleted_count
            response.failed_count = len(failed_alerts)
            response.failed_alert_ids = failed_alerts
            response.remaining_alerts = 5  # 가데이터
            
            if deleted_count == len(request.alert_ids):
                response.message = "모든 알림이 삭제되었습니다"
            elif deleted_count > 0:
                response.message = f"{deleted_count}개 알림이 삭제되었습니다 ({len(failed_alerts)}개 실패)"
            else:
                response.message = "알림 삭제에 실패했습니다"
            
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            response.deleted_count = 0
            response.failed_count = len(request.alert_ids)
            response.failed_alert_ids = request.alert_ids
            response.remaining_alerts = 0
            response.message = "알림 삭제 실패"
            Logger.error(f"Notification delete alert error: {e}")
        
        return response