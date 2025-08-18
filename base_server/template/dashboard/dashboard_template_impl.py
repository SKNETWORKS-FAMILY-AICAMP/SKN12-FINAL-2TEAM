from datetime import datetime, timezone, timedelta
import traceback

import aiohttp
from typing import Any, List
from template.base.base_template import BaseTemplate
from template.base.template_config import AppConfig
from template.dashboard.common.dashboard_serialize import (
    DashboardMainRequest, DashboardMainResponse,
    DashboardAlertsRequest, DashboardAlertsResponse,
    DashboardPerformanceRequest, DashboardPerformanceResponse,
    SecuritiesLoginRequest, SecuritiesLoginResponse,
    PriceRequest, PriceResponse,
    StockRecommendationRequest, StockRecommendationResponse,
    EconomicCalendarRequest, EconomicCalendarResponse,
    MarketRiskPremiumRequest, MarketRiskPremiumResponse
)
from template.dashboard.common.dashboard_model import AssetSummary, StockHolding, MarketAlert, MarketOverview
from service.service_container import ServiceContainer
from service.core.logger import Logger
from service.llm.AIChat.BasicTools.NewsTool import NewsTool
from service.llm.AIChat.BasicTools.MarketDataTool import MarketDataTool
import os, re, json, asyncio, uuid, time

