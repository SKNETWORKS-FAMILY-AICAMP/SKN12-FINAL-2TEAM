from .notification_serialize import (
    NotificationListRequest, NotificationMarkReadRequest, NotificationMarkAllReadRequest,
    NotificationDeleteRequest, NotificationStatsRequest
)

class NotificationProtocol:
    """인앱 알림 프로토콜"""
    def __init__(self):
        # 콜백 함수들
        self.on_notification_list_req_callback = None
        self.on_notification_mark_read_req_callback = None
        self.on_notification_mark_all_read_req_callback = None
        self.on_notification_delete_req_callback = None
        self.on_notification_stats_req_callback = None

    async def notification_list_req_controller(self, session, msg: bytes, length: int):
        """인앱 알림 목록 조회"""
        request = NotificationListRequest.model_validate_json(msg)
        if self.on_notification_list_req_callback:
            return await self.on_notification_list_req_callback(session, request)
        raise NotImplementedError('on_notification_list_req_callback is not set')

    async def notification_mark_read_req_controller(self, session, msg: bytes, length: int):
        """알림 읽음 처리"""
        request = NotificationMarkReadRequest.model_validate_json(msg)
        if self.on_notification_mark_read_req_callback:
            return await self.on_notification_mark_read_req_callback(session, request)
        raise NotImplementedError('on_notification_mark_read_req_callback is not set')

    async def notification_mark_all_read_req_controller(self, session, msg: bytes, length: int):
        """알림 일괄 읽음 처리"""
        request = NotificationMarkAllReadRequest.model_validate_json(msg)
        if self.on_notification_mark_all_read_req_callback:
            return await self.on_notification_mark_all_read_req_callback(session, request)
        raise NotImplementedError('on_notification_mark_all_read_req_callback is not set')

    async def notification_delete_req_controller(self, session, msg: bytes, length: int):
        """알림 삭제"""
        request = NotificationDeleteRequest.model_validate_json(msg)
        if self.on_notification_delete_req_callback:
            return await self.on_notification_delete_req_callback(session, request)
        raise NotImplementedError('on_notification_delete_req_callback is not set')

    async def notification_stats_req_controller(self, session, msg: bytes, length: int):
        """알림 통계 조회"""
        request = NotificationStatsRequest.model_validate_json(msg)
        if self.on_notification_stats_req_callback:
            return await self.on_notification_stats_req_callback(session, request)
        raise NotImplementedError('on_notification_stats_req_callback is not set')