import hashlib
import uuid
import json
import time
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor

# 템플릿 기본 클래스
from template.base.template.crawler_template import CrawlerTemplate
from template.base.template_context import TemplateContext
from template.base.template_type import TemplateType

# 직렬화 클래스 (Request/Response)
from template.crawler.common.crawler_serialize import (
    CrawlerExecuteRequest, CrawlerExecuteResponse,
    CrawlerStatusRequest, CrawlerStatusResponse,
    CrawlerHealthRequest, CrawlerHealthResponse,
    CrawlerStopRequest, CrawlerStopResponse,
    CrawlerDataRequest, CrawlerDataResponse,
    CrawlerYahooFinanceRequest, CrawlerYahooFinanceResponse,
    CrawlerScheduleRequest, CrawlerScheduleResponse
)

# 모델 클래스
from template.crawler.common.crawler_model import CrawlerTask, CrawlerData, NewsData

# 서비스 클래스
from service.service_container import ServiceContainer
from service.core.logger import Logger
from service.cache.cache_service import CacheService
from service.search.search_service import SearchService
from service.vectordb.vectordb_service import VectorDbService
from service.external.external_service import ExternalService
from service.scheduler.scheduler_service import SchedulerService
from service.lock.lock_service import LockService
from service.storage.storage_service import StorageService

# 외부 라이브러리
import yfinance as yf
import pandas as pd

