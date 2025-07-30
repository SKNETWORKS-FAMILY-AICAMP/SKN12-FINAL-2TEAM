"""
AWS SES 이메일 클라이언트

이 파일은 AWS SES(Simple Email Service)를 사용해서 이메일을 보내는 클라이언트입니다.
기존 S3Client, OpenSearchClient와 완전히 동일한 패턴으로 구현했습니다.

주요 개념:
1. AWS SES: 아마존의 이메일 발송 서비스 (Gmail, Outlook 같은 것의 기업용 버전)
2. boto3: 파이썬에서 AWS 서비스를 사용하기 위한 공식 라이브러리
3. 비동기: 이메일 발송은 시간이 걸리므로 다른 작업을 막지 않도록 비동기로 처리
4. 에러 처리: AWS에서 에러가 나면 친화적인 메시지로 변환해서 반환
"""
import asyncio
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

# boto3: AWS를 파이썬에서 사용하기 위한 라이브러리
# 설치되어 있지 않을 수도 있으니 try-except로 체크
try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    # boto3가 설치되지 않은 경우
    BOTO3_AVAILABLE = False

from service.core.logger import Logger
from .email_config import EmailConfig


class SESClient:
    """
    AWS SES 클라이언트 클래스
    
    이 클래스는 실제로 이메일을 보내는 역할을 합니다.
    
    왜 클래스로 만들었나?
    - AWS 연결 정보(인증키, 리전 등)를 저장해두고 재사용하기 위해
    - 여러 번 이메일을 보낼 때마다 새로 연결하지 않고 한 번만 연결하기 위해
    - 에러 처리, 로깅 등을 일관되게 하기 위해
    
    기존 S3Client, OpenSearchClient와 완전히 동일한 구조:
    - __init__: 설정만 저장
    - start(): 실제 AWS 연결
    - close(): 연결 종료
    - 각종 메서드: 실제 기능 수행
    """
    
    def __init__(self, config: EmailConfig):
        """
        SES 클라이언트 초기화
        
        이 단계에서는 아직 AWS에 연결하지 않습니다.
        설정만 저장해두고, 실제 연결은 start() 메서드에서 합니다.
        
        Args:
            config: EmailConfig 객체 (AWS 접속 정보, 이메일 설정 등이 들어있음)
        """
        # boto3가 설치되어 있는지 확인
        if not BOTO3_AVAILABLE:
            raise ImportError("boto3가 설치되지 않았습니다. pip install boto3로 설치하세요")
        
        self.config = config           # 설정 저장
        self._client = None           # AWS SES 클라이언트 (나중에 start()에서 생성)
        self._initialized = False     # 초기화 완료 여부 플래그
    
    async def start(self):
        """
        AWS SES에 실제로 연결하는 메서드
        
        왜 별도 메서드로 분리했나?
        - __init__에서 하면 동기 함수가 되어버림
        - AWS 연결은 시간이 걸릴 수 있으므로 비동기로 처리
        - 에러가 나면 여기서 잡아서 처리
        """
        try:
            # boto3 세션 설정 준비
            # session_kwargs: boto3.client()에 전달할 파라미터들을 딕셔너리로 모음
            session_kwargs = {
                'region_name': self.config.region_name  # AWS 리전 (예: ap-northeast-2 = 서울)
            }
            
            # AWS 인증 정보가 설정에 있으면 추가
            # 인증 정보가 없으면 AWS CLI 설정이나 IAM Role을 사용
            if self.config.aws_access_key_id:
                session_kwargs['aws_access_key_id'] = self.config.aws_access_key_id
            if self.config.aws_secret_access_key:
                session_kwargs['aws_secret_access_key'] = self.config.aws_secret_access_key
            if self.config.aws_session_token:
                session_kwargs['aws_session_token'] = self.config.aws_session_token
            
            # boto3 클라이언트 생성
            # 'ses'라고 하면 AWS SES 서비스에 연결됨
            self._client = boto3.client('ses', **session_kwargs)
            self._initialized = True
            
            Logger.info(f"SES 클라이언트가 초기화되었습니다. 리전: {self.config.region_name}")
            
        except Exception as e:
            Logger.error(f"SES 클라이언트 초기화 실패: {e}")
            raise
    
    async def close(self):
        """
        AWS 연결 종료
        
        사실 boto3는 명시적으로 종료할 필요가 없지만,
        기존 다른 클라이언트들과 일관성을 위해 만들어둠
        """
        if self._client:
            self._client = None
            self._initialized = False
            Logger.info("SES 클라이언트가 종료되었습니다")
    
    def _ensure_initialized(self):
        """
        클라이언트가 초기화되었는지 확인하는 헬퍼 메서드
        
        모든 실제 기능 메서드에서 맨 처음에 호출해서
        초기화가 안되어 있으면 에러를 던짐
        """
        if not self._initialized or not self._client:
            raise RuntimeError("SES 클라이언트가 초기화되지 않았습니다. start()를 먼저 호출하세요.")
    
    async def send_email(self, 
                        to_addresses: List[str],
                        subject: str,
                        body_text: Optional[str] = None,
                        body_html: Optional[str] = None,
                        from_email: Optional[str] = None,
                        from_name: Optional[str] = None,
                        reply_to: Optional[List[str]] = None,
                        cc_addresses: Optional[List[str]] = None,
                        bcc_addresses: Optional[List[str]] = None,
                        configuration_set: Optional[str] = None,
                        tags: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        이메일 발송 메서드
        
        가장 중요한 메서드입니다. 실제로 이메일을 보내는 기능.
        
        파라미터 설명:
        - to_addresses: 받는 사람 이메일 목록 (예: ["user1@gmail.com", "user2@naver.com"])
        - subject: 이메일 제목
        - body_text: 텍스트 버전 본문 (일반 텍스트)
        - body_html: HTML 버전 본문 (꾸밈 있는 버전)
        - from_email: 보내는 사람 이메일 (없으면 config에서 기본값 사용)
        - from_name: 보내는 사람 이름 (예: "Finance App")
        - reply_to: 답장받을 이메일 주소
        - cc_addresses: 참조 (다른 사람들도 볼 수 있음)
        - bcc_addresses: 숨은 참조 (다른 사람들이 못 봄)
        - configuration_set: AWS SES 설정 그룹 (고급 기능)
        - tags: 이메일에 붙일 태그 (분석용)
        
        Returns:
            dict: 성공하면 {"success": True, "message_id": "xxx"}
                  실패하면 {"success": False, "error": "에러메시지"}
        """
        # 초기화 확인
        self._ensure_initialized()
        
        try:
            # 1. 발신자 설정
            if not from_email:
                # 발신자 이메일이 없으면 config에서 기본값 사용
                from_email = self.config.default_from_email
            
            # 발신자 이름이 있으면 "이름 <이메일>" 형태로 만듦
            source = from_email
            if from_name:
                source = f"{from_name} <{from_email}>"
            
            # 2. 수신자 설정
            destination = {"ToAddresses": to_addresses}  # 받는 사람들
            if cc_addresses:
                destination["CcAddresses"] = cc_addresses  # 참조
            if bcc_addresses:
                destination["BccAddresses"] = bcc_addresses  # 숨은 참조
            
            # 3. 이메일 제목 설정
            message = {
                "Subject": {
                    "Data": subject,  # 제목 텍스트
                    "Charset": self.config.default_charset  # 문자 인코딩 (UTF-8)
                }
            }
            
            # 4. 이메일 본문 설정
            body = {}
            if body_text:
                # 텍스트 버전 본문 (일반 텍스트)
                body["Text"] = {
                    "Data": body_text,
                    "Charset": self.config.default_charset
                }
            if body_html:
                # HTML 버전 본문 (꾸밈 있는 버전)
                body["Html"] = {
                    "Data": body_html,
                    "Charset": self.config.default_charset
                }
            
            # 텍스트나 HTML 중 하나는 반드시 있어야 함
            if not body:
                return {"success": False, "error": "이메일 본문(텍스트 또는 HTML)이 필요합니다"}
            
            message["Body"] = body
            
            # 5. AWS SES API 호출용 파라미터 구성
            params = {
                "Source": source,           # 보내는 사람
                "Destination": destination, # 받는 사람들
                "Message": message         # 제목과 본문
            }
            
            # 선택적 파라미터들 추가
            if reply_to:
                params["ReplyToAddresses"] = reply_to
            
            if configuration_set or self.config.configuration_set:
                params["ConfigurationSetName"] = configuration_set or self.config.configuration_set
            
            if tags:
                # 태그를 AWS API 형태로 변환 {"key": "value"} → [{"Name": "key", "Value": "value"}]
                params["Tags"] = [{"Name": k, "Value": v} for k, v in tags.items()]
            
            # 6. 실제 이메일 발송
            # AWS API 호출은 시간이 걸리므로 run_in_executor로 비동기 처리
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,  # 기본 스레드 풀 사용
                lambda: self._client.send_email(**params)  # 실제 AWS API 호출
            )
            
            # 7. 성공 처리
            message_id = response.get("MessageId", "")  # AWS에서 받은 메시지 ID
            
            Logger.info(f"이메일 발송 성공. MessageId: {message_id}")
            
            return {
                "success": True,
                "message_id": message_id,
                "response": response  # 전체 AWS 응답 (디버깅용)
            }
            
        except ClientError as e:
            # AWS에서 온 에러 (권한 없음, 잘못된 이메일 주소 등)
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            Logger.error(f"SES 이메일 발송 실패: {error_code} - {error_message}")
            
            return {
                "success": False,
                "error": f"{error_code}: {error_message}",
                "error_code": error_code
            }
            
        except Exception as e:
            # 예상치 못한 에러
            Logger.error(f"SES 이메일 발송 중 예상치 못한 에러: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_templated_email(self,
                                  to_addresses: List[str],
                                  template_name: str,
                                  template_data: Dict[str, Any],
                                  from_email: Optional[str] = None,
                                  configuration_set: Optional[str] = None,
                                  tags: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        템플릿 이메일 발송
        
        AWS SES 템플릿 기능을 사용하는 고급 기능입니다.
        
        템플릿이란?
        - 미리 AWS SES에 저장해둔 이메일 양식
        - 제목과 본문에 {{name}}, {{amount}} 같은 변수를 넣어둠
        - 발송할 때마다 변수만 바꿔서 개인화된 이메일 보냄
        
        예시:
        - 템플릿: "안녕하세요 {{name}}님, {{stock}} 주식이 {{price}}원에 도달했습니다"
        - template_data: {"name": "홍길동", "stock": "삼성전자", "price": "50000"}
        - 결과: "안녕하세요 홍길동님, 삼성전자 주식이 50000원에 도달했습니다"
        
        Args:
            to_addresses: 받는 사람 목록
            template_name: AWS SES에 저장된 템플릿 이름
            template_data: 템플릿 변수에 넣을 데이터
            from_email: 발신자 이메일
            configuration_set: SES 구성 세트
            tags: 메시지 태그
            
        Returns:
            dict: 발송 결과
        """
        self._ensure_initialized()
        
        try:
            # 발신자 설정
            source = from_email or self.config.default_from_email
            
            # 템플릿 데이터 병합
            # config에 있는 기본 데이터(회사명, 지원 이메일 등) + 사용자가 준 데이터
            merged_data = {**self.config.default_template_data, **template_data}
            
            # AWS SES API 파라미터 구성
            params = {
                "Source": source,
                "Destination": {"ToAddresses": to_addresses},
                "Template": template_name,  # 템플릿 이름
                "TemplateData": json.dumps(merged_data)  # 데이터를 JSON 문자열로 변환
            }
            
            if configuration_set or self.config.configuration_set:
                params["ConfigurationSetName"] = configuration_set or self.config.configuration_set
            
            if tags:
                params["Tags"] = [{"Name": k, "Value": v} for k, v in tags.items()]
            
            # 템플릿 이메일 발송
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._client.send_templated_email(**params)
            )
            
            message_id = response.get("MessageId", "")
            
            Logger.info(f"템플릿 이메일 발송 성공. MessageId: {message_id}, Template: {template_name}")
            
            return {
                "success": True,
                "message_id": message_id,
                "template_name": template_name,
                "response": response
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            Logger.error(f"SES 템플릿 이메일 발송 실패: {error_code} - {error_message}")
            
            return {
                "success": False,
                "error": f"{error_code}: {error_message}",
                "error_code": error_code
            }
            
        except Exception as e:
            Logger.error(f"SES 템플릿 이메일 발송 중 예상치 못한 에러: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_bulk_templated_email(self,
                                       destinations: List[Dict[str, Any]],
                                       template_name: str,
                                       default_template_data: Optional[Dict[str, Any]] = None,
                                       from_email: Optional[str] = None,
                                       configuration_set: Optional[str] = None,
                                       tags: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        대량 템플릿 이메일 발송
        
        한 번의 API 호출로 여러 사람에게 개인화된 이메일을 보내는 기능.
        예측 알림 같은 걸 1000명에게 한번에 보낼 때 사용.
        
        destinations 형태 예시:
        [
            {"email": "user1@gmail.com", "data": {"name": "홍길동", "stock": "삼성전자"}},
            {"email": "user2@naver.com", "data": {"name": "김영희", "stock": "LG전자"}},
            ...
        ]
        
        Args:
            destinations: 수신자별 데이터 목록
            template_name: 템플릿 이름
            default_template_data: 모든 이메일에 공통으로 들어갈 데이터
            from_email: 발신자
            configuration_set: 구성 세트
            tags: 태그
            
        Returns:
            dict: 발송 결과 (message_ids 리스트 포함)
        """
        self._ensure_initialized()
        
        try:
            # 기본 템플릿 데이터 준비
            base_data = {**self.config.default_template_data}
            if default_template_data:
                base_data.update(default_template_data)
            
            # AWS SES 대량 발송 API에 맞는 형태로 변환
            ses_destinations = []
            for dest in destinations:
                # 기본 데이터 + 사용자별 데이터 병합
                user_data = {**base_data, **dest.get("data", {})}
                ses_destinations.append({
                    "Destination": {"ToAddresses": [dest["email"]]},
                    "ReplacementTemplateData": json.dumps(user_data)  # 개인별 데이터
                })
            
            # API 파라미터 구성
            params = {
                "Source": from_email or self.config.default_from_email,
                "Template": template_name,
                "DefaultTemplateData": json.dumps(base_data),  # 공통 데이터
                "Destinations": ses_destinations  # 개인별 데이터 목록
            }
            
            if configuration_set or self.config.configuration_set:
                params["ConfigurationSetName"] = configuration_set or self.config.configuration_set
            
            if tags:
                params["Tags"] = [{"Name": k, "Value": v} for k, v in tags.items()]
            
            # 대량 발송 실행
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._client.send_bulk_templated_email(**params)
            )
            
            # 각 이메일별로 받은 메시지 ID들
            message_ids = [msg.get("MessageId", "") for msg in response.get("MessageIds", [])]
            
            Logger.info(f"대량 이메일 발송 성공. 수량: {len(message_ids)}, Template: {template_name}")
            
            return {
                "success": True,
                "message_ids": message_ids,
                "count": len(message_ids),
                "template_name": template_name,
                "response": response
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            Logger.error(f"SES 대량 템플릿 이메일 발송 실패: {error_code} - {error_message}")
            
            return {
                "success": False,
                "error": f"{error_code}: {error_message}",
                "error_code": error_code
            }
            
        except Exception as e:
            Logger.error(f"SES 대량 템플릿 이메일 발송 중 예상치 못한 에러: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def verify_email_identity(self, email: str) -> Dict[str, Any]:
        """
        이메일 주소 검증
        
        AWS SES에서 이메일을 보내려면 먼저 보내는 이메일 주소를 검증해야 합니다.
        이 메서드를 호출하면 해당 이메일로 검증 메일이 발송됩니다.
        
        예시:
        1. verify_email_identity("admin@mycompany.com") 호출
        2. admin@mycompany.com으로 검증 메일 발송됨
        3. 메일의 링크를 클릭하면 검증 완료
        4. 이제 admin@mycompany.com으로 이메일 발송 가능
        
        Args:
            email: 검증할 이메일 주소
            
        Returns:
            dict: 검증 요청 결과
        """
        self._ensure_initialized()
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._client.verify_email_identity(EmailAddress=email)
            )
            
            Logger.info(f"이메일 검증 요청 발송됨: {email}")
            
            return {
                "success": True,
                "email": email,
                "message": "검증 이메일이 발송되었습니다"
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            Logger.error(f"SES 이메일 검증 실패: {error_code} - {error_message}")
            
            return {
                "success": False,
                "error": f"{error_code}: {error_message}",
                "error_code": error_code
            }
            
        except Exception as e:
            Logger.error(f"SES 이메일 검증 중 예상치 못한 에러: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_send_statistics(self) -> Dict[str, Any]:
        """
        발송 통계 조회
        
        지난 2주간의 이메일 발송 통계를 가져옵니다.
        - 발송된 이메일 수
        - 반송(Bounce) 수
        - 스팸 신고(Complaint) 수
        - 거부(Reject) 수
        
        이 데이터를 보고 이메일 발송 품질을 모니터링할 수 있습니다.
        
        Returns:
            dict: 발송 통계 데이터
        """
        self._ensure_initialized()
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._client.get_send_statistics()
            )
            
            return {
                "success": True,
                "statistics": response.get("SendDataPoints", [])
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            Logger.error(f"SES 발송 통계 조회 실패: {error_code} - {error_message}")
            
            return {
                "success": False,
                "error": f"{error_code}: {error_message}",
                "error_code": error_code
            }
            
        except Exception as e:
            Logger.error(f"SES 발송 통계 조회 중 예상치 못한 에러: {e}")
            return {
                "success": False,
                "error": str(e)
            }