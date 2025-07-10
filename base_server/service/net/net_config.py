from typing import List, Optional
from pydantic import BaseModel

class NetConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    reload: bool = True