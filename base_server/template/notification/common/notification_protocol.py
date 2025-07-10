from .notification_serialize import (
    NotificationListRequest, NotificationMarkReadRequest, NotificationCreateAlertRequest,
    NotificationAlertListRequest, NotificationDeleteAlertRequest
)

class NotificationProtocol:
    def __init__(self):
        self.on_notification_list_req_callback = None
        self.on_notification_mark_read_req_callback = None
        self.on_notification_create_alert_req_callback = None
        self.on_notification_alert_list_req_callback = None
        self.on_notification_delete_alert_req_callback = None

    async def notification_list_req_controller(self, session, msg: bytes, length: int):
        request = NotificationListRequest.model_validate_json(msg)
        if self.on_notification_list_req_callback:
            return await self.on_notification_list_req_callback(session, request)
        raise NotImplementedError('on_notification_list_req_callback is not set')

    async def notification_mark_read_req_controller(self, session, msg: bytes, length: int):
        request = NotificationMarkReadRequest.model_validate_json(msg)
        if self.on_notification_mark_read_req_callback:
            return await self.on_notification_mark_read_req_callback(session, request)
        raise NotImplementedError('on_notification_mark_read_req_callback is not set')

    async def notification_create_alert_req_controller(self, session, msg: bytes, length: int):
        request = NotificationCreateAlertRequest.model_validate_json(msg)
        if self.on_notification_create_alert_req_callback:
            return await self.on_notification_create_alert_req_callback(session, request)
        raise NotImplementedError('on_notification_create_alert_req_callback is not set')

    async def notification_alert_list_req_controller(self, session, msg: bytes, length: int):
        request = NotificationAlertListRequest.model_validate_json(msg)
        if self.on_notification_alert_list_req_callback:
            return await self.on_notification_alert_list_req_callback(session, request)
        raise NotImplementedError('on_notification_alert_list_req_callback is not set')

    async def notification_delete_alert_req_controller(self, session, msg: bytes, length: int):
        request = NotificationDeleteAlertRequest.model_validate_json(msg)
        if self.on_notification_delete_alert_req_callback:
            return await self.on_notification_delete_alert_req_callback(session, request)
        raise NotImplementedError('on_notification_delete_alert_req_callback is not set')