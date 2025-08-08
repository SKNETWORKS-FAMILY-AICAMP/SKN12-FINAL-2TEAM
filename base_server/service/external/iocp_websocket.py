"""
범용 IOCP WebSocket 모듈

게임서버 IOCP 패턴을 적용한 이벤트 기반 WebSocket:
1. 완전한 이벤트 기반 아키텍처
2. 상태 머신 패턴
3. 이벤트 핸들러 시스템
4. 메시지 인터셉터 시스템
"""
import asyncio
import websockets
import json
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any, Union
from enum import Enum
from dataclasses import dataclass
from service.core.logger import Logger


class WebSocketState(Enum):
    """WebSocket 상태"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting" 
    CONNECTED = "connected"
    AUTHENTICATING = "authenticating"
    AUTHENTICATED = "authenticated"
    SUBSCRIBING = "subscribing"
    SUBSCRIBED = "subscribed"
    CLOSING = "closing"
    CLOSED = "closed"
    ERROR = "error"


class IOCPEventType(Enum):
    """IOCP 이벤트 타입"""
    CONNECT_REQUEST = "connect_request"
    CONNECT_COMPLETE = "connect_complete"
    RECV_DATA = "recv_data"
    SEND_REQUEST = "send_request"  
    SEND_COMPLETE = "send_complete"
    SUBSCRIBE_REQUEST = "subscribe_request"
    SUBSCRIBE_COMPLETE = "subscribe_complete"
    UNSUBSCRIBE_REQUEST = "unsubscribe_request"
    UNSUBSCRIBE_COMPLETE = "unsubscribe_complete"
    CLOSE_REQUEST = "close_request"
    CLOSE_COMPLETE = "close_complete"
    ERROR_OCCURRED = "error_occurred"
    CONNECTION_LOST = "connection_lost"


@dataclass
class IOCPWebSocketEvent:
    """IOCP WebSocket 이벤트"""
    event_type: IOCPEventType
    data: Dict[str, Any]
    timestamp: datetime
    connection_id: str = ""
    callback: Optional[Callable] = None


class IOCPWebSocket:
    """IOCP 패턴 WebSocket 클래스"""
    
    def __init__(self, connection_id: str = ""):
        # 연결 ID
        self.connection_id = connection_id or f"ws_{datetime.now().timestamp()}"
        
        # WebSocket 상태
        self._state = WebSocketState.DISCONNECTED
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        
        # 연결 정보
        self.url: Optional[str] = None
        self.headers: Dict[str, str] = {}
        
        # IOCP 이벤트 시스템
        self._event_queue = asyncio.Queue()
        self._event_handlers = {}
        self._event_loop_task: Optional[asyncio.Task] = None
        self._recv_task: Optional[asyncio.Task] = None
        self._running = False
        
        # 메시지 인터셉터
        self._message_interceptors: List[Callable] = []
        
        # 상태별 이벤트
        self._state_events = {
            state: asyncio.Event() for state in WebSocketState
        }
        
        # 작업 완료 이벤트
        self._unsubscribe_complete_event = asyncio.Event()
        
        # 이벤트 핸들러 등록
        self._register_event_handlers()
        
        Logger.info(f"🚀 IOCP WebSocket 생성: {self.connection_id}")
    
    def _register_event_handlers(self):
        """이벤트 핸들러 등록"""
        self._event_handlers = {
            IOCPEventType.CONNECT_REQUEST: self._handle_connect_request,
            IOCPEventType.CONNECT_COMPLETE: self._handle_connect_complete,
            IOCPEventType.RECV_DATA: self._handle_recv_data,
            IOCPEventType.SEND_REQUEST: self._handle_send_request,
            IOCPEventType.SEND_COMPLETE: self._handle_send_complete,
            IOCPEventType.SUBSCRIBE_REQUEST: self._handle_subscribe_request,
            IOCPEventType.SUBSCRIBE_COMPLETE: self._handle_subscribe_complete,
            IOCPEventType.UNSUBSCRIBE_REQUEST: self._handle_unsubscribe_request,
            IOCPEventType.UNSUBSCRIBE_COMPLETE: self._handle_unsubscribe_complete,
            IOCPEventType.CLOSE_REQUEST: self._handle_close_request,
            IOCPEventType.CLOSE_COMPLETE: self._handle_close_complete,
            IOCPEventType.ERROR_OCCURRED: self._handle_error,
            IOCPEventType.CONNECTION_LOST: self._handle_connection_lost
        }
    
    # =================
    # Public Methods
    # =================
    
    async def start(self):
        """IOCP 이벤트 루프 시작"""
        if self._running:
            Logger.warn(f"⚠️ IOCP 루프가 이미 실행 중: {self.connection_id}")
            return
            
        self._running = True
        self._event_loop_task = asyncio.create_task(self._event_loop())
        Logger.info(f"🔄 IOCP 이벤트 루프 시작: {self.connection_id}")
    
    async def stop(self):
        """IOCP 이벤트 루프 종료"""
        self._running = False
        
        # recv 태스크 정리
        if self._recv_task and not self._recv_task.done():
            self._recv_task.cancel()
            try:
                await self._recv_task
            except asyncio.CancelledError:
                pass
        
        # 이벤트 루프 종료
        if self._event_loop_task:
            await self._event_loop_task
            
        Logger.info(f"✅ IOCP 이벤트 루프 종료: {self.connection_id}")
    
    async def connect(self, url: str, headers: Optional[Dict[str, str]] = None) -> bool:
        """WebSocket 연결"""
        if not self._running:
            await self.start()
        
        self.url = url
        self.headers = headers or {}
        
        # 연결 이벤트 전송
        event = IOCPWebSocketEvent(
            event_type=IOCPEventType.CONNECT_REQUEST,
            data={"url": url, "headers": self.headers},
            timestamp=datetime.now(),
            connection_id=self.connection_id
        )
        
        await self._post_event(event)
        
        # 연결 완료 대기
        try:
            await asyncio.wait_for(
                self._state_events[WebSocketState.CONNECTED].wait(),
                timeout=10.0
            )
            return True
        except asyncio.TimeoutError:
            Logger.error(f"❌ 연결 타임아웃: {self.connection_id}")
            return False
    
    async def send_message(self, message: Union[str, Dict]) -> bool:
        """메시지 전송"""
        if self._state == WebSocketState.DISCONNECTED:
            Logger.error(f"❌ 연결되지 않은 상태: {self.connection_id}")
            return False
        
        # 전송 이벤트 생성
        event = IOCPWebSocketEvent(
            event_type=IOCPEventType.SEND_REQUEST,
            data={"message": message},
            timestamp=datetime.now(),
            connection_id=self.connection_id
        )
        
        await self._post_event(event)
        return True
    
    async def subscribe(self, subscribe_data: Dict) -> bool:
        """구독 요청"""
        event = IOCPWebSocketEvent(
            event_type=IOCPEventType.SUBSCRIBE_REQUEST,
            data=subscribe_data,
            timestamp=datetime.now(),
            connection_id=self.connection_id
        )
        
        await self._post_event(event)
        return True
    
    async def unsubscribe(self, unsubscribe_data: Dict) -> bool:
        """구독 취소"""
        # 완료 이벤트 리셋
        self._unsubscribe_complete_event.clear()
        
        event = IOCPWebSocketEvent(
            event_type=IOCPEventType.UNSUBSCRIBE_REQUEST,
            data=unsubscribe_data,
            timestamp=datetime.now(),
            connection_id=self.connection_id
        )
        
        await self._post_event(event)
        return True
    
    async def wait_for_unsubscribe_complete(self, timeout: float = 2.0) -> bool:
        """구독 취소 완료 대기"""
        try:
            await asyncio.wait_for(self._unsubscribe_complete_event.wait(), timeout=timeout)
            Logger.info(f"✅ 구독 취소 완료 확인: {self.connection_id}")
            return True
        except asyncio.TimeoutError:
            Logger.warn(f"⚠️ 구독 취소 완료 대기 타임아웃: {self.connection_id}")
            return False
    
    async def disconnect(self):
        """연결 해제"""
        if self._state == WebSocketState.DISCONNECTED:
            return
            
        event = IOCPWebSocketEvent(
            event_type=IOCPEventType.CLOSE_REQUEST,
            data={},
            timestamp=datetime.now(),
            connection_id=self.connection_id
        )
        
        await self._post_event(event)
        
        # 연결 해제 완료 대기
        try:
            await asyncio.wait_for(
                self._state_events[WebSocketState.DISCONNECTED].wait(),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            Logger.warn(f"⚠️ 연결 해제 타임아웃: {self.connection_id}")
    
    def add_message_interceptor(self, interceptor: Callable[[Dict], None]):
        """메시지 인터셉터 추가"""
        if interceptor not in self._message_interceptors:
            self._message_interceptors.append(interceptor)
            Logger.info(f"📨 메시지 인터셉터 등록: {self.connection_id}")
    
    def remove_message_interceptor(self, interceptor: Callable[[Dict], None]):
        """메시지 인터셉터 제거"""
        if interceptor in self._message_interceptors:
            self._message_interceptors.remove(interceptor)
            Logger.info(f"🗑️ 메시지 인터셉터 해제: {self.connection_id}")
    
    # =================
    # State Management
    # =================
    
    def _set_state(self, new_state: WebSocketState):
        """상태 변경"""
        old_state = self._state
        self._state = new_state
        
        # 이전 상태 이벤트 클리어
        if old_state in self._state_events:
            self._state_events[old_state].clear()
        
        # 새 상태 이벤트 설정
        if new_state in self._state_events:
            self._state_events[new_state].set()
        
        Logger.info(f"🔄 상태 변경: {old_state.value} → {new_state.value} ({self.connection_id})")
    
    def get_state(self) -> WebSocketState:
        """현재 상태 반환"""
        return self._state
    
    def is_connected(self) -> bool:
        """연결 상태 확인"""
        return self._state in [
            WebSocketState.CONNECTED,
            WebSocketState.AUTHENTICATED,
            WebSocketState.SUBSCRIBED
        ]
    
    def is_fully_disconnected(self) -> bool:
        """완전 해제 상태 확인"""
        return self._state == WebSocketState.DISCONNECTED and not self._running
    
    async def wait_for_complete_shutdown(self, timeout: float = 5.0) -> bool:
        """완전 종료 대기 (이벤트 기반)"""
        if self.is_fully_disconnected():
            return True
            
        try:
            # DISCONNECTED 상태가 될 때까지 대기
            await asyncio.wait_for(
                self._state_events[WebSocketState.DISCONNECTED].wait(),
                timeout=timeout
            )
            
            # 이벤트 루프 완전 종료까지 대기
            if self._event_loop_task:
                await asyncio.wait_for(self._event_loop_task, timeout=2.0)
                
            return True
            
        except asyncio.TimeoutError:
            Logger.warn(f"⚠️ 완전 종료 타임아웃: {self.connection_id}")
            return False
    
    # =================
    # IOCP Event Loop
    # =================
    
    async def _event_loop(self):
        """IOCP 메인 이벤트 루프"""
        Logger.info(f"🔄 IOCP 이벤트 처리 시작: {self.connection_id}")
        
        while self._running:
            try:
                # 이벤트 대기
                try:
                    event = await asyncio.wait_for(
                        self._event_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # 이벤트 처리
                await self._process_event(event)
                
            except Exception as e:
                Logger.error(f"❌ IOCP 루프 에러: {e} ({self.connection_id})")
                # 에러 이벤트 생성
                error_event = IOCPWebSocketEvent(
                    event_type=IOCPEventType.ERROR_OCCURRED,
                    data={"error": str(e)},
                    timestamp=datetime.now(),
                    connection_id=self.connection_id
                )
                await self._process_event(error_event)
        
        Logger.info(f"🏁 IOCP 이벤트 루프 종료: {self.connection_id}")
    
    async def _post_event(self, event: IOCPWebSocketEvent):
        """이벤트 큐에 이벤트 게시"""
        await self._event_queue.put(event)
    
    async def _process_event(self, event: IOCPWebSocketEvent):
        """이벤트 처리"""
        try:
            handler = self._event_handlers.get(event.event_type)
            if handler:
                Logger.info(f"📨 IOCP 이벤트 처리: {event.event_type.value} ({self.connection_id})")
                await handler(event)
            else:
                Logger.warn(f"⚠️ 미등록 이벤트: {event.event_type.value} ({self.connection_id})")
                
        except Exception as e:
            Logger.error(f"❌ 이벤트 처리 실패: {event.event_type.value} - {e} ({self.connection_id})")
    
    # =================
    # Event Handlers
    # =================
    
    async def _handle_connect_request(self, event: IOCPWebSocketEvent):
        """연결 요청 처리"""
        self._set_state(WebSocketState.CONNECTING)
        
        try:
            url = event.data["url"]
            headers = event.data["headers"]
            
            Logger.info(f"🔌 WebSocket 연결 시도: {url} ({self.connection_id})")
            
            # WebSocket 연결
            self.websocket = await websockets.connect(
                url,
                additional_headers=headers,
                ping_interval=20,
                ping_timeout=10
            )
            
            self._set_state(WebSocketState.CONNECTED)
            Logger.info(f"✅ WebSocket 연결 성공: {self.connection_id}")
            
            # recv 루프 시작
            self._recv_task = asyncio.create_task(self._recv_loop())
            
            # 연결 완료 이벤트
            complete_event = IOCPWebSocketEvent(
                event_type=IOCPEventType.CONNECT_COMPLETE,
                data={"success": True},
                timestamp=datetime.now(),
                connection_id=self.connection_id
            )
            await self._post_event(complete_event)
            
        except Exception as e:
            Logger.error(f"❌ 연결 실패: {e} ({self.connection_id})")
            self._set_state(WebSocketState.ERROR)
            
            # 연결 완료 이벤트 (실패)
            complete_event = IOCPWebSocketEvent(
                event_type=IOCPEventType.CONNECT_COMPLETE,
                data={"success": False, "error": str(e)},
                timestamp=datetime.now(),
                connection_id=self.connection_id
            )
            await self._post_event(complete_event)
    
    async def _handle_connect_complete(self, event: IOCPWebSocketEvent):
        """연결 완료 처리"""
        success = event.data.get("success", False)
        if success:
            Logger.info(f"✅ 연결 완료 이벤트 처리: {self.connection_id}")
        else:
            error = event.data.get("error", "Unknown error")
            Logger.error(f"❌ 연결 완료 실패: {error} ({self.connection_id})")
    
    async def _handle_recv_data(self, event: IOCPWebSocketEvent):
        """수신 데이터 처리"""
        try:
            data = event.data["message"]
            Logger.info(f"📨 데이터 수신: {self.connection_id}")
            
            # 메시지 인터셉터 호출
            for interceptor in self._message_interceptors:
                try:
                    await interceptor(data)
                except Exception as e:
                    Logger.error(f"❌ 인터셉터 에러: {e} ({self.connection_id})")
            
        except Exception as e:
            Logger.error(f"❌ 수신 데이터 처리 실패: {e} ({self.connection_id})")
    
    async def _handle_send_request(self, event: IOCPWebSocketEvent):
        """전송 요청 처리"""
        try:
            message = event.data["message"]
            
            if not self.websocket:
                Logger.error(f"❌ WebSocket 연결 없음: {self.connection_id}")
                return
            
            # JSON 변환
            if isinstance(message, dict):
                message_str = json.dumps(message)
            else:
                message_str = str(message)
            
            # 전송
            await self.websocket.send(message_str)
            Logger.info(f"📤 메시지 전송 완료: {self.connection_id}")
            
            # 전송 완료 이벤트
            complete_event = IOCPWebSocketEvent(
                event_type=IOCPEventType.SEND_COMPLETE,
                data={"success": True},
                timestamp=datetime.now(),
                connection_id=self.connection_id
            )
            await self._post_event(complete_event)
            
        except Exception as e:
            Logger.error(f"❌ 메시지 전송 실패: {e} ({self.connection_id})")
            
            # 전송 완료 이벤트 (실패)
            complete_event = IOCPWebSocketEvent(
                event_type=IOCPEventType.SEND_COMPLETE,
                data={"success": False, "error": str(e)},
                timestamp=datetime.now(),
                connection_id=self.connection_id
            )
            await self._post_event(complete_event)
    
    async def _handle_send_complete(self, event: IOCPWebSocketEvent):
        """전송 완료 처리"""
        success = event.data.get("success", False)
        if success:
            Logger.info(f"📤 전송 완료: {self.connection_id}")
        else:
            error = event.data.get("error", "Unknown error")
            Logger.error(f"❌ 전송 실패: {error} ({self.connection_id})")
    
    async def _handle_subscribe_request(self, event: IOCPWebSocketEvent):
        """구독 요청 처리"""
        self._set_state(WebSocketState.SUBSCRIBING)
        Logger.info(f"📤 구독 요청: {self.connection_id}")
        
        # 구독 메시지 전송
        await self.send_message(event.data)
        
        self._set_state(WebSocketState.SUBSCRIBED)
        
        # 구독 완료 이벤트
        complete_event = IOCPWebSocketEvent(
            event_type=IOCPEventType.SUBSCRIBE_COMPLETE,
            data={"success": True},
            timestamp=datetime.now(),
            connection_id=self.connection_id
        )
        await self._post_event(complete_event)
    
    async def _handle_subscribe_complete(self, event: IOCPWebSocketEvent):
        """구독 완료 처리"""
        success = event.data.get("success", False)
        if success:
            Logger.info(f"📤 구독 완료: {self.connection_id}")
        else:
            error = event.data.get("error", "Unknown error")
            Logger.error(f"❌ 구독 실패: {error} ({self.connection_id})")
    
    async def _handle_unsubscribe_request(self, event: IOCPWebSocketEvent):
        """구독 취소 처리"""
        Logger.info(f"📤 구독 취소: {self.connection_id}")
        
        # 구독 취소 메시지 전송
        await self.send_message(event.data)
        
        self._set_state(WebSocketState.CONNECTED)
        
        # 구독 취소 완료 이벤트
        complete_event = IOCPWebSocketEvent(
            event_type=IOCPEventType.UNSUBSCRIBE_COMPLETE,
            data={"success": True},
            timestamp=datetime.now(),
            connection_id=self.connection_id
        )
        await self._post_event(complete_event)
    
    async def _handle_unsubscribe_complete(self, event: IOCPWebSocketEvent):
        """구독 취소 완료 처리"""
        success = event.data.get("success", False)
        if success:
            Logger.info(f"📤 구독 취소 완료: {self.connection_id}")
        else:
            error = event.data.get("error", "Unknown error")
            Logger.error(f"❌ 구독 취소 실패: {error} ({self.connection_id})")
        
        # 구독 취소 완료 이벤트 설정
        self._unsubscribe_complete_event.set()
    
    async def _handle_close_request(self, event: IOCPWebSocketEvent):
        """연결 해제 요청 처리"""
        self._set_state(WebSocketState.CLOSING)
        Logger.info(f"🚪 연결 해제 시작: {self.connection_id}")
        
        try:
            # recv 태스크 정리
            if self._recv_task and not self._recv_task.done():
                self._recv_task.cancel()
                try:
                    await self._recv_task
                except asyncio.CancelledError:
                    pass
            
            # WebSocket 연결 해제
            if self.websocket:
                await self.websocket.close()
                self.websocket = None
            
            self._set_state(WebSocketState.DISCONNECTED)
            Logger.info(f"✅ 연결 해제 완료: {self.connection_id}")
            
            # 해제 완료 이벤트
            complete_event = IOCPWebSocketEvent(
                event_type=IOCPEventType.CLOSE_COMPLETE,
                data={"success": True},
                timestamp=datetime.now(),
                connection_id=self.connection_id
            )
            await self._post_event(complete_event)
            
        except Exception as e:
            Logger.error(f"❌ 연결 해제 실패: {e} ({self.connection_id})")
            self._set_state(WebSocketState.ERROR)
    
    async def _handle_close_complete(self, event: IOCPWebSocketEvent):
        """연결 해제 완료 처리"""
        success = event.data.get("success", False)
        if success:
            Logger.info(f"🚪 연결 해제 완료: {self.connection_id}")
        else:
            error = event.data.get("error", "Unknown error")
            Logger.error(f"❌ 연결 해제 실패: {error} ({self.connection_id})")
    
    async def _handle_error(self, event: IOCPWebSocketEvent):
        """에러 처리"""
        error_msg = event.data.get("error", "Unknown error")
        Logger.error(f"❌ IOCP 에러: {error_msg} ({self.connection_id})")
        self._set_state(WebSocketState.ERROR)
    
    async def _handle_connection_lost(self, event: IOCPWebSocketEvent):
        """연결 끊김 처리"""
        Logger.warn(f"🔌 연결 끊어짐: {self.connection_id}")
        self._set_state(WebSocketState.DISCONNECTED)
        
        # WebSocket 정리
        if self.websocket:
            self.websocket = None
    
    # =================
    # Recv Loop
    # =================
    
    async def _recv_loop(self):
        """IOCP 수신 루프"""
        Logger.info(f"🔄 IOCP recv 루프 시작: {self.connection_id}")
        
        try:
            while self.is_connected() and self.websocket:
                try:
                    # 메시지 수신 대기
                    message_str = await self.websocket.recv()
                    
                    # JSON 파싱
                    try:
                        message_data = json.loads(message_str)
                    except json.JSONDecodeError:
                        message_data = {"raw": message_str}
                    
                    # 수신 이벤트 생성
                    recv_event = IOCPWebSocketEvent(
                        event_type=IOCPEventType.RECV_DATA,
                        data={"message": message_data},
                        timestamp=datetime.now(),
                        connection_id=self.connection_id
                    )
                    
                    await self._post_event(recv_event)
                    
                except websockets.exceptions.ConnectionClosed:
                    Logger.info(f"🚪 WebSocket 연결 종료: {self.connection_id}")
                    break
                except Exception as e:
                    Logger.error(f"❌ recv 루프 에러: {e} ({self.connection_id})")
                    break
                    
        except Exception as e:
            Logger.error(f"❌ recv 루프 예외: {e} ({self.connection_id})")
        finally:
            # 연결 끊김 이벤트
            lost_event = IOCPWebSocketEvent(
                event_type=IOCPEventType.CONNECTION_LOST,
                data={},
                timestamp=datetime.now(),
                connection_id=self.connection_id
            )
            await self._post_event(lost_event)
            
        Logger.info(f"🏁 IOCP recv 루프 종료: {self.connection_id}")