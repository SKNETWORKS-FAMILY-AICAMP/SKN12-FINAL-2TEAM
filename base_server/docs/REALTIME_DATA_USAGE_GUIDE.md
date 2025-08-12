# 실시간 데이터 사용 가이드

## 개요

이 가이드는 대시보드에서 OAuth 인증과 실시간 데이터 구독/해제 기능을 사용하는 방법을 설명합니다.

## 기능

### 1. OAuth 인증
- 한국투자증권 API 키를 사용한 OAuth 인증
- 토큰 발급 및 관리

### 2. 실시간 데이터 구독/해제
- 종목별 실시간 데이터 구독
- 지수별 실시간 데이터 구독
- 동적 구독 추가/제거

## 사용 방법

### 1. OAuth 인증

```bash
# OAuth 인증 요청
curl -X POST http://localhost:8000/dashboard/oauth/authenticate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

**응답:**
```json
{
  "success": true,
  "message": "OAuth 인증 성공",
  "account_db_key": 1000
}
```

### 2. 실시간 데이터 구독

```bash
# Tesla, Microsoft, Nike 구독
curl -X POST http://localhost:8000/dashboard/realtime/subscribe \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["TSLA", "MSFT", "NKE"],
    "indices": ["0001", "1001"]
  }'
```

**응답:**
```json
{
  "success": true,
  "message": "구독 성공",
  "subscribed_symbols": ["TSLA", "MSFT", "NKE"],
  "subscribed_indices": ["0001", "1001"],
  "new_symbols": ["TSLA", "MSFT", "NKE"],
  "new_indices": ["0001", "1001"]
}
```

### 3. 실시간 데이터 구독 해제

```bash
# Nike 구독 해제
curl -X POST http://localhost:8000/dashboard/realtime/unsubscribe \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["NKE"],
    "indices": []
  }'
```

**응답:**
```json
{
  "success": true,
  "message": "구독 해제 성공",
  "subscribed_symbols": ["TSLA", "MSFT"],
  "subscribed_indices": ["0001", "1001"],
  "unsubscribed_symbols": ["NKE"],
  "unsubscribed_indices": []
}
```

### 4. 구독 상태 조회

```bash
curl -X GET http://localhost:8000/dashboard/realtime/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**응답:**
```json
{
  "is_authenticated": true,
  "is_connected": true,
  "subscribed_symbols": ["TSLA", "MSFT"],
  "subscribed_indices": ["0001", "1001"],
  "total_subscriptions": 4
}
```

### 5. 연결 해제

```bash
curl -X POST http://localhost:8000/dashboard/realtime/disconnect \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**응답:**
```json
{
  "success": true,
  "message": "연결 해제 완료"
}
```

## 프론트엔드 사용 예시

### 1. 대시보드에서 실시간 데이터 관리

```typescript
// 대시보드 페이지에서 실시간 데이터 관리 버튼 클릭
const [showRealtimeManager, setShowRealtimeManager] = useState(false);

// 실시간 데이터 관리 패널 표시
{showRealtimeManager && (
  <RealtimeDataManager 
    onDataUpdate={(data) => {
      console.log('실시간 데이터 업데이트:', data);
    }}
  />
)}
```

### 2. RealtimeDataManager 컴포넌트 사용

```typescript
import { RealtimeDataManager } from '@/components/dashboard/RealtimeDataManager';

// 컴포넌트에서 사용
<RealtimeDataManager 
  onDataUpdate={(data) => {
    // 실시간 데이터 처리
    updateMarketData(data);
  }}
/>
```

## 사용 시나리오

### 시나리오 1: Tesla, Microsoft 구독 후 Nike 추가

1. **OAuth 인증**
   ```bash
   POST /dashboard/oauth/authenticate
   ```

2. **Tesla, Microsoft 구독**
   ```bash
   POST /dashboard/realtime/subscribe
   {
     "symbols": ["TSLA", "MSFT"]
   }
   ```

3. **Nike 추가 구독**
   ```bash
   POST /dashboard/realtime/subscribe
   {
     "symbols": ["NKE"]
   }
   ```

4. **결과**: TSLA, MSFT, NKE 모두 실시간 데이터 수신

### 시나리오 2: Nike만 구독 해제

```bash
POST /dashboard/realtime/unsubscribe
{
  "symbols": ["NKE"]
}
```

**결과**: TSLA, MSFT만 실시간 데이터 수신

## 지원하는 종목 코드

### 주요 종목
- `TSLA` - Tesla
- `MSFT` - Microsoft
- `AAPL` - Apple
- `NKE` - Nike
- `005930` - 삼성전자
- `051910` - LG화학

### 주요 지수
- `0001` - KOSPI
- `1001` - KOSDAQ

## 에러 처리

### 1. OAuth 인증 실패
```json
{
  "detail": "OAuth 인증 실패"
}
```

### 2. API 키 없음
```json
{
  "detail": "API key not found"
}
```

### 3. 구독 실패
```json
{
  "detail": "구독 실패"
}
```

## 주의사항

1. **OAuth 인증 필수**: 실시간 데이터 구독 전에 반드시 OAuth 인증을 완료해야 합니다.
2. **API 키 등록**: DB에 한국투자증권 API 키가 등록되어 있어야 합니다.
3. **연결 관리**: 사용 완료 후 연결 해제를 권장합니다.
4. **Rate Limit**: API 호출 시 적절한 지연을 두어 Rate Limit을 준수합니다.

## 환경 설정

### 환경 변수
```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_USE_REAL_WEBSOCKET=true
```

### API 키 등록
```sql
INSERT INTO table_user_api_keys (
  account_db_key, 
  korea_investment_app_key, 
  korea_investment_app_secret
) VALUES (
  1000, 
  'YOUR_APP_KEY', 
  'YOUR_APP_SECRET'
);
``` 