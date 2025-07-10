from .settings_serialize import (
    SettingsGetRequest, SettingsUpdateProfileRequest, SettingsUpdateNotificationRequest,
    SettingsUpdateSecurityRequest, SettingsUpdateDisplayRequest, SettingsUpdateTradingRequest,
    SettingsResetRequest, SettingsExportRequest, SettingsImportRequest,
    SettingsApplyTemplateRequest, SettingsGetTemplatesRequest, SettingsGetHistoryRequest,
    SettingsUpdatePersonalizationRequest
)

class SettingsProtocol:
    def __init__(self):
        self.on_settings_get_req_callback = None
        self.on_settings_update_profile_req_callback = None
        self.on_settings_update_notification_req_callback = None
        self.on_settings_update_security_req_callback = None
        self.on_settings_update_display_req_callback = None
        self.on_settings_update_trading_req_callback = None
        self.on_settings_reset_req_callback = None
        self.on_settings_export_req_callback = None
        self.on_settings_import_req_callback = None
        self.on_settings_apply_template_req_callback = None
        self.on_settings_get_templates_req_callback = None
        self.on_settings_get_history_req_callback = None
        self.on_settings_update_personalization_req_callback = None

    async def settings_get_req_controller(self, session, msg: bytes, length: int):
        request = SettingsGetRequest.model_validate_json(msg)
        if self.on_settings_get_req_callback:
            return await self.on_settings_get_req_callback(session, request)
        raise NotImplementedError('on_settings_get_req_callback is not set')

    async def settings_update_profile_req_controller(self, session, msg: bytes, length: int):
        request = SettingsUpdateProfileRequest.model_validate_json(msg)
        if self.on_settings_update_profile_req_callback:
            return await self.on_settings_update_profile_req_callback(session, request)
        raise NotImplementedError('on_settings_update_profile_req_callback is not set')

    async def settings_update_notification_req_controller(self, session, msg: bytes, length: int):
        request = SettingsUpdateNotificationRequest.model_validate_json(msg)
        if self.on_settings_update_notification_req_callback:
            return await self.on_settings_update_notification_req_callback(session, request)
        raise NotImplementedError('on_settings_update_notification_req_callback is not set')

    async def settings_update_security_req_controller(self, session, msg: bytes, length: int):
        request = SettingsUpdateSecurityRequest.model_validate_json(msg)
        if self.on_settings_update_security_req_callback:
            return await self.on_settings_update_security_req_callback(session, request)
        raise NotImplementedError('on_settings_update_security_req_callback is not set')

    async def settings_update_display_req_controller(self, session, msg: bytes, length: int):
        request = SettingsUpdateDisplayRequest.model_validate_json(msg)
        if self.on_settings_update_display_req_callback:
            return await self.on_settings_update_display_req_callback(session, request)
        raise NotImplementedError('on_settings_update_display_req_callback is not set')

    async def settings_update_trading_req_controller(self, session, msg: bytes, length: int):
        request = SettingsUpdateTradingRequest.model_validate_json(msg)
        if self.on_settings_update_trading_req_callback:
            return await self.on_settings_update_trading_req_callback(session, request)
        raise NotImplementedError('on_settings_update_trading_req_callback is not set')

    async def settings_reset_req_controller(self, session, msg: bytes, length: int):
        request = SettingsResetRequest.model_validate_json(msg)
        if self.on_settings_reset_req_callback:
            return await self.on_settings_reset_req_callback(session, request)
        raise NotImplementedError('on_settings_reset_req_callback is not set')

    async def settings_export_req_controller(self, session, msg: bytes, length: int):
        request = SettingsExportRequest.model_validate_json(msg)
        if self.on_settings_export_req_callback:
            return await self.on_settings_export_req_callback(session, request)
        raise NotImplementedError('on_settings_export_req_callback is not set')

    async def settings_import_req_controller(self, session, msg: bytes, length: int):
        request = SettingsImportRequest.model_validate_json(msg)
        if self.on_settings_import_req_callback:
            return await self.on_settings_import_req_callback(session, request)
        raise NotImplementedError('on_settings_import_req_callback is not set')

    async def settings_apply_template_req_controller(self, session, msg: bytes, length: int):
        request = SettingsApplyTemplateRequest.model_validate_json(msg)
        if self.on_settings_apply_template_req_callback:
            return await self.on_settings_apply_template_req_callback(session, request)
        raise NotImplementedError('on_settings_apply_template_req_callback is not set')

    async def settings_get_templates_req_controller(self, session, msg: bytes, length: int):
        request = SettingsGetTemplatesRequest.model_validate_json(msg)
        if self.on_settings_get_templates_req_callback:
            return await self.on_settings_get_templates_req_callback(session, request)
        raise NotImplementedError('on_settings_get_templates_req_callback is not set')

    async def settings_get_history_req_controller(self, session, msg: bytes, length: int):
        request = SettingsGetHistoryRequest.model_validate_json(msg)
        if self.on_settings_get_history_req_callback:
            return await self.on_settings_get_history_req_callback(session, request)
        raise NotImplementedError('on_settings_get_history_req_callback is not set')

    async def settings_update_personalization_req_controller(self, session, msg: bytes, length: int):
        request = SettingsUpdatePersonalizationRequest.model_validate_json(msg)
        if self.on_settings_update_personalization_req_callback:
            return await self.on_settings_update_personalization_req_callback(session, request)
        raise NotImplementedError('on_settings_update_personalization_req_callback is not set')