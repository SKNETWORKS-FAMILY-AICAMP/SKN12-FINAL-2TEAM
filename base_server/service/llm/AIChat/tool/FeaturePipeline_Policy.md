## FeaturePipeline 정책 정리

### 1. 정규화 (Normalization):
- `normalize=True` 옵션 사용 시 FeaturePipelineTool에서 통합적으로 처리합니다.
- **log1p 변환**: `GDP`, `CPIAUCSL`, `marketCap`, `news_count`
- **Z-score 표준화**: `RSI`, `MACD`, `VIX`, `priceEarningsRatio`, `returnOnEquity`, `positive_news_ratio`
- `normalize=False` 옵션 사용 시 어떤 전처리도 하지 않으며, 원시 값(raw value)을 반환합니다. 이 경우 피처는 원 단위(original unit)를 유지합니다.

### 2. 결측치 처리:
- 기본적으로 `NaN` 또는 `None` 값은 `0.0`으로 처리됩니다.
- 향후 마스킹(masking) 또는 다른 결측치 처리 전략을 옵션으로 추가할 수 있습니다.

### 3. 시계열 처리:
- 현재는 각 피처의 **최근 1개 시점 값**만 사용합니다.
- `PRICE_HISTORY`와 같이 시계열 데이터 자체를 반환하는 피처는 해당 툴에서 직접 처리해야 합니다.
- 향후 시계열 피처에 대한 주기(daily, weekly 등) 및 길이(length) 관리 로직을 별도로 설계할 예정입니다.
