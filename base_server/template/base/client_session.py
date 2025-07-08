from typing import Optional
from .session_info import SessionInfo

class ClientSession:
    def __init__(self, session_key: str = "", session_info: Optional[SessionInfo] = None):
        self.session_key = session_key
        self.session = session_info or SessionInfo()
    
    def send(self, protocol_id: int, buffer: bytes) -> bool:
        return False
    
    def send(self, protocol_id: int, method: str, json_data: str) -> bool:
        return False