# 📁 AutoTrade Template

## 📌 개요
AutoTrade Template은 자동매매 전략 실행, 시그널 알림 관리, 야후 파이낸스 데이터 연동을 담당하는 템플릿입니다. 사용자별 시그널 알림 등록/관리, 실시간 주식 데이터 조회, 그리고 자동매매 시그널 히스토리 추적을 제공합니다. DatabaseService와 YahooFinanceClient를 활용한 자동매매 인프라를 구축합니다.

## 🏗️ 구조
```
base_server/template/autotrade/
├── autotrade_template_impl.py          # 자동매매 템플릿 구현체
├── common/                             # 공통 모델 및 프로토콜
│   ├── __init__.py
│   ├── autotrade_model.py             # 자동매매 데이터 모델
│   ├── autotrade_protocol.py          # 자동매매 프로토콜 정의
│   └── autotrade_serialize.py         # 자동매매 직렬화 클래스
└── README.md                           
```

## 🔧 핵심 기능

### **AutoTradeTemplateImpl 클래스**
- **야후 파이낸스 검색**: `on_autotrade_yahoo_search_req()` - 주식 종목 검색 및 결과 반환
- **야후 파이낸스 상세**: `on_autotrade_yahoo_detail_req()` - 종목별 상세 가격 정보 조회
- **시그널 알림 등록**: `on_signal_alarm_create_req()` - 자동매매 시그널 알림 생성 및 DB 저장
- **시그널 알림 목록**: `on_signal_alarm_list_req()` - 사용자별 등록된 알림 목록 조회 (통계 포함)
- **시그널 알림 토글**: `on_signal_alarm_toggle_req()` - 알림 수신 ON/OFF 상태 변경
- **시그널 알림 삭제**: `on_signal_alarm_delete_req()` - 소프트 삭제로 알림 완전 제거
- **시그널 히스토리**: `on_signal_history_req()` - 자동매매 시그널 발생 이력 및 성과 조회

### **주요 메서드**
- `on_autotrade_yahoo_search_req()`: ServiceContainer.get_cache_service()로 CacheService 획득, YahooFinanceClient를 통한 주식 검색, SearchResult 객체를 dictionary로 변환
- `on_autotrade_yahoo_detail_req()`: symbol 유효성 검사, YahooFinanceClient를 통한 종목별 상세 가격 데이터 조회, 에러 시 기본값으로 응답 구성
- `on_signal_alarm_create_req()`: 세션 정보 검증 (account_db_key, shard_id), Yahoo Finance 종목 정보 조회, UUID 기반 alarm_id 생성, fp_signal_alarm_create 프로시저 호출
- `on_signal_alarm_list_req()`: fp_signal_alarms_get_with_stats 프로시저로 통계 정보 포함 알림 목록 조회, 결과 파싱하여 SignalAlarmInfo 리스트 생성
- `on_signal_alarm_toggle_req()`: fp_signal_alarm_toggle 프로시저로 알림 활성화 상태 변경, 프로시저 반환값의 new_status로 is_active 설정
- `on_signal_alarm_delete_req()`: fp_signal_alarm_soft_delete 프로시저로 소프트 삭제 처리, 삭제 성공 시 응답 메시지 설정
- `on_signal_history_req()`: fp_signal_history_get 프로시저로 필터링된 시그널 히스토리 조회, alarm_id, symbol, signal_type, limit 파라미터 지원

## 🔄 Template-Service 연동

### **사용하는 Service 목록**
- **ServiceContainer**: CacheService 및 DatabaseService 접근을 위한 서비스 컨테이너
- **CacheService**: YahooFinanceClient 생성 시 캐시 서비스 전달 (ServiceContainer.get_cache_service())
- **DatabaseService**: 샤드 DB 연동 및 저장 프로시저 호출 (ServiceContainer.get_database_service())
- **YahooFinanceClient**: 야후 파이낸스 API 연동 및 주식 데이터 수집 (service.external.yahoo_finance_client)
- **Logger**: 로깅 서비스 (service.core.logger)

