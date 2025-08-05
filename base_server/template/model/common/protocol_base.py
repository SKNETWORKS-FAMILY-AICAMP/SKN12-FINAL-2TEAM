"""
프로토콜 베이스 클래스 - Pydantic 기반
팀 협업용 BaseRequest/BaseResponse 표준
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class BaseRequest(BaseModel):
    """기본 요청 클래스"""
    request_id: Optional[str] = Field(None, description="요청 ID")
    timestamp: Optional[datetime] = Field(None, description="요청 시간")
    client_info: Optional[Dict[str, Any]] = Field({}, description="클라이언트 정보")

class BaseResponse(BaseModel):
    """기본 응답 클래스"""
    success: bool = Field(True, description="성공 여부")
    message: Optional[str] = Field(None, description="응답 메시지")
    request_id: Optional[str] = Field(None, description="요청 ID")
    timestamp: Optional[datetime] = Field(None, description="응답 시간")
    error_code: Optional[str] = Field(None, description="에러 코드")