class DashboardTemplateImpl(BaseTemplate):
    def __init__(self):
        super().__init__()
        self.app_config: AppConfig | None = None

    def init(self, config: AppConfig):
        # 템플릿 초기화 시 전체 앱 설정 보관
        try:
            self.app_config = config
            Logger.info("DashboardTemplateImpl initialized with AppConfig")
        except Exception as e:
            Logger.warn(f"DashboardTemplateImpl init: failed to set app_config: {e}")

    async def on_dashboard_main_req(self, client_session, request: DashboardMainRequest):
        """대시보드 메인 데이터 요청 처리"""
        response = DashboardMainResponse()
        response.sequence = request.sequence
        
        Logger.info(f"Dashboard main request: period={request.chart_period}")
        
        try:
            # 세션에서 사용자 정보 가져오기 (세션 검증은 template_service에서 이미 완료)
            account_db_key = getattr(client_session.session, 'account_db_key', 0)
            shard_id = getattr(client_session.session, 'shard_id', 1)
            
            db_service = ServiceContainer.get_database_service()
            
            # 1. 대시보드 메인 데이터 조회 DB 프로시저 호출
            dashboard_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_get_dashboard_main",
                (account_db_key, True, request.chart_period)  # include_chart=True
            )
            
            if not dashboard_result or len(dashboard_result) < 4:
                response.errorCode = 2002
                Logger.info("Dashboard main data not found")
                return response
            
            # 2. DB 결과 처리
            asset_data = dashboard_result[0][0] if dashboard_result[0] else {}
            holdings_data = dashboard_result[1] if len(dashboard_result) > 1 else []
            alerts_data = dashboard_result[2] if len(dashboard_result) > 2 else []
            market_data = dashboard_result[3] if len(dashboard_result) > 3 else []
            chart_data = dashboard_result[4] if len(dashboard_result) > 4 else []
            
            # 3. 자산 요약 정보 생성
            asset_summary = AssetSummary(
                total_assets=float(asset_data.get('total_assets', 0.0)),
                cash_balance=float(asset_data.get('cash_balance', 0.0)),
                stock_value=float(asset_data.get('stock_value', 0.0)),
                total_return=float(asset_data.get('total_return', 0.0)),
                return_rate=float(asset_data.get('return_rate', 0.0)),
                currency=asset_data.get('currency', 'KRW')
            )
            
            # 4. 보유 종목 정보 생성
            holdings = []
            for holding in holdings_data:
                holdings.append(StockHolding(
                    symbol=holding.get('symbol'),
                    name=holding.get('name'),
                    quantity=int(holding.get('quantity', 0)),
                    avg_price=float(holding.get('avg_price', 0.0)),
                    current_price=float(holding.get('current_price', 0.0)),
                    market_value=float(holding.get('market_value', 0.0)),
                    unrealized_pnl=float(holding.get('unrealized_pnl', 0.0)),
                    return_rate=round(float(holding.get('return_rate', 0.0)), 2)
                ))
            
            # 5. 최근 알림 정보 생성
            recent_alerts = []
            for alert in alerts_data:
                recent_alerts.append(MarketAlert(
                    alert_id=alert.get('alert_id'),
                    type=alert.get('type'),
                    title=alert.get('title'),
                    message=alert.get('message'),
                    severity=alert.get('severity', 'INFO'),
                    created_at=str(alert.get('created_at')),
                    symbol=alert.get('symbol', '')
                ))
            
            # 6. 시장 개요 정보 생성
            market_overview = []
            for market in market_data:
                market_overview.append(MarketOverview(
                    symbol=market.get('symbol'),
                    name=market.get('name'),
                    current_price=float(market.get('current_price', 0.0)),
                    change_amount=float(market.get('change_amount', 0.0)),
                    change_rate=float(market.get('change_rate', 0.0)),
                    volume=int(market.get('volume', 0))
                ))
            
            # 7. 포트폴리오 차트 데이터 처리 (시간별 포트폴리오 가치 변화)
            portfolio_chart = []
            if chart_data:
                for chart_point in chart_data:
                    portfolio_chart.append({
                        "date": str(chart_point.get('date')),               # 날짜
                        "value": float(chart_point.get('total_value', 0.0)), # 포트폴리오 총 가치
                        "return_rate": float(chart_point.get('return_rate', 0.0)) # 수익률
                    })
            
            # 8. 자산 배분 차트 데이터 생성 (종목별 포트폴리오 비중)
            allocation_chart = []
            total_stock_value = sum(float(h.get('market_value', 0)) for h in holdings_data)
            if total_stock_value > 0:
                for holding in holdings_data[:5]:  # 상위 5개 종목만 표시
                    allocation_chart.append({
                        "symbol": holding.get('symbol'),                    # 종목 코드
                        "name": holding.get('name'),                       # 종목명
                        "value": float(holding.get('market_value', 0.0)),  # 시장 가치
                        "percentage": round(float(holding.get('market_value', 0.0)) / total_stock_value * 100, 1) # 비중
                    })
            
            # 9. Response 데이터 설정
            response.errorCode = 0
            response.asset_summary = asset_summary
            response.holdings = holdings
            response.portfolio_chart = portfolio_chart    # 차트 데이터 활성화
            response.allocation_chart = allocation_chart  # 차트 데이터 활성화  
            response.recent_alerts = recent_alerts
            response.market_overview = market_overview
            
            Logger.info(f"Dashboard main data retrieved for account_db_key={account_db_key}")
            
        except Exception as e:
            response.errorCode = 1000
            Logger.error(f"Dashboard main error: {e}")
        
        return response

    async def on_dashboard_alerts_req(self, client_session, request: DashboardAlertsRequest):
        """알림 목록 요청 처리"""
        response = DashboardAlertsResponse()
        response.sequence = request.sequence
        
        Logger.info(f"Dashboard alerts request: page={request.page}, type={request.alert_type}")
        
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            db_service = ServiceContainer.get_database_service()
            
            # 1. 알림 목록 조회 (대시보드 알림 테이블에서)
            # 실제로는 별도의 fp_get_dashboard_alerts 프로시저가 필요하지만
            # 여기서는 기존 대시보드 메인 데이터에서 알림 정보를 활용
            
            dashboard_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_get_dashboard_main",
                (account_db_key, False, "1D")  # chart 데이터는 불필요
            )
            
            alerts = []
            if dashboard_result and len(dashboard_result) > 2:
                alerts_data = dashboard_result[2]  # 알림 데이터는 3번째 결과셋
                
                for alert_data in alerts_data:
                    # 타입 필터링 적용
                    if request.alert_type and request.alert_type != "ALL":
                        if alert_data.get('type') != request.alert_type:
                            continue
                    
                    alerts.append(MarketAlert(
                        alert_id=alert_data.get('alert_id'),
                        type=alert_data.get('type'),
                        title=alert_data.get('title'),
                        message=alert_data.get('message'),
                        severity=alert_data.get('severity', 'INFO'),
                        created_at=str(alert_data.get('created_at')),
                        symbol=alert_data.get('symbol', '')
                    ))
            
            # 페이지네이션 적용
            start_idx = (request.page - 1) * request.limit
            end_idx = start_idx + request.limit
            paginated_alerts = alerts[start_idx:end_idx]
            
            # 안읽음 알림 수 계산 (간단한 예시)
            unread_count = len([a for a in alerts if a.severity in ['WARNING', 'ERROR']])
            
            response.errorCode = 0
            response.alerts = paginated_alerts
            response.total_count = len(alerts)
            response.unread_count = unread_count
            
        except Exception as e:
            response.errorCode = 1000
            Logger.error(f"Dashboard alerts error: {e}")
        
        return response

    async def on_dashboard_performance_req(self, client_session, request: DashboardPerformanceRequest):
        """성과 분석 요청 처리"""
        response = DashboardPerformanceResponse()
        response.sequence = request.sequence
        
        Logger.info(f"Dashboard performance request: period={request.period}")
        
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            db_service = ServiceContainer.get_database_service()
            
            # 1. 성과 분석 데이터 조회 (포트폴리오 성과 테이블에서)
            # 실제로는 fp_get_performance_analysis 프로시저가 필요하지만
            # 여기서는 기존 데이터를 활용
            
            # 포트폴리오 성과 데이터 조회
            performance_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_get_portfolio_performance",
                (account_db_key, request.period)
            )
            
            if not performance_result:
                # 기본값으로 설정
                response.portfolio_return = 0.0
                response.benchmark_return = 0.0
                response.sharpe_ratio = 0.0
                response.max_drawdown = 0.0
                response.volatility = 0.0
                response.performance_chart = []
                response.errorCode = 0
                return response
            
            # 2. 성과 지표 계산
            perf_data = performance_result[0] if performance_result else {}
            
            portfolio_return = float(perf_data.get('return_rate', 0.0))
            benchmark_return = float(perf_data.get('benchmark_return', 0.0))
            sharpe_ratio = float(perf_data.get('sharpe_ratio', 0.0))
            max_drawdown = float(perf_data.get('max_drawdown', 0.0))
            volatility = float(perf_data.get('volatility', 0.0))
            
            # 3. 성과 차트 데이터 생성
            performance_chart = []
            if len(performance_result) > 1:
                chart_data = performance_result[1:]
                for chart_point in chart_data:
                    performance_chart.append({
                        "date": str(chart_point.get('date')),
                        "portfolio_value": float(chart_point.get('total_value', 0.0)),
                        "return_rate": float(chart_point.get('return_rate', 0.0)),
                        "benchmark_value": float(chart_point.get('total_value', 0.0)) * (1 + benchmark_return / 100)
                    })
            
            response.portfolio_return = round(portfolio_return, 2)
            response.benchmark_return = round(benchmark_return, 2)
            response.sharpe_ratio = round(sharpe_ratio, 2)
            response.max_drawdown = round(max_drawdown, 2)
            response.volatility = round(volatility, 2)
            response.performance_chart = performance_chart
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            Logger.error(f"Dashboard performance error: {e}")
        
        return response

    async def on_dashboard_oauth_req(self, client_session, request: SecuritiesLoginRequest):
        """OAuth 인증 요청 처리"""
        print(f"📥 OAuth body received: {request.model_dump_json()}")

        account_db_key = client_session.session.account_db_key
        db_service = ServiceContainer.get_database_service()
        Logger.debug(f"Dashboard OAuth request: account_db_key={account_db_key}")

        # 기본값 설정
        sequence = request.sequence

        # API 키 조회
        result = await db_service.call_global_procedure(
            "fp_get_api_keys",
            (account_db_key,)
        )
        Logger.debug(f"API keys result: {result}")

        if not result:
            return SecuritiesLoginResponse(
                result="fail",
                message="API 키 조회 실패",
                app_key="",
                sequence=sequence,
                errorCode=9007
            )

        api_data = result[0]
        try:
            appkey = api_data.get('korea_investment_app_key', '')
            appsecret = api_data.get('korea_investment_app_secret', '')

            url = "https://openapi.koreainvestment.com:9443/oauth2/tokenP"
            payload = {
                "grant_type": "client_credentials",
                "appkey": appkey,
                "appsecret": appsecret
            }

            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json; charset=utf-8"}
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        Logger.error(f"🔐 OAuth 인증 실패: {error_text}")
                        return SecuritiesLoginResponse(
                            result="fail",
                            message="한국투자증권 OAuth 인증 실패",
                            app_key=appkey,
                            sequence=sequence,
                            errorCode=5001
                        )

                    data = await resp.json()
                    token = data.get("access_token")
                    Logger.info(f"✅ OAuth 토큰 발급 성공: {token}")

                    # 사용자별 Redis 저장 (계정 단위로 토큰 캐시)
                    try:
                        cache_service = ServiceContainer.get_cache_service()
                        async with cache_service.get_client() as redis_client:
                            # 키 네임스페이스: user:{account_db_key}:korea_investment:access_token
                            user_prefix = f"user:{account_db_key}:korea_investment"
                            expires_in = int(data.get("expires_in", 0)) if str(data.get("expires_in", "")).isdigit() else 0
                            # 만료는 응답 TTL에서 60초 버퍼, 최소 5분 보장
                            ttl_seconds = max(expires_in - 60, 300) if expires_in > 0 else 23 * 3600
                            await redis_client.set_string(f"{user_prefix}:access_token", token, expire=ttl_seconds)
                            await redis_client.set_string(f"{user_prefix}:issued_at", datetime.utcnow().isoformat(), expire=ttl_seconds)
                            Logger.info(f"✅ Redis에 사용자별 OAuth 토큰 저장 완료 (account={account_db_key}, ttl={ttl_seconds}s)")
                    except Exception as cache_e:
                        Logger.warn(f"⚠️ OAuth 토큰 Redis 저장 실패: {cache_e}")

            return SecuritiesLoginResponse(
                result="success",
                message="OAuth 인증 성공",
                app_key=appkey,
                sequence=sequence,
                errorCode=0
            )

        except Exception as e:
            Logger.error(f"🔥 Dashboard OAuth error: {e}")
            return SecuritiesLoginResponse(
                result="fail",
                message=f"서버 오류: {str(e)}",
                app_key="",
                sequence=sequence,
                errorCode=1000
            )
    async def on_dashboard_price_us_req(self, client_session, request: PriceRequest):
        """미국 나스닥 종가 조회 요청 처리 (한투증 REST API 사용)"""
        Logger.info(f"📥 미국 종가 요청: {request.model_dump_json()}")

        ticker = request.ticker.upper()
        db_service = ServiceContainer.get_database_service()

        Logger.debug(f"🔍 DB에서 API 키 조회 시작: account_db_key={client_session.session.account_db_key}")

        # DB에서 앱키, 앱시크릿, 토큰 정보 가져오기
        result = await db_service.call_global_procedure(
            "fp_get_api_keys", (client_session.session.account_db_key,)
        )

        Logger.debug(f"📦 DB 조회 결과: {result}")

        if not result:
            Logger.error("❌ API 키 조회 실패 (DB에서 결과 없음)")
            return PriceResponse(
                result="fail",
                message="API 키 조회 실패",
                ticker=ticker,
                price=0,
                change=0,
                change_pct=0,
                volume=0,
                timestamp="",
                errorCode=9007
            )

        keys = result[0]
        appkey = keys.get("korea_investment_app_key", "")
        app_secret = keys.get("korea_investment_app_secret", "")

        # 우선순위: 사용자별 Redis 저장 토큰 → DB 저장 토큰(폴백)
        token = ""
        try:
            cache_service = ServiceContainer.get_cache_service()
            async with cache_service.get_client() as redis_client:
                user_prefix = f"user:{client_session.session.account_db_key}:korea_investment"
                redis_token = await redis_client.get_string(f"{user_prefix}:access_token")
                if redis_token:
                    token = redis_token
                    Logger.info("✅ Redis에서 사용자별 OAuth 토큰 로드 성공")
        except Exception as e:
            Logger.warn(f"⚠️ Redis에서 사용자별 토큰 조회 실패: {e}")

        if not token:
            # 폴백: DB 컬럼 값 사용
            token = keys.get("korea_investment_access_token", "")
            if token:
                Logger.info("ℹ️ Redis 토큰 없음 → DB 저장 토큰 사용")

        Logger.debug(f"🔑 조회된 앱키: {appkey}, 앱시크릿: {app_secret}, 토큰 유무: {'Y' if token else 'N'}")

        if not token:
            Logger.error("❌ OAuth 토큰이 없음")
            return PriceResponse(
                result="fail",
                message="OAuth 토큰 없음",
                ticker=ticker,
                price=0,
                change=0,
                change_pct=0,
                volume=0,
                timestamp="",
                errorCode=9008
            )

        # 한투증 해외주식 시세 REST API 요청
        url = "https://openapi.koreainvestment.com:9443/uapi/overseas-price/v1/quotations/price"
        params = {
            "AUTH": "",
            "EXCD": "NAS",  # 나스닥
            "SYMB": ticker  # 종목 티커
        }
        headers = {
            "authorization": f"Bearer {token}",
            "appkey": appkey,
            "appsecret": app_secret,
            "tr_id": "HHDFS00000300",  # 미국 실시간 시세
            "custtype": "P",  # 개인
            "Content-Type": "application/json"
        }

        Logger.info(f"🌐 한투증 시세 요청 준비: url={url}, params={params}, headers={headers}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as resp:
                    Logger.info(f"📡 HTTP 요청 전송됨 (status={resp.status})")

                    if resp.status != 200:
                        text = await resp.text()
                        Logger.error(f"🔴 시세 요청 실패: status={resp.status}, body={text}")
                        return PriceResponse(
                            result="fail",
                            message="시세 요청 실패",
                            ticker=ticker,
                            price=0,
                            change=0,
                            change_pct=0,
                            volume=0,
                            timestamp="",
                            errorCode=5001
                        )

                    data = await resp.json()
                    Logger.debug(f"📥 API 응답 JSON: {data}")

                    output = data.get("output", {})
                    Logger.debug(f"📦 output 데이터: {output}")

                    # 응답 키 가변성 처리: diff/chg, tvol/pvol, ctime 미제공 시 UTC now
                    change_value = output.get("chg")
                    if change_value is None:
                        change_value = output.get("diff", 0)
                    volume_value = output.get("tvol")
                    if volume_value is None:
                        volume_value = output.get("pvol", 0)

                    return PriceResponse(
                        result="success",
                        message="시세 요청 성공",
                        ticker=ticker,
                        price=float(output.get("last", 0)),
                        change=float(change_value or 0),
                        change_pct=float(output.get("rate", 0)),
                        volume=float(volume_value or 0),
                        timestamp=output.get("ctime", datetime.utcnow().isoformat()),
                        errorCode=0
                    )

        except Exception as e:
            Logger.error(f"🔥 시세 조회 예외 발생: {e}\n{traceback.format_exc()}")
            return PriceResponse(
                result="fail",
                message=f"서버 오류: {str(e)}",
                ticker=ticker,
                price=0,
                change=0,
                change_pct=0,
                volume=0,
                timestamp="",
                errorCode=1000
            )

    async def on_stock_recommendation_req(self, client_session, request: StockRecommendationRequest):
        """AIChat 의존 없이 동작하는 종목 추천 파이프라인 (뉴스/거시/재무 직접 호출)

        단계:
        1) 스타일별 후보 티커 목록 준비(기본 내장, 필요 시 환경/요청에 따라 확장)
        2) 각 티커 최신 뉴스(GNews) 수집
        3) 거시지표(FRED: S&P500, NASDAQ, VIX) 수집 및 요약
        4) (옵션) FMP 재무지표 일부 조회해 힌트로 활용
        5) 단독 LLM(ChatOpenAI)로 상위 3개 선별→최종 1개 선정(없으면 휴리스틱)
        6) {date,ticker,reason,report} 형식으로 반환
        """
        # ── DEBUG helpers ───────────────────────────────────────────
        TRACE_ID = getattr(request, "trace_id", None) or uuid.uuid4().hex[:8]
        DEBUG = bool(getattr(request, "debug", False) or os.getenv("DEBUG_STOCK_REC", "0") == "1")
        MAX_LOG = int(os.getenv("STOCK_REC_MAX_LOG_CHARS", "1200"))

        def clip(s: str, n: int = MAX_LOG) -> str:
            if not isinstance(s, str):
                try:
                    s = str(s)
                except Exception:
                    return "<non-str>"
            return s if len(s) <= n else f"{s[:n]} … <clipped {len(s)-n} chars>"

        _SECRET_PAT = re.compile(r"(sk-[A-Za-z0-9]{10,}|api[_-]?key\s*=\s*['\"][^'\"]+['\"])", flags=re.IGNORECASE)

        def redact(s: str) -> str:
            return _SECRET_PAT.sub("***REDACTED***", s or "")

        def dbg(msg: str, **kw):
            if DEBUG:
                extra = f" | {kw}" if kw else ""
                Logger.debug(f"[stock-rec][{TRACE_ID}] {msg}{extra}")

        def step_timer():
            t0 = time.perf_counter()
            return lambda name: (name, time.perf_counter() - t0)

        Logger.info(f"📥 주식 추천 요청(standalone): {request.model_dump_json()}")

        response = StockRecommendationResponse(result="pending", recommendations=[], message="")
        response.sequence = request.sequence

        tick = step_timer()
        timings = {}

        try:
            # AppConfig 우선 → 환경변수 폴백 방식으로 API 키 확보 및 LLM 직접 구성
            def get_key(name: str) -> str:
                try:
                    if self.app_config and getattr(self.app_config, "llmConfig", None):
                        val = self.app_config.llmConfig.API_Key.get(name)
                        if val:
                            return val
                except Exception:
                    pass
                return os.getenv(name, "")

            llm = None
            try:
                from langchain_openai import ChatOpenAI  # type: ignore
                # 기본값
                openai_key: str | None = os.getenv("OPENAI_API_KEY") or None
                openai_model: str | None = os.getenv("OPENAI_MODEL") or None
                base_url: str | None = None
                temperature = 0.2
                timeout = 30

                # AppConfig 기반 설정 우선
                if self.app_config and getattr(self.app_config, "llmConfig", None):
                    try:
                        prov_id = self.app_config.llmConfig.default_provider
                        prov = self.app_config.llmConfig.providers.get(prov_id)
                        if prov:
                            openai_key = openai_key or prov.api_key
                            openai_model = "gpt-4o-mini"
                            base_url = getattr(prov, "base_url", None) or base_url
                            if isinstance(prov.temperature, (int, float)) and prov.temperature is not None:
                                temperature = float(prov.temperature)
                            if isinstance(prov.timeout, int) and prov.timeout is not None:
                                timeout = int(prov.timeout)
                    except Exception:
                        pass

                # 최종 키 확인 후 LLM 생성 (파라미터명은 기존 서비스 구현과 동일하게 openai_api_key 사용)
                if openai_key:
                    if base_url:
                        llm = ChatOpenAI(model=openai_model or "gpt-4o-mini", temperature=temperature, timeout=timeout, openai_api_key=openai_key, base_url=base_url)
                    else:
                        llm = ChatOpenAI(model=openai_model or "gpt-4o-mini", temperature=temperature, timeout=timeout, openai_api_key=openai_key)
            except Exception:
                llm = None

            NEWSAPI_KEY = get_key("NEWSAPI_KEY")
            FMP_API_KEY = get_key("FMP_API_KEY")
            FRED_API_KEY = get_key("FRED_API_KEY")

            market = (request.market or "NASDAQ").upper()
            today = datetime.now(timezone.utc).date().isoformat()

            # ── 1) 후보 티커 (LLM으로 카테고리별 10개 생성) ───────────
            styles = ["CONSERVATIVE", "GROWTH", "VALUE"]
            prompts = ["주식 시장을 분석하는 전문 애널리스트입니다. 저는 변동성이 낮고 꾸준한 수익을 기대할 수 있는 안정적인(Conservative) 투자","혁신 기술과 미래 산업 트렌드를 분석하는 전문 벤처 캐피탈리스트입니다. 저는 단기적인 변동성을 감수하더라도 높은 자본 수익률을 목표로 하는 성장주(Growth Stock)에 투자","워렌 버핏의 투자 철학을 따르는 가치 투자 전문가입니다. 저는 현재 기업의 내재 가치에 비해 저평가되어 있는 가치주(Value Stock)를 발굴하여 장기적인 관점에서 투자"]
            style_to_tickers: dict[str, list[str]] = {}

            # 심볼 검증: AAPL, MSFT, BRK.B 등 허용
            _SYMBOL_RE = re.compile(r'^[A-Z]{1,5}(?:\.[A-Z]{1,2})?$')
            # "tickers": [ ... ] 블록을 넓게 잡아 추출
            _TICKERS_BLOCK_RE = re.compile(r'"tickers"\s*:\s*\[(.*?)\]', re.S | re.I)

            def _strip_code_fences(s: str) -> str:
                # ```json ... ``` 혹은 ``` ... ``` 제거
                m = re.findall(r"```(?:json)?\s*(.*?)\s*```", s, flags=re.S | re.I)
                return m[0] if m else s

            def _try_json(s: str):
                try:
                    return json.loads(s)
                except Exception:
                    return None

            def parse_ticker_list(raw: Any) -> list[str]:
                """
                LLM 응답이 문자열/딕셔너리/메시지객체(out.content 보유) 등 어떤 형태든
                tickers를 최대 10개까지 정제해 반환.
                """
                # 0) 메시지 객체에서 content 우선 추출
                if hasattr(raw, "content"):
                    raw = getattr(raw, "content") or raw
                # 1) 딕셔너리면 바로 접근
                if isinstance(raw, dict):
                    arr = raw.get("tickers")
                    return _normalize_tickers(arr)

                # 2) 문자열로 캐스팅
                s = str(raw)

                # 3) 코드펜스 제거 후 JSON 시도
                s_clean = _strip_code_fences(s).strip()
                obj = _try_json(s_clean)
                if isinstance(obj, dict) and isinstance(obj.get("tickers"), list):
                    return _normalize_tickers(obj["tickers"])

                # 4) 원문 전체를 JSON으로도 시도 (일부 모델이 코드펜스 없이 순수 JSON을 줄 때)
                obj2 = _try_json(s)
                if isinstance(obj2, dict) and isinstance(obj2.get("tickers"), list):
                    return _normalize_tickers(obj2["tickers"])

                # 5) 정규식으로 "tickers":[ ... ] 블록에서 후보 추출
                m = _TICKERS_BLOCK_RE.search(s)
                if m:
                    inside = m.group(1).upper()
                    # 따옴표 유무/쉼표/공백 섞여도 심볼 패턴으로 걸러냄
                    candidates = re.findall(r'[A-Z]{1,5}(?:\.[A-Z]{1,2})?', inside)
                    if candidates:
                        return _normalize_tickers(candidates)

                # 6) 마지막 안전망: 본문 전체에서 심볼 패턴 스캔
                candidates = re.findall(r'[A-Z]{1,5}(?:\.[A-Z]{1,2})?', s.upper())
                return _normalize_tickers(candidates)

            def _normalize_tickers(arr, limit: int = 10) -> list[str]:
                if not isinstance(arr, list):
                    return []
                out: list[str] = []
                seen = set()
                for t in arr:
                    if not isinstance(t, str):
                        continue
                    sym = t.strip().upper()
                    if not sym or not _SYMBOL_RE.fullmatch(sym):
                        continue
                    if sym in seen:
                        continue
                    seen.add(sym)
                    out.append(sym)
                    if len(out) >= limit:
                        break
                return out
            def pick_unique(seq: list[str], k: int, banned: set[str] | None = None) -> list[str]:
                """seq에서 앞에서부터 중복/금지(banned) 없이 최대 k개를 뽑아 반환."""
                banned = banned or set()
                out: list[str] = []
                seen: set[str] = set()
                for t in seq:
                    u = (t or "").strip().upper()
                    if not u or u in banned or u in seen:
                        continue
                    out.append(u)
                    seen.add(u)
                    if len(out) >= k:
                        break
                return out

            # 루프 돌기 전에 한 줄 추가
            used_tickers: set[str] = set()
            TARGET_PER_STYLE = 10  # 기존처럼 10개를 상한으로 유지

            for style, prompt in zip(styles, prompts):
                tickers: list[str] = []

                # ── 기존 1-a, 1-b, 폴백 로직 그대로 유지 ─────────────────────────────
                try:
                    from openai import OpenAI  # type: ignore
                    openai_key_cfg = os.getenv("OPENAI_API_KEY") or None
                    openai_model_cfg = os.getenv("OPENAI_SEARCH_MODEL") or None
                    base_url_cfg: str | None = None
                    if self.app_config and getattr(self.app_config, "llmConfig", None):
                        prov_id = self.app_config.llmConfig.default_provider
                        prov = self.app_config.llmConfig.providers.get(prov_id)
                        if prov:
                            openai_key_cfg = openai_key_cfg or prov.api_key
                            base_url_cfg = getattr(prov, "base_url", None) or base_url_cfg
                    search_model = openai_model_cfg or os.getenv("OPENAI_MODEL_SEARCH_DEFAULT", "gpt-4.1")
                    if openai_key_cfg:
                        client = OpenAI(api_key=openai_key_cfg, base_url=base_url_cfg)
                        prompt_tickers_ws = (
                            f"You are a professional equity analyst. Using up-to-date web search, "
                            f"select 10 promising US {market} tickers for the category {style}. "
                            'Return strictly JSON only: {"tickers":["AAPL", ...]} with UPPERCASE tickers. '
                            "Do not include any explanation. Consider liquidity and recency."
                        )
                        ws = client.responses.create(
                            model=search_model,
                            tools=[{"type": "web_search_preview"}],
                            tool_choice={"type": "web_search_preview"},
                            input=prompt_tickers_ws,
                        )
                        raw = getattr(ws, "output_text", None)
                        if not raw:
                            try:
                                outputs = getattr(ws, "output", [])
                                if outputs:
                                    for item in outputs:
                                        if getattr(item, "type", "") == "message":
                                            contents = getattr(item, "content", [])
                                            for c in contents:
                                                if getattr(c, "type", "") == "output_text":
                                                    raw = getattr(c, "text", None)
                                                    if raw:
                                                        break
                                            if raw:
                                                break
                            except Exception:
                                raw = None
                        if isinstance(raw, str) and raw.strip():
                            tickers = parse_ticker_list(raw)
                except Exception:
                    pass

                if not tickers and llm is not None:
                    try:
                        prompt_tickers = (
                            f"다음 카테고리({style})에 적합한 미국 나스닥에 유망 티커 10개를 선택. "
                            f"{prompt}하기 좋은 주식 시장을 분석하고, 유망 티커 10개를 선택하고 "
                            '오직 JSON으로만 응답하라. 형식: {"tickers":["AAPL", ...]}'
                        )
                        print(f"llm이 시도 한다.")
                        out = llm.invoke(prompt_tickers)
                        print(f"llm이 이렇게 말함. : -- {out}")
                        tickers = parse_ticker_list(out)
                    except Exception:
                        tickers = []

                if not tickers:
                    fallback: dict[str, list[str]] = {
                        "CONSERVATIVE": ["AAPL","MSFT","GOOGL","AVGO","COST","PEP","KO","JNJ","PG","V"],
                        "GROWTH": ["NVDA","TSLA","AMD","SMCI","PLTR","SHOP","MDB","CRWD","SNOW","NET"],
                        "VALUE": ["AMZN","META","NFLX","ADBE","INTC","ORCL","CSCO","IBM","QCOM","TXN"],
                    }
                    print("LLM 실패/미사용 시 간단 폴백")
                    tickers = fallback.get(style, [])[:TARGET_PER_STYLE]

                final_list = pick_unique(tickers, TARGET_PER_STYLE, banned=used_tickers)
                style_to_tickers[style] = final_list
                used_tickers.update(final_list)

            timings["step1_candidates"] = tick("step1_candidates")[1]
            tick = step_timer()

            # ── helpers: 외부호출 ─────────────────────────────────
            async def fetch_gnews(query: str, k: int = 5) -> list[dict]:
                if not NEWSAPI_KEY:
                    return []
                url = "https://gnews.io/api/v4/search"
                params = {"q": query, "lang": "en", "token": NEWSAPI_KEY, "max": k}
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, params=params, timeout=10) as resp:
                            if resp.status != 200:
                                return []
                            data = await resp.json()
                            articles = data.get("articles", [])
                            out = []
                            for a in articles:
                                out.append({
                                    "title": a.get("title", ""),
                                    "url": a.get("url", ""),
                                    "date": (a.get("publishedAt", "") or "")[:10],
                                })
                            return out
                except Exception:
                    return []

            async def fetch_fred_latest(series_id: str) -> float:
                if not FRED_API_KEY:
                    return 0.0
                url = "https://api.stlouisfed.org/fred/series/observations"
                params = {
                    "series_id": series_id,
                    "api_key": FRED_API_KEY,
                    "file_type": "json",
                    "sort_order": "desc",
                    "limit": 1,
                }
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, params=params, timeout=10) as resp:
                            if resp.status != 200:
                                return 0.0
                            data = await resp.json()
                            obs = (data.get("observations") or [])
                            if not obs:
                                return 0.0
                            v = obs[0].get("value")
                            try:
                                return float(v)
                            except Exception:
                                return 0.0
                except Exception:
                    return 0.0

            async def fetch_fmp_metrics(ticker: str) -> dict:
                if not FMP_API_KEY:
                    return {}
                base = "https://financialmodelingprep.com/api/v3"
                params = {"apikey": FMP_API_KEY, "period": "annual", "limit": 4}
                endpoints = [
                    (f"{base}/key-metrics/{ticker}", {}),
                    (f"{base}/ratios/{ticker}", {}),
                    (f"{base}/income-statement/{ticker}", {}),
                ]
                out: dict[str, Any] = {}
                try:
                    async with aiohttp.ClientSession() as session:
                        for url, extra in endpoints:
                            p = params.copy(); p.update(extra)
                            async with session.get(url, params=p, timeout=10) as resp:
                                if resp.status != 200:
                                    continue
                                try:
                                    out[url.rsplit("/", 1)[-1]] = await resp.json()
                                except Exception:
                                    pass
                except Exception:
                    pass
                return out

            # ── 2) 뉴스 수집 ───────────────────────────────────────
            ticker_news: dict[str, list[dict]] = {}
            flat_tickers = [t for arr in style_to_tickers.values() for t in arr]
            dbg("news_fetch_start", total_symbols=len(flat_tickers))
            t_news = step_timer()
            news_results = await asyncio.gather(*[fetch_gnews(t, 5) for t in flat_tickers], return_exceptions=True)
            timings["step2_news_fetch"] = t_news("news_fetch")[1]
            idx = 0
            for style in styles:
                for t in style_to_tickers.get(style, []):
                    res = news_results[idx]; idx += 1
                    if isinstance(res, Exception):
                        ticker_news[t] = []
                    else:
                        ticker_news[t] = res or []

            # ── 3) 거시지표 수집(FRED) ─────────────────────────────
            t_macro = step_timer()
            sp500, nasdaq, vix = await asyncio.gather(
                fetch_fred_latest("SP500"),
                fetch_fred_latest("NASDAQCOM"),
                fetch_fred_latest("VIXCLS"),
            )
            macro_brief = "\n".join([
                f"S&P 500: {sp500:.2f}" if sp500 else "S&P 500: N/A",
                f"NASDAQ: {nasdaq:.2f}" if nasdaq else "NASDAQ: N/A",
                f"VIX: {vix:.2f}" if vix else "VIX: N/A",
            ])
            timings["step3_macro_fetch"] = t_macro("macro_fetch")[1]
            tick = step_timer()

            # ── 4) (옵션) 재무 메트릭 일부 조회(병렬, 실패 허용) ─────
            t_fin = step_timer()
            fin_map: dict[str, dict] = {}
            if FMP_API_KEY:
                fin_results = await asyncio.gather(*[fetch_fmp_metrics(t) for t in flat_tickers], return_exceptions=True)
                j = 0
                for t in flat_tickers:
                    r = fin_results[j]; j += 1
                    if not isinstance(r, Exception):
                        fin_map[t] = r
            timings["step4_financials_fetch"] = t_fin("fin_fetch")[1]
            tick = step_timer()

            # ── 5) 상위 3개 선별 → 최종 1개 ────────────────────────
            def build_news_lines(tk: str) -> str:
                items = ticker_news.get(tk, [])[:5]
                return "; ".join([i.get("title", "") for i in items if i.get("title")])

            def heuristic_pick_top3(cands: list[str]) -> list[dict]:
                # 매우 단순한 휴리스틱: 뉴스 제목 길이/가짓수 기반 가중치
                scored = []
                for tkr in cands:
                    titles = [n.get("title", "") for n in ticker_news.get(tkr, [])]
                    score = sum(min(len(s), 120) for s in titles[:5])
                    scored.append((score, tkr))
                scored.sort(reverse=True)
                return [{"ticker": t, "reason": "최근 뉴스 노출/활동량이 상대적으로 높음"} for _, t in scored[:3]]

            def safe_json_loads(text: str):
                if text is None:
                    return None
                try:
                    return json.loads(text)
                except Exception:
                    start = text.find("{"); end = text.rfind("}")
                    if start != -1 and end != -1 and end > start:
                        try:
                            return json.loads(text[start:end+1])
                        except Exception:
                            return None
                    return None

            def is_valid_hex_color(value: str) -> bool:
                try:
                    return bool(re.fullmatch(r"#([0-9A-Fa-f]{6})", str(value)))
                except Exception:
                    return False

            def pick_brand_color(ticker: str) -> str:
                t = (ticker or "").upper()
                brand = {
                    "AAPL": "#0EA5E9",  # Apple blue-ish
                    "MSFT": "#2563EB",
                    "GOOGL": "#EA4335",
                    "GOOG": "#EA4335",
                    "AVGO": "#DC2626",
                    "COST": "#1D4ED8",
                    "NVDA": "#22C55E",
                    "TSLA": "#EF4444",
                    "AMD": "#F97316",
                    "SMCI": "#3B82F6",
                    "PLTR": "#64748B",
                    "AMZN": "#F59E0B",
                    "META": "#2563EB",
                    "NFLX": "#DC2626",
                    "ADBE": "#EF4444",
                    "INTC": "#1E3A8A",
                }
                return brand.get(t, "#1f2937")

            style_top3: dict[str, list[dict]] = {}
            for style in styles:
                cands = style_to_tickers.get(style, [])
                if not cands:
                    style_top3[style] = []
                    continue
                if llm is None:
                    style_top3[style] = heuristic_pick_top3(cands)
                    continue

                news_snippets = [f"- {t}: {build_news_lines(t)}" for t in cands]
                prompt = (
                    "아래 후보 티커와 최신 뉴스 제목을 참고하여 카테고리 {style} 관점에서 상위 3개를 고르고, "
                    "각 선택 이유를 한 줄로 설명하라. 오직 JSON 배열로만 응답. 형식: "
                    '[{{"ticker":"TSLA","reason":"..."}}, ...]'
                ).format(style=style)
                full = f"{prompt}\n\n" + "\n".join(news_snippets)
                try:
                    out = llm.invoke(full)
                    raw = getattr(out, "content", "") if out is not None else ""
                    parsed = safe_json_loads(raw) or []
                    top3: list[dict] = []
                    if isinstance(parsed, list):
                        for it in parsed:
                            if isinstance(it, dict) and it.get("ticker"):
                                top3.append({
                                    "ticker": str(it["ticker"]).upper(),
                                    "reason": str(it.get("reason", "")).strip(),
                                })
                            if len(top3) == 3:
                                break
                    if not top3:
                        top3 = heuristic_pick_top3(cands)
                    style_top3[style] = top3[:3]
                except Exception:
                    style_top3[style] = heuristic_pick_top3(cands)

            timings["step5_pick_top3"] = tick("pick_top3")[1]
            tick = step_timer()

            finals: list[dict] = []
            for style in styles:
                triples = style_top3.get(style, [])
                if not triples:
                    continue
                if llm is None:
                    pick = triples[0]
                    finals.append({
                        "date": today,
                        "ticker": pick["ticker"],
                        "reason": pick.get("reason", ""),
                        "report": "거시지표와 최근 뉴스 노출을 참고한 단순 추천입니다.",
                        "color": pick_brand_color(pick["ticker"]),
                    })
                    continue

                triple_text = "\n".join([f"- {x['ticker']}: {x.get('reason','')}" for x in triples])
                prompt = (
                    "다음 3개 후보 중에서 {style} 관점에서 최종 1개 티커를 고르고, "
                    "선정 사유(2~3문장)와 간단한 애널리스트 레포트(마크다운) 요약(8~12문장)을 한국어로 작성하라. "
                    "거시 지표를 참고하라. 오직 JSON으로만 응답하되, 해당 기업과 어울리는 대표 색상을 포함해서 다음 형식으로만 응답: "
                    '{{"ticker":"TSLA","reason":"...","report":"...","color":"#000000"}}'
                ).format(style=style)
                user_block = f"[거시 요약]\n{macro_brief}\n\n[후보]\n{triple_text}"
                full = f"{prompt}\n\n{user_block}"
                try:
                    out = llm.invoke(full)
                    raw = getattr(out, "content", "") if out is not None else ""
                    data3 = safe_json_loads(raw) or {}
                    ticker = str(data3.get("ticker") or (triples[0]["ticker"] if triples else "AAPL")).upper()
                    reason = str(data3.get("reason") or (triples[0].get("reason") if triples else "기본 추천")).strip()
                    report = str(data3.get("report") or "최근 뉴스와 거시지표를 바탕으로 간이 추천입니다.").strip()
                    raw_color = data3.get("color")
                    color = raw_color if isinstance(raw_color, str) and is_valid_hex_color(raw_color) else pick_brand_color(ticker)
                    finals.append({"date": today, "ticker": ticker, "reason": reason, "report": report, "color": color})
                except Exception:
                    pick = triples[0]
                    finals.append({
                        "date": today,
                        "ticker": pick["ticker"],
                        "reason": pick.get("reason", ""),
                        "report": "거시지표와 최근 뉴스 노출을 참고한 단순 추천입니다.",
                        "color": pick_brand_color(pick["ticker"]),
                    })

            # 응답 구성
            response.result = "success"
            response.recommendations = finals
            response.message = f"{market} 시장 단독 AI 추천 완료"
            response.errorCode = 0

            timings["step6_final"] = tick("final")[1]
            total_ms = sum(v for v in timings.values())
            try:
                timings_ms = {k: round(v * 1000, 1) for k, v in timings.items()}
                Logger.info(
                    f"✅ Standalone 추천 완료[{TRACE_ID}] styles={len(styles)} picks={len(finals)} "
                    f"timings(ms)={timings_ms} total_ms={round(total_ms * 1000, 1)}"
                )
            except Exception:
                Logger.info(
                    f"✅ Standalone 추천 완료[{TRACE_ID}] picks={len(finals)} total_ms={round(total_ms * 1000, 1)}"
                )

        except Exception as e:
            Logger.error(f"🔥 Standalone 추천 파이프라인 오류[{TRACE_ID}]: {e}\n{traceback.format_exc()}")
            response.result = "fail"
            response.message = f"서버 오류: {str(e)}"
            response.errorCode = 1000

        return response

    async def on_economic_calendar_req(self, client_session, request: EconomicCalendarRequest):
        """경제 일정 요청 처리 (FMP API 사용)"""
        Logger.info(f"📥 경제 일정 요청: {request.model_dump_json()}")

        response = EconomicCalendarResponse()
        response.sequence = request.sequence

        try:
            # 설정 파일에서 FMP API 키 가져오기
            fmp_api_key = ""
            Logger.info(f"🔍 app_config 확인: {self.app_config is not None}")
            
            if self.app_config:
                Logger.info(f"🔍 app_config 속성들: {dir(self.app_config)}")
                if hasattr(self.app_config, 'llmConfig'):
                    Logger.info(f"🔍 llmConfig 확인: {self.app_config.llmConfig}")
                    if hasattr(self.app_config.llmConfig, 'API_Key'):
                        Logger.info(f"🔍 API_Key 확인: {self.app_config.llmConfig.API_Key}")
                        fmp_api_key = self.app_config.llmConfig.API_Key.get("FMP_API_KEY", "")
                        Logger.info(f"🔑 FMP API 키: {'있음' if fmp_api_key else '없음'} ({fmp_api_key[:10] if fmp_api_key else 'N/A'}...)")
                    else:
                        Logger.warn("⚠️ llmConfig에 API_Key 속성 없음")
                else:
                    Logger.warn("⚠️ app_config에 llmConfig 속성 없음")
            else:
                Logger.warn("⚠️ app_config가 None")

            if not fmp_api_key:
                # 환경변수에서 폴백 시도
                import os
                fmp_api_key = os.getenv("FMP_API_KEY", "")
                Logger.info(f"🔍 환경변수에서 FMP API 키 조회: {'있음' if fmp_api_key else '없음'}")

            if not fmp_api_key:
                Logger.warn("❌ FMP API 키 없음 - 더미 데이터 반환")
                response.result = "success"
                response.events = self._get_dummy_events(request.days)
                response.message = "FMP API 키가 설정되지 않아 더미 데이터를 반환합니다."
                response.source = "더미 데이터"
                response.errorCode = 0
                return response

            # FMP API 호출
            events = await self._fetch_fmp_economic_calendar(fmp_api_key, request.days)
            
            response.result = "success"
            response.events = events
            response.message = "경제 일정 조회 성공"
            response.source = "FMP API"
            response.errorCode = 0

        except Exception as e:
            Logger.error(f"🔥 경제 일정 조회 오류: {e}")
            response.result = "fail"
            response.events = self._get_dummy_events(request.days)
            response.message = f"API 오류로 인해 더미 데이터를 반환합니다: {str(e)}"
            response.source = "더미 데이터 (오류 폴백)"
            response.errorCode = 1000

        return response

    async def on_market_risk_premium_req(self, client_session, request: MarketRiskPremiumRequest):
        """시장 위험 프리미엄 요청 처리 (FMP API 사용)"""
        Logger.info(f"📥 시장 위험 프리미엄 요청: {request.model_dump_json()}")

        response = MarketRiskPremiumResponse()
        response.sequence = request.sequence

        try:
            # 설정 파일에서 FMP API 키 가져오기
            fmp_api_key = ""
            if self.app_config and hasattr(self.app_config, 'llmConfig') and hasattr(self.app_config.llmConfig, 'API_Key'):
                fmp_api_key = self.app_config.llmConfig.API_Key.get("FMP_API_KEY", "")
            
            if not fmp_api_key:
                # 환경변수에서 폴백 시도
                import os
                fmp_api_key = os.getenv("FMP_API_KEY", "")

            if not fmp_api_key:
                Logger.warn("❌ FMP API 키 없음 - 더미 데이터 반환")
                response.result = "success"
                response.premiums = self._get_dummy_market_risk_premiums(request.countries)
                response.message = "FMP API 키가 설정되지 않아 더미 데이터를 반환합니다."
                response.source = "더미 데이터"
                response.errorCode = 0
                return response

            # FMP API 호출
            premiums = await self._fetch_fmp_market_risk_premiums(fmp_api_key, request.countries)
            
            response.result = "success"
            response.premiums = premiums
            response.message = "시장 위험 프리미엄 조회 성공"
            response.source = "FMP API"
            response.lastUpdated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            response.errorCode = 0

        except Exception as e:
            Logger.error(f"🔥 시장 위험 프리미엄 조회 오류: {e}")
            response.result = "fail"
            response.premiums = self._get_dummy_market_risk_premiums(request.countries)
            response.message = f"API 오류로 인해 더미 데이터를 반환합니다: {str(e)}"
            response.source = "더미 데이터 (오류 폴백)"
            response.errorCode = 1000

        return response

    async def _fetch_fmp_economic_calendar(self, fmp_api_key: str, days: int) -> list:
        """FMP API에서 경제 일정 데이터 가져오기 (캐싱 적용)"""
        try:
            # 캐시 키 생성 (날짜와 일수 기반)
            cache_key = f"economic_calendar_{days}_{datetime.now().strftime('%Y-%m-%d')}"
            
            # 캐시된 데이터가 있고 10분 이내라면 반환
            if hasattr(self, '_economic_calendar_cache'):
                cached_data = self._economic_calendar_cache.get(cache_key)
                if cached_data and (datetime.now() - cached_data['timestamp']).total_seconds() < 600:  # 10분
                    Logger.info(f"💾 캐시된 경제 일정 데이터 사용 (경과: {(datetime.now() - cached_data['timestamp']).total_seconds():.0f}초)")
                    return cached_data['data']
            else:
                self._economic_calendar_cache = {}

            # 오늘부터 지정된 일수 후까지의 날짜 계산 (최대 90일)
            today = datetime.now()
            end_date = today.replace(day=today.day + min(days, 90))
            
            from_date = today.strftime("%Y-%m-%d")
            to_date = end_date.strftime("%Y-%m-%d")

            Logger.info(f"🌐 FMP API 호출 준비: from={from_date}, to={to_date}")

            # FMP API 호출 (공식 예시와 동일한 엔드포인트 사용)
            url = "https://financialmodelingprep.com/api/v3/economic_calendar"
            params = {
                "from": from_date,
                "to": to_date,
                "apikey": fmp_api_key
            }

            Logger.info(f"🌐 FMP API 호출: {url}")
            Logger.info(f"📋 파라미터: {params}")

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=30) as resp:
                    Logger.info(f"📡 FMP API 응답 상태: {resp.status}")
                    Logger.info(f"📡 FMP API 응답 헤더: {dict(resp.headers)}")
                    
                    if resp.status == 429:
                        Logger.warn("⚠️ FMP API 레이트 리밋 도달 - 캐시된 데이터 또는 더미 데이터 반환")
                        # 캐시된 데이터가 있으면 반환, 없으면 더미 데이터
                        if hasattr(self, '_economic_calendar_cache') and self._economic_calendar_cache.get(cache_key):
                            return self._economic_calendar_cache[cache_key]['data']
                        return self._get_dummy_events(days)
                    
                    if resp.status != 200:
                        error_text = await resp.text()
                        Logger.error(f"🔴 FMP API 호출 실패: status={resp.status}, body={error_text}")
                        raise Exception(f"FMP API 호출 실패: {resp.status}")
                    
                    data = await resp.json()
                    Logger.info(f"📥 FMP API 응답 데이터 타입: {type(data)}")
                    Logger.info(f"📥 FMP API 응답 데이터 길이: {len(data) if isinstance(data, list) else 'not list'}")
                    
                    if isinstance(data, list) and len(data) > 0:
                        Logger.info(f"📥 FMP API 첫 번째 항목: {data[0]}")
                    
                    if not isinstance(data, list):
                        Logger.warn("⚠️ FMP API 응답이 리스트가 아님 - 더미 데이터 반환")
                        return self._get_dummy_events(days)
                    
                    # FMP API 응답을 우리 형식으로 변환 (정확한 필드명 사용)
                    events = []
                    for item in data:
                        try:
                            Logger.debug(f"🔍 FMP API 항목 파싱: {item}")
                            
                            # 날짜 파싱 - 다양한 형식 지원
                            raw_date = item.get("date", "")
                            Logger.debug(f"📅 원본 날짜: {raw_date}")
                            
                            event_date = None
                            if raw_date:
                                try:
                                    # "2024-12-18 09:30:00" 형식
                                    if " " in raw_date:
                                        event_date = datetime.strptime(raw_date, "%Y-%m-%d %H:%M:%S")
                                    # "2024-12-18" 형식
                                    elif "-" in raw_date:
                                        event_date = datetime.strptime(raw_date, "%Y-%m-%d")
                                    else:
                                        Logger.warn(f"⚠️ 알 수 없는 날짜 형식: {raw_date}")
                                        continue
                                except Exception as e:
                                    Logger.warn(f"⚠️ 날짜 파싱 실패: {raw_date}, 에러: {e}")
                                    continue
                            
                            if not event_date:
                                Logger.warn(f"⚠️ 유효한 날짜 없음: {raw_date}")
                                continue
                            
                            # 한국 시간으로 변환 (UTC+9)
                            event_date = event_date.replace(tzinfo=None)  # timezone 정보 제거
                            
                            event = {
                                "date": event_date.strftime("%m월 %d일"),
                                "time": event_date.strftime("%H:%M"),
                                "country": self._get_country_name(item.get("country", "")),
                                "event": item.get("event", "경제 지표"),
                                "impact": self._get_impact_level(item.get("impact", "")),
                                "previous": str(item.get("previous", "N/A")),
                                "forecast": str(item.get("estimate", "N/A")),  # estimate 필드 사용
                                "actual": str(item.get("actual", "")) if item.get("actual") is not None else None,
                                "currency": item.get("currency", ""),
                                "change": str(item.get("change", "N/A")) if item.get("change") is not None else "N/A",
                                "changePercentage": str(item.get("changePercentage", "N/A")) if item.get("changePercentage") is not None else "N/A"
                            }
                            
                            Logger.debug(f"✅ 변환된 이벤트: {event}")
                            events.append(event)
                            
                        except Exception as e:
                            Logger.warn(f"⚠️ 이벤트 데이터 변환 실패: {e}, item={item}")
                            continue

                    Logger.info(f"✅ FMP API 데이터 변환 완료: {len(events)}개 이벤트")

                    # 중요도 순으로 정렬 (High > Medium > Low)
                    impact_order = {"High": 3, "Medium": 2, "Low": 1}
                    events.sort(key=lambda x: impact_order.get(x["impact"], 0), reverse=True)
                    
                    # 최대 8개 이벤트만 반환
                    limited_events = events[:8]
                    Logger.info(f"🎯 최종 이벤트: {len(limited_events)}개 (정렬 및 제한 적용)")
                    
                    # 캐시에 저장
                    self._economic_calendar_cache[cache_key] = {
                        'data': limited_events,
                        'timestamp': datetime.now()
                    }
                    Logger.info(f"💾 경제 일정 데이터 캐시 저장 완료")
                    
                    return limited_events

        except Exception as e:
            Logger.error(f"🔥 FMP API 호출 실패: {e}")
            # 에러 발생 시 캐시된 데이터가 있으면 반환
            if hasattr(self, '_economic_calendar_cache') and self._economic_calendar_cache.get(cache_key):
                Logger.info(f"💾 에러 발생으로 캐시된 데이터 반환")
                return self._economic_calendar_cache[cache_key]['data']
            raise e

    def _get_country_name(self, country_code: str) -> str:
        """국가 코드를 한국어 국가명으로 변환"""
        country_names = {
            "US": "미국",
            "JP": "일본", 
            "CN": "중국",
            "KR": "한국",
            "EU": "유럽연합",
            "GB": "영국",
            "DE": "독일",
            "FR": "프랑스",
            "CA": "캐나다",
            "AU": "호주"
        }
        return country_names.get(country_code, country_code)

    def _get_impact_level(self, impact: str) -> str:
        """FMP API의 impact 값을 우리 형식으로 변환"""
        if not impact:
            return "Low"
        
        impact_lower = impact.lower()
        if "high" in impact_lower or "높음" in impact_lower:
            return "High"
        elif "medium" in impact_lower or "보통" in impact_lower:
            return "Medium"
        else:
            return "Low"

    def _get_dummy_events(self, days: int) -> list:
        """더미 경제 일정 데이터 생성 (현재 날짜 기준)"""
        today = datetime.now()
        events = []
        
        # 주요 경제 지표들
        indicators = [
            {"name": "비농업 고용지표", "country": "미국", "impact": "High", "previous": "187K", "forecast": "180K"},
            {"name": "ISM 제조업 지수", "country": "미국", "impact": "Medium", "previous": "49.0", "forecast": "49.5"},
            {"name": "소비자 물가지수(CPI)", "country": "미국", "impact": "High", "previous": "3.2%", "forecast": "3.1%"},
            {"name": "연방기금 금리", "country": "미국", "impact": "High", "previous": "5.50%", "forecast": "5.50%"},
            {"name": "소매 판매", "country": "미국", "impact": "Medium", "previous": "0.3%", "forecast": "0.2%"},
            {"name": "주택 판매", "country": "미국", "impact": "Low", "previous": "6.5M", "forecast": "6.6M"},
            {"name": "GDP 성장률", "country": "미국", "impact": "High", "previous": "2.1%", "forecast": "2.0%"},
            {"name": "기업 수익", "country": "미국", "impact": "Medium", "previous": "N/A", "forecast": "N/A"}
        ]
        
        for i, indicator in enumerate(indicators[:8]):  # 최대 8개
            # 오늘부터 i일 후
            event_date = today + timedelta(days=i)
            
            event = {
                "date": event_date.strftime("%m월 %d일"),
                "time": "09:30" if i % 2 == 0 else "14:00",  # 번갈아가며 시간 설정
                "country": indicator["country"],
                "event": indicator["name"],
                "impact": indicator["impact"],
                "previous": indicator["previous"],
                "forecast": indicator["forecast"],
                "actual": None,  # 더미 데이터는 실제값 없음
                "currency": "USD",
                "change": "N/A",
                "changePercentage": "N/A"
            }
            events.append(event)
        
        Logger.info(f"🎭 더미 경제 일정 데이터 생성: {len(events)}개 (현재 날짜 기준)")
        return events

    async def _fetch_fmp_market_risk_premiums(self, fmp_api_key: str, countries: List[str]) -> list:
        """FMP API에서 시장 위험 프리미엄 데이터 가져오기"""
        try:
            Logger.info(f"🌐 FMP 시장 위험 프리미엄 API 호출 준비")

            # FMP API 호출
            url = "https://financialmodelingprep.com/stable/market-risk-premium"
            params = {
                "apikey": fmp_api_key
            }

            Logger.info(f"🌐 FMP API 호출: {url}")

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=30) as resp:
                    Logger.info(f"📡 FMP API 응답 상태: {resp.status}")
                    
                    if resp.status == 429:
                        Logger.warn("⚠️ FMP API 레이트 리밋 도달 - 더미 데이터 반환")
                        return self._get_dummy_market_risk_premiums(countries)
                    
                    if resp.status != 200:
                        error_text = await resp.text()
                        Logger.error(f"🔴 FMP API 호출 실패: status={resp.status}, body={error_text}")
                        raise Exception(f"FMP API 호출 실패: {resp.status}")
                    
                    data = await resp.json()
                    Logger.info(f"📥 FMP API 응답 데이터: {len(data) if isinstance(data, list) else 'not list'}개 항목")
                    
                    if not isinstance(data, list):
                        Logger.warn("⚠️ FMP API 응답이 리스트가 아님 - 더미 데이터 반환")
                        return self._get_dummy_market_risk_premiums(countries)
                    
                    # 요청된 국가들만 필터링
                    filtered_premiums = []
                    for item in data:
                        country_code = item.get("country", "")
                        if country_code in countries:
                            premium = {
                                "country": self._get_country_name(country_code),
                                "countryCode": country_code,
                                "continent": item.get("continent", ""),
                                "countryRiskPremium": round(float(item.get("countryRiskPremium", 0)), 2),
                                "totalEquityRiskPremium": round(float(item.get("totalEquityRiskPremium", 0)), 2)
                            }
                            filtered_premiums.append(premium)
                    
                    Logger.info(f"✅ FMP API 데이터 변환 완료: {len(filtered_premiums)}개 국가")
                    return filtered_premiums

        except Exception as e:
            Logger.error(f"🔥 FMP API 호출 실패: {e}")
            raise e

    def _get_dummy_market_risk_premiums(self, countries: List[str]) -> list:
        """더미 시장 위험 프리미엄 데이터 생성"""
        dummy_data = {
            "US": {"countryRiskPremium": 0.0, "totalEquityRiskPremium": 4.6},
            "KR": {"countryRiskPremium": 1.2, "totalEquityRiskPremium": 5.8},
            "JP": {"countryRiskPremium": 0.8, "totalEquityRiskPremium": 5.4},
            "CN": {"countryRiskPremium": 1.5, "totalEquityRiskPremium": 6.1},
            "EU": {"countryRiskPremium": 0.5, "totalEquityRiskPremium": 5.1}
        }
        
        premiums = []
        for country_code in countries:
            if country_code in dummy_data:
                premium = {
                    "country": self._get_country_name(country_code),
                    "countryCode": country_code,
                    "continent": "Asia" if country_code in ["KR", "JP", "CN"] else "North America" if country_code == "US" else "Europe",
                    "countryRiskPremium": dummy_data[country_code]["countryRiskPremium"],
                    "totalEquityRiskPremium": dummy_data[country_code]["totalEquityRiskPremium"]
                }
                premiums.append(premium)
        
        Logger.info(f"🎭 더미 시장 위험 프리미엄 데이터 생성: {len(premiums)}개 국가")
        return premiums
