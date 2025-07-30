"""
AWS SNS SMS 서비스

이 파일은 기존 EmailService와 완전히 동일한 패턴으로 구현된 SMS 서비스입니다.
정적 클래스(static class) 방식으로 구현되어 있고, ServiceContainer에서 관리됩니다.

주요 특징:
1. 정적 클래스 패턴: 전역에서 SmsService.send_sms() 형태로 사용
2. 비용 관리: SMS는 건당 비용이 발생하므로 발송량 제한
3. 비동기 처리: 모든 SMS 발송은 비동기로 처리
4. 유효성 검사: 전화번호, 메시지 내용 사전 검증
5. 다양한 발송 방식: 단일, 대량, 템플릿 발송 지원

SMS vs 이메일 차이점:
- 비용: SMS는 건당 $0.05, 이메일은 거의 무료
- 길이: SMS는 160자 제한, 이메일은 제한 없음
- 즉시성: SMS는 즉시 확인, 이메일은 늦게 확인
- 중요도: SMS는 긴급/중요, 이메일은 일반/상세

사용 예시:
```python
# 서비스 초기화 (main.py에서)
config = SmsConfig(default_sender_id="AITrade")
SmsService.init(config)

# 긴급 알림 발송
result = await SmsService.send_urgent_alert(
    phone_number="+82-10-1234-5678",
    stock_symbol="AAPL",
    alert_message="급락 5% 감지"
)
```
"""

from typing import Dict, Any, Optional, List
from service.core.logger import Logger
from .sms_config import SmsConfig
from .sms_client import SNSClient


