"""
AWS SNS SMS 클라이언트

이 파일은 AWS SNS(Simple Notification Service)를 사용해서 SMS를 보내는 클라이언트입니다.
기존 SESClient와 완전히 동일한 패턴으로 구현했습니다.

주요 개념:
1. AWS SNS: 아마존의 알림 서비스 (SMS, 푸시, 이메일, 웹훅 통합)
2. SMS vs 다른 채널: SMS는 비용이 높고 글자 제한이 있어서 중요한 알림만 발송
3. 메시지 타입: Transactional(중요) vs Promotional(광고) - 비용과 전송률이 다름
4. 전화번호 형식: 국제 형식(+82-10-1234-5678) 필수
5. 비용 관리: SMS는 건당 비용이 발생하므로 발송량 제한 필요

사용 시나리오:
- 급락/급등 알림: "삼성전자 -5% 급락 감지"
- 매매 신호: "AAPL 매수 신호 발생, 목표가 $150"
- 시스템 장애: "시스템 점검 완료, 정상 서비스 재개"
- 보안 알림: "새로운 기기에서 로그인 감지"
"""

import asyncio
import json
import re
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

# boto3: AWS를 파이썬에서 사용하기 위한 라이브러리
try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    # boto3가 설치되지 않은 경우
    BOTO3_AVAILABLE = False

from service.core.logger import Logger
from .sms_config import SmsConfig


