from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class CrawlerTask(BaseModel):
    """크롤러 작업 정보"""
    task_id: str
    task_type: str
    status: str  # pending, running, completed, failed, skipped
    target_url: Optional[str] = None
    target_api: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    priority: int = 0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    data_count: int = 0
    lock_key: Optional[str] = None
    lock_token: Optional[str] = None

class CrawlerData(BaseModel):
    """크롤링된 데이터"""
    data_id: str
    task_id: str
    task_type: str
    source: str
    title: Optional[str] = None
    content: str
    metadata: Optional[Dict[str, Any]] = None
    embedding: Optional[List[float]] = None
    crawled_at: str  # ISO format datetime string