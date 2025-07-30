import asyncio
import json
from typing import Dict, List, Set, Callable
from service.core.logger import Logger
from service.external.korea_investment_websocket import KoreaInvestmentWebSocket

class WebSocketManager:
    """웹소켓 연결 관리자"""
    
    def __init__(self):
        self.connections: Dict[str, KoreaInvestmentWebSocket] = {}  # account_db_key -> websocket
        self.subscribers: Dict[str, Set[str]] = {}  # account_db_key -> set of client_ids
        self.data_callbacks: Dict[str, List[Callable]] = {}  # account_db_key -> list of callbacks
        self.is_running = False
    
    async def start(self):
        """웹소켓 매니저 시작"""
        self.is_running = True
        Logger.info("웹소켓 매니저 시작")
    
    async def stop(self):
        """웹소켓 매니저 중지"""
        self.is_running = False
        # 모든 연결 해제
        for account_db_key, websocket in self.connections.items():
            await websocket.disconnect()
        self.connections.clear()
        self.subscribers.clear()
        self.data_callbacks.clear()
        Logger.info("웹소켓 매니저 중지")
    
    async def connect_user(self, account_db_key: str, app_key: str, app_secret: str) -> bool:
        """사용자 웹소켓 연결"""
        try:
            if account_db_key in self.connections:
                Logger.info(f"이미 연결된 사용자: {account_db_key}")
                return True
            
            # 새로운 웹소켓 연결 생성
            websocket = KoreaInvestmentWebSocket()
            if await websocket.connect(app_key, app_secret):
                self.connections[account_db_key] = websocket
                self.subscribers[account_db_key] = set()
                self.data_callbacks[account_db_key] = []
                
                # 기본 지수 구독 (KOSPI, KOSDAQ)
                await websocket.subscribe_market_index(['0001', '1001'], 
                    lambda data: self._handle_market_data(account_db_key, data))
                
                Logger.info(f"사용자 웹소켓 연결 성공: {account_db_key}")
                return True
            else:
                Logger.error(f"사용자 웹소켓 연결 실패: {account_db_key}")
                return False
                
        except Exception as e:
            Logger.error(f"사용자 웹소켓 연결 에러: {account_db_key} - {e}")
            return False
    
    async def disconnect_user(self, account_db_key: str):
        """사용자 웹소켓 연결 해제"""
        try:
            if account_db_key in self.connections:
                await self.connections[account_db_key].disconnect()
                del self.connections[account_db_key]
                del self.subscribers[account_db_key]
                del self.data_callbacks[account_db_key]
                Logger.info(f"사용자 웹소켓 연결 해제: {account_db_key}")
        except Exception as e:
            Logger.error(f"사용자 웹소켓 연결 해제 에러: {account_db_key} - {e}")
    
    async def subscribe_stocks(self, account_db_key: str, symbols: List[str]) -> bool:
        """주식 구독 추가"""
        try:
            if account_db_key not in self.connections:
                Logger.error(f"연결되지 않은 사용자: {account_db_key}")
                return False
            
            websocket = self.connections[account_db_key]
            success = await websocket.subscribe_stock_price(symbols, 
                lambda data: self._handle_stock_data(account_db_key, data))
            
            if success:
                Logger.info(f"주식 구독 성공: {account_db_key} - {symbols}")
            else:
                Logger.error(f"주식 구독 실패: {account_db_key} - {symbols}")
            
            return success
            
        except Exception as e:
            Logger.error(f"주식 구독 에러: {account_db_key} - {e}")
            return False
    
    def add_data_callback(self, account_db_key: str, callback: Callable):
        """데이터 콜백 추가"""
        if account_db_key not in self.data_callbacks:
            self.data_callbacks[account_db_key] = []
        self.data_callbacks[account_db_key].append(callback)
        Logger.info(f"데이터 콜백 추가: {account_db_key}")
    
    def remove_data_callback(self, account_db_key: str, callback: Callable):
        """데이터 콜백 제거"""
        if account_db_key in self.data_callbacks:
            try:
                self.data_callbacks[account_db_key].remove(callback)
                Logger.info(f"데이터 콜백 제거: {account_db_key}")
            except ValueError:
                pass
    
    async def _handle_market_data(self, account_db_key: str, data):
        """시장 데이터 핸들러"""
        try:
            Logger.info(f"시장 데이터 수신: {account_db_key} - {data}")
            
            # 데이터를 시장 데이터 형식으로 변환
            market_data = {}
            if 'index_name' in data:
                index_name = data['index_name']
                market_data[index_name] = {
                    'current_price': data.get('current_price', 0),
                    'change_amount': data.get('change_amount', 0),
                    'change_rate': data.get('change_rate', 0),
                    'volume': data.get('volume', 0)
                }
            
            # 콜백 함수들 호출
            if account_db_key in self.data_callbacks:
                for callback in self.data_callbacks[account_db_key]:
                    try:
                        await callback('market', market_data)
                    except Exception as e:
                        Logger.error(f"시장 데이터 콜백 에러: {e}")
                        
        except Exception as e:
            Logger.error(f"시장 데이터 처리 에러: {account_db_key} - {e}")
    
    async def _handle_stock_data(self, account_db_key: str, data):
        """주식 데이터 핸들러"""
        try:
            Logger.info(f"주식 데이터 수신: {account_db_key} - {data}")
            
            # 데이터를 포트폴리오 데이터 형식으로 변환
            portfolio_data = {
                'symbol': data.get('symbol', ''),
                'name': data.get('symbol', ''),  # 실제로는 종목명 조회 필요
                'current_price': data.get('current_price', 0),
                'change_amount': data.get('change_amount', 0),
                'change_rate': data.get('change_rate', 0),
                'volume': data.get('volume', 0)
            }
            
            # 콜백 함수들 호출
            if account_db_key in self.data_callbacks:
                for callback in self.data_callbacks[account_db_key]:
                    try:
                        await callback('stock', portfolio_data)
                    except Exception as e:
                        Logger.error(f"주식 데이터 콜백 에러: {e}")
                        
        except Exception as e:
            Logger.error(f"주식 데이터 처리 에러: {account_db_key} - {e}")
    
    def get_connection_status(self, account_db_key: str) -> bool:
        """연결 상태 확인"""
        return account_db_key in self.connections and self.connections[account_db_key].is_connected

# 싱글톤 인스턴스
_websocket_manager = None

def get_websocket_manager() -> WebSocketManager:
    """웹소켓 매니저 인스턴스 반환"""
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
    return _websocket_manager 