from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class WebSocketConfig(BaseModel):
    """WebSocket 서비스 설정"""
    
    # 연결 설정
    max_connections: int = 1000
    max_message_size: int = 1024 * 1024  # 1MB
    ping_interval: int = 20  # 20초마다 ping
    ping_timeout: int = 10   # ping 응답 10초 대기
    
    # 연결 유지 설정
    heartbeat_interval: int = 30  # 30초마다 heartbeat
    connection_timeout: int = 60  # 60초 비활성 시 연결 종료
    
    # 메시지 관련 설정
    message_queue_size: int = 100  # 클라이언트별 메시지 큐 크기
    broadcast_buffer_size: int = 1000  # 브로드캐스트 버퍼 크기
    
    # 보안 설정
    allowed_origins: List[str] = ["*"]  # 허용된 origin 목록
    require_auth: bool = True     # 인증 필수 여부
    
    # Redis 설정 (선택사항 - 다중 서버 환경에서 사용)
    use_redis_pubsub: bool = False
    redis_channel_prefix: str = "websocket"
    
    # 재시도 설정
    max_retries: int = 3
    connection_timeout_seconds: int = 5