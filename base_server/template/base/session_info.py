from enum import Enum
from dataclasses import dataclass

class ClientSessionState(Enum):
    NONE = "None"
    NORMAL = "Normal"
    FATAL = "Fatal"
    EXPIRED = "Expired"
    DUPLICATED = "Duplicated"
    BLOCKED = "Blocked"
    NETERROR = "NetError"

@dataclass
class SessionInfo:
    shard_id: int = -1 
    account_db_key: int = 0
    platform_id: str = ""
    platform_type: int = -1
    account_id: str = ""
    account_level: int = 0
    app_version: str = ""
    os: str = ""
    country: str = ""
    session_state: ClientSessionState = ClientSessionState.NONE