### **연동 방식 설명**
1. **야후 파이낸스 연동** → ServiceContainer.get_cache_service()로 CacheService 획득, YahooFinanceClient(cache_service) 생성 및 데이터 조회
2. **시그널 알림 관리** → ServiceContainer.get_database_service()로 DatabaseService 획득, 샤드 DB 저장 프로시저 호출 (`fp_signal_alarm_*`)
3. **데이터 처리** → YahooFinanceClient 응답 데이터를 asdict()를 사용하여 dictionary로 변환, 프론트엔드 호환성 확보
4. **세션 관리** → client_session.session에서 account_db_key, shard_id 획득, getattr()로 기본값 설정

## 📊 데이터 흐름

### **Request → Template → Service → Response**

```
1. 자동매매 요청 (Request)
   ↓
2. AutoTradeTemplateImpl.on_*_req()
   ↓
3. ServiceContainer.get_cache_service() 또는 ServiceContainer.get_database_service()로 서비스 획득
   ↓
4. YahooFinanceClient(cache_service) 또는 call_shard_procedure() 호출
   ↓
5. 응답 데이터 파싱 및 모델 객체 생성 (asdict(), 프로시저 결과 파싱)
   ↓
6. 자동매매 응답 (Response)
```

### **야후 파이낸스 검색 플로우**
```
1. 주식 검색 요청 (query)
   ↓
2. ServiceContainer.get_cache_service()로 CacheService 획득
   ↓
3. YahooFinanceClient(cache_service) 생성 및 client.search_stocks() 호출
   ↓
4. SearchResult.securities를 asdict()로 dictionary 변환
   ↓
5. AutoTradeYahooSearchResponse 반환
```

### **시그널 알림 등록 플로우**
```
1. 시그널 알림 등록 요청 (symbol, note)
   ↓
2. getattr()로 세션 정보 검증 (account_db_key, shard_id)
   ↓
3. ServiceContainer.get_cache_service()로 YahooFinanceClient 생성, 종목 정보 조회 및 검증
   ↓
4. str(uuid.uuid4())로 alarm_id 생성, Decimal('0.000001') 정밀도로 가격 처리
   ↓
5. ServiceContainer.get_database_service()로 fp_signal_alarm_create 프로시저 호출
   ↓
6. 프로시저 결과 파싱하여 SignalAlarmInfo 모델 생성 및 응답
```

### **시그널 알림 목록 조회 플로우**
```
1. 알림 목록 조회 요청
   ↓
2. getattr()로 세션 정보 검증 (account_db_key, shard_id)
   ↓
3. ServiceContainer.get_database_service()로 fp_signal_alarms_get_with_stats 프로시저 호출
   ↓
4. 프로시저 결과 파싱하여 통계 정보 포함 SignalAlarmInfo 리스트 생성
   ↓
5. 결과 개수에 따른 메시지 설정 및 응답
```

### **시그널 히스토리 조회 플로우**
```
1. 히스토리 조회 요청 (alarm_id, symbol, signal_type, limit)
   ↓
2. getattr()로 세션 정보 검증 (account_db_key, shard_id)
   ↓
3. ServiceContainer.get_database_service()로 fp_signal_history_get 프로시저 호출
   ↓
4. 프로시저 결과 파싱하여 SignalHistoryItem 리스트 생성 (첫 번째는 상태, 나머지는 데이터)
   ↓
5. total_count 설정 및 응답
```

## 🚀 사용 예제

### **야후 파이낸스 검색 예제**
```python
# 주식 검색 요청 처리
from service.core.logger import Logger
from service.service_container import ServiceContainer
from service.external.yahoo_finance_client import YahooFinanceClient
from dataclasses import asdict

async def on_autotrade_yahoo_search_req(self, client_session, request: AutoTradeYahooSearchRequest):
    """야후 파이낸스 주식 검색"""
    response = AutoTradeYahooSearchResponse()
    response.sequence = request.sequence
    
    Logger.info(f"Yahoo Finance search request: query={request.query}")
    
    try:
        cache_service = ServiceContainer.get_cache_service()
        async with YahooFinanceClient(cache_service) as client:
            result = await client.search_stocks(request.query)
            
            # SearchResult 객체의 필드에 직접 접근
            response.errorCode = result.errorCode
            
            # StockQuote 객체들을 dictionary로 변환
            response.results = [asdict(stock) for stock in result.securities]
            
            # 에러가 있을 경우 로깅만 수행
            if response.errorCode != 0:
                Logger.warn(f"Search returned error: {result.message}")
                
    except Exception as e:
        Logger.error(f"Yahoo Finance search error: {e}")
        response.errorCode = 1
        response.results = []
    
    return response
```