class SmsService:
    """
    SMS 서비스 (정적 클래스)
    
    EmailService와 완전히 동일한 패턴으로 구현:
    - 정적 메서드만 사용
    - _initialized 플래그로 초기화 상태 관리
    - init(), shutdown(), is_initialized() 제공
    - ServiceContainer에서 생명주기 관리
    
    차이점:
    - SMS 특화 기능: 전화번호 검증, 메시지 길이 제한
    - 비용 관리: 발송량 제한, 비용 추적
    - 긴급성: 중요한 알림만 SMS로 발송
    """
    
    # 클래스 변수
    _config: Optional[SmsConfig] = None          # SMS 설정
    _client: Optional[SNSClient] = None          # SNS 클라이언트
    _initialized: bool = False                   # 초기화 완료 여부
    _daily_send_count: int = 0                   # 일일 발송 카운트 (비용 제한용)
    _monthly_send_count: int = 0                 # 월간 발송 카운트

    @classmethod
    def init(cls, config: SmsConfig) -> bool:
        """
        SMS 서비스 초기화
        
        main.py의 서비스 초기화 단계에서 호출됩니다.
        
        Args:
            config: SmsConfig 객체 (AWS 인증정보, 발송 제한 등)
            
        Returns:
            bool: 초기화 성공 여부
        """
        try:
            cls._config = config
            cls._initialized = True
            cls._daily_send_count = 0
            cls._monthly_send_count = 0
            Logger.info("SmsService 초기화 완료")
            return True
        except Exception as e:
            Logger.error(f"SmsService 초기화 실패: {e}")
            return False

    @classmethod
    async def shutdown(cls):
        """
        SMS 서비스 종료
        
        애플리케이션 종료 시 호출되어 리소스를 정리합니다.
        """
        try:
            if cls._client:
                await cls._client.close()
                cls._client = None
            cls._config = None
            cls._initialized = False
            Logger.info("SmsService 종료 완료")
        except Exception as e:
            Logger.error(f"SmsService 종료 중 에러: {e}")

    @classmethod
    def is_initialized(cls) -> bool:
        """
        초기화 여부 확인
        
        Returns:
            bool: 초기화 완료 여부
        """
        return cls._initialized

    @classmethod
    async def _get_client(cls) -> SNSClient:
        """
        SNS 클라이언트 가져오기 (내부용)
        
        지연 생성(Lazy Loading) 패턴 사용
        
        Returns:
            SNSClient: 초기화된 SNS 클라이언트
        """
        if not cls._initialized:
            raise RuntimeError("SmsService가 초기화되지 않았습니다. init()을 먼저 호출하세요.")
        
        if not cls._client:
            cls._client = SNSClient(cls._config)
            await cls._client.start()
        
        return cls._client

    @classmethod
    def _check_send_limits(cls) -> Dict[str, Any]:
        """
        발송 제한 확인 (비용 관리)
        
        SMS는 비용이 발생하므로 일일/월간 제한을 확인합니다.
        
        Returns:
            dict: 제한 확인 결과
            {
                "allowed": True/False,
                "reason": "제한 사유",
                "daily_remaining": 숫자,
                "monthly_remaining": 숫자
            }
        """
        if not cls._config:
            return {"allowed": False, "reason": "서비스가 초기화되지 않음"}
        
        # 일일 제한 확인
        daily_limit = cls._config.daily_send_limit
        if cls._daily_send_count >= daily_limit:
            return {
                "allowed": False,
                "reason": f"일일 발송 제한 초과 ({daily_limit}건)",
                "daily_remaining": 0,
                "monthly_remaining": cls._config.monthly_send_limit - cls._monthly_send_count
            }
        
        # 월간 제한 확인
        monthly_limit = cls._config.monthly_send_limit
        if cls._monthly_send_count >= monthly_limit:
            return {
                "allowed": False,
                "reason": f"월간 발송 제한 초과 ({monthly_limit}건)",
                "daily_remaining": daily_limit - cls._daily_send_count,
                "monthly_remaining": 0
            }
        
        return {
            "allowed": True,
            "daily_remaining": daily_limit - cls._daily_send_count,
            "monthly_remaining": monthly_limit - cls._monthly_send_count
        }

    # ====================================================================
    # 핵심 SMS 발송 메서드들
    # ====================================================================

    @classmethod
    async def send_sms(cls,
                      phone_number: str,
                      message: str,
                      message_type: str = "prediction_alert",
                      sender_id: Optional[str] = None,
                      **kwargs) -> Dict[str, Any]:
        """
        기본 SMS 발송
        
        가장 기본적인 SMS 발송 메서드입니다.
        
        Args:
            phone_number: 받는 사람 전화번호 (국제형식: +82-10-1234-5678)
            message: 보낼 메시지 (최대 160자)
            message_type: 메시지 타입 (config.message_types의 키)
            sender_id: 발신자 표시명
            **kwargs: 추가 파라미터
            
        Returns:
            dict: 발송 결과
            
        예시:
        ```python
        result = await SmsService.send_sms(
            phone_number="+82-10-1234-5678",
            message="[AI매매] 삼성전자 매수 신호 발생",
            message_type="prediction_alert"
        )
        ```
        """
        try:
            # 1. 발송 제한 확인
            limit_check = cls._check_send_limits()
            if not limit_check["allowed"]:
                return {
                    "success": False,
                    "error": f"발송 제한: {limit_check['reason']}",
                    "daily_remaining": limit_check.get("daily_remaining", 0),
                    "monthly_remaining": limit_check.get("monthly_remaining", 0)
                }
            
            # 2. SNS 클라이언트로 실제 발송
            client = await cls._get_client()
            result = await client.send_sms(
                phone_number=phone_number,
                message=message,
                message_type=message_type,
                sender_id=sender_id,
                **kwargs
            )
            
            # 3. 성공 시 발송 카운트 증가
            if result["success"]:
                cls._daily_send_count += 1
                cls._monthly_send_count += 1
            
            # 4. 제한 정보 추가
            result["daily_remaining"] = limit_check["daily_remaining"] - (1 if result["success"] else 0)
            result["monthly_remaining"] = limit_check["monthly_remaining"] - (1 if result["success"] else 0)
            
            return result
            
        except Exception as e:
            Logger.error(f"SMS 발송 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    @classmethod
    async def send_bulk_sms(cls,
                           recipients: List[Dict[str, str]],
                           message_template: str,
                           message_type: str = "prediction_alert",
                           sender_id: Optional[str] = None,
                           max_recipients: Optional[int] = None) -> Dict[str, Any]:
        """
        대량 SMS 발송
        
        여러 사람에게 개인화된 SMS를 보냅니다.
        비용 때문에 수량 제한이 있습니다.
        
        Args:
            recipients: 수신자 목록 (phone, name, 기타 변수 포함)
            message_template: 메시지 템플릿 ("{name}님, {stock} 알림")
            message_type: 메시지 타입
            sender_id: 발신자 ID
            max_recipients: 최대 발송 수량 (비용 제한)
            
        Returns:
            dict: 대량 발송 결과
            
        예시:
        ```python
        users = [
            {"phone": "+82-10-1111-1111", "name": "홍길동", "stock": "삼성전자"},
            {"phone": "+82-10-2222-2222", "name": "김영희", "stock": "LG전자"}
        ]
        
        result = await SmsService.send_bulk_sms(
            recipients=users,
            message_template="{name}님, {stock} 매수 신호입니다",
            message_type="prediction_alert"
        )
        ```
        """
        try:
            # 1. 수량 제한 확인
            if max_recipients is None:
                max_recipients = cls._config.daily_send_limit // 2  # 일일 제한의 절반만 사용
            
            if len(recipients) > max_recipients:
                return {
                    "success": False,
                    "error": f"대량 발송 제한 초과. 최대 {max_recipients}건 (요청: {len(recipients)}건)"
                }
            
            # 2. 전체 제한 확인
            limit_check = cls._check_send_limits()
            if not limit_check["allowed"]:
                return {
                    "success": False,
                    "error": f"발송 제한: {limit_check['reason']}"
                }
            
            if limit_check["daily_remaining"] < len(recipients):
                return {
                    "success": False,
                    "error": f"일일 잔여 발송량 부족. 잔여: {limit_check['daily_remaining']}건, 요청: {len(recipients)}건"
                }
            
            # 3. SNS 클라이언트로 대량 발송
            client = await cls._get_client()
            result = await client.send_bulk_sms(
                recipients=recipients,
                message_template=message_template,
                message_type=message_type,
                sender_id=sender_id
            )
            
            # 4. 성공한 발송 수만큼 카운트 증가
            if result["success"]:
                success_count = result.get("success_count", 0)
                cls._daily_send_count += success_count
                cls._monthly_send_count += success_count
            
            return result
            
        except Exception as e:
            Logger.error(f"대량 SMS 발송 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    # ====================================================================
    # 편의 메서드들 (알림 시스템 특화)
    # ====================================================================

    @classmethod
    async def send_urgent_alert(cls,
                               phone_number: str,
                               stock_symbol: str,
                               alert_type: str,
                               price_info: str,
                               additional_info: str = "") -> Dict[str, Any]:
        """
        긴급 주식 알림 SMS 발송 (편의 메서드)
        
        주식 급등/급락, 매매 신호 등 긴급한 알림을 보냅니다.
        
        Args:
            phone_number: 전화번호
            stock_symbol: 주식 코드 (예: "AAPL", "005930")
            alert_type: 알림 종류 ("급등", "급락", "매수신호", "매도신호")
            price_info: 가격 정보 (예: "$150.00", "50,000원")
            additional_info: 추가 정보
            
        Returns:
            dict: 발송 결과
            
        예시:
        ```python
        result = await SmsService.send_urgent_alert(
            phone_number="+82-10-1234-5678",
            stock_symbol="AAPL",
            alert_type="급등",
            price_info="$155.50 (+5.2%)",
            additional_info="목표가 도달"
        )
        ```
        """
        # 알림 타입별 이모지와 텍스트
        alert_configs = {
            "급등": {"emoji": "📈", "prefix": "[급등]"},
            "급락": {"emoji": "📉", "prefix": "[급락]"},
            "매수신호": {"emoji": "🟢", "prefix": "[매수]"},
            "매도신호": {"emoji": "🔴", "prefix": "[매도]"},
            "목표달성": {"emoji": "🎯", "prefix": "[목표]"},
            "손절": {"emoji": "⚠️", "prefix": "[손절]"}
        }
        
        config = alert_configs.get(alert_type, {"emoji": "📊", "prefix": f"[{alert_type}]"})
        
        # 메시지 구성 (160자 제한 고려)
        message = f"{config['prefix']} {stock_symbol} {price_info}"
        if additional_info and len(message) + len(additional_info) + 2 <= 160:
            message += f" {additional_info}"
        
        return await cls.send_sms(
            phone_number=phone_number,
            message=message,
            message_type="prediction_alert"
        )

    @classmethod
    async def send_system_alert(cls,
                               phone_numbers: List[str],
                               alert_message: str,
                               alert_priority: str = "medium") -> Dict[str, Any]:
        """
        시스템 알림 SMS 발송 (편의 메서드)
        
        시스템 장애, 점검, 보안 알림 등을 발송합니다.
        
        Args:
            phone_numbers: 전화번호 목록
            alert_message: 알림 메시지
            alert_priority: 우선도 ("high", "medium", "low")
            
        Returns:
            dict: 발송 결과
        """
        # 우선도별 접두사
        priority_prefixes = {
            "high": "[긴급]",
            "medium": "[알림]",
            "low": "[정보]"
        }
        
        prefix = priority_prefixes.get(alert_priority, "[알림]")
        message = f"{prefix} {alert_message}"
        
        # 여러 명에게 동일한 메시지 발송
        recipients = [{"phone": phone, "message": message} for phone in phone_numbers]
        
        return await cls.send_bulk_sms(
            recipients=recipients,
            message_template="{message}",
            message_type="system_alert"
        )

    @classmethod
    async def send_trading_signal(cls,
                                 user_phone: str,
                                 user_name: str,
                                 stock_symbol: str,
                                 signal_type: str,
                                 target_price: str,
                                 confidence: str) -> Dict[str, Any]:
        """
        매매 신호 SMS 발송 (편의 메서드)
        
        AI 모델의 매매 신호를 SMS로 발송합니다.
        
        Args:
            user_phone: 사용자 전화번호
            user_name: 사용자 이름
            stock_symbol: 주식 코드
            signal_type: 신호 종류 ("BUY", "SELL", "HOLD")
            target_price: 목표가
            confidence: 신뢰도 (예: "85%")
            
        Returns:
            dict: 발송 결과
        """
        # 신호 종류별 한글 변환
        signal_text = {
            "BUY": "매수",
            "SELL": "매도",
            "HOLD": "보유"
        }.get(signal_type, signal_type)
        
        # 신호별 이모지
        signal_emoji = {
            "BUY": "🟢",
            "SELL": "🔴", 
            "HOLD": "🟡"
        }.get(signal_type, "📊")
        
        # 메시지 구성
        message = f"{signal_emoji}[AI신호] {stock_symbol} {signal_text} (목표:{target_price}, 신뢰도:{confidence})"
        
        return await cls.send_sms(
            phone_number=user_phone,
            message=message,
            message_type="prediction_alert"
        )

    # ====================================================================
    # 유틸리티 메서드들
    # ====================================================================

    @classmethod
    async def get_send_statistics(cls) -> Dict[str, Any]:
        """
        SMS 발송 통계 조회
        
        일일/월간 발송량, 잔여량, 예상 비용 등을 확인합니다.
        
        Returns:
            dict: 발송 통계
            {
                "daily_sent": 25,
                "daily_remaining": 75,
                "monthly_sent": 450,
                "monthly_remaining": 550,
                "estimated_cost": 22.50
            }
        """
        if not cls._config:
            return {"success": False, "error": "서비스가 초기화되지 않음"}
        
        cost_per_sms = cls._config.cost_management.get("cost_per_sms_usd", 0.05)
        
        return {
            "success": True,
            "daily_sent": cls._daily_send_count,
            "daily_remaining": cls._config.daily_send_limit - cls._daily_send_count,
            "daily_limit": cls._config.daily_send_limit,
            "monthly_sent": cls._monthly_send_count,
            "monthly_remaining": cls._config.monthly_send_limit - cls._monthly_send_count,
            "monthly_limit": cls._config.monthly_send_limit,
            "estimated_monthly_cost_usd": cls._monthly_send_count * cost_per_sms,
            "cost_per_sms_usd": cost_per_sms
        }

    @classmethod
    async def check_aws_sms_settings(cls) -> Dict[str, Any]:
        """
        AWS SNS SMS 설정 확인
        
        AWS 계정의 SMS 발송 한도, 설정 등을 확인합니다.
        
        Returns:
            dict: AWS SMS 설정 정보
        """
        try:
            client = await cls._get_client()
            return await client.get_sms_attributes()
        except Exception as e:
            Logger.error(f"AWS SMS 설정 확인 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    @classmethod
    def reset_daily_counter(cls):
        """
        일일 발송 카운터 리셋
        
        매일 자정에 스케줄러에서 호출하여 일일 제한을 리셋합니다.
        """
        cls._daily_send_count = 0
        Logger.info("SMS 일일 발송 카운터가 리셋되었습니다")

    @classmethod
    def reset_monthly_counter(cls):
        """
        월간 발송 카운터 리셋
        
        매월 1일에 스케줄러에서 호출하여 월간 제한을 리셋합니다.
        """
        cls._monthly_send_count = 0
        Logger.info("SMS 월간 발송 카운터가 리셋되었습니다")