"""
채팅 상태 머신 - Redis 기반 원자적 상태 관리

메시지와 방의 생명주기를 State Machine으로 관리하여 Race Condition 해결
- CacheService와 동일한 정적 클래스 싱글톤 패턴
- Redis Lua Script로 원자적 상태 전이 보장
- 분산 환경에서 안전한 상태 추적
- 카카오톡 방식의 메시지 삭제 처리 구현
"""

import asyncio
from enum import Enum
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime, timedelta

from service.core.logger import Logger
from service.cache.cache_service import CacheService


class MessageState(Enum):
    """메시지 상태"""
    COMPOSING = "COMPOSING"      # 작성 중 (클라이언트에서만 사용)
    PENDING = "PENDING"          # 전송 대기 중 (Redis 저장됨)
    PROCESSING = "PROCESSING"    # DB 저장 중
    SENT = "SENT"               # 전송 완료 (DB 저장 완료)
    DELETING = "DELETING"       # 삭제 중
    DELETED = "DELETED"         # 삭제 완료


class RoomState(Enum):
    """채팅방 상태"""
    CREATING = "CREATING"       # 생성 중 (클라이언트에서만 사용)
    PENDING = "PENDING"         # 생성 대기 중 (Redis 저장됨)
    PROCESSING = "PROCESSING"   # DB 저장 중
    ACTIVE = "ACTIVE"          # 활성 상태 (DB 저장 완료)
    DELETING = "DELETING"      # 삭제 중
    DELETED = "DELETED"        # 삭제 완료


class StateTransitionError(Exception):
    """상태 전이 불가능 예외"""
    pass


