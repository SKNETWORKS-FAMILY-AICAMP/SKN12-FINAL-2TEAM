# 📁 Market Template

## 📌 개요
Market Template은 AI 기반 금융 거래 플랫폼의 시장 데이터 핵심 비즈니스 로직을 담당하는 템플릿입니다. 종목 검색, 시세 조회, 뉴스 분석, 시장 개요, 실시간 데이터 처리 등 종합적인 시장 정보 기능을 제공합니다. 한국투자증권 API와 연동하여 실시간 시장 데이터를 수집하고, 기술적 지표와 시장 심리 분석을 통해 투자 의사결정을 지원합니다.

## 🏗️ 구조
```
base_server/template/market/
├── market_template_impl.py              # 시장 템플릿 구현체
├── common/                              # 공통 모델 및 프로토콜
│   ├── __init__.py
│   ├── market_model.py                  # 시장 데이터 모델
│   ├── market_protocol.py               # 시장 프로토콜 정의
│   └── market_serialize.py              # 시장 직렬화 클래스
└── README.md                            
```

## 🔧 핵심 기능

### **MarketTemplateImpl 클래스**
- **종목 검색**: `on_market_security_search_req()` - 종목명, 거래소, 섹터 기반 종목 검색, 검색 기록 저장
- **시세 조회**: `on_market_price_req()` - 다중 종목 시세 데이터 및 기술적 지표 조회
- **뉴스 분석**: `on_market_news_req()` - 카테고리별 뉴스 조회, 감정 분석, 관련 종목 매핑
- **시장 개요**: `on_market_overview_req()` - 주요 지수 현황, 상승/하락 종목, 거래량 많은 종목, 시장 심리 분석
- **실시간 데이터**: `on_market_real_time_req()` - 웹소켓 기반 실시간 시장 데이터 및 포트폴리오 데이터 처리

### **웹소켓 데이터 핸들러**
- **`_handle_market_data()`**: KOSPI(0001), KOSDAQ(1001) 지수 실시간 데이터 처리
- **`_handle_stock_data()`**: 개별 종목 실시간 데이터 처리 및 포트폴리오 데이터 업데이트

### **데이터 모델**
- **SecurityInfo**: 종목 코드, 종목명, 거래소, 섹터, 시가총액, 통화, 국가
- **PriceData**: 시세 데이터 (OHLCV, 변동금액, 변동률)
- **TechnicalIndicators**: RSI, MACD, 볼린저 밴드, 이동평균선 등 기술적 지표
- **NewsItem**: 뉴스 ID, 제목, 요약, 출처, 발행일시, 감정 점수, 관련 종목

## 🔄 Template-Service 연동

### **사용하는 Service 목록**
- **DatabaseService**: 샤드 DB 연동 및 저장 프로시저 호출 (call_shard_procedure, execute_global_query)

### **연동 방식 설명**
1. **데이터베이스 연동** → ServiceContainer.get_database_service()로 DatabaseService 획득, fp_search_securities, fp_get_price_data, fp_get_news, fp_get_market_overview 프로시저 호출
2. **웹소켓 데이터 처리** → 내부 웹소켓 핸들러(_handle_market_data, _handle_stock_data)를 통한 실시간 데이터 수신 및 저장
3. **API 키 관리** → table_user_api_keys 테이블에서 한국투자증권 API 키 조회 (실제 API 호출은 미구현)

## 📊 데이터 흐름

### **종목 검색 플로우**
```
1. 종목 검색 요청
   ↓
2. fp_search_securities 프로시저 호출 (검색어, 거래소, 섹터, 제한수)
   ↓
3. 검색 결과 데이터 파싱 및 SecurityInfo 모델 생성
   ↓
4. fp_save_search_history 프로시저로 검색 기록 저장
   ↓
5. MarketSecuritySearchResponse 반환
```

### **시세 조회 플로우**
```
1. 시세 조회 요청
   ↓
2. fp_get_price_data 프로시저로 가격 데이터 조회
   ↓
3. fp_get_technical_indicators 프로시저로 기술적 지표 조회
   ↓
4. PriceData와 TechnicalIndicators 모델 생성
   ↓
5. MarketPriceResponse 반환
```

### **뉴스 분석 플로우**
```
1. 뉴스 조회 요청
   ↓
2. fp_get_news 프로시저로 뉴스 데이터 조회 (종목, 카테고리, 페이지, 제한수)
   ↓
3. 뉴스 데이터, 총 개수, 감정 분석 요약 데이터 파싱
   ↓
4. NewsItem 모델 생성 및 감정 점수 기반 분류
   ↓
5. MarketNewsResponse 반환
```

