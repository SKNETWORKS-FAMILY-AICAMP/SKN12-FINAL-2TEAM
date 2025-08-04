### 거시경제 지표 (MacroEconomicTool)
- `GDP`: 미국 국내총생산 (분기 기준, 연환산)
- `CPIAUCSL`: 소비자 물가지수
- `DEXKOUS`: 원/달러 환율

### 기술적 분석 (TechnicalAnalysisTool)
- `RSI`: 상대강도지수 (14일 기준)
- `MACD`: 이동평균 수렴확산
- `EMA`: 지수이동평균 (20일 기준)

### 재무 비율 (FinancialStatementTool)
- `priceEarningsRatio`: 주가수익비율
- `returnOnEquity`: 자기자본이익률
- `marketCap`: 시가총액 (달러 단위)

### 시장 데이터 (MarketDataTool)
- `VIX`: 변동성 지수
- `PRICE`: 최신 종가
- `PRICE_HISTORY`: 과거 가격 데이터 (Pandas DataFrame)

### 뉴스 분석 (NewsTool)
- `news_count`: 최근 수집된 뉴스 개수
- `positive_news_ratio`: 긍정 기사 비율 (NewsTool의 키워드 기반 감성 분석 결과)