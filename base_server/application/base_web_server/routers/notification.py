from fastapi import APIRouter, Request
from template.base.template_context import TemplateContext, TemplateType
from template.base.template_service import TemplateService
from template.notification.common.notification_serialize import (
    NotificationGetListRequest, NotificationMarkReadRequest, NotificationCreatePriceAlertRequest,
    NotificationGetPriceAlertsRequest, NotificationDeletePriceAlertRequest, NotificationCreateRuleRequest,
    NotificationGetRulesRequest, NotificationUpdateRuleRequest, NotificationGetSettingsRequest,
    NotificationUpdateSettingsRequest, NotificationTestSendRequest, NotificationGetStatsRequest,
    NotificationBulkDeleteRequest
)
from template.notification.common.notification_protocol import NotificationProtocol

router = APIRouter()

notification_protocol = NotificationProtocol()

def setup_notification_protocol_callbacks():
    """Notification protocol 콜백 설정 (main.py에서 한 번만 호출됨)"""
    notification_template = TemplateContext.get_template(TemplateType.NOTIFICATION)
    notification_protocol.on_notification_get_list_req_callback = getattr(notification_template, "on_notification_get_list_req", None)
    notification_protocol.on_notification_mark_read_req_callback = getattr(notification_template, "on_notification_mark_read_req", None)
    notification_protocol.on_notification_create_price_alert_req_callback = getattr(notification_template, "on_notification_create_price_alert_req", None)
    notification_protocol.on_notification_get_price_alerts_req_callback = getattr(notification_template, "on_notification_get_price_alerts_req", None)
    notification_protocol.on_notification_delete_price_alert_req_callback = getattr(notification_template, "on_notification_delete_price_alert_req", None)
    notification_protocol.on_notification_create_rule_req_callback = getattr(notification_template, "on_notification_create_rule_req", None)
    notification_protocol.on_notification_get_rules_req_callback = getattr(notification_template, "on_notification_get_rules_req", None)
    notification_protocol.on_notification_update_rule_req_callback = getattr(notification_template, "on_notification_update_rule_req", None)
    notification_protocol.on_notification_get_settings_req_callback = getattr(notification_template, "on_notification_get_settings_req", None)
    notification_protocol.on_notification_update_settings_req_callback = getattr(notification_template, "on_notification_update_settings_req", None)
    notification_protocol.on_notification_test_send_req_callback = getattr(notification_template, "on_notification_test_send_req", None)
    notification_protocol.on_notification_get_stats_req_callback = getattr(notification_template, "on_notification_get_stats_req", None)
    notification_protocol.on_notification_bulk_delete_req_callback = getattr(notification_template, "on_notification_bulk_delete_req", None)

@router.post("/get-list")
async def notification_get_list(request: NotificationGetListRequest, req: Request):
    """알림 목록 조회"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        notification_protocol.notification_get_list_req_controller
    )

@router.post("/mark-read")
async def notification_mark_read(request: NotificationMarkReadRequest, req: Request):
    """알림 읽음 처리"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        notification_protocol.notification_mark_read_req_controller
    )

@router.post("/create-price-alert")
async def notification_create_price_alert(request: NotificationCreatePriceAlertRequest, req: Request):
    """가격 알림 생성"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        notification_protocol.notification_create_price_alert_req_controller
    )

@router.post("/get-price-alerts")
async def notification_get_price_alerts(request: NotificationGetPriceAlertsRequest, req: Request):
    """가격 알림 조회"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        notification_protocol.notification_get_price_alerts_req_controller
    )

@router.post("/delete-price-alert")
async def notification_delete_price_alert(request: NotificationDeletePriceAlertRequest, req: Request):
    """가격 알림 삭제"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        notification_protocol.notification_delete_price_alert_req_controller
    )

@router.post("/create-rule")
async def notification_create_rule(request: NotificationCreateRuleRequest, req: Request):
    """알림 규칙 생성"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        notification_protocol.notification_create_rule_req_controller
    )

@router.post("/get-rules")
async def notification_get_rules(request: NotificationGetRulesRequest, req: Request):
    """알림 규칙 조회"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        notification_protocol.notification_get_rules_req_controller
    )

@router.post("/update-rule")
async def notification_update_rule(request: NotificationUpdateRuleRequest, req: Request):
    """알림 규칙 수정"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        notification_protocol.notification_update_rule_req_controller
    )

@router.post("/get-settings")
async def notification_get_settings(request: NotificationGetSettingsRequest, req: Request):
    """알림 설정 조회"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        notification_protocol.notification_get_settings_req_controller
    )

@router.post("/update-settings")
async def notification_update_settings(request: NotificationUpdateSettingsRequest, req: Request):
    """알림 설정 수정"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        notification_protocol.notification_update_settings_req_controller
    )

@router.post("/test-send")
async def notification_test_send(request: NotificationTestSendRequest, req: Request):
    """알림 테스트 발송"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        notification_protocol.notification_test_send_req_controller
    )

@router.post("/get-stats")
async def notification_get_stats(request: NotificationGetStatsRequest, req: Request):
    """알림 통계 조회"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        notification_protocol.notification_get_stats_req_controller
    )

@router.post("/bulk-delete")
async def notification_bulk_delete(request: NotificationBulkDeleteRequest, req: Request):
    """알림 일괄 삭제"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        notification_protocol.notification_bulk_delete_req_controller
    )