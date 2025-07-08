from .account_serialize import AccountLoginRequest, AccountLogoutRequest, AccountSignupRequest, AccountInfoRequest

class AccountProtocol:
    def __init__(self):
        # 콜백 속성
        self.on_account_login_req_callback = None
        self.on_account_logout_req_callback = None
        self.on_account_signup_req_callback = None
        self.on_account_info_req_callback = None

    async def account_login_req_controller(self, session, msg: bytes, length: int):
        # msg를 AccountLoginRequest로 역직렬화
        # 콜백 호출
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
