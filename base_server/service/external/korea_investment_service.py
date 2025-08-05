import aiohttp
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from service.core.logger import Logger

class KoreaInvestmentService:
    """한국투자증권 API 서비스 (정적 클래스)"""
    
    _base_url = "https://openapi.koreainvestment.com:9443"
    _app_key = None
    _app_secret = None
    _session = None
    _initialized = False
    
    # Redis 키 상수 - HTTP/WebSocket 별도 관리
    _REDIS_TOKEN_KEY = "korea_investment:access_token"
    _REDIS_EXPIRES_KEY = "korea_investment:token_expires_at" 
    _REDIS_APPROVAL_KEY = "korea_investment:approval_key"
    _REDIS_APPROVAL_EXPIRES_KEY = "korea_investment:approval_expires_at"
    
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
            
            # HTTP API 인증 시도
            http_auth = await cls._authenticate()
            if not http_auth:
                await cls._session.close()
                cls._session = None
                Logger.error("❌ KoreaInvestmentService HTTP 인증 실패")
                return False
            
            # WebSocket 인증 시도
            websocket_auth = await cls._authenticate_websocket()
            if not websocket_auth:
                Logger.warn("⚠️ WebSocket 인증 실패 - HTTP API만 사용 가능")
            
            cls._initialized = True
            Logger.info(f"✅ KoreaInvestmentService 초기화 완료 (HTTP: ✓, WebSocket: {'✓' if websocket_auth else '✗'})")
            return True
                
        except Exception as e:
            Logger.error(f"❌ KoreaInvestmentService 초기화 실패: {e}")
            if cls._session:
                await cls._session.close()
                cls._session = None
            return False
    
    @classmethod
    async def _load_token_from_redis(cls) -> tuple[Optional[str], Optional[datetime]]:
        """Redis에서 토큰 정보 로드 (ServiceContainer 사용)"""
        try:
            from service.service_container import ServiceContainer
            cache_service = ServiceContainer.get_cache_service()
            
            # Redis에서 토큰과 만료시간 조회
            async with cache_service.get_client() as client:
                token = await client.get_string(cls._REDIS_TOKEN_KEY)
                expires_str = await client.get_string(cls._REDIS_EXPIRES_KEY)
                
                if token and expires_str:
                    expires_at = datetime.fromisoformat(expires_str)
                    Logger.info("Redis에서 토큰 정보 로드 성공")
                    return token, expires_at
                else:
                    Logger.info("Redis에 저장된 토큰 없음")
                    return None, None
                    
        except Exception as e:
            Logger.error(f"Redis 토큰 로드 실패: {e}")
            return None, None
    
    @classmethod
    async def _save_token_to_redis(cls, token: str, expires_at: datetime) -> bool:
        """Redis에 토큰 정보 저장 (ServiceContainer 사용)"""
        try:
            from service.service_container import ServiceContainer
            cache_service = ServiceContainer.get_cache_service()
            
            # Redis에 토큰과 만료시간 저장 (24시간 + 1시간 여유)
            async with cache_service.get_client() as client:
                await client.set_string(cls._REDIS_TOKEN_KEY, token, expire=25*3600)  # 25시간
                await client.set_string(cls._REDIS_EXPIRES_KEY, expires_at.isoformat(), expire=25*3600)
                
            Logger.info("Redis에 토큰 정보 저장 성공")
            return True
            
        except Exception as e:
            Logger.error(f"Redis 토큰 저장 실패: {e}")
            return False
    
    @classmethod
    async def _authenticate(cls) -> bool:
        """한국투자증권 API 인증 (Redis 지속성 포함)"""
        try:
            # 1. Redis에서 기존 토큰 로드 시도
            redis_token, redis_expires = await cls._load_token_from_redis()
            
            if redis_token and redis_expires:
                if datetime.now() < redis_expires:
                    Logger.info(f"Redis에서 유효한 토큰 복구 성공 (만료: {redis_expires})")
                    return True
                else:
                    Logger.info("Redis 토큰 만료됨, 새로 발급 필요")
            
            # 2. 새 토큰 발급
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
                    new_token = result.get('access_token')
                    
                    # 토큰 만료 시간 설정 (23시간 후, 안전하게)
                    expires_at = datetime.now() + timedelta(hours=23)
                    
                    # 3. Redis에 토큰 저장
                    await cls._save_token_to_redis(new_token, expires_at)
                    
                    Logger.info("한국투자증권 API 인증 성공 및 Redis 저장 완료")
                    return True
                else:
                    error_text = await response.text()
                    Logger.error(f"한국투자증권 API 인증 실패: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            Logger.error(f"한국투자증권 API 인증 에러: {e}")
            return False
    
    @classmethod
    async def _load_approval_key_from_redis(cls) -> tuple[Optional[str], Optional[datetime]]:
        """Redis에서 WebSocket approval_key 로드"""
        try:
            from service.service_container import ServiceContainer
            cache_service = ServiceContainer.get_cache_service()
            
            async with cache_service.get_client() as client:
                approval_key = await client.get_string(cls._REDIS_APPROVAL_KEY)
                expires_str = await client.get_string(cls._REDIS_APPROVAL_EXPIRES_KEY)
                
                if approval_key and expires_str:
                    expires_at = datetime.fromisoformat(expires_str)
                    Logger.info("Redis에서 approval_key 로드 성공")
                    return approval_key, expires_at
                else:
                    Logger.info("Redis에 저장된 approval_key 없음")
                    return None, None
                    
        except Exception as e:
            Logger.error(f"Redis approval_key 로드 실패: {e}")
            return None, None
    
    @classmethod
    async def _save_approval_key_to_redis(cls, approval_key: str, expires_at: datetime) -> bool:
        """Redis에 WebSocket approval_key 저장"""
        try:
            from service.service_container import ServiceContainer
            cache_service = ServiceContainer.get_cache_service()
            
            async with cache_service.get_client() as client:
                await client.set_string(cls._REDIS_APPROVAL_KEY, approval_key, expire=25*3600)
                await client.set_string(cls._REDIS_APPROVAL_EXPIRES_KEY, expires_at.isoformat(), expire=25*3600)
                
            Logger.info("Redis에 approval_key 저장 성공")
            return True
            
        except Exception as e:
            Logger.error(f"Redis approval_key 저장 실패: {e}")
            return False
    
    @classmethod
    async def _authenticate_websocket(cls) -> bool:
        """WebSocket용 approval_key 인증 (Redis 지속성 포함)"""
        try:
            # 1. Redis에서 기존 approval_key 로드 시도
            redis_key, redis_expires = await cls._load_approval_key_from_redis()
            
            if redis_key and redis_expires:
                if datetime.now() < redis_expires:
                    Logger.info(f"Redis에서 유효한 approval_key 복구 성공 (만료: {redis_expires})")
                    return True
                else:
                    Logger.info("Redis approval_key 만료됨, 새로 발급 필요")
            
            # 2. 새 approval_key 발급
            url = f"{cls._base_url}/oauth2/Approval"
            headers = {
                'content-type': 'application/json; charset=utf-8'
            }
            data = {
                'grant_type': 'client_credentials',
                'appkey': cls._app_key,
                'secretkey': cls._app_secret  # WebSocket은 secretkey 사용
            }
            
            Logger.info(f"WebSocket approval_key 발급 시도: {cls._app_key[:10]}...")
            
            async with cls._session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    new_approval_key = result.get('approval_key')
                    
                    if not new_approval_key:
                        Logger.error("approval_key가 응답에 없습니다")
                        return False
                    
                    # approval_key 만료 시간 설정 (23시간 후)
                    expires_at = datetime.now() + timedelta(hours=23)
                    
                    # 3. Redis에 approval_key 저장
                    await cls._save_approval_key_to_redis(new_approval_key, expires_at)
                    
                    Logger.info("WebSocket approval_key 발급 및 Redis 저장 완료")
                    return True
                else:
                    error_text = await response.text()
                    Logger.error(f"WebSocket approval_key 발급 실패: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            Logger.error(f"WebSocket approval_key 인증 에러: {e}")
            return False
    
    @classmethod
    async def _get_current_token(cls) -> Optional[str]:
        """현재 유효한 토큰 반환 (Redis 우선, HTTP/WebSocket 범용)"""
        try:
            # Redis에서 토큰 로드
            token, expires_at = await cls._load_token_from_redis()
            
            if token and expires_at and datetime.now() < expires_at:
                return token
            else:
                Logger.warn("유효한 토큰이 없음 - 재인증 필요")
                return None
                
        except Exception as e:
            Logger.error(f"토큰 조회 실패: {e}")
            return None
    
    @classmethod
    async def _get_current_approval_key(cls) -> Optional[str]:
        """현재 유효한 WebSocket approval_key 반환 (Redis 우선)"""
        try:
            # Redis에서 approval_key 로드
            approval_key, expires_at = await cls._load_approval_key_from_redis()
            
            if approval_key and expires_at and datetime.now() < expires_at:
                return approval_key
            else:
                Logger.warn("유효한 approval_key가 없음 - WebSocket 재인증 필요")
                return None
                
        except Exception as e:
            Logger.error(f"approval_key 조회 실패: {e}")
            return None
    
    @classmethod
    async def get_stock_price(cls, symbol: str) -> Optional[Dict]:
        """주식 현재가 조회"""
        if not cls._initialized:
            Logger.error("KoreaInvestmentService가 초기화되지 않았습니다")
            return None
            
        # 동적 토큰 조회
        access_token = await cls._get_current_token()
        if not access_token:
            Logger.error("유효한 토큰이 없습니다 - 재인증이 필요합니다")
            return None
            
        try:
            url = f"{cls._base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
            headers = {
                'Content-Type': 'application/json',
                'authorization': f'Bearer {access_token}',
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
            
        # 동적 토큰 조회
        access_token = await cls._get_current_token()
        if not access_token:
            Logger.error("유효한 토큰이 없습니다 - 재인증이 필요합니다")
            return None
            
        try:
            url = f"{cls._base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
            headers = {
                'Content-Type': 'application/json',
                'authorization': f'Bearer {access_token}',
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
    async def get_overseas_stock_price(cls, exchange: str, symbol: str) -> Optional[Dict]:
        """해외주식 현재가 조회
        
        Args:
            exchange: 거래소 코드 (NASD=나스닥, NYSE=뉴욕, AMEX=아멕스, TSE=도쿄, etc)
            symbol: 종목 심볼 (AAPL, TSLA, MSFT, etc)
        """
        if not cls._initialized:
            Logger.error("KoreaInvestmentService가 초기화되지 않았습니다")
            return None
            
        # 동적 토큰 조회
        access_token = await cls._get_current_token()
        if not access_token:
            Logger.error("유효한 토큰이 없습니다 - 재인증이 필요합니다")
            return None
            
        try:
            url = f"{cls._base_url}/uapi/overseas-price/v1/quotations/price"
            headers = {
                'Content-Type': 'application/json',
                'authorization': f'Bearer {access_token}',
                'appkey': cls._app_key,
                'appsecret': cls._app_secret,
                'tr_id': 'HHDFS00000300'  # 해외주식 현재가 TR ID
            }
            params = {
                'AUTH': '',
                'EXCD': exchange,  # 거래소코드
                'SYMB': symbol     # 심볼
            }
            
            Logger.info(f"해외주식 조회 파라미터: {params}")
            Logger.info(f"해외주식 조회 URL: {url}")
            
            async with cls._session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    Logger.info(f"해외주식 가격 조회 성공: {result}")
                    return result.get('output', {})
                else:
                    error_text = await response.text()
                    Logger.error(f"해외주식 가격 조회 실패: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            Logger.error(f"해외주식 가격 조회 에러: {e}")
            return None
    
    @classmethod
    async def get_overseas_real_time_data(cls, exchange: str, symbols: List[str]) -> Dict[str, Dict]:
        """해외주식 실시간 데이터 조회 (여러 종목)
        
        Args:
            exchange: 거래소 코드
            symbols: 종목 심볼 리스트
        """
        results = {}
        
        for symbol in symbols:
            try:
                # 해외주식 가격 조회
                price_data = await cls.get_overseas_stock_price(exchange, symbol)
                if price_data:
                    results[f"{exchange}^{symbol}"] = {
                        'symbol': symbol,
                        'exchange': exchange,
                        'current_price': float(price_data.get('last', 0)),
                        'change_amount': float(price_data.get('diff', 0)),
                        'change_rate': float(price_data.get('rate', 0)),
                        'volume': int(price_data.get('tvol', 0)),
                        'high_price': float(price_data.get('high', 0)),
                        'low_price': float(price_data.get('low', 0)),
                        'open_price': float(price_data.get('open', 0)),
                        'timestamp': price_data.get('date', '')
                    }
            except Exception as e:
                Logger.error(f"해외주식 실시간 데이터 조회 에러 ({exchange}^{symbol}): {e}")
                continue
        
        return results
    
    @classmethod
    async def shutdown(cls):
        """서비스 종료"""
        try:
            if cls._session:
                await cls._session.close()
                cls._session = None
            
            cls._app_key = None
            cls._app_secret = None
            cls._initialized = False
            
            Logger.info("KoreaInvestmentService 종료 완료")
            
        except Exception as e:
            Logger.error(f"KoreaInvestmentService 종료 실패: {e}")
    
    @classmethod
    def is_initialized(cls) -> bool:
        """초기화 여부 확인"""
        return cls._initialized
    
    @classmethod
    async def get_approval_key_for_websocket(cls) -> Optional[str]:
        """WebSocket용 approval_key 반환 (외부 접근 허용)"""
        if not cls._initialized:
            Logger.error("KoreaInvestmentService가 초기화되지 않았습니다")
            return None
            
        # approval_key 조회 시도
        approval_key = await cls._get_current_approval_key()
        
        # 없거나 만료된 경우 재발급 시도
        if not approval_key:
            Logger.info("approval_key 재발급 시도")
            if await cls._authenticate_websocket():
                approval_key = await cls._get_current_approval_key()
            
        return approval_key
    
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