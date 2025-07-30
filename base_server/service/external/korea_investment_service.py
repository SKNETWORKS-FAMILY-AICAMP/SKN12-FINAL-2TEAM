import aiohttp
import asyncio
from typing import Dict, List, Optional
from service.core.logger import Logger
from service.service_container import ServiceContainer

class KoreaInvestmentService:
    """한국투자증권 API 서비스"""
    
    def __init__(self):
        self.base_url = "https://openapi.koreainvestment.com:9443"
        self.access_token = None
        self.app_key = None
        self.app_secret = None
        self.session = None
        self.token_expires_at = None  # 토큰 만료 시간
    
    async def init(self):
        """서비스 초기화"""
        self.session = aiohttp.ClientSession()
    
    async def authenticate(self, app_key: str, app_secret: str) -> bool:
        """한국투자증권 API 인증"""
        try:
            # API 키 저장
            self.app_key = app_key.strip()
            self.app_secret = app_secret.strip()
            
            # 기존 토큰이 있고 아직 유효한지 확인
            if self.access_token and self.token_expires_at:
                from datetime import datetime
                if datetime.now() < self.token_expires_at:
                    Logger.info("기존 토큰 사용 (아직 유효함)")
                    return True
                else:
                    Logger.info("토큰 만료됨, 새로 발급 필요")
            
            url = f"{self.base_url}/oauth2/tokenP"
            headers = {
                'content-type': 'application/json; charset=utf-8'
            }
            data = {
                'grant_type': 'client_credentials',
                'appkey': self.app_key,
                'appsecret': self.app_secret
            }
            
            Logger.info(f"한국투자증권 API 인증 시도: {self.app_key[:10]}... (전체 길이: {len(self.app_key)})")
            
            async with self.session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    self.access_token = result.get('access_token')
                    
                    # 토큰 만료 시간 설정 (23시간 후, 안전하게)
                    from datetime import datetime, timedelta
                    self.token_expires_at = datetime.now() + timedelta(hours=23)
                    
                    Logger.info("한국투자증권 API 인증 성공")
                    return True
                else:
                    error_text = await response.text()
                    Logger.error(f"한국투자증권 API 인증 실패: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            Logger.error(f"한국투자증권 API 인증 에러: {e}")
            return False
    
    async def get_stock_price(self, symbol: str) -> Optional[Dict]:
        """주식 현재가 조회"""
        if not self.access_token:
            Logger.error("한국투자증권 API 인증이 필요합니다")
            return None
            
        try:
            url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
            headers = {
                'Content-Type': 'application/json',
                'authorization': f'Bearer {self.access_token}',
                'appkey': self.app_key,
                'appsecret': self.app_secret,
                'tr_id': 'FHKST01010100'
            }
            params = {
                'FID_COND_MRKT_DIV_CODE': 'J',
                'FID_INPUT_ISCD': symbol
            }
            
            Logger.info(f"주식 조회 파라미터: {params}")
            Logger.info(f"주식 조회 URL: {url}")
            Logger.info(f"주식 조회 헤더: {headers}")
            
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    Logger.info(f"주식 가격 조회 성공: {result}")
                    return result.get('output', {})
                else:
                    error_text = await response.text()
                    Logger.error(f"주식 가격 조회 실패: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            Logger.error(f"주식 가격 조회 에러: {e}")
            return None
    
    async def get_market_index(self, index_code: str = "0001") -> Optional[Dict]:
        """시장 지수 조회 (KOSPI: 0001, KOSDAQ: 1001)"""
        if not self.access_token:
            Logger.error("한국투자증권 API 인증이 필요합니다")
            return None
            
        try:
            url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
            headers = {
                'Content-Type': 'application/json',
                'authorization': f'Bearer {self.access_token}',
                'appkey': self.app_key,
                'appsecret': self.app_secret,
                'tr_id': 'FHKST01010100'
            }
            params = {
                'FID_COND_MRKT_DIV_CODE': 'J',  # 주식 시장으로 변경
                'FID_INPUT_ISCD': index_code
            }
            
            Logger.info(f"지수 조회 파라미터: {params}")
            Logger.info(f"지수 조회 URL: {url}")
            Logger.info(f"지수 조회 헤더: {headers}")
            
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    Logger.info(f"시장 지수 조회 성공: {result}")
                    return result.get('output', {})
                else:
                    error_text = await response.text()
                    Logger.error(f"시장 지수 조회 실패: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            Logger.error(f"시장 지수 조회 에러: {e}")
            return None
    
    async def get_real_time_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """실시간 데이터 조회 (여러 종목)"""
        results = {}
        
        for symbol in symbols:
            try:
                # 주식 가격 조회
                price_data = await self.get_stock_price(symbol)
                if price_data:
                    results[symbol] = {
                        'current_price': float(price_data.get('stck_prpr', 0)),
                        'change_amount': float(price_data.get('prdy_vrss', 0)),
                        'change_rate': float(price_data.get('prdy_ctrt', 0)),
                        'volume': int(price_data.get('acml_vol', 0)),
                        'timestamp': price_data.get('hts_kor_isnm', '')
                    }
            except Exception as e:
                Logger.error(f"실시간 데이터 조회 에러 ({symbol}): {e}")
                continue
        
        return results
    
    async def close(self):
        """세션 종료"""
        if self.session:
            await self.session.close()

# 싱글톤 인스턴스
_korea_investment_service = None

async def get_korea_investment_service() -> KoreaInvestmentService:
    """한국투자증권 서비스 인스턴스 반환"""
    global _korea_investment_service
    if _korea_investment_service is None:
        _korea_investment_service = KoreaInvestmentService()
        await _korea_investment_service.init()
    return _korea_investment_service 