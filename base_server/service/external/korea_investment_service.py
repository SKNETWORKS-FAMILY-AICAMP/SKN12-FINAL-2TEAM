import aiohttp
import asyncio
from typing import Dict, List, Optional
from service.core.logger import Logger

class KoreaInvestmentService:
    """한국투자증권 API 서비스 (정적 클래스)"""
    
    _base_url = "https://openapi.koreainvestment.com:9443"
    _access_token = None
    _app_key = None
    _app_secret = None
    _session = None
    _token_expires_at = None  # 토큰 만료 시간
    _initialized = False
    
    @classmethod
    async def init(cls, app_key: str, app_secret: str) -> bool:
        """서비스 초기화 및 인증"""
        try:
            if cls._initialized:
                Logger.warn("KoreaInvestmentService가 이미 초기화되었습니다")
                return True
                
            cls._session = aiohttp.ClientSession()
            cls._app_key = app_key
            cls._app_secret = app_secret
            
            # 인증 시도
            if await cls._authenticate():
                cls._initialized = True
                Logger.info("✅ KoreaInvestmentService 초기화 및 인증 완료")
                return True
            else:
                await cls._session.close()
                cls._session = None
                Logger.error("❌ KoreaInvestmentService 인증 실패")
                return False
                
        except Exception as e:
            Logger.error(f"❌ KoreaInvestmentService 초기화 실패: {e}")
            if cls._session:
                await cls._session.close()
                cls._session = None
            return False
    
    @classmethod
    async def _authenticate(cls) -> bool:
        """한국투자증권 API 인증 (내부 메서드)"""
        try:
            # 기존 토큰이 있고 아직 유효한지 확인
            if cls._access_token and cls._token_expires_at:
                from datetime import datetime
                if datetime.now() < cls._token_expires_at:
                    Logger.info("기존 토큰 사용 (아직 유효함)")
                    return True
                else:
                    Logger.info("토큰 만료됨, 새로 발급 필요")
            
            url = f"{cls._base_url}/oauth2/tokenP"
            headers = {
                'content-type': 'application/json; charset=utf-8'
            }
            data = {
                'grant_type': 'client_credentials',
                'appkey': cls._app_key,
                'appsecret': cls._app_secret
            }
            
            Logger.info(f"한국투자증권 API 인증 시도: {cls._app_key[:10]}... (전체 길이: {len(cls._app_key)})")
            
            async with cls._session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    cls._access_token = result.get('access_token')
                    
                    # 토큰 만료 시간 설정 (23시간 후, 안전하게)
                    from datetime import datetime, timedelta
                    cls._token_expires_at = datetime.now() + timedelta(hours=23)
                    
                    Logger.info("한국투자증권 API 인증 성공")
                    return True
                else:
                    error_text = await response.text()
                    Logger.error(f"한국투자증권 API 인증 실패: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            Logger.error(f"한국투자증권 API 인증 에러: {e}")
            return False
    
    @classmethod
    async def get_stock_price(cls, symbol: str) -> Optional[Dict]:
        """주식 현재가 조회"""
        if not cls._initialized:
            Logger.error("KoreaInvestmentService가 초기화되지 않았습니다")
            return None
            
        if not cls._access_token:
            Logger.error("한국투자증권 API 인증이 필요합니다")
            return None
            
        try:
            url = f"{cls._base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
            headers = {
                'Content-Type': 'application/json',
                'authorization': f'Bearer {cls._access_token}',
                'appkey': cls._app_key,
                'appsecret': cls._app_secret,
                'tr_id': 'FHKST01010100'
            }
            params = {
                'FID_COND_MRKT_DIV_CODE': 'J',
                'FID_INPUT_ISCD': symbol
            }
            
            Logger.info(f"주식 조회 파라미터: {params}")
            Logger.info(f"주식 조회 URL: {url}")
            Logger.info(f"주식 조회 헤더: {headers}")
            
            async with cls._session.get(url, headers=headers, params=params) as response:
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
    
    @classmethod
    async def get_market_index(cls, index_code: str = "0001") -> Optional[Dict]:
        """시장 지수 조회 (KOSPI: 0001, KOSDAQ: 1001)"""
        if not cls._initialized:
            Logger.error("KoreaInvestmentService가 초기화되지 않았습니다")
            return None
            
        if not cls._access_token:
            Logger.error("한국투자증권 API 인증이 필요합니다")
            return None
            
        try:
            url = f"{cls._base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
            headers = {
                'Content-Type': 'application/json',
                'authorization': f'Bearer {cls._access_token}',
                'appkey': cls._app_key,
                'appsecret': cls._app_secret,
                'tr_id': 'FHKST01010100'
            }
            params = {
                'FID_COND_MRKT_DIV_CODE': 'J',  # 주식 시장으로 변경
                'FID_INPUT_ISCD': index_code
            }
            
            Logger.info(f"지수 조회 파라미터: {params}")
            Logger.info(f"지수 조회 URL: {url}")
            Logger.info(f"지수 조회 헤더: {headers}")
            
            async with cls._session.get(url, headers=headers, params=params) as response:
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
    
    @classmethod
    async def get_real_time_data(cls, symbols: List[str]) -> Dict[str, Dict]:
        """실시간 데이터 조회 (여러 종목)"""
        results = {}
        
        for symbol in symbols:
            try:
                # 주식 가격 조회
                price_data = await cls.get_stock_price(symbol)
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
    
    @classmethod
    async def shutdown(cls):
        """서비스 종료"""
        try:
            if cls._session:
                await cls._session.close()
                cls._session = None
            
            cls._access_token = None
            cls._app_key = None
            cls._app_secret = None
            cls._token_expires_at = None
            cls._initialized = False
            
            Logger.info("KoreaInvestmentService 종료 완료")
            
        except Exception as e:
            Logger.error(f"KoreaInvestmentService 종료 실패: {e}")
    
    @classmethod
    def is_initialized(cls) -> bool:
        """초기화 여부 확인"""
        return cls._initialized
    
    @classmethod
    async def health_check(cls) -> Dict[str, any]:
        """Korea Investment API 연결 상태 확인 (삼성전자 주가 조회로 테스트)"""
        if not cls._initialized:
            return {
                "healthy": False,
                "error": "KoreaInvestmentService가 초기화되지 않았습니다",
                "status": "not_initialized"
            }
        
        try:
            # 삼성전자(005930) 주가 조회로 API 연결 테스트
            test_result = await cls.get_stock_price("005930")
            
            if test_result:
                current_price = test_result.get('stck_prpr', '0')
                return {
                    "healthy": True,
                    "status": "connected",
                    "test_api": "주식현재가조회",
                    "test_symbol": "005930(삼성전자)",
                    "test_result": f"현재가: {current_price}원",
                    "response_time": "success"
                }
            else:
                return {
                    "healthy": False,
                    "error": "API 호출은 성공했지만 데이터가 없습니다",
                    "status": "no_data"
                }
                
        except Exception as e:
            return {
                "healthy": False,
                "error": f"API 연결 테스트 실패: {str(e)}",
                "status": "connection_failed"
            } 