from .account_serialize import (
    AccountLoginRequest, AccountLogoutRequest, AccountSignupRequest, AccountInfoRequest,
    AccountEmailVerifyRequest, AccountEmailConfirmRequest, AccountOTPSetupRequest,
    AccountOTPVerifyRequest, AccountOTPLoginRequest, AccountProfileSetupRequest,
    AccountProfileGetRequest, AccountProfileUpdateRequest, AccountTokenRefreshRequest,
    AccountTokenValidateRequest
)

class AccountProtocol:
    def __init__(self):
        # 기존 콜백 속성
        self.on_account_login_req_callback = None
        self.on_account_logout_req_callback = None
        self.on_account_signup_req_callback = None
        self.on_account_info_req_callback = None
        
        # 새로운 콜백 속성
        self.on_account_email_verify_req_callback = None
        self.on_account_email_confirm_req_callback = None
        self.on_account_otp_setup_req_callback = None
        self.on_account_otp_verify_req_callback = None
        self.on_account_otp_login_req_callback = None
        self.on_account_profile_setup_req_callback = None
        self.on_account_profile_get_req_callback = None
        self.on_account_profile_update_req_callback = None
        self.on_account_token_refresh_req_callback = None
        self.on_account_token_validate_req_callback = None

    async def account_login_req_controller(self, session, msg: bytes, length: int):
        request = AccountLoginRequest.model_validate_json(msg)
        if self.on_account_login_req_callback:
            return await self.on_account_login_req_callback(session, request)
        raise NotImplementedError('on_account_login_req_callback is not set')

    async def account_logout_req_controller(self, session, msg: bytes, length: int):
        request = AccountLogoutRequest.model_validate_json(msg)
        if self.on_account_logout_req_callback:
            return await self.on_account_logout_req_callback(session, request)
        raise NotImplementedError('on_account_logout_req_callback is not set')

    async def account_signup_req_controller(self, session, msg: bytes, length: int):
        request = AccountSignupRequest.model_validate_json(msg)
        if self.on_account_signup_req_callback:
            return await self.on_account_signup_req_callback(session, request)
        raise NotImplementedError('on_account_signup_req_callback is not set')

    async def account_info_req_controller(self, session, msg: bytes, length: int):
        request = AccountInfoRequest.model_validate_json(msg)
        if self.on_account_info_req_callback:
            return await self.on_account_info_req_callback(session, request)
        raise NotImplementedError('on_account_info_req_callback is not set')

    # 새로운 컨트롤러들
    async def account_email_verify_req_controller(self, session, msg: bytes, length: int):
        request = AccountEmailVerifyRequest.model_validate_json(msg)
        if self.on_account_email_verify_req_callback:
            return await self.on_account_email_verify_req_callback(session, request)
        raise NotImplementedError('on_account_email_verify_req_callback is not set')

    async def account_email_confirm_req_controller(self, session, msg: bytes, length: int):
        request = AccountEmailConfirmRequest.model_validate_json(msg)
        if self.on_account_email_confirm_req_callback:
            return await self.on_account_email_confirm_req_callback(session, request)
        raise NotImplementedError('on_account_email_confirm_req_callback is not set')

    async def account_otp_setup_req_controller(self, session, msg: bytes, length: int):
        request = AccountOTPSetupRequest.model_validate_json(msg)
        if self.on_account_otp_setup_req_callback:
            return await self.on_account_otp_setup_req_callback(session, request)
        raise NotImplementedError('on_account_otp_setup_req_callback is not set')

    async def account_otp_verify_req_controller(self, session, msg: bytes, length: int):
        request = AccountOTPVerifyRequest.model_validate_json(msg)
        if self.on_account_otp_verify_req_callback:
            return await self.on_account_otp_verify_req_callback(session, request)
        raise NotImplementedError('on_account_otp_verify_req_callback is not set')

    async def account_otp_login_req_controller(self, session, msg: bytes, length: int):
        request = AccountOTPLoginRequest.model_validate_json(msg)
        if self.on_account_otp_login_req_callback:
            return await self.on_account_otp_login_req_callback(session, request)
        raise NotImplementedError('on_account_otp_login_req_callback is not set')

    async def account_profile_setup_req_controller(self, session, msg: bytes, length: int):
        request = AccountProfileSetupRequest.model_validate_json(msg)
        if self.on_account_profile_setup_req_callback:
            return await self.on_account_profile_setup_req_callback(session, request)
        raise NotImplementedError('on_account_profile_setup_req_callback is not set')

    async def account_profile_get_req_controller(self, session, msg: bytes, length: int):
        request = AccountProfileGetRequest.model_validate_json(msg)
        if self.on_account_profile_get_req_callback:
            return await self.on_account_profile_get_req_callback(session, request)
        raise NotImplementedError('on_account_profile_get_req_callback is not set')

    async def account_profile_update_req_controller(self, session, msg: bytes, length: int):
        request = AccountProfileUpdateRequest.model_validate_json(msg)
        if self.on_account_profile_update_req_callback:
            return await self.on_account_profile_update_req_callback(session, request)
        raise NotImplementedError('on_account_profile_update_req_callback is not set')

    async def account_token_refresh_req_controller(self, session, msg: bytes, length: int):
        request = AccountTokenRefreshRequest.model_validate_json(msg)
        if self.on_account_token_refresh_req_callback:
            return await self.on_account_token_refresh_req_callback(session, request)
        raise NotImplementedError('on_account_token_refresh_req_callback is not set')

    async def account_token_validate_req_controller(self, session, msg: bytes, length: int):
        request = AccountTokenValidateRequest.model_validate_json(msg)
        if self.on_account_token_validate_req_callback:
            return await self.on_account_token_validate_req_callback(session, request)
        raise NotImplementedError('on_account_token_validate_req_callback is not set')
