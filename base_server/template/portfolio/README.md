# 📁 Portfolio Template

## 📌 개요
Portfolio Template은 사용자의 투자 포트폴리오 관리, 종목 추가/삭제, 리밸런싱 분석, 성과 분석 등을 담당하는 템플릿입니다. 샤드 DB를 통한 포트폴리오 데이터 관리, DB 저장 프로시저를 활용한 포트폴리오 연산, 그리고 실시간 성과 지표 계산을 제공합니다.

## 🏗️ 구조
```
base_server/template/portfolio/
├── portfolio_template_impl.py          # 포트폴리오 템플릿 구현체
├── common/                             # 공통 모델 및 프로토콜
│   ├── __init__.py
│   ├── portfolio_model.py             # 포트폴리오 데이터 모델
│   ├── portfolio_protocol.py          # 포트폴리오 프로토콜 정의
│   └── portfolio_serialize.py         # 포트폴리오 직렬화 클래스
└── README.md                           
```

## 🔧 핵심 기능

### **PortfolioTemplateImpl 클래스**
- **포트폴리오 조회**: `on_portfolio_get_req()` - 포트폴리오 정보, 보유 종목, 선택적 성과 지표 조회 (include_performance 파라미터에 따라)
- **종목 추가**: `on_portfolio_add_stock_req()` - 신규 종목 매수 주문 생성 및 잔고 검증
- **종목 삭제**: `on_portfolio_remove_stock_req()` - 보유 종목 매도 주문 생성 및 수량 검증
- **리밸런싱 분석**: `on_portfolio_rebalance_req()` - 목표 배분 대비 1% 이상 차이나는 종목에 대한 리밸런싱 권장사항 생성
- **성과 분석**: `on_portfolio_performance_req()` - 기간별 성과 지표 계산, KOSPI 벤치마크 비교, 위험 지표 산출 (변동성, VaR, 추적 오차 등)

### **주요 메서드**
- `on_portfolio_get_req()`: 포트폴리오 기본 정보, 보유 종목, 선택적 성과 지표 조회 (request.include_performance에 따라 조건부 처리)
- `on_portfolio_add_stock_req()`: 계좌 잔고 확인, 매수 주문 생성, 주문 ID 생성 (UUID 기반: ord_{uuid.hex[:16]})
- `on_portfolio_remove_stock_req()`: 보유 수량 검증, 매도 주문 생성, 수량 부족 검증
- `on_portfolio_rebalance_req()`: 현재 포트폴리오 구성 분석, 목표 배분 대비 1% 이상 차이나는 종목에 대한 거래 권장사항 생성, 0.25% 수수료 포함 비용 추정
- `on_portfolio_performance_req()`: 포트폴리오 성과 기록 (fp_record_portfolio_performance), 기간별 성과 지표 계산 (1D~1Y), KOSPI 대비 성과 비교, 위험 지표 산출 (변동성, VaR 95%, 추적 오차, 정보 비율)

## 🔄 Template-Service 연동

### **사용하는 Service 목록**
- **ServiceContainer**: DatabaseService 접근을 위한 서비스 컨테이너
- **DatabaseService**: 샤드 DB 연동 및 저장 프로시저 호출
- **Logger**: 로깅 서비스

### **연동 방식 설명**
1. **포트폴리오 조회** → DatabaseService를 통한 샤드 DB 프로시저 호출 (`fp_get_portfolio_extended`, `fp_get_portfolio_performance`)
2. **종목 거래** → DatabaseService를 통한 주문 생성 (`fp_create_stock_order`)
3. **계좌 정보** → DatabaseService를 통한 계좌 잔고 조회 (`fp_get_account_info`)
4. **리밸런싱** → DatabaseService를 통한 리밸런싱 리포트 생성 (`fp_create_rebalance_report`)
5. **성과 기록** → DatabaseService를 통한 포트폴리오 성과 저장 (`fp_record_portfolio_performance`)

