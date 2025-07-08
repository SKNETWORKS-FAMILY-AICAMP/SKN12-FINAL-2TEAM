from typing import List, Optional, Dict, Any
from service.net.protocol_base import BaseRequest, BaseResponse
from .account_model import AccountInfo

class AccountLoginRequest(BaseRequest):
    platform_type: int = 1
    account_id: str
    password: str

class AccountLoginResponse(BaseResponse):
    accessToken: str = ""
    account_db_key: int = 0
    nickname: str = ""
    account_level: int = 1
    shard_id: int = 0
    account_info: Optional[Dict[str, Any]] = None

class AccountSignupRequest(BaseRequest):
    platform_type: int = 1
    account_id: str
    password: str
    nickname: str = ""
    email: str = ""

class AccountSignupResponse(BaseResponse):
    account_db_key: int = 0
    message: str = ""

class AccountLogoutRequest(BaseRequest):
    pass

class AccountLogoutResponse(BaseResponse):
    message: str = ""

# 계좌 정보 조회 (샤딩 DB 사용 예시)
class AccountInfoRequest(BaseRequest):
    pass

class AccountInfoResponse(BaseResponse):
    account_info: Optional[AccountInfo] = None
    shard_id: int = 0  # 디버깅용