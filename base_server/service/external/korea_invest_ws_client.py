"""
한국투자증권 WebSocket 클라이언트
"""
import json
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional, AsyncGenerator
from service.core.logger import Logger


class KoreaInvestWebSocketClient:
    """한국투자증권 WebSocket 클라이언트"""
    
    def __init__(self, app_key: str, app_secret: str, mode: str = "prod"):
        self.app_key = app_key
        self.app_secret = app_secret
        self.mode = mode
        
        # WebSocket 연결 정보
        self.ws_url = "ws://ops.koreainvestment.com:31000"  # 프로덕션
        if mode == "test":
            self.ws_url = "ws://ops.koreainvestment.com:21000"  # 테스트
        
        self.session = None
        self.websocket = None
        self.access_token = None
        self.approval_key = None
        
        # 구독 정보
        self.subscribed_symbols = set()
        self.subscribed_indices = set()
        
        # 메시지 큐
        self.message_queue = asyncio.Queue()
        self.running = False
    
    async def connect(self) -> bool:
        """WebSocket 연결 및 인증"""
        try:
            Logger.info("🚀 ===== 한국투자증권 WebSocket 연결 시작 =====")
            Logger.info(f"🔧 연결 정보: app_key={self.app_key[:10]}..., mode={self.mode}")
            Logger.info(f"🔗 WebSocket URL: {self.ws_url}")
            
            # 1. OAuth 토큰 발급
            Logger.info("🔑 1단계: OAuth 토큰 발급 시작")
            if not await self._get_access_token():
                Logger.error("❌ OAuth 토큰 발급 실패")
                return False
            Logger.info("✅ 1단계: OAuth 토큰 발급 완료")
            
            # 2. Approval 키 발급 (REST API 사용)
            Logger.info("🔑 2단계: Approval 키 발급 시작")
            if not await self._get_approval_key():
                Logger.error("❌ Approval 키 발급 실패")
                return False
            Logger.info("✅ 2단계: Approval 키 발급 완료")
            
            # 3. WebSocket 연결
            Logger.info("🔗 3단계: WebSocket 연결 시작")
            Logger.info(f"🔗 연결 시도 URL: {self.ws_url}")
            self.session = aiohttp.ClientSession()
            try:
                Logger.info("🔗 aiohttp ClientSession 생성 완료")
                Logger.info("🔗 WebSocket 연결 시도 중...")
                
                # 헤더 구성
                headers = {
                    "authorization": f"Bearer {self.access_token}",
                    "approval_key": self.approval_key,
                    "appkey": self.app_key,
                    "appsecret": self.app_secret
                }
                
                Logger.info(f"🔗 연결 헤더: {headers}")
                self.websocket = await self.session.ws_connect(self.ws_url, headers=headers)
                Logger.info("✅ 3단계: WebSocket 연결 성공")
                Logger.info(f"🔗 WebSocket 객체: {self.websocket}")
                Logger.info(f"🔗 WebSocket 상태: {self.websocket.closed}")
            except Exception as ws_error:
                Logger.error(f"❌ 3단계: WebSocket 연결 실패")
                Logger.error(f"❌ 에러 타입: {type(ws_error)}")
                Logger.error(f"❌ 에러 내용: {ws_error}")
                return False
            
            Logger.info("🎉 ===== 한국투자증권 WebSocket 연결 성공 =====")
            return True
            
        except Exception as e:
            Logger.error(f"❌ 한국투자증권 WebSocket 연결 실패: {e}")
            Logger.error(f"❌ 에러 타입: {type(e)}")
            return False
    
    async def _get_access_token(self) -> bool:
        """OAuth 액세스 토큰 발급"""
        try:
            url = "https://openapi.koreainvestment.com:9443/oauth2/tokenP"
            headers = {
                'content-type': 'application/json; charset=utf-8'
            }
            data = {
                'grant_type': 'client_credentials',
                'appkey': self.app_key,
                'appsecret': self.app_secret
            }
            
            Logger.info(f"🔑 OAuth 토큰 발급 URL: {url}")
            Logger.info(f"🔑 App Key: {self.app_key[:10]}...{self.app_key[-10:] if len(self.app_key) > 20 else self.app_key}")
            Logger.info(f"🔑 App Secret: {self.app_secret[:10]}...{self.app_secret[-10:] if len(self.app_secret) > 20 else self.app_secret}")
            Logger.info(f"🔑 요청 데이터: {data}")
            Logger.info(f"🔑 요청 헤더: {headers}")
            
            Logger.info("🔑 OAuth 토큰 발급 요청 전송 중...")
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    Logger.info(f"🔑 OAuth 응답 상태: {response.status}")
                    Logger.info(f"🔑 응답 헤더: {dict(response.headers)}")
                    
                    if response.status == 200:
                        result = await response.json()
                        Logger.info(f"🔑 OAuth 응답 전체: {result}")
                        self.access_token = result.get('access_token')
                        Logger.info(f"✅ OAuth 토큰 발급 성공: {self.access_token[:10] if self.access_token else 'None'}...{self.access_token[-10:] if self.access_token and len(self.access_token) > 20 else ''}")
                        Logger.info(f"🔑 토큰 타입: {result.get('token_type')}")
                        Logger.info(f"🔑 만료 시간: {result.get('expires_in')}")
                        return True
                    else:
                        error_text = await response.text()
                        Logger.error(f"❌ OAuth 토큰 발급 실패: {response.status}")
                        Logger.error(f"❌ 에러 응답: {error_text}")
                        Logger.error(f"❌ 응답 헤더: {dict(response.headers)}")
                        return False
                        
        except Exception as e:
            Logger.error(f"❌ OAuth 토큰 발급 에러: {e}")
            Logger.error(f"❌ 에러 타입: {type(e)}")
            return False
    
    async def _get_approval_key(self) -> bool:
        """Approval 키 발급 (REST API 사용)"""
        try:
            url = "https://openapi.koreainvestment.com:9443/oauth2/Approval"
            headers = {
                "authorization": f"Bearer {self.access_token}",
                "appkey": self.app_key,
                "appsecret": self.app_secret,
                "content-type": "application/json"
            }
            data = {
                "grant_type": "client_credentials",
                "appkey": self.app_key,
                "secretkey": self.app_secret
            }
            
            Logger.info(f"🔑 Approval 키 발급 URL: {url}")
            Logger.info(f"🔑 요청 헤더: {headers}")
            Logger.info(f"🔑 요청 데이터: {data}")
            
            Logger.info("🔑 Approval 키 발급 요청 전송 중...")
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    Logger.info(f"🔑 Approval 키 응답 상태: {response.status}")
                    Logger.info(f"🔑 응답 헤더: {dict(response.headers)}")
                    
                    if response.status == 200:
                        result = await response.json()
                        Logger.info(f"🔑 Approval 키 응답 전체: {result}")
                        self.approval_key = result.get('approval_key')
                        Logger.info(f"✅ Approval 키 발급 성공: {self.approval_key[:10] if self.approval_key else 'None'}...{self.approval_key[-10:] if self.approval_key and len(self.approval_key) > 20 else ''}")
                        return True
                    else:
                        error_text = await response.text()
                        Logger.error(f"❌ Approval 키 발급 실패: {response.status}")
                        Logger.error(f"❌ 에러 응답: {error_text}")
                        Logger.error(f"❌ 응답 헤더: {dict(response.headers)}")
                        return False
                        
        except Exception as e:
            Logger.error(f"❌ Approval 키 발급 에러: {e}")
            Logger.error(f"❌ 에러 타입: {type(e)}")
            return False
    
    async def subscribe(self, symbols: List[str] = None, indices: List[str] = None) -> bool:
        """종목/지수 구독"""
        try:
            Logger.info("📡 ===== 구독 시작 =====")
            Logger.info(f"📡 구독 요청: symbols={symbols}, indices={indices}")
            
            if not self.websocket:
                Logger.error("❌ WebSocket이 연결되지 않음")
                return False
            
            symbols = symbols or []
            indices = indices or []
            
            Logger.info(f"📡 처리할 종목 수: {len(symbols)}")
            Logger.info(f"📡 처리할 지수 수: {len(indices)}")
            
            # 국내 주식 구독 (H0STCNT0)
            Logger.info("📡 국내 주식 구독 시작")
            for i, symbol in enumerate(symbols):
                if symbol not in self.subscribed_symbols:
                    Logger.info(f"📡 국내 주식 구독 #{i+1}: {symbol}")
                    
                    subscribe_request = {
                        "header": {
                            "approval_key": self.approval_key,
                            "custtype": "P",
                            "tr_type": "1",
                            "content-type": "utf-8"
                        },
                        "body": {
                            "input": {
                                "tr_id": "H0STCNT0",  # 국내 실시간 현재가
                                "tr_key": symbol
                            }
                        }
                    }
                    
                    Logger.info(f"📡 구독 요청 데이터: {subscribe_request}")
                    
                    try:
                        await self.websocket.send_str(json.dumps(subscribe_request))
                        Logger.info(f"✅ 국내 주식 구독 요청 전송 완료: {symbol}")
                        self.subscribed_symbols.add(symbol)
                        Logger.info(f"✅ 국내 주식 구독 등록 완료: {symbol}")
                    except Exception as send_error:
                        Logger.error(f"❌ 국내 주식 구독 요청 전송 실패: {symbol}, 에러: {send_error}")
                        return False
                    
                    await asyncio.sleep(0.1)  # Rate limit 방지
                else:
                    Logger.info(f"⚠️ 국내 주식 이미 구독 중: {symbol}")
            
            # 지수 구독 (H0STCNT0)
            Logger.info("📡 지수 구독 시작")
            for i, index in enumerate(indices):
                if index not in self.subscribed_indices:
                    Logger.info(f"📡 지수 구독 #{i+1}: {index}")
                    
                    subscribe_request = {
                        "header": {
                            "approval_key": self.approval_key,
                            "custtype": "P",
                            "tr_type": "1",
                            "content-type": "utf-8"
                        },
                        "body": {
                            "input": {
                                "tr_id": "H0STCNT0",  # 국내 실시간 현재가
                                "tr_key": index
                            }
                        }
                    }
                    
                    Logger.info(f"📡 구독 요청 데이터: {subscribe_request}")
                    
                    try:
                        await self.websocket.send_str(json.dumps(subscribe_request))
                        Logger.info(f"✅ 지수 구독 요청 전송 완료: {index}")
                        self.subscribed_indices.add(index)
                        Logger.info(f"✅ 지수 구독 등록 완료: {index}")
                    except Exception as send_error:
                        Logger.error(f"❌ 지수 구독 요청 전송 실패: {index}, 에러: {send_error}")
                        return False
                    
                    await asyncio.sleep(0.1)  # Rate limit 방지
                else:
                    Logger.info(f"⚠️ 지수 이미 구독 중: {index}")
            
            Logger.info(f"🎉 ===== 구독 완료 =====")
            Logger.info(f"📊 총 구독 종목: {len(self.subscribed_symbols)}")
            Logger.info(f"📊 총 구독 지수: {len(self.subscribed_indices)}")
            return True
            
        except Exception as e:
            Logger.error(f"❌ 구독 실패: {e}")
            Logger.error(f"❌ 에러 타입: {type(e)}")
            return False
    
    async def unsubscribe(self, targets: List[str]) -> bool:
        """구독 해제"""
        try:
            if not self.websocket:
                return False
            
            for target in targets:
                unsubscribe_request = {
                    "header": {
                        "approval_key": self.approval_key,
                        "custtype": "P",
                        "tr_type": "2",  # 해제
                        "content-type": "utf-8"
                    },
                    "body": {
                        "input": {
                            "tr_id": "H0STCNT0",
                            "tr_key": target
                        }
                    }
                }
                
                await self.websocket.send_str(json.dumps(unsubscribe_request))
                self.subscribed_symbols.discard(target)
                self.subscribed_indices.discard(target)
                Logger.info(f"구독 해제: {target}")
                await asyncio.sleep(0.1)
            
            return True
            
        except Exception as e:
            Logger.error(f"구독 해제 실패: {e}")
            return False
    
    async def iter_messages(self) -> AsyncGenerator[Dict[str, Any], None]:
        """메시지 스트림 생성기"""
        try:
            Logger.info("🔄 ===== 메시지 스트림 시작 =====")
            self.running = True
            message_count = 0
            
            Logger.info("🔄 메시지 수신 루프 시작")
            while self.running and self.websocket:
                try:
                    Logger.info(f"📨 메시지 #{message_count + 1} 수신 대기 중...")
                    
                    # 메시지 수신
                    ws_message = await self.websocket.receive()
                    message_count += 1
                    
                    Logger.info(f"📨 WebSocket 메시지 타입: {ws_message.type}")
                    Logger.info(f"📨 WebSocket 메시지 데이터: {ws_message.data}")
                    
                    # 메시지 타입에 따른 처리
                    if ws_message.type == aiohttp.WSMsgType.TEXT:
                        # 원본 문자열 로그
                        Logger.info(f"📨 원본 문자열 메시지 #{message_count}: '{ws_message.data}'")
                        Logger.info(f"📨 문자열 길이: {len(ws_message.data)}")
                        Logger.info(f"📨 문자열 타입: {type(ws_message.data)}")
                        
                        # 메시지 파싱 및 변환
                        Logger.info(f"🔍 메시지 #{message_count} 파싱 시작")
                        parsed_message = self._parse_message(ws_message.data)
                        
                        if parsed_message:
                            Logger.info(f"✅ 메시지 #{message_count} 파싱 성공: {parsed_message}")
                            yield parsed_message
                        else:
                            Logger.info(f"⚠️ 메시지 #{message_count} 파싱 실패 또는 무시: {ws_message.data}")
                            
                    elif ws_message.type == aiohttp.WSMsgType.BINARY:
                        Logger.info(f"📨 바이너리 메시지 #{message_count} 수신 (크기: {len(ws_message.data)} bytes)")
                        # 바이너리 메시지는 무시 (PINGPONG 등)
                        
                    elif ws_message.type == aiohttp.WSMsgType.CLOSED:
                        Logger.warn("🔄 WebSocket 연결이 닫힘")
                        break
                        
                    elif ws_message.type == aiohttp.WSMsgType.ERROR:
                        Logger.error(f"❌ WebSocket 에러: {ws_message.data}")
                        break
                        
                    else:
                        Logger.info(f"📨 기타 메시지 타입 #{message_count}: {ws_message.type}")
                        
                except asyncio.CancelledError:
                    Logger.info("🔄 메시지 수신 취소됨")
                    break
                except Exception as e:
                    Logger.error(f"❌ 메시지 #{message_count + 1} 수신 에러: {e}")
                    Logger.error(f"❌ 에러 타입: {type(e)}")
                    await asyncio.sleep(1)  # 에러 시 잠시 대기
                    
        except Exception as e:
            Logger.error(f"❌ 메시지 스트림 에러: {e}")
            Logger.error(f"❌ 에러 타입: {type(e)}")
        finally:
            Logger.info(f"🔄 ===== 메시지 스트림 종료 (총 {message_count}개 메시지 처리) =====")
            self.running = False
    
    def _parse_message(self, message: str) -> Optional[Dict[str, Any]]:
        """메시지 파싱 (파이프 형식)"""
        try:
            Logger.info(f"🔍 메시지 파싱 시작: {message}")
            
            # JSON 형식인지 확인
            try:
                json_data = json.loads(message)
                Logger.info(f"📨 JSON 메시지: {json_data}")
                
                # JSON 메시지 처리 (에러 메시지 등)
                if "header" in json_data:
                    header = json_data.get("header", {})
                    tr_id = header.get("tr_id")
                    
                    if tr_id == "PINGPONG":
                        Logger.info("📨 PINGPONG 메시지 수신")
                        return {
                            "type": "pingpong",
                            "datetime": header.get("datetime", "")
                        }
                    else:
                        Logger.info(f"📨 기타 JSON 메시지: tr_id={tr_id}")
                        return None
                else:
                    Logger.info(f"📨 일반 JSON 메시지: {json_data}")
                    return None
                    
            except json.JSONDecodeError:
                # 파이프 형식 메시지 처리
                Logger.info("📨 파이프 형식 메시지 처리")
                
                if "|" not in message:
                    Logger.warn(f"⚠️ 파이프 구분자 없음: {message}")
                    return None
                
                parts = message.split("|")
                Logger.info(f"📨 파이프 분할 결과: {parts}")
                
                if len(parts) < 4:
                    Logger.warn(f"⚠️ 파이프 분할 부족: {len(parts)} < 4")
                    return None
                
                tr_id = parts[1]
                payload = parts[3].split("^")
                Logger.info(f"📨 tr_id: {tr_id}, payload: {payload}")
                
                # 국내 주식 실시간 현재가 (H0STCNT0)
                if tr_id == "H0STCNT0" and len(payload) >= 6:
                    parsed_data = {
                        "type": "domestic_stock",
                        "symbol": payload[0],
                        "time": payload[1],
                        "current_price": float(payload[2]) if payload[2] else 0,
                        "change_amount": float(payload[4]) if payload[4] else 0,
                        "change_rate": float(payload[5]) if payload[5] else 0,
                        "volume": int(payload[6]) if len(payload) > 6 and payload[6] else 0,
                        "raw_data": payload
                    }
                    
                    Logger.info(f"✅ 국내 주식 메시지 파싱 성공: {parsed_data}")
                    return parsed_data
                
                # 기타 메시지 타입
                Logger.info(f"📨 기타 메시지 타입: tr_id={tr_id}")
                return None
                
        except Exception as e:
            Logger.error(f"❌ 메시지 파싱 에러: {e}, 원본 메시지: {message}")
            return None
    
    async def disconnect(self):
        """연결 해제"""
        try:
            self.running = False
            
            if self.websocket:
                await self.websocket.close()
                self.websocket = None
            
            if self.session:
                await self.session.close()
                self.session = None
            
            Logger.info("한국투자증권 WebSocket 연결 해제")
            
        except Exception as e:
            Logger.error(f"연결 해제 에러: {e}")
    
    def is_connected(self) -> bool:
        """연결 상태 확인"""
        return self.websocket is not None and not self.websocket.closed 