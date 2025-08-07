import asyncio
import json
import websockets
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from service.core.logger import Logger

class KoreaInvestmentWebSocket:
    """한국투자증권 웹소켓 API 서비스
    
    한투 WebSocket API 인증 방식:
    1. REST API에서 OAuth2 access_token을 미리 발급받아야 함
    2. WebSocket 연결 시에는 appkey만 사용 (access_token은 메시지에 포함하지 않음)
    3. 서버에서 해당 appkey가 인증된 세션인지 확인 후 허용
    """
    
    def __init__(self):
        # WebSocket 연결 정보
        self.ws_url = "ws://ops.koreainvestment.com:31000"  # 한투 실시간 웹소켓 URL
        self.websocket = None
        self.is_connected = False
        
        # 콜백 및 인증 정보
        self.callbacks = {}  # tr_id별 콜백 함수 저장
        self.approval_key = None  # 실제로는 appkey를 저장
        self.app_secret = None    # appsecret 저장 (WebSocket 메시지에 필요)
        
        # 재연결 및 구독 상태 관리
        self.subscriptions = {}   # 활성 구독 상태 저장 {tr_key: subscription_data}
        self.max_reconnect_attempts = 10  # 최대 재연결 시도 횟수
        self.reconnect_delay = 5  # 재연결 대기 시간 (초)
        self.last_heartbeat = None  # 마지막 하트비트 시간
        self.connection_start_time = None  # 연결 시작 시간
        self.heartbeat_timeout = 30  # 하트비트 타임아웃 (30초)
        
        # 중복 태스크 방지를 위한 플래그
        self._message_loop_task = None  # 현재 실행 중인 _message_loop 태스크
        
    async def connect(self, app_key: str, app_secret: str) -> bool:
        """한투 웹소켓 연결 (OAuth2 방식 - appkey 기반 인증)
        
        Args:
            app_key: 한투에서 발급받은 앱 키
            app_secret: 한투에서 발급받은 앱 시크릿 (WebSocket에서는 직접 사용 안함)
            
        Returns:
            bool: 연결 성공 여부
            
        Note:
            - REST API에서 OAuth2 access_token을 미리 발급받아야 WebSocket 사용 가능
            - WebSocket 메시지에는 appkey만 포함 (access_token은 포함하지 않음)
            - 서버에서 해당 appkey의 인증 상태를 확인하여 허용/거부 결정
        """
        try:
            Logger.info("한국투자증권 웹소켓 연결 시도 (appkey 기반 인증)")
            
            # 1. OAuth2 인증 상태 확인 (ServiceContainer를 통해)
            self._check_oauth2_authentication(app_key)
            
            # 2. 웹소켓 연결 수행
            self.websocket = await websockets.connect(self.ws_url)
            self.is_connected = True
            self.approval_key = app_key  # WebSocket에서는 appkey 사용
            self.app_secret = app_secret  # appsecret 저장 (메시지 헤더에 필요)
            self.connection_start_time = datetime.now()  # 연결 시작 시간 기록
            
            Logger.info(f"WebSocket 연결 성공, appkey: {app_key[:10]}...")
            
            # 3. 초기 연결 완료 (한투 WebSocket - 연결만으로 인증 완료)
            # 별도의 초기 인증 메시지 불필요 - 구독 메시지에서 인증 진행
            Logger.info("한국투자증권 웹소켓 연결 완료 - 구독 요청 시 appkey/appsecret 인증")
            
            # 4. 테스트용 구독/구독취소 실행
            asyncio.create_task(self._test_subscription())
            
            # 5. 메시지 수신 루프 시작 (중복 실행 방지)
            if self._message_loop_task is None or self._message_loop_task.done():
                self._message_loop_task = asyncio.create_task(self._message_loop())
                Logger.info("새로운 메시지 루프 태스크 시작")
            else:
                Logger.info("메시지 루프 태스크 이미 실행 중 - 중복 생성 방지")
            
            return True
            
        except Exception as e:
            Logger.error(f"한국투자증권 웹소켓 연결 실패: {e}")
            self.is_connected = False
            return False
    
    async def _test_subscription(self) -> None:
        """테스트용 구독/구독취소 로직
        
        Note:
            삼성전자(005930)를 구독 후 3초 뒤 구독 취소하여 WebSocket 기능 테스트
        """
        try:
            # 1초 대기 후 구독 시작
            await asyncio.sleep(1)
            
            test_symbol = "005930"  # 삼성전자
            
            # 구독 메시지 전송 (한투 표준 형식 - 인증 정보 포함)
            subscribe_message = {
                "header": {
                    "appkey": self.approval_key,     # appkey 필수
                    "appsecret": self.app_secret,    # appsecret 필수
                    "custtype": "P",                 # 개인 고객
                    "tr_type": "1",                  # 등록 요청
                    "content-type": "utf-8"
                },
                "body": {
                    "input": {
                        "tr_id": "HDFSCNT0",         # 한투 표준 주식 실시간 TR ID
                        "tr_key": test_symbol        # 삼성전자 종목코드
                    }
                }
            }
            
            await self.websocket.send(json.dumps(subscribe_message))
            Logger.info(f"🔔 테스트 구독 시작: {test_symbol} (삼성전자)")
            
            # 3초 대기
            await asyncio.sleep(3)
            
            # 구독 취소 메시지 전송 (tr_type을 2로 변경)
            unsubscribe_message = {
                "header": {
                    "appkey": self.approval_key,     # appkey 필수
                    "appsecret": self.app_secret,    # appsecret 필수
                    "custtype": "P",                 # 개인 고객
                    "tr_type": "2",                  # 구독 취소
                    "content-type": "utf-8"
                },
                "body": {
                    "input": {
                        "tr_id": "HDFSCNT0",         # 동일한 TR ID
                        "tr_key": test_symbol        # 동일한 종목코드
                    }
                }
            }
            
            await self.websocket.send(json.dumps(unsubscribe_message))
            Logger.info(f"🔕 테스트 구독 취소: {test_symbol} (삼성전자)")
            
        except Exception as e:
            Logger.error(f"❌ 테스트 구독/구독취소 실패: {e}")
    
    def _check_oauth2_authentication(self, app_key: str) -> None:
        """OAuth2 인증 상태 확인 및 로깅
        
        Args:
            app_key: 확인할 앱 키
            
        Note:
            실제 OAuth2 토큰 검증보다는 상태 확인 및 로깅 목적
            WebSocket은 appkey만 사용하므로 별도 토큰 검증 불필요
        """
        try:
            from service.service_container import ServiceContainer
            
            # ServiceContainer에서 한투 서비스 상태 확인
            if ServiceContainer.is_korea_investment_service_initialized():
                korea_service = ServiceContainer.get_korea_investment_service()
                if korea_service and korea_service.is_initialized():
                    Logger.info("✅ OAuth2 인증 완료 - WebSocket appkey 사용 가능")
                else:
                    Logger.warn("⚠️ 한투 서비스 초기화되지 않음 - WebSocket 연결 시도")
            else:
                Logger.info("🔄 초기화 단계: ServiceContainer 등록 전 - WebSocket 직접 연결 (정상)")
                
        except Exception as e:
            Logger.warn(f"⚠️ OAuth2 상태 확인 실패, WebSocket 직접 연결 시도: {e}")
    
    async def _reconnect_only(self, app_key: str, app_secret: str) -> bool:
        """재연결 전용 메서드 - 메시지 루프 태스크는 생성하지 않음"""
        try:
            Logger.info("한국투자증권 웹소켓 재연결 시도 (메시지 루프 태스크 재생성 안함)")
            
            # OAuth2 인증 상태 확인
            self._check_oauth2_authentication(app_key)
            
            # 웹소켓 연결 수행
            self.websocket = await websockets.connect(self.ws_url)
            self.is_connected = True
            self.approval_key = app_key
            self.app_secret = app_secret
            self.connection_start_time = datetime.now()
            
            Logger.info(f"WebSocket 재연결 성공, appkey: {app_key[:10]}...")
            Logger.info("한국투자증권 웹소켓 재연결 완료 - 기존 메시지 루프 계속 사용")
            
            return True
            
        except Exception as e:
            Logger.error(f"한국투자증권 웹소켓 재연결 실패: {e}")
            self.is_connected = False
            return False
    
    async def _message_loop(self):
        """웹소켓 메시지 수신 루프 (재연결 포함)"""
        reconnect_attempts = 0
        
        while self.is_connected:
            try:
                # 하트비트 타임아웃 체크
                if (self.last_heartbeat and 
                    (datetime.now() - self.last_heartbeat).total_seconds() > self.heartbeat_timeout):
                    Logger.warn("하트비트 타임아웃 - 재연결 필요")
                    await self._cleanup_existing_connection()
                
                if not self.websocket or not self._is_websocket_open():
                    # 재연결 시도
                    if reconnect_attempts >= self.max_reconnect_attempts:
                        Logger.error(f"최대 재연결 시도 횟수 초과: {self.max_reconnect_attempts}")
                        self.is_connected = False
                        break
                    
                    Logger.warn(f"WebSocket 재연결 시도 {reconnect_attempts + 1}/{self.max_reconnect_attempts}")
                    await asyncio.sleep(self.reconnect_delay)
                    
                    # 기존 연결 정리 후 재연결 (메시지 루프 태스크는 재생성하지 않음)
                    await self._cleanup_existing_connection()
                    connection_success = await self._reconnect_only(self.approval_key, self.app_secret)
                    
                    if not connection_success:
                        reconnect_attempts += 1
                        continue
                    
                    # 구독 상태 복원
                    await self._restore_subscriptions()
                    reconnect_attempts = 0
                    Logger.info("WebSocket 재연결 및 구독 복원 완료")
                
                # TCP 특성상 recv()는 한 번에 하나만 호출 가능 - timeout으로 안전하게 처리
                try:
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=10.0)
                    self.last_heartbeat = datetime.now()
                    await self._handle_message(message)
                    reconnect_attempts = 0  # 성공 시 재연결 카운터 리셋
                    
                except asyncio.TimeoutError:
                    # 타임아웃은 정상 - 메시지가 없을 뿐, 연결 상태만 확인
                    if not self._is_websocket_open():
                        Logger.warn("WebSocket 연결 끊어짐 감지 (timeout)")
                        await self._cleanup_existing_connection()
                        continue
                    continue  # 연결 정상이면 다음 루프
                    
                except Exception as recv_error:
                    # recv() 실제 에러 - 연결 문제이므로 정리 후 재연결
                    Logger.error(f"웹소켓 메시지 수신 에러: {recv_error}")
                    await self._cleanup_existing_connection()
                    raise recv_error  # 재연결 로직으로 전달
                
            except Exception as e:
                Logger.error(f"웹소켓 메시지 루프 에러: {e}")
                # 기존 recv() 코루틴 완전 정리 - TCP 동시성 충돌 방지
                await self._cleanup_existing_connection()
                reconnect_attempts += 1
                if reconnect_attempts >= self.max_reconnect_attempts:
                    Logger.error("재연결 한계 도달 - 연결 종료")
                    self.is_connected = False
                    break
                await asyncio.sleep(self.reconnect_delay)  # 재연결 대기
    
    async def _handle_message(self, message: str):
        """메시지 처리"""
        try:
            data = json.loads(message)
            Logger.info(f"웹소켓 메시지 수신: {data}")
            
            # 한국투자증권 API 응답 처리
            if 'header' in data and 'tr_id' in data['header']:
                tr_id = data['header']['tr_id']
                
                # 지수 및 해외주식 데이터 처리
                if tr_id.startswith('H0_'):
                    if 'OVFUTURE' in tr_id:
                        # 해외주식 데이터 처리
                        await self._process_overseas_stock_data(data)
                    else:
                        # 국내 지수 데이터 처리
                        await self._process_market_index_data(data)
                # 국내 주식 데이터 처리
                elif tr_id.startswith('H1_'):
                    await self._process_stock_data(data)
                # 기타 콜백 함수 호출
                elif tr_id in self.callbacks:
                    await self.callbacks[tr_id](data)
                    
        except Exception as e:
            Logger.error(f"메시지 처리 에러: {e}")
    
    async def _process_market_index_data(self, data: dict):
        """지수 데이터 처리"""
        try:
            if 'body' in data and 'output' in data['body']:
                output = data['body']['output']
                tr_key = data['header'].get('tr_key', '')
                
                # 지수 코드에 따른 매핑
                index_mapping = {
                    '0001': 'kospi',
                    '1001': 'kosdaq'
                }
                
                index_name = index_mapping.get(tr_key)
                if index_name:
                    processed_data = {
                        'index_code': tr_key,
                        'index_name': index_name,
                        'current_price': float(output.get('stck_prpr', 0)),
                        'change_amount': float(output.get('prdy_vrss', 0)),
                        'change_rate': float(output.get('prdy_ctrt', 0)),
                        'volume': int(output.get('acml_vol', 0)),
                        'high_price': float(output.get('stck_hgpr', 0)),
                        'low_price': float(output.get('stck_lwpr', 0)),
                        'open_price': float(output.get('stck_oprc', 0))
                    }
                    
                    Logger.info(f"지수 데이터 처리 완료: {index_name} - {processed_data}")
                    
                    # 콜백 함수 호출
                    callback_key = f"H0_{tr_key}"
                    if callback_key in self.callbacks:
                        await self.callbacks[callback_key](processed_data)
                        
        except Exception as e:
            Logger.error(f"지수 데이터 처리 에러: {e}")
    
    async def _process_stock_data(self, data: dict):
        """주식 데이터 처리"""
        try:
            if 'body' in data and 'output' in data['body']:
                output = data['body']['output']
                tr_key = data['header'].get('tr_key', '')
                
                processed_data = {
                    'symbol': tr_key,
                    'current_price': float(output.get('stck_prpr', 0)),
                    'change_amount': float(output.get('prdy_vrss', 0)),
                    'change_rate': float(output.get('prdy_ctrt', 0)),
                    'volume': int(output.get('acml_vol', 0)),
                    'high_price': float(output.get('stck_hgpr', 0)),
                    'low_price': float(output.get('stck_lwpr', 0)),
                    'open_price': float(output.get('stck_oprc', 0)),
                    'market_cap': int(output.get('hts_avls', 0)),
                    'trade_value': int(output.get('acml_tr_pbmn', 0))
                }
                
                Logger.info(f"주식 데이터 처리 완료: {tr_key} - {processed_data}")
                
                # 콜백 함수 호출
                callback_key = f"H1_{tr_key}"
                if callback_key in self.callbacks:
                    await self.callbacks[callback_key](processed_data)
                    
        except Exception as e:
            Logger.error(f"주식 데이터 처리 에러: {e}")
    
    async def _process_overseas_stock_data(self, data: dict):
        """해외주식 데이터 처리"""
        try:
            if 'body' in data and 'output' in data['body']:
                output = data['body']['output']
                tr_key = data['header'].get('tr_key', '')
                
                # tr_key에서 거래소와 종목 분리 (예: "NASD^AAPL")
                if '^' in tr_key:
                    exchange, symbol = tr_key.split('^', 1)
                else:
                    exchange = 'UNKNOWN'
                    symbol = tr_key
                
                processed_data = {
                    'exchange': exchange,
                    'symbol': symbol,
                    'current_price': float(output.get('last', 0)),
                    'change_amount': float(output.get('diff', 0)),
                    'change_rate': float(output.get('rate', 0)),
                    'volume': int(output.get('tvol', 0)),
                    'high_price': float(output.get('high', 0)),
                    'low_price': float(output.get('low', 0)),
                    'open_price': float(output.get('open', 0)),
                    'timestamp': output.get('date', ''),
                    'currency': output.get('curr', 'USD')
                }
                
                Logger.info(f"해외주식 데이터 처리 완료: {exchange}^{symbol} - {processed_data}")
                
                # 콜백 함수 호출
                callback_key = f"H0_{tr_key}"
                if callback_key in self.callbacks:
                    await self.callbacks[callback_key](processed_data)
                    
        except Exception as e:
            Logger.error(f"해외주식 데이터 처리 에러: {e}")
    
    async def subscribe_stock_price(self, symbols: List[str], callback: Callable) -> bool:
        """국내 주식 실시간 가격 구독
        
        Args:
            symbols: 구독할 종목 코드 리스트 (예: ['005930', '000660'])
            callback: 데이터 수신 시 호출할 콜백 함수
            
        Returns:
            bool: 구독 요청 성공 여부
            
        Note:
            - tr_id: "H1_" (국내 주식 실시간 데이터)
            - 각 종목별로 개별 구독 메시지 전송
            - 콜백은 "H1_{symbol}" 키로 등록
        """
        if not self.is_connected:
            Logger.error("웹소켓이 연결되지 않음 - 구독 불가")
            return False
            
        try:
            for symbol in symbols:
                # 국내 주식 실시간 구독 메시지 (한투 표준 형식)
                subscribe_message = {
                    "header": {
                        "appkey": self.approval_key,     # appkey 사용
                        "appsecret": self.app_secret,    # appsecret 필수
                        "custtype": "P",                 # 개인 고객
                        "tr_type": "1",                  # 등록 요청
                        "content-type": "utf-8"
                    },
                    "body": {
                        "input": {
                            "tr_id": "H1_",               # 국내 주식 실시간 TR ID
                            "tr_key": symbol              # 종목 코드 (6자리)
                        }
                    }
                }
                
                # 구독 메시지 전송
                await self.websocket.send(json.dumps(subscribe_message))
                
                # 콜백 함수 등록 ("H1_{종목코드}" 형식)
                callback_key = f"H1_{symbol}"
                self.callbacks[callback_key] = callback
                
                # 구독 상태 저장 (재연결 시 복원용)
                self.subscriptions[symbol] = {
                    "type": "stock",
                    "tr_id": "H1_",
                    "tr_key": symbol,
                    "callback": callback
                }
                
                Logger.info(f"✅ 국내 주식 실시간 구독 등록: {symbol} -> {callback_key}")
                
            return True
            
        except Exception as e:
            Logger.error(f"❌ 주식 구독 실패: {e}")
            return False
    
    async def subscribe_market_index(self, indices: List[str], callback: Callable) -> bool:
        """시장 지수 실시간 구독
        
        Args:
            indices: 구독할 지수 코드 리스트 (예: ['0001', '1001'] - KOSPI, KOSDAQ)
            callback: 데이터 수신 시 호출할 콜백 함수
            
        Returns:
            bool: 구독 요청 성공 여부
            
        Note:
            - tr_id: "H0_CNT0" (시장 지수 실시간 데이터)
            - 지수 코드: 0001(KOSPI), 1001(KOSDAQ)
            - 콜백은 "H0_{지수코드}" 키로 등록
        """
        if not self.is_connected:
            Logger.error("웹소켓이 연결되지 않음 - 지수 구독 불가")
            return False
            
        try:
            for index in indices:
                # 시장 지수 실시간 구독 메시지
                subscribe_message = {
                    "header": {
                        "appkey": self.approval_key,     # appkey 사용
                        "appsecret": self.app_secret,    # appsecret 필수
                        "custtype": "P",                 # 개인 고객
                        "tr_type": "1",                  # 등록 요청
                        "content-type": "utf-8"
                    },
                    "body": {
                        "input": {
                            "tr_id": "H0_CNT0",            # 지수 실시간 TR ID
                            "tr_key": index               # 지수 코드 (0001, 1001 등)
                        }
                    }
                }
                
                # 구독 메시지 전송
                await self.websocket.send(json.dumps(subscribe_message))
                
                # 콜백 함수 등록 ("H0_{지수코드}" 형식)
                callback_key = f"H0_{index}"
                self.callbacks[callback_key] = callback
                
                # 구독 상태 저장 (재연결 시 복원용)
                self.subscriptions[index] = {
                    "type": "index",
                    "tr_id": "H0_CNT0",
                    "tr_key": index,
                    "callback": callback
                }
                
                # 지수명 매핑 (로그용)
                index_name = {'0001': 'KOSPI', '1001': 'KOSDAQ'}.get(index, index)
                Logger.info(f"✅ 시장 지수 실시간 구독 등록: {index}({index_name}) -> {callback_key}")
                
            return True
            
        except Exception as e:
            Logger.error(f"❌ 지수 구독 실패: {e}")
            return False
    
    async def subscribe_overseas_stock_price(self, exchange: str, symbols: List[str], callback: Callable) -> bool:
        """해외주식 실시간 가격 구독
        
        Args:
            exchange: 거래소 코드 (NASD=나스닥, NYSE=뉴욕, AMEX=아멕스, TSE=도쿄, etc)
            symbols: 종목 심볼 리스트 (AAPL, TSLA, MSFT, etc)
            callback: 데이터 수신 시 호출할 콜백 함수
            
        Returns:
            bool: 구독 요청 성공 여부
            
        Note:
            - tr_id: "H0_OVFUTURE0" (해외주식 실시간 데이터)
            - tr_key 형식: "{거래소}^{심볼}" (예: "NASD^AAPL")
            - 콜백은 "H0_{거래소}^{심볼}" 키로 등록
        """
        if not self.is_connected:
            Logger.error("웹소켓이 연결되지 않음 - 해외주식 구독 불가")
            return False
            
        try:
            for symbol in symbols:
                # 해외주식 실시간 구독 메시지
                subscribe_message = {
                    "header": {
                        "appkey": self.approval_key,     # appkey 사용
                        "appsecret": self.app_secret,    # appsecret 필수
                        "custtype": "P",                 # 개인 고객
                        "tr_type": "1",                  # 등록 요청
                        "content-type": "utf-8"
                    },
                    "body": {
                        "input": {
                            "tr_id": "H0_OVFUTURE0",      # 해외주식 실시간 TR ID
                            "tr_key": f"{exchange}^{symbol}"  # 거래소^종목심볼 형식
                        }
                    }
                }
                
                # 구독 메시지 전송
                await self.websocket.send(json.dumps(subscribe_message))
                
                # 콜백 함수 등록 ("H0_{거래소}^{심볼}" 형식)
                callback_key = f"H0_{exchange}^{symbol}"
                self.callbacks[callback_key] = callback
                
                # 구독 상태 저장 (재연결 시 복원용)
                overseas_key = f"{exchange}^{symbol}"
                self.subscriptions[overseas_key] = {
                    "type": "overseas",
                    "tr_id": "H0_OVFUTURE0",
                    "tr_key": overseas_key,
                    "callback": callback
                }
                
                Logger.info(f"✅ 해외주식 실시간 구독 등록: {exchange}^{symbol} -> {callback_key}")
                
            return True
            
        except Exception as e:
            Logger.error(f"❌ 해외주식 구독 실패: {e}")
            return False
    
    def _is_websocket_open(self) -> bool:
        """WebSocket 연결 상태 확인 (버전 호환성 처리)"""
        if not self.websocket:
            return False
        
        try:
            # websockets 라이브러리 버전에 따른 호환성 처리
            if hasattr(self.websocket, 'closed'):
                return not self.websocket.closed
            elif hasattr(self.websocket, 'close_code'):
                return self.websocket.close_code is None
            elif hasattr(self.websocket, 'state'):
                # websockets 10.0+ 버전
                from websockets.protocol import State
                return self.websocket.state == State.OPEN
            else:
                # 다른 속성들로 확인
                return getattr(self.websocket, 'open', True)
        except Exception as e:
            Logger.warn(f"WebSocket 상태 확인 실패: {e}")
            return False

    async def disconnect(self):
        """웹소켓 연결 해제"""
        self.is_connected = False
        
        # 메시지 루프 태스크 정리
        if self._message_loop_task and not self._message_loop_task.done():
            self._message_loop_task.cancel()
            try:
                await self._message_loop_task
            except asyncio.CancelledError:
                pass
            Logger.info("메시지 루프 태스크 종료")
        
        # WebSocket 연결 해제
        if self.websocket:
            await self.websocket.close()
            Logger.info("한국투자증권 웹소켓 연결 해제")
    
    async def health_check(self, app_key: str, app_secret: str) -> Dict[str, Any]:
        """WebSocket 연결 상태 확인 (서버 초기화용)
        
        Args:
            app_key: 한투 앱 키
            app_secret: 한투 앱 시크릿
            
        Returns:
            Dict[str, Any]: 상태 확인 결과
            
        Raises:
            RuntimeError: 최대 재시도 후에도 연결 실패 시
            
        Note:
            - 최대 5회 재시도 (각 시도마다 2초 대기)
            - 연결 성공 후 1초 대기하여 안정성 확인
            - 실패 시 RuntimeError 발생으로 서버 초기화 중단
        """
        max_retries = 5
        retry_delay = 2  # 2초 대기
        
        for attempt in range(1, max_retries + 1):
            try:
                Logger.info(f"🔍 WebSocket health_check 시도 {attempt}/{max_retries}")
                
                # 1. 기존 연결 상태 확인
                if self.is_connected and self.websocket and self._is_websocket_open():
                    Logger.info("✅ WebSocket 이미 연결됨 - health_check 성공")
                    return {
                        "healthy": True,
                        "status": "websocket_already_connected",
                        "test_result": f"WebSocket 이미 정상 연결됨 (시도 {attempt})",
                        "websocket_url": self.ws_url
                    }
                
                # 2. 기존 연결 정리 (끊어진 연결이 있다면)
                await self._cleanup_existing_connection()
                
                # 3. 새로운 연결 시도
                Logger.info(f"🔄 WebSocket 새 연결 시도 {attempt}/{max_retries}")
                connection_success = await self.connect(app_key, app_secret)
                
                # 4. 연결 성공 확인 및 안정성 테스트
                if connection_success and self.is_connected and self.websocket and self._is_websocket_open():
                    # 연결 후 잠시 대기하여 서버 응답 확인
                    Logger.info(f"⏳ WebSocket 연결 성공, 안정성 확인 중... (시도 {attempt}/{max_retries})")
                    await asyncio.sleep(1)  # 1초 대기
                    
                    # 여전히 연결되어 있으면 성공
                    if self.is_connected and self.websocket and self._is_websocket_open():
                        Logger.info(f"✅ WebSocket 연결 및 안정성 확인 완료! (시도 {attempt}/{max_retries})")
                        return {
                            "healthy": True,
                            "status": "websocket_connected_and_stable",
                            "test_result": f"WebSocket 연결 및 안정성 확인 완료 (시도 {attempt}회)",
                            "websocket_url": self.ws_url
                        }
                    else:
                        Logger.warn(f"⚠️ WebSocket 연결 후 불안정 - 재시도 (시도 {attempt}/{max_retries})")
                        continue
                
                # 5. 연결 실패 시 재시도 또는 최종 실패
                if attempt < max_retries:
                    Logger.warn(f"⚠️ WebSocket 연결 실패 - {retry_delay}초 후 재시도 ({attempt}/{max_retries})")
                    await asyncio.sleep(retry_delay)
                else:
                    Logger.error(f"❌ WebSocket 연결 {max_retries}회 모두 실패 - 서버 시작 중단!")
                    raise RuntimeError(f"WebSocket 연결 {max_retries}회 시도 후 모두 실패")
                    
            except Exception as e:
                if attempt < max_retries:
                    Logger.warn(f"⚠️ WebSocket health_check 예외 발생 - {retry_delay}초 후 재시도 ({attempt}/{max_retries}): {e}")
                    await asyncio.sleep(retry_delay)
                else:
                    Logger.error(f"❌ WebSocket health_check {max_retries}회 모두 실패 - 서버 시작 중단: {e}")
                    raise RuntimeError(f"WebSocket health_check 최종 실패: {e}")
        
        # 여기에 도달하면 안됨 (안전장치)
        raise RuntimeError("WebSocket health_check 예상치 못한 종료")
    
    async def _cleanup_existing_connection(self) -> None:
        """기존 WebSocket 연결 정리
        
        Note:
            끊어진 연결이나 불안정한 연결을 안전하게 정리
        """
        if self.websocket:
            try:
                await self.websocket.close()
                Logger.info("기존 WebSocket 연결 정리 완료")
            except Exception as e:
                Logger.warn(f"기존 WebSocket 연결 정리 중 예외 (무시): {e}")
            finally:
                self.websocket = None
                self.is_connected = False
    
    async def _restore_subscriptions(self) -> None:
        """재연결 후 구독 상태 복원"""
        if not self.subscriptions:
            Logger.info("복원할 구독 없음")
            return
        
        Logger.info(f"구독 상태 복원 시작: {len(self.subscriptions)}개 항목")
        
        try:
            for key, subscription in self.subscriptions.items():
                # 구독 메시지 재생성
                subscribe_message = {
                    "header": {
                        "appkey": self.approval_key,
                        "appsecret": self.app_secret,
                        "custtype": "P",
                        "tr_type": "1",
                        "content-type": "utf-8"
                    },
                    "body": {
                        "input": {
                            "tr_id": subscription["tr_id"],
                            "tr_key": subscription["tr_key"]
                        }
                    }
                }
                
                # 구독 재전송
                await self.websocket.send(json.dumps(subscribe_message))
                
                # 콜백 복원
                if subscription["type"] == "stock":
                    callback_key = f"H1_{key}"
                elif subscription["type"] == "index":
                    callback_key = f"H0_{key}"
                else:  # overseas
                    callback_key = f"H0_{key}"
                
                self.callbacks[callback_key] = subscription["callback"]
                Logger.info(f"구독 복원: {subscription['type']} - {key}")
                
                # 구독 간 짧은 지연
                await asyncio.sleep(0.1)
                
        except Exception as e:
            Logger.error(f"구독 상태 복원 실패: {e}")

# 싱글톤 인스턴스
_korea_investment_websocket = None

async def get_korea_investment_websocket() -> KoreaInvestmentWebSocket:
    """한국투자증권 웹소켓 서비스 인스턴스 반환"""
    global _korea_investment_websocket
    if _korea_investment_websocket is None:
        _korea_investment_websocket = KoreaInvestmentWebSocket()
    return _korea_investment_websocket 