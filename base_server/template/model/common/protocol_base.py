"""
프로토콜 베이스 클래스 - 팀 표준 준수
service.net.protocol_base와 동일한 구조
"""

from pydantic import BaseModel

class BaseRequest(BaseModel):
    """기본 요청 클래스 - 팀 표준"""
    accessToken: str = ""
    sequence: int = 0

class BaseResponse(BaseModel):
    """기본 응답 클래스 - 팀 표준"""
    errorCode: int = 0
    sequence: int = 0