## 📊 데이터 흐름

### **Request → Template → Service → Response**

```
1. 포트폴리오 요청 (Request)
   ↓
2. PortfolioTemplateImpl.on_*_req()
   ↓
3. ServiceContainer.get_database_service()로 DatabaseService 획득
   ↓
4. 샤드 DB 프로시저 호출 (call_shard_procedure)
   ↓
5. DB 결과 파싱 및 모델 객체 생성
   ↓
6. 포트폴리오 응답 (Response)
```

### **포트폴리오 조회 플로우**
```
1. 포트폴리오 조회 요청 (include_performance, include_holdings)
   ↓
2. 계좌 정보 조회 (fp_get_account_info)
   ↓
3. 포트폴리오 확장 정보 조회 (fp_get_portfolio_extended)
   ↓
4. 보유 종목 정보 추출 (portfolio_result[1:])
   ↓
5. 성과 지표 조회 (fp_get_portfolio_performance, include_performance=True인 경우)
   ↓
6. Portfolio, StockHolding, PerformanceMetrics 모델 생성
   ↓
7. PortfolioGetResponse 반환
```

### **종목 추가 플로우**
```
1. 종목 추가 요청 (symbol, quantity, price, order_type)
   ↓
2. 계좌 잔고 확인 (fp_get_account_info)
   ↓
3. 잔고 부족 검증 (required_amount vs account_balance)
   ↓
4. 주문 ID 생성 (UUID 기반: ord_{uuid.hex[:16]})
   ↓
5. 매수 주문 생성 (fp_create_stock_order)
   ↓
6. StockOrder 모델 생성 및 응답
```

### **종목 삭제 플로우**
```
1. 종목 삭제 요청 (symbol, quantity, price)
   ↓
2. 현재 포트폴리오 구성 조회 (fp_get_portfolio_extended)
   ↓
3. 보유 수량 확인 및 검증
   ↓
4. 수량 부족 검증 (request.quantity vs holding_quantity)
   ↓
5. 매도 주문 생성 (fp_create_stock_order, order_type="SELL")
   ↓
6. StockOrder 모델 생성 및 응답
```

### **리밸런싱 분석 플로우**
```
1. 리밸런싱 요청 (target_allocation, min_trade_amount)
   ↓
2. 현재 포트폴리오 구성 조회 (fp_get_portfolio_extended)
   ↓
3. 리밸런싱 리포트 생성 (fp_create_rebalance_report)
   ↓
4. 목표 배분 대비 현재 배분 차이 계산
   ↓
5. 1% 이상 차이나는 종목에 대한 거래 권장사항 생성
   ↓
6. RebalanceReport 모델 생성 및 응답
```

### **성과 분석 플로우**
```
1. 성과 분석 요청 (period, benchmark, include_chart)
   ↓
2. 현재 포트폴리오 가치 계산 (fp_get_portfolio_extended)
   ↓
3. 성과 데이터 DB 저장 (fp_record_portfolio_performance)
   ↓
4. 기간별 성과 지표 계산 (1D, 1W, 1M, 3M, 6M, 1Y)
   ↓
5. 벤치마크 비교 (KOSPI 대비 성과)
   ↓
6. 위험 지표 계산 (변동성, VaR, 추적 오차 등)
   ↓
7. PerformanceMetrics 모델 생성 및 응답
```

## 🚀 사용 예제

