# 상세한 워크플로우 가이드 🔍

> **React ↔ Base Server 개발 워크플로우의 모든 것**
> 
> 이 문서는 프론트엔드 개발자가 백엔드 API를 사용할 때 거치는 모든 단계를 상세히 설명합니다. 실제 개발 시나리오를 기반으로 작성되었습니다.

## 📋 목차

1. [개발 환경 설정 워크플로우](#개발-환경-설정-워크플로우)
2. [새로운 기능 개발 워크플로우](#새로운-기능-개발-워크플로우)
3. [API 통신 워크플로우](#api-통신-워크플로우)
4. [에러 디버깅 워크플로우](#에러-디버깅-워크플로우)
5. [상태 관리 워크플로우](#상태-관리-워크플로우)
6. [테스트 및 배포 워크플로우](#테스트-및-배포-워크플로우)
7. [협업 워크플로우](#협업-워크플로우)

---

## 🛠️ 개발 환경 설정 워크플로우

### Phase 1: 백엔드 서버 확인

#### Step 1.1: 백엔드 서버 상태 점검
```bash
# 1. 백엔드 디렉토리로 이동
cd base_server

# 2. 서버 실행 상태 확인
curl http://localhost:8000/api/admin/ping

# 3. 예상 응답
{
  "status": "pong",
  "timestamp": "2024-07-16T10:30:00Z"
}
```

#### Step 1.2: 서버 실행 (실행되지 않은 경우)
```bash
# 1. 가상환경 확인
python --version
pip --version

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 서버 실행
python -m uvicorn application.base_web_server.main:app --reload --host 0.0.0.0 --port 8000

# 4. 서버 로그 확인
# [Info] : base_web_server 시작 (로그레벨: ALL, 환경: RELEASE)
# [Info] : Config 파일 로드 성공
```

#### Step 1.3: API 엔드포인트 확인
```bash
# 1. 모든 라우터 확인
ls application/base_web_server/routers/

# 2. 예상 출력
account.py    admin.py      autotrade.py  chat.py
crawler.py    dashboard.py  market.py     notification.py
portfolio.py  settings.py   tutorial.py

# 3. 각 라우터의 엔드포인트 확인
grep -n "@router.post" application/base_web_server/routers/account.py
```

### Phase 2: 프론트엔드 프로젝트 설정

#### Step 2.1: React 프로젝트 생성
```bash
# 1. 프로젝트 생성
npx create-react-app finance-frontend --template typescript
cd finance-frontend

# 2. 필수 패키지 설치
npm install axios react-router-dom @tanstack/react-query

# 3. 개발 의존성 설치
npm install -D @types/react-router-dom tailwindcss postcss autoprefixer

# 4. 패키지 설치 확인
npm list axios react-router-dom
```

#### Step 2.2: 프로젝트 구조 생성
```bash
# 디렉토리 구조 생성
mkdir -p src/{components,hooks,services,types,utils,contexts}

# 파일 구조 확인
tree src/
```

```
src/
├── components/
├── hooks/
├── services/
├── types/
├── utils/
├── contexts/
├── App.tsx
├── index.tsx
└── App.css
```

#### Step 2.3: 환경 변수 설정
```bash
# .env.local 생성
cat > .env.local << EOF
REACT_APP_API_BASE_URL=http://localhost:8000
REACT_APP_API_TIMEOUT=30000
REACT_APP_DEBUG=true
EOF

# 환경 변수 확인
cat .env.local
```

---

## 🔄 새로운 기능 개발 워크플로우

### 시나리오: 주식 검색 기능 개발

#### Phase 1: 백엔드 API 분석

#### Step 1.1: API 엔드포인트 찾기
```bash
# 1. 시장 관련 라우터 확인
cat application/base_web_server/routers/market.py

# 2. 주식 검색 엔드포인트 찾기
grep -A 10 -B 5 "search" application/base_web_server/routers/market.py
```

**발견된 엔드포인트:**
```python
@router.post("/security/search")
async def search_security(request: MarketSecuritySearchRequest, req: Request):
```

#### Step 1.2: Request/Response 구조 분석
```bash
# 1. serialize 파일 확인
cat template/market/common/market_serialize.py

# 2. 주식 검색 관련 클래스 찾기
grep -A 20 "class MarketSecuritySearchRequest" template/market/common/market_serialize.py
grep -A 20 "class MarketSecuritySearchResponse" template/market/common/market_serialize.py
```

**발견된 구조:**
```python
class MarketSecuritySearchRequest(BaseRequest):
    query: str
    market_type: Optional[str] = None
    limit: int = 50

class MarketSecuritySearchResponse(BaseResponse):
    securities: List[SecurityInfo] = []
    total_count: int = 0
```

#### Step 1.3: 데이터 모델 확인
```bash
# 1. 모델 파일 확인
cat template/market/common/market_model.py

# 2. SecurityInfo 클래스 찾기
grep -A 15 "class SecurityInfo" template/market/common/market_model.py
```

**발견된 모델:**
```python
class SecurityInfo(BaseModel):
    symbol: str
    name: str
    market_type: str
    sector: str
    current_price: float
    change: float
    change_percent: float
```

#### Phase 2: 프론트엔드 타입 정의

#### Step 2.1: 타입 파일 생성
```typescript
// src/types/market.ts
import { BaseRequest, BaseResponse } from './api';

export interface SecurityInfo {
  symbol: string;
  name: string;
  market_type: string;
  sector: string;
  current_price: number;
  change: number;
  change_percent: number;
}

export interface MarketSecuritySearchRequest extends BaseRequest {
  query: string;
  market_type?: string;
  limit?: number;
}

export interface MarketSecuritySearchResponse extends BaseResponse {
  securities: SecurityInfo[];
  total_count: number;
}
```

#### Step 2.2: API 서비스 함수 생성
```typescript
// src/services/marketService.ts
import { api } from '../lib/api';
import { MarketSecuritySearchRequest, MarketSecuritySearchResponse } from '../types/market';

export const marketService = {
  async searchSecurities(query: string, options?: {
    market_type?: string;
    limit?: number;
  }): Promise<MarketSecuritySearchResponse> {
    const request: Omit<MarketSecuritySearchRequest, 'accessToken' | 'sequence'> = {
      query,
      market_type: options?.market_type,
      limit: options?.limit || 50,
    };
    
    return await api.post<MarketSecuritySearchResponse>('/market/security/search', request);
  },
};
```

#### Phase 3: React Hook 개발

#### Step 3.1: 커스텀 Hook 생성
```typescript
// src/hooks/useStockSearch.ts
import { useState, useCallback } from 'react';
import { marketService } from '../services/marketService';
import { SecurityInfo } from '../types/market';

interface UseStockSearchState {
  securities: SecurityInfo[];
  loading: boolean;
  error: string | null;
  totalCount: number;
}

export const useStockSearch = () => {
  const [state, setState] = useState<UseStockSearchState>({
    securities: [],
    loading: false,
    error: null,
    totalCount: 0,
  });

  const search = useCallback(async (query: string, options?: {
    market_type?: string;
    limit?: number;
  }) => {
    if (!query.trim()) {
      setState(prev => ({ ...prev, securities: [], totalCount: 0 }));
      return;
    }

    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const response = await marketService.searchSecurities(query, options);
      
      if (response.errorCode === 0) {
        setState(prev => ({
          ...prev,
          securities: response.securities,
          totalCount: response.total_count,
          loading: false,
        }));
      } else {
        setState(prev => ({
          ...prev,
          error: `검색 실패: 에러코드 ${response.errorCode}`,
          loading: false,
        }));
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: '검색 중 오류가 발생했습니다.',
        loading: false,
      }));
    }
  }, []);

  const clear = useCallback(() => {
    setState({
      securities: [],
      loading: false,
      error: null,
      totalCount: 0,
    });
  }, []);

  return {
    ...state,
    search,
    clear,
  };
};
```

#### Phase 4: React 컴포넌트 개발

#### Step 4.1: 검색 컴포넌트 생성
```typescript
// src/components/StockSearch.tsx
import React, { useState, useEffect } from 'react';
import { useStockSearch } from '../hooks/useStockSearch';
import { SecurityInfo } from '../types/market';

interface StockSearchProps {
  onSelectStock?: (stock: SecurityInfo) => void;
  placeholder?: string;
}

const StockSearch: React.FC<StockSearchProps> = ({ 
  onSelectStock, 
  placeholder = "종목명이나 심볼을 입력하세요..." 
}) => {
  const [query, setQuery] = useState('');
  const [marketType, setMarketType] = useState<string>('');
  const { securities, loading, error, totalCount, search, clear } = useStockSearch();

  // 디바운스 처리
  useEffect(() => {
    const timer = setTimeout(() => {
      if (query.length >= 2) {
        search(query, { market_type: marketType || undefined });
      } else {
        clear();
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [query, marketType, search, clear]);

  const handleStockSelect = (stock: SecurityInfo) => {
    onSelectStock?.(stock);
    setQuery(stock.name);
    clear();
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('ko-KR').format(price);
  };

  const formatChange = (change: number, changePercent: number) => {
    const sign = change >= 0 ? '+' : '';
    return `${sign}${formatPrice(change)} (${sign}${changePercent.toFixed(2)}%)`;
  };

  return (
    <div className="relative">
      {/* 검색 입력 */}
      <div className="flex space-x-2 mb-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder}
          className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <select
          value={marketType}
          onChange={(e) => setMarketType(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">전체 시장</option>
          <option value="KOSPI">코스피</option>
          <option value="KOSDAQ">코스닥</option>
          <option value="NASDAQ">나스닥</option>
          <option value="NYSE">뉴욕증권거래소</option>
        </select>
      </div>

      {/* 로딩 상태 */}
      {loading && (
        <div className="absolute top-full left-0 right-0 bg-white border border-gray-300 rounded-md p-4 shadow-lg z-10">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
            <span className="ml-2 text-gray-600">검색 중...</span>
          </div>
        </div>
      )}

      {/* 에러 상태 */}
      {error && (
        <div className="absolute top-full left-0 right-0 bg-white border border-red-300 rounded-md p-4 shadow-lg z-10">
          <div className="text-red-600 text-center">{error}</div>
        </div>
      )}

      {/* 검색 결과 */}
      {securities.length > 0 && (
        <div className="absolute top-full left-0 right-0 bg-white border border-gray-300 rounded-md shadow-lg z-10 max-h-96 overflow-y-auto">
          <div className="p-2 border-b border-gray-200 bg-gray-50">
            <span className="text-sm text-gray-600">총 {totalCount}개 결과</span>
          </div>
          
          {securities.map((stock) => (
            <div
              key={stock.symbol}
              onClick={() => handleStockSelect(stock)}
              className="p-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100 last:border-b-0"
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="font-medium text-gray-900">
                    {stock.name} ({stock.symbol})
                  </div>
                  <div className="text-sm text-gray-500">
                    {stock.market_type} · {stock.sector}
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-medium text-gray-900">
                    {formatPrice(stock.current_price)}원
                  </div>
                  <div className={`text-sm ${
                    stock.change >= 0 ? 'text-red-600' : 'text-blue-600'
                  }`}>
                    {formatChange(stock.change, stock.change_percent)}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 검색 결과 없음 */}
      {query.length >= 2 && !loading && !error && securities.length === 0 && (
        <div className="absolute top-full left-0 right-0 bg-white border border-gray-300 rounded-md p-4 shadow-lg z-10">
          <div className="text-center text-gray-500">
            '{query}'에 대한 검색 결과가 없습니다.
          </div>
        </div>
      )}
    </div>
  );
};

export default StockSearch;
```

#### Step 4.2: 컴포넌트 테스트
```typescript
// src/components/StockSearchTest.tsx
import React, { useState } from 'react';
import StockSearch from './StockSearch';
import { SecurityInfo } from '../types/market';

const StockSearchTest: React.FC = () => {
  const [selectedStock, setSelectedStock] = useState<SecurityInfo | null>(null);

  const handleStockSelect = (stock: SecurityInfo) => {
    setSelectedStock(stock);
    console.log('Selected stock:', stock);
  };

  return (
    <div className="max-w-md mx-auto p-6">
      <h2 className="text-xl font-bold mb-4">주식 검색 테스트</h2>
      
      <StockSearch onSelectStock={handleStockSelect} />
      
      {selectedStock && (
        <div className="mt-6 p-4 bg-gray-50 rounded-md">
          <h3 className="font-medium mb-2">선택된 종목:</h3>
          <div className="text-sm space-y-1">
            <div>종목명: {selectedStock.name}</div>
            <div>심볼: {selectedStock.symbol}</div>
            <div>시장: {selectedStock.market_type}</div>
            <div>섹터: {selectedStock.sector}</div>
            <div>현재가: {selectedStock.current_price.toLocaleString()}원</div>
            <div>변동: {selectedStock.change} ({selectedStock.change_percent}%)</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StockSearchTest;
```

#### Phase 5: 개발 검증

#### Step 5.1: 로컬 테스트
```bash
# 1. 개발 서버 실행
npm start

# 2. 브라우저에서 테스트
# http://localhost:3000

# 3. 개발자 도구에서 네트워크 탭 확인
# - API 호출 상태 확인
# - 요청/응답 데이터 확인
```

#### Step 5.2: API 호출 디버깅
```typescript
// API 호출 로그 추가
const response = await marketService.searchSecurities(query, options);
console.log('API Request:', { query, options });
console.log('API Response:', response);
```

---

## 🌐 API 통신 워크플로우

### 전체 통신 흐름

#### Phase 1: 요청 전 준비

#### Step 1.1: 토큰 확인
```typescript
// 1. 로컬 스토리지에서 토큰 확인
const token = localStorage.getItem('accessToken');
console.log('Current token:', token);

// 2. 토큰 유효성 확인 (필요한 경우)
if (!token) {
  // 로그인 페이지로 리다이렉트
  window.location.href = '/login';
  return;
}
```

#### Step 1.2: 요청 데이터 준비
```typescript
// 1. BaseRequest 형태로 데이터 준비
const requestData = {
  query: 'Apple',
  market_type: 'NASDAQ',
  limit: 20,
  // 아래 필드들은 인터셉터에서 자동 추가
  // accessToken: token,
  // sequence: Date.now()
};

console.log('Request data:', requestData);
```

#### Phase 2: API 호출

#### Step 2.1: HTTP 요청 발송
```typescript
// src/lib/api.ts의 인터셉터 동작
this.client.interceptors.request.use((config) => {
  console.log('Request interceptor triggered');
  console.log('Original config:', config);
  
  const token = localStorage.getItem('accessToken');
  if (token && config.data) {
    config.data = {
      ...config.data,
      accessToken: token,
      sequence: Date.now(),
    };
  }
  
  console.log('Modified config:', config);
  return config;
});
```

#### Step 2.2: 백엔드 처리 과정
```python
# application/base_web_server/routers/market.py
@router.post("/security/search")
async def search_security(request: MarketSecuritySearchRequest, req: Request):
    # 1. IP 주소 추출
    ip = req.headers.get("X-Forwarded-For") or req.client.host
    
    # 2. TemplateService로 전달
    return await TemplateService.run_user(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        market_protocol.market_security_search_req_controller
    )
```

#### Step 2.3: 템플릿 처리
```python
# template/market/market_template_impl.py
async def on_market_security_search_req(self, client_session, request):
    response = MarketSecuritySearchResponse()
    
    try:
        # 1. 토큰 검증
        if not self.validate_token(request.accessToken):
            response.errorCode = 1001
            return response
        
        # 2. 비즈니스 로직 수행
        securities = await self.search_securities(request.query, request.market_type)
        
        # 3. 응답 데이터 설정
        response.securities = securities
        response.total_count = len(securities)
        
    except Exception as e:
        response.errorCode = 1005
        Logger.error(f"Security search error: {e}")
    
    return response
```

#### Phase 3: 응답 처리

#### Step 3.1: 응답 인터셉터
```typescript
// src/lib/api.ts의 응답 인터셉터 동작
this.client.interceptors.response.use(
  (response) => {
    console.log('Response interceptor triggered');
    console.log('Response data:', response.data);
    
    const data = response.data as BaseResponse;
    
    // 인증 에러 처리
    if (data.errorCode === 1001 || data.errorCode === 1002) {
      console.log('Authentication error detected');
      localStorage.clear();
      window.location.href = '/login';
    }
    
    return response;
  },
  (error) => {
    console.error('Response error:', error);
    return Promise.reject(error);
  }
);
```

#### Step 3.2: 서비스 레이어 처리
```typescript
// src/services/marketService.ts
export const marketService = {
  async searchSecurities(query: string, options?: any): Promise<MarketSecuritySearchResponse> {
    console.log('Service call started');
    console.log('Parameters:', { query, options });
    
    try {
      const response = await api.post<MarketSecuritySearchResponse>('/market/security/search', {
        query,
        market_type: options?.market_type,
        limit: options?.limit || 50,
      });
      
      console.log('Service call completed');
      console.log('Response:', response);
      
      return response;
    } catch (error) {
      console.error('Service call failed:', error);
      throw error;
    }
  },
};
```

#### Step 3.3: Hook 레이어 처리
```typescript
// src/hooks/useStockSearch.ts
const search = useCallback(async (query: string, options?: any) => {
  console.log('Hook search started');
  console.log('Parameters:', { query, options });
  
  setState(prev => ({ ...prev, loading: true, error: null }));
  
  try {
    const response = await marketService.searchSecurities(query, options);
    console.log('Hook received response:', response);
    
    if (response.errorCode === 0) {
      console.log('Success - updating state');
      setState(prev => ({
        ...prev,
        securities: response.securities,
        totalCount: response.total_count,
        loading: false,
      }));
    } else {
      console.log('Error response:', response.errorCode);
      setState(prev => ({
        ...prev,
        error: `검색 실패: 에러코드 ${response.errorCode}`,
        loading: false,
      }));
    }
  } catch (error) {
    console.error('Hook search failed:', error);
    setState(prev => ({
      ...prev,
      error: '검색 중 오류가 발생했습니다.',
      loading: false,
    }));
  }
}, []);
```

#### Step 3.4: 컴포넌트 레이어 처리
```typescript
// src/components/StockSearch.tsx
const StockSearch: React.FC<StockSearchProps> = ({ onSelectStock }) => {
  const { securities, loading, error, search } = useStockSearch();
  
  useEffect(() => {
    console.log('Component state updated');
    console.log('Securities:', securities);
    console.log('Loading:', loading);
    console.log('Error:', error);
  }, [securities, loading, error]);
  
  useEffect(() => {
    const timer = setTimeout(() => {
      if (query.length >= 2) {
        console.log('Triggering search from component');
        search(query, { market_type: marketType || undefined });
      }
    }, 300);
    
    return () => clearTimeout(timer);
  }, [query, marketType, search]);
  
  // 렌더링 로직...
};
```

---

## 🐛 에러 디버깅 워크플로우

### 일반적인 에러 시나리오

#### 시나리오 1: 401 Unauthorized 에러

#### Step 1.1: 에러 발생 상황
```bash
# 브라우저 개발자 도구 Console 에러
POST http://localhost:8000/api/portfolio/get 401 (Unauthorized)

# 네트워크 탭에서 확인할 수 있는 응답
{
  "errorCode": 1001,
  "sequence": 1642123456789,
  "message": "Authentication failed"
}
```

#### Step 1.2: 토큰 상태 확인
```typescript
// 브라우저 개발자 도구 Console에서 실행
console.log('AccessToken:', localStorage.getItem('accessToken'));
console.log('RefreshToken:', localStorage.getItem('refreshToken'));
console.log('UserId:', localStorage.getItem('userId'));

// 토큰 디코딩 (JWT인 경우)
const token = localStorage.getItem('accessToken');
if (token) {
  const payload = JSON.parse(atob(token.split('.')[1]));
  console.log('Token payload:', payload);
  console.log('Token expiry:', new Date(payload.exp * 1000));
}
```

#### Step 1.3: 토큰 갱신 또는 재로그인
```typescript
// 토큰 갱신 시도
const refreshToken = localStorage.getItem('refreshToken');
if (refreshToken) {
  try {
    const response = await api.post('/account/token/refresh', {
      refreshToken: refreshToken
    });
    
    if (response.errorCode === 0) {
      localStorage.setItem('accessToken', response.accessToken);
      // 원래 요청 재시도
    } else {
      // 로그인 페이지로 리다이렉트
      window.location.href = '/login';
    }
  } catch (error) {
    window.location.href = '/login';
  }
}
```

#### 시나리오 2: Network Error

#### Step 2.1: 네트워크 연결 확인
```bash
# 1. 서버 상태 확인
curl -I http://localhost:8000/api/admin/ping

# 2. 포트 확인
netstat -an | grep :8000

# 3. 방화벽 확인 (Windows)
netsh advfirewall firewall show rule name="Python"
```

#### Step 2.2: CORS 문제 해결
```python
# application/base_web_server/main.py에서 CORS 설정 확인
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React 개발 서버
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### Step 2.3: 프록시 설정 (개발 환경)
```json
// package.json에 프록시 설정 추가
{
  "name": "finance-frontend",
  "proxy": "http://localhost:8000",
  "dependencies": {
    // ...
  }
}
```

#### 시나리오 3: API 응답 구조 불일치

#### Step 3.1: 응답 데이터 확인
```typescript
// 실제 응답 데이터 로깅
const response = await api.post('/market/security/search', requestData);
console.log('Actual response structure:', JSON.stringify(response, null, 2));

// 예상 구조와 비교
console.log('Expected structure:', {
  errorCode: 0,
  sequence: 123456789,
  securities: [
    {
      symbol: 'AAPL',
      name: 'Apple Inc.',
      market_type: 'NASDAQ',
      // ...
    }
  ],
  total_count: 1
});
```

#### Step 3.2: 백엔드 로그 확인
```bash
# 백엔드 서버 로그 확인
tail -f logs/app.log

# 또는 개발 서버 콘솔에서 확인
# [Info] : Market security search request: {"query": "Apple", "market_type": "NASDAQ"}
# [Info] : Market security search response: {"errorCode": 0, "securities": [...]}
```

#### Step 3.3: 타입 정의 수정
```typescript
// 실제 응답에 맞게 타입 수정
export interface MarketSecuritySearchResponse extends BaseResponse {
  securities: SecurityInfo[];
  total_count: number;
  // 추가 필드가 있다면 여기에 정의
  market_status?: string;
  last_updated?: string;
}
```

---

## 🔄 상태 관리 워크플로우

### Context API 활용

#### Phase 1: 전역 상태 설계

#### Step 1.1: 상태 구조 정의
```typescript
// src/types/globalState.ts
export interface GlobalState {
  user: {
    id: string;
    email: string;
    isAuthenticated: boolean;
    loading: boolean;
  };
  portfolio: {
    data: any;
    loading: boolean;
    error: string | null;
    lastUpdated: string | null;
  };
  market: {
    searchResults: any[];
    loading: boolean;
    error: string | null;
  };
  notifications: {
    items: any[];
    unreadCount: number;
  };
}
```

#### Step 1.2: Context 생성
```typescript
// src/contexts/GlobalContext.tsx
import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { GlobalState } from '../types/globalState';

interface GlobalContextType {
  state: GlobalState;
  dispatch: React.Dispatch<any>;
}

const GlobalContext = createContext<GlobalContextType | undefined>(undefined);

const initialState: GlobalState = {
  user: {
    id: '',
    email: '',
    isAuthenticated: false,
    loading: true,
  },
  portfolio: {
    data: null,
    loading: false,
    error: null,
    lastUpdated: null,
  },
  market: {
    searchResults: [],
    loading: false,
    error: null,
  },
  notifications: {
    items: [],
    unreadCount: 0,
  },
};

const globalReducer = (state: GlobalState, action: any): GlobalState => {
  switch (action.type) {
    case 'SET_USER':
      return {
        ...state,
        user: {
          ...state.user,
          ...action.payload,
        },
      };
    
    case 'SET_PORTFOLIO':
      return {
        ...state,
        portfolio: {
          ...state.portfolio,
          ...action.payload,
        },
      };
    
    case 'SET_MARKET_SEARCH':
      return {
        ...state,
        market: {
          ...state.market,
          ...action.payload,
        },
      };
    
    case 'ADD_NOTIFICATION':
      return {
        ...state,
        notifications: {
          items: [...state.notifications.items, action.payload],
          unreadCount: state.notifications.unreadCount + 1,
        },
      };
    
    default:
      return state;
  }
};

export const GlobalProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(globalReducer, initialState);

  // 초기 인증 상태 확인
  useEffect(() => {
    const token = localStorage.getItem('accessToken');
    const userId = localStorage.getItem('userId');
    
    if (token && userId) {
      dispatch({
        type: 'SET_USER',
        payload: {
          id: userId,
          isAuthenticated: true,
          loading: false,
        },
      });
    } else {
      dispatch({
        type: 'SET_USER',
        payload: {
          loading: false,
        },
      });
    }
  }, []);

  return (
    <GlobalContext.Provider value={{ state, dispatch }}>
      {children}
    </GlobalContext.Provider>
  );
};

export const useGlobalState = () => {
  const context = useContext(GlobalContext);
  if (context === undefined) {
    throw new Error('useGlobalState must be used within a GlobalProvider');
  }
  return context;
};
```

#### Phase 2: 상태 활용

#### Step 2.1: 로그인 상태 관리
```typescript
// src/hooks/useAuth.ts
import { useCallback } from 'react';
import { useGlobalState } from '../contexts/GlobalContext';
import { api } from '../lib/api';

export const useAuth = () => {
  const { state, dispatch } = useGlobalState();

  const login = useCallback(async (credentials: any) => {
    dispatch({
      type: 'SET_USER',
      payload: { loading: true },
    });

    try {
      const response = await api.post('/account/login', credentials);
      
      if (response.errorCode === 0) {
        localStorage.setItem('accessToken', response.accessToken);
        localStorage.setItem('userId', response.user_id);
        
        dispatch({
          type: 'SET_USER',
          payload: {
            id: response.user_id,
            email: credentials.account_id,
            isAuthenticated: true,
            loading: false,
          },
        });
        
        return { success: true, nextStep: response.next_step };
      } else {
        dispatch({
          type: 'SET_USER',
          payload: { loading: false },
        });
        return { success: false, error: `로그인 실패: ${response.errorCode}` };
      }
    } catch (error) {
      dispatch({
        type: 'SET_USER',
        payload: { loading: false },
      });
      return { success: false, error: '로그인 중 오류가 발생했습니다.' };
    }
  }, [dispatch]);

  const logout = useCallback(async () => {
    try {
      await api.post('/account/logout');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.clear();
      dispatch({
        type: 'SET_USER',
        payload: {
          id: '',
          email: '',
          isAuthenticated: false,
          loading: false,
        },
      });
    }
  }, [dispatch]);

  return {
    user: state.user,
    login,
    logout,
  };
};
```

#### Step 2.2: 포트폴리오 상태 관리
```typescript
// src/hooks/usePortfolio.ts
import { useCallback, useEffect } from 'react';
import { useGlobalState } from '../contexts/GlobalContext';
import { api } from '../lib/api';

export const usePortfolio = () => {
  const { state, dispatch } = useGlobalState();

  const fetchPortfolio = useCallback(async () => {
    dispatch({
      type: 'SET_PORTFOLIO',
      payload: { loading: true, error: null },
    });

    try {
      const response = await api.post('/portfolio/get');
      
      if (response.errorCode === 0) {
        dispatch({
          type: 'SET_PORTFOLIO',
          payload: {
            data: response.portfolio,
            loading: false,
            lastUpdated: new Date().toISOString(),
          },
        });
      } else {
        dispatch({
          type: 'SET_PORTFOLIO',
          payload: {
            loading: false,
            error: `포트폴리오 조회 실패: ${response.errorCode}`,
          },
        });
      }
    } catch (error) {
      dispatch({
        type: 'SET_PORTFOLIO',
        payload: {
          loading: false,
          error: '포트폴리오 조회 중 오류가 발생했습니다.',
        },
      });
    }
  }, [dispatch]);

  // 인증된 사용자일 때 자동으로 포트폴리오 조회
  useEffect(() => {
    if (state.user.isAuthenticated && !state.portfolio.data) {
      fetchPortfolio();
    }
  }, [state.user.isAuthenticated, state.portfolio.data, fetchPortfolio]);

  return {
    portfolio: state.portfolio,
    refreshPortfolio: fetchPortfolio,
  };
};
```

---

## 🧪 테스트 및 배포 워크플로우

### 개발 테스트 워크플로우

#### Phase 1: 단위 테스트

#### Step 1.1: 테스트 환경 설정
```bash
# 테스트 라이브러리 설치
npm install -D @testing-library/react @testing-library/jest-dom @testing-library/user-event
npm install -D msw axios-mock-adapter

# 테스트 설정 파일 생성
mkdir src/__tests__ src/__mocks__
```

#### Step 1.2: API 모킹 설정
```typescript
// src/__mocks__/api.ts
import { MarketSecuritySearchResponse } from '../types/market';

export const mockMarketService = {
  searchSecurities: jest.fn().mockResolvedValue({
    errorCode: 0,
    sequence: 123456789,
    securities: [
      {
        symbol: 'AAPL',
        name: 'Apple Inc.',
        market_type: 'NASDAQ',
        sector: 'Technology',
        current_price: 150.50,
        change: 2.50,
        change_percent: 1.69,
      },
    ],
    total_count: 1,
  } as MarketSecuritySearchResponse),
};
```

#### Step 1.3: 컴포넌트 테스트
```typescript
// src/__tests__/StockSearch.test.tsx
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import StockSearch from '../components/StockSearch';
import { mockMarketService } from '../__mocks__/api';

// 모킹 설정
jest.mock('../services/marketService', () => ({
  marketService: mockMarketService,
}));

describe('StockSearch', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('검색 입력 시 API 호출됨', async () => {
    const user = userEvent.setup();
    const onSelectStock = jest.fn();
    
    render(<StockSearch onSelectStock={onSelectStock} />);
    
    const searchInput = screen.getByPlaceholderText('종목명이나 심볼을 입력하세요...');
    
    await user.type(searchInput, 'Apple');
    
    await waitFor(() => {
      expect(mockMarketService.searchSecurities).toHaveBeenCalledWith('Apple', {
        market_type: undefined,
      });
    });
  });

  test('검색 결과 렌더링', async () => {
    const user = userEvent.setup();
    const onSelectStock = jest.fn();
    
    render(<StockSearch onSelectStock={onSelectStock} />);
    
    const searchInput = screen.getByPlaceholderText('종목명이나 심볼을 입력하세요...');
    await user.type(searchInput, 'Apple');
    
    await waitFor(() => {
      expect(screen.getByText('Apple Inc. (AAPL)')).toBeInTheDocument();
      expect(screen.getByText('150.50원')).toBeInTheDocument();
    });
  });

  test('종목 선택 시 콜백 호출됨', async () => {
    const user = userEvent.setup();
    const onSelectStock = jest.fn();
    
    render(<StockSearch onSelectStock={onSelectStock} />);
    
    const searchInput = screen.getByPlaceholderText('종목명이나 심볼을 입력하세요...');
    await user.type(searchInput, 'Apple');
    
    await waitFor(() => {
      expect(screen.getByText('Apple Inc. (AAPL)')).toBeInTheDocument();
    });
    
    await user.click(screen.getByText('Apple Inc. (AAPL)'));
    
    expect(onSelectStock).toHaveBeenCalledWith({
      symbol: 'AAPL',
      name: 'Apple Inc.',
      market_type: 'NASDAQ',
      sector: 'Technology',
      current_price: 150.50,
      change: 2.50,
      change_percent: 1.69,
    });
  });
});
```

#### Phase 2: 통합 테스트

#### Step 2.1: E2E 테스트 설정
```bash
# Cypress 설치
npm install -D cypress @cypress/react @cypress/webpack-preprocessor

# Cypress 설정 파일 생성
npx cypress open
```

#### Step 2.2: E2E 테스트 시나리오
```typescript
// cypress/e2e/stock-search.cy.ts
describe('Stock Search E2E', () => {
  beforeEach(() => {
    // 백엔드 서버 상태 확인
    cy.request('GET', 'http://localhost:8000/api/admin/ping').then((response) => {
      expect(response.status).to.eq(200);
    });
    
    // 로그인 처리
    cy.visit('/login');
    cy.get('[data-testid="email-input"]').type('test@example.com');
    cy.get('[data-testid="password-input"]').type('password123');
    cy.get('[data-testid="login-button"]').click();
    
    // 대시보드 페이지 확인
    cy.url().should('include', '/dashboard');
  });

  it('주식 검색 및 선택 플로우', () => {
    // 주식 검색 컴포넌트로 이동
    cy.get('[data-testid="stock-search-input"]').should('be.visible');
    
    // 검색어 입력
    cy.get('[data-testid="stock-search-input"]').type('Apple');
    
    // 로딩 상태 확인
    cy.get('[data-testid="search-loading"]').should('be.visible');
    
    // 검색 결과 확인
    cy.get('[data-testid="search-results"]').should('be.visible');
    cy.get('[data-testid="search-result-item"]').should('have.length.greaterThan', 0);
    
    // 첫 번째 결과 클릭
    cy.get('[data-testid="search-result-item"]').first().click();
    
    // 선택된 종목 확인
    cy.get('[data-testid="selected-stock"]').should('contain', 'Apple Inc.');
  });

  it('검색 에러 처리', () => {
    // 잘못된 검색어 입력
    cy.get('[data-testid="stock-search-input"]').type('INVALID_SYMBOL_XYZ');
    
    // 에러 메시지 확인
    cy.get('[data-testid="search-error"]').should('be.visible');
    cy.get('[data-testid="search-error"]').should('contain', '검색 결과가 없습니다');
  });
});
```

#### Phase 3: 성능 테스트

#### Step 3.1: 네트워크 성능 확인
```typescript
// src/utils/performanceMonitor.ts
export class PerformanceMonitor {
  private static instance: PerformanceMonitor;
  private metrics: Array<{
    name: string;
    duration: number;
    timestamp: number;
  }> = [];

  static getInstance(): PerformanceMonitor {
    if (!PerformanceMonitor.instance) {
      PerformanceMonitor.instance = new PerformanceMonitor();
    }
    return PerformanceMonitor.instance;
  }

  startMeasure(name: string): void {
    performance.mark(`${name}-start`);
  }

  endMeasure(name: string): void {
    performance.mark(`${name}-end`);
    performance.measure(name, `${name}-start`, `${name}-end`);
    
    const measure = performance.getEntriesByName(name)[0];
    this.metrics.push({
      name,
      duration: measure.duration,
      timestamp: Date.now(),
    });
  }

  getMetrics(): Array<{ name: string; duration: number; timestamp: number }> {
    return this.metrics;
  }

  clearMetrics(): void {
    this.metrics = [];
    performance.clearMeasures();
    performance.clearMarks();
  }
}

// API 서비스에서 사용
export const marketService = {
  async searchSecurities(query: string, options?: any): Promise<MarketSecuritySearchResponse> {
    const monitor = PerformanceMonitor.getInstance();
    
    monitor.startMeasure('market-search');
    
    try {
      const response = await api.post<MarketSecuritySearchResponse>('/market/security/search', {
        query,
        market_type: options?.market_type,
        limit: options?.limit || 50,
      });
      
      monitor.endMeasure('market-search');
      
      // 성능 로깅
      const metrics = monitor.getMetrics();
      const lastMetric = metrics[metrics.length - 1];
      if (lastMetric.duration > 1000) {
        console.warn(`Slow API call: ${lastMetric.name} took ${lastMetric.duration}ms`);
      }
      
      return response;
    } catch (error) {
      monitor.endMeasure('market-search');
      throw error;
    }
  },
};
```

#### Step 3.2: 메모리 사용량 모니터링
```typescript
// src/hooks/useMemoryMonitor.ts
import { useEffect, useState } from 'react';

export const useMemoryMonitor = () => {
  const [memoryInfo, setMemoryInfo] = useState<any>(null);

  useEffect(() => {
    const checkMemory = () => {
      if ('memory' in performance) {
        const memory = (performance as any).memory;
        setMemoryInfo({
          usedJSHeapSize: memory.usedJSHeapSize,
          totalJSHeapSize: memory.totalJSHeapSize,
          jsHeapSizeLimit: memory.jsHeapSizeLimit,
          timestamp: Date.now(),
        });
      }
    };

    checkMemory();
    const interval = setInterval(checkMemory, 5000); // 5초마다 체크

    return () => clearInterval(interval);
  }, []);

  return memoryInfo;
};

// 컴포넌트에서 사용
const App: React.FC = () => {
  const memoryInfo = useMemoryMonitor();

  useEffect(() => {
    if (memoryInfo) {
      const usedMB = memoryInfo.usedJSHeapSize / 1024 / 1024;
      const totalMB = memoryInfo.totalJSHeapSize / 1024 / 1024;
      
      console.log(`Memory usage: ${usedMB.toFixed(2)}MB / ${totalMB.toFixed(2)}MB`);
      
      // 메모리 사용량이 높을 때 경고
      if (usedMB > 50) {
        console.warn('High memory usage detected');
      }
    }
  }, [memoryInfo]);

  return <div>...</div>;
};
```

---

## 🤝 협업 워크플로우

### 프론트엔드 ↔ 백엔드 협업

#### Phase 1: API 스펙 협의

#### Step 1.1: API 스펙 문서 작성
```markdown
# API 스펙: 주식 검색 기능

## 엔드포인트
POST /api/market/security/search

## 요청 구조
{
  "accessToken": "string",
  "sequence": number,
  "query": "string",           // 필수: 검색어
  "market_type": "string",     // 선택: 시장 타입 (KOSPI, KOSDAQ, NASDAQ, NYSE)
  "limit": number,             // 선택: 결과 개수 (기본값: 50)
  "sector": "string",          // 선택: 섹터 필터
  "sort_by": "string",         // 선택: 정렬 기준 (name, price, change)
  "sort_order": "string"       // 선택: 정렬 순서 (asc, desc)
}

## 응답 구조
{
  "errorCode": number,         // 0: 성공, 그외: 에러
  "sequence": number,
  "securities": [
    {
      "symbol": "string",      // 종목 심볼
      "name": "string",        // 종목명
      "market_type": "string", // 시장 타입
      "sector": "string",      // 섹터
      "current_price": number, // 현재가
      "change": number,        // 변동가
      "change_percent": number,// 변동률
      "volume": number,        // 거래량
      "market_cap": number,    // 시가총액
      "last_updated": "string" // 마지막 업데이트 시간
    }
  ],
  "total_count": number,       // 전체 결과 개수
  "page": number,              // 현재 페이지
  "has_more": boolean          // 더 많은 결과 여부
}

## 에러 코드
- 0: 성공
- 1001: 인증 실패
- 1002: 권한 없음
- 1003: 잘못된 파라미터
- 1004: 결과 없음
- 1005: 서버 오류
```

#### Step 1.2: 백엔드 구현 확인
```bash
# 백엔드 개발자에게 확인할 사항
1. API 엔드포인트 경로 확인
2. Request/Response 구조 확인
3. 에러 코드 체계 확인
4. 테스트 데이터 준비 상태 확인
```

#### Step 1.3: 프론트엔드 구현 계획
```typescript
// 구현 계획서
/*
1. 타입 정의 (types/market.ts)
2. API 서비스 함수 (services/marketService.ts)
3. 커스텀 Hook (hooks/useStockSearch.ts)
4. UI 컴포넌트 (components/StockSearch.tsx)
5. 통합 테스트 (StockSearch.test.tsx)

예상 소요 시간: 4시간
의존성: 백엔드 API 완성 후 진행
*/
```

#### Phase 2: 개발 진행

#### Step 2.1: 동시 개발 진행
```typescript
// 백엔드 개발 중일 때 Mock 데이터 사용
const mockMarketService = {
  async searchSecurities(query: string, options?: any): Promise<MarketSecuritySearchResponse> {
    // 개발 중에는 Mock 데이터 반환
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          errorCode: 0,
          sequence: Date.now(),
          securities: [
            {
              symbol: 'AAPL',
              name: 'Apple Inc.',
              market_type: 'NASDAQ',
              sector: 'Technology',
              current_price: 150.50,
              change: 2.50,
              change_percent: 1.69,
              volume: 1000000,
              market_cap: 2500000000000,
              last_updated: new Date().toISOString(),
            },
          ],
          total_count: 1,
          page: 1,
          has_more: false,
        });
      }, 500); // 네트워크 지연 시뮬레이션
    });
  },
};

