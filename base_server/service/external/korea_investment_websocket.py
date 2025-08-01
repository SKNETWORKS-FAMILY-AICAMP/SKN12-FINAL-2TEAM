import asyncio
import json
import websockets
from typing import Dict, List, Optional, Callable, Any
from service.core.logger import Logger

class KoreaInvestmentWebSocket:
    """한국투자증권 웹소켓 API 서비스"""
    
    def __init__(self):
        self.ws_url = "ws://ops.koreainvestment.com:31000"  # 실시간 웹소켓 URL
        self.websocket = None
        self.is_connected = False
        self.callbacks = {}
        self.approval_key = None
        
    async def connect(self, app_key: str, app_secret: str) -> bool:
        """웹소켓 연결"""
        try:
            Logger.info("한국투자증권 웹소켓 연결 시도")
            
            # 웹소켓 연결
            self.websocket = await websockets.connect(self.ws_url)
            self.is_connected = True
            
            # approval key 생성 (실제로는 한국투자증권에서 발급받아야 함)
            # 임시로 app_key를 approval_key로 사용하되, 실제로는 별도 발급 필요
            self.approval_key = app_key
            
            # 한국투자증권 웹소켓 API는 approval_key가 필요하지만,
            # 현재는 app_key로 대체하여 테스트
            Logger.info(f"Approval key 설정: {self.approval_key[:10]}...")
            
            # 인증 메시지 전송
            auth_message = {
                "header": {
                    "approval_key": self.approval_key,
                    "custtype": "P",
                    "tr_type": "1",
                    "content-type": "utf-8"
                },
                "body": {
                    "input": {
                        "tr_id": "H0_CNT0",
                        "tr_key": ""
                    }
                }
            }
            
            await self.websocket.send(json.dumps(auth_message))
            Logger.info("한국투자증권 웹소켓 연결 성공")
            
            # 메시지 수신 루프 시작
            asyncio.create_task(self._message_loop())
            
            return True
            
        except Exception as e:
            Logger.error(f"한국투자증권 웹소켓 연결 실패: {e}")
            self.is_connected = False
            return False
    
    async def _message_loop(self):
        """웹소켓 메시지 수신 루프"""
        try:
            while self.is_connected and self.websocket:
                message = await self.websocket.recv()
                await self._handle_message(message)
        except Exception as e:
            Logger.error(f"웹소켓 메시지 루프 에러: {e}")
            self.is_connected = False
    
    async def _handle_message(self, message: str):
        """메시지 처리"""
        try:
            data = json.loads(message)
            Logger.info(f"웹소켓 메시지 수신: {data}")
            
            # 한국투자증권 API 응답 처리
            if 'header' in data and 'tr_id' in data['header']:
                tr_id = data['header']['tr_id']
                
                # 지수 데이터 처리
                if tr_id.startswith('H0_'):
                    await self._process_market_index_data(data)
                # 주식 데이터 처리
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
    
    async def subscribe_stock_price(self, symbols: List[str], callback: Callable):
        """주식 실시간 가격 구독"""
        if not self.is_connected:
            Logger.error("웹소켓이 연결되지 않음")
            return False
            
        try:
            for symbol in symbols:
                # 실시간 주식 가격 구독 (한국투자증권 API 형식에 맞춤)
                subscribe_message = {
                    "header": {
                        "approval_key": self.approval_key,
                        "custtype": "P",
                        "tr_type": "1",
                        "content-type": "utf-8"
                    },
                    "body": {
                        "input": {
                            "tr_id": "H1_",
                            "tr_key": symbol
                        }
                    }
                }
                
                Logger.info(f"주식 구독 메시지 전송: {subscribe_message}")
                await self.websocket.send(json.dumps(subscribe_message))
                self.callbacks[f"H1_{symbol}"] = callback
                Logger.info(f"주식 실시간 구독 등록: {symbol}")
                
            return True
            
        except Exception as e:
            Logger.error(f"주식 구독 실패: {e}")
            return False
    
    async def subscribe_market_index(self, indices: List[str], callback: Callable):
        """시장 지수 실시간 구독"""
        if not self.is_connected:
            Logger.error("웹소켓이 연결되지 않음")
            return False
            
        try:
            for index in indices:
                # 실시간 지수 구독 (한국투자증권 API 형식에 맞춤)
                subscribe_message = {
                    "header": {
                        "approval_key": self.approval_key,
                        "custtype": "P",
                        "tr_type": "1",
                        "content-type": "utf-8"
                    },
                    "body": {
                        "input": {
                            "tr_id": "H0_CNT0",
                            "tr_key": index
                        }
                    }
                }
                
                Logger.info(f"지수 구독 메시지 전송: {subscribe_message}")
                await self.websocket.send(json.dumps(subscribe_message))
                self.callbacks[f"H0_{index}"] = callback
                Logger.info(f"지수 실시간 구독 등록: {index}")
                
            return True
            
        except Exception as e:
            Logger.error(f"지수 구독 실패: {e}")
            return False
    
    async def disconnect(self):
        """웹소켓 연결 해제"""
        self.is_connected = False
        if self.websocket:
            await self.websocket.close()
            Logger.info("한국투자증권 웹소켓 연결 해제")
    
    async def health_check(self, app_key: str, app_secret: str) -> Dict[str, Any]:
        """WebSocket 연결 상태 확인"""
        try:
            # 기존 연결이 있으면 해제
            if self.is_connected:
                await self.disconnect()
            
            # WebSocket 연결 테스트
            connection_success = await self.connect(app_key, app_secret)
            
            if connection_success and self.is_connected:
                # 연결 성공 후 즉시 해제 (테스트 목적)
                await self.disconnect()
                
                return {
                    "healthy": True,
                    "status": "websocket_connected",
                    "test_result": "WebSocket 연결 테스트 성공",
                    "websocket_url": self.ws_url
                }
            else:
                return {
                    "healthy": False,
                    "error": "WebSocket 연결 실패",
                    "status": "connection_failed",
                    "websocket_url": self.ws_url
                }
                
        except Exception as e:
            return {
                "healthy": False,
                "error": f"WebSocket 연결 테스트 실패: {str(e)}",
                "status": "test_failed"
            }

# 싱글톤 인스턴스
_korea_investment_websocket = None

async def get_korea_investment_websocket() -> KoreaInvestmentWebSocket:
    """한국투자증권 웹소켓 서비스 인스턴스 반환"""
    global _korea_investment_websocket
    if _korea_investment_websocket is None:
        _korea_investment_websocket = KoreaInvestmentWebSocket()
    return _korea_investment_websocket 