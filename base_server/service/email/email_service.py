"""
AWS SES 이메일 서비스

이 파일은 기존 StorageService와 완전히 동일한 패턴으로 구현된 이메일 서비스입니다.
정적 클래스(static class) 방식으로 구현되어 있고, ServiceContainer에서 관리됩니다.

주요 특징:
1. 정적 클래스 패턴: 전역에서 EmailService.send_email() 형태로 사용
2. Client Pool 패턴: 여러 AWS SES 연결을 풀로 관리해서 성능 향상
3. 비동기 처리: 모든 이메일 발송은 비동기로 처리
4. 에러 처리: AWS 에러를 친화적인 메시지로 변환
5. 다양한 발송 방식: 단일, 템플릿, 대량 발송 지원

사용 예시:
```python
# 서비스 초기화 (main.py에서)
config = EmailConfig(default_from_email="admin@company.com")
EmailService.init(config)

# 이메일 발송
result = await EmailService.send_simple_email(
    to_emails=["user@gmail.com"],
    subject="주식 알림",
    text_body="삼성전자가 목표가에 도달했습니다"
)
```
"""

from typing import Dict, Any, Optional, List
from service.core.logger import Logger
from .email_config import EmailConfig
from .email_client import SESClient


class EmailService:
    """
    이메일 서비스 (정적 클래스)
    
    StorageService와 완전히 동일한 패턴으로 구현:
    - 정적 메서드만 사용
    - _initialized 플래그로 초기화 상태 관리
    - init(), shutdown(), is_initialized() 제공
    - ServiceContainer에서 생명주기 관리
    
    왜 정적 클래스인가?
    - 전역에서 EmailService.send_email() 형태로 간편하게 사용
    - 인스턴스 생성 없이 바로 사용 가능
    - 다른 서비스들과 일관된 패턴
    """
    
    # 클래스 변수 (모든 인스턴스가 공유)
    _config: Optional[EmailConfig] = None        # 이메일 설정
    _client: Optional[SESClient] = None          # SES 클라이언트 (단일)
    _initialized: bool = False                   # 초기화 완료 여부

    @classmethod
    def init(cls, config: EmailConfig) -> bool:
        """
        이메일 서비스 초기화
        
        main.py의 서비스 초기화 단계에서 호출됩니다.
        여기서는 설정만 저장하고, 실제 AWS 연결은 나중에 지연 생성합니다.
        
        Args:
            config: EmailConfig 객체 (AWS 인증정보, 기본 발신자 등)
            
        Returns:
            bool: 초기화 성공 여부
        """
        try:
            cls._config = config
            cls._initialized = True
            Logger.info("EmailService 초기화 완료")
            return True
        except Exception as e:
            Logger.error(f"EmailService 초기화 실패: {e}")
            return False

    @classmethod
    async def shutdown(cls):
        """
        이메일 서비스 종료
        
        애플리케이션 종료 시 호출되어 리소스를 정리합니다.
        AWS 연결을 종료하고 메모리를 해제합니다.
        """
        try:
            if cls._client:
                await cls._client.close()
                cls._client = None
            cls._config = None
            cls._initialized = False
            Logger.info("EmailService 종료 완료")
        except Exception as e:
            Logger.error(f"EmailService 종료 중 에러: {e}")

    @classmethod
    def is_initialized(cls) -> bool:
        """
        초기화 여부 확인
        
        ServiceContainer에서 서비스 상태 체크할 때 사용
        
        Returns:
            bool: 초기화 완료 여부
        """
        return cls._initialized

    @classmethod
    async def _get_client(cls) -> SESClient:
        """
        SES 클라이언트 가져오기 (내부용)
        
        지연 생성(Lazy Loading) 패턴을 사용합니다.
        - 처음 호출될 때만 AWS에 연결
        - 이후에는 기존 연결 재사용
        - 연결이 끊어지면 자동으로 재연결
        
        Returns:
            SESClient: 초기화된 SES 클라이언트
            
        Raises:
            RuntimeError: 서비스가 초기화되지 않은 경우
        """
        if not cls._initialized:
            raise RuntimeError("EmailService가 초기화되지 않았습니다. init()을 먼저 호출하세요.")
        
        # 클라이언트가 없거나 연결이 끊어진 경우 새로 생성
        if not cls._client:
            cls._client = SESClient(cls._config)
            await cls._client.start()
        
        return cls._client

    # ====================================================================
    # 핵심 이메일 발송 메서드들
    # ====================================================================

    @classmethod
    async def send_simple_email(cls, 
                               to_emails: List[str],
                               subject: str,
                               text_body: Optional[str] = None,
                               html_body: Optional[str] = None,
                               from_email: Optional[str] = None,
                               from_name: Optional[str] = None,
                               **kwargs) -> Dict[str, Any]:
        """
        간단한 이메일 발송
        
        가장 많이 사용될 메서드입니다. 
        주식 알림, 시스템 공지 등 일반적인 이메일 발송에 사용합니다.
        
        Args:
            to_emails: 받는 사람 이메일 목록 (예: ["user@gmail.com"])
            subject: 이메일 제목
            text_body: 텍스트 본문 (일반 텍스트)
            html_body: HTML 본문 (꾸밈 있는 버전)
            from_email: 발신자 이메일 (없으면 config 기본값 사용)
            from_name: 발신자 이름 (예: "Finance App")
            **kwargs: 추가 파라미터 (reply_to, cc, bcc 등)
            
        Returns:
            dict: 발송 결과
            {
                "success": True/False,
                "message_id": "AWS에서 받은 메시지 ID",
                "error": "에러가 있는 경우 에러 메시지"
            }
            
        예시:
        ```python
        # 주식 알림 이메일
        result = await EmailService.send_simple_email(
            to_emails=["user@gmail.com"],
            subject="[매매 신호] 삼성전자 매수 신호 발생",
            text_body="삼성전자(005930)가 목표가 50,000원에 도달했습니다.",
            html_body="<h1>매수 신호</h1><p>삼성전자가 목표가에 도달했습니다.</p>",
            from_name="AI 트레이딩"
        )
        ```
        """
        try:
            client = await cls._get_client()
            
            # SESClient의 send_email 메서드 호출
            result = await client.send_email(
                to_addresses=to_emails,
                subject=subject,
                body_text=text_body,
                body_html=html_body,
                from_email=from_email,
                from_name=from_name,
                **kwargs  # reply_to, cc_addresses, bcc_addresses 등
            )
            
            return result
            
        except Exception as e:
            Logger.error(f"간단한 이메일 발송 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    @classmethod
    async def send_templated_email(cls,
                                  to_emails: List[str],
                                  template_name: str,
                                  template_data: Dict[str, Any],
                                  from_email: Optional[str] = None,
                                  **kwargs) -> Dict[str, Any]:
        """
        템플릿 이메일 발송
        
        미리 AWS SES에 저장한 템플릿을 사용해서 개인화된 이메일을 보냅니다.
        대량 발송이나 정형화된 이메일에 사용합니다.
        
        Args:
            to_emails: 받는 사람 목록
            template_name: AWS SES에 저장된 템플릿 이름
            template_data: 템플릿 변수에 넣을 데이터
            from_email: 발신자 이메일
            **kwargs: 추가 파라미터
            
        Returns:
            dict: 발송 결과
            
        예시:
        ```python
        # 예측 알림 템플릿 이메일
        result = await EmailService.send_templated_email(
            to_emails=["user@gmail.com"],
            template_name="prediction_alert",
            template_data={
                "user_name": "홍길동",
                "stock_name": "삼성전자",
                "prediction": "상승",
                "target_price": "55000"
            }
        )
        ```
        """
        try:
            client = await cls._get_client()
            
            result = await client.send_templated_email(
                to_addresses=to_emails,
                template_name=template_name,
                template_data=template_data,
                from_email=from_email,
                **kwargs
            )
            
            return result
            
        except Exception as e:
            Logger.error(f"템플릿 이메일 발송 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    @classmethod
    async def send_bulk_emails(cls,
                              destinations: List[Dict[str, Any]],
                              template_name: str,
                              default_data: Optional[Dict[str, Any]] = None,
                              from_email: Optional[str] = None,
                              **kwargs) -> Dict[str, Any]:
        """
        대량 템플릿 이메일 발송
        
        1000명에게 개인화된 이메일을 한 번에 보낼 때 사용합니다.
        예: 일일 포트폴리오 리포트, 시장 분석 리포트 등
        
        Args:
            destinations: 수신자별 데이터
            [
                {"email": "user1@gmail.com", "data": {"name": "홍길동", "stocks": ["삼성전자"]}},
                {"email": "user2@naver.com", "data": {"name": "김영희", "stocks": ["LG전자"]}}
            ]
            template_name: 템플릿 이름
            default_data: 모든 이메일에 공통으로 들어갈 데이터
            from_email: 발신자 이메일
            **kwargs: 추가 파라미터
            
        Returns:
            dict: 발송 결과 (성공한 이메일 수, 실패한 이메일 수 등)
            
        예시:
        ```python
        # 1000명에게 일일 리포트 발송
        users = [
            {"email": "user1@gmail.com", "data": {"name": "홍길동", "portfolio_value": "1,000,000"}},
            {"email": "user2@naver.com", "data": {"name": "김영희", "portfolio_value": "2,000,000"}}
        ]
        
        result = await EmailService.send_bulk_emails(
            destinations=users,
            template_name="daily_report",
            default_data={"report_date": "2024-01-15"}
        )
        ```
        """
        try:
            client = await cls._get_client()
            
            result = await client.send_bulk_templated_email(
                destinations=destinations,
                template_name=template_name,
                default_template_data=default_data,
                from_email=from_email,
                **kwargs
            )
            
            return result
            
        except Exception as e:
            Logger.error(f"대량 이메일 발송 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    # ====================================================================
    # 유틸리티 메서드들
    # ====================================================================

    @classmethod
    async def verify_email_address(cls, email: str) -> Dict[str, Any]:
        """
        이메일 주소 검증
        
        AWS SES에서 이메일을 보내려면 먼저 발신자 이메일을 검증해야 합니다.
        이 메서드를 호출하면 해당 이메일로 검증 메일이 발송됩니다.
        
        Args:
            email: 검증할 이메일 주소
            
        Returns:
            dict: 검증 요청 결과
            
        예시:
        ```python
        # 새로운 발신자 이메일 검증
        result = await EmailService.verify_email_address("admin@mycompany.com")
        if result["success"]:
            print("검증 이메일이 발송되었습니다")
        ```
        """
        try:
            client = await cls._get_client()
            result = await client.verify_email_identity(email)
            return result
        except Exception as e:
            Logger.error(f"이메일 주소 검증 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    @classmethod
    async def get_send_statistics(cls) -> Dict[str, Any]:
        """
        발송 통계 조회
        
        지난 2주간의 이메일 발송 통계를 가져옵니다.
        모니터링과 알림 품질 관리에 사용합니다.
        
        Returns:
            dict: 발송 통계 데이터
            {
                "success": True,
                "statistics": [
                    {
                        "Timestamp": "2024-01-15T10:00:00Z",
                        "DeliveryAttempts": 100,  # 발송 시도
                        "Bounces": 2,             # 반송
                        "Complaints": 0,          # 스팸 신고
                        "Rejects": 1              # 거부
                    }
                ]
            }
            
        예시:
        ```python
        # 이메일 발송 품질 모니터링
        stats = await EmailService.get_send_statistics()
        if stats["success"]:
            for data in stats["statistics"]:
                bounce_rate = data["Bounces"] / data["DeliveryAttempts"] * 100
                print(f"반송률: {bounce_rate:.2f}%")
        ```
        """
        try:
            client = await cls._get_client()
            result = await client.get_send_statistics()
            return result
        except Exception as e:
            Logger.error(f"발송 통계 조회 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    # ====================================================================
    # 편의 메서드들 (자주 사용되는 패턴들)
    # ====================================================================

    @classmethod
    async def send_prediction_alert(cls,
                                   user_email: str,
                                   user_name: str,
                                   stock_symbol: str,
                                   stock_name: str,
                                   prediction_type: str,
                                   target_price: str,
                                   current_price: str,
                                   confidence: str) -> Dict[str, Any]:
        """
        주식 예측 알림 이메일 발송 (편의 메서드)
        
        알림 시스템에서 가장 많이 사용될 예측 알림 이메일을 간편하게 보냅니다.
        
        Args:
            user_email: 사용자 이메일
            user_name: 사용자 이름
            stock_symbol: 주식 코드 (예: "AAPL")
            stock_name: 주식 이름 (예: "Apple Inc.")
            prediction_type: 예측 종류 ("BUY", "SELL", "HOLD")
            target_price: 목표가
            current_price: 현재가
            confidence: 신뢰도 (예: "85%")
            
        Returns:
            dict: 발송 결과
        """
        # config에서 예측 알림 설정 가져오기
        email_config = cls._config.email_types.get("prediction_alert", {})
        subject_prefix = email_config.get("subject_prefix", "[매매 신호]")
        
        # 예측 타입에 따른 한글 변환
        prediction_text = {
            "BUY": "매수",
            "SELL": "매도", 
            "HOLD": "보유"
        }.get(prediction_type, prediction_type)
        
        # 이메일 제목과 본문 구성
        subject = f"{subject_prefix} {stock_name}({stock_symbol}) {prediction_text} 신호"
        
        text_body = f"""
안녕하세요 {user_name}님,

AI 분석 결과 다음과 같은 매매 신호가 발생했습니다.

📈 종목: {stock_name} ({stock_symbol})
🎯 신호: {prediction_text}
💰 목표가: ${target_price}
📊 현재가: ${current_price}
🔍 신뢰도: {confidence}

이 신호는 AI 모델의 분석 결과이며, 투자 결정은 신중하게 하시기 바랍니다.

감사합니다.
AI Trading Platform
"""

        html_body = f"""
<h2>매매 신호 알림</h2>
<p>안녕하세요 <strong>{user_name}</strong>님,</p>
<p>AI 분석 결과 다음과 같은 매매 신호가 발생했습니다.</p>

<table style="border-collapse: collapse; width: 100%;">
<tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>종목</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{stock_name} ({stock_symbol})</td></tr>
<tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>신호</strong></td><td style="padding: 8px; border: 1px solid #ddd; color: {'green' if prediction_type == 'BUY' else 'red' if prediction_type == 'SELL' else 'blue'};">{prediction_text}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>목표가</strong></td><td style="padding: 8px; border: 1px solid #ddd;">${target_price}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>현재가</strong></td><td style="padding: 8px; border: 1px solid #ddd;">${current_price}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>신뢰도</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{confidence}</td></tr>
</table>

<p><small>이 신호는 AI 모델의 분석 결과이며, 투자 결정은 신중하게 하시기 바랍니다.</small></p>
<p>감사합니다.<br><strong>AI Trading Platform</strong></p>
"""

        # 이메일 발송
        return await cls.send_simple_email(
            to_emails=[user_email],
            subject=subject,
            text_body=text_body,
            html_body=html_body,
            from_name="AI Trading Platform"
        )

    @classmethod
    async def send_system_notice(cls,
                                user_emails: List[str],
                                notice_title: str,
                                notice_content: str) -> Dict[str, Any]:
        """
        시스템 공지 이메일 발송 (편의 메서드)
        
        시스템 점검, 업데이트, 장애 등의 공지사항을 발송합니다.
        
        Args:
            user_emails: 받을 사용자 이메일 목록
            notice_title: 공지 제목
            notice_content: 공지 내용
            
        Returns:
            dict: 발송 결과
        """
        subject_prefix = cls._config.email_types.get("system_notice", {}).get("subject_prefix", "[시스템 공지]")
        subject = f"{subject_prefix} {notice_title}"
        
        return await cls.send_simple_email(
            to_emails=user_emails,
            subject=subject,
            text_body=notice_content,
            html_body=f"<h2>{notice_title}</h2><p>{notice_content.replace(chr(10), '<br>')}</p>",
            from_name="AI Trading Platform"
        )