### **포트폴리오 조회 예제**
```python
# 포트폴리오 조회 요청 처리
async def on_portfolio_get_req(self, client_session, request: PortfolioGetRequest):
    """포트폴리오 조회 요청 처리"""
    response = PortfolioGetResponse()
    
    Logger.info("Portfolio get request received")
    
    try:
        account_db_key = client_session.session.account_db_key
        shard_id = client_session.session.shard_id
        
        db_service = ServiceContainer.get_database_service()
        
        # 1. 계좌 정보 조회
        account_result = await db_service.call_shard_procedure(
            shard_id,
            "fp_get_account_info",
            (account_db_key,)
        )
        
        # 2. 포트폴리오 확장 정보 조회 (DB 프로시저 활용)
        portfolio_result = await db_service.call_shard_procedure(
            shard_id,
            "fp_get_portfolio_extended",
            (account_db_key, request.include_performance, True)
        )
        
        if not portfolio_result:
            response.errorCode = 2003
            Logger.info("No portfolio found")
            return response
        
        # DB에서 조회된 실제 포트폴리오 데이터 사용
        portfolio_data = portfolio_result[0] if portfolio_result else {}
        
        # Portfolio 모델 생성
        portfolio = Portfolio(
            portfolio_id=portfolio_data.get('portfolio_id', f"portfolio_{account_db_key}"),
            name=portfolio_data.get('name', '메인 포트폴리오'),
            total_value=float(portfolio_data.get('total_value', 0.0)),
            cash_balance=float(portfolio_data.get('cash_balance', 0.0)),
            invested_amount=float(portfolio_data.get('invested_amount', 0.0)),
            total_return=float(portfolio_data.get('total_return', 0.0)),
            return_rate=float(portfolio_data.get('return_rate', 0.0)),
            created_at=str(portfolio_data.get('created_at', datetime.now()))
        )
        
        response.portfolio = portfolio
        
        # 보유 종목 정보도 DB 프로시저 결과에서 가져오기
        if len(portfolio_result) > 1:
            response.holdings = portfolio_result[1:]  # 첫 번째는 포트폴리오 정보, 나머지는 보유종목
        else:
            response.holdings = []
        
        response.errorCode = 0
        Logger.info(f"Portfolio retrieved successfully for account_db_key: {account_db_key}")
        
    except Exception as e:
        response.errorCode = 1000
        Logger.error(f"Portfolio get error: {e}")
    
    return response
```

### **종목 추가 예제**
```python
# 종목 추가 요청 처리
async def on_portfolio_add_stock_req(self, client_session, request: PortfolioAddStockRequest):
    """종목 추가 요청 처리"""
    response = PortfolioAddStockResponse()
    
    Logger.info(f"Portfolio add stock request: {request.symbol}")
    
    try:
        account_db_key = client_session.session.account_db_key
        shard_id = client_session.session.shard_id
        
        db_service = ServiceContainer.get_database_service()
        
        # 주문 ID 생성
        order_id = f"ord_{uuid.uuid4().hex[:16]}"
        
        # 1. 계좌 잔고 확인
        account_info = await db_service.call_shard_procedure(
            shard_id,
            "fp_get_account_info",
            (account_db_key,)
        )
        
        if not account_info or len(account_info) == 0:
            response.errorCode = 3001
            response.message = "계좌 정보를 찾을 수 없습니다"
            return response
        
        account_balance = float(account_info[0].get('balance', 0.0))
        required_amount = request.quantity * request.price
        
        if account_balance < required_amount:
            response.errorCode = 3002
            response.message = f"잔고 부족: 필요 {required_amount:,.0f}원, 보유 {account_balance:,.0f}원"
            return response
        
        # 2. 주식 주문 생성 (DB 저장)
        order_result = await db_service.call_shard_procedure(
            shard_id,
            "fp_create_stock_order",
            (order_id, account_db_key, request.symbol, "BUY", 
             request.order_type or "MARKET", request.quantity, request.price, 
             None, 0.0)  # stop_price, commission
        )
        
        if not order_result or order_result[0].get('result') != 'SUCCESS':
            response.errorCode = 3003
            response.message = "주문 생성 실패"
            return response
        
        # DB 결과를 바탕으로 주문 정보 생성
        order_data = order_result[0]
        stock_order = StockOrder(
            order_id=order_data.get('order_id', order_id),
            symbol=request.symbol,
            order_type="BUY",
            quantity=request.quantity,
            price=request.price,
            order_status=order_data.get('order_status', 'PENDING'),
            created_at=str(order_data.get('order_time', datetime.now()))
        )
        
        response.order = stock_order
        response.message = "종목 추가 주문이 생성되었습니다"
        response.errorCode = 0
        
        Logger.info(f"Stock order created: {order_id}")
        
    except Exception as e:
        response.errorCode = 1000
        response.message = "종목 추가 실패"
        Logger.error(f"Portfolio add stock error: {e}")
    
    return response
```

