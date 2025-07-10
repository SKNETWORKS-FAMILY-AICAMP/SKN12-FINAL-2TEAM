from fastapi import APIRouter, Request
from template.base.template_context import TemplateContext, TemplateType
from template.base.template_service import TemplateService
from template.notification.common.notification_serialize import (
    NotificationListRequest, NotificationMarkReadRequest, NotificationCreateAlertRequest,
    NotificationAlertListRequest, NotificationDeleteAlertRequest
)
from template.notification.common.notification_protocol import NotificationProtocol

router = APIRouter()

notification_protocol = NotificationProtocol()

def setup_notification_protocol_callbacks():
    """Notification protocol 콜백 설정 (main.py에서 한 번만 호출됨)"""
    notification_template = TemplateContext.get_template(TemplateType.NOTIFICATION)
    notification_protocol.on_notification_list_req_callback = getattr(notification_template, "on_notification_list_req", None)
    notification_protocol.on_notification_mark_read_req_callback = getattr(notification_template, "on_notification_mark_read_req", None)
    notification_protocol.on_notification_create_alert_req_callback = getattr(notification_template, "on_notification_create_alert_req", None)
    notification_protocol.on_notification_alert_list_req_callback = getattr(notification_template, "on_notification_alert_list_req", None)
    notification_protocol.on_notification_delete_alert_req_callback = getattr(notification_template, "on_notification_delete_alert_req", None)

@router.post("/list")
async def notification_list(request: NotificationListRequest, req: Request):
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
        notification_protocol.notification_list_req_controller
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

@router.post("/create-alert")
async def notification_create_alert(request: NotificationCreateAlertRequest, req: Request):
    """알림 생성"""
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
        notification_protocol.notification_create_alert_req_controller
    )

@router.post("/alert/list")
async def notification_alert_list(request: NotificationAlertListRequest, req: Request):
    """알림 설정 목록 조회"""
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
        notification_protocol.notification_alert_list_req_controller
    )

@router.post("/delete-alert")
async def notification_delete_alert(request: NotificationDeleteAlertRequest, req: Request):
    """알림 설정 삭제"""
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
        notification_protocol.notification_delete_alert_req_controller
    )