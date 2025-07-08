from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from enum import IntEnum

class ECacheType(IntEnum):
    NONE = 0
    REDIS = 1

class ConnectionPoolConfig(BaseModel):
    max_connections: int = 20
    retry_on_timeout: bool = True

class CacheConfig(BaseModel):
    type: str = "redis"
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str = ""
    session_expire_seconds: int = 3600
    connection_pool: ConnectionPoolConfig = ConnectionPoolConfig()