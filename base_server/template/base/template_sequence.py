import json
import random
import time
from typing import Tuple, Optional
from enum import IntEnum


class ENetErrorCode(IntEnum):
    """네트워크 에러 코드 열거형"""
    SessionExpired = 1001
    SequenceDuplicated = 1002
    SequenceProcess = 1003
    Fatal = 1004


class TemplateSequence:
    """웹 요청 시퀀스 관리를 위한 템플릿 클래스"""
    
    # 상수 정의
    EXPIRE_TIME_SEC_15 = 15
    EXPIRE_TIME_SEC_30 = 30
    
    @staticmethod
    def _get_web_sequence_key(session_key: str) -> str:
        """웹 시퀀스 키 생성"""
        return f"webrequest:sequence:session_key:{session_key}"
    
    @staticmethod
    def _get_web_request_key(func_path: str, session_key: str, sequence: int) -> str:
        """웹 요청 키 생성"""
        return f"webrequest:session_key:{func_path}:{session_key}:{sequence}"
    
    @staticmethod
    def set_web_sequence(session_key: str, path: str, res_json: str) -> Tuple[int, str]:
        """
        로그인 시점에 시퀀스 발급
        
        Args:
            session_key: 세션 키
            path: 요청 경로
            res_json: 응답 JSON 문자열
            
        Returns:
            Tuple[int, str]: (시퀀스 번호, 수정된 응답 JSON)
        """
        j_obj = json.loads(res_json)
        
        sequence_key = TemplateSequence._get_web_sequence_key(session_key)
        seq = random.randint(0, 99) * 1000000
        
        # 캐시 클라이언트 사용 (기존 코드가 있다고 가정)
        # using (var cacheClient = CacheService.GetClient()) 대신
        cache_client = CacheService.get_client()  # 기존 코드 사용
        
        try:
            inc_seq = seq + 1
            before_sequence_str = cache_client.get_set(sequence_key, str(inc_seq))
            
            # 로그인 도중 중단되는 경우, Sequence 값이 업데이트 되지 않아 로그인하지 못함.
            # ttl을 15초로 설정. 15초 이내의 중복 요청에 대해서만 처리
            if not cache_client.expire(sequence_key, TemplateSequence.EXPIRE_TIME_SEC_15):
                j_obj["errorCode"] = int(ENetErrorCode.SessionExpired)
                return 0, json.dumps(j_obj)
            
            if before_sequence_str is None:
                before_seq = -1
            else:
                before_seq = int(before_sequence_str)
            
            # 이미 진행 중인 요청
            if before_seq == inc_seq:
                cache_client.set_string(sequence_key, before_sequence_str, 
                                      TemplateSequence.EXPIRE_TIME_SEC_15)
                
                j_obj["errorCode"] = int(ENetErrorCode.SequenceDuplicated)
                return 0, json.dumps(j_obj)
            elif before_seq == seq + 2:  # 이미 완료된 요청에 대한 시퀀스 값
                cache_client.set_string(sequence_key, before_sequence_str, 
                                      TemplateSequence.EXPIRE_TIME_SEC_15)
                request_key = TemplateSequence._get_web_request_key(path, session_key, seq + 2)
                # 이전에 완료되었던 response 값을 불러온다.
                res_json = cache_client.get_string(request_key)
                return 0, res_json
                
        finally:
            # 캐시 클라이언트 정리 (필요시)
            pass
        
        return seq, res_json
    
    @staticmethod
    def update_web_sequence(session_key: str, path: str, client_sequence: int, res_json: str) -> str:
        """
        웹 시퀀스 업데이트
        
        Args:
            session_key: 세션 키
            path: 요청 경로
            client_sequence: 클라이언트 시퀀스
            res_json: 응답 JSON 문자열
            
        Returns:
            str: 수정된 응답 JSON
        """
        sequence = client_sequence + 2
        # Sequence를 저장할 key
        sequence_key = TemplateSequence._get_web_sequence_key(session_key)
        # 응답 객체를 저장할 key
        request_key = TemplateSequence._get_web_request_key(path, session_key, sequence)
        
        # Sequence 저장
        cache_client = CacheService.get_client()  # 기존 코드 사용
        
        try:
            cache_client.set_string(sequence_key, str(sequence), 
                                  TemplateSequence.EXPIRE_TIME_SEC_30 * 60)  # 분 단위
            cache_client.set_string(request_key, res_json, 
                                  TemplateSequence.EXPIRE_TIME_SEC_15)
            
            j_obj = json.loads(res_json)
            j_obj["sequence"] = sequence
            res_json = json.dumps(j_obj)
            
        finally:
            # 캐시 클라이언트 정리 (필요시)
            pass
        
        return res_json
    
    @staticmethod
    def check_web_sequence(session_key: str, path: str, req_json: str) -> Tuple[int, Optional[str], int]:
        """
        웹 시퀀스 체크
        
        Args:
            session_key: 세션 키
            path: 요청 경로
            req_json: 요청 JSON 문자열
            
        Returns:
            Tuple[int, Optional[str], int]: (에러 코드, 이전 응답 JSON, 클라이언트 시퀀스)
        """
        j_obj = json.loads(req_json)
        
        client_sequence = int(j_obj["sequence"])
        error_code = 0
        before_res_json = None
        sequence_key = TemplateSequence._get_web_sequence_key(session_key)
        
        cache_client = CacheService.get_client()  # 기존 코드 사용
        
        try:
            inc_seq = client_sequence + 1
            sequence_str = cache_client.get_set(sequence_key, str(inc_seq))
            
            if sequence_str is None:
                # Sequence 값 삭제 오래되었을 경우 값이 없을 수 있음.
                cache_client.delete(sequence_key)
                error_code = int(ENetErrorCode.SessionExpired)
                return error_code, before_res_json, client_sequence
            
            redis_sequence = int(sequence_str)
            # 정상일 경우
            if redis_sequence + 1 == client_sequence:
                return error_code, before_res_json, client_sequence
            
            # 정상적이지 않은 경우, 기존 Sequence로 되돌린다.
            cache_client.set_string(sequence_key, str(redis_sequence))
            
            # 완료된 요청에 대한 재요청인지 체크
            if redis_sequence == client_sequence + 2:
                request_key = TemplateSequence._get_web_request_key(path, session_key, client_sequence + 2)
                before_res_json = cache_client.get_string(request_key)
                if before_res_json is None:
                    error_code = int(ENetErrorCode.Fatal)
                    return error_code, before_res_json, client_sequence
                return error_code, before_res_json, client_sequence
            elif redis_sequence == client_sequence + 1:  # 이미 진행중인 요청
                error_code = int(ENetErrorCode.SequenceProcess)
                return error_code, before_res_json, client_sequence
            else:
                error_code = int(ENetErrorCode.Fatal)
                
                # if redis_sequence > client_sequence:
                #     error_code = -1  # errorcode 정의 _ERR_WEB_SEQUENCE_DUPLICATE_CLIENT_REQ
                # else:
                #     error_code = -1  # errorcode 정의 _ERR_WEB_SEQUENCE_TOO_FAST_REQUEST
                
        finally:
            # 캐시 클라이언트 정리 (필요시)
            pass
        
        return error_code, before_res_json, client_sequence


# 편의를 위한 함수들
def set_web_sequence(session_key: str, path: str, res_json: str) -> Tuple[int, str]:
    """로그인 시점에 시퀀스 발급"""
    return TemplateSequence.set_web_sequence(session_key, path, res_json)


def update_web_sequence(session_key: str, path: str, client_sequence: int, res_json: str) -> str:
    """웹 시퀀스 업데이트"""
    return TemplateSequence.update_web_sequence(session_key, path, client_sequence, res_json)


def check_web_sequence(session_key: str, path: str, req_json: str) -> Tuple[int, Optional[str], int]:
    """웹 시퀀스 체크"""
    return TemplateSequence.check_web_sequence(session_key, path, req_json)
