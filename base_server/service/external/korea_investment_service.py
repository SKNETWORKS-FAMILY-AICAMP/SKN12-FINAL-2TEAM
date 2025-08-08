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
    async def _authenticate(cls, force_new_token: bool = False) -> bool:
        """한국투자증권 API 인증 (Redis 지속성 포함)
        
        Args:
            force_new_token: True일 경우 Redis 토큰 무시하고 새 토큰 강제 발급
        """
        try:
            # 1. 강제 재인증이 아닐 때만 Redis에서 기존 토큰 확인
            if not force_new_token:
                redis_token, redis_expires = await cls._load_token_from_redis()
                
                if redis_token and redis_expires:
                    if datetime.now() < redis_expires:
                        Logger.info(f"Redis에서 유효한 토큰 복구 성공 (만료: {redis_expires})")
                        return True
                    else:
                        Logger.info("Redis 토큰 만료됨, 새로 발급 필요")
            else:
                Logger.info("🔄 강제 재인증 - Redis 토큰 건너뛰고 새 토큰 발급")
            
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
                Logger.info(f"📡 인증 API 응답 상태: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    new_token = result.get('access_token')
                    Logger.info(f"📊 발급받은 새 토큰: {new_token[:20] if new_token else 'None'}...")
                    
                    if not new_token:
                        Logger.error("❌ 응답에 access_token이 없습니다")
                        Logger.info(f"📊 전체 응답: {result}")
                        return False
                    
                    # 토큰 만료 시간 설정 (23시간 후, 안전하게)
                    expires_at = datetime.now() + timedelta(hours=23)
                    Logger.info(f"📊 토큰 만료 시간 설정: {expires_at}")
                    
                    # 3. Redis에 토큰 저장
                    redis_save_success = await cls._save_token_to_redis(new_token, expires_at)
                    Logger.info(f"📊 Redis 저장 결과: {redis_save_success}")
                    
                    if redis_save_success:
                        Logger.info("✅ 한국투자증권 API 인증 성공 및 Redis 저장 완료")
                        return True
                    else:
                        Logger.error("❌ Redis 토큰 저장 실패")
                        return False
                else:
                    error_text = await response.text()
                    Logger.error(f"❌ 한국투자증권 API 인증 실패: {response.status}")
                    Logger.error(f"📊 에러 상세: {error_text}")
                    Logger.info(f"📊 요청 URL: {url}")
                    Logger.info(f"📊 요청 헤더: {headers}")
                    Logger.info(f"📊 요청 데이터: {data}")
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
    async def _is_token_valid_by_api_test(cls, token: str) -> bool:
        """실제 API 호출로 토큰 유효성 검증 (간단한 테스트)"""
        try:
            # 가장 간단한 API로 토큰 유효성 테스트
            url = f"{cls._base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
            headers = {
                'Content-Type': 'application/json',
                'authorization': f'Bearer {token}',
                'appkey': cls._app_key,
                'appsecret': cls._app_secret,
                'tr_id': 'FHKST01010100'
            }
            params = {
                'FID_COND_MRKT_DIV_CODE': 'J',
                'FID_INPUT_ISCD': '005930'  # 삼성전자
            }
            
            # 3초 타임아웃으로 빠른 검증
            async with cls._session.get(url, headers=headers, params=params, timeout=aiohttp.ClientTimeout(total=3)) as response:
                if response.status == 200:
                    return True
                elif response.status == 500:
                    error_text = await response.text()
                    if "기간이 만료된 token" in error_text or "token" in error_text.lower():
                        Logger.warn("🔍 토큰 검증: 만료됨")
                        return False
                
                # 기타 에러는 네트워크 문제일 수 있으므로 유효하다고 가정
                Logger.warn(f"🔍 토큰 검증 불확실: {response.status}")
                return True
                
        except asyncio.TimeoutError:
            # 타임아웃은 네트워크 문제, 토큰은 유효하다고 가정
            Logger.warn("🔍 토큰 검증 타임아웃 - 유효하다고 가정")
            return True
        except Exception as e:
            # 기타 예외도 네트워크 문제로 간주
            Logger.warn(f"🔍 토큰 검증 예외 - 유효하다고 가정: {e}")
            return True

    @classmethod
    async def _get_current_token(cls) -> Optional[str]:
        """현재 유효한 토큰 반환 (실제 검증 후 사용)"""
        try:
            # 1. Redis에서 기존 토큰 조회
            token, expires_at = await cls._load_token_from_redis()
            
            # 2. 토큰이 있으면 실제 API로 유효성 검증
            if token and expires_at:
                # 시간상 유효한지 먼저 확인
                if datetime.now() < expires_at:
                    Logger.info(f"📅 Redis 토큰 시간 검증 통과 (만료: {expires_at})")
                    
                    # 실제 API 호출로 검증
                    if await cls._is_token_valid_by_api_test(token):
                        Logger.info("✅ 토큰 실제 API 검증 통과")
                        return token
                    else:
                        Logger.warn("⚠️ 토큰이 실제로는 만료됨")
                else:
                    Logger.warn(f"⚠️ Redis 토큰 시간 만료 (현재: {datetime.now()})")
            
            # 3. 토큰이 없거나 만료된 경우 새로 발급 (강제 재인증)
            Logger.info("🔄 새 토큰 강제 발급 중...")
            if await cls._authenticate(force_new_token=True):
                new_token, new_expires = await cls._load_token_from_redis()
                if new_token:
                    Logger.info("✅ 새 토큰 강제 발급 성공")
                    return new_token
            
            Logger.error("❌ 토큰 발급 실패")
            return None
                
        except Exception as e:
            Logger.error(f"❌ 토큰 조회 실패: {e}")
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
                Logger.warn("유효한 approval_key가 없음 - WebSocket 재인증 시도")
                # 자동 재인증 시도
                if await cls._authenticate_websocket():
                    # 재인증 성공 시 새 approval_key 반환
                    new_key, new_expires = await cls._load_approval_key_from_redis()
                    return new_key
                else:
                    Logger.error("approval_key 재인증 실패")
                    return None
                
        except Exception as e:
            Logger.error(f"approval_key 조회 실패: {e}")
            return None
    
    @classmethod
    async def get_stock_price(cls, symbol: str, retry_count: int = 0) -> Optional[Dict]:
        """주식 현재가 조회 (토큰 만료 시 자동 재시도)"""
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
                    
                    # 토큰 만료 에러인지 확인
                    if response.status == 500 and "기간이 만료된 token" in error_text:
                        Logger.warn(f"⚠️ 토큰 만료 감지 - 재인증 시도 (retry: {retry_count})")
                        Logger.info(f"📊 현재 사용된 토큰: {access_token[:20]}...")
                        Logger.info(f"📊 현재 appkey: {cls._app_key[:10]}...")
                        
                        # 최대 1회 재시도
                        if retry_count < 1:
                            Logger.info("🔄 강제 재인증 시작...")
                            # 강제 재인증 (Redis 토큰 무시)
                            auth_success = await cls._authenticate(force_new_token=True)
                            Logger.info(f"📊 재인증 결과: {auth_success}")
                            
                            if auth_success:
                                # 새 토큰 확인
                                new_token = await cls._get_current_token()
                                Logger.info(f"📊 새 토큰: {new_token[:20] if new_token else 'None'}...")
                                Logger.info("✅ 토큰 재인증 성공 - API 재시도")
                                return await cls.get_stock_price(symbol, retry_count + 1)
                            else:
                                Logger.error("❌ 토큰 재인증 실패 - 상세 확인 필요")
                                return None
                        else:
                            Logger.error("❌ 재시도 횟수 초과 - API 호출 포기")
                            return None
                    
                    Logger.error(f"주식 가격 조회 실패: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            Logger.error(f"주식 가격 조회 에러: {e}")
            return None
    
    @classmethod
    async def get_market_index(cls, index_code: str = "0001", retry_count: int = 0) -> Optional[Dict]:
        """시장 지수 조회 (KOSPI: 0001, KOSDAQ: 1001) - 토큰 만료 시 자동 재시도"""
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
                    
                    # 토큰 만료 에러인지 확인
                    if response.status == 500 and "기간이 만료된 token" in error_text:
                        Logger.warn(f"⚠️ 토큰 만료 감지 - 재인증 시도 (retry: {retry_count})")
                        
                        # 최대 1회 재시도
                        if retry_count < 1:
                            # 강제 재인증 (Redis 토큰 무시)
                            auth_success = await cls._authenticate(force_new_token=True)
                            if auth_success:
                                Logger.info("✅ 토큰 재인증 성공 - 지수 API 재시도")
                                return await cls.get_market_index(index_code, retry_count + 1)
                            else:
                                Logger.error("❌ 토큰 재인증 실패")
                                return None
                        else:
                            Logger.error("❌ 재시도 횟수 초과 - 지수 API 호출 포기")
                            return None
                    
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
    async def get_overseas_stock_price(cls, exchange: str, symbol: str, retry_count: int = 0) -> Optional[Dict]:
        """해외주식 현재가 조회 (토큰 만료 시 자동 재시도)
        
        Args:
            exchange: 거래소 코드 (NASD=나스닥, NYSE=뉴욕, AMEX=아멕스, TSE=도쿄, etc)
            symbol: 종목 심볼 (AAPL, TSLA, MSFT, etc)
            retry_count: 재시도 카운트
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
                    
                    # 토큰 만료 에러인지 확인
                    if response.status == 500 and "기간이 만료된 token" in error_text:
                        Logger.warn(f"⚠️ 토큰 만료 감지 - 재인증 시도 (retry: {retry_count})")
                        
                        # 최대 1회 재시도
                        if retry_count < 1:
                            # 강제 재인증 (Redis 토큰 무시)
                            auth_success = await cls._authenticate(force_new_token=True)
                            if auth_success:
                                Logger.info("✅ 토큰 재인증 성공 - 해외주식 API 재시도")
                                return await cls.get_overseas_stock_price(exchange, symbol, retry_count + 1)
                            else:
                                Logger.error("❌ 토큰 재인증 실패")
                                return None
                        else:
                            Logger.error("❌ 재시도 횟수 초과 - 해외주식 API 호출 포기")
                            return None
                    
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
        """Korea Investment API 연결 상태 확인 (REST + WebSocket 통합 테스트)"""
        if not cls._initialized:
            return {
                "healthy": False,
                "error": "KoreaInvestmentService가 초기화되지 않았습니다",
                "status": "not_initialized"
            }
        
        results = {
            "healthy": True,
            "status": "all_connected",
            "rest_api": {},
            "websocket": {}
        }
        
        # 1. IOCP WebSocket 테스트 먼저 실행 (appkey 충돌 방지)
        try:
            from .korea_investment_websocket_iocp import KoreaInvestmentWebSocketIOCP
            
            Logger.info("🚀 IOCP WebSocket 테스트 시작")
            
            # IOCP WebSocket 인스턴스 생성
            iocp_ws = KoreaInvestmentWebSocketIOCP()
            
            try:
                # 연결 시도
                connection_success = await iocp_ws.connect(cls._app_key, cls._app_secret)
                
                if connection_success:
                    # 구독 테스트
                    subscribe_success = await iocp_ws.subscribe_stock("005930")
                    
                    # 데이터 수신 대기 (2초)
                    await asyncio.sleep(2)
                    
                    # 구독 취소 테스트 (완료까지 대기)
                    unsubscribe_success = await iocp_ws.unsubscribe_stock("005930")
                    
                    # 연결 해제
                    await iocp_ws.disconnect()
                    
                    # ⭐ 완전 종료 대기 (이벤트 기반) ⭐
                    Logger.info("⏳ IOCP WebSocket 완전 종료 대기 중...")
                    shutdown_success = await iocp_ws.wait_for_complete_shutdown(timeout=5.0)
                    
                    if shutdown_success:
                        Logger.info("✅ IOCP WebSocket 완전 종료 확인")
                    else:
                        Logger.warn("⚠️ IOCP WebSocket 종료 타임아웃")
                    
                    websocket_test_success = connection_success and subscribe_success and unsubscribe_success
                    
                    results["websocket"] = {
                        "healthy": websocket_test_success,
                        "test_result": "IOCP WebSocket 연결/구독/구독취소 테스트 완료" if websocket_test_success else "IOCP WebSocket 테스트 실패",
                        "connection": connection_success,
                        "subscribe": subscribe_success,
                        "unsubscribe": unsubscribe_success,
                        "shutdown": shutdown_success
                    }
                    
                    if websocket_test_success:
                        Logger.info("✅ IOCP WebSocket 테스트 완료")
                    else:
                        Logger.error("❌ IOCP WebSocket 테스트 실패")
                        results["healthy"] = False
                else:
                    results["websocket"] = {
                        "healthy": False,
                        "error": "IOCP WebSocket 연결 실패"
                    }
                    results["healthy"] = False
                    Logger.error("❌ IOCP WebSocket 연결 실패")
                    
            except Exception as ws_e:
                Logger.error(f"❌ IOCP WebSocket 테스트 내부 예외: {ws_e}")
                results["websocket"] = {
                    "healthy": False,
                    "error": f"IOCP WebSocket 테스트 예외: {str(ws_e)}"
                }
                results["healthy"] = False
            finally:
                # 최종 정리 - 강제 해제 시도
                try:
                    await iocp_ws.disconnect()
                    await iocp_ws.wait_for_complete_shutdown(timeout=2.0)
                except Exception as cleanup_e:
                    Logger.error(f"❌ IOCP WebSocket 정리 중 예외: {cleanup_e}")
                    
        except Exception as e:
            results["websocket"] = {
                "healthy": False,
                "error": f"IOCP WebSocket 모듈 로드 실패: {str(e)}"
            }
            results["healthy"] = False
            Logger.error(f"❌ IOCP WebSocket 테스트 예외: {e}")
        
        # WebSocket 테스트가 완전히 끝났으므로 REST API 테스트 시작
        Logger.info("🔄 WebSocket 테스트 완료 → REST API 테스트 시작")
        
        # 2. REST API 테스트 실행 (WebSocket 테스트 완료 후)
        try:
            Logger.info("🚀 REST API 테스트 시작 (WebSocket 완료 후)")
            test_result = await cls.get_stock_price("005930")
            
            if test_result:
                current_price = test_result.get('stck_prpr', '0')
                results["rest_api"] = {
                    "healthy": True,
                    "test_api": "주식현재가조회",
                    "test_symbol": "005930(삼성전자)",
                    "test_result": f"현재가: {current_price}원"
                }
                Logger.info(f"✅ Korea Investment REST API 테스트 완료: 현재가: {current_price}원")
            else:
                results["rest_api"] = {
                    "healthy": False,
                    "error": "API 호출은 성공했지만 데이터가 없습니다"
                }
                results["healthy"] = False
                
        except Exception as e:
            results["rest_api"] = {
                "healthy": False,
                "error": f"REST API 연결 실패: {str(e)}"
            }
            results["healthy"] = False
            Logger.error(f"❌ REST API 테스트 실패: {e}")
        
        # 전체 상태 결정
        if results["rest_api"].get("healthy") and results["websocket"].get("healthy"):
            results["status"] = "all_connected"
            Logger.info("✅ Korea Investment 서비스 (REST + WebSocket) 초기화 완료")
        elif results["rest_api"].get("healthy"):
            results["status"] = "rest_only"
            Logger.warn("⚠️ Korea Investment 서비스: REST만 사용 가능")
        elif results["websocket"].get("healthy"):
            results["status"] = "websocket_only"
            Logger.warn("⚠️ Korea Investment 서비스: WebSocket만 사용 가능")
        else:
            results["status"] = "connection_failed"
            Logger.error("❌ Korea Investment 서비스: 모든 연결 실패")
            
        return results 