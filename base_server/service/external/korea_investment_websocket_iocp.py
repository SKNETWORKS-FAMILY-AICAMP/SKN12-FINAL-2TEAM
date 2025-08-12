"""
한국투자증권 WebSocket 클래스 - IOCP 패턴 사용

범용 IOCP WebSocket 모듈을 사용하는 한국투자증권 전용 구현
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, Optional, Callable, Any
from service.core.logger import Logger
from .iocp_websocket import IOCPWebSocket, WebSocketState


class KoreaInvestmentWebSocketIOCP:
    """한국투자증권 WebSocket - IOCP 패턴"""
    
    def __init__(self):
        self.iocp_websocket = IOCPWebSocket("korea_investment_ws")
        
        # 한투증권 관련 정보
        self.app_key: Optional[str] = None
        self.app_secret: Optional[str] = None
        self.approval_key: Optional[str] = None
        
        # WebSocket URL
        self.ws_url = "ws://ops.koreainvestment.com:21000"
        
        # REST API 폴백 플래그
        self._use_rest_fallback = False
        
        Logger.info("🚀 한국투자증권 IOCP WebSocket 생성")
    
    async def connect(self, app_key: str, app_secret: str, approval_key: Optional[str] = None) -> bool:
        """한국투자증권 WebSocket 연결"""
        try:
            self.app_key = app_key
            self.app_secret = app_secret
            
            # WebSocket 연결 전에 REST API 토큰이 유효한지 확인 (중요!)
            try:
                from service.external.korea_investment_service import KoreaInvestmentService
                if KoreaInvestmentService.is_initialized():
                    # 유효한 토큰이 있는지 확인 (이 과정에서 자동으로 토큰 검증/갱신됨)
                    current_token = await KoreaInvestmentService._get_current_token()
                    if current_token:
                        Logger.info("✅ WebSocket 연결 전 REST API 토큰 유효성 확인 완료")
                    else:
                        Logger.warn("⚠️ WebSocket 연결 전 REST API 토큰 확인 실패")
                else:
                    Logger.warn("⚠️ KoreaInvestmentService가 초기화되지 않음")
            except Exception as token_check_e:
                Logger.warn(f"⚠️ WebSocket 연결 전 토큰 확인 중 예외: {token_check_e}")
            
            self.approval_key = approval_key or await self._get_approval_key()
            
            if not self.approval_key:
                Logger.error("❌ approval_key가 없습니다")
                return False
            
            # 연결 헤더 설정
            headers = {
                "Sec-WebSocket-Protocol": "echo-protocol"
            }
            
            Logger.info(f"🔌 한국투자증권 WebSocket 연결 시도")
            
            # 한투증권 메시지 인터셉터 등록 (연결 전에 등록)
            self.iocp_websocket.add_message_interceptor(self._korea_message_interceptor)
            Logger.info("📌 한투증권 메시지 인터셉터 등록 완료")
            
            # IOCP WebSocket으로 연결
            success = await self.iocp_websocket.connect(self.ws_url, headers)
            
            if success:
                Logger.info("✅ 한국투자증권 WebSocket 연결 성공")
            else:
                Logger.error("❌ 한국투자증권 WebSocket 연결 실패")
                
            return success
            
        except Exception as e:
            Logger.error(f"❌ 한국투자증권 WebSocket 연결 예외: {e}")
            return False
    
    async def subscribe_stock(self, symbol: str) -> bool:
        """주식 실시간 데이터 구독"""
        try:
            subscribe_message = {
                "header": {
                    "appkey": self.app_key,
                    "appsecret": self.app_secret,
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
            
            Logger.info(f"📤 주식 구독 요청: {symbol}")
            return await self.iocp_websocket.subscribe(subscribe_message)
            
        except Exception as e:
            Logger.error(f"❌ 주식 구독 실패: {e}")
            return False
    
    async def unsubscribe_stock(self, symbol: str) -> bool:
        """주식 실시간 데이터 구독 취소"""
        try:
            unsubscribe_message = {
                "header": {
                    "appkey": self.app_key,
                    "appsecret": self.app_secret,
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
            
            Logger.info(f"📤 주식 구독 취소: {symbol}")
            success = await self.iocp_websocket.unsubscribe(unsubscribe_message)
            
            if success:
                # 구독 취소 완료 대기
                await self.iocp_websocket.wait_for_unsubscribe_complete(timeout=2.0)
            
            return success
            
        except Exception as e:
            Logger.error(f"❌ 주식 구독 취소 실패: {e}")
            return False
    
    async def subscribe_overseas_stock_price(self, exchange: str, symbols: list, callback=None) -> bool:
        """해외주식 실시간 데이터 구독 (기존 코드 호환성)"""
        try:
            Logger.info(f"📤 해외주식 구독 요청: {exchange} - {symbols}")
            
            # 콜백이 있으면 메시지 인터셉터로 등록
            if callback:
                async def overseas_interceptor(data):
                    try:
                        # 해외주식 데이터인지 확인하고 콜백 호출
                        if 'header' in data and 'body' in data:
                            # 해외주식 데이터 변환 로직
                            processed_data = {
                                'current_price': data.get('body', {}).get('output', {}).get('last', 0),
                                'high_price': data.get('body', {}).get('output', {}).get('high', 0),
                                'low_price': data.get('body', {}).get('output', {}).get('low', 0),
                                'open_price': data.get('body', {}).get('output', {}).get('open', 0),
                                'volume': data.get('body', {}).get('output', {}).get('tvol', 0)
                            }
                            
                            if callable(callback):
                                callback(processed_data)
                                
                    except Exception as e:
                        Logger.error(f"❌ 해외주식 콜백 처리 에러: {e}")
                
                self.add_message_interceptor(overseas_interceptor)
            
            # 각 종목별로 구독 메시지 전송
            for symbol in symbols:
                subscribe_message = {
                    "header": {
                        "appkey": self.app_key,
                        "appsecret": self.app_secret,
                        "custtype": "P",
                        "tr_type": "1",  # 구독 등록
                        "content-type": "utf-8"
                    },
                    "body": {
                        "input": {
                            "tr_id": "HHDFS76240000",  # 해외주식 실시간 TR ID
                            "tr_key": f"RBAQ{symbol}"  # 한투증권 해외주식 실시간 포맷
                        }
                    }
                }
                
                success = await self.iocp_websocket.subscribe(subscribe_message)
                if not success:
                    Logger.error(f"❌ 해외주식 구독 실패: {exchange}^{symbol}")
                    return False
            
            Logger.info(f"✅ 해외주식 구독 완료: {exchange} - {symbols}")
            return True
            
        except Exception as e:
            Logger.error(f"❌ 해외주식 구독 예외: {e}")
            return False
    
    async def subscribe_market_index(self, indices: list, callback=None) -> bool:
        """시장 지수 구독 (기존 코드 호환성)"""
        try:
            Logger.info(f"📤 시장 지수 구독 요청: {indices}")
            
            # 콜백이 있으면 메시지 인터셉터로 등록
            if callback:
                async def index_interceptor(data):
                    try:
                        # 시장 지수 데이터인지 확인하고 콜백 호출
                        if 'header' in data and 'body' in data:
                            # 시장 지수 데이터 변환 로직
                            processed_data = {
                                'index_code': data.get('body', {}).get('output', {}).get('mksc_shrn_iscd', ''),
                                'current_value': data.get('body', {}).get('output', {}).get('bstp_nmix_prpr', 0),
                                'change_amount': data.get('body', {}).get('output', {}).get('prdy_vrss_sign', 0),
                                'change_rate': data.get('body', {}).get('output', {}).get('prdy_ctrt', 0)
                            }
                            
                            if callable(callback):
                                callback(processed_data)
                                
                    except Exception as e:
                        Logger.error(f"❌ 시장 지수 콜백 처리 에러: {e}")
                
                self.add_message_interceptor(index_interceptor)
            
            # 각 지수별로 구독 메시지 전송
            for index_code in indices:
                subscribe_message = {
                    "header": {
                        "appkey": self.app_key,
                        "appsecret": self.app_secret,
                        "custtype": "P",
                        "tr_type": "1",  # 구독 등록
                        "content-type": "utf-8"
                    },
                    "body": {
                        "input": {
                            "tr_id": "HDFSCNT1",  # 지수 실시간 TR ID
                            "tr_key": index_code
                        }
                    }
                }
                
                success = await self.iocp_websocket.subscribe(subscribe_message)
                if not success:
                    Logger.error(f"❌ 시장 지수 구독 실패: {index_code}")
                    return False
            
            Logger.info(f"✅ 시장 지수 구독 완료: {indices}")
            return True
            
        except Exception as e:
            Logger.error(f"❌ 시장 지수 구독 예외: {e}")
            return False
    
    async def send_message(self, message: Dict) -> bool:
        """메시지 전송"""
        return await self.iocp_websocket.send_message(message)
    
    async def disconnect(self):
        """연결 해제"""
        Logger.info("🚪 한국투자증권 WebSocket 연결 해제")
        await self.iocp_websocket.disconnect()
        await self.iocp_websocket.stop()
    
    def add_message_interceptor(self, interceptor: Callable[[Dict], None]):
        """메시지 인터셉터 추가"""
        self.iocp_websocket.add_message_interceptor(interceptor)
    
    def remove_message_interceptor(self, interceptor: Callable[[Dict], None]):
        """메시지 인터셉터 제거"""
        self.iocp_websocket.remove_message_interceptor(interceptor)
    
    def is_connected(self) -> bool:
        """연결 상태 확인"""
        return self.iocp_websocket.is_connected()
    
    def get_state(self) -> WebSocketState:
        """현재 상태 반환"""
        return self.iocp_websocket.get_state()
    
    async def wait_for_complete_shutdown(self, timeout: float = 5.0) -> bool:
        """완전 종료 대기 (이벤트 기반)"""
        return await self.iocp_websocket.wait_for_complete_shutdown(timeout)
    
    async def _get_approval_key(self) -> Optional[str]:
        """approval_key 조회 (ServiceContainer에서)"""
        try:
            from service.service_container import ServiceContainer
            cache_service = ServiceContainer.get_cache_service()
            
            async with cache_service.get_client() as client:
                approval_key = await client.get_string("korea_investment:approval_key")
                
            if approval_key:
                Logger.info("✅ approval_key Redis에서 로드 성공")
                return approval_key
            else:
                Logger.warn("⚠️ approval_key가 Redis에 없습니다")
                return None
                
        except Exception as e:
            Logger.error(f"❌ approval_key 조회 실패: {e}")
            return None
    
    async def _korea_message_interceptor(self, data: Dict[str, Any]) -> None:
        """한국투자증권 전용 메시지 인터셉터 (PINGPONG 처리 포함)"""
        try:
            # 모든 메시지 로깅 (디버깅용)
            Logger.debug(f"🔍 한투증권 인터셉터 수신 데이터: {data}")
            
            # PINGPONG 메시지 감지 - 다양한 형태 체크
            pingpong_detected = False
            
            if isinstance(data, dict):
                # 1. header의 tr_id가 PINGPONG인 경우
                header = data.get("header", {})
                if header.get("tr_id") == "PINGPONG":
                    Logger.warn("🏓 PINGPONG 메시지 감지 (header.tr_id) - REST API 폴백 모드로 전환")
                    pingpong_detected = True
                
                # 2. body의 rt_cd가 특정 값인 경우 (한투증권 PINGPONG 응답 코드)
                body = data.get("body", {})
                if body.get("rt_cd") == "9" and "PINGPONG" in str(body.get("msg1", "")):
                    Logger.warn("🏓 PINGPONG 메시지 감지 (body.msg1) - REST API 폴백 모드로 전환")
                    pingpong_detected = True
                
                # 3. 전체 딕셔너리를 문자열로 변환해서 체크
                if "PINGPONG" in str(data):
                    Logger.warn("🏓 PINGPONG 메시지 감지 (전체 데이터) - REST API 폴백 모드로 전환")
                    pingpong_detected = True
                    
            elif isinstance(data, str):
                # 4. 문자열 데이터에 PINGPONG 포함
                if "PINGPONG" in data:
                    Logger.warn("🏓 PINGPONG 메시지 감지 (RAW 문자열) - REST API 폴백 모드로 전환")
                    pingpong_detected = True
            
            # PINGPONG 감지 시 처리
            if pingpong_detected:
                self._use_rest_fallback = True
                
                # 연결 종료는 별도 태스크로 처리 (이벤트 루프 충돌 방지)
                asyncio.create_task(self._delayed_disconnect())
                
                # REST API 폴백 모드 알림
                Logger.info("🔄 WebSocket → REST API 폴백 모드 활성화")
                return
                
            # 정상 메시지 처리 로깅
            if isinstance(data, dict) and "header" in data:
                tr_id = data.get("header", {}).get("tr_id", "")
                if tr_id:
                    Logger.debug(f"📊 한투증권 메시지 수신: {tr_id}")
                    
        except Exception as e:
            Logger.error(f"❌ 한투증권 메시지 인터셉터 에러: {e}")
    
    def is_rest_fallback_mode(self) -> bool:
        """REST API 폴백 모드 여부 확인"""
        return self._use_rest_fallback
    
    def reset_fallback_mode(self) -> None:
        """폴백 모드 리셋 (WebSocket 재시도용)"""
        self._use_rest_fallback = False
        Logger.info("🔄 REST API 폴백 모드 해제")
    
    async def _delayed_disconnect(self):
        """지연된 연결 종료 및 REST API 폴링 시작"""
        try:
            await asyncio.sleep(0.1)  # 약간의 지연
            await self.disconnect()
            Logger.info("🔌 PINGPONG으로 인한 WebSocket 연결 종료 완료")
            
            # REST API 폴링 즉시 시작
            from service.signal.signal_monitoring_service import SignalMonitoringService
            if SignalMonitoringService._initialized and SignalMonitoringService._monitoring_symbols:
                Logger.info(f"🔄 REST API 폴링 즉시 시작 - {len(SignalMonitoringService._monitoring_symbols)}개 종목")
                for symbol in SignalMonitoringService._monitoring_symbols:
                    await SignalMonitoringService._start_rest_api_polling(symbol)
                Logger.info("✅ 모든 종목 REST API 폴링 전환 완료")
        except Exception as e:
            Logger.error(f"❌ 지연된 연결 종료 실패: {e}")
    
    # 기존 코드 호환성을 위한 속성들
    @property
    def websocket(self):
        """기존 코드 호환성"""
        return self.iocp_websocket.websocket
    
    @property
    def state(self):
        """기존 코드 호환성"""
        return self.iocp_websocket.get_state()
    
    async def health_check(self, app_key: str, app_secret: str) -> Dict[str, Any]:
        """헬스 체크 (기존 코드 호환성)"""
        try:
            Logger.info("🩺 IOCP WebSocket 헬스 체크 시작")
            
            # 연결 테스트
            connection_success = await self.connect(app_key, app_secret)
            
            if connection_success:
                # 간단한 구독/구독취소 테스트
                subscribe_success = await self.subscribe_stock("005930")
                await asyncio.sleep(1)
                unsubscribe_success = await self.unsubscribe_stock("005930")
                
                await self.disconnect()
                
                test_success = subscribe_success and unsubscribe_success
                
                return {
                    "healthy": test_success,
                    "test_result": "IOCP WebSocket 헬스 체크 완료" if test_success else "IOCP WebSocket 헬스 체크 실패",
                    "connection": connection_success,
                    "subscribe": subscribe_success,
                    "unsubscribe": unsubscribe_success
                }
            else:
                return {
                    "healthy": False,
                    "test_result": "IOCP WebSocket 연결 실패"
                }
                
        except Exception as e:
            Logger.error(f"❌ IOCP WebSocket 헬스 체크 예외: {e}")
            return {
                "healthy": False,
                "test_result": f"IOCP WebSocket 헬스 체크 예외: {str(e)}"
            }
    
    # 기존 메서드들 호환성
    async def graceful_close(self, code: int = 1000, reason: str = ""):
        """기존 코드 호환성 - graceful close"""
        Logger.info(f"🚪 Graceful close: {reason}")
        await self.disconnect()


# 기존 코드 호환성을 위한 전역 함수들
_global_websocket_instance: Optional[KoreaInvestmentWebSocketIOCP] = None


async def get_korea_investment_websocket() -> KoreaInvestmentWebSocketIOCP:
    """전역 WebSocket 인스턴스 반환 (기존 코드 호환성)"""
    global _global_websocket_instance
    
    if _global_websocket_instance is None:
        _global_websocket_instance = KoreaInvestmentWebSocketIOCP()
        Logger.info("🚀 전역 IOCP WebSocket 인스턴스 생성")
    
    return _global_websocket_instance


def reset_korea_investment_websocket():
    """전역 WebSocket 인스턴스 초기화 (테스트용)"""
    global _global_websocket_instance
    _global_websocket_instance = None