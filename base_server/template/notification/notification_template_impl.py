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
            
            # 1. 알림 목록 조회 DB 프로시저 호출
            notifications_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_get_notifications",
                (account_db_key, request.type_filter, 
                 "read" if request.include_read else "unread", 
                 request.page, request.limit)
            )
            
            if not notifications_result or len(notifications_result) < 2:
                response.notifications = []
                response.total_count = 0
                response.unread_count = 0
                response.has_more = False
                response.errorCode = 0
                return response
            
            # 2. DB 결과를 바탕으로 응답 생성
            notifications_data = notifications_result[0]
            count_data = notifications_result[1]
            
            response.notifications = []
            for notif in notifications_data:
                data_json = json.loads(notif.get('data', '{}'))
                response.notifications.append({
                    "notification_id": notif.get('notification_id'),
                    "type": notif.get('type'),
                    "title": notif.get('title'),
                    "message": notif.get('message'),
                    "symbol": data_json.get('symbol', ''),
                    "price": data_json.get('price'),
                    "is_read": bool(notif.get('is_read')),
                    "created_at": str(notif.get('created_at')),
                    "priority": notif.get('priority', 'NORMAL')
                })
            
            response.total_count = count_data.get('total_count', 0)
            response.unread_count = count_data.get('unread_count', 0)
            response.has_more = len(response.notifications) >= request.limit
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
            
            # 1. 알림 읽음 처리 DB 프로시저 호출
            mark_read_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_mark_notifications_read",
                (account_db_key, json.dumps(request.notification_ids))
            )
            
            if not mark_read_result or mark_read_result[0].get('result') != 'SUCCESS':
                response.errorCode = 8001
                response.updated_count = 0
                response.remaining_unread = 0
                response.message = "알림 읽음 처리 실패"
                return response
            
            # 2. 결과 데이터 처리
            updated_count = mark_read_result[0].get('updated_count', 0)
            
            # 3. 남은 안읽음 알림 수 조회
            remaining_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_get_notifications",
                (account_db_key, "ALL", "unread", 1, 1)  # 안읽음만 카운트
            )
            
            remaining_unread = 0
            if remaining_result and len(remaining_result) > 1:
                remaining_unread = remaining_result[1].get('unread_count', 0)
            
            response.updated_count = updated_count
            response.remaining_unread = remaining_unread
            response.message = f"{updated_count}개 알림이 읽음 처리되었습니다"
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
            
            # 1. 알림 조건 검증
            if not request.symbol or not request.target_price:
                response.errorCode = 8002
                response.message = "종목과 목표 가격을 입력해주세요"
                return response
            
            # 2. 현재 가격 조회 (시장 데이터에서)
            current_price_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_get_price_data",
                (json.dumps([request.symbol]), "1D", "1d")
            )
            
            current_price = 150.0  # 기본값
            if current_price_result and len(current_price_result) > 0:
                current_price = float(current_price_result[0].get('close_price', 150.0))
            
            # 3. 가격 알림 생성 DB 프로시저 호출
            create_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_create_price_alert",
                (account_db_key, request.symbol, request.alert_type,
                 request.target_price, request.message or f"{request.symbol} 가격 알림")
            )
            
            if not create_result or create_result[0].get('result') != 'SUCCESS':
                response.errorCode = 8003
                response.message = "가격 알림 생성 실패"
                return response
            
            # 4. 결과 데이터 처리
            alert_id = create_result[0].get('alert_id')
            price_difference = abs(request.target_price - current_price)
            
            # 5. 예상 트리거 시간 계산 (간단한 예시)
            trigger_hours = max(1, min(24, int(price_difference / current_price * 100)))  # 가격 차이에 비례
            estimated_trigger_time = datetime.now() + timedelta(hours=trigger_hours)
            
            response.alert_id = alert_id
            response.estimated_trigger_time = str(estimated_trigger_time)
            response.current_price = current_price
            response.price_difference = round(price_difference, 2)
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
            
            # 1. 알림 설정 목록 조회 DB 프로시저 호출
            # 먼저 사용자의 가격 알림 목록을 조회
            alerts_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_get_notifications",  # 가격 알림도 노티피케이션의 일종
                (account_db_key, "PRICE_ALERT", request.status or "ALL", request.page, request.limit)
            )
            
            if not alerts_result:
                response.alerts = []
                response.total_count = 0
                response.active_count = 0
                response.triggered_count = 0
                response.errorCode = 0
                return response
            
            # 2. 종목별 필터링 및 응답 데이터 구성
            alerts_data = alerts_result[0] if len(alerts_result) > 0 else []
            count_data = alerts_result[1] if len(alerts_result) > 1 else {}
            
            response.alerts = []
            active_count = 0
            triggered_count = 0
            
            for alert in alerts_data:
                # 종목 필터링 적용
                alert_data = json.loads(alert.get('data', '{}'))
                alert_symbol = alert_data.get('symbol', '')
                
                if request.symbol and request.symbol != alert_symbol:
                    continue
                
                alert_info = {
                    "alert_id": alert.get('notification_id'),  # 알림 ID는 노티피케이션 ID와 동일
                    "symbol": alert_symbol,
                    "alert_type": alert_data.get('alert_type', 'PRICE_ABOVE'),
                    "target_price": float(alert_data.get('target_price', 0)),
                    "current_price": float(alert_data.get('current_price', 0)),
                    "condition": alert_data.get('condition', 'ABOVE'),
                    "status": "ACTIVE" if not alert.get('is_read') else "TRIGGERED",
                    "notification_methods": alert_data.get('notification_methods', ['PUSH']),
                    "is_repeatable": alert_data.get('is_repeatable', False),
                    "created_at": str(alert.get('created_at')),
                    "triggered_count": alert_data.get('triggered_count', 0),
                    "last_triggered_at": alert_data.get('last_triggered_at')
                }
                
                response.alerts.append(alert_info)
                
                # 카운트 집계
                if not alert.get('is_read'):
                    active_count += 1
                if alert_data.get('triggered_count', 0) > 0:
                    triggered_count += 1
            
            response.total_count = len(response.alerts)
            response.active_count = active_count
            response.triggered_count = triggered_count
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
            
            # 1. 알림 삭제 처리 (대량 삭제 지원)
            # 노티피케이션 시스템에서 알림 ID들을 삭제
            delete_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_mark_notifications_read",  # 알림을 읽음 처리하여 비활성화
                (account_db_key, json.dumps(request.alert_ids))
            )
            
            deleted_count = 0
            failed_alerts = []
            
            if delete_result and delete_result[0].get('result') == 'SUCCESS':
                deleted_count = delete_result[0].get('updated_count', 0)
                
                # 삭제되지 않은 알림 ID 계산
                total_requested = len(request.alert_ids)
                if deleted_count < total_requested:
                    failed_alerts = request.alert_ids[deleted_count:]
            else:
                failed_alerts = request.alert_ids
            
            # 2. 남은 알림 수 조회
            remaining_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_get_notifications",
                (account_db_key, "PRICE_ALERT", "ALL", 1, 1)
            )
            
            remaining_alerts = 0
            if remaining_result and len(remaining_result) > 1:
                remaining_alerts = remaining_result[1].get('total_count', 0)
            
            response.deleted_count = deleted_count
            response.failed_count = len(failed_alerts)
            response.failed_alert_ids = failed_alerts
            response.remaining_alerts = remaining_alerts
            
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