"""
임시 프로토콜 베이스 클래스
팀 협업용 - service.net.protocol_base 대체
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class BaseRequest(BaseModel):
    """기본 요청 클래스"""
    request_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    client_info: Optional[Dict[str, Any]] = {}

class BaseResponse(BaseModel):
    """기본 응답 클래스"""
    success: bool = True
    message: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    error_code: Optional[str] = None