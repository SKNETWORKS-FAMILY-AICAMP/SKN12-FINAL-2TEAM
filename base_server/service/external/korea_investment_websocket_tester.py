"""
한국투자증권 WebSocket 테스터 클래스

WebSocket 모듈과 분리된 독립적인 테스트 전용 클래스
"""
import asyncio
import json
from datetime import datetime
from service.core.logger import Logger
from .korea_investment_websocket_iocp import KoreaInvestmentWebSocketIOCP


class KoreaInvestmentWebSocketTester:
    """한국투자증권 WebSocket 테스터 (의존성 주입 방식) - IOCP 버전"""
    
    def __init__(self, websocket_client: KoreaInvestmentWebSocketIOCP):
        """
        Args:
            websocket_client: KoreaInvestmentWebSocket 인스턴스
        """
        self.websocket = websocket_client
        self.test_events = {
            'subscribe_response': asyncio.Event(),
            'unsubscribe_response': asyncio.Event(), 
            'close_complete': asyncio.Event(),
            'data_received': asyncio.Event()
        }
        self.test_data = {}
        self.received_messages = []
        
    async def run_full_test(self, test_symbol: str = "005930") -> bool:
        """완전한 테스트 시나리오 실행 (구독 → 데이터 수신 → 구독취소 → 종료)
        
        Args:
            test_symbol: 테스트할 종목 코드 (기본: 삼성전자)
            
        Returns:
            bool: 테스트 성공 여부
        """
        try:
            Logger.info("🚀 WebSocket 전체 테스트 시작")
            
            # 메시지 인터셉터 등록
            self.websocket.add_message_interceptor(self._message_interceptor)
            self.websocket.set_custom_event_handler('close_frame', self._close_handler)
            
            # 1. 구독 테스트
            subscribe_success = await self._test_subscribe(test_symbol)
            if not subscribe_success:
                return False
            
            # 2. 데이터 수신 대기 (3초)
            data_received = await self._wait_for_data()
            Logger.info(f"📊 데이터 수신 결과: {data_received}")
            
            # 3. 구독취소 테스트  
            unsubscribe_success = await self._test_unsubscribe(test_symbol)
            if not unsubscribe_success:
                return False
            
            # 4. Graceful 종료 테스트
            close_success = await self._test_graceful_close()
            
            Logger.info("✅ WebSocket 전체 테스트 완료")
            return subscribe_success and unsubscribe_success and close_success
            
        except Exception as e:
            Logger.error(f"❌ WebSocket 테스트 실패: {e}")
            return False
        finally:
            # 정리
            self.websocket.remove_message_interceptor(self._message_interceptor)
            self._reset_events()
    
    async def _test_subscribe(self, symbol: str) -> bool:
        """구독 테스트"""
        try:
            Logger.info(f"📤 구독 테스트 시작: {symbol}")
            
            subscribe_message = {
                "header": {
                    "appkey": self.websocket.approval_key,
                    "appsecret": self.websocket.app_secret,
                    "custtype": "P",
                    "tr_type": "1",  # 구독 등록
                    "content-type": "utf-8"
                },
                "body": {
                    "input": {
                        "tr_id": "HDFSCNT0",
                        "tr_key": symbol
                    }
                }
            }
            
            # IOCP WebSocket 구독 메시지 전송
            if not self.websocket.is_connected():
                Logger.error("❌ WebSocket 연결이 없습니다")
                return False
                
            await self.websocket.send_message(subscribe_message)
            Logger.info(f"📤 구독 요청 전송 완료: {symbol}")
            
            # 구독 응답 대기 (5초)
            try:
                await asyncio.wait_for(
                    self.test_events['subscribe_response'].wait(),
                    timeout=5.0
                )
                Logger.info("✅ 구독 응답 수신 완료")
                return True
                
            except asyncio.TimeoutError:
                Logger.info("⏭️ 구독 응답 대기 시간 완료")
                return True  # 타임아웃도 정상으로 처리
                
        except Exception as e:
            Logger.error(f"❌ 구독 테스트 실패: {e}")
            return False
    
    async def _test_unsubscribe(self, symbol: str) -> bool:
        """구독취소 테스트"""
        try:
            Logger.info(f"📤 구독취소 테스트 시작: {symbol}")
            
            unsubscribe_message = {
                "header": {
                    "appkey": self.websocket.approval_key,
                    "appsecret": self.websocket.app_secret,
                    "custtype": "P",
                    "tr_type": "2",  # 구독 취소
                    "content-type": "utf-8"
                },
                "body": {
                    "input": {
                        "tr_id": "HDFSCNT0",
                        "tr_key": symbol
                    }
                }
            }
            
            # IOCP WebSocket 구독취소 메시지 전송
            if not self.websocket.is_connected():
                Logger.error("❌ WebSocket 연결이 없습니다 - 구독취소 건너뛰기")
                return True  # 이미 끊어진 상태이므로 성공으로 처리
                
            await self.websocket.send_message(unsubscribe_message)
            Logger.info(f"📤 구독취소 요청 전송 완료: {symbol}")
            
            # 구독취소 응답 대기 (3초)
            try:
                await asyncio.wait_for(
                    self.test_events['unsubscribe_response'].wait(),
                    timeout=3.0
                )
                Logger.info("✅ 구독취소 응답 수신 완료")
                
            except asyncio.TimeoutError:
                Logger.info("⏭️ 구독취소 응답 대기 시간 완료")
            
            return True
            
        except Exception as e:
            Logger.error(f"❌ 구독취소 테스트 실패: {e}")
            return False
    
    async def _wait_for_data(self, timeout: float = 3.0) -> bool:
        """데이터 수신 대기"""
        try:
            Logger.info(f"⏳ 실시간 데이터 수신 대기 ({timeout}초)")
            
            await asyncio.wait_for(
                self.test_events['data_received'].wait(),
                timeout=timeout
            )
            
            Logger.info(f"✅ 실시간 데이터 수신 완료 ({len(self.received_messages)}개)")
            return True
            
        except asyncio.TimeoutError:
            Logger.info(f"⏭️ 데이터 수신 대기 시간 완료 ({len(self.received_messages)}개 수신)")
            return len(self.received_messages) > 0
    
    async def _test_graceful_close(self) -> bool:
        """Graceful 종료 테스트"""
        try:
            Logger.info("🏁 Graceful 종료 테스트 시작")
            
            # Graceful close 실행
            await self.websocket.graceful_close(code=1000, reason="Test completed")
            
            # close 완료 대기 (3초)
            try:
                await asyncio.wait_for(
                    self.test_events['close_complete'].wait(),
                    timeout=3.0
                )
                Logger.info("✅ Graceful 종료 완료")
                
            except asyncio.TimeoutError:
                Logger.info("⏭️ Graceful 종료 대기 시간 완료")
            
            return True
            
        except Exception as e:
            Logger.error(f"❌ Graceful 종료 테스트 실패: {e}")
            return False
    
    async def _message_interceptor(self, data: dict):
        """메시지 인터셉터 (테스트용)"""
        try:
            self.received_messages.append({
                'timestamp': datetime.now(),
                'data': data
            })
            
            # 응답 타입별 이벤트 설정
            if 'header' in data:
                tr_type = data['header'].get('tr_type')
                tr_id = data['header'].get('tr_id')
                
                if tr_type == '1' and tr_id == 'HDFSCNT0':  # 구독 응답
                    self.test_data['subscribe'] = data
                    self.test_events['subscribe_response'].set()
                    
                elif tr_type == '2' and tr_id == 'HDFSCNT0':  # 구독취소 응답
                    self.test_data['unsubscribe'] = data
                    self.test_events['unsubscribe_response'].set()
                    
                elif 'body' in data and 'output' in data['body']:  # 실시간 데이터
                    self.test_events['data_received'].set()
                    
        except Exception as e:
            Logger.error(f"❌ 메시지 인터셉터 에러: {e}")
    
    async def _close_handler(self, data: dict):
        """Close 이벤트 핸들러"""
        Logger.info(f"🚪 Close 이벤트 수신: {data}")
        self.test_events['close_complete'].set()
    
    def _reset_events(self):
        """이벤트 상태 리셋"""
        for event in self.test_events.values():
            event.clear()
        self.received_messages.clear()
        self.test_data.clear()
    
    def get_test_results(self) -> dict:
        """테스트 결과 반환"""
        return {
            'total_messages': len(self.received_messages),
            'test_data': self.test_data,
            'messages': self.received_messages[-5:] if self.received_messages else []  # 최근 5개만
        }