### **시장 개요 플로우**
```
1. 시장 개요 요청
   ↓
2. fp_get_market_overview 프로시저로 주요 지수 데이터 조회
   ↓
3. 상승/하락 종목 분류 (3% 기준), 거래량 많은 종목 분류 (100만주 기준)
   ↓
4. 시장 심리 계산 (평균 변동률 기반 BULLISH/NEUTRAL/BEARISH)
   ↓
5. fp_save_market_analysis 프로시저로 분석 결과 저장
   ↓
6. MarketOverviewResponse 반환
```

### **실시간 데이터 플로우**
```
1. 실시간 데이터 요청
   ↓
2. table_user_api_keys에서 한국투자증권 API 키 조회
   ↓
3. 구버전 웹소켓 매니저 → 새로운 WebSocket 시스템 전환 안내
   ↓
4. API 키 없거나 실패 시 빈 데이터 반환 (N/A 표시)
   ↓
5. MarketRealTimeResponse 반환
```

## 🚀 사용 예제

### **종목 검색 예제**
```python
async def on_market_security_search_req(self, client_session, request: MarketSecuritySearchRequest):
    """종목 검색 요청 처리"""
    response = MarketSecuritySearchResponse()
    
    try:
        account_db_key = client_session.session.account_db_key
        shard_id = client_session.session.shard_id
        
        db_service = ServiceContainer.get_database_service()
        
        # 1. 종목 검색 DB 프로시저 호출
        search_result = await db_service.call_shard_procedure(
            shard_id,
            "fp_search_securities",
            (request.query, request.exchange, request.sector, request.limit)
        )
        
        if not search_result:
            response.securities = []
            response.total_count = 0
            response.errorCode = 0
            return response
        
        # 2. 검색 기록 저장
        await db_service.call_shard_procedure(
            shard_id,
            "fp_save_search_history",
            (account_db_key, request.query, "SECURITIES")
        )
        
        # 3. DB 결과를 바탕으로 응답 생성
        from template.market.common.market_model import SecurityInfo
        securities_data = search_result[0] if isinstance(search_result[0], list) else search_result
        total_count_data = search_result[1] if len(search_result) > 1 else {}
        
        response.securities = []
        for security in securities_data:
            response.securities.append(SecurityInfo(
                symbol=security.get('symbol'),
                name=security.get('name'),
                exchange=security.get('exchange'),
                sector=security.get('sector'),
                industry=security.get('industry'),
                market_cap=security.get('market_cap', 0),
                currency=security.get('currency', 'KRW'),
                description=security.get('description', '')
            ))
        
        response.total_count = total_count_data.get('total_count', len(response.securities))
        response.errorCode = 0
        
    except Exception as e:
        response.errorCode = 1000
        response.securities = []
        response.total_count = 0
        Logger.error(f"Market security search error: {e}")
    
    return response
```

### **시세 조회 예제**
```python
async def on_market_price_req(self, client_session, request: MarketPriceRequest):
    """시세 조회 요청 처리"""
    response = MarketPriceResponse()
    
    try:
        account_db_key = client_session.session.account_db_key
        shard_id = client_session.session.shard_id
        
        db_service = ServiceContainer.get_database_service()
        
        # 1. 가격 데이터 조회 DB 프로시저 호출
        price_result = await db_service.call_shard_procedure(
            shard_id,
            "fp_get_price_data",
            (json.dumps(request.symbols), request.period, request.interval)
        )
        
        # 2. 기술적 지표 조회 DB 프로시저 호출
        tech_result = await db_service.call_shard_procedure(
            shard_id,
            "fp_get_technical_indicators",
            (json.dumps(request.symbols),)
        )
        
        # 3. 응답 데이터 구성
        from template.market.common.market_model import PriceData, TechnicalIndicators
        
        response.price_data = {}
        if price_result:
            for price_item in price_result:
                symbol = price_item.get('symbol')
                if symbol not in response.price_data:
                    response.price_data[symbol] = []
                
                response.price_data[symbol].append(PriceData(
                    symbol=symbol,
                    timestamp=str(price_item.get('timestamp')),
                    open=float(price_item.get('open_price', 0)),
                    high=float(price_item.get('high_price', 0)),
                    low=float(price_item.get('low_price', 0)),
                    close=float(price_item.get('close_price', 0)),
                    volume=int(price_item.get('volume', 0)),
                    change=float(price_item.get('change_amount', 0)),
                    change_percent=float(price_item.get('change_rate', 0))
                ))
        
        response.technical_indicators = {}
        if tech_result:
            for tech_item in tech_result:
                symbol = tech_item.get('symbol')
                response.technical_indicators[symbol] = TechnicalIndicators(
                    symbol=symbol,
                    rsi=float(tech_item.get('rsi', 0)),
                    macd=float(tech_item.get('macd', 0)),
                    macd_signal=float(tech_item.get('macd_signal', 0)),
                    bollinger_upper=float(tech_item.get('bollinger_upper', 0)),
                    bollinger_middle=float(tech_item.get('bollinger_middle', 0)),
                    bollinger_lower=float(tech_item.get('bollinger_lower', 0)),
                    ma5=float(tech_item.get('ma5', 0)),
                    ma20=float(tech_item.get('ma20', 0)),
                    ma60=float(tech_item.get('ma60', 0))
                )
        response.errorCode = 0
        
    except Exception as e:
        response.errorCode = 1000
        response.price_data = {}
        response.technical_indicators = {}
        Logger.error(f"Market price error: {e}")
    
    return response
```

