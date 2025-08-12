import asyncio
import json
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from service.core.logger import Logger
from service.service_container import ServiceContainer
from service.external.korea_investment_websocket_iocp import KoreaInvestmentWebSocketIOCP
from service.external.yahoo_finance_client import YahooFinanceClient
from service.external.external_service import ExternalService
from service.cache.cache_service import CacheService
# Model Server 호출을 위한 import
from template.model.common.model_serialize import PredictRequest, PredictResponse
from template.model.common.model_model import PredictionResult
from service.scheduler.scheduler_service import SchedulerService
# NotificationService 알림 발송을 위한 import
from service.notification.notification_service import NotificationService, NotificationChannel
from service.scheduler.base_scheduler import ScheduleJob, ScheduleType
import uuid

class SignalMonitoringService:
    """시그널 모니터링 서비스 - 실시간 주가 감시 및 볼린저 밴드 기반 시그널 발생"""
    
    _initialized = False
    _monitoring_symbols: Set[str] = set()  # 모니터링 중인 종목
    _korea_websocket: Optional[KoreaInvestmentWebSocketIOCP] = None
    _scheduler_job_ids: Set[str] = set()  # 스케줄러 작업 ID들
    
    # 캐시 키 패턴
    CACHE_KEY_PATTERN = "signal:price:{symbol}:{date}"  # 일별 가격 데이터
    CACHE_KEY_5DAYS = "signal:5days:{symbol}"  # 5일치 데이터
    CACHE_KEY_BOLLINGER = "signal:bollinger:{symbol}"  # 볼린저 밴드 데이터
    CACHE_TTL = 86400  # 24시간
    
    @classmethod
    async def init(cls):
        """서비스 초기화"""
        if cls._initialized:
            Logger.warn("SignalMonitoringService 이미 초기화됨")
            return
        
        try:
            # ServiceContainer에서 검증된 한투증권 서비스 인스턴스 획득
            cls._korea_websocket = None
            
            try:
                from service.service_container import ServiceContainer
                
                # ExternalService에서 이미 초기화되고 검증된 인스턴스 사용
                if ServiceContainer.is_korea_investment_service_initialized():
                    Logger.info("✅ KoreaInvestmentService 이미 초기화됨 (ExternalService)")
                    
                    # 검증된 WebSocket 인스턴스 획득
                    cls._korea_websocket = ServiceContainer.get_korea_investment_websocket()
                    if cls._korea_websocket:
                        Logger.info("🔗 ServiceContainer에서 검증된 WebSocket 인스턴스 획득")
                        
                        # 연결 상태 확인
                        if cls._korea_websocket.is_connected():
                            Logger.info("✅ WebSocket 이미 연결됨 - 즉시 사용 가능")
                        else:
                            Logger.info("🔌 WebSocket 연결되지 않음 - 구독 시 자동 연결 시도")
                    else:
                        Logger.error("❌ ServiceContainer에서 WebSocket 인스턴스 획득 실패")
                        
                else:
                    Logger.error("❌ KoreaInvestmentService 초기화되지 않음")
                    Logger.error("🚨 ExternalService 초기화가 선행되어야 합니다")
                    
            except Exception as service_e:
                Logger.error(f"❌ ServiceContainer 접근 실패: {service_e}")
                Logger.error("🚨 한투증권 WebSocket 기능을 사용할 수 없습니다")
            
            # SchedulerService는 이미 상단에서 import됨
            
            # 주기적으로 활성 알림 동기화 (5분마다)
            sync_job = ScheduleJob(
                job_id="signal_sync_alarms",
                name="시그널 알림 동기화",
                schedule_type=ScheduleType.INTERVAL,
                schedule_value=300,  # 5분
                callback=cls._sync_active_alarms,
                use_distributed_lock=True,
                lock_key="signal:sync:alarms"
            )
            await SchedulerService.add_job(sync_job)
            cls._scheduler_job_ids.add(sync_job.job_id)
            
            # 🩺 안전한 WebSocket 상태 확인 (기존 연결 보존)
            Logger.info("🩺 WebSocket 상태 확인 시작 (연결 보존 모드)")
            try:
                from service.service_container import ServiceContainer
                
                # 1. REST API만 테스트 (안전)
                korea_service = ServiceContainer.get_korea_investment_service()
                if korea_service:
                    Logger.info("🌐 REST API 상태 확인 중...")
                    try:
                        # 삼성전자 현재가 조회로 REST API 테스트
                        test_result = await korea_service.get_stock_price("005930")
                        if test_result:
                            current_price = test_result.get('stck_prpr', '0')
                            Logger.info(f"✅ REST API 정상: 삼성전자 현재가 {current_price}원")
                        else:
                            Logger.warn("⚠️ REST API 응답 없음")
                    except Exception as rest_e:
                        Logger.error(f"❌ REST API 테스트 실패: {rest_e}")
                
                # 2. 기존 WebSocket 연결 상태만 확인 (해제하지 않음)
                if cls._korea_websocket:
                    is_connected = cls._korea_websocket.is_connected()
                    Logger.info(f"📡 기존 WebSocket 연결 상태: {'✅ 연결됨' if is_connected else '❌ 끊어짐'}")
                    
                    if is_connected:
                        Logger.info("✅ WebSocket 연결 정상 - 기존 구독 유지하며 AAPL 추가 구독")
                    else:
                        Logger.warn("⚠️ WebSocket 연결 끊어짐 - 재연결 후 AAPL 구독 시도")
                else:
                    Logger.warn("⚠️ WebSocket 인스턴스 없음")
                    
                Logger.info("📊 ===== 안전한 상태 확인 완료 =====")
                Logger.info("🔒 기존 WebSocket 연결 및 구독 상태 보존됨")
                Logger.info("======================================")
                
            except Exception as health_e:
                Logger.error(f"❌ WebSocket 상태 확인 실패: {health_e}")
                import traceback
                Logger.error(f"Traceback: {traceback.format_exc()}")
            
            # 테스트용 AAPL 자동 구독 
            Logger.info("🍎 테스트용 AAPL 자동 구독 시작")
            await cls.subscribe_symbol("AAPL")
            Logger.info("🍎 AAPL 구독 완료 - 실시간 데이터 수신 시작")
            
            # WebSocket 연결 상태 주기적 체크 (1분마다)
            async def websocket_health_monitor():
                while cls._initialized:
                    try:
                        if cls._korea_websocket:
                            is_connected = cls._korea_websocket.is_connected()
                            monitoring_count = len(cls._monitoring_symbols)
                            Logger.info(f"📡 WebSocket 상태체크: 연결={'✅' if is_connected else '❌'}, 구독종목={monitoring_count}개 {list(cls._monitoring_symbols)}")
                            
                            # PINGPONG 폴백 모드 체크
                            if cls._korea_websocket.is_rest_fallback_mode():
                                Logger.info("🔄 REST API 폴백 모드 감지 - 모든 구독 종목을 REST API 폴링으로 전환")
                                for symbol in cls._monitoring_symbols:
                                    await cls._start_rest_api_polling(symbol)
                                Logger.info(f"✅ {len(cls._monitoring_symbols)}개 종목 REST API 폴링 시작됨")
                        else:
                            Logger.warn("⚠️ WebSocket 인스턴스 없음")
                    except Exception as monitor_e:
                        Logger.error(f"❌ WebSocket 상태체크 에러: {monitor_e}")
                    
                    # 60초 대기
                    await asyncio.sleep(60)
            
            # 백그라운드 태스크로 실행
            asyncio.create_task(websocket_health_monitor())
            
            # 매일 자정에 성과 업데이트
            performance_job = ScheduleJob(
                job_id="signal_update_performance",
                name="시그널 성과 업데이트",
                schedule_type=ScheduleType.DAILY,
                schedule_value="00:00",
                callback=cls._update_signal_performance,
                use_distributed_lock=True,
                lock_key="signal:update:performance"
            )
            await SchedulerService.add_job(performance_job)
            cls._scheduler_job_ids.add(performance_job.job_id)
            
            cls._initialized = True
            Logger.info("✅ SignalMonitoringService 초기화 완료")
            
        except Exception as e:
            Logger.error(f"❌ SignalMonitoringService 초기화 실패: {e}")
            raise
    
    @classmethod
    async def _sync_active_alarms(cls):
        """활성 알림 목록 조회 및 구독 (동적 샤드 조회)"""
        try:
            db_service = ServiceContainer.get_database_service()
            new_symbols = set()
            
            # 글로벌 DB에서 활성 샤드 목록 동적 조회
            active_shards = await cls._get_active_shard_ids(db_service)
            if not active_shards:
                Logger.error("활성 샤드가 없습니다. 시그널 동기화를 건너뜁니다.")
                return  # 폴백 없이 중단
            
            Logger.info(f"활성 샤드 조회: {len(active_shards)}개 샤드 [{', '.join(map(str, active_shards))}]")
            
            # 활성 샤드에서만 심볼 조회 (병렬 처리)
            shard_tasks = []
            for shard_id in active_shards:
                task = cls._get_active_symbols_from_shard(db_service, shard_id)
                shard_tasks.append(task)
            
            # 모든 활성 샤드를 동시에 쿼리
            shard_results = await asyncio.gather(*shard_tasks, return_exceptions=True)
            
            # 결과 통합
            for shard_id, result in zip(active_shards, shard_results):
                if isinstance(result, Exception):
                    Logger.error(f"샤드 {shard_id} 심볼 조회 실패: {result}")
                    continue
                
                if result:
                    new_symbols.update(result)
                    Logger.debug(f"샤드 {shard_id}: {len(result)}개 심볼 조회")
            
            # 새로운 종목 구독 (배치 처리)
            new_subscriptions = new_symbols - cls._monitoring_symbols
            if new_subscriptions:
                subscription_tasks = [cls.subscribe_symbol(symbol) for symbol in new_subscriptions]
                await asyncio.gather(*subscription_tasks, return_exceptions=True)
                Logger.info(f"신규 구독: {len(new_subscriptions)}개 종목")
            
            # 제거된 종목 구독 해제 (배치 처리)
            removed_subscriptions = cls._monitoring_symbols - new_symbols
            if removed_subscriptions:
                unsubscription_tasks = [cls.unsubscribe_symbol(symbol) for symbol in removed_subscriptions]
                await asyncio.gather(*unsubscription_tasks, return_exceptions=True)
                Logger.info(f"구독 해제: {len(removed_subscriptions)}개 종목")
            
            Logger.info(f"활성 알림 동기화 완료: {len(cls._monitoring_symbols)}개 종목 모니터링 중")
            
        except Exception as e:
            Logger.error(f"활성 알림 동기화 실패: {e}")
    
    @classmethod
    async def _get_active_shard_ids(cls, db_service) -> List[int]:
        """글로벌 DB에서 활성 샤드 ID 목록 조회"""
        try:
            result = await db_service.call_global_procedure(
                "fp_get_active_shard_ids",
                ()
            )
            
            if not result:
                Logger.warn("활성 샤드 조회 실패, 빈 결과")
                return []
            
            Logger.debug(f"프로시저 결과: {len(result)}개 행, 첫 번째 행: {result[0]}")
            
            # 첫 번째 행은 상태 확인 (ErrorCode, ErrorMessage)
            if len(result) >= 1:
                proc_result = result[0]
                if proc_result.get('ErrorCode', 1) != 0:
                    Logger.error(f"활성 샤드 조회 프로시저 오류: {proc_result.get('ErrorMessage', '')}")
                    return []
            
            # 두 번째 행부터가 샤드 데이터 (shard_id, shard_name, host, port, database_name, status, max_connections)
            active_shard_ids = []
            for i in range(1, len(result)):
                shard_data = result[i]
                shard_id = shard_data.get('shard_id')
                status = shard_data.get('status', '')
                if shard_id and status == 'active':
                    active_shard_ids.append(shard_id)
                    Logger.debug(f"활성 샤드 발견: {shard_id} ({status})")
            
            Logger.info(f"활성 샤드 조회 성공: {active_shard_ids}")
            return active_shard_ids
            
        except Exception as e:
            Logger.error(f"활성 샤드 조회 실패: {e}")
            import traceback
            Logger.error(f"Traceback: {traceback.format_exc()}")
            return []
    
    @classmethod
    async def _get_active_symbols_from_shard(cls, db_service, shard_id: int) -> set:
        """개별 샤드에서 활성 심볼 조회 (병렬 처리용)"""
        symbols = set()
        try:
            result = await db_service.call_shard_procedure(
                shard_id,
                "fp_signal_symbols_get_active",  # 최적화된 프로시저
                ()  # 빈 튜플
            )
            
            if result and len(result) > 1:  # 첫 번째는 상태
                for symbol_data in result[1:]:
                    symbol = symbol_data.get('symbol', '')
                    if symbol:
                        symbols.add(symbol)
                        
        except Exception as e:
            Logger.error(f"샤드 {shard_id} 심볼 조회 실패: {e}")
            
        return symbols
    
    @classmethod
    async def subscribe_symbol(cls, symbol: str):
        """종목 실시간 구독 시작 - 신뢰성 있는 연결 보장"""
        if symbol in cls._monitoring_symbols:
            Logger.info(f"🔄 이미 구독 중인 종목: {symbol}")
            return
        
        try:
            # 미국 주식만 처리
            if not cls._is_us_stock(symbol):
                Logger.info(f"⚠️ 한국주식은 현재 미지원: {symbol}")
                return
            
            # WebSocket 인스턴스 상태 검증
            if not cls._korea_websocket:
                Logger.error(f"❌ WebSocket 인스턴스 없음, 구독 불가: {symbol}")
                return
                
            # PINGPONG 폴백 모드 확인
            if cls._korea_websocket.is_rest_fallback_mode():
                Logger.info(f"🔄 {symbol} REST API 폴백 모드로 처리")
                # REST API로 주기적 폴링 처리
                await cls._start_rest_api_polling(symbol)
                return
                
            # 연결 상태 확인 및 자동 재연결 시도
            connection_ready = await cls._ensure_websocket_connection()
            if not connection_ready:
                Logger.error(f"❌ WebSocket 연결 실패, 구독 불가: {symbol}")
                return
            
            # 거래소 결정 (기본 NASDAQ)
            exchange = cls._determine_exchange(symbol)
            Logger.info(f"🏢 {symbol} → 거래소: {exchange}")
            
            # 콜백 함수 정의 (동기 함수로 처리 - IOCP 호환)
            def data_callback(data):
                try:
                    # 비동기 처리를 위해 task 생성
                    asyncio.create_task(cls._handle_us_stock_data(symbol, data))
                except Exception as callback_e:
                    Logger.error(f"❌ {symbol} 데이터 처리 콜백 에러: {callback_e}")
            
            # 미국주식 실시간 구독 시도 (재시도 로직 포함)
            subscribe_success = await cls._robust_subscribe_overseas_stock(
                exchange, symbol, data_callback
            )
            
            if subscribe_success:
                # 5일치 과거 데이터 캐싱 (병렬 처리)
                cache_task = asyncio.create_task(cls._cache_historical_data(symbol))
                
                # 모니터링 심볼에 추가
                cls._monitoring_symbols.add(symbol)
                Logger.info(f"✅ {symbol} 실시간 구독 성공 ({exchange})")
                
                # 백그라운드에서 캐싱 완료 대기
                try:
                    await asyncio.wait_for(cache_task, timeout=30.0)
                    Logger.info(f"📊 {symbol} 과거 데이터 캐싱 완료")
                except asyncio.TimeoutError:
                    Logger.warn(f"⚠️ {symbol} 과거 데이터 캐싱 타임아웃")
                except Exception as cache_e:
                    Logger.warn(f"⚠️ {symbol} 과거 데이터 캐싱 실패: {cache_e}")
            else:
                Logger.error(f"❌ {symbol} 실시간 구독 실패")
            
        except Exception as e:
            Logger.error(f"❌ 종목 구독 예외 ({symbol}): {e}")
            import traceback
            Logger.error(f"Traceback: {traceback.format_exc()}")
    
    @classmethod
    async def unsubscribe_symbol(cls, symbol: str):
        """종목 실시간 구독 중지"""
        if symbol not in cls._monitoring_symbols:
            return
        
        try:
            # WebSocket 구독 해제는 KoreaInvestmentWebSocket에서 자동 처리
            # 스케줄러 작업도 사용하지 않으므로 제거할 것 없음
            
            cls._monitoring_symbols.remove(symbol)
            Logger.info(f"종목 구독 중지: {symbol}")
            
        except Exception as e:
            Logger.error(f"종목 구독 중지 실패 ({symbol}): {e}")
    
    @classmethod
    def _is_us_stock(cls, symbol: str) -> bool:
        """미국 주식 여부 확인"""
        # 알파벳으로만 구성되고 1-5자리면 미국 주식으로 판단
        return symbol.isalpha() and 1 <= len(symbol) <= 5
    
    @classmethod
    def _determine_exchange(cls, symbol: str) -> str:
        """심볼 기반 거래소 결정"""
        # NYSE 상장 주요 종목들
        nyse_stocks = {
            'KO', 'BA', 'DIS', 'IBM', 'GE', 'F', 'GM', 'WMT', 'JPM', 'BAC',
            'XOM', 'CVX', 'PFE', 'JNJ', 'PG', 'MRK', 'VZ', 'T', 'HD', 'MCD'
        }
        
        if symbol.upper() in nyse_stocks:
            return "NYSE"
        else:
            return "NASD"  # 기본값: NASDAQ
    
    @classmethod
    async def _ensure_websocket_connection(cls) -> bool:
        """WebSocket 연결 상태 확인 및 자동 재연결"""
        try:
            if not cls._korea_websocket:
                Logger.error("❌ WebSocket 인스턴스가 없습니다")
                return False
            
            # 이미 연결되어 있으면 성공
            if cls._korea_websocket.is_connected():
                Logger.debug("✅ WebSocket 이미 연결됨")
                return True
            
            Logger.info("🔌 WebSocket 연결 시도 중...")
            
            # ServiceContainer에서 인증 정보 가져오기
            from service.service_container import ServiceContainer
            korea_service = ServiceContainer.get_korea_investment_service()
            
            if not korea_service:
                Logger.error("❌ KoreaInvestmentService 인스턴스 없음")
                return False
                
            # app_key, app_secret 획득
            if not hasattr(korea_service, '_app_key') or not hasattr(korea_service, '_app_secret'):
                Logger.error("❌ 한투증권 인증 정보가 없습니다")
                return False
                
            app_key = korea_service._app_key
            app_secret = korea_service._app_secret
            
            # approval_key 획득
            approval_key = await korea_service.get_approval_key_for_websocket()
            if not approval_key:
                Logger.warn("⚠️ approval_key 획득 실패 - 연결 시도는 계속")
                
            # WebSocket 연결 시도 (최대 3회)
            for attempt in range(3):
                try:
                    Logger.info(f"🔌 WebSocket 연결 시도 {attempt + 1}/3")
                    connection_success = await cls._korea_websocket.connect(
                        app_key, app_secret, approval_key
                    )
                    
                    if connection_success:
                        Logger.info("✅ WebSocket 연결 성공")
                        return True
                    else:
                        Logger.warn(f"❌ WebSocket 연결 실패 (시도 {attempt + 1}/3)")
                        
                except Exception as connect_e:
                    Logger.error(f"❌ WebSocket 연결 예외 (시도 {attempt + 1}/3): {connect_e}")
                
                # 재시도 전 잠시 대기
                if attempt < 2:
                    await asyncio.sleep(2.0 * (attempt + 1))
            
            Logger.error("❌ WebSocket 연결 모든 시도 실패")
            return False
            
        except Exception as e:
            Logger.error(f"❌ WebSocket 연결 확인 중 예외: {e}")
            return False
    
    @classmethod
    async def _robust_subscribe_overseas_stock(cls, exchange: str, symbol: str, callback) -> bool:
        """신뢰성 있는 해외주식 구독 (재시도 로직 포함)"""
        try:
            max_attempts = 3
            
            for attempt in range(max_attempts):
                try:
                    Logger.info(f"📤 해외주식 구독 시도 {attempt + 1}/{max_attempts}: {exchange}^{symbol}")
                    
                    # 구독 시도
                    success = await cls._korea_websocket.subscribe_overseas_stock_price(
                        exchange, [symbol], callback
                    )
                    
                    if success:
                        Logger.info(f"✅ 해외주식 구독 성공: {exchange}^{symbol}")
                        
                        # 구독 확인을 위해 잠시 대기
                        await asyncio.sleep(1.0)
                        return True
                    else:
                        Logger.warn(f"❌ 해외주식 구독 실패 (시도 {attempt + 1}/{max_attempts})")
                        
                except Exception as subscribe_e:
                    Logger.error(f"❌ 해외주식 구독 예외 (시도 {attempt + 1}/{max_attempts}): {subscribe_e}")
                
                # 재시도 전 연결 상태 다시 확인
                if attempt < max_attempts - 1:
                    Logger.info("🔄 연결 상태 재확인 후 재시도...")
                    connection_ready = await cls._ensure_websocket_connection()
                    if not connection_ready:
                        Logger.error("❌ 연결 복구 실패 - 구독 중단")
                        break
                        
                    await asyncio.sleep(1.0)
                    
            Logger.error(f"❌ 해외주식 구독 모든 시도 실패: {exchange}^{symbol}")
            return False
            
        except Exception as e:
            Logger.error(f"❌ 신뢰성 해외주식 구독 예외: {e}")
            return False
    
    @classmethod
    async def _start_rest_api_polling(cls, symbol: str):
        """REST API 폴링 모드 시작 (PINGPONG 대응)"""
        try:
            Logger.info(f"🔄 {symbol} REST API 폴링 모드 시작 (30초 간격)")
            
            # 폴링 태스크 이름
            task_name = f"rest_polling_{symbol}"
            
            # 기존 폴링 태스크가 있으면 제거
            if hasattr(cls, '_polling_tasks') and task_name in cls._polling_tasks:
                cls._polling_tasks[task_name].cancel()
                
            # 폴링 태스크 생성
            if not hasattr(cls, '_polling_tasks'):
                cls._polling_tasks = {}
                
            cls._polling_tasks[task_name] = asyncio.create_task(
                cls._rest_api_polling_loop(symbol)
            )
            
            Logger.info(f"✅ {symbol} REST API 폴링 태스크 시작됨")
            
        except Exception as e:
            Logger.error(f"❌ REST API 폴링 시작 실패 ({symbol}): {e}")
    
    @classmethod
    async def _rest_api_polling_loop(cls, symbol: str):
        """REST API 주기적 폴링 루프"""
        try:
            while True:
                try:
                    # KoreaInvestmentService를 통한 REST API 호출
                    from service.service_container import ServiceContainer
                    korea_service = ServiceContainer.get_korea_investment_service()
                    
                    if korea_service:
                        # 거래소 결정 (미국 주식은 대부분 NASDAQ/NYSE)
                        exchange = cls._determine_exchange(symbol)
                        
                        # 해외 주식 가격 조회 (REST API)
                        price_data = await korea_service.get_overseas_stock_price(exchange, symbol)
                        
                        if price_data:
                            # 빈 문자열이나 None을 0으로 처리
                            last_price = price_data.get('last', '')
                            
                            # 데이터가 빈 문자열이면 Yahoo Finance 사용
                            if last_price == '' or last_price == '0':
                                Logger.warn(f"⚠️ {symbol} 한투 API 빈 응답 - Yahoo Finance 사용")
                                try:
                                    import yfinance as yf
                                    ticker = yf.Ticker(symbol)
                                    info = ticker.info
                                    
                                    converted_data = {
                                        'current_price': float(info.get('currentPrice', info.get('regularMarketPrice', 0))),
                                        'high_price': float(info.get('dayHigh', 0)),
                                        'low_price': float(info.get('dayLow', 0)),
                                        'open_price': float(info.get('open', info.get('regularMarketOpen', 0))),
                                        'volume': int(info.get('volume', info.get('regularMarketVolume', 0)))
                                    }
                                    Logger.info(f"✅ Yahoo Finance 데이터 사용: ${converted_data['current_price']}")
                                except Exception as yf_e:
                                    Logger.error(f"❌ Yahoo Finance 실패: {yf_e}")
                                    converted_data = {'current_price': 0, 'high_price': 0, 'low_price': 0, 'open_price': 0, 'volume': 0}
                            else:
                                # 한투 API 데이터 사용
                                converted_data = {
                                    'current_price': float(last_price) if last_price else 0,
                                    'high_price': float(price_data.get('high', 0)) if price_data.get('high') else 0,
                                    'low_price': float(price_data.get('low', 0)) if price_data.get('low') else 0,
                                    'open_price': float(price_data.get('open', 0)) if price_data.get('open') else 0,
                                    'volume': int(price_data.get('tvol', 0)) if price_data.get('tvol') else 0
                                }
                            
                            Logger.info(f"📊 {symbol} REST API 데이터: ${converted_data['current_price']}")
                            
                            # 기존 처리 로직 재사용
                            await cls._handle_us_stock_data(symbol, converted_data)
                        else:
                            Logger.warn(f"⚠️ {symbol} REST API 데이터 없음")
                    
                    # 30초 대기
                    await asyncio.sleep(30)
                    
                except Exception as loop_e:
                    Logger.error(f"❌ REST API 폴링 루프 에러 ({symbol}): {loop_e}")
                    await asyncio.sleep(30)  # 에러 시에도 대기
                    
        except asyncio.CancelledError:
            Logger.info(f"🔄 {symbol} REST API 폴링 태스크 종료됨")
        except Exception as e:
            Logger.error(f"❌ REST API 폴링 루프 예외 ({symbol}): {e}")
    
    @classmethod
    async def _handle_us_stock_data(cls, symbol: str, data: Dict):
        """미국 주식 실시간 데이터 처리 (한국투자증권 WebSocket)"""
        try:
            # 원본 데이터 로깅 (디버깅용)
            Logger.info(f"🍎 {symbol} 원본 데이터 수신:")
            Logger.info(f"   📄 Raw Data: {data}")
            
            processed_data = {
                'symbol': symbol,
                'current_price': float(data.get('current_price', 0)),
                'high_price': float(data.get('high_price', 0)),
                'low_price': float(data.get('low_price', 0)),
                'open_price': float(data.get('open_price', 0)),
                'volume': int(data.get('volume', 0)),
                'timestamp': datetime.now().isoformat()
            }
            
            # 가공된 데이터 로깅
            Logger.info(f"🍎 {symbol} 가공된 데이터:")
            Logger.info(f"   💰 현재가: ${processed_data['current_price']}")
            Logger.info(f"   📈 고가: ${processed_data['high_price']}")
            Logger.info(f"   📉 저가: ${processed_data['low_price']}")
            Logger.info(f"   🚀 시가: ${processed_data['open_price']}")
            Logger.info(f"   📊 거래량: {processed_data['volume']:,}")
            Logger.info(f"   ⏰ 시간: {processed_data['timestamp']}")
            
            # 데이터 유효성 검사
            if processed_data['current_price'] > 0:
                Logger.info(f"✅ {symbol} 유효한 데이터 - 가격 처리 진행")
                await cls._process_price_data(symbol, processed_data)
            else:
                Logger.warn(f"⚠️ {symbol} 유효하지 않은 가격 데이터: {processed_data['current_price']}")
            
        except Exception as e:
            Logger.error(f"❌ 미국 주식 데이터 처리 에러 ({symbol}): {e}")
            import traceback
            Logger.error(f"Traceback: {traceback.format_exc()}")
    
    @classmethod
    async def _process_price_data(cls, symbol: str, data: Dict):
        """가격 데이터 처리 및 시그널 체크"""
        try:
            current_price = float(data.get('current_price', 0))
            if current_price <= 0:
                return
            
            cache_service = ServiceContainer.get_cache_service()
            
            # 오늘 데이터 캐싱
            today = datetime.now().strftime('%Y%m%d')
            cache_key = cls.CACHE_KEY_PATTERN.format(symbol=symbol, date=today)
            
            price_data = {
                'date': today,
                'price': current_price,
                'high': float(data.get('high_price', current_price)),
                'low': float(data.get('low_price', current_price)),
                'open': float(data.get('open_price', current_price)),
                'volume': int(data.get('volume', 0)),
                'timestamp': data.get('timestamp')
            }
            
            async with cache_service.get_client() as client:
                await client.set_string(cache_key, json.dumps(price_data), expire=cls.CACHE_TTL)
            
            # 5일치 캐시 업데이트
            await cls._update_5days_cache(symbol, price_data)
            
            # 볼린저 밴드 계산 및 시그널 체크
            await cls._check_bollinger_signal(symbol, current_price)
            
        except Exception as e:
            Logger.error(f"가격 데이터 처리 에러 ({symbol}): {e}")
    
    @classmethod
    async def _cache_historical_data(cls, symbol: str):
        """5일치 과거 데이터 캐싱 (미국주식만 지원)"""
        try:
            cache_service = ServiceContainer.get_cache_service()
            
            # 캐시 확인
            cache_key = cls.CACHE_KEY_5DAYS.format(symbol=symbol)
            async with cache_service.get_client() as client:
                cached = await client.get_string(cache_key)
            if cached:
                Logger.info(f"5일치 데이터 캐시 존재: {symbol}")
                return
            
            days_data = []
            
            if cls._is_us_stock(symbol):
                # Model Server에서 예측 데이터 가져오기 (template/model/common 사용)
                prediction_result = await cls._call_model_server_predict(symbol)
                if prediction_result and prediction_result.status == 'success':
                    # PredictionResult를 5일치 캐시 형태로 변환  
                    current_price = prediction_result.current_price
                    predictions = prediction_result.predictions
                    
                    # 현재 데이터 추가
                    today = datetime.now().strftime('%Y%m%d')
                    days_data.append({
                        'date': today,
                        'price': current_price,
                        'high': current_price * 1.005,  # 0.5% 상위
                        'low': current_price * 0.995,   # 0.5% 하위
                        'open': current_price,
                        'volume': 1000000  # 더미 볼륨
                    })
                    
                    # 예측 데이터 추가 (5일간)
                    for pred in predictions:
                        pred_date = pred.date.replace('-', '')
                        pred_price = pred.predicted_close
                        days_data.append({
                            'date': pred_date,
                            'price': pred_price,
                            'high': pred_price * 1.005,
                            'low': pred_price * 0.995,
                            'open': pred_price,
                            'volume': 1000000
                        })
                    
                    Logger.info(f"Model Server로 예측 데이터 생성: {symbol} @ ${current_price}, confidence={prediction_result.confidence_score}")
                    
                    # Model Server 예측 결과를 시그널로 분석
                    signal_data = cls._analyze_prediction_for_signals(prediction_result)
                    if signal_data:
                        Logger.info(f"🔔 Model Server 시그널 감지: {symbol} {signal_data['signal_type']}")
                        # 시그널 저장 및 알림 발송
                        await cls._process_model_server_signal(symbol, signal_data)
                    
                else:
                    # Model Server 실패 시 Yahoo Finance 폴백
                    Logger.warn(f"Model Server 실패, Yahoo Finance 폴백 사용: {symbol}")
                    async with YahooFinanceClient(cache_service) as client:
                        stock_detail = await client.get_stock_detail(symbol)
                        if stock_detail:
                            base_price = stock_detail.current_price
                            for i in range(5):
                                date = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
                                import random
                                variation = random.uniform(0.98, 1.02)
                                price = base_price * variation
                                days_data.append({
                                    'date': date,
                                    'price': price,
                                    'high': price * 1.01,
                                    'low': price * 0.99,
                                    'open': price,
                                    'volume': stock_detail.volume
                                })
            else:
                # 한국 주식은 서비스하지 않음
                Logger.info(f"한국 주식은 서비스하지 않습니다: {symbol}")
                return
            
            if days_data:
                async with cache_service.get_client() as client:
                    await client.set_string(cache_key, json.dumps(days_data), expire=cls.CACHE_TTL)
                Logger.info(f"5일치 데이터 캐싱 완료: {symbol}")
                
        except Exception as e:
            Logger.error(f"과거 데이터 캐싱 실패 ({symbol}): {e}")
    
    @classmethod
    async def _call_model_server_predict(cls, symbol: str) -> Optional[PredictionResult]:
        """Model Server API 호출하여 예측 데이터 가져오기 (template/model/common 사용)"""
        try:
            external_service = ServiceContainer.get_external_service()
            
            # PredictRequest 객체 생성 (template/model/common 사용)
            predict_request = PredictRequest(
                symbol=symbol,
                days=60,  # 기본값
                model_type="lstm"  # 기본값
            )
            
            # Model Server API 호출 (JSON 형태로 전송)
            response_data = await external_service.post_request(
                api_name="model_server",
                endpoint="/api/model/predict",
                data=predict_request.model_dump(),  # Pydantic 모델을 dict로 변환
                timeout=30
            )
            
            if response_data and isinstance(response_data, dict):
                # 응답을 PredictionResult로 파싱
                if response_data.get('status') == 'success':
                    prediction_result = PredictionResult(**response_data)
                    Logger.info(f"Model Server 예측 성공: {symbol}, confidence={prediction_result.confidence_score}")
                    return prediction_result
                else:
                    Logger.warn(f"Model Server 응답 실패: {symbol}, status={response_data.get('status')}")
                    return None
            else:
                Logger.warn(f"Model Server 응답 형식 오류: {symbol}, response={response_data}")
                return None
                
        except Exception as e:
            Logger.error(f"Model Server API 호출 실패 ({symbol}): {e}")
            return None
    
    @classmethod
    def _analyze_prediction_for_signals(cls, prediction: PredictionResult) -> Optional[Dict]:
        """PredictionResult를 분석하여 매수/매도 시그널 생성"""
        try:
            symbol = prediction.symbol
            current_price = prediction.current_price
            confidence = prediction.confidence_score
            predictions = prediction.predictions
            bollinger_bands = prediction.bollinger_bands
            
            if not predictions or len(predictions) < 1:
                Logger.warn(f"예측 데이터 부족: {symbol}")
                return None
            
            # 1일차 예측 분석
            day1_pred = predictions[0]
            day1_price = day1_pred.predicted_close
            day1_trend = day1_pred.trend
            
            # 가격 변화율 계산 (%)
            price_change_pct = (day1_price - current_price) / current_price * 100
            
            # 볼린저 밴드 분석 (과매수/과매도 구간)
            bb_position = 0.5  # 기본값 (중간)
            if bollinger_bands and len(bollinger_bands) > 0:
                bb = bollinger_bands[0]
                if bb.bb_upper > bb.bb_lower:
                    # 현재가의 볼린저 밴드 내 위치 (0~1)
                    bb_position = (current_price - bb.bb_lower) / (bb.bb_upper - bb.bb_lower)
                    bb_position = max(0, min(1, bb_position))  # 0~1 범위로 제한
            
            # 시그널 생성 로직
            signal_type = "HOLD"
            signal_strength = confidence
            signal_reason = []
            
            # 강한 매수 시그널 조건
            if (day1_trend == "up" and 
                price_change_pct > 2.0 and 
                confidence > 0.75 and 
                bb_position < 0.8):  # 과매수 구간 아님
                signal_type = "STRONG_BUY"
                signal_reason.append(f"상승추세 예측 (+{price_change_pct:.2f}%)")
                signal_reason.append(f"고신뢰도 ({confidence:.2f})")
                
            # 일반 매수 시그널 조건  
            elif (day1_trend == "up" and 
                  price_change_pct > 1.0 and 
                  confidence > 0.65):
                signal_type = "BUY"
                signal_reason.append(f"상승추세 예측 (+{price_change_pct:.2f}%)")
                
            # 강한 매도 시그널 조건
            elif (day1_trend == "down" and 
                  price_change_pct < -2.0 and 
                  confidence > 0.75 and 
                  bb_position > 0.2):  # 과매도 구간 아님
                signal_type = "STRONG_SELL"
                signal_reason.append(f"하락추세 예측 ({price_change_pct:.2f}%)")
                signal_reason.append(f"고신뢰도 ({confidence:.2f})")
                
            # 일반 매도 시그널 조건
            elif (day1_trend == "down" and 
                  price_change_pct < -1.0 and 
                  confidence > 0.65):
                signal_type = "SELL"
                signal_reason.append(f"하락추세 예측 ({price_change_pct:.2f}%)")
            
            # 볼린저 밴드 특별 시그널
            if bb_position > 0.95:  # 상한선 근처 (과매수)
                signal_type = "SELL" if signal_type == "HOLD" else signal_type
                signal_reason.append("볼린저 밴드 과매수 구간")
            elif bb_position < 0.05:  # 하한선 근처 (과매도)
                signal_type = "BUY" if signal_type == "HOLD" else signal_type
                signal_reason.append("볼린저 밴드 과매도 구간")
            
            # HOLD 시그널은 알림을 발송하지 않음
            if signal_type == "HOLD":
                return None
                
            # 시그널 객체 생성
            signal = {
                "signal_id": str(uuid.uuid4()),
                "symbol": symbol,
                "signal_type": signal_type,
                "signal_strength": signal_strength,
                "current_price": current_price,
                "predicted_price": day1_price,
                "price_change_pct": price_change_pct,
                "confidence_score": confidence,
                "bollinger_position": bb_position,
                "reasons": signal_reason,
                "prediction_date": prediction.prediction_date,
                "created_at": datetime.now().isoformat()
            }
            
            Logger.info(f"시그널 생성: {symbol} {signal_type} (강도: {signal_strength:.2f}, 변화율: {price_change_pct:+.2f}%)")
            return signal
            
        except Exception as e:
            Logger.error(f"시그널 분석 실패 ({prediction.symbol}): {e}")
            return None
    
    @classmethod
    async def _process_model_server_signal(cls, symbol: str, signal_data: Dict):
        """Model Server에서 생성된 시그널 처리 및 알림 발송"""
        try:
            db_service = ServiceContainer.get_database_service()
            
            # 활성 샤드 목록 조회
            active_shards = await cls._get_active_shard_ids(db_service)
            if not active_shards:
                Logger.warn("활성 샤드가 없어 Model Server 시그널 처리 건너뜀")
                return
            
            signal_type = signal_data['signal_type']
            current_price = signal_data['current_price']
            confidence = signal_data['confidence_score']
            
            # 시그널 히스토리 저장 및 알림 발송 (모든 구독자)
            for shard_id in active_shards:
                try:
                    # 해당 종목을 구독하는 사용자 조회
                    result = await db_service.call_shard_procedure(
                        shard_id,
                        "fp_signal_alarms_get_by_symbol",
                        (symbol,)
                    )
                    
                    if result and len(result) > 1:
                        for alarm_data in result[1:]:
                            alarm_id = alarm_data.get('alarm_id')
                            account_db_key = alarm_data.get('account_db_key')
                            
                            # 시그널 히스토리 저장
                            signal_id = signal_data['signal_id']
                            save_result = await db_service.execute_shard_procedure(
                                account_db_key,
                                "fp_signal_history_save",
                                (signal_id, alarm_id, signal_type, current_price)
                            )
                            
                            if save_result and save_result[0].get('ErrorCode') == 0:
                                Logger.info(f"✅ Model Server 시그널 저장: {alarm_id} - {signal_type} @ {current_price} (신뢰도: {confidence:.2f})")
                                
                                # 볼린저 밴드 데이터 생성 (Model Server 기반)
                                band_data = {
                                    'upper_band': current_price * (1 + signal_data['bollinger_position'] * 0.05),
                                    'avg_price': current_price,
                                    'lower_band': current_price * (1 - signal_data['bollinger_position'] * 0.05),
                                    'std_dev': current_price * 0.02,
                                    'timestamp': signal_data['created_at']
                                }
                                
                                # NotificationService를 통한 알림 전송
                                await cls._send_signal_notification(
                                    account_db_key,
                                    shard_id,
                                    symbol,
                                    signal_type,
                                    current_price,
                                    band_data,
                                    confidence
                                )
                            else:
                                Logger.error(f"Model Server 시그널 저장 실패: {alarm_id}")
                                
                except Exception as e:
                    Logger.error(f"샤드 {shard_id} Model Server 시그널 처리 실패: {e}")
                    continue
                    
        except Exception as e:
            Logger.error(f"Model Server 시그널 처리 실패: {e}")
    
    @classmethod
    async def _update_5days_cache(cls, symbol: str, new_data: Dict):
        """5일치 캐시 업데이트"""
        try:
            cache_service = ServiceContainer.get_cache_service()
            cache_key = cls.CACHE_KEY_5DAYS.format(symbol=symbol)
            
            async with cache_service.get_client() as client:
                cached = await client.get_string(cache_key)
                
            if cached:
                days_data = json.loads(cached)
            else:
                days_data = []
            
            # 오늘 데이터 업데이트
            today = new_data['date']
            found = False
            
            for i, day_data in enumerate(days_data):
                if day_data['date'] == today:
                    days_data[i] = new_data
                    found = True
                    break
            
            if not found:
                days_data.insert(0, new_data)
            
            # 최근 5일만 유지
            days_data = sorted(days_data, key=lambda x: x['date'], reverse=True)[:5]
            
            async with cache_service.get_client() as client:
                await client.set_string(cache_key, json.dumps(days_data), expire=cls.CACHE_TTL)
            
        except Exception as e:
            Logger.error(f"5일치 캐시 업데이트 실패 ({symbol}): {e}")
    
    @classmethod
    async def _check_bollinger_signal(cls, symbol: str, current_price: float):
        """볼린저 밴드 기반 시그널 체크"""
        try:
            cache_service = ServiceContainer.get_cache_service()
            
            # 5일치 데이터 가져오기
            cache_key = cls.CACHE_KEY_5DAYS.format(symbol=symbol)
            async with cache_service.get_client() as client:
                cached = await client.get_string(cache_key)
            
            if not cached:
                return
            
            days_data = json.loads(cached)
            if len(days_data) < 5:
                return
            
            # 가격 리스트 추출
            prices = [d['price'] for d in days_data]
            
            # 볼린저 밴드 계산 (5일 이동평균)
            avg_price = sum(prices) / len(prices)
            variance = sum((p - avg_price) ** 2 for p in prices) / len(prices)
            std_dev = variance ** 0.5
            
            # 볼린저 밴드 (2 표준편차)
            upper_band = avg_price + (2 * std_dev)
            lower_band = avg_price - (2 * std_dev)
            
            # 볼린저 밴드 데이터 캐싱
            bollinger_data = {
                'avg_price': avg_price,
                'upper_band': upper_band,
                'lower_band': lower_band,
                'std_dev': std_dev,
                'timestamp': datetime.now().isoformat()
            }
            
            bollinger_key = cls.CACHE_KEY_BOLLINGER.format(symbol=symbol)
            async with cache_service.get_client() as client:
                await client.set_string(bollinger_key, json.dumps(bollinger_data), expire=3600)  # 1시간
            
            # 시그널 판단
            signal_type = None
            if current_price <= lower_band:
                signal_type = "BUY"
                Logger.info(f"📈 BUY 시그널 발생: {symbol} @ {current_price} (하단: {lower_band})")
            elif current_price >= upper_band:
                signal_type = "SELL"
                Logger.info(f"📉 SELL 시그널 발생: {symbol} @ {current_price} (상단: {upper_band})")
            
            if signal_type:
                await cls._save_signal(symbol, current_price, signal_type, bollinger_data)
                
        except Exception as e:
            Logger.error(f"볼린저 밴드 시그널 체크 실패 ({symbol}): {e}")
    
    @classmethod
    async def _save_signal(cls, symbol: str, price: float, signal_type: str, band_data: Dict):
        """시그널 저장 및 Model Server 연동"""
        try:
            # TODO: Model Server 연동 - ExternalService 사용하여 추론 요청
            # 1. Model Server에 시그널 분석 요청
            # 2. 응답 받은 후 확정된 시그널만 DB 저장
            # 
            # 현재는 볼린저 밴드 시그널을 바로 저장
            
            db_service = ServiceContainer.get_database_service()
            
            # 활성 샤드 목록 조회
            active_shards = await cls._get_active_shard_ids(db_service)
            if not active_shards:
                Logger.warn("활성 샤드가 없어 시그널 저장 건너뜀")
                return
            
            # 해당 종목의 활성 알림만 조회 (활성 샤드에서만)
            for shard_id in active_shards:
                try:
                    result = await db_service.call_shard_procedure(
                        shard_id,
                        "fp_signal_alarms_get_by_symbol",  # 최적화된 프로시저
                        (symbol,)  # 심볼 파라미터
                    )
                    
                    if result and len(result) > 1:
                        for alarm_data in result[1:]:
                                alarm_id = alarm_data.get('alarm_id')
                                account_db_key = alarm_data.get('account_db_key')
                                
                                # TODO: Model Server 추론 요청
                                model_decision = await cls._request_model_inference(
                                    symbol, price, signal_type, band_data
                                )
                                
                                # Model Server 응답이 있으면 해당 결과 사용
                                if model_decision:
                                    final_signal_type = model_decision.get('signal_type', signal_type)
                                    confidence = model_decision.get('confidence', 0.5)
                                else:
                                    # Model Server 없으면 볼린저 밴드 결과 사용
                                    final_signal_type = signal_type
                                    confidence = 0.7  # 기본 신뢰도
                                
                                # 시그널 히스토리 저장
                                signal_id = str(uuid.uuid4())
                                save_result = await db_service.execute_shard_procedure(
                                    account_db_key,
                                    "fp_signal_history_save",
                                    (signal_id, alarm_id, final_signal_type, price)
                                )
                                
                                if save_result and save_result[0].get('ErrorCode') == 0:
                                    Logger.info(f"✅ 시그널 저장 완료: {alarm_id} - {final_signal_type} @ {price} (신뢰도: {confidence})")
                                    
                                    # NotificationService를 통한 알림 전송
                                    await cls._send_signal_notification(
                                        account_db_key,
                                        shard_id,  # 이미 알고 있는 shard_id 전달
                                        symbol, 
                                        final_signal_type, 
                                        price,
                                        band_data,
                                        confidence
                                    )
                                
                except Exception as e:
                    Logger.error(f"샤드 {shard_id} 시그널 저장 실패: {e}")
                    continue
                    
        except Exception as e:
            Logger.error(f"시그널 저장 실패: {e}")
    
    @classmethod
    async def _request_model_inference(cls, symbol: str, price: float, signal_type: str, band_data: Dict) -> Optional[Dict]:
        """Model Server에 추론 요청 - TODO: ExternalService 사용"""
        try:
            # TODO: ExternalService를 통해 Model Server API 호출
            # 
            # 예상 로직:
            # external_service = ServiceContainer.get_external_service()
            # response = await external_service.post(
            #     "model_server", 
            #     "/api/signal/inference",
            #     {
            #         "symbol": symbol,
            #         "current_price": price,
            #         "signal_type": signal_type,
            #         "bollinger_data": band_data,
            #         "historical_data": await cls.get_5days_data(symbol)
            #     }
            # )
            # 
            # if response.get("success"):
            #     return response.get("data")
            
            Logger.info(f"TODO: Model Server 추론 요청 - {symbol} {signal_type} @ {price}")
            
            # 임시로 None 반환 (Model Server 미구현)
            return None
            
        except Exception as e:
            Logger.error(f"Model Server 추론 요청 실패: {e}")
            return None
    
    @classmethod  
    async def _send_signal_notification(cls, account_db_key: int, shard_id: int, symbol: str, 
                                       signal_type: str, price: float, band_data: Dict, confidence: float = 0.7):
        """NotificationService 큐를 통한 시그널 알림 전송"""
        try:
            from service.notification.notification_service import NotificationService
            from service.notification.notification_config import NotificationType, NotificationChannel
            from datetime import datetime, timedelta
            
            # 1. 사용자 알림 설정 조회 (SQL 프로시저 사용)
            database_service = ServiceContainer.get_database_service()
            settings_result = await database_service.call_global_procedure(
                "fp_get_user_notification_settings",
                (account_db_key,)
            )
            
            if not settings_result or len(settings_result) < 2:
                Logger.warn(f"사용자 알림 설정 조회 실패, 기본값 사용: account_db_key={account_db_key}")
                user_settings = {
                    'email_notifications_enabled': 0,
                    'sms_notifications_enabled': 0,
                    'push_notifications_enabled': 0,
                    'trade_alert_enabled': 0
                }
            else:
                # 두 번째 행이 실제 설정 데이터 (첫 번째는 상태)
                settings_data = settings_result[1]
                user_settings = {
                    'email_notifications_enabled': int(settings_data.get('email_notifications_enabled', 0)),
                    'sms_notifications_enabled': int(settings_data.get('sms_notifications_enabled', 0)),
                    'push_notifications_enabled': int(settings_data.get('push_notifications_enabled', 0)),
                    'trade_alert_enabled': int(settings_data.get('trade_alert_enabled', 0))
                }
            
            # 2. 거래 알림이 비활성화되어 있으면 전송하지 않음
            if not user_settings['trade_alert_enabled']:
                Logger.info(f"거래 알림 비활성화됨, 전송 건너뜀: user={account_db_key}, {symbol} {signal_type}")
                return
            
            # 3. 시그널 타입에 따른 메시지 생성
            if signal_type == "BUY":
                title = f"📈 {symbol} 매수 시그널"
                message = f"{symbol} 종목에서 매수 신호가 발생했습니다. 현재가: ${price:.2f}"
            else:  # SELL
                title = f"📉 {symbol} 매도 시그널"
                message = f"{symbol} 종목에서 매도 신호가 발생했습니다. 현재가: ${price:.2f}"
            
            # 4. 알림 데이터 구성
            notification_data = {
                'symbol': symbol,
                'signal_type': signal_type,
                'price': price,
                'confidence': confidence,
                'bollinger': {
                    'upper': band_data['upper_band'],
                    'middle': band_data['avg_price'],
                    'lower': band_data['lower_band']
                },
                'timestamp': datetime.now().isoformat()
            }
            
            # 5. 우선순위 결정 (신뢰도 기반)
            if confidence >= 0.8:
                priority = 2  # HIGH
            elif confidence >= 0.6:
                priority = 3  # NORMAL  
            else:
                priority = 4  # LOW
            
            # 6. 사용자 설정에 따라 전송할 채널 결정
            channels = [NotificationChannel.IN_APP]  # 인앱 알림은 항상 포함
            
            if user_settings['email_notifications_enabled']:
                channels.append(NotificationChannel.EMAIL)
            if user_settings['sms_notifications_enabled']:
                channels.append(NotificationChannel.SMS)  
            if user_settings['push_notifications_enabled']:
                channels.append(NotificationChannel.PUSH)
            
            # 7. NotificationService를 통한 멀티채널 알림 발송 (큐 사용)
            success = await NotificationService.send_notification(
                user_id=str(account_db_key),
                shard_id=shard_id,
                notification_type=NotificationType.PREDICTION_ALERT,
                title=title,
                message=message,
                data=notification_data,
                priority=priority,
                channels=channels
            )
            
            if success:
                channel_names = [ch.value for ch in channels]
                Logger.info(f"📢 시그널 알림 큐 발송 성공: user={account_db_key}, {symbol} {signal_type}, 채널={channel_names}, 신뢰도={confidence}")
            else:
                Logger.error(f"시그널 알림 큐 발송 실패: user={account_db_key}, {symbol} {signal_type}")
                
        except Exception as e:
            Logger.error(f"시그널 알림 전송 에러: {e}")
            import traceback
            Logger.error(f"Traceback: {traceback.format_exc()}")
    
    @classmethod
    async def _update_signal_performance(cls):
        """1일 경과한 시그널의 성과 업데이트 - 실제 가격 조회 및 계산"""
        try:
            db_service = ServiceContainer.get_database_service()
            
            # 활성 샤드 목록 조회
            active_shards = await cls._get_active_shard_ids(db_service)
            if not active_shards:
                Logger.warn("활성 샤드가 없어 성과 업데이트 건너뜀")
                return
            
            # 어제 날짜 (1일 경과한 시그널 평가)
            yesterday = (datetime.now() - timedelta(days=1)).date()
            total_updated = 0
            
            # 각 샤드에서 미평가 시그널 조회 및 처리
            for shard_id in active_shards:
                try:
                    # 어제 발생한 미평가 시그널 조회
                    result = await db_service.call_shard_procedure(
                        shard_id,
                        "fp_signal_get_pending_evaluation",
                        (yesterday,)
                    )
                    
                    if not result or result[0].get('ErrorCode') != 0:
                        Logger.warn(f"샤드 {shard_id}: 미평가 시그널 조회 실패")
                        continue
                    
                    # 시그널 데이터가 있으면 처리 (첫 번째 행은 상태, 두 번째 행부터 데이터)
                    if len(result) > 1:
                        Logger.info(f"샤드 {shard_id}: {len(result)-1}개 미평가 시그널 발견")
                        
                        for signal_row in result[1:]:  # 첫 번째 행은 상태, 나머지가 시그널 데이터
                            signal_id = signal_row.get('signal_id')
                            account_db_key = signal_row.get('account_db_key')
                            symbol = signal_row.get('symbol')
                            signal_type = signal_row.get('signal_type')
                            signal_price = float(signal_row.get('signal_price', 0))
                            
                            if signal_price <= 0:
                                Logger.warn(f"잘못된 시그널 가격: {signal_id}")
                                continue
                            
                            # Yahoo Finance에서 현재 가격 조회
                            current_price = await cls._get_current_price_for_evaluation(symbol)
                            if current_price <= 0:
                                Logger.warn(f"현재 가격 조회 실패: {symbol}")
                                continue
                            
                            # 수익률 계산
                            profit_rate = (current_price - signal_price) / signal_price * 100
                            
                            # 성공 판정 (1% 이상 움직임)
                            is_win = 1 if abs(profit_rate) >= 1.0 else 0
                            
                            # DB 업데이트
                            update_result = await db_service.execute_shard_procedure(
                                account_db_key,
                                "fp_signal_performance_update",
                                (signal_id, current_price, profit_rate, is_win)
                            )
                            
                            if update_result and update_result[0].get('ErrorCode') == 0:
                                total_updated += 1
                                Logger.info(f"✅ 시그널 성과 업데이트: {symbol} {signal_type} "
                                          f"${signal_price:.2f} → ${current_price:.2f} "
                                          f"({profit_rate:+.2f}%, {'성공' if is_win else '실패'})")
                            else:
                                Logger.error(f"시그널 성과 업데이트 실패: {signal_id}")
                    
                except Exception as e:
                    Logger.error(f"샤드 {shard_id} 성과 업데이트 실패: {e}")
                    continue
            
            Logger.info(f"✅ 시그널 성과 업데이트 완료: 총 {total_updated}개 시그널 처리")
            
        except Exception as e:
            Logger.error(f"시그널 성과 업데이트 실패: {e}")
    
    @classmethod
    async def _get_current_price_for_evaluation(cls, symbol: str) -> float:
        """성과 평가용 현재 가격 조회 (Yahoo Finance 사용)"""
        try:
            cache_service = ServiceContainer.get_cache_service()
            
            # Yahoo Finance 클라이언트로 실시간 가격 조회
            async with YahooFinanceClient(cache_service) as yahoo_client:
                stock_detail = await yahoo_client.get_stock_detail(symbol)
                if stock_detail and stock_detail.current_price > 0:
                    Logger.info(f"💰 {symbol} 현재가: ${stock_detail.current_price:.2f}")
                    return stock_detail.current_price
                else:
                    Logger.warn(f"Yahoo Finance에서 {symbol} 가격 조회 실패")
                    return 0.0
                    
        except Exception as e:
            Logger.error(f"현재 가격 조회 실패 ({symbol}): {e}")
            return 0.0
    
    @classmethod
    async def get_bollinger_data(cls, symbol: str) -> Optional[Dict]:
        """캐시된 볼린저 밴드 데이터 조회"""
        try:
            cache_service = ServiceContainer.get_cache_service()
            bollinger_key = cls.CACHE_KEY_BOLLINGER.format(symbol=symbol)
            
            async with cache_service.get_client() as client:
                cached = await client.get_string(bollinger_key)
            if cached:
                return json.loads(cached)
            
            return None
            
        except Exception as e:
            Logger.error(f"볼린저 밴드 데이터 조회 실패 ({symbol}): {e}")
            return None
    
    @classmethod
    async def get_5days_data(cls, symbol: str) -> Optional[List[Dict]]:
        """캐시된 5일치 데이터 조회"""
        try:
            cache_service = ServiceContainer.get_cache_service()
            cache_key = cls.CACHE_KEY_5DAYS.format(symbol=symbol)
            
            async with cache_service.get_client() as client:
                cached = await client.get_string(cache_key)
            if cached:
                return json.loads(cached)
            
            return None
            
        except Exception as e:
            Logger.error(f"5일치 데이터 조회 실패 ({symbol}): {e}")
            return None
    
    @classmethod
    async def shutdown(cls):
        """서비스 종료"""
        try:
            cls._initialized = False
            
            # 모든 스케줄러 작업 제거
            for job_id in cls._scheduler_job_ids:
                try:
                    await SchedulerService.remove_job(job_id)
                except:
                    pass
            cls._scheduler_job_ids.clear()
            
            # WebSocket 연결 해제
            if cls._korea_websocket:
                await cls._korea_websocket.disconnect()
            
            # KoreaInvestmentService 종료
            try:
                from service.external.korea_investment_service import KoreaInvestmentService
                if KoreaInvestmentService.is_initialized():
                    await KoreaInvestmentService.shutdown()
                    Logger.info("✅ KoreaInvestmentService 종료 완료")
            except Exception as e:
                Logger.error(f"❌ KoreaInvestmentService 종료 실패: {e}")
            
            cls._monitoring_symbols.clear()
            
            Logger.info("SignalMonitoringService 종료 완료")
            
        except Exception as e:
            Logger.error(f"SignalMonitoringService 종료 실패: {e}")
    
    @classmethod
    def is_initialized(cls) -> bool:
        """초기화 여부 확인"""
        return cls._initialized