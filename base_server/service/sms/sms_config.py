"""
AWS SNS (Simple Notification Service) SMS 설정
기존 StorageConfig, EmailConfig와 동일한 패턴으로 구현
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class SmsConfig(BaseModel):
    """
    AWS SNS SMS 서비스 설정
    
    AWS SNS는 SMS뿐만 아니라 푸시 알림, 이메일 등 다양한 알림을 보낼 수 있는 서비스입니다.
    여기서는 SMS 기능만 사용합니다.
    
    주요 개념:
    1. AWS SNS: 아마존의 알림 서비스 (SMS, 푸시, 이메일 통합)
    2. 발송률 제한: SMS는 비용이 많이 드므로 발송률 제한 필요
    3. 국가별 제한: 각 국가마다 SMS 발송 규칙이 다름
    4. 메시지 타입: 트랜잭션(중요) vs 프로모션(광고) 구분
    """
    
    # AWS 인증 설정 (기존 서비스와 동일)
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    region_name: str = "ap-northeast-2"  # 한국 리전 (서울)
    aws_session_token: Optional[str] = None
    
    # SNS 기본 설정
    default_sender_id: str = "FinanceApp"  # 발신자 표시명 (일부 국가에서만 지원)
    default_message_type: str = "Transactional"  # 메시지 타입: Transactional(중요) / Promotional(광고)
    
    # SMS 발송 설정
    default_country_code: str = "+82"      # 한국 국가 코드
    max_message_length: int = 160          # SMS 최대 길이 (한글은 70자)
    enable_delivery_receipt: bool = True   # 전송 확인 수신 여부
    
    # 성능 및 제한 설정
    send_timeout: int = 30                 # 발송 타임아웃 (초)
    max_retries: int = 3                   # 재시도 횟수
    retry_delay: float = 2.0               # 재시도 간격 (초)
    
    # 발송률 제한 (비용 절약)
    max_send_rate: int = 1                 # 초당 최대 발송 수 (SNS 기본값 대로)
    daily_send_limit: int = 100            # 일일 발송 제한 (비용 통제)
    monthly_send_limit: int = 1000         # 월간 발송 제한
    
    # 국가별 설정
    supported_countries: List[str] = [
        "+82",  # 한국
        "+1",   # 미국/캐나다  
        "+44",  # 영국
        "+81",  # 일본
        "+86",  # 중국
    ]
    
    # 메시지 타입별 설정
    message_types: Dict[str, Dict[str, Any]] = {
        "prediction_alert": {
            "type": "Transactional",     # 중요한 알림
            "sender_id": "AITrade",      # 발신자 표시
            "template": "[AI매매] {stock}: {action} 신호 ({price}원)",
            "priority": "high"
        },
        "price_target": {
            "type": "Transactional",
            "sender_id": "AITrade", 
            "template": "[목표달성] {stock}이 목표가 {price}원에 도달했습니다",
            "priority": "high"
        },
        "system_alert": {
            "type": "Transactional",
            "sender_id": "System",
            "template": "[시스템] {message}",
            "priority": "medium"
        },
        "daily_summary": {
            "type": "Promotional",       # 일반 정보
            "sender_id": "Report",
            "template": "[일일리포트] 포트폴리오 수익률: {return_rate}%",
            "priority": "low"
        }
    }
    
    # 비용 관리 설정
    cost_management: Dict[str, Any] = {
        "enable_cost_limit": True,       # 비용 제한 활성화
        "monthly_budget_usd": 50.0,      # 월간 예산 (달러)
        "cost_per_sms_usd": 0.05,        # SMS당 예상 비용
        "alert_threshold": 0.8,          # 예산의 80% 도달 시 알림
    }
    
    # 전화번호 검증 설정
    phone_validation: Dict[str, Any] = {
        "enable_validation": True,       # 전화번호 유효성 검사
        "allow_landline": False,         # 유선전화 허용 여부 (SMS 불가능)
        "require_country_code": True,    # 국가코드 필수 여부
        "blocked_prefixes": [            # 차단할 번호 접두사
            "+82-1588",  # 고객센터
            "+82-080",   # 무료전화
        ]
    }
    
    # 메시지 내용 필터링
    content_filter: Dict[str, Any] = {
        "enable_spam_filter": True,      # 스팸 필터 활성화
        "blocked_keywords": [            # 차단할 키워드
            "광고", "홍보", "할인", "이벤트", "무료"
        ],
        "max_url_count": 1,              # 최대 URL 개수
        "allow_emoji": True,             # 이모지 허용 여부
    }
    
    # 로깅 및 모니터링
    monitoring: Dict[str, Any] = {
        "enable_delivery_tracking": True,  # 전송 상태 추적
        "enable_cost_tracking": True,      # 비용 추적
        "log_message_content": False,      # 메시지 내용 로깅 (개인정보 고려)
        "retention_days": 30,              # 로그 보관 기간
    }
    
    class Config:
        # Pydantic 설정
        arbitrary_types_allowed = True
        use_enum_values = True