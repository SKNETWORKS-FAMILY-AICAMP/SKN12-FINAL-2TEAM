from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Any, Dict
from service.llm.AIChat.BaseFinanceTool import BaseFinanceTool

__all__ = ["SessionAwareTool", "ClientSession"]

class ClientSession:
    """클라이언트 세션 정보를 담는 클래스"""
    
    def __init__(self, account_db_key: int, account_id: str, shard_id: int = 1):
        self.account_db_key = account_db_key
        self.account_id = account_id
        self.shard_id = shard_id
    
    @classmethod
    def from_template_session(cls, template_session) -> Optional['ClientSession']:
        """Template 세션에서 ClientSession 생성"""
        if not template_session:
            return None
        
        account_db_key = getattr(template_session, 'account_db_key', 0)
        account_id = getattr(template_session, 'account_id', '')
        shard_id = getattr(template_session, 'shard_id', 1)
        
        if account_db_key == 0:
            return None
            
        return cls(account_db_key, account_id, shard_id)

class SessionAwareTool(BaseFinanceTool, ABC):
    """
    세션 인식을 지원하는 툴들의 공통 인터페이스
    
    사용자별 상태 관리가 필요한 툴들이 이 클래스를 상속받아야 함
    """
    
    def __init__(self):
        super().__init__()
        self._client_session: Optional[ClientSession] = None
    
    def inject_session(self, session: ClientSession) -> None:
        """세션 정보 주입"""
        self._client_session = session
    
    def get_session(self) -> Optional[ClientSession]:
        """현재 주입된 세션 반환"""
        return self._client_session
    
    def get_account_db_key(self) -> int:
        """계정 DB 키 반환 (fallback 포함)"""
        if self._client_session:
            return self._client_session.account_db_key
        return 0  # fallback
    
    def get_account_id(self) -> str:
        """계정 ID 반환"""
        if self._client_session:
            return self._client_session.account_id
        return ""
    
    def get_shard_id(self) -> int:
        """샤드 ID 반환"""
        if self._client_session:
            return self._client_session.shard_id
        return 1  # default shard
    
    def require_session(self) -> bool:
        """세션이 필수인지 여부 (하위 클래스에서 오버라이드)"""
        return True
    
    def validate_session(self) -> None:
        """세션 유효성 검증"""
        if self.require_session() and not self._client_session:
            raise ValueError("Session is required but not provided")
        
        if self._client_session and self._client_session.account_db_key == 0:
            raise ValueError("Invalid session: account_db_key is 0")
    
    @abstractmethod
    def get_data(self, **kwargs) -> Any:
        """데이터 조회 (세션 검증 포함)"""
        self.validate_session()
        return super().get_data(**kwargs) 