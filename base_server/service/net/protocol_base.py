from pydantic import BaseModel

class BaseRequest(BaseModel):
    accessToken: str = ""
    sequence: int = 0

class BaseResponse(BaseModel):
    errorCode: int = 0
    sequence: int = 0