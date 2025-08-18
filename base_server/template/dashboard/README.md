# 📁 Dashboard Template

## 📌 개요
Dashboard Template은 AI 기반 금융 거래 플랫폼의 대시보드 핵심 비즈니스 로직을 담당하는 템플릿입니다. 포트폴리오 자산 요약, 보유 종목 현황, 시장 개요, 성과 분석, 실시간 알림, 증권사 API 연동, AI 기반 주식 추천 등 종합적인 대시보드 기능을 제공합니다.

## 🏗️ 구조
```
base_server/template/dashboard/
├── dashboard_template_impl.py          # 대시보드 템플릿 구현체
├── common/                             # 공통 모델 및 프로토콜
│   ├── dashboard_model.py             # 대시보드 데이터 모델
│   ├── dashboard_protocol.py          # 대시보드 프로토콜 정의
│   └── dashboard_serialize.py         # 대시보드 직렬화 클래스
└── README.md                          
```

## 🔧 핵심 기능

### **DashboardTemplateImpl 클래스**
- **대시보드 메인 데이터**: `on_dashboard_main_req()` - 자산 요약, 보유 종목, 포트폴리오 차트, 자산 배분 차트, 최근 알림, 시장 개요 통합 조회
- **알림 목록 관리**: `on_dashboard_alerts_req()` - 페이지네이션 지원, 타입별 필터링, 안읽음 알림 수 계산
- **성과 분석**: `on_dashboard_performance_req()` - 포트폴리오 수익률, 벤치마크 비교, 샤프 비율, 최대 낙폭, 변동성, 성과 차트 데이터
- **OAuth 인증**: `on_dashboard_oauth_req()` - 한국투자증권 API OAuth 토큰 발급, Redis 사용자별 토큰 캐싱
- **실시간 시세**: `on_dashboard_price_us_req()` - 미국 나스닥 종목 실시간 시세 조회, 한국투자증권 해외주식 API 연동
- **AI 종목 추천**: `on_stock_recommendation_req()` - NewsAPI, FMP, FRED API 직접 호출 기반 독립형 ChatOpenAI 추천 시스템

## 🔄 Template-Service 연동

### **사용하는 Service 목록**
- **DatabaseService**: 샤드 DB 연동 및 저장 프로시저 호출 (call_shard_procedure, call_global_procedure)
- **CacheService**: Redis 기반 OAuth 토큰 캐싱 (get_client(), set_string, get_string)
- **ExternalService**: 한국투자증권 API 연동 (aiohttp 기반 REST API 호출)
- **LLM Service**: 독립형 ChatOpenAI를 통한 종목 추천 (NewsAPI, FMP, FRED API 직접 호출)

### **연동 방식 설명**
1. **데이터베이스 연동** → ServiceContainer.get_database_service()로 DatabaseService 획득, fp_get_dashboard_main, fp_get_portfolio_performance, fp_get_api_keys 프로시저 호출
2. **캐시 연동** → ServiceContainer.get_cache_service()로 CacheService 획득, 사용자별 OAuth 토큰 Redis 저장/조회
3. **외부 API 연동** → aiohttp.ClientSession으로 한국투자증권 해외주식 시세 API 호출, OAuth 토큰 인증
4. **AI 도구 연동** → NewsAPI, FMP, FRED API 직접 호출을 통한 뉴스 및 시장 데이터 수집, 독립형 ChatOpenAI로 종목 추천

## 📊 데이터 흐름

### **대시보드 메인 데이터 플로우**
```
1. 대시보드 메인 요청
   ↓
2. fp_get_dashboard_main 프로시저 호출 (자산, 보유종목, 알림, 시장, 차트)
   ↓
3. DB 결과 데이터 파싱 및 모델 생성
   ↓
4. 포트폴리오 차트 데이터 생성 (시간별 가치 변화)
   ↓
5. 자산 배분 차트 데이터 생성 (종목별 비중)
   ↓
6. DashboardMainResponse 반환
```

### **OAuth 인증 플로우**
```
1. OAuth 인증 요청
   ↓
2. fp_get_api_keys 프로시저로 한국투자증권 API 키 조회
   ↓
3. 한국투자증권 OAuth 토큰 발급 API 호출
   ↓
4. Redis에 사용자별 토큰 저장 (user:{account_db_key}:korea_investment:access_token)
   ↓
5. SecuritiesLoginResponse 반환
```

## 🚀 사용 예제

### **대시보드 메인 데이터 조회 예제**
```python
async def on_dashboard_main_req(self, client_session, request):
    response = DashboardMainResponse()
    try:
        account_db_key = getattr(client_session.session, 'account_db_key', 0)
        shard_id = getattr(client_session.session, 'shard_id', 1)
        
        db_service = ServiceContainer.get_database_service()
        dashboard_result = await db_service.call_shard_procedure(
            shard_id, "fp_get_dashboard_main", (account_db_key, True, request.chart_period)
        )
        
        # DB 결과 처리 및 모델 생성
        asset_data = dashboard_result[0][0] if dashboard_result[0] else {}
        holdings_data = dashboard_result[1] if len(dashboard_result) > 1 else []
        
        # 자산 요약 정보 생성
        asset_summary = AssetSummary(
            total_assets=float(asset_data.get('total_assets', 0.0)),
            cash_balance=float(asset_data.get('cash_balance', 0.0)),
            stock_value=float(asset_data.get('stock_value', 0.0)),
            total_return=float(asset_data.get('total_return', 0.0)),
            return_rate=float(asset_data.get('return_rate', 0.0)),
            currency=asset_data.get('currency', 'KRW')
        )
        
        response.asset_summary = asset_summary
        response.errorCode = 0
        
    except Exception as e:
        response.errorCode = 1000
    
    return response
```

## ⚙️ 설정

### **데이터베이스 프로시저 설정**
- **fp_get_dashboard_main**: 대시보드 메인 데이터 통합 조회
- **fp_get_portfolio_performance**: 포트폴리오 성과 분석 데이터 조회
- **fp_get_api_keys**: 한국투자증권 API 키 조회

### **OAuth 토큰 설정**
- **Redis 키 패턴**: user:{account_db_key}:korea_investment:access_token
- **TTL 설정**: 만료시간 - 60초 버퍼, 최소 5분 보장
- **폴백 메커니즘**: Redis 토큰 없을 시 DB 저장 토큰 사용

### **외부 API 설정**
- **한국투자증권 OAuth**: https://openapi.koreainvestment.com:9443/oauth2/tokenP
- **해외주식 시세**: https://openapi.koreainvestment.com:9443/uapi/overseas-price/v1/quotations/price

## 🔗 연관 폴더

### **의존성 관계**
- **`service.db.database_service`**: DatabaseService - 샤드 DB 연동
- **`service.cache.cache_service`**: CacheService - Redis 기반 OAuth 토큰 캐싱
- **`service.llm.AIChat.BasicTools.NewsTool`**: NewsTool - import만 되어있음 (실제 사용되지 않음)
- **`service.llm.AIChat.BasicTools.MarketDataTool`**: MarketDataTool - import만 되어있음 (실제 사용되지 않음)

### **기본 템플릿 연관**
- **`template.base.base_template`**: BaseTemplate - 기본 템플릿 클래스 상속
- **`template.base.client_session`**: ClientSession - 클라이언트 세션 관리

---
