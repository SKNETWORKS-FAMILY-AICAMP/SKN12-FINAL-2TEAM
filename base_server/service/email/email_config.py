"""
AWS SES (Simple Email Service) 설정
기존 StorageConfig와 동일한 패턴으로 구현
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class EmailConfig(BaseModel):
    """
    AWS SES 서비스 설정
    
    기존 AWS 서비스와 동일한 설정 패턴 사용
    - AWS 인증 정보
    - 리전 설정
    - 타임아웃 및 재시도 설정
    """
    
    # AWS 인증 설정 (StorageConfig와 동일)
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    region_name: str = "ap-northeast-2"  # 한국 리전
    aws_session_token: Optional[str] = None
    
    # SES 기본 설정
    default_from_email: str = "noreply@mail.bullant-kr.com"  # BullAnt-KR 도메인
    default_from_name: str = "BullAnt Trading Platform Korea"  # BullAnt 브랜드
    
    # 이메일 템플릿 설정
    template_bucket: Optional[str] = None  # S3 버킷 (템플릿 저장용)
    template_prefix: str = "email-templates/"
    default_charset: str = "UTF-8"
    
    # 성능 설정
    send_timeout: int = 30                 # 발송 타임아웃 (초)
    max_retries: int = 3                   # 재시도 횟수
    retry_delay: float = 1.0               # 재시도 간격 (초)
    
    # 배치 발송 설정
    batch_size: int = 50                   # SES 배치 크기 제한
    max_send_rate: int = 14                # SES 기본 발송률 (초당)
    
    # 검증 설정
    verify_email_addresses: bool = True    # 이메일 주소 자동 검증
    configuration_set: Optional[str] = None  # SES 구성 세트
    
    # 모니터링 설정
    enable_tracking: bool = True           # 이메일 추적 활성화
    enable_bounce_handling: bool = True    # 반송 처리 활성화
    enable_complaint_handling: bool = True # 스팸 신고 처리 활성화
    
    # 기본 템플릿 데이터
    default_template_data: Dict[str, Any] = {
        "company_name": "BullAnt Korea",
        "support_email": "support@mail.bullant-kr.com",
        "unsubscribe_url": "https://www.bullant-kr.com/unsubscribe"
    }
    
    # 이메일 타입별 설정
    email_types: Dict[str, Dict[str, Any]] = {
        "prediction_alert": {
            "template_name": "prediction_alert",
            "subject_prefix": "[매매 신호]",
            "priority": "high"
        },
        "price_target": {
            "template_name": "price_target",
            "subject_prefix": "[목표가 달성]",
            "priority": "high"
        },
        "daily_summary": {
            "template_name": "daily_summary",
            "subject_prefix": "[일일 리포트]",
            "priority": "normal"
        },
        "system_notice": {
            "template_name": "system_notice",
            "subject_prefix": "[시스템 공지]",
            "priority": "normal"
        }
    }
    
    class Config:
        # Pydantic 설정
        arbitrary_types_allowed = True
        use_enum_values = True