### **시그널 알림 등록 예제**
```python
# 시그널 알림 등록 요청 처리
from service.core.logger import Logger
from service.service_container import ServiceContainer
from service.external.yahoo_finance_client import YahooFinanceClient
from template.autotrade.common.autotrade_model import SignalAlarmInfo
from dataclasses import asdict
import uuid
from decimal import Decimal, ROUND_HALF_UP

async def on_signal_alarm_create_req(self, client_session, request: SignalAlarmCreateRequest):
    """시그널 알림 등록"""
    response = SignalAlarmCreateResponse()
    response.sequence = request.sequence
    
    try:
        # 세션 정보 조회
        account_db_key = getattr(client_session.session, 'account_db_key', 0)
        if account_db_key == 0:
            response.errorCode = 1001
            response.message = "유효하지 않은 세션입니다"
            return response
        
        shard_id = getattr(client_session.session, 'shard_id', 1)

        # Yahoo Finance에서 종목 정보 조회
        cache_service = ServiceContainer.get_cache_service()
        async with YahooFinanceClient(cache_service) as client:
            stock_detail = await client.get_stock_detail(request.symbol)
            
            if stock_detail is None:
                response.errorCode = 1004
                response.message = f"종목 정보를 찾을 수 없습니다: {request.symbol}"
                return response
        
        # UUID 생성 및 데이터 준비
        alarm_id = str(uuid.uuid4())
        stock_name = str(stock_detail.name) if stock_detail.name else str(request.symbol)
        current_price = (
            Decimal(str(stock_detail.current_price)).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
            if stock_detail.current_price is not None
            else Decimal('0.000000')
        )
        
        # 프로시저 파라미터 구성
        params = (
            alarm_id, account_db_key, str(request.symbol), stock_name,
            current_price, str(stock_detail.exchange), str(stock_detail.currency), str(request.note or "")
        )
        
        # DB 저장 프로시저 호출
        db_service = ServiceContainer.get_database_service()
        result = await db_service.call_shard_procedure(shard_id, "fp_signal_alarm_create", params)
        
        if not result:
            response.errorCode = 1002
            response.message = "알림 등록 중 오류가 발생했습니다"
            return response
        
        # 응답 처리
        proc_result = result[0]
        error_code = proc_result.get('ErrorCode', 1)
        response.errorCode = error_code
        
        if error_code == 0:
            response.message = "알림이 성공적으로 등록되었습니다"
            response.alarm_id = alarm_id
            response.alarm_info = SignalAlarmInfo(
                alarm_id=alarm_id, symbol=str(request.symbol), company_name=stock_name,
                current_price=float(current_price), is_active=True, signal_count=0,
                win_rate=0.0, profit_rate=0.0
            )
            Logger.info(f"Signal alarm created: user={account_db_key}, symbol={request.symbol}, alarm_id={alarm_id}")
        else:
            response.message = error_message
            Logger.warn(f"Signal alarm creation failed: {error_message}")
        
    except Exception as e:
        Logger.error(f"Signal alarm create error: {e}")
        response.errorCode = 1003
        response.message = f"알림 등록 중 오류가 발생했습니다: {str(e)}"
    
    return response
```

## ⚙️ 설정

### **DB 저장 프로시저**
- **시그널 알림 생성**: `fp_signal_alarm_create(alarm_id, account_db_key, symbol, company_name, current_price, exchange, currency, note)`
- **시그널 알림 목록**: `fp_signal_alarms_get_with_stats(account_db_key)` - 통계 정보 포함
- **시그널 알림 토글**: `fp_signal_alarm_toggle(alarm_id, account_db_key)` - 활성화 상태 변경
- **시그널 알림 삭제**: `fp_signal_alarm_soft_delete(alarm_id, account_db_key)` - 소프트 삭제
- **시그널 히스토리**: `fp_signal_history_get(account_db_key, alarm_id, symbol, signal_type, limit)` - 필터링된 히스토리