### **웹소켓 데이터 핸들러 예제**
```python
async def _handle_market_data(self, data):
    """웹소켓 시장 데이터 핸들러"""
    try:
        Logger.info(f"웹소켓 시장 데이터 수신: {data}")
        if 'body' in data and 'output' in data['body']:
            output = data['body']['output']
            index_code = data.get('tr_key', '')
            
            if index_code == '0001':  # KOSPI
                self._received_market_data['kospi'] = {
                    'current_price': float(output.get('stck_prpr', 0)),
                    'change_amount': float(output.get('prdy_vrss', 0)),
                    'change_rate': float(output.get('prdy_ctrt', 0)),
                    'volume': int(output.get('acml_vol', 0))
                }
            elif index_code == '1001':  # KOSDAQ
                self._received_market_data['kosdaq'] = {
                    'current_price': float(output.get('stck_prpr', 0)),
                    'change_amount': float(output.get('prdy_vrss', 0)),
                    'change_rate': float(output.get('prdy_ctrt', 0)),
                    'volume': int(output.get('acml_vol', 0))
                }
    except Exception as e:
        Logger.error(f"웹소켓 시장 데이터 처리 에러: {e}")
```

## ⚙️ 설정

### **데이터베이스 프로시저 설정**
- **fp_search_securities**: 종목 검색 (검색어, 거래소, 섹터, 제한수)
- **fp_save_search_history**: 검색 기록 저장 (계정, 검색어, 검색 타입)
- **fp_get_price_data**: 시세 데이터 조회 (종목, 기간, 간격)
- **fp_get_technical_indicators**: 기술적 지표 조회 (종목)
- **fp_get_news**: 뉴스 데이터 조회 (종목, 카테고리, 페이지, 제한수)
- **fp_get_market_overview**: 시장 개요 데이터 조회 (지수)
- **fp_save_market_analysis**: 시장 분석 결과 저장 (계정, 분석 타입, 데이터)

### **웹소켓 설정**
- **구버전 시스템**: 한국투자증권 웹소켓 매니저 (더 이상 사용되지 않음)
- **새로운 시스템**: /api/dashboard/market/ws 엔드포인트 사용 권장
- **지수 코드**: 0001 (KOSPI), 1001 (KOSDAQ)

### **시장 분석 설정**
- **상승 종목 기준**: 변동률 > 3.0%
- **하락 종목 기준**: 변동률 < -3.0%
- **거래량 많은 종목 기준**: 거래량 > 1,000,000주
- **시장 심리 기준**: 평균 변동률 > 1.0% (BULLISH), < -1.0% (BEARISH), 그 외 (NEUTRAL)

### **기술적 지표 설정**
- **이동평균선**: MA5, MA20, MA60
- **RSI**: 상대강도지수
- **MACD**: 이동평균수렴확산지수
- **볼린저 밴드**: 상단, 중간, 하단 밴드

## 🔗 연관 폴더

### **의존성 관계**
- **`service.db.database_service`**: DatabaseService - 샤드 DB 연동 및 저장 프로시저 호출
- **`service.websocket.websocket_service`**: WebSocketService - 실시간 시장 데이터 스트리밍

### **기본 템플릿 연관**
- **`template.base.base_template`**: BaseTemplate - 기본 템플릿 클래스 상속
- **`template.base.client_session`**: ClientSession - 클라이언트 세션 관리

### **외부 서비스 연동**
- **한국투자증권 API**: 실시간 시장 데이터 및 웹소켓 연동
- **새로운 WebSocket 시스템**: /api/dashboard/market/ws 엔드포인트

---
