from fastapi import APIRouter, Request
from template.base.template_context import TemplateContext, TemplateType
from template.base.template_service import TemplateService
from template.notification.common.notification_serialize import (
    NotificationListRequest, NotificationMarkReadRequest, NotificationMarkAllReadRequest,
    NotificationDeleteRequest, NotificationStatsRequest, NotificationCreateRequest
)
from template.notification.common.notification_protocol import NotificationProtocol

router = APIRouter()

notification_protocol = NotificationProtocol()

def setup_notification_protocol_callbacks():
    """Notification protocol 콜백 설정 (main.py에서 한 번만 호출됨)"""
    notification_template = TemplateContext.get_template(TemplateType.NOTIFICATION)
    notification_protocol.on_notification_list_req_callback = getattr(notification_template, "on_notification_list_req", None)
    notification_protocol.on_notification_mark_read_req_callback = getattr(notification_template, "on_notification_mark_read_req", None)
    notification_protocol.on_notification_mark_all_read_req_callback = getattr(notification_template, "on_notification_mark_all_read_req", None)
    notification_protocol.on_notification_delete_req_callback = getattr(notification_template, "on_notification_delete_req", None)
    notification_protocol.on_notification_stats_req_callback = getattr(notification_template, "on_notification_stats_req", None)
    notification_protocol.on_notification_create_req_callback = getattr(notification_template, "on_notification_create_req", None)

@router.post("/list")
async def notification_list(request: NotificationListRequest, req: Request):
    """인앱 알림 목록 조회 (게임 패턴: 읽은 알림 조회 시 자동 삭제)"""
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

@router.post("/mark-all-read")
async def notification_mark_all_read(request: NotificationMarkAllReadRequest, req: Request):
    """알림 일괄 읽음 처리"""
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
        notification_protocol.notification_mark_all_read_req_controller
    )

@router.post("/delete")
async def notification_delete(request: NotificationDeleteRequest, req: Request):
    """알림 삭제 (소프트 삭제)"""
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
        notification_protocol.notification_delete_req_controller
    )

@router.post("/stats")
async def notification_stats(request: NotificationStatsRequest, req: Request):
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
        notification_protocol.notification_stats_req_controller
    )

@router.post("/create")
async def notification_create(request: NotificationCreateRequest, req: Request):
    """운영자 알림 생성 (OPERATOR 권한 필요)"""
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_operator(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        notification_protocol.notification_create_req_controller
    )