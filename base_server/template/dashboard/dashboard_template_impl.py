from datetime import datetime

import aiohttp
from template.base.base_template import BaseTemplate
from template.dashboard.common.dashboard_serialize import (
    DashboardMainRequest, DashboardMainResponse,
    DashboardAlertsRequest, DashboardAlertsResponse,
    DashboardPerformanceRequest, DashboardPerformanceResponse,
    SecuritiesLoginRequest, SecuritiesLoginResponse,
    PriceRequest, PriceResponse
)
from template.dashboard.common.dashboard_model import AssetSummary, StockHolding, MarketAlert, MarketOverview
from service.service_container import ServiceContainer
from service.core.logger import Logger

class DashboardTemplateImpl(BaseTemplate):
    def __init__(self):
        super().__init__()

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
            Logger.error(f"🔥 시세 조회 예외 발생: {e}", exc_info=True)
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