class SNSClient:
    """
    AWS SNS SMS 클라이언트 클래스
    
    이 클래스는 실제로 SMS를 보내는 역할을 합니다.
    SESClient와 완전히 동일한 구조로 구현되어 있습니다.
    
    주요 차이점:
    - 이메일 대신 SMS 발송
    - 메시지 길이 제한 (160자/70자)
    - 전화번호 유효성 검사
    - 발송 비용이 높아서 더 엄격한 제한
    - 국가별 발송 규칙 다름
    """
    
    def __init__(self, config: SmsConfig):
        """
        SNS 클라이언트 초기화
        
        Args:
            config: SmsConfig 객체 (AWS 접속 정보, SMS 설정 등)
        """
        if not BOTO3_AVAILABLE:
            raise ImportError("boto3가 설치되지 않았습니다. pip install boto3로 설치하세요")
        
        self.config = config
        self._client = None           # AWS SNS 클라이언트
        self._initialized = False     # 초기화 완료 여부
        
        # 전화번호 검증용 정규식 패턴
        # 국제 형식: +82-10-1234-5678 또는 +821012345678
        self._phone_pattern = re.compile(r'^\+\d{1,3}[\d\-\s]{7,15}$')
    
    async def start(self):
        """
        AWS SNS에 실제로 연결하는 메서드
        """
        try:
            # boto3 세션 설정
            session_kwargs = {
                'region_name': self.config.region_name
            }
            
            # AWS 인증 정보 추가
            if self.config.aws_access_key_id:
                session_kwargs['aws_access_key_id'] = self.config.aws_access_key_id
            if self.config.aws_secret_access_key:
                session_kwargs['aws_secret_access_key'] = self.config.aws_secret_access_key
            if self.config.aws_session_token:
                session_kwargs['aws_session_token'] = self.config.aws_session_token
            
            # boto3 SNS 클라이언트 생성
            self._client = boto3.client('sns', **session_kwargs)
            self._initialized = True
            
            Logger.info(f"SNS 클라이언트가 초기화되었습니다. 리전: {self.config.region_name}")
            
        except Exception as e:
            Logger.error(f"SNS 클라이언트 초기화 실패: {e}")
            raise
    
    async def close(self):
        """
        AWS 연결 종료
        """
        if self._client:
            self._client = None
            self._initialized = False
            Logger.info("SNS 클라이언트가 종료되었습니다")
    
    def _ensure_initialized(self):
        """
        클라이언트가 초기화되었는지 확인
        """
        if not self._initialized or not self._client:
            raise RuntimeError("SNS 클라이언트가 초기화되지 않았습니다. start()를 먼저 호출하세요.")
    
    def _validate_phone_number(self, phone_number: str) -> Dict[str, Any]:
        """
        전화번호 유효성 검사
        
        SMS는 잘못된 번호로 보내도 비용이 발생하므로 사전 검증이 중요합니다.
        
        Args:
            phone_number: 검증할 전화번호
            
        Returns:
            dict: 검증 결과
            {
                "valid": True/False,
                "formatted": "정규화된 번호",
                "country_code": "국가코드",
                "error": "에러 메시지 (에러가 있는 경우)"
            }
        """
        # 1. 기본 형식 검사
        if not phone_number:
            return {"valid": False, "error": "전화번호가 비어있습니다"}
        
        # 공백 제거
        phone_number = phone_number.strip()
        
        # 2. 국제 형식 확인 (+로 시작)
        if not phone_number.startswith('+'):
            return {"valid": False, "error": "국제 형식(+로 시작)이 아닙니다"}
        
        # 3. 정규식 패턴 매칭
        if not self._phone_pattern.match(phone_number):
            return {"valid": False, "error": "전화번호 형식이 올바르지 않습니다"}
        
        # 4. 국가코드 추출
        # +82-10-1234-5678 -> +82
        country_code = None
        for supported in self.config.supported_countries:
            if phone_number.startswith(supported):
                country_code = supported
                break
        
        if not country_code:
            return {
                "valid": False, 
                "error": f"지원하지 않는 국가입니다. 지원 국가: {self.config.supported_countries}"
            }
        
        # 5. 차단된 접두사 확인
        for blocked in self.config.phone_validation.get("blocked_prefixes", []):
            if phone_number.startswith(blocked):
                return {"valid": False, "error": f"차단된 번호 유형입니다: {blocked}"}
        
        # 6. 번호 정규화 (하이픈, 공백 제거)
        formatted = re.sub(r'[\s\-]', '', phone_number)
        
        return {
            "valid": True,
            "formatted": formatted,
            "country_code": country_code,
            "original": phone_number
        }
    
    def _validate_message_content(self, message: str, message_type: str = "prediction_alert") -> Dict[str, Any]:
        """
        SMS 메시지 내용 유효성 검사
        
        SMS는 길이 제한과 스팸 규정이 있으므로 사전 검증이 필요합니다.
        
        Args:
            message: 보낼 메시지 내용
            message_type: 메시지 타입 (config.message_types 키)
            
        Returns:
            dict: 검증 결과
        """
        if not message:
            return {"valid": False, "error": "메시지가 비어있습니다"}
        
        # 1. 길이 검사
        max_length = self.config.max_message_length
        if len(message) > max_length:
            return {
                "valid": False, 
                "error": f"메시지가 너무 깁니다. 최대 {max_length}자 (현재: {len(message)}자)"
            }
        
        # 2. 스팸 필터 (활성화된 경우)
        if self.config.content_filter.get("enable_spam_filter", False):
            blocked_keywords = self.config.content_filter.get("blocked_keywords", [])
            for keyword in blocked_keywords:
                if keyword in message:
                    return {"valid": False, "error": f"차단된 키워드 포함: {keyword}"}
        
        # 3. URL 개수 제한
        url_count = len(re.findall(r'http[s]?://\S+', message))
        max_urls = self.config.content_filter.get("max_url_count", 1)
        if url_count > max_urls:
            return {"valid": False, "error": f"URL이 너무 많습니다. 최대 {max_urls}개"}
        
        return {"valid": True, "message": message}
    
    async def send_sms(self,
                      phone_number: str,
                      message: str,
                      message_type: str = "prediction_alert",
                      sender_id: Optional[str] = None,
                      message_attributes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        SMS 발송 메서드
        
        가장 중요한 메서드입니다. 실제로 SMS를 보내는 기능.
        
        Args:
            phone_number: 받는 사람 전화번호 (국제 형식, 예: +82-10-1234-5678)
            message: 보낼 메시지 내용
            message_type: 메시지 타입 (config.message_types의 키값)
            sender_id: 발신자 표시명 (일부 국가에서만 지원)
            message_attributes: 추가 메시지 속성 (우선도, 만료시간 등)
            
        Returns:
            dict: 발송 결과
            {
                "success": True/False,
                "message_id": "AWS에서 받은 메시지 ID",
                "phone_number": "정규화된 전화번호",
                "cost_estimate": "예상 비용",
                "error": "에러가 있는 경우"
            }
            
        예시:
        ```python
        # 주식 급등 알림
        result = await client.send_sms(
            phone_number="+82-10-1234-5678",
            message="[AI매매] 삼성전자: 매수 신호 (50,000원)",
            message_type="prediction_alert"
        )
        ```
        """
        self._ensure_initialized()
        
        try:
            # 1. 전화번호 유효성 검사
            phone_validation = self._validate_phone_number(phone_number)
            if not phone_validation["valid"]:
                return {
                    "success": False,
                    "error": f"전화번호 오류: {phone_validation['error']}",
                    "phone_number": phone_number
                }
            
            formatted_phone = phone_validation["formatted"]
            
            # 2. 메시지 내용 검사
            content_validation = self._validate_message_content(message, message_type)
            if not content_validation["valid"]:
                return {
                    "success": False,
                    "error": f"메시지 내용 오류: {content_validation['error']}",
                    "phone_number": formatted_phone
                }
            
            # 3. 메시지 타입별 설정 가져오기
            type_config = self.config.message_types.get(message_type, {})
            sns_message_type = type_config.get("type", self.config.default_message_type)
            display_sender_id = sender_id or type_config.get("sender_id", self.config.default_sender_id)
            
            # 4. AWS SNS 발송 파라미터 구성 (심플하게)
            # SMS는 MessageAttributes 없이 간단하게 보낼 수 있음
            params = {
                "PhoneNumber": formatted_phone,
                "Message": message
            }
            
            # 사용자 정의 속성 추가 (SMS는 지원 안함)
            # SMS 발송시 MessageAttributes는 사용하지 않음
            # 필요시 SNS Topic을 통해 발송하는 방식으로 변경 필요
            
            # 5. 실제 SMS 발송
            # AWS API 호출은 시간이 걸리므로 비동기 처리
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._client.publish(**params)
            )
            
            # 6. 성공 처리
            message_id = response.get("MessageId", "")
            
            # 예상 비용 계산 (대략적)
            cost_estimate = self.config.cost_management.get("cost_per_sms_usd", 0.05)
            
            Logger.info(f"SMS 발송 성공. MessageId: {message_id}, Phone: {formatted_phone}")
            
            return {
                "success": True,
                "message_id": message_id,
                "phone_number": formatted_phone,
                "message_type": sns_message_type,
                "cost_estimate_usd": cost_estimate,
                "response": response
            }
            
        except ClientError as e:
            # AWS에서 온 에러
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            Logger.error(f"SNS SMS 발송 실패: {error_code} - {error_message}")
            
            return {
                "success": False,
                "error": f"{error_code}: {error_message}",
                "error_code": error_code,
                "phone_number": phone_number
            }
            
        except Exception as e:
            # 예상치 못한 에러
            Logger.error(f"SNS SMS 발송 중 예상치 못한 에러: {e}")
            return {
                "success": False,
                "error": str(e),
                "phone_number": phone_number
            }
    
    async def send_bulk_sms(self,
                           recipients: List[Dict[str, str]],
                           message_template: str,
                           message_type: str = "prediction_alert",
                           sender_id: Optional[str] = None) -> Dict[str, Any]:
        """
        대량 SMS 발송
        
        여러 사람에게 개인화된 SMS를 보낼 때 사용합니다.
        비용이 많이 들므로 신중하게 사용해야 합니다.
        
        Args:
            recipients: 수신자 목록
            [
                {"phone": "+82-10-1111-1111", "name": "홍길동", "stock": "삼성전자"},
                {"phone": "+82-10-2222-2222", "name": "김영희", "stock": "LG전자"}
            ]
            message_template: 메시지 템플릿 (예: "안녕하세요 {name}님, {stock} 매수 신호입니다")
            message_type: 메시지 타입
            sender_id: 발신자 ID
            
        Returns:
            dict: 발송 결과
            {
                "success": True,
                "total_count": 100,
                "success_count": 95,
                "failed_count": 5,
                "results": [...],
                "total_cost_estimate": 4.75
            }
        """
        self._ensure_initialized()
        
        results = []
        success_count = 0
        failed_count = 0
        total_cost = 0.0
        
        try:
            # 각 수신자에게 개별 발송
            for recipient in recipients:
                phone = recipient.get("phone", "")
                if not phone:
                    failed_count += 1
                    results.append({
                        "phone": "",
                        "success": False,
                        "error": "전화번호가 없습니다"
                    })
                    continue
                
                # 템플릿에 개인화 데이터 적용
                try:
                    personalized_message = message_template.format(**recipient)
                except KeyError as e:
                    failed_count += 1
                    results.append({
                        "phone": phone,
                        "success": False,
                        "error": f"템플릿 변수 누락: {e}"
                    })
                    continue
                
                # 개별 SMS 발송
                result = await self.send_sms(
                    phone_number=phone,
                    message=personalized_message,
                    message_type=message_type,
                    sender_id=sender_id
                )
                
                results.append({
                    "phone": phone,
                    "success": result["success"],
                    "message_id": result.get("message_id", ""),
                    "error": result.get("error", "")
                })
                
                if result["success"]:
                    success_count += 1
                    total_cost += result.get("cost_estimate_usd", 0.05)
                else:
                    failed_count += 1
                
                # 발송률 제한 (과금 방지)
                if len(recipients) > 10:  # 10건 이상일 때만 지연
                    await asyncio.sleep(1.0 / self.config.max_send_rate)
            
            Logger.info(f"대량 SMS 발송 완료. 성공: {success_count}, 실패: {failed_count}")
            
            return {
                "success": True,
                "total_count": len(recipients),
                "success_count": success_count,
                "failed_count": failed_count,
                "results": results,
                "total_cost_estimate_usd": round(total_cost, 2)
            }
            
        except Exception as e:
            Logger.error(f"대량 SMS 발송 중 에러: {e}")
            return {
                "success": False,
                "error": str(e),
                "total_count": len(recipients),
                "success_count": success_count,
                "failed_count": failed_count,
                "results": results
            }
    
    async def get_sms_attributes(self) -> Dict[str, Any]:
        """
        SMS 발송 설정 조회
        
        현재 계정의 SMS 발송 한도, 비용 등을 확인합니다.
        
        Returns:
            dict: SMS 설정 정보
        """
        self._ensure_initialized()
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._client.get_sms_attributes()
            )
            
            attributes = response.get("attributes", {})
            
            return {
                "success": True,
                "monthly_spend_limit": attributes.get("MonthlySpendLimit", "Unknown"),
                "delivery_status_enabled": attributes.get("DeliveryStatusSuccessSamplingRate", "Unknown"),
                "default_sender_id": attributes.get("DefaultSenderID", "Unknown"),
                "default_sms_type": attributes.get("DefaultSMSType", "Unknown"),
                "usage_reporting": attributes.get("UsageReportS3Bucket", "Unknown")
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            Logger.error(f"SMS 설정 조회 실패: {error_code} - {error_message}")
            
            return {
                "success": False,
                "error": f"{error_code}: {error_message}",
                "error_code": error_code
            }
            
        except Exception as e:
            Logger.error(f"SMS 설정 조회 중 에러: {e}")
            return {
                "success": False,
                "error": str(e)
            }