// 환경에 따라 실제 서비스 또는 Mock 서비스 사용
export const marketService = process.env.NODE_ENV === 'development' && !process.env.REACT_APP_USE_REAL_API
  ? mockMarketService
  : realMarketService;
```

#### Step 2.2: 진행 상황 공유
```markdown
# 일일 진행 상황 보고

## 완료된 작업
- [x] 타입 정의 완료
- [x] API 서비스 함수 구현 완료
- [x] 기본 UI 컴포넌트 구현 완료

## 진행 중인 작업
- [ ] 고급 필터링 기능 구현 중
- [ ] 검색 결과 정렬 기능 구현 중

## 백엔드 팀에 요청사항
- [ ] 검색 API 응답 속도 최적화 필요 (현재 2초 → 목표 500ms)
- [ ] 시가총액 필드 추가 요청
- [ ] 에러 메시지 다국어 지원 필요

## 발견된 이슈
- [ ] 한글 종목명 검색 시 인코딩 문제
- [ ] 대량 검색 결과 시 페이지네이션 필요
```

#### Phase 3: 테스트 및 통합

#### Step 3.1: API 통합 테스트
```typescript
// 백엔드 API 준비 완료 후 통합 테스트
describe('Market API Integration', () => {
  test('실제 API 호출 테스트', async () => {
    // Mock이 아닌 실제 API 호출
    const originalEnv = process.env.REACT_APP_USE_REAL_API;
    process.env.REACT_APP_USE_REAL_API = 'true';
    
    try {
      const response = await marketService.searchSecurities('Apple');
      
      expect(response.errorCode).toBe(0);
      expect(response.securities).toHaveLength.greaterThan(0);
      expect(response.securities[0]).toHaveProperty('symbol');
      expect(response.securities[0]).toHaveProperty('name');
    } finally {
      process.env.REACT_APP_USE_REAL_API = originalEnv;
    }
  });

  test('에러 처리 테스트', async () => {
    // 잘못된 파라미터로 API 호출
    const response = await marketService.searchSecurities('');
    
    expect(response.errorCode).not.toBe(0);
  });
});
```

#### Step 3.2: 성능 최적화 협의
```typescript
// 성능 이슈 발견 시 백엔드 팀과 협의
const performanceTest = async () => {
  const startTime = performance.now();
  
  const response = await marketService.searchSecurities('Apple');
  
  const endTime = performance.now();
  const duration = endTime - startTime;
  
  console.log(`API 호출 시간: ${duration}ms`);
  
  // 성능 기준 초과 시 알림
  if (duration > 1000) {
    console.warn('API 응답 시간이 1초를 초과했습니다.');
    console.warn('백엔드 최적화가 필요합니다.');
  }
};
```

#### Step 3.3: 최종 검수 및 배포
```typescript
// 배포 전 최종 체크리스트
const deploymentChecklist = {
  // 기능 검증
  functionalTests: [
    '기본 검색 기능 동작',
    '필터링 기능 동작',
    '정렬 기능 동작',
    '페이지네이션 동작',
    '에러 처리 동작',
  ],
  
  // 성능 검증
  performanceTests: [
    'API 응답 시간 < 1초',
    '메모리 사용량 정상',
    '대량 데이터 처리 가능',
  ],
  
  // 사용성 검증
  usabilityTests: [
    '검색 결과 로딩 표시',
    '에러 메시지 명확',
    '키보드 네비게이션 지원',
    '모바일 반응형 디자인',
  ],
  
  // 보안 검증
  securityTests: [
    '인증 토큰 올바르게 처리',
    'XSS 방지 처리',
    '입력 데이터 검증',
  ],
};
```

---

## 🎯 마무리

이 상세한 워크플로우 가이드는 React 프론트엔드와 Base Server 백엔드 간의 모든 개발 과정을 다룹니다.

### 핵심 워크플로우 요약:

1. **환경 설정**: 백엔드 확인 → 프론트엔드 설정 → 개발 환경 구성
2. **기능 개발**: API 분석 → 타입 정의 → Hook 개발 → 컴포넌트 구현
3. **API 통신**: 요청 준비 → 호출 → 응답 처리 → 상태 업데이트
4. **에러 디버깅**: 에러 발견 → 원인 분석 → 해결 방안 적용
5. **상태 관리**: 전역 상태 설계 → Context 구현 → Hook 활용
6. **테스트**: 단위 테스트 → 통합 테스트 → 성능 테스트 → E2E 테스트
7. **협업**: 스펙 협의 → 동시 개발 → 통합 테스트 → 배포

### 개발 효율성 향상 팁:

- **Mock 데이터 활용**: 백엔드 개발 중에도 프론트엔드 개발 진행
- **타입 안전성**: TypeScript로 컴파일 타임 에러 방지
- **자동화**: 테스트 자동화로 회귀 버그 방지
- **모니터링**: 성능 모니터링으로 사용자 경험 개선
- **협업**: 명확한 API 스펙으로 협업 효율성 증대

이 워크플로우를 따라하면 안정적이고 효율적인 프론트엔드-백엔드 통합 개발이 가능합니다! 🚀

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "Create detailed workflow-focused documentation", "status": "completed", "priority": "high", "id": "1"}]