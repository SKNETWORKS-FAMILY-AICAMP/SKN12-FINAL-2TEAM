from enum import IntEnum

class ENetErrorCode(IntEnum):
    SUCCESS = 0
    FATAL = -1
    INVALID_REQUEST = 1001
    ACCESS_DENIED = 1003
    SERVER_ERROR = 5000
    SESSION_EXPIRED = 10000