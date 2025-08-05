import asyncio
import json
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from service.core.logger import Logger
from service.service_container import ServiceContainer
from service.external.korea_investment_websocket import KoreaInvestmentWebSocket
from service.external.yahoo_finance_client import YahooFinanceClient
from service.cache.cache_service import CacheService
from service.scheduler.scheduler_service import SchedulerService
from service.scheduler.base_scheduler import ScheduleJob, ScheduleType
import uuid

class SignalMonitoringService:
    """시그널 모니터링 서비스 - 실시간 주가 감시 및 볼린저 밴드 기반 시그널 발생"""
    
    _initialized = False
    _monitoring_symbols: Set[str] = set()  # 모니터링 중인 종목
    _korea_websocket: Optional[KoreaInvestmentWebSocket] = None
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
            # 한국투자증권 WebSocket 초기화 (미국 주식용)
            cls._korea_websocket = KoreaInvestmentWebSocket()
            
            # ServiceContainer에서 config 가져오기 (template 초기화 시 이미 로드됨)
            try:
                from template.base.template_service import TemplateService
                app_config = TemplateService.get_config()
                
                if app_config and hasattr(app_config, 'externalConfig') and app_config.externalConfig:
                    korea_config = getattr(app_config.externalConfig, 'korea_investment', None)
                    
                    if korea_config:
                        app_key = getattr(korea_config, 'app_key', None)
                        app_secret = getattr(korea_config, 'app_secret', None)
                        
                        if app_key and app_secret:
                            # WebSocket 연결 시도
                            connection_success = await cls._korea_websocket.connect(app_key, app_secret)
                            if connection_success:
                                Logger.info("✅ 한국투자증권 WebSocket 연결 성공 (미국주식용)")
                            else:
                                Logger.error("❌ 한국투자증권 WebSocket 연결 실패")
                                # 연결 실패해도 서비스는 시작 (폴백으로 Yahoo Finance 사용 가능)
                        else:
                            Logger.warn("⚠️ 한국투자증권 API 키가 설정되지 않음 - WebSocket 사용 불가")
                    else:
                        Logger.warn("⚠️ 한국투자증권 설정을 찾을 수 없음 - WebSocket 사용 불가")
                else:
                    Logger.warn("⚠️ External 설정을 찾을 수 없음 - WebSocket 사용 불가")
                    
            except Exception as config_e:
                Logger.error(f"❌ 설정 로드 실패: {config_e} - WebSocket 사용 불가")
            
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
            result = await db_service.execute_global_procedure(
                "fp_get_active_shard_ids",
                ()
            )
            
            if not result or len(result) < 2:
                Logger.warn("활성 샤드 조회 실패, 빈 결과")
                return []
            
            # 첫 번째는 상태, 두 번째부터는 샤드 데이터
            proc_result = result[0]
            if proc_result.get('ErrorCode', 1) != 0:
                Logger.error(f"활성 샤드 조회 프로시저 오류: {proc_result.get('ErrorMessage', '')}")
                return []
            
            active_shard_ids = []
            for shard_data in result[1:]:
                shard_id = shard_data.get('shard_id')
                status = shard_data.get('status', '')
                if shard_id and status == 'active':
                    active_shard_ids.append(shard_id)
            
            return active_shard_ids
            
        except Exception as e:
            Logger.error(f"활성 샤드 조회 실패: {e}")
            return []
    
    @classmethod
    async def _get_active_symbols_from_shard(cls, db_service, shard_id: int) -> set:
        """개별 샤드에서 활성 심볼 조회 (병렬 처리용)"""
        symbols = set()
        try:
            result = await db_service.execute_shard_procedure_by_shard_id(
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
        """종목 실시간 구독 시작"""
        if symbol in cls._monitoring_symbols:
            return
        
        try:
            # 미국 주식만 처리
            if cls._is_us_stock(symbol):
                if cls._korea_websocket and cls._korea_websocket.is_connected:
                    # 거래소 결정 (기본 NASDAQ)
                    exchange = "NASD"
                    nyse_stocks = ['KO', 'BA', 'DIS', 'IBM', 'GE', 'F', 'GM', 'WMT', 'JPM', 'BAC']
                    if symbol in nyse_stocks:
                        exchange = "NYSE"
                    
                    # 미국주식 실시간 구독
                    await cls._korea_websocket.subscribe_overseas_stock_price(
                        exchange,
                        [symbol],
                        lambda data: asyncio.create_task(cls._handle_us_stock_data(symbol, data))
                    )
                    Logger.info(f"✅ 미국주식 구독: {exchange}^{symbol}")
                else:
                    Logger.warn(f"WebSocket 연결 없음, 구독 건너뜀: {symbol}")
                    return
            else:
                Logger.info(f"한국주식은 미지원: {symbol}")
                return
            
            # 5일치 데이터 캐싱
            await cls._cache_historical_data(symbol)
            
            cls._monitoring_symbols.add(symbol)
            Logger.info(f"✅ 종목 구독 시작: {symbol}")
            
        except Exception as e:
            Logger.error(f"종목 구독 실패 ({symbol}): {e}")
    
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
    async def _handle_us_stock_data(cls, symbol: str, data: Dict):
        """미국 주식 실시간 데이터 처리 (한국투자증권 WebSocket)"""
        try:
            processed_data = {
                'symbol': symbol,
                'current_price': float(data.get('current_price', 0)),
                'high_price': float(data.get('high_price', 0)),
                'low_price': float(data.get('low_price', 0)),
                'open_price': float(data.get('open_price', 0)),
                'volume': int(data.get('volume', 0)),
                'timestamp': datetime.now().isoformat()
            }
            
            Logger.info(f"미국주식 실시간 데이터 수신: {symbol} @ ${processed_data['current_price']}")
            await cls._process_price_data(symbol, processed_data)
            
        except Exception as e:
            Logger.error(f"미국 주식 데이터 처리 에러 ({symbol}): {e}")
    
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
            
            await cache_service.set(cache_key, json.dumps(price_data), cls.CACHE_TTL)
            
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
            cached = await cache_service.get(cache_key)
            if cached:
                Logger.info(f"5일치 데이터 캐시 존재: {symbol}")
                return
            
            days_data = []
            
            if cls._is_us_stock(symbol):
                # Yahoo Finance에서 초기 데이터 가져오기 (캐싱용)
                async with YahooFinanceClient(cache_service) as client:
                    stock_detail = await client.get_stock_detail(symbol)
                    if stock_detail:
                        # 임시로 최근 가격 기반 더미 데이터 생성
                        base_price = stock_detail.current_price
                        for i in range(5):
                            date = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
                            # ±2% 변동
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
                        
                        Logger.info(f"Yahoo Finance로 초기 데이터 생성: {symbol} @ ${base_price}")
            else:
                # 한국 주식은 서비스하지 않음
                Logger.info(f"한국 주식은 서비스하지 않습니다: {symbol}")
                return
            
            if days_data:
                await cache_service.set(cache_key, json.dumps(days_data), cls.CACHE_TTL)
                Logger.info(f"5일치 데이터 캐싱 완료: {symbol}")
                
        except Exception as e:
            Logger.error(f"과거 데이터 캐싱 실패 ({symbol}): {e}")
    
    @classmethod
    async def _update_5days_cache(cls, symbol: str, new_data: Dict):
        """5일치 캐시 업데이트"""
        try:
            cache_service = ServiceContainer.get_cache_service()
            cache_key = cls.CACHE_KEY_5DAYS.format(symbol=symbol)
            
            cached = await cache_service.get(cache_key)
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
            
            await cache_service.set(cache_key, json.dumps(days_data), cls.CACHE_TTL)
            
        except Exception as e:
            Logger.error(f"5일치 캐시 업데이트 실패 ({symbol}): {e}")
    
    @classmethod
    async def _check_bollinger_signal(cls, symbol: str, current_price: float):
        """볼린저 밴드 기반 시그널 체크"""
        try:
            cache_service = ServiceContainer.get_cache_service()
            
            # 5일치 데이터 가져오기
            cache_key = cls.CACHE_KEY_5DAYS.format(symbol=symbol)
            cached = await cache_service.get(cache_key)
            
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
            await cache_service.set(bollinger_key, json.dumps(bollinger_data), 3600)  # 1시간
            
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
                    result = await db_service.execute_shard_procedure_by_shard_id(
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
            settings_result = await database_service.execute_global_procedure(
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
        """1일 경과한 시그널의 성과 업데이트"""
        try:
            db_service = ServiceContainer.get_database_service()
            cache_service = ServiceContainer.get_cache_service()
            
            # 활성 샤드 목록 조회
            active_shards = await cls._get_active_shard_ids(db_service)
            if not active_shards:
                Logger.warn("활성 샤드가 없어 성과 업데이트 건너뜀")
                return
            
            # 활성 샤드에서만 성과 업데이트 필요한 시그널 처리
            for shard_id in active_shards:
                try:
                    # 어제 발생한 시그널들 조회 및 업데이트
                    result = await db_service.execute_shard_procedure_by_shard_id(
                        shard_id,
                        "fp_signal_performance_update",
                        ()
                    )
                    
                    if result and result[0].get('ErrorCode') == 0:
                        updated_count = result[0].get('updated_count', 0)
                        if updated_count > 0:
                            Logger.info(f"샤드 {shard_id}: {updated_count}개 시그널 성과 업데이트")
                            
                except Exception as e:
                    Logger.error(f"샤드 {shard_id} 성과 업데이트 실패: {e}")
                    continue
            
            Logger.info("모든 시그널 성과 업데이트 완료")
            
        except Exception as e:
            Logger.error(f"시그널 성과 업데이트 실패: {e}")
    
    @classmethod
    async def get_bollinger_data(cls, symbol: str) -> Optional[Dict]:
        """캐시된 볼린저 밴드 데이터 조회"""
        try:
            cache_service = ServiceContainer.get_cache_service()
            bollinger_key = cls.CACHE_KEY_BOLLINGER.format(symbol=symbol)
            
            cached = await cache_service.get(bollinger_key)
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
            
            cached = await cache_service.get(cache_key)
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
            
            cls._monitoring_symbols.clear()
            
            Logger.info("SignalMonitoringService 종료 완료")
            
        except Exception as e:
            Logger.error(f"SignalMonitoringService 종료 실패: {e}")
    
    @classmethod
    def is_initialized(cls) -> bool:
        """초기화 여부 확인"""
        return cls._initialized