from typing import Dict, List, Optional
from pydantic import BaseModel

class DatabaseTable(BaseModel):
    table_name: str
    primary_key: str

class DatabaseConfig(BaseModel):
    type: str
    host: str
    port: int
    database: str
    user: str
    password: str
    charset: str = "utf8mb4"
    pool_size: int = 10
    max_overflow: int = 20