class CrawlerTemplateImpl(CrawlerTemplate):
    def __init__(self):
        super().__init__()
        self.v_active_tasks = {}  # task_id -> CrawlerTask
        self.v_processed_hashes = set()  # 처리된 뉴스 해시키 세트
        self.v_news_cache = []  # 수집된 뉴스 캐시
        self.v_scheduler_task_id = None  # 스케줄러 작업 ID
        
    def on_load_data(self, config):
        """크롤러 템플릿 전용 데이터 로딩"""
        try:
            Logger.info("Crawler 템플릿 데이터 로드 시작")
            
            # 캐시에서 기존 해시키 복원
            # self._restore_hash_cache()
            
            # 스케줄러 초기화
            # self._initialize_scheduler()
            
            Logger.info("Crawler 템플릿 데이터 로드 완료")
        except Exception as e:
            Logger.error(f"Crawler 템플릿 데이터 로드 실패: {e}")
            
    def on_client_create(self, db_client, client_session):
        """신규 클라이언트 생성 시 호출"""
        try:
            Logger.info(f"Crawler: 신규 클라이언트 생성")
            # 크롤러는 사용자별 초기화가 필요 없음
        except Exception as e:
            Logger.error(f"Crawler 클라이언트 생성 처리 실패: {e}")
            
    def on_client_update(self, db_client, client_session):
        """클라이언트 업데이트 시 호출"""
        try:
            Logger.info(f"Crawler: 클라이언트 업데이트")
            # 크롤러는 사용자별 업데이트가 필요 없음
        except Exception as e:
            Logger.error(f"Crawler 클라이언트 업데이트 처리 실패: {e}")

    def _restore_hash_cache(self):
        """캐시에서 기존 해시키 복원"""
        try:
            # CacheService 직접 사용 (ServiceContainer.get_cache_service()가 CacheService 클래스를 반환)
            cache_service = ServiceContainer.get_cache_service()
            if cache_service and cache_service.is_initialized():
                # 지난 7일간의 해시키 복원
                v_cache_key = "crawler:processed_hashes"
                
                # get_client()를 통해 클라이언트를 얻고 get_string() 사용
                async def restore_hashes():
                    try:
                        async with cache_service.get_client() as client:
                            v_cached_hashes = await client.get_string(v_cache_key)
                            if v_cached_hashes:
                                self.v_processed_hashes = set(json.loads(v_cached_hashes))
                                Logger.info(f"캐시에서 {len(self.v_processed_hashes)}개 해시키 복원")
                    except Exception as e:
                        Logger.error(f"비동기 해시키 복원 실패: {e}")
                
                # 동기 메서드에서 비동기 호출 처리
                import asyncio
                try:
                    # 현재 실행 중인 이벤트 루프가 있는지 확인
                    loop = asyncio.get_running_loop()
                    # 백그라운드 태스크로 실행 (기다리지 않음)
                    loop.create_task(restore_hashes())
                    Logger.debug("해시키 복원 작업을 백그라운드에서 시작")
                except RuntimeError:
                    # 이벤트 루프가 없는 경우 새로 실행
                    try:
                        asyncio.run(restore_hashes())
                        Logger.debug("해시키 복원 작업 완료")
                    except Exception as run_error:
                        Logger.warn(f"해시키 캐시 복원 실행 실패: {run_error}")
                    
        except Exception as e:
            Logger.error(f"해시키 캐시 복원 실패: {e}")

    def _initialize_scheduler(self):
        """1시간마다 실행되는 스케줄러 초기화"""
        try:
            # SchedulerService를 직접 사용 (ServiceContainer.get_scheduler_service()는 존재하지 않음)
            from service.scheduler.scheduler_service import SchedulerService
            from service.scheduler.base_scheduler import ScheduleJob, ScheduleType
            
            if SchedulerService.is_initialized():
                # 1시간(3600초)마다 크롤링 실행하는 작업 생성
                crawler_job = ScheduleJob(
                    job_id="yahoo_finance_crawler",
                    name="Yahoo Finance 뉴스 크롤링",
                    schedule_type=ScheduleType.INTERVAL,  # 주기적 실행
                    schedule_value=3600,  # 1시간(3600초)
                    callback=self._scheduled_crawling_task,
                    enabled=True,  # 활성화
                    use_distributed_lock=True,  # 분산락 사용
                    lock_key="crawler_yahoo_finance_lock",  # 락 키
                    lock_ttl=1800  # 30분 (크롤링 최대 시간)
                )
                
                # 비동기 작업 추가를 위한 래퍼
                async def add_crawler_job():
                    try:
                        await SchedulerService.add_job(crawler_job)
                        self.v_scheduler_task_id = crawler_job.job_id
                        Logger.info(f"스케줄러 초기화 완료 - Task ID: {self.v_scheduler_task_id}")
                        
                        # 즉시 한 번 실행 (immediate_run 효과)
                        Logger.info("크롤러 즉시 실행 시작")
                        await self._scheduled_crawling_task()
                        
                    except Exception as e:
                        Logger.error(f"스케줄러 작업 추가 실패: {e}")
                
                # 비동기 작업 스케줄링
                import asyncio
                try:
                    # 현재 실행 중인 이벤트 루프가 있는지 확인
                    loop = asyncio.get_running_loop()
                    # 백그라운드 태스크로 실행 (기다리지 않음)
                    loop.create_task(add_crawler_job())
                    Logger.debug("스케줄러 초기화 작업을 백그라운드에서 시작")
                except RuntimeError:
                    # 이벤트 루프가 없는 경우 새로 실행
                    try:
                        asyncio.run(add_crawler_job())
                        Logger.debug("스케줄러 초기화 작업 완료")
                    except Exception as run_error:
                        Logger.warn(f"스케줄러 초기화 실행 실패: {run_error}")
            else:
                Logger.warn("SchedulerService가 초기화되지 않았습니다")
                
        except Exception as e:
            Logger.error(f"스케줄러 초기화 실패: {e}")

    async def _scheduled_crawling_task(self):
        """스케줄러에 의해 호출되는 크롤링 작업"""
        Logger.info("⏰ 스케줄러에 의한 자동 크롤링 시작")
        
        try:
            # 자동 크롤링 요청 생성 (모든 필수 필드를 생성 시점에 제공)
            p_request = CrawlerYahooFinanceRequest(
                task_id=f"scheduled_{int(time.time())}",
                task_type="yahoo_finance_auto",
                symbols=[]  # 전체 심볼 수집
            )
            
            # 크롤링 실행
            await self.on_crawler_yahoo_finance_req(None, p_request)
            
        except Exception as e:
            Logger.error(f"스케줄러 크롤링 작업 실패: {e}")

    def _generate_hash_key(self, p_title: str) -> str:
        """뉴스 제목으로 해시키 생성"""
        try:
            if not p_title or p_title.strip() == '':
                return ''
            return hashlib.md5(p_title.encode('utf-8')).hexdigest()
        except Exception as e:
            Logger.error(f"해시키 생성 실패: {e}")
            return ''

    def _save_hash_cache(self):
        """처리된 해시키를 캐시에 저장"""
        try:
            cache_service = ServiceContainer.get_cache_service()
            if cache_service and cache_service.is_initialized() and self.v_processed_hashes:
                v_cache_key = "crawler:processed_hashes"
                v_hash_list = list(self.v_processed_hashes)
                
                # 비동기 저장 작업
                async def save_hashes():
                    try:
                        async with cache_service.get_client() as client:
                            await client.set_string(v_cache_key, json.dumps(v_hash_list), 604800)  # 7일간 보관
                            Logger.info(f"캐시에 {len(v_hash_list)}개 해시키 저장")
                    except Exception as e:
                        Logger.error(f"비동기 해시키 저장 실패: {e}")
                
                # 비동기 작업 스케줄링
                import asyncio
                try:
                    asyncio.create_task(save_hashes())
                except RuntimeError:
                    Logger.warn("이벤트 루프가 없어 해시키 캐시 저장을 건너뜀")
                    
        except Exception as e:
            Logger.error(f"해시키 캐시 저장 실패: {e}")

    async def on_crawler_yahoo_finance_req(self, client_session, request: CrawlerYahooFinanceRequest):
        """Yahoo Finance 뉴스 수집 요청 처리"""
        response = CrawlerYahooFinanceResponse()
        response.sequence = request.sequence
        
        Logger.info(f"Yahoo Finance 뉴스 수집 요청 수신: {request.task_id}")
        
        try:
            # 1. 중복 실행 방지 (Lock 사용)
            v_lock_key = f"crawler_yahoo_finance_{request.task_id}"
            lock_service = ServiceContainer.get_lock_service()
            v_lock_token = None
            
            if lock_service:
                v_lock_token = await lock_service.acquire(v_lock_key, ttl=7200, timeout=5)
                if not v_lock_token:
                    response.errorCode = 5001  # Crawler 에러 코드 시작
                    response.message = "다른 크롤링 작업이 진행 중입니다"
                    Logger.warn(f"Lock 획득 실패: {v_lock_key}")
                    return response
            
            # 2. Yahoo Finance 데이터 수집
            v_collected_news = await self._collect_yahoo_finance_data(request)
            
            # 3. 중복 제거 처리
            v_filtered_news = await self._process_duplicate_removal(v_collected_news)
            
            # 4. OpenSearch에 저장
            v_opensearch_result = await self._store_to_opensearch(v_filtered_news, request.task_id)
            
            # 5. VectorDB에 저장 (S3 업로드 + Knowledge Base 동기화)
            v_vectordb_result = await self._store_to_vectordb(v_filtered_news, request.task_id)
            
            # 6. 캐시 업데이트
            self._save_hash_cache()
            
            # 7. 성공 응답 설정
            response.errorCode = 0
            response.task_id = request.task_id
            response.collected_count = len(v_collected_news)
            response.new_count = len(v_filtered_news)
            response.duplicate_count = len(v_collected_news) - len(v_filtered_news)
            response.opensearch_stored = v_opensearch_result.get('success', False)
            response.vectordb_stored = v_vectordb_result.get('success', False)
            response.message = "Yahoo Finance 뉴스 수집 완료"
            
            Logger.info(f"Yahoo Finance 수집 완료: 총 {response.collected_count}개, 신규 {response.new_count}개")
            
        except Exception as e:
            response.errorCode = 5000  # 서버 오류
            response.message = "뉴스 수집 중 오류 발생"
            Logger.error(f"Yahoo Finance 수집 오류: {e}")
        
        finally:
            # Lock 해제
            if v_lock_token and lock_service:
                try:
                    await lock_service.release(v_lock_key, v_lock_token)
                except Exception as e:
                    Logger.error(f"Lock 해제 실패: {e}")
        
        return response

    async def _collect_yahoo_finance_data(self, p_request: CrawlerYahooFinanceRequest) -> List[NewsData]:
        """Yahoo Finance에서 뉴스 데이터 수집"""
        Logger.info("Yahoo Finance 뉴스 수집 시작")
        
        try:
            # 수집할 심볼 리스트 (기본값 또는 요청에서 지정)
            v_symbols = p_request.symbols if p_request.symbols else [# 대형 테크주 (FAANG+)
         "AAPL", "MSFT", "GOOG", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "NFLX", "ORCL", "CRM", "ADBE", "INTC", "AMD", "CSCO", "IBM",
    
    # 반도체
    "QCOM", "AVGO", "TXN", "MU", "AMAT", "LRCX", "ADI", "MCHP", "KLAC", "MRVL",
    
    # 주요 ETF들
    "SPY", "QQQ", "VTI", "IWM", "VEA", "VWO", "EFA", "GLD", "SLV", "TLT", "HYG", "LQD", "XLF", "XLK", "XLE", "XLV", "XLI", "XLP", "XLU", "XLRE",
    
    # 금융 (은행, 보험, 핀테크)
    "JPM", "BAC", "WFC", "C", "GS", "MS", "BRK-B", "V", "MA", "PYPL", "SQ", "AXP", "USB", "PNC", "TFC", "COF",
    
    # 헬스케어/제약
    "JNJ", "PFE", "UNH", "ABBV", "MRK", "TMO", "ABT", "DHR", "BMY", "AMGN", "GILD", "BIIB", "CVS", "CI", "ANTM", "HUM",
    
    # 소비재 (필수/임의)
    "PG", "KO", "PEP", "WMT", "HD", "MCD", "NKE", "SBUX", "TGT", "LOW", "COST", "DIS", "BABA", "AMZN", "EBAY", "ETSY",
    
    # 에너지
    "XOM", "CVX", "COP", "EOG", "SLB", "PSX", "VLO", "KMI", "OKE", "WMB",
    
    # 산업재/항공
    "BA", "CAT", "DE", "GE", "HON", "MMM", "UPS", "FDX", "LMT", "RTX", "AAL", "DAL", "UAL", "LUV",
    
    # 통신
    "VZ", "T", "TMUS", "CHTR", "CMCSA", "DISH",
    
    # 자동차
    "F", "GM", "RIVN", "LCID", "NIO", "XPEV", "LI",
    
    # 부동산 REITs
    "AMT", "PLD", "CCI", "EQIX", "SPG", "O", "WELL", "EXR", "AVB", "EQR",
    
    # 유틸리티
    "NEE", "DUK", "SO", "D", "AEP", "EXC", "XEL", "SRE", "PEG", "ED",
    
    # 엔터테인먼트/미디어
    "DIS", "NFLX", "ROKU", "SPOT", "WBD", "PARA", "FOX", "FOXA",
    
    # 중국 ADR
    "BABA", "JD", "PDD", "BIDU", "BILI", "DIDI", "TME",
    
    # 암호화폐 관련
    "COIN", "MSTR", "RIOT", "MARA", "BITB", "IBIT",
    
    # 기타 주요 기업들
    "TSLA", "UBER", "LYFT", "SNAP", "TWTR", "ZOOM", "DOCU", "PLTR", "SNOW", "CRM", "WORK", "ZM", "PTON", "ARKK", "ARKG", "ARKW"
    ]
            
            v_collected_news = []
            v_total_symbols = len(v_symbols)
            v_processed_symbols = 0
            
            for v_symbol in v_symbols:
                try:
                    v_processed_symbols += 1
                    Logger.info(f"[{v_processed_symbols}/{v_total_symbols}] {v_symbol} 뉴스 수집 중...")
                    
                    # yfinance로 뉴스 수집 (스레드풀에서 실행)
                    loop = asyncio.get_running_loop()
                    v_ticker = await loop.run_in_executor(None, yf.Ticker, v_symbol)
                    v_news_list = await loop.run_in_executor(None, lambda: v_ticker.news)
                    
                    if not v_news_list:
                        Logger.info(f"{v_symbol}: 뉴스 없음")
                        continue
                    
                    # 뉴스 파싱
                    v_parsed_count = 0
                    for v_news_item in v_news_list:
                        try:
                            v_parsed_news = self._parse_yahoo_news_item(v_news_item, v_symbol)
                            if v_parsed_news:
                                v_collected_news.append(v_parsed_news)
                                v_parsed_count += 1
                        except Exception as e:
                            Logger.error(f"뉴스 파싱 오류: {e}")
                            continue
                    
                    Logger.info(f"{v_symbol}: {v_parsed_count}개 뉴스 수집 완료")
                    await asyncio.sleep(0.5)  # API 호출 간격 조절
                    
                except Exception as e:
                    Logger.error(f"{v_symbol} 수집 오류: {e}")
                    continue
            
            Logger.info(f"총 {len(v_collected_news)}개 뉴스 수집 완료")
            return v_collected_news
            
        except Exception as e:
            Logger.error(f"Yahoo Finance 데이터 수집 실패: {e}")
            return []

    def _parse_yahoo_news_item(self, p_news_item: dict, p_symbol: str) -> NewsData:
        """Yahoo Finance 뉴스 아이템 파싱"""
        try:
            if not p_news_item or not isinstance(p_news_item, dict):
                return None
            
            v_content = p_news_item.get('content', {})
            if not v_content or not isinstance(v_content, dict):
                return None
            
            # 제목 추출
            v_title = v_content.get('title', '').strip()
            if not v_title or v_title == 'N/A':
                return None
            
            # 일주일 이내 뉴스만 필터링
            v_pub_date_str = v_content.get('pubDate', '')
            v_formatted_date = self._parse_and_filter_date(v_pub_date_str)
            if not v_formatted_date:
                return None  # 오래된 뉴스 제외
            
            # 기타 정보 추출
            v_provider = v_content.get('provider', {})
            v_click_url = v_content.get('clickThroughUrl', {})
            
            # NewsData 객체 생성
            v_news_data = NewsData(
                data_id=str(uuid.uuid4()),
                title=v_title,
                ticker=p_symbol,
                date=v_formatted_date,
                source=v_provider.get('displayName', 'Yahoo Finance') if isinstance(v_provider, dict) else 'Yahoo Finance',
                link=v_click_url.get('url', 'N/A') if isinstance(v_click_url, dict) else 'N/A',
                collected_at=datetime.now().isoformat()
            )
            
            return v_news_data
            
        except Exception as e:
            Logger.error(f"뉴스 아이템 파싱 오류: {e}")
            return None

    def _parse_and_filter_date(self, p_date_str: str) -> str:
        """날짜 파싱 및 일주일 이내 필터링"""
        try:
            if not p_date_str:
                return None
            
            # 날짜 파싱
            v_pub_date = pd.to_datetime(p_date_str)
            if v_pub_date.tz is None:
                v_pub_date = v_pub_date.tz_localize('UTC')
            
            # 일주일 이내 체크
            v_now = datetime.now()
            if v_now.tzinfo is None:
                v_now = v_now.replace(tzinfo=v_pub_date.tzinfo)
            
            v_one_week_ago = v_now - timedelta(days=7)
            if v_pub_date < v_one_week_ago:
                return None  # 오래된 뉴스
            
            return v_pub_date.strftime('%Y-%m-%d %H:%M')
            
        except Exception as e:
            Logger.error(f"날짜 파싱 오류: {e}")
            return datetime.now().strftime('%Y-%m-%d %H:%M')

    async def _process_duplicate_removal(self, p_news_list: List[NewsData]) -> List[NewsData]:
        """뉴스 중복 제거 처리"""
        Logger.info(f"뉴스 중복 제거 처리 시작: {len(p_news_list)}개")
        
        try:
            v_filtered_news = []
            v_new_count = 0
            v_duplicate_count = 0
            
            for v_news in p_news_list:
                # 해시키 생성
                v_hash_key = self._generate_hash_key(v_news.title)
                if not v_hash_key:
                    continue
                
                # 중복 체크
                if v_hash_key in self.v_processed_hashes:
                    v_duplicate_count += 1
                    Logger.debug(f"중복 뉴스 제외: {v_news.title[:50]}...")
                else:
                    # 새 뉴스 추가
                    self.v_processed_hashes.add(v_hash_key)
                    v_filtered_news.append(v_news)
                    v_new_count += 1
                    Logger.debug(f"새 뉴스 추가: {v_news.title[:50]}...")
            
            Logger.info(f"중복 제거 완료: 새 뉴스 {v_new_count}개, 중복 {v_duplicate_count}개")
            return v_filtered_news
            
        except Exception as e:
            Logger.error(f"중복 제거 처리 실패: {e}")
            return []

    async def _store_to_opensearch(self, p_news_list: List[NewsData], p_task_id: str) -> Dict[str, Any]:
        """OpenSearch에 뉴스 데이터 저장"""
        Logger.info(f"OpenSearch에 {len(p_news_list)}개 뉴스 저장 시작")
        
        try:
            if not SearchService.is_initialized():
                Logger.warn("SearchService가 초기화되지 않음")
                return {'success': False, 'error': 'SearchService not initialized'}
            
            v_index_name = 'yahoo_finance_news'
            v_successful_count = 0
            v_failed_count = 0
            
            # 인덱스 생성 (없는 경우)
            await self._ensure_opensearch_index(v_index_name)
            
            # 각 뉴스를 OpenSearch에 저장
            for v_news in p_news_list:
                try:
                    v_doc = {
                        'task_id': p_task_id,
                        'ticker': v_news.ticker,
                        'title': v_news.title,
                        'source': v_news.source,
                        'date': v_news.date,
                        'link': v_news.link,
                        'collected_at': v_news.collected_at,
                        'created_at': datetime.now().isoformat(),
                        'content_type': 'yahoo_finance_news'
                    }
                    
                    v_result = await SearchService.index_document(
                        index=v_index_name,
                        document=v_doc,
                        doc_id=v_news.data_id
                    )
                    
                    if v_result.get('success', False):
                        v_successful_count += 1
                    else:
                        v_failed_count += 1
                        Logger.warn(f"OpenSearch 저장 실패: {v_result.get('error', 'Unknown')}")
                        
                except Exception as e:
                    v_failed_count += 1
                    Logger.error(f"OpenSearch 개별 저장 오류: {e}")
            
            Logger.info(f"OpenSearch 저장 완료: 성공 {v_successful_count}개, 실패 {v_failed_count}개")
            return {
                'success': v_successful_count > 0,
                'successful_count': v_successful_count,
                'failed_count': v_failed_count
            }
            
        except Exception as e:
            Logger.error(f"OpenSearch 저장 실패: {e}")
            return {'success': False, 'error': str(e)}

    async def _ensure_opensearch_index(self, p_index_name: str):
        """OpenSearch 인덱스 생성 확인"""
        try:
            v_index_check = await SearchService.index_exists(p_index_name)
            if not v_index_check.get('exists', False):
                Logger.info(f"OpenSearch 인덱스 생성: {p_index_name}")
                
                v_mappings = {
                    "properties": {
                        "task_id": {"type": "keyword"},
                        "ticker": {"type": "keyword"},
                        "title": {
                            "type": "text",
                            "analyzer": "standard",
                            "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}
                        },
                        "source": {"type": "keyword"},
                        "date": {"type": "date", "format": "yyyy-MM-dd HH:mm||yyyy-MM-dd||epoch_millis"},
                        "link": {"type": "keyword", "index": False},
                        "collected_at": {"type": "date"},
                        "created_at": {"type": "date"},
                        "content_type": {"type": "keyword"}
                    }
                }
                
                await SearchService.create_index(index=p_index_name, mappings=v_mappings)
                
        except Exception as e:
            Logger.error(f"OpenSearch 인덱스 생성 실패: {e}")

    async def _store_to_vectordb(self, p_news_list: List[NewsData], p_task_id: str) -> Dict[str, Any]:
        """VectorDB에 뉴스 데이터 저장 (S3 업로드 + Knowledge Base 동기화)"""
        Logger.info(f"VectorDB(Knowledge Base)에 {len(p_news_list)}개 뉴스 저장 시작")
        
        try:
            # 1. VectorDB 서비스 초기화 확인
            if not VectorDbService.is_initialized():
                Logger.warn("VectorDbService가 초기화되지 않음")
                return {'success': False, 'error': 'VectorDbService not initialized'}
            
            # 2. Storage 서비스 초기화 확인
            if not StorageService.is_initialized():
                Logger.warn("StorageService가 초기화되지 않음")
                return {'success': False, 'error': 'StorageService not initialized'}
            
            # 3. Knowledge Base 상태 확인
            v_kb_status = await VectorDbService.get_knowledge_base_status()
            if not v_kb_status.get('success', False):
                Logger.error(f"Knowledge Base 상태 확인 실패: {v_kb_status.get('error', 'Unknown')}")
                return {'success': False, 'error': f"Knowledge Base unavailable: {v_kb_status.get('error', 'Unknown')}"}
            
            Logger.info(f"Knowledge Base 상태: {v_kb_status.get('status', 'Unknown')}")
            
            # 4. 뉴스 데이터를 JSON 형식으로 변환
            v_json_documents = []
            for v_news in p_news_list:
                try:
                    # Knowledge Base 친화적인 텍스트 구성
                    v_content_text = f"""
Title: {v_news.title}
Ticker: {v_news.ticker}
Source: {v_news.source}
Date: {v_news.date}
URL: {v_news.link}
Content Type: Financial News
Task ID: {p_task_id}
Collected At: {v_news.collected_at}

This is a financial news article about {v_news.ticker} from {v_news.source}. 
The news title is: {v_news.title}
Published on: {v_news.date}
"""
                    
                    v_json_doc = {
                        "id": v_news.data_id,
                        "title": v_news.title,
                        "content": v_news.title,
                        "metadata": {
                            "ticker": v_news.ticker,
                            "source": v_news.source,
                            "date": v_news.date,
                            "url": v_news.link,
                            "task_id": p_task_id,
                            "content_type": "yahoo_finance_news",
                            "collected_at": v_news.collected_at
                        }
                    }
                    v_json_documents.append(v_json_doc)
                    
                except Exception as e:
                    Logger.error(f"뉴스 JSON 변환 오류: {e}")
                    continue
            
            if not v_json_documents:
                return {'success': False, 'error': 'No valid documents to upload'}
            
            # 5. S3에 JSON 파일 업로드
            v_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # S3 업로드 (설정에서 버킷 이름 가져오기)
            try:
                # VectorDB 설정 가져오기
                v_vectordb_config = VectorDbService._config
                if not v_vectordb_config:
                    raise ValueError("VectorDB config not available")
                
                v_s3_bucket = getattr(v_vectordb_config, 's3_bucket', None)
                if not v_s3_bucket:
                    raise ValueError("S3 bucket not configured in VectorDB settings")
                
                v_s3_prefix = getattr(v_vectordb_config, 's3_prefix', 'knowledge-base-data/')
                v_s3_key = f"{v_s3_prefix}yahoo_finance_news/{p_task_id}_{v_timestamp}.json"
                
            except Exception as e:
                Logger.error(f"VectorDB 설정 가져오기 실패: {e}")
                return {'success': False, 'error': f"VectorDB configuration error: {e}"}
            
            # 임시 파일에 JSON 데이터 저장
            import tempfile
            import json
            import os
            
            v_temp_file = None
            try:
                # JSON 데이터 객체 생성 (AWS Bedrock Knowledge Base용 직접 배열)
                v_upload_data = v_json_documents
                
                # 임시 파일에 저장
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
                    json.dump(v_upload_data, f, ensure_ascii=False, indent=2)
                    v_temp_file = f.name
                
                # S3 업로드 (설정에서 가져온 버킷명 사용)
                v_upload_result = await StorageService.upload_file(
                    bucket=v_s3_bucket,
                    key=v_s3_key,
                    file_path=v_temp_file,
                    extra_args={
                        'ContentType': 'application/json',
                        'Metadata': {
                            'task_id': p_task_id,
                            'content_type': 'yahoo_finance_news',
                            'document_count': str(len(v_json_documents))
                        }
                    }
                )
                
                if not v_upload_result.get('success', False):
                    Logger.error(f"S3 업로드 실패: {v_upload_result.get('error', 'Unknown')}")
                    return {'success': False, 'error': f"S3 upload failed: {v_upload_result.get('error', 'Unknown')}"}
                
                Logger.info(f"S3 업로드 성공: s3://{v_s3_bucket}/{v_s3_key}")
                
            finally:
                # 임시 파일 정리
                if v_temp_file and os.path.exists(v_temp_file):
                    try:
                        os.unlink(v_temp_file)
                    except Exception as e:
                        Logger.warn(f"임시 파일 삭제 실패: {e}")
            
            # 6. Knowledge Base 동기화 시작
            try:
                v_data_source_id = getattr(v_vectordb_config, 'data_source_id', None)
                if not v_data_source_id:
                    Logger.warn("Data source ID not configured - skipping Knowledge Base sync")
                    return {
                        'success': True,  # S3 업로드는 성공
                        'uploaded_documents': len(v_json_documents),
                        's3_bucket': v_s3_bucket,
                        's3_key': v_s3_key,
                        'ingestion_job_id': None,
                        'ingestion_error': 'Data source ID not configured',
                        'message': f'Uploaded {len(v_json_documents)} documents to S3 but skipped Knowledge Base sync (data_source_id not configured)'
                    }
                
            except Exception as e:
                Logger.error(f"데이터 소스 ID 가져오기 실패: {e}")
                return {'success': False, 'error': f"Data source configuration error: {e}"}
            
            # 🔍 Knowledge Base 동기화 시작 (디버깅 로그 추가)
            Logger.info(f"🚀 Knowledge Base 동기화 시작 준비: data_source_id = {v_data_source_id}")
            Logger.info(f"📊 VectorDbService 초기화 상태: {VectorDbService.is_initialized()}")
            
            try:
                Logger.info("🔄 VectorDbService.start_ingestion_job 호출 시작...")
                v_ingestion_result = await VectorDbService.start_ingestion_job(v_data_source_id)
                Logger.info(f"✅ VectorDbService.start_ingestion_job 호출 완료: {v_ingestion_result}")
                
            except Exception as ingestion_error:
                Logger.error(f"❌ start_ingestion_job 호출 중 에러 발생: {ingestion_error}")
                Logger.error(f"📋 에러 타입: {type(ingestion_error).__name__}")
                import traceback
                Logger.error(f"🔍 상세 스택 트레이스: {traceback.format_exc()}")
                
                # S3 업로드는 성공했지만 ingestion job 실패
                return {
                    'success': True,  # S3 업로드는 성공
                    'uploaded_documents': len(v_json_documents),
                    's3_bucket': v_s3_bucket,
                    's3_key': v_s3_key,
                    'ingestion_job_id': None,
                    'ingestion_error': f"Ingestion job failed: {str(ingestion_error)}",
                    'message': f'Uploaded {len(v_json_documents)} documents to S3 but failed to start Knowledge Base sync due to error'
                }
            
            if v_ingestion_result.get('success', False):
                v_job_id = v_ingestion_result.get('job_id', '')
                Logger.info(f"Knowledge Base 동기화 시작: Job ID = {v_job_id}")
                
                return {
                    'success': True,
                    'uploaded_documents': len(v_json_documents),
                    's3_bucket': v_s3_bucket,
                    's3_key': v_s3_key,
                    'ingestion_job_id': v_job_id,
                    'ingestion_status': v_ingestion_result.get('status', 'STARTING'),
                    'message': f'Successfully uploaded {len(v_json_documents)} documents to S3 and started Knowledge Base sync'
                }
            else:
                # S3 업로드는 성공했지만 동기화 실패
                Logger.warn(f"Knowledge Base 동기화 시작 실패: {v_ingestion_result.get('error', 'Unknown')}")
                return {
                    'success': True,  # S3 업로드는 성공
                    'uploaded_documents': len(v_json_documents),
                    's3_bucket': v_s3_bucket,
                    's3_key': v_s3_key,
                    'ingestion_job_id': None,
                    'ingestion_error': v_ingestion_result.get('error', 'Unknown'),
                    'message': f'Uploaded {len(v_json_documents)} documents to S3 but failed to start Knowledge Base sync'
                }
            
        except Exception as e:
            Logger.error(f"VectorDB 저장 실패: {e}")
            return {'success': False, 'error': str(e)}

    async def check_vectordb_connection(self) -> Dict[str, Any]:
        """VectorDB(Knowledge Base) 연결 및 설정 상태 확인"""
        Logger.info("VectorDB 연결 상태 확인 시작")
        
        try:
            # 1. VectorDB 서비스 초기화 확인
            if not VectorDbService.is_initialized():
                return {
                    'success': False,
                    'error': 'VectorDbService not initialized',
                    'details': {
                        'vectordb_service': False,
                        'storage_service': StorageService.is_initialized() if 'StorageService' in globals() else False
                    }
                }
            
            # 2. 설정 확인
            v_vectordb_config = VectorDbService._config
            v_config_check = {
                'config_available': v_vectordb_config is not None,
                'knowledge_base_id': getattr(v_vectordb_config, 'knowledge_base_id', None),
                'data_source_id': getattr(v_vectordb_config, 'data_source_id', None),
                's3_bucket': getattr(v_vectordb_config, 's3_bucket', None),
                's3_prefix': getattr(v_vectordb_config, 's3_prefix', 'knowledge-base-data/'),
                'region_name': getattr(v_vectordb_config, 'region_name', 'unknown'),
                'embedding_model': getattr(v_vectordb_config, 'embedding_model', 'unknown')
            }
            
            # 3. Knowledge Base 상태 확인
            v_kb_status = await VectorDbService.get_knowledge_base_status()
            
            # 4. Storage Service 확인
            v_storage_available = StorageService.is_initialized()
            
            return {
                'success': True,
                'services': {
                    'vectordb_service': True,
                    'storage_service': v_storage_available,
                    'knowledge_base_accessible': v_kb_status.get('success', False)
                },
                'configuration': v_config_check,
                'knowledge_base': {
                    'status': v_kb_status.get('status', 'unknown'),
                    'name': v_kb_status.get('name', 'unknown'),
                    'error': v_kb_status.get('error') if not v_kb_status.get('success') else None
                },
                'ready_for_upload': all([
                    v_vectordb_config is not None,
                    v_config_check['s3_bucket'] is not None,
                    v_storage_available,
                    v_kb_status.get('success', False)
                ]),
                'ready_for_sync': all([
                    v_config_check['data_source_id'] is not None,
                    v_kb_status.get('success', False)
                ])
            }
            
        except Exception as e:
            Logger.error(f"VectorDB 연결 상태 확인 실패: {e}")
            return {
                'success': False,
                'error': str(e),
                'services': {
                    'vectordb_service': VectorDbService.is_initialized(),
                    'storage_service': StorageService.is_initialized() if 'StorageService' in globals() else False
                }
            }

    async def on_crawler_execute_req(self, client_session, request: CrawlerExecuteRequest):
        """크롤러 작업 실행 요청 처리"""
        response = CrawlerExecuteResponse()
        response.sequence = request.sequence
        
        Logger.info(f"크롤러 실행 요청 수신: {request.task_type}")
        
        try:
            # Yahoo Finance 크롤링으로 리다이렉트
            if request.task_type == "yahoo_finance":
                v_yahoo_request = CrawlerYahooFinanceRequest()
                v_yahoo_request.task_id = request.task_id
                v_yahoo_request.task_type = request.task_type
                v_yahoo_request.symbols = request.parameters.get('symbols', []) if request.parameters else []
                
                v_yahoo_response = await self.on_crawler_yahoo_finance_req(client_session, v_yahoo_request)
                
                response.errorCode = v_yahoo_response.errorCode
                response.task_id = v_yahoo_response.task_id
                response.status = "completed" if v_yahoo_response.errorCode == 0 else "failed"
                response.message = v_yahoo_response.message
                response.started_at = datetime.now().isoformat()
                response.lock_acquired = True
            else:
                response.errorCode = 5002
                response.message = f"지원하지 않는 작업 타입: {request.task_type}"
                
        except Exception as e:
            response.errorCode = 5000
            response.message = "크롤러 실행 중 오류 발생"
            Logger.error(f"크롤러 실행 오류: {e}")
        
        return response

    async def on_crawler_status_req(self, client_session, request: CrawlerStatusRequest):
        """크롤러 상태 조회 요청 처리"""
        response = CrawlerStatusResponse()
        response.sequence = request.sequence
        
        Logger.info("크롤러 상태 조회 요청 수신")
        
        try:
            v_tasks = []
            
            # 활성 작업 정보 구성
            for v_task_id, v_task in self.v_active_tasks.items():
                if request.task_id and v_task_id != request.task_id:
                    continue
                if request.status and v_task.status != request.status:
                    continue
                
                v_tasks.append({
                    "task_id": v_task_id,
                    "task_type": v_task.task_type,
                    "status": v_task.status,
                    "started_at": v_task.started_at,
                    "completed_at": getattr(v_task, 'completed_at', None)
                })
            
            # 제한 적용
            if request.limit and request.limit > 0:
                v_tasks = v_tasks[:request.limit]
            
            response.errorCode = 0
            response.tasks = v_tasks
            response.total_count = len(v_tasks)
            response.scheduler_active = self.v_scheduler_task_id is not None
            response.processed_hashes_count = len(self.v_processed_hashes)
            
            Logger.info(f"크롤러 상태 조회 완료: {len(v_tasks)}개 작업")
            
        except Exception as e:
            response.errorCode = 5000
            response.message = "상태 조회 중 오류 발생"
            Logger.error(f"크롤러 상태 조회 오류: {e}")
        
        return response

    async def on_crawler_health_req(self, client_session, request: CrawlerHealthRequest):
        """크롤러 헬스체크 요청 처리"""
        response = CrawlerHealthResponse()
        response.sequence = request.sequence
        
        Logger.info("크롤러 헬스체크 요청 수신")
        
        try:
            response.errorCode = 0
            response.status = "healthy"
            response.timestamp = datetime.now().isoformat()
            response.active_tasks = len([t for t in self.v_active_tasks.values() if t.status == "running"])
            response.processed_hashes_count = len(self.v_processed_hashes)
            response.scheduler_active = self.v_scheduler_task_id is not None
            
            # 서비스 상태 체크
            if request.check_services:
                v_services = {}
                v_services["cache_service"] = ServiceContainer.get_cache_service() is not None
                v_services["search_service"] = SearchService.is_initialized()
                v_services["vectordb_service"] = VectorDbService.is_initialized()
                v_services["scheduler_service"] = SchedulerService.is_initialized()
                response.services = v_services
            
            Logger.info(f"크롤러 헬스체크 완료: {response.status}")
            
        except Exception as e:
            response.errorCode = 5000
            response.status = "unhealthy"
            response.message = "헬스체크 중 오류 발생"
            Logger.error(f"크롤러 헬스체크 오류: {e}")
        
        return response

    async def on_crawler_data_req(self, client_session, request: CrawlerDataRequest):
        """크롤러 데이터 조회 요청 처리"""
        response = CrawlerDataResponse()
        response.sequence = request.sequence
        
        Logger.info("크롤러 데이터 조회 요청 수신")
        
        try:
            v_filtered_news = []
            
            # 캐시에서 뉴스 데이터 조회
            for v_news in self.v_news_cache:
                if request.task_id and hasattr(v_news, 'task_id') and v_news.task_id != request.task_id:
                    continue
                v_filtered_news.append(v_news)
            
            # 제한 적용
            if request.limit and request.limit > 0:
                v_limited_news = v_filtered_news[:request.limit]
            else:
                v_limited_news = v_filtered_news
            
            # 응답 데이터 구성
            v_response_data = []
            for i, v_news in enumerate(v_limited_news):
                v_news_item = {
                    "news_index": i + 1,
                    "title": getattr(v_news, 'title', 'N/A'),
                    "ticker": getattr(v_news, 'ticker', 'N/A'),
                    "date": getattr(v_news, 'date', 'N/A'),
                    "source": getattr(v_news, 'source', 'N/A'),
                    "link": getattr(v_news, 'link', 'N/A'),
                    "collected_at": getattr(v_news, 'collected_at', 'N/A')
                }
                v_response_data.append(v_news_item)
            
            response.errorCode = 0
            response.data = v_response_data
            response.total_count = len(v_filtered_news)
            
            Logger.info(f"크롤러 데이터 조회 완료: {len(v_limited_news)}개 뉴스 반환")
            
        except Exception as e:
            response.errorCode = 5000
            response.message = "데이터 조회 중 오류 발생"
            Logger.error(f"크롤러 데이터 조회 오류: {e}")
        
        return response

    # 기존 메서드들은 호환성을 위해 유지하되 deprecated 표시
    async def on_crawler_stop_req(self, client_session, request: CrawlerStopRequest):
        """크롤러 작업 중단 요청 처리 (Deprecated)"""
        response = CrawlerStopResponse()
        response.sequence = request.sequence
        response.task_id = request.task_id
        response.stopped = True
        response.message = "크롤러는 스케줄러 기반으로 동작하므로 개별 중단이 불가능합니다"
        return response

    # ============================================================================
    # 저장 확인 메서드들 (OpenSearch & VectorDB 저장 검증)
    # ============================================================================

    async def verify_opensearch_storage(self, p_task_id: str = None, p_limit: int = 10) -> Dict[str, Any]:
        """OpenSearch 저장 확인"""
        Logger.info("OpenSearch 저장 확인 시작")
        
        try:
            if not SearchService.is_initialized():
                return {'success': False, 'error': 'SearchService not available'}
            
            v_index_name = 'yahoo_finance_news'
            
            # 인덱스 존재 확인
            v_index_check = await SearchService.index_exists(v_index_name)
            if not v_index_check.get('exists', False):
                return {'success': False, 'error': f'Index {v_index_name} does not exist'}
            
            # 문서 수 조회
            v_count_query = {"query": {"match_all": {}}}
            if p_task_id:
                v_count_query = {"query": {"term": {"task_id": p_task_id}}}
            
            v_count_result = await SearchService.count_documents(v_index_name, v_count_query)
            v_total_count = v_count_result.get('count', 0) if v_count_result.get('success') else 0
            
            # 최근 문서 조회
            v_search_query = {
                "query": v_count_query["query"],
                "sort": [{"created_at": {"order": "desc"}}],
                "size": p_limit
            }
            
            v_search_result = await SearchService.search_documents(v_index_name, v_search_query)
            v_documents = v_search_result.get('documents', []) if v_search_result.get('success') else []
            
            Logger.info(f"OpenSearch 확인 완료: 총 {v_total_count}개 문서, 최근 {len(v_documents)}개 조회")
            
            return {
                'success': True,
                'index_name': v_index_name,
                'total_count': v_total_count,
                'recent_documents': v_documents,
                'sample_titles': [doc.get('_source', {}).get('title', 'N/A') for doc in v_documents[:5]]
            }
            
        except Exception as e:
            Logger.error(f"OpenSearch 저장 확인 실패: {e}")
            return {'success': False, 'error': str(e)}

    async def verify_vectordb_storage(self, p_task_id: str = None, p_limit: int = 10) -> Dict[str, Any]:
        """VectorDB(Knowledge Base) 저장 확인"""
        Logger.info("VectorDB(Knowledge Base) 저장 확인 시작")
        
        try:
            if not VectorDbService.is_initialized():
                return {'success': False, 'error': 'VectorDbService not available'}
            
            # 1. Knowledge Base 상태 확인
            v_kb_status = await VectorDbService.get_knowledge_base_status()
            if not v_kb_status.get('success', False):
                return {
                    'success': False, 
                    'error': 'Knowledge Base not available',
                    'kb_error': v_kb_status.get('error', 'Unknown')
                }
            
            # 2. Knowledge Base에서 뉴스 검색
            v_search_queries = [
                "financial news",
                "yahoo finance news", 
                "stock market news"
            ]
            
            v_all_documents = []
            v_search_results = {}
            
            for v_query in v_search_queries:
                try:
                    v_search_result = await VectorDbService.similarity_search(
                        query=v_query,
                        top_k=p_limit
                    )
                    
                    if v_search_result.get('success'):
                        v_docs = v_search_result.get('results', [])
                        v_search_results[v_query] = len(v_docs)
                        v_all_documents.extend(v_docs)
                    else:
                        v_search_results[v_query] = 0
                        Logger.warn(f"검색 실패 ({v_query}): {v_search_result.get('error', 'Unknown')}")
                        
                except Exception as e:
                    v_search_results[v_query] = 0
                    Logger.error(f"검색 오류 ({v_query}): {e}")
            
            # 3. 중복 제거 및 통계 수집
            v_unique_docs = {}
            for v_doc in v_all_documents:
                v_content = v_doc.get('content', '')
                if v_content and len(v_content) > 10:  # 최소 길이 체크
                    v_doc_hash = hashlib.md5(v_content.encode()).hexdigest()
                    if v_doc_hash not in v_unique_docs:
                        v_unique_docs[v_doc_hash] = v_doc
            
            v_unique_documents = list(v_unique_docs.values())
            
            # 4. 샘플 제목 추출
            v_sample_titles = []
            v_ticker_counts = {}
            
            for v_doc in v_unique_documents[:10]:  # 상위 10개만
                v_content = v_doc.get('content', '')
                
                # 제목 추출 시도
                v_title = 'N/A'
                if 'Title:' in v_content:
                    v_lines = v_content.split('\n')
                    for v_line in v_lines:
                        if v_line.strip().startswith('Title:'):
                            v_title = v_line.replace('Title:', '').strip()
                            break
                
                v_sample_titles.append(v_title)
                
                # 티커 카운트
                if 'Ticker:' in v_content:
                    v_lines = v_content.split('\n')
                    for v_line in v_lines:
                        if v_line.strip().startswith('Ticker:'):
                            v_ticker = v_line.replace('Ticker:', '').strip()
                            v_ticker_counts[v_ticker] = v_ticker_counts.get(v_ticker, 0) + 1
                            break
            
            Logger.info(f"VectorDB 확인 완료: {len(v_unique_documents)}개 고유 문서 발견")
            
            return {
                'success': True,
                'knowledge_base_id': v_kb_status.get('knowledge_base_id', 'Unknown'),
                'knowledge_base_status': v_kb_status.get('status', 'Unknown'),
                'knowledge_base_name': v_kb_status.get('name', 'Unknown'),
                'total_documents_found': len(v_unique_documents),
                'search_results_by_query': v_search_results,
                'sample_titles': v_sample_titles[:5],
                'top_tickers': dict(sorted(v_ticker_counts.items(), key=lambda x: x[1], reverse=True)[:5]),
                'kb_created_at': v_kb_status.get('created_at'),
                'kb_updated_at': v_kb_status.get('updated_at'),
                'operation_time': v_kb_status.get('operation_time', 0)
            }
            
        except Exception as e:
            Logger.error(f"VectorDB 저장 확인 실패: {e}")
            return {'success': False, 'error': str(e)}

    async def verify_storage_health(self, p_task_id: str = None) -> Dict[str, Any]:
        """전체 저장소 상태 확인 (OpenSearch + VectorDB)"""
        Logger.info("전체 저장소 상태 확인 시작")
        
        try:
            # OpenSearch 확인
            v_opensearch_result = await self.verify_opensearch_storage(p_task_id, 5)
            
            # VectorDB 확인
            v_vectordb_result = await self.verify_vectordb_storage(p_task_id, 5)
            
            # 전체 상태 판정
            v_overall_health = "healthy"
            if not v_opensearch_result.get('success') or not v_vectordb_result.get('success'):
                v_overall_health = "degraded"
            
            v_result = {
                'success': True,
                'overall_health': v_overall_health,
                'timestamp': datetime.now().isoformat(),
                'opensearch': v_opensearch_result,
                'vectordb': v_vectordb_result,
                'recommendations': []
            }
            
            # 권장사항 생성
            if not v_opensearch_result.get('success'):
                v_result['recommendations'].append("OpenSearch 연결 및 인덱스 상태를 확인하세요")
            
            if not v_vectordb_result.get('success'):
                v_result['recommendations'].append("VectorDB Knowledge Base 상태를 확인하세요")
            
            if v_opensearch_result.get('total_count', 0) == 0:
                v_result['recommendations'].append("OpenSearch에 저장된 뉴스 데이터가 없습니다. 크롤링을 실행하세요")
            
            if v_vectordb_result.get('documents_count', 0) == 0:
                v_result['recommendations'].append("VectorDB에 저장된 임베딩 데이터가 없습니다. 크롤링을 실행하세요")
            
            Logger.info(f"전체 저장소 상태 확인 완료: {v_overall_health}")
            return v_result
            
        except Exception as e:
            Logger.error(f"전체 저장소 상태 확인 실패: {e}")
            return {
                'success': False,
                'overall_health': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }