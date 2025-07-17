from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Any
import json
import asyncio
import traceback
import uuid
from .template_context import TemplateContext
from .template_exception import TemplateException
from .client_session import ClientSession
from service.net.protocol_base import BaseResponse
from service.net.net_error_code import ENetErrorCode
from service.core.logger import Logger

class EServerStatus(Enum):
    None_ = 0  # 'None'은 파이썬 예약어이므로 'None_'으로 변경
    Operating = 1  # 운영중인 상태
    Repairing = 2  # 점검중인 상태(화이트리스트 접속도 허용하지 않음)
    RepairingConfirm = 3  # 점검 확인중인 상태(화이트리스트 접속만 허용함)
    Reloading = 4  # 재로딩 상태

class EAccountLevel(Enum):
    NONE = 0  # 기본값
    USER = 1  # 일반 유저
    OPERATOR = 2  # 운영자
    DEVELOPER = 3  # 개발자
    ADMINISTRATOR = 4  # 관리자

class EProtocolType(Enum):
    ANONYMOUS = 0
    USER = 1
    OPERATOR = 2
    ADMINISTRATOR = 3

@dataclass
class ServerStatus:
    status: EServerStatus
    start_time: datetime
    end_time: datetime

class TemplateService:
    _config = None
    SessionContextCallback: Callable[[Any, bytes, int], Any] = None  # 타입 힌트

    @classmethod
    def init(cls, config):
        cls._config = config
        TemplateContext.load_data_table(config)
        TemplateContext.init_template(config)
    
    @classmethod
    async def run_anonymous(cls, method: str, path: str, ip_address: str, req_json: str, callback: Callable[[Any, bytes, int], Any]) -> str:
        """익명 컨트롤러 함수 실행 (서버 인증 이전)"""
        client_session = None
        try:
            Logger.info(f"REQ[{method}:{path}, IP:{ip_address} - UID: ]: {req_json}")
            cls.check_allowed_request(ip_address, EProtocolType.ANONYMOUS)
            
            # 익명 요청은 세션 없이 콜백 호출
            msg = req_json.encode('utf-8')
            res = await callback(None, msg, len(msg))
            res_json = cls._serialize_response(res)
            
            # 응답에 account_info가 있으면 세션 생성 (로그인 성공 시)
            j_obj = json.loads(res_json)
            if 'account_info' in j_obj and j_obj['account_info'] is not None:
                account_info = j_obj['account_info']
                # accessToken 생성 (없으면 새로 생성)
                access_token = account_info.get('accessToken', str(uuid.uuid4()))
                
                # SessionInfo 객체 생성
                from .session_info import SessionInfo, ClientSessionState
                session_info = SessionInfo()
                session_info.account_db_key = account_info.get('account_db_key', 0)
                session_info.platform_id = account_info.get('platform_id', '')
                session_info.platform_type = account_info.get('platform_type', 1)
                session_info.account_id = account_info.get('account_id', '')
                session_info.account_level = account_info.get('account_level', 1)
                session_info.app_version = account_info.get('app_version', '1.0.0')
                session_info.os = account_info.get('os', 'unknown')
                session_info.country = account_info.get('country', 'KR')
                session_info.session_state = ClientSessionState.NORMAL
                session_info.shard_id = account_info.get('shard_id', 1)
                
                # Redis에 세션 정보 저장
                client_session = await cls.set_session_info(access_token, '', session_info)
                
                # 로그인 성공 시 템플릿 콜백 호출
                if client_session:
                    await cls._handle_user_login_callbacks(client_session)
                
                # 응답에 accessToken 추가
                j_obj['accessToken'] = access_token
                
                # account_info는 내부 세션 생성용이므로 클라이언트 응답에서 제거
                if 'account_info' in j_obj:
                    del j_obj['account_info']
                
                res_json = json.dumps(j_obj)
                
                account_db_key = getattr(client_session.session, 'account_db_key', 0) if client_session else 0
                Logger.info(f"RES[{method}:{path}, IP:{ip_address} - ACCOUNT_KEY: {account_db_key}]: {res_json}")
                # TODO: 시퀀스 검증 구현 필요
            else:
                Logger.info(f"RES[{method}:{path}, IP:{ip_address} - ACCOUNT_KEY: ]: {res_json}")
            
            return res_json
            
        except TemplateException as ex:
            return cls._handle_template_exception(ex, method, path, ip_address)
        except Exception as ex:
            return cls._handle_general_exception(ex, method, path, ip_address)
    
    @classmethod
    async def run_user(cls, method: str, path: str, ip_address: str, req_json: str, callback: Callable[[Any, bytes, int], Any]) -> str:
        """유저 컨트롤러 함수 실행 (서버 인증 이후)"""
        client_session = None
        try:
            Logger.info(f"REQ[{method}:{path}, IP:{ip_address} - UID: ]: {req_json}")
            cls.check_allowed_request(ip_address, EProtocolType.USER)
            
            # 요청에서 세션 생성 및 검증
            client_session = await cls.create_client_session(req_json)
            
            # 세션 유효성 검증
            if client_session is None:
                raise TemplateException("SessionExpired", getattr(ENetErrorCode, 'SESSION_EXPIRED', -1))
            
            # 세션 상태 검증 (중복 로그인, 차단 계정 등)
            await cls._validate_session_state(client_session)
            
            # TODO: 시퀀스 검증 구현 필요
            
            # 유효한 세션으로 콜백 호출
            msg = req_json.encode('utf-8')
            res = await callback(client_session, msg, len(msg))
            res_json = cls._serialize_response(res)
            
            account_db_key = getattr(client_session.session, 'account_db_key', 0) if client_session and client_session.session else 0
            Logger.info(f"RES[{method}:{path}, IP:{ip_address} - ACCOUNT_KEY: {account_db_key}]: {res_json}")
            
            # TODO: API 경로를 사용자 캐시에 저장
            
            return res_json
            
        except TemplateException as ex:
            return cls._handle_template_exception(ex, method, path, ip_address)
        except Exception as ex:
            return cls._handle_general_exception(ex, method, path, ip_address)

    @classmethod
    async def run_operator(cls, method: str, path: str, ip_address: str, req_json: str, callback: Callable[[Any, bytes, int], Any]) -> str:
        """운영자 컨트롤러 함수 실행"""
        client_session = None
        try:
            Logger.info(f"REQ[{method}:{path}, IP:{ip_address} - UID: ]: {req_json}")
            
            # 먼저 세션 생성 및 검증
            client_session = await cls.create_client_session(req_json)
            if client_session is None:
                raise TemplateException("SessionExpired", getattr(ENetErrorCode, 'SESSION_EXPIRED', -1))
            
            cls.check_allowed_request(ip_address, EProtocolType.OPERATOR, client_session)
            
            # 세션 상태 검증
            await cls._validate_session_state(client_session)
            
            # TODO: 시퀀스 검증 구현 필요
            
            # 유효한 세션으로 콜백 호출
            msg = req_json.encode('utf-8')
            res = await callback(client_session, msg, len(msg))
            res_json = cls._serialize_response(res)
            
            account_db_key = getattr(client_session.session, 'account_db_key', 0) if client_session and client_session.session else 0
            Logger.info(f"RES[{method}:{path}, IP:{ip_address} - ACCOUNT_KEY: {account_db_key}]: {res_json}")
            
            return res_json
            
        except TemplateException as ex:
            return cls._handle_template_exception(ex, method, path, ip_address)
        except Exception as ex:
            return cls._handle_general_exception(ex, method, path, ip_address)

    @classmethod
    async def run_administrator(cls, method: str, path: str, ip_address: str, req_json: str, callback: Callable[[Any, bytes, int], Any]) -> str:
        """관리자 컨트롤러 함수 실행"""
        try:
            Logger.info(f"REQ[{method}:{path}, IP:{ip_address} - UID: ]: {req_json}")
            cls.check_allowed_request(ip_address, EProtocolType.ADMINISTRATOR)
            
            # 관리자는 세션 없이 콜백 호출
            msg = req_json.encode('utf-8')
            res = await callback(None, msg, len(msg))
            res_json = cls._serialize_response(res)
            
            Logger.info(f"RES[{method}:{path}, IP:{ip_address} - UID: ]: {res_json}")
            return res_json
            
        except TemplateException as ex:
            return cls._handle_template_exception(ex, method, path, ip_address)
        except Exception as ex:
            return cls._handle_general_exception(ex, method, path, ip_address)

    @staticmethod
    async def create_client_session(json_str: str) -> ClientSession:
        """JSON에서 ClientSession 생성"""
        j_obj = json.loads(json_str)
        access_token = j_obj.get("accessToken", "")
        
        # 테스트용: CacheService 없이 임시 세션 생성
        if access_token:
            session_info = await TemplateService.check_session_info(access_token)
            return ClientSession(access_token, session_info)
        else:
            # accessToken이 없으면 None 반환 (익명 요청)
            return None

    @staticmethod
    async def set_session_info(access_token: str, last_access_token: str, session_info: 'SessionInfo') -> ClientSession:
        """세션 정보를 Redis에 설정"""
        from service.cache.cache_service import CacheService
        
        try:
            async with CacheService.get_client() as client:
                # 기존 세션이 있다면 중복 로그인 처리
                if last_access_token:
                    redis_key = f"accessToken:{last_access_token}"
                    redis_value = await client.get_string(redis_key)
                    if redis_value:
                        session_key = f"sessionInfo:{last_access_token}"
                        session_value = await client.get_string(session_key)
                        if session_value:
                            last_session_info = json.loads(session_value)
                            # 중복 로그인 상태로 설정
                            last_session_info["session_state"] = "Duplicated"
                            await client.set_string(session_key, json.dumps(last_session_info))
                            Logger.info(f"Logout duplicated account. account_db_key: {last_session_info.get('account_db_key')}")

                # 새로운 액세스 토큰 설정 (토큰 자체를 값으로 저장)
                token_key = f"accessToken:{access_token}"
                await client.set_string(token_key, access_token, expire=client.session_expire_time)
                
                # 세션 정보 설정
                session_dict = {
                    "account_db_key": session_info.account_db_key,
                    "platform_id": session_info.platform_id,
                    "platform_type": session_info.platform_type,
                    "account_id": session_info.account_id,
                    "account_level": session_info.account_level,
                    "app_version": session_info.app_version,
                    "os": session_info.os,
                    "country": session_info.country,
                    "session_state": session_info.session_state.value if hasattr(session_info.session_state, 'value') else str(session_info.session_state),
                    "shard_id": session_info.shard_id
                }
                session_key = f"sessionInfo:{access_token}"
                await client.set_string(session_key, json.dumps(session_dict), expire=client.session_expire_time)
                
                Logger.info(f"Session created: account_db_key={session_info.account_db_key}, shard_id={session_info.shard_id}")
                return ClientSession(access_token, session_info)
        except Exception as e:
            Logger.error(f"SetSessionInfo error: {e}")
            return None

    @staticmethod
    async def check_session_info(access_token: str):
        """세션 정보를 읽어오고 만료시간 갱신"""
        from service.cache.cache_service import CacheService
        from .session_info import SessionInfo, ClientSessionState
        
        try:
            async with CacheService.get_client() as client:
                redis_key = f"accessToken:{access_token}"
                redis_value = await client.get_string(redis_key)
                if not redis_value:
                    Logger.error(f"failed to get accessToken. key: {redis_key}")
                    return None

                session_key = f"sessionInfo:{access_token}"
                session_value = await client.get_string(session_key)
                if not session_value:
                    await client.delete(redis_key)
                    Logger.error(f"not found session info. key: {session_key}")
                    return None

                # 액세스 토큰이 유효하다면 만료 시간을 갱신
                if not await client.expire(redis_key, client.session_expire_time):
                    Logger.error(f"failed to expire key. key: {redis_key}")
                    return None
                    
                # 세션 정보도 만료 시간 갱신
                await client.expire(session_key, client.session_expire_time)

                # SessionInfo 객체로 변환
                session_dict = json.loads(session_value)
                session_info = SessionInfo()
                session_info.account_db_key = session_dict.get("account_db_key", 0)
                session_info.platform_id = session_dict.get("platform_id", "")
                session_info.platform_type = session_dict.get("platform_type", -1)
                session_info.account_id = session_dict.get("account_id", "")
                session_info.account_level = session_dict.get("account_level", 0)
                session_info.app_version = session_dict.get("app_version", "")
                session_info.os = session_dict.get("os", "")
                session_info.country = session_dict.get("country", "")
                
                # session_state 처리
                state_value = session_dict.get("session_state", "NORMAL")
                try:
                    session_info.session_state = ClientSessionState(state_value)
                except (ValueError, AttributeError):
                    session_info.session_state = ClientSessionState.NORMAL
                    
                session_info.shard_id = session_dict.get("shard_id", -1)
                
                return session_info
        except Exception as e:
            Logger.error(f"CheckSessionInfo error: {e}")
            return None

    @staticmethod
    async def get_session_info(access_token: str):
        """세션 정보만 가져오기 (만료시간 갱신 안함)"""
        # 테스트용: check_session_info와 동일하게 처리
        return await TemplateService.check_session_info(access_token)

    @staticmethod
    async def remove_session_info(access_token: str) -> bool:
        """세션 정보를 삭제"""
        from service.cache.cache_service import CacheService
        
        try:
            async with CacheService.get_client() as client:
                # 액세스 토큰과 세션 정보 모두 삭제
                token_deleted = await client.delete(f"accessToken:{access_token}")
                session_deleted = await client.delete(f"sessionInfo:{access_token}")
                
                Logger.info(f"Session removed: {access_token}, token_deleted={token_deleted}, session_deleted={session_deleted}")
                return token_deleted or session_deleted
        except Exception as e:
            Logger.error(f"RemoveSessionInfo error: {e}")
            return False

    @staticmethod
    def check_allowed_request(ip_address: str, protocol_type: EProtocolType, client_session: 'ClientSession' = None):
        """허용 요청 여부 체크"""
        try:
            if protocol_type == EProtocolType.ADMINISTRATOR:
                # 관리자: 반드시 화이트리스트에 있어야 함
                if not TemplateService.check_white_list(ip_address):
                    raise TemplateException("AdminAccessDenied", getattr(ENetErrorCode, 'ACCESS_DENIED', -1))
                    
            elif protocol_type == EProtocolType.OPERATOR:
                # 운영자: 화이트리스트 OR 계정 레벨 체크
                is_whitelist = TemplateService.check_white_list(ip_address)
                has_operator_level = False
                
                if client_session and client_session.session:
                    account_level = getattr(client_session.session, 'account_level', 0)
                    has_operator_level = account_level >= 2  # Operator level and above (2=Operator, 3=Developer, 4=Administrator)
                
                if not (is_whitelist or has_operator_level):
                    raise TemplateException("OperatorAccessDenied", getattr(ENetErrorCode, 'ACCESS_DENIED', -1))
                    
            else:
                # USER, ANONYMOUS: 서버 상태 및 화이트리스트 체크
                # TODO: 서버 상태 체크 구현 필요
                # if server_status != EServerStatus.Operating:
                #     if not TemplateService.check_white_list(ip_address):
                #         raise TemplateException("ServerMaintenance", ...)
                pass
                
        except Exception as e:
            Logger.error(f"Access control error: {e}")
            raise

    @staticmethod
    def check_white_list(ip_address: str) -> bool:
        """화이트리스트 체크"""
        try:
            # TODO: 실제 화이트리스트 설정에서 로드
            # 현재는 개발용으로 localhost 허용
            whitelist_patterns = [
                "127.0.0.1",
                "localhost", 
                "::1",
                "192.168.*",
                "10.*"
            ]
            
            for pattern in whitelist_patterns:
                if TemplateService._match_ip_pattern(ip_address, pattern):
                    return True
                    
            return False
        except Exception as e:
            Logger.error(f"Whitelist check error: {e}")
            return False
    
    @staticmethod
    def _match_ip_pattern(ip_address: str, pattern: str) -> bool:
        """IP 패턴 매칭 (와일드카드 지원)"""
        if pattern == ip_address:
            return True
            
        # 와일드카드 패턴 처리
        if '*' in pattern:
            pattern_parts = pattern.split('.')
            ip_parts = ip_address.split('.')
            
            if len(pattern_parts) != len(ip_parts):
                return False
                
            for p_part, ip_part in zip(pattern_parts, ip_parts):
                if p_part != '*' and p_part != ip_part:
                    return False
            return True
            
        return False

    # === Helper Methods ===
    
    @classmethod
    def _serialize_response(cls, res) -> str:
        """응답을 JSON 문자열로 직렬화"""
        if hasattr(res, 'model_dump_json'):
            return res.model_dump_json()
        elif hasattr(res, '__dict__'):
            return json.dumps(res.__dict__)
        else:
            return json.dumps(str(res))
    
    @classmethod
    async def _handle_session_creation(cls, res_json: str, method: str, path: str, ip_address: str) -> None:
        """세션 생성 처리"""
        try:
            j_obj = json.loads(res_json)
            if 'account_info' in j_obj:
                await cls.create_client_session(json.dumps(j_obj['account_info']))
        except Exception as e:
            Logger.error(f"Session creation failed: {e}")
    
    @classmethod
    async def _validate_session_state(cls, client_session: 'ClientSession') -> None:
        """세션 상태 검증"""
        if not client_session or not client_session.session:
            raise TemplateException("SessionInvalid", getattr(ENetErrorCode, 'SESSION_INVALID', -1))
        
        session_state = getattr(client_session.session, 'session_state', None)
        if session_state:
            if hasattr(session_state, 'value'):
                state_value = session_state.value
            else:
                state_value = str(session_state)
            
            if state_value == "Duplicated":
                raise TemplateException("DuplicatedLogin", getattr(ENetErrorCode, 'DUPLICATED_LOGIN', -1))
            elif state_value == "Blocked":
                raise TemplateException("BlockedAccount", getattr(ENetErrorCode, 'BLOCKED_ACCOUNT', -1))
    
    @classmethod
    def _handle_template_exception(cls, ex: 'TemplateException', method: str, path: str, ip_address: str) -> str:
        """TemplateException 처리"""
        Logger.error(f"TemplateException: errorCode: {ex.error_code}, message: {ex}")
        Logger.error(f"StackTrace: {getattr(ex, 'stack_trace', '')}")
        
        if hasattr(ex, 'response') and ex.response is not None:
            res_json = json.dumps(ex.response)
        else:
            response = BaseResponse()
            response.errorCode = ex.error_code
            res_json = json.dumps(response.__dict__)
        
        Logger.info(f"RES[{method}:{path}, IP:{ip_address}]: {res_json}")
        return res_json
    
    @classmethod
    def _handle_general_exception(cls, ex: Exception, method: str, path: str, ip_address: str) -> str:
        """일반 Exception 처리"""
        Logger.error(f"Exception: message: {ex}")
        Logger.error(f"StackTrace: {traceback.format_exc()}")
        
        response = BaseResponse()
        response.errorCode = getattr(ENetErrorCode, 'FATAL', -1)
        res_json = json.dumps(response.__dict__)
        
        Logger.info(f"RES[{method}:{path}, IP:{ip_address}]: {res_json}")
        return res_json

    @classmethod
    async def _handle_user_login_callbacks(cls, client_session: 'ClientSession'):
        """로그인 성공 시 템플릿 콜백 처리"""
        try:
            from service.service_container import ServiceContainer
            
            db_service = ServiceContainer.get_database_service()
            if not db_service:
                Logger.warn("데이터베이스 서비스를 찾을 수 없어 템플릿 콜백을 건너뜀")
                return
            
            account_db_key = getattr(client_session.session, 'account_db_key', 0)
            account_id = getattr(client_session.session, 'account_id', '')
            
            # 로그인 카운트 기반 첫 로그인 체크
            is_first_login = await cls._check_is_first_login_by_count(db_service, account_db_key, account_id)
            
            if is_first_login:
                Logger.info(f"첫 로그인 감지 - 템플릿 CreateClient 호출: account_db_key={account_db_key}")
                TemplateContext.create_client(db_service, client_session)
            else:
                Logger.info(f"재로그인 감지 - 템플릿 UpdateClient 호출: account_db_key={account_db_key}")
                TemplateContext.update_client(db_service, client_session)
                
        except Exception as e:
            Logger.error(f"템플릿 로그인 콜백 처리 실패: {e}")
    
    @staticmethod
    async def _check_is_first_login_by_count(db_service, account_db_key: int, account_id: str) -> bool:
        """로그인 카운트로 첫 로그인 여부 확인"""
        try:
            # 1. 계정 복구 체크
            if '_restore' in account_id:
                Logger.info(f"계정 복구 감지: {account_id}")
                await cls._process_account_restore(db_service, account_db_key, account_id)
                return True
            
            # 2. 현재 로그인 카운트 조회
            query = "SELECT login_count FROM table_accountid WHERE account_db_key = %s"
            result = await db_service.call_global_read_query(query, (account_db_key,))
            
            if result and len(result) > 0:
                login_count = result[0].get('login_count', 0)
                
                # 로그인 카운트 증가
                await cls._increment_login_count(db_service, account_db_key)
                
                # 첫 로그인 판정 (카운트가 0이면 첫 로그인)
                if login_count == 0:
                    Logger.info(f"첫 로그인 감지: login_count={login_count}")
                    return True
            
            return False
            
        except Exception as e:
            Logger.error(f"첫 로그인 체크 실패: {e}")
            return False
    
    @staticmethod
    async def _increment_login_count(db_service, account_db_key: int):
        """로그인 카운트 증가"""
        try:
            query = """
                UPDATE table_accountid 
                SET login_count = login_count + 1,
                    login_time = NOW()
                WHERE account_db_key = %s
            """
            
            await db_service.call_global_procedure_update(query, (account_db_key,))
            
        except Exception as e:
            Logger.error(f"로그인 카운트 업데이트 실패: {e}")
    
    @staticmethod
    async def _process_account_restore(db_service, account_db_key: int, account_id: str):
        """계정 복구 처리"""
        try:
            new_account_id = account_id.replace('_restore', '')
            
            query = """
                UPDATE table_accountid 
                SET account_id = %s,
                    login_count = 1,
                    login_time = NOW()
                WHERE account_db_key = %s
            """
            
            await db_service.call_global_procedure_update(query, (new_account_id, account_db_key))
            Logger.info(f"계정 복구 완료: {account_db_key} -> {new_account_id}")
            
        except Exception as e:
            Logger.error(f"계정 복구 처리 실패: {e}")

