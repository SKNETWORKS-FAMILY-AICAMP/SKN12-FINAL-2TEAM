from .settings_serialize import (
    SettingsGetRequest, SettingsUpdateRequest, SettingsResetRequest,
    SettingsOTPToggleRequest, SettingsPasswordChangeRequest, SettingsExportDataRequest
)

class SettingsProtocol:
    def __init__(self):
        self.on_settings_get_req_callback = None
        self.on_settings_update_req_callback = None
        self.on_settings_reset_req_callback = None
        self.on_settings_otp_toggle_req_callback = None
        self.on_settings_password_change_req_callback = None
        self.on_settings_export_data_req_callback = None

    async def settings_get_req_controller(self, session, msg: bytes, length: int):
        request = SettingsGetRequest.model_validate_json(msg)
        if self.on_settings_get_req_callback:
            return await self.on_settings_get_req_callback(session, request)
        raise NotImplementedError('on_settings_get_req_callback is not set')

    async def settings_update_req_controller(self, session, msg: bytes, length: int):
        request = SettingsUpdateRequest.model_validate_json(msg)
        if self.on_settings_update_req_callback:
            return await self.on_settings_update_req_callback(session, request)
        raise NotImplementedError('on_settings_update_req_callback is not set')

    async def settings_reset_req_controller(self, session, msg: bytes, length: int):
        request = SettingsResetRequest.model_validate_json(msg)
        if self.on_settings_reset_req_callback:
            return await self.on_settings_reset_req_callback(session, request)
        raise NotImplementedError('on_settings_reset_req_callback is not set')

    async def settings_otp_toggle_req_controller(self, session, msg: bytes, length: int):
        request = SettingsOTPToggleRequest.model_validate_json(msg)
        if self.on_settings_otp_toggle_req_callback:
            return await self.on_settings_otp_toggle_req_callback(session, request)
        raise NotImplementedError('on_settings_otp_toggle_req_callback is not set')

    async def settings_password_change_req_controller(self, session, msg: bytes, length: int):
        request = SettingsPasswordChangeRequest.model_validate_json(msg)
        if self.on_settings_password_change_req_callback:
            return await self.on_settings_password_change_req_callback(session, request)
        raise NotImplementedError('on_settings_password_change_req_callback is not set')

    async def settings_export_data_req_controller(self, session, msg: bytes, length: int):
        request = SettingsExportDataRequest.model_validate_json(msg)
        if self.on_settings_export_data_req_callback:
            return await self.on_settings_export_data_req_callback(session, request)
        raise NotImplementedError('on_settings_export_data_req_callback is not set')