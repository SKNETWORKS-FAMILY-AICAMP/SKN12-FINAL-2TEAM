from .notification_serialize import (
    NotificationGetListRequest, NotificationMarkReadRequest, NotificationCreatePriceAlertRequest,
    NotificationGetPriceAlertsRequest, NotificationDeletePriceAlertRequest, NotificationCreateRuleRequest,
    NotificationGetRulesRequest, NotificationUpdateRuleRequest, NotificationGetSettingsRequest,
    NotificationUpdateSettingsRequest, NotificationTestSendRequest, NotificationGetStatsRequest,
    NotificationBulkDeleteRequest
)

class NotificationProtocol:
    def __init__(self):
        self.on_notification_get_list_req_callback = None
        self.on_notification_mark_read_req_callback = None
        self.on_notification_create_price_alert_req_callback = None
        self.on_notification_get_price_alerts_req_callback = None
        self.on_notification_delete_price_alert_req_callback = None
        self.on_notification_create_rule_req_callback = None
        self.on_notification_get_rules_req_callback = None
        self.on_notification_update_rule_req_callback = None
        self.on_notification_get_settings_req_callback = None
        self.on_notification_update_settings_req_callback = None
        self.on_notification_test_send_req_callback = None
        self.on_notification_get_stats_req_callback = None
        self.on_notification_bulk_delete_req_callback = None

    async def notification_get_list_req_controller(self, session, msg: bytes, length: int):
        request = NotificationGetListRequest.model_validate_json(msg)
        if self.on_notification_get_list_req_callback:
            return await self.on_notification_get_list_req_callback(session, request)
        raise NotImplementedError('on_notification_get_list_req_callback is not set')

    async def notification_mark_read_req_controller(self, session, msg: bytes, length: int):
        request = NotificationMarkReadRequest.model_validate_json(msg)
        if self.on_notification_mark_read_req_callback:
            return await self.on_notification_mark_read_req_callback(session, request)
        raise NotImplementedError('on_notification_mark_read_req_callback is not set')

    async def notification_create_price_alert_req_controller(self, session, msg: bytes, length: int):
        request = NotificationCreatePriceAlertRequest.model_validate_json(msg)
        if self.on_notification_create_price_alert_req_callback:
            return await self.on_notification_create_price_alert_req_callback(session, request)
        raise NotImplementedError('on_notification_create_price_alert_req_callback is not set')

    async def notification_get_price_alerts_req_controller(self, session, msg: bytes, length: int):
        request = NotificationGetPriceAlertsRequest.model_validate_json(msg)
        if self.on_notification_get_price_alerts_req_callback:
            return await self.on_notification_get_price_alerts_req_callback(session, request)
        raise NotImplementedError('on_notification_get_price_alerts_req_callback is not set')

    async def notification_delete_price_alert_req_controller(self, session, msg: bytes, length: int):
        request = NotificationDeletePriceAlertRequest.model_validate_json(msg)
        if self.on_notification_delete_price_alert_req_callback:
            return await self.on_notification_delete_price_alert_req_callback(session, request)
        raise NotImplementedError('on_notification_delete_price_alert_req_callback is not set')

    async def notification_create_rule_req_controller(self, session, msg: bytes, length: int):
        request = NotificationCreateRuleRequest.model_validate_json(msg)
        if self.on_notification_create_rule_req_callback:
            return await self.on_notification_create_rule_req_callback(session, request)
        raise NotImplementedError('on_notification_create_rule_req_callback is not set')

    async def notification_get_rules_req_controller(self, session, msg: bytes, length: int):
        request = NotificationGetRulesRequest.model_validate_json(msg)
        if self.on_notification_get_rules_req_callback:
            return await self.on_notification_get_rules_req_callback(session, request)
        raise NotImplementedError('on_notification_get_rules_req_callback is not set')

    async def notification_update_rule_req_controller(self, session, msg: bytes, length: int):
        request = NotificationUpdateRuleRequest.model_validate_json(msg)
        if self.on_notification_update_rule_req_callback:
            return await self.on_notification_update_rule_req_callback(session, request)
        raise NotImplementedError('on_notification_update_rule_req_callback is not set')

    async def notification_get_settings_req_controller(self, session, msg: bytes, length: int):
        request = NotificationGetSettingsRequest.model_validate_json(msg)
        if self.on_notification_get_settings_req_callback:
            return await self.on_notification_get_settings_req_callback(session, request)
        raise NotImplementedError('on_notification_get_settings_req_callback is not set')

    async def notification_update_settings_req_controller(self, session, msg: bytes, length: int):
        request = NotificationUpdateSettingsRequest.model_validate_json(msg)
        if self.on_notification_update_settings_req_callback:
            return await self.on_notification_update_settings_req_callback(session, request)
        raise NotImplementedError('on_notification_update_settings_req_callback is not set')

    async def notification_test_send_req_controller(self, session, msg: bytes, length: int):
        request = NotificationTestSendRequest.model_validate_json(msg)
        if self.on_notification_test_send_req_callback:
            return await self.on_notification_test_send_req_callback(session, request)
        raise NotImplementedError('on_notification_test_send_req_callback is not set')

    async def notification_get_stats_req_controller(self, session, msg: bytes, length: int):
        request = NotificationGetStatsRequest.model_validate_json(msg)
        if self.on_notification_get_stats_req_callback:
            return await self.on_notification_get_stats_req_callback(session, request)
        raise NotImplementedError('on_notification_get_stats_req_callback is not set')

    async def notification_bulk_delete_req_controller(self, session, msg: bytes, length: int):
        request = NotificationBulkDeleteRequest.model_validate_json(msg)
        if self.on_notification_bulk_delete_req_callback:
            return await self.on_notification_bulk_delete_req_callback(session, request)
        raise NotImplementedError('on_notification_bulk_delete_req_callback is not set')