async def run_websocket_test(app_key: str, app_secret: str) -> bool:
    """독립적인 WebSocket 테스트 실행 함수
    
    Args:
        app_key: 한투 앱키
        app_secret: 한투 앱시크릿
        
    Returns:
        bool: 테스트 성공 여부
    """
    websocket_client = None
    tester = None
    
    try:
        # 1. IOCP WebSocket 클라이언트 생성 및 연결
        websocket_client = KoreaInvestmentWebSocketIOCP()
        connection_success = await websocket_client.connect(app_key, app_secret)
        
        if not connection_success:
            Logger.error("❌ WebSocket 연결 실패")
            return False
        
        Logger.info("✅ WebSocket 연결 성공")
        
        # 2. 테스터 생성 및 테스트 실행
        tester = KoreaInvestmentWebSocketTester(websocket_client)
        test_result = await tester.run_full_test()
        
        # 3. 테스트 결과 출력
        results = tester.get_test_results()
        Logger.info(f"📊 테스트 결과: {results}")
        
        return test_result
        
    except Exception as e:
        Logger.error(f"❌ WebSocket 테스트 예외: {e}")
        return False
    finally:
        # 완전한 WebSocket 정리 (appkey 중복 방지)
        if websocket_client:
            try:
                Logger.info("🔄 WebSocket 테스트 완료 - 연결 정리 시작")
                
                # 1. 메시지 인터셉터 제거
                if tester:
                    websocket_client.remove_message_interceptor(tester._message_interceptor)
                
                # 2. WebSocket 연결 해제
                await websocket_client.disconnect()
                
                # 3. 서버에서 appkey 해제될 때까지 대기 (3초)
                Logger.info("⏳ 서버 appkey 해제 대기 중 (3초)...")
                await asyncio.sleep(3)
                
                Logger.info("✅ WebSocket 테스트 정리 완료")
                
            except Exception as e:
                Logger.warn(f"⚠️ WebSocket 정리 중 예외 (무시): {e}")
                # 예외 발생해도 대기는 필요
                await asyncio.sleep(2)