### **자동매매 모델 설정**
- **SignalAlarmInfo**: alarm_id, symbol, company_name, current_price, exchange, currency, note, is_active, signal_count, win_rate, profit_rate, created_at
- **SignalHistoryItem**: signal_id, alarm_id, symbol, signal_type, signal_price, volume, triggered_at, price_after_1d, profit_rate, is_win, evaluated_at

### **요청/응답 모델 설정**
- **AutoTradeYahooSearchRequest**: query (필수)
- **AutoTradeYahooSearchResponse**: results (List[Dict[str, Any]])
- **AutoTradeYahooDetailRequest**: symbol (필수)
- **AutoTradeYahooDetailResponse**: price_data (Dict[str, Any])
- **SignalAlarmCreateRequest**: symbol (필수), note (선택)
- **SignalAlarmCreateResponse**: alarm_id, alarm_info, message
- **SignalAlarmListRequest**: 파라미터 없음
- **SignalAlarmListResponse**: alarms, total_count, active_count, message
- **SignalAlarmToggleRequest**: alarm_id (필수)
- **SignalAlarmToggleResponse**: alarm_id, is_active, message
- **SignalAlarmDeleteRequest**: alarm_id (필수)
- **SignalAlarmDeleteResponse**: alarm_id, message
- **SignalHistoryRequest**: alarm_id (선택), symbol (선택), signal_type (선택), limit (기본값: 50)
- **SignalHistoryResponse**: signals, total_count, message

### **에러 코드**
- **1001**: 유효하지 않은 세션
- **1002**: 프로시저 호출 실패
- **1003**: 일반적인 오류
- **1004**: 종목 정보를 찾을 수 없음

### **기본값 설정**
- **기본 샤드 ID**: 1 (getattr(client_session.session, 'shard_id', 1))
- **기본 계정 키**: 0 (getattr(client_session.session, 'account_db_key', 0))
- **가격 정밀도**: Decimal('0.000001') (금융권 표준, ROUND_HALF_UP 사용)
- **기본 거래소**: "NASDAQ" (autotrade_model.py의 SignalAlarmInfo 기본값)
- **기본 통화**: "USD" (autotrade_model.py의 SignalAlarmInfo 기본값)
- **히스토리 조회 제한**: 50개 (autotrade_serialize.py의 SignalHistoryRequest 기본값)

### **Yahoo Finance 연동 설정**
- **캐시 서비스**: ServiceContainer.get_cache_service()로 CacheService 획득하여 YahooFinanceClient 생성자에 전달
- **에러 처리**: 검색 실패 시 빈 results 리스트 반환, 상세 정보 실패 시 기본값으로 응답 구성 (current_price: 0.0, exchange: "NASDAQ", currency: "USD")
- **데이터 변환**: asdict()를 사용하여 SearchResult.securities의 StockQuote 객체들을 dictionary로 변환
- **응답 구조**: 프론트엔드 호환성을 위해 price_data에 symbol을 키로 하는 중첩 구조 사용

## 🔗 연관 폴더

### **의존성 관계**
- **`service.service_container`**: ServiceContainer - 서비스 컨테이너 및 CacheService/DatabaseService 접근
- **`service.cache.cache_service`**: CacheService - YahooFinanceClient 생성자에 전달
- **`service.db.database_service`**: DatabaseService - 샤드 DB 연동 및 저장 프로시저 호출
- **`service.external.yahoo_finance_client`**: YahooFinanceClient - 야후 파이낸스 API 연동
- **`service.core.logger`**: Logger - 로깅 서비스

### **데이터 흐름 연관**
- **`template.account`**: 계정 정보 및 샤드 ID 제공 (`client_session.session.account_db_key`, `client_session.session.shard_id`)
- **`template.portfolio`**: 포트폴리오 정보와 연동하여 자동매매 시그널 실행 (실제 코드에서 직접적인 의존성은 없음, 추후 연동 가능성)

### **기본 템플릿 연관**
- **`template.base.base_template`**: BaseTemplate - 기본 템플릿 클래스 (AutoTradeTemplateImpl이 상속)

### **외부 서비스 연동**
- **`service.external.yahoo_finance_client`**: Yahoo Finance API 클라이언트 (YahooFinanceClient)
- **`service.cache.cache_service`**: CacheService (ServiceContainer.get_cache_service()로 획득)

---