## ⚙️ 설정

### **DB 저장 프로시저**
- **포트폴리오 조회**: `fp_get_portfolio_extended(account_db_key, include_performance, include_holdings)`
- **계좌 정보**: `fp_get_account_info(account_db_key)`
- **성과 지표**: `fp_get_portfolio_performance(account_db_key, period)`
- **주문 생성**: `fp_create_stock_order(order_id, account_db_key, symbol, order_type, price_type, quantity, price, stop_price, commission)`
- **리밸런싱 리포트**: `fp_create_rebalance_report(account_db_key, trigger_reason, target_allocation, min_trade_amount)`
- **성과 기록**: `fp_record_portfolio_performance(account_db_key, date, total_value, cash_balance, invested_amount)`

### **포트폴리오 모델 설정**
- **Portfolio**: portfolio_id, name, total_value, cash_balance, invested_amount, total_return, return_rate, created_at
- **StockHolding**: symbol, name, quantity, avg_price, current_price, market_value, unrealized_pnl, return_rate, weight
- **StockOrder**: order_id, symbol, order_type, price_type, quantity, price, stop_price, filled_quantity, avg_fill_price, order_status, order_source, commission, order_time, fill_time
- **PerformanceMetrics**: total_return, annualized_return, sharpe_ratio, max_drawdown, volatility, win_rate, profit_factor, benchmark_return
- **RebalanceReport**: report_id, trigger_reason, recommendations, expected_improvement, target_allocation, trades_required, estimated_cost, status, generated_at, applied_at

### **에러 코드**
- **2003**: 포트폴리오를 찾을 수 없음
- **3001**: 계좌 정보를 찾을 수 없음
- **3002**: 잔고 부족
- **3003**: 주문 생성 실패
- **3004**: 보유 종목이 없음
- **3005**: 해당 종목을 보유하고 있지 않음
- **3006**: 보유 수량 부족
- **3007**: 매도 주문 생성 실패
- **4001**: 리밸런싱을 위한 포트폴리오가 없음
- **4002**: 리밸런싱 리포트 생성 실패
- **5001**: 성과 분석을 위한 포트폴리오가 없음
- **5002**: 포트폴리오 성과 기록 실패

### **기본값 설정**
- **포트폴리오 이름**: "메인 포트폴리오" (portfolio_data.get('name', '메인 포트폴리오'))
- **주문 타입**: "MARKET" (시장가) (request.order_type or "MARKET")
- **최소 거래 금액**: 10,000원 (min_trade_amount 기본값)
- **성과 분석 기간**: "1Y" (1년) (request.period or '1Y')
- **벤치마크**: "KOSPI" (request.benchmark 기본값, 코드에서 8.0% 수익률로 예시)
- **수수료**: 0.25% (리밸런싱 계산 시: quantity * 0.0025)

## 🔗 연관 폴더

### **의존성 관계**
- **`service.service_container`**: ServiceContainer - 서비스 컨테이너 및 DatabaseService 접근
- **`service.core.logger`**: Logger - 로깅 서비스

### **데이터 흐름 연관**
- **`template.account`**: 계정 정보 및 샤드 ID 제공 (`client_session.session.account_db_key`, `client_session.session.shard_id`)
- **`template.dashboard`**: StockHolding 모델 공유 (`from template.dashboard.common.dashboard_model import StockHolding`)

### **기본 템플릿 연관**
- **`template.base.base_template`**: BaseTemplate - 기본 템플릿 클래스

---