class ChatStateMachine:
    """채팅 상태 머신 - CacheService와 동일한 정적 클래스 싱글톤 패턴"""
    
    _instance: Optional['ChatStateMachine'] = None
    _initialized: bool = False
    
    def __init__(self):
        if ChatStateMachine._instance is not None:
            raise RuntimeError("ChatStateMachine은 싱글톤입니다. get_instance()를 사용하세요.")
        
        # 상태 전이 규칙 정의
        self.message_transitions = {
            MessageState.COMPOSING: [MessageState.PENDING, MessageState.DELETED],
            MessageState.PENDING: [MessageState.PROCESSING, MessageState.DELETED],
            MessageState.PROCESSING: [MessageState.SENT, MessageState.DELETED],
            MessageState.SENT: [MessageState.DELETING],
            MessageState.DELETING: [MessageState.DELETED],
            MessageState.DELETED: []  # 최종 상태
        }
        
        self.room_transitions = {
            RoomState.CREATING: [RoomState.PENDING, RoomState.DELETED],
            RoomState.PENDING: [RoomState.PROCESSING, RoomState.DELETED],
            RoomState.PROCESSING: [RoomState.ACTIVE, RoomState.DELETED],
            RoomState.ACTIVE: [RoomState.DELETING],
            RoomState.DELETING: [RoomState.DELETED],
            RoomState.DELETED: []  # 최종 상태
        }
        
        # Redis 키 패턴
        self.message_state_key_pattern = "msg_state:{message_id}"
        self.room_state_key_pattern = "room_state:{room_id}"
        
        # Lua Scripts - Redis 네임스페이스 고려
        self._atomic_transition_script = """
        -- 원자적 상태 전이 스크립트
        -- KEYS[1]: state_key (네임스페이스 적용됨)
        -- ARGV[1]: current_state (빈 문자열이면 첫 상태 설정)
        -- ARGV[2]: new_state  
        -- ARGV[3]: ttl_seconds
        -- ARGV[4]: transition_log
        
        local current = redis.call('GET', KEYS[1])
        if current == false then
            current = nil
        end
        
        -- 첫 상태 설정인 경우 (ARGV[1]이 빈 문자열)
        if ARGV[1] == '' then
            -- 현재 상태가 없어야 함 (중복 설정 방지)
            if current ~= nil then
                return {0, current}  -- 이미 상태가 있음
            end
        else
            -- 기존 상태 전이인 경우 - 현재 상태가 예상과 다르면 실패
            if current ~= ARGV[1] then
                return {0, current}  -- 실패, 현재 상태 반환
            end
        end
        
        -- 상태 전이 실행
        redis.call('SET', KEYS[1], ARGV[2])
        if tonumber(ARGV[3]) > 0 then
            redis.call('EXPIRE', KEYS[1], tonumber(ARGV[3]))
        end
        
        -- 전이 로그 저장 (선택적)
        if ARGV[4] ~= '' then
            local log_key = KEYS[1] .. ':log'
            redis.call('LPUSH', log_key, ARGV[4])
            redis.call('LTRIM', log_key, 0, 9)  -- 최근 10개만 유지
            redis.call('EXPIRE', log_key, 86400)  -- 24시간 TTL
        end
        
        return {1, ARGV[2]}  -- 성공, 새 상태 반환
        """
    
    @classmethod
    def get_instance(cls) -> 'ChatStateMachine':
        """싱글톤 인스턴스 반환"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    async def init(cls) -> bool:
        """상태 머신 초기화"""
        try:
            if cls._initialized:
                Logger.warn("ChatStateMachine이 이미 초기화되었습니다")
                return True
            
            # CacheService 의존성 확인
            if not CacheService.is_initialized():
                Logger.error("CacheService가 초기화되지 않음. ChatStateMachine 초기화 중단")
                return False
            
            # 인스턴스 생성
            instance = cls.get_instance()
            
            # Redis 연결 테스트 (main.py 패턴 사용)
            try:
                health_check = await CacheService.health_check()
                if health_check.get("healthy", False):
                    Logger.info("ChatStateMachine Redis 연결 테스트 성공")
                else:
                    Logger.error(f"ChatStateMachine Redis 연결 실패: {health_check.get('error', 'Unknown error')}")
                    return False
            except Exception as e:
                Logger.error(f"ChatStateMachine Redis 연결 실패: {e}")
                return False
            
            cls._initialized = True
            Logger.info("ChatStateMachine 초기화 완료")
            return True
            
        except Exception as e:
            Logger.error(f"ChatStateMachine 초기화 실패: {e}")
            return False
    
    @classmethod
    async def shutdown(cls):
        """상태 머신 종료"""
        try:
            if cls._initialized:
                cls._initialized = False
                cls._instance = None
                Logger.info("ChatStateMachine 종료 완료")
        except Exception as e:
            Logger.error(f"ChatStateMachine 종료 중 오류: {e}")
    
    @classmethod
    def is_initialized(cls) -> bool:
        """초기화 상태 확인"""
        return cls._initialized
    
    # ==================== 메시지 상태 관리 ====================
    
    async def get_message_state(self, message_id: str) -> Optional[MessageState]:
        """메시지 현재 상태 조회"""
        try:
            if not self.__class__._initialized:
                Logger.warn("ChatStateMachine이 초기화되지 않음")
                return None
            
            state_key = self.message_state_key_pattern.format(message_id=message_id)
            
            async with CacheService.get_client() as redis:
                state_str = await redis.get_string(state_key)
                if state_str:
                    return MessageState(state_str)
                else:
                    # 상태가 없으면 None 반환 (첫 상태 설정은 transition_message에서 처리)
                    return None
                    
        except Exception as e:
            Logger.error(f"메시지 상태 조회 실패: {message_id} - {e}")
            return None
    
    async def transition_message(self, message_id: str, to_state: MessageState, 
                               from_state: Optional[MessageState] = None,
                               ttl_seconds: int = 3600) -> bool:
        """메시지 상태 전이 (원자적)"""
        try:
            if not self.__class__._initialized:
                Logger.warn("ChatStateMachine이 초기화되지 않음")
                return False
            
            # 현재 상태 확인
            is_initial_state = False
            if from_state is None:
                current_state = await self.get_message_state(message_id)
                if current_state is None:
                    # 첫 상태 설정 - 전이 규칙 검증 건너뛰기
                    is_initial_state = True
                    from_state = None  # Lua script에서 nil 처리
                else:
                    from_state = current_state
            
            # 전이 가능성 검증 (첫 상태 설정이 아닌 경우만)
            if not is_initial_state and to_state not in self.message_transitions.get(from_state, []):
                from_state_str = from_state.value if from_state else "None"
                Logger.warn(f"불가능한 메시지 상태 전이: {from_state_str} → {to_state.value}")
                return False
            
            # 원자적 상태 전이 실행
            state_key = self.message_state_key_pattern.format(message_id=message_id)
            from_state_str = from_state.value if from_state else ""  # 첫 상태 설정 시 빈 문자열
            transition_log = f"{datetime.now().isoformat()}:{from_state_str}→{to_state.value}"
            
            async with CacheService.get_client() as redis:
                result = await redis.eval(
                    self._atomic_transition_script,
                    1,  # numkeys
                    redis._get_key(state_key),  # 네임스페이스 적용된 키
                    from_state_str,     # ARGV[1]: 현재 상태 (빈 문자열이면 첫 설정)
                    to_state.value,      # ARGV[2]: 새 상태
                    str(ttl_seconds),    # ARGV[3]: TTL
                    transition_log       # ARGV[4]: 로그
                )
                
                # 디버깅: result 값 확인
                Logger.info(f"메시지 Lua 스크립트 결과: {result}, type: {type(result)}, len: {len(result) if hasattr(result, '__len__') else 'N/A'}")
                
                success, final_state = result
                if success:
                    from_state_str = from_state.value if from_state else ""
                    Logger.debug(f"메시지 상태 전이 성공: {message_id} {from_state_str}→{to_state.value}")
                    return True
                else:
                    from_state_str = from_state.value if from_state else ""
                    Logger.warn(f"메시지 상태 전이 실패: {message_id} 예상={from_state_str} 실제={final_state}")
                    return False
        
        except Exception as e:
            Logger.error(f"메시지 상태 전이 중 오류: {message_id} - {e}")
            return False
    
    async def can_delete_message(self, message_id: str) -> Tuple[bool, Optional[str]]:
        """메시지 삭제 가능 여부 확인"""
        try:
            current_state = await self.get_message_state(message_id)
            if current_state is None:
                return False, "상태 조회 실패"
            
            if current_state in [MessageState.DELETED, MessageState.DELETING]:
                return False, "이미 삭제된 메시지"
            
            return True, "삭제 가능"
            
        except Exception as e:
            Logger.error(f"메시지 삭제 가능성 확인 실패: {message_id} - {e}")
            return False, "확인 실패"
    
    async def smart_delete_message(self, message_id: str) -> Tuple[bool, str]:
        """지능형 메시지 삭제 - 상태에 따른 적절한 처리"""
        try:
            current_state = await self.get_message_state(message_id)
            if current_state is None:
                return False, "상태 조회 실패"
            
            if current_state == MessageState.COMPOSING:
                # 아직 전송 안됨 → 즉시 취소
                success = await self.transition_message(message_id, MessageState.DELETED, current_state)
                return success, "작성 취소" if success else "취소 실패"
                
            elif current_state == MessageState.PENDING:
                # Redis에만 있음 → 빠른 취소
                success = await self.transition_message(message_id, MessageState.DELETED, current_state)
                return success, "전송 전 취소" if success else "취소 실패"
                
            elif current_state == MessageState.PROCESSING:
                # DB 저장 중 → 삭제 대기
                success = await self.transition_message(message_id, MessageState.DELETING, current_state)
                return success, "처리 중 삭제 예약" if success else "삭제 예약 실패"
                
            elif current_state == MessageState.SENT:
                # 정상 전송됨 → Soft Delete
                success = await self.transition_message(message_id, MessageState.DELETING, current_state)
                return success, "메시지 삭제 중" if success else "삭제 시작 실패"
                
            elif current_state in [MessageState.DELETING, MessageState.DELETED]:
                # 이미 삭제 중/완료 → 무해한 중복 요청
                return True, "이미 삭제됨"
                
            else:
                return False, f"예상치 못한 상태: {current_state.value}"
                
        except Exception as e:
            Logger.error(f"지능형 메시지 삭제 실패: {message_id} - {e}")
            return False, "삭제 처리 오류"
    
    # ==================== 방 상태 관리 ====================
    
    async def get_room_state(self, room_id: str) -> Optional[RoomState]:
        """채팅방 현재 상태 조회"""
        try:
            if not self.__class__._initialized:
                Logger.warn("ChatStateMachine이 초기화되지 않음")
                return None
            
            state_key = self.room_state_key_pattern.format(room_id=room_id)
            
            async with CacheService.get_client() as redis:
                state_str = await redis.get_string(state_key)
                if state_str:
                    return RoomState(state_str)
                else:
                    # 상태가 없으면 None 반환 (첫 상태 설정은 transition_room에서 처리)
                    return None
                    
        except Exception as e:
            Logger.error(f"방 상태 조회 실패: {room_id} - {e}")
            return None
    
    async def transition_room(self, room_id: str, to_state: RoomState,
                            from_state: Optional[RoomState] = None,
                            ttl_seconds: int = 86400) -> bool:
        """채팅방 상태 전이 (원자적)"""
        try:
            if not self.__class__._initialized:
                Logger.warn("ChatStateMachine이 초기화되지 않음")
                return False
            
            # 현재 상태 확인
            is_initial_state = False
            if from_state is None:
                current_state = await self.get_room_state(room_id)
                if current_state is None:
                    # 첫 상태 설정 - 전이 규칙 검증 건너뛰기
                    is_initial_state = True
                    from_state = None  # Lua script에서 nil 처리
                else:
                    from_state = current_state
            
            # 전이 가능성 검증 (첫 상태 설정이 아닌 경우만)
            if not is_initial_state and to_state not in self.room_transitions.get(from_state, []):
                from_state_str = from_state.value if from_state else "None"
                Logger.warn(f"불가능한 방 상태 전이: {from_state_str} → {to_state.value}")
                return False
            
            # 원자적 상태 전이 실행
            state_key = self.room_state_key_pattern.format(room_id=room_id)
            from_state_str = from_state.value if from_state else ""  # 첫 상태 설정 시 빈 문자열
            transition_log = f"{datetime.now().isoformat()}:{from_state_str}→{to_state.value}"
            
            async with CacheService.get_client() as redis:
                result = await redis.eval(
                    self._atomic_transition_script,
                    1,  # numkeys
                    redis._get_key(state_key),  # 네임스페이스 적용된 키
                    from_state_str,     # ARGV[1]: 현재 상태 (빈 문자열이면 첫 설정)
                    to_state.value,      # ARGV[2]: 새 상태
                    str(ttl_seconds),    # ARGV[3]: TTL
                    transition_log       # ARGV[4]: 로그
                )
                
                success, final_state = result
                if success:
                    from_state_str = from_state.value if from_state else ""
                    Logger.debug(f"방 상태 전이 성공: {room_id} {from_state_str}→{to_state.value}")
                    return True
                else:
                    from_state_str = from_state.value if from_state else ""
                    Logger.warn(f"방 상태 전이 실패: {room_id} 예상={from_state_str} 실제={final_state}")
                    return False
        
        except Exception as e:
            Logger.error(f"방 상태 전이 중 오류: {room_id} - {e}")
            return False
    
    async def can_delete_room(self, room_id: str) -> Tuple[bool, Optional[str]]:
        """채팅방 삭제 가능 여부 확인"""
        try:
            current_state = await self.get_room_state(room_id)
            if current_state is None:
                return False, "상태 조회 실패"
            
            if current_state in [RoomState.DELETED, RoomState.DELETING]:
                return False, "이미 삭제된 방"
            
            return True, "삭제 가능"
            
        except Exception as e:
            Logger.error(f"방 삭제 가능성 확인 실패: {room_id} - {e}")
            return False, "확인 실패"
    
    # ==================== 유틸리티 메서드 ====================
    
    async def _set_initial_state(self, redis, state_key: str, initial_state: str, ttl: int = 3600):
        """초기 상태 설정"""
        try:
            await redis.set_string(state_key, initial_state, expire=ttl)
        except Exception as e:
            Logger.error(f"초기 상태 설정 실패: {state_key} - {e}")
    
    async def get_state_logs(self, entity_id: str, entity_type: str = "message") -> List[str]:
        """상태 전이 로그 조회 (디버깅용)"""
        try:
            if entity_type == "message":
                state_key = self.message_state_key_pattern.format(message_id=entity_id)
            else:
                state_key = self.room_state_key_pattern.format(room_id=entity_id)
            
            log_key = f"{state_key}:log"
            
            async with CacheService.get_client() as redis:
                logs = await redis.list_range(log_key, 0, -1)
                return logs or []
                
        except Exception as e:
            Logger.error(f"상태 로그 조회 실패: {entity_id} - {e}")
            return []
    
    async def cleanup_expired_states(self, batch_size: int = 100) -> int:
        """만료된 상태 정리 (스케줄러에서 주기적 호출)"""
        try:
            if not self.__class__._initialized:
                return 0
            
            cleaned_count = 0
            async with CacheService.get_client() as redis:
                # 만료된 상태 키들 스캔 및 정리
                # 실제 구현에서는 더 정교한 정리 로직 필요
                pass
            
            return cleaned_count
            
        except Exception as e:
            Logger.error(f"상태 정리 중 오류: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """상태 머신 통계 반환"""
        return {
            "initialized": self.__class__._initialized,
            "message_states": [state.value for state in MessageState],
            "room_states": [state.value for state in RoomState],
            "transitions_defined": {
                "message": len(self.message_transitions),
                "room": len(self.room_transitions)
            }
        }


# 전역 함수들 (CacheService 패턴과 동일)
def get_chat_state_machine() -> ChatStateMachine:
    """ChatStateMachine 인스턴스 반환"""
    return ChatStateMachine.get_instance()


async def initialize_chat_state_machine() -> bool:
    """ChatStateMachine 초기화"""
    return await ChatStateMachine.init()


async def shutdown_chat_state_machine():
    """ChatStateMachine 종료"""
    await ChatStateMachine.shutdown()