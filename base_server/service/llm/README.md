# AI Trading Platform — LLM Service

> **개요**: SKN12-FINAL-2TEAM의 AI 트레이딩 플랫폼 백엔드 LLM 서비스입니다. OpenAI GPT 모델을 기반으로 금융 분석 도구들과 연동하여 지능형 투자 상담과 시장 분석을 제공하는 LangChain + LangGraph 기반 시스템입니다.

---

## 🏗️ 프로젝트 구조

### 디렉토리 구조
```
llm/
├── __init__.py                    # 패키지 초기화
├── AIChat_service.py              # 메인 AI 채팅 서비스
├── llm_config.py                  # LLM 설정 및 구성
└── AIChat/                        # AI 채팅 핵심 모듈
    ├── __init__.py                # AIChat 패키지 초기화
    ├── Router.py                  # LangGraph 기반 라우터
    ├── BaseFinanceTool.py         # 금융 도구 기본 클래스
    ├── SessionAwareTool.py        # 세션 인식 도구
    ├── requirements.txt           # Python 의존성
    ├── BasicTools/                # 기본 금융 분석 도구
    │   ├── FinancialStatementTool.py    # 재무제표 분석
    │   ├── MacroEconomicTool.py         # 거시경제 분석
    │   ├── SectorAnalysisTool.py       # 섹터 분석
    │   ├── TechnicalAnalysisTool.py    # 기술적 분석
    │   ├── MarketDataTool.py           # 시장 데이터
    │   ├── NewsTool.py                 # 뉴스 분석
    │   └── IndustryAnalysisTool.py    # 산업 분석
    ├── tool/                       # 고급 분석 도구
    │   ├── MarketRegimeDetectorTool.py # 시장 체제 감지
    │   └── KalmanRegimeFilterTool.py   # 칼만 필터 기반 체제 분석
    ├── renderer/                   # 응답 렌더링
    └── manager/                    # 도구 관리
```

---

## 🔧 핵심 기능

### 1. **AI 채팅 서비스 (AIChatService)**
- **LLM 통합**: OpenAI GPT 모델과의 연동 및 스트리밍 지원
- **세션 관리**: Redis 기반 대화 히스토리 및 메모리 관리
- **멀티 프로토콜**: REST API 및 WebSocket 스트리밍 지원
- **캐시 연동**: CacheService와의 통합으로 성능 최적화

### 2. **금융 분석 라우터 (AIChatRouter)**
- **LangGraph 파이프라인**: 복잡한 금융 분석 워크플로우 관리
- **도구 체인**: 다양한 금융 분석 도구들의 순차적 실행
- **상태 관리**: 분석 과정의 상태 추적 및 관리
- **에러 처리**: 도구 실행 실패 시 대체 로직 및 복구

### 3. **기본 금융 도구 (BasicTools)**
- **재무제표 분석**: 기업 재무 상태 및 성과 분석
- **거시경제 분석**: 경제 지표 및 정책 영향 분석
- **섹터 분석**: 산업별 성과 및 트렌드 분석
- **기술적 분석**: 차트 패턴 및 기술적 지표 분석
- **시장 데이터**: 실시간 시장 정보 및 가격 데이터
- **뉴스 분석**: 금융 뉴스 및 시장 동향 분석
- **산업 분석**: 특정 산업의 구조 및 경쟁력 분석

### 4. **고급 분석 도구 (Advanced Tools)**
- **시장 체제 감지**: 시장 상황에 따른 체제 변화 감지
- **칼만 필터**: 시계열 데이터의 노이즈를 제거하고, 변동성 뒤에 숨겨진 실제 추세(Regime)를 추정하여 시장의 국면(상승/하락/횡보)을 판단

---

## 📚 사용된 라이브러리

### **Core AI/ML Framework**
- **LangChain**: LLM 애플리케이션 개발 프레임워크
- **LangGraph**: 복잡한 AI 워크플로우 관리
- **OpenAI**: GPT 모델 API 연동
- **Pydantic**: 데이터 검증 및 설정 관리

### **금융 데이터 & 분석**
- **Financial Modeling Prep (FMP)**: 재무제표 및 시장 데이터
- **NewsAPI**: 금융 뉴스 및 시장 동향
- **FRED**: 연방준비제도 경제 데이터
- **Pandas**: 데이터 처리 및 분석
- **NumPy**: 수치 계산 및 배열 처리

### **백엔드 & 인프라**
- **FastAPI**: 비동기 웹 API 프레임워크
- **Redis**: 대화 히스토리 및 캐싱
- **WebSocket**: 실시간 스트리밍 통신
- **asyncio**: 비동기 프로그래밍

### **개발 도구**
- **Python 3.8+**: 메인 프로그래밍 언어
- **Type Hints**: 타입 안전성 및 코드 가독성
- **Logging**: 구조화된 로깅 시스템

---

## 🪝 핵심 클래스 및 메서드

### **AIChatService - 메인 서비스 클래스**

```python
class AIChatService:
    def __init__(self, llm_config: LlmConfig):
        # OpenAI LLM 인스턴스 초기화
        self.llm = ChatOpenAI(model=model, temperature=temperature)
        self.llm_stream = ChatOpenAI(streaming=True)  # 스트리밍용
        self._session_mem: dict[str, ConversationBufferMemory] = {}
    
    def mem(self, session_id: str) -> ConversationBufferMemory:
        """세션별 대화 메모리 관리 (Redis 기반)"""
        # Redis에 대화 히스토리 저장
        # key_prefix: finance_app:LOCAL:chat:{session_id}
    
    async def chat(self, message: str, session_id: str = "", client_session=None):
        """REST API용 채팅 응답 생성"""
        # AIChatRouter를 통한 도구 체인 실행
        # 비동기 처리로 도구 호출 안전성 보장
    
    async def stream(self, ws: WebSocket):
        """WebSocket용 스트리밍 채팅 응답 생성"""
        # 실시간 스트리밍 응답
        # SSE 호환 가능한 형태로 데이터 전송
```

**동작 방식**:
- LLM 설정을 통한 모델 초기화
- Redis 기반 세션별 대화 메모리 관리
- AIChatRouter를 통한 도구 체인 실행
- REST API 및 WebSocket 스트리밍 지원

### **AIChatRouter - 금융 분석 라우터**

```python
class AIChatRouter:
    def __init__(self, client_session=None):
        self.client_session = client_session
        self.ai_chat_service = ServiceContainer.get_ai_chat_service()
        
        # 금융 분석 도구들 초기화
        self.tools = [
            FinancialStatementTool(),
            MacroEconomicTool(),
            SectorAnalysisTool(),
            TechnicalAnalysisTool(),
            MarketDataTool(),
            NewsTool(),
            IndustryAnalysisTool(),
            MarketRegimeDetector(),
            KalmanRegimeFilterTool()
        ]
    
    def run_question(self, question: str) -> str:
        """사용자 질문을 도구 체인으로 처리"""
        # LangGraph 파이프라인 실행
        # 도구 선택 및 순차적 실행
        # 최종 응답 생성
```

**동작 방식**:
- LangGraph 기반 상태 머신 구성
- 사용자 질문에 따른 적절한 도구 선택
- 도구 체인을 통한 순차적 분석 실행
- 결과 통합 및 최종 응답 생성

---

## 🌐 API 연동 방식

### **LLM 설정 및 프로바이더 관리**

```python
# llm_config.py
class LlmConfig(BaseModel):
    default_provider: str                    # 기본 LLM 프로바이더
    concurrent_requests: int                 # 동시 요청 수 제한
    providers: Dict[str, ProviderConfig]    # 프로바이더별 설정
    API_Key: Dict[str, str]                 # API 키 관리
    
    # 채팅 관련 설정
    max_conversation_length: int = 20       # 최대 대화 길이
    system_prompts: Dict[str, str] = {}     # 시스템 프롬프트
    
    # 분석 관련 설정
    analysis_timeout: int = 60              # 분석 타임아웃
    max_concurrent_requests: int = 5        # 최대 동시 요청
```

### **외부 API 연동**

```python
# AIChat_service.py
class AIChatService:
    def __init__(self, llm_config: LlmConfig):
        # OpenAI API 키 설정
        api_key = os.getenv("OPENAI_API_KEY") or llm_config.providers[llm_config.default_provider].api_key
        
        # LLM 인스턴스 생성
        self.llm = ChatOpenAI(
            model=llm_config.providers[llm_config.default_provider].model,
            temperature=llm_config.providers[llm_config.default_provider].temperature,
            openai_api_key=api_key
        )
```

### **Redis 캐시 연동**

```python
# AIChat_service.py
def mem(self, session_id: str) -> ConversationBufferMemory:
    """세션별 대화 메모리 관리 (Redis 기반)"""
    if session_id not in self._session_mem:
        cache_client = self.cache_service.get_client()
        redis_url = f"redis://{cache_client._host}:{cache_client._port}/{cache_client._db}"
        
        # RedisChatMessageHistory 생성
        history = RedisChatMessageHistory(
            session_id=session_id,
            url=redis_url,
            key_prefix=self.KEY_PREFIX  # finance_app:LOCAL:chat:
        )
        
        # ConversationBufferMemory에 연결
        self._session_mem[session_id] = ConversationBufferMemory(
            chat_memory=history,
            return_messages=True
        )
```

---

## 🔄 LLM 서비스 전체 흐름

### **1. 서비스 초기화**
```
1. ServiceContainer에서 AIChatService 인스턴스 생성
2. LlmConfig를 통한 LLM 설정 로드
3. OpenAI API 키 및 모델 설정
4. Redis 캐시 서비스 연결 확인
5. 금융 분석 도구들 초기화
```

### **2. REST API 채팅 플로우**
```
1. 사용자 메시지 수신 (/api/chat)
2. AIChatService.chat() 메서드 호출
3. 세션 ID 생성 또는 기존 세션 사용
4. AIChatRouter를 통한 도구 체인 실행
5. LangGraph 파이프라인으로 분석 수행
6. Redis에 대화 히스토리 저장
7. 최종 응답 반환
```

### **3. WebSocket 스트리밍 플로우**
```
1. WebSocket 연결 수립
2. AIChatService.stream() 메서드 호출
3. 실시간 메시지 수신 및 처리
4. 스트리밍 LLM을 통한 응답 생성
5. WebSocket을 통한 실시간 응답 전송
6. 연결 종료 시 정리 작업
```

### **4. 도구 체인 실행 플로우**
```
1. 사용자 질문 분석
2. 적절한 금융 분석 도구 선택
3. 도구별 입력 파라미터 준비
4. 순차적 도구 실행 및 결과 수집
5. 중간 결과 검증 및 에러 처리
6. 최종 응답 통합 및 포맷팅
```

---

## 🔌 도구 체인 구현 상세

### **금융 도구 확장 가이드 (`BaseFinanceTool` 상속)**

모든 금융 분석 도구는 `BaseFinanceTool`을 상속받아 일관된 인터페이스를 유지해야 합니다. 이는 LangGraph 라우터가 각 도구를 동적으로 식별하고 실행하기 위해 필수적입니다.

```python
# AIChat/BaseFinanceTool.py
from pydantic import BaseModel, Field

class BaseFinanceTool(BaseModel):
    name: str = Field(..., description="도구의 고유한 이름")
    description: str = Field(..., description="LLM이 도구의 용도를 이해하기 위한 설명")

    def run(self, params: BaseModel) -> str:
        """도구의 실제 실행 로직"""
        raise NotImplementedError("이 메서드는 서브클래스에서 구현되어야 합니다.")

# 세션 정보가 필요한 경우 SessionAwareTool을 상속
class SessionAwareTool(BaseFinanceTool):
    client_session: object = Field(None, description="사용자 세션 정보")
```

**새로운 도구 추가 예시 (`MyNewTool.py`)**
```python
import json
from pydantic import BaseModel, Field
from .BaseFinanceTool import BaseFinanceTool

# 1. 도구의 입력 파라미터를 Pydantic 모델로 정의
class MyToolParams(BaseModel):
    symbol: str = Field(..., description="분석할 주식 심볼")
    period: int = Field(14, description="분석 기간(일)")

# 2. BaseFinanceTool을 상속하여 새 도구 클래스 생성
class MyNewTool(BaseFinanceTool):
    def __init__(self):
        super().__init__(
            name="my_new_tool_analyzer",
            description="새로운 분석을 수행하는 도구입니다. 특정 심볼과 기간을 받아 분석 결과를 반환합니다."
        )

    # 3. run 메서드 구현
    def run(self, params: MyToolParams) -> str:
        """도구의 핵심 로직"""
        try:
            # 여기에 실제 분석 로직 구현
            # 예: 외부 API 호출, 데이터 분석 등
            analysis_result = {
                "symbol": params.symbol,
                "period": params.period,
                "result": "매우 긍정적",
                "confidence": 0.95
            }
            
            # 4. 결과를 JSON 문자열로 반환
            return json.dumps(analysis_result, ensure_ascii=False)
        
        except Exception as e:
            # 에러 처리
            return json.dumps({"error": f"분석 중 오류 발생: {str(e)}"})

```

### **도구 출력 포맷 (Tool Output Format)**

- **반환 타입**: 모든 도구의 `run` 메서드는 최종적으로 **문자열(string)**을 반환해야 합니다.
- **데이터 구조**: 복잡한 분석 결과는 **JSON 형식의 문자열**로 변환하여 반환하는 것을 강력히 권장합니다. LLM은 구조화된 JSON을 파싱하여 사용자에게 더 풍부하고 정확한 답변을 생성할 수 있습니다.

**좋은 출력 예시:**
```json
{
  "status": "success",
  "analysis_type": "기술적 분석 (RSI)",
  "data": {
    "symbol": "AAPL",
    "current_rsi": 68.5,
    "signal": "과매수 구간에 근접. 단기 조정 가능성 있음.",
    "recommendation": "HOLD"
  },
  "generated_at": "2025-01-20T10:30:00Z"
}
```

---

## 🔬 고급 분석 도구 심층 분석: `KalmanRegimeFilterTool`

`KalmanRegimeFilterTool`은 이 플랫폼의 대표적인 고급 분석 도구로, **5차원 칼만 필터**와 **블랙-숄즈 옵션 가격 계산**을 결합하여 실시간 트레이딩 신호를 생성하는 시스템입니다.

### **1. 개요**
이 도구는 **FeaturePipelineTool**을 통해 OHLCV, 경제지표, 기술적 지표 등의 원시 데이터를 수집하고, 이를 **5차원 관측 벡터**로 변환하여 칼만 필터에 입력합니다. 칼만 필터는 노이즈를 제거하고 숨겨진 추세를 추정한 후, 블랙-숄즈 모델을 사용하여 ATM 기반 옵션 이론가를 계산하고 실제 시장가와 비교하여 매수/매도/관망 신호를 생성합니다.

### **2. 핵심 아키텍처 및 데이터 플로우**

#### **2.1 데이터 수집 및 전처리**
```
1. FeaturePipelineTool 호출
   ├── 기본 피처: GDP, CPIAUCSL, DEXKOUS, RSI, MACD, VIX, PRICE
   ├── 정규화: 모든 피처를 [-5, 5] 범위로 스케일링
   └── 복합 피처 생성: 5차원 칼만 필터 전용 공식 적용

2. 5차원 관측 벡터 구성
   ├── kalman_trend: 거시경제 + 변동성 복합 (GDP 0.1% + CPI 1% + VIX 98.9%)
   ├── kalman_momentum: 기술적 + 거시경제 복합 (RSI 70% + MACD 25% + CPI 5%)
   ├── kalman_volatility: VIX 변동성 (100%)
   ├── kalman_macro: 거시경제 신호 (GDP 0.1% + CPI 99.9%)
   └── kalman_tech: 기술적 신호 (RSI 60% + MACD 40%)
```

#### **2.2 칼만 필터 상태 관리**
```
상태 벡터: [trend, momentum, volatility, macro_signal, tech_signal]
├── Redis + SQL 하이브리드 저장
├── 사용자별 세션 기반 필터 인스턴스 관리
├── 매 호출마다 상태 복원 및 업데이트
└── 성능 메트릭 모니터링 (innovation, divergence 감지)
```

#### **2.3 블랙-숄즈 가격 분석**
```
1. 현재가 기준 행사가 그리드 생성
   ├── 현재가 기준 ±5%, ±10% 행사가 (예: 현재가 $100이면 $95, $100, $105, $110)
   ├── 각 행사가별 이론가 계산 (수학적 공식으로 정확한 가격 도출)
   └── 민감도 지표 계산 (가격 변화에 따른 옵션 가치 변화율)

2. 이론가 vs 시장가 비교 분석
   ├── 이론가가 시장가보다 높으면 → "시장가가 싸다" → 매수 신호
   ├── 이론가가 시장가보다 낮으면 → "시장가가 비싸다" → 매도 신호
   └── 차이가 적으면 → "적정가" → 관망

3. 칼만 필터 방향성과 정합성 체크
   ├── 칼만이 "상승 예상" + 가격이 "매수 신호" = 완벽한 조합 ✅
   ├── 칼만이 "하락 예상" + 가격이 "매도 신호" = 완벽한 조합 ✅
   └── 방향성이 다르면 → 신중한 접근 필요 ⚠️

4. 최종 액션 결정 (레버리지 없이 현물 매수/매도 개념)
   ├── 매수: 이론가 대비 싼 가격을 사서 상승 시 수익 실현
   ├── 매도: 이론가 대비 비싼 가격을 팔아서 하락 시 수익 실현
   └── 관망: 적정가 범위이거나 불확실성이 높은 경우
```

### **3. 실제 구현된 동작 과정**

#### **3.1 데이터 파이프라인 실행**
```python
# FeaturePipelineTool을 통한 데이터 수집 및 정규화
pipeline_result = FeaturePipelineTool(self.ai_chat_service).transform(
    tickers=inp.tickers,
    start_date=inp.start_date,
    end_date=inp.end_date,
    feature_set=["GDP", "CPIAUCSL", "DEXKOUS", "RSI", "MACD", "VIX", "PRICE"],
    normalize=True,  # 정규화 활성화
    normalize_targets=["GDP", "CPIAUCSL", "VIX", "RSI", "MACD"],
    generate_composites=True,  # 복합 피처 생성
    composite_formula_map=kalman_composite_formulas,  # 5차원 칼만 전용 공식
    return_raw=True,  # Raw + Normalized 동시 반환
    debug=debug
)
```

#### **3.2 5차원 관측 벡터 구성**
```python
# 5차원 칼만 필터용 관측 벡터
z = np.array([
    norm_features.get("kalman_trend", 0.0),      # trend
    norm_features.get("kalman_momentum", 0.0),   # momentum
    norm_features.get("kalman_volatility", 0.0), # volatility
    norm_features.get("kalman_macro", 0.0),      # macro_signal
    norm_features.get("kalman_tech", 0.0)        # tech_signal
])
```

#### **3.3 칼만 필터 상태 복원 및 실행**
```python
# Redis + SQL 하이브리드 상태 관리
if self.state_manager:
    # 1. SQL에서 최신 상태 복원
    filter_instance = restore_from_sql_sync()
    
    if filter_instance is None:
        # 2. Rule-Based 초기화 (KalmanInitializerTool 사용)
        initializer = KalmanInitializerTool()
        x, P = initializer.initialize_kalman_state(ticker)
        
        filter_instance = KalmanRegimeFilterCore()
        filter_instance.x = x
        filter_instance.P = P
        filter_instance.step_count = 0

# 칼만 필터 실행
filter_instance.step(z)
state, cov = filter_instance.x.copy(), filter_instance.P.copy()
```

#### **3.4 블랙-숄즈 가격 뷰 생성**
```python
# 블랙-숄즈 입력 파라미터 생성
bs_inputs = self._build_bs_inputs(
    entry_price=entry_price,        # 현재 주식 가격
    atr_pct=atr_pct,               # 일간 변동성
    rate=0.02,                     # 무위험이자율 (연 2%)
    div_yield=0.0,                 # 배당수익률 (0%)
    days_to_expiry=inp.horizon_days # 만기까지 일수
)

# 가격 뷰 추가 (이론가, 민감도 지표, 시장가 비교)
self._attach_option_view(rec, bs_inputs, signal, market_prices, threshold)
```

### **4. 트레이딩 신호 생성 로직**

#### **4.1 종합 신호 계산**
```python
# 5차원 상태를 종합 신호로 변환
trend = state[0]        # 추세
momentum = state[1]     # 모멘텀
macro_signal = state[3] # 거시경제 신호
tech_signal = state[4]  # 기술적 신호

# 가중 평균으로 종합 신호 계산
combined_signal = 0.4 * trend + 0.3 * momentum + 0.2 * macro_signal + 0.1 * tech_signal
combined_signal = np.clip(combined_signal, -5.0, 5.0)  # 범위 제한

# 신호 방향 결정
if combined_signal > 0.5:
    signal = "Long"      # 매수 신호
elif combined_signal < -0.5:
    signal = "Short"     # 매도 신호
else:
    signal = "Neutral"   # 관망
```

#### **4.2 시장가 비교 신호**
```python
# 시장가가 제공된 경우 이론가와 비교
if market_prices:
    raw_signals = self._analyze_option_signals(bs_inputs, market_prices, threshold, signal)
    
    # 칼만 방향성과 정합성 체크
    bias_ok = (
        (bias == "Long" and action == "매수") or 
        (bias == "Short" and action == "매도") or 
        (bias == "Neutral")
    )
    
    # 우선순위 정렬: 방향성 일치 우선 → 편차가 큰 순
    signals.sort(key=lambda s: (not s["bias_ok"], -abs(s["ratio"])))
```

### **5. 사용자 질문 기반 지속적 학습**

#### **5.1 상태 지속성**
- **매 호출마다 새로운 필터 상태**: 사용자가 질문할 때마다 칼만 필터가 새로운 관측 벡터로 업데이트
- **Redis + SQL 이중 저장**: 실시간 접근성과 영속성 보장
- **성능 메트릭 추적**: innovation history, divergence 감지, step_count 모니터링

#### **5.2 점진적 정교화**
```
1. 첫 번째 호출: Rule-Based 초기화
2. 두 번째 호출: 이전 상태 복원 + 새로운 관측으로 업데이트
3. N번째 호출: N-1번째 상태 + 최신 관측으로 정교화
4. 결과: 더 정확한 추세 추정 및 신뢰도 향상
```

### **6. LLM과의 연계 및 최종 출력**

#### **6.1 도구 출력 (구조화된 JSON)**
```json
{
  "trading_signal": "Long",
  "strategy": "Trend Following",
  "signal_confidence": "높음 (85.2%)",
  "combined_signal": "강함 (2.847) - 강한 신호 (적극적 진입) (매수 신호)",
  "position_size": 15.234,
  "leverage": "노출 23%",
  "options": {
    "spot": 340.84,
    "sigma_annual": 0.456,
    "view": "call/put grid by strikes",
    "preferred": "call",
    "table": [
      {
        "K": 306.76, "call": 35.0, "put": 0.8,
        "delta": 0.987, "gamma": 0.001, "vega": 12.5, "theta": -0.8, "rho": 0.2
      }
    ]
  },
  "stop_loss": "$325.50",
  "take_profit": "$365.20"
}
```

#### **6.2 LLM의 자연어 해석**
LLM은 위의 구조화된 JSON을 받아 다음과 같이 자연스러운 투자 조언을 생성합니다:

> "칼만 필터 분석 결과, 현재 테슬라는 **강한 매수 신호**를 보이고 있습니다. 5차원 상태 분석에서 추세(2.1), 모멘텀(1.8), 기술적 신호(1.5)가 모두 상승 방향이며, 85.2%의 높은 신뢰도를 보입니다. 블랙-숄즈 옵션 분석에 따르면 ATM 콜 옵션이 현재 시장가 대비 5% 저평가되어 있어 매수 기회로 판단됩니다. 손절가는 $325.50, 목표가는 $365.20으로 설정하는 것을 권장합니다."

### **7. 핵심 특징 및 장점**

#### **7.1 실시간 적응성**
- **매 호출마다 상태 업데이트**: 새로운 시장 데이터로 지속적 학습
- **동적 신뢰도 조정**: 관측 데이터 품질에 따른 신뢰도 자동 조정
- **적응형 임계값**: 시장 상황에 따른 동적 신호 임계값 조정

#### **7.2 다차원 분석**
- **5차원 상태 벡터**: 추세, 모멘텀, 변동성, 거시경제, 기술적 신호를 독립적으로 모델링
- **복합 피처 생성**: 단일 지표의 한계를 극복하는 복합 신호 생성
- **교차 검증**: 여러 차원의 신호가 일치할 때 신뢰도 향상

#### **7.3 가격 전략 통합**
- **현재가 기준 분석**: 현재가 기준 현실적인 가격 전략 제시
- **시장가 비교**: 이론가 대비 실제 시장가 편차 분석
- **리스크 관리**: 손절가/목표가 자동 계산 및 포지션 크기 최적화

이 도구는 단순한 기술적 분석을 넘어서 **거시경제, 기술적 지표, 변동성, 가격 분석**을 통합적으로 분석하여 **실행 가능한 트레이딩 전략**을 제공하는 고도화된 AI 금융 분석 시스템입니다.

---

## 🎯 코드 철학

### **1. 모듈화 및 확장성**
- **도구 기반 아키텍처**: 새로운 분석 도구를 쉽게 추가 가능
- **플러그인 구조**: 도구별 독립적인 개발 및 배포
- **인터페이스 표준화**: BaseFinanceTool을 통한 일관된 도구 구조

### **2. 성능 및 안정성**
- **비동기 처리**: asyncio를 통한 동시성 처리
- **캐싱 전략**: Redis를 통한 대화 히스토리 및 결과 캐싱
- **에러 처리**: 도구별 예외 처리 및 복구 메커니즘

### **3. 사용자 경험**
- **스트리밍 응답**: 실시간 AI 응답으로 즉시성 제공
- **세션 관리**: 사용자별 대화 컨텍스트 유지
- **도구 설명**: 각 도구의 기능과 사용법을 명확히 제시

### **4. 개발자 경험**
- **타입 힌트**: Python 타입 힌트를 통한 코드 가독성
- **설정 관리**: Pydantic을 통한 설정 검증 및 관리
- **로깅**: 구조화된 로깅을 통한 디버깅 지원

---

## 🚀 개선할 점

### **1. 성능 최적화**
- [ ] **병렬 처리**: 도구 체인의 병렬 실행으로 응답 시간 단축
- [ ] **배치 처리**: 여러 요청을 묶어서 처리하는 배치 시스템
- [ ] **메모리 최적화**: 대용량 데이터 처리 시 메모리 사용량 최적화

### **2. 기능 확장**
- [ ] **멀티 모델 지원**: OpenAI 외 다른 LLM 프로바이더 추가
- [ ] **커스텀 도구**: 사용자 정의 분석 도구 생성 기능
- [ ] **학습 기능**: 사용자 피드백을 통한 응답 품질 개선

### **3. 보안 강화**
- [ ] **API 키 관리**: 환경 변수 및 시크릿 관리 시스템
- [ ] **요청 제한**: Rate limiting 및 사용량 제한
- [ ] **입력 검증**: 사용자 입력에 대한 보안 검증 강화

### **4. 모니터링 및 관측성**
- [ ] **성능 메트릭**: 응답 시간, 처리량, 에러율 측정
- [ ] **사용량 추적**: API 호출 패턴 및 사용자 행동 분석
- [ ] **알림 시스템**: 시스템 장애 및 성능 저하 시 알림

### **5. 테스트 및 품질**
- [ ] **단위 테스트**: 각 도구별 단위 테스트 작성
- [ ] **통합 테스트**: 전체 파이프라인 통합 테스트
- [ ] **성능 테스트**: 부하 테스트 및 성능 벤치마크

---

### **의존성 설치**
```bash
# requirements.txt 기반 설치
pip install -r AIChat/requirements.txt

# 또는 개별 설치
pip install langchain langgraph openai redis fastapi
```

### **Redis 설정**
```bash
# Redis 서버 실행
redis-server

# Redis 클라이언트 테스트
redis-cli ping
```

---

## 📚 추가 리소스

- **LangChain 문서**: https://python.langchain.com/
- **LangGraph 문서**: https://langchain-ai.github.io/langgraph/
- **OpenAI API 문서**: https://platform.openai.com/docs
- **Redis 문서**: https://redis.io/documentation
- **FastAPI 문서**: https://fastapi.tiangolo.com/

---

> **문서 버전**: v1.1 (도구 확장 가이드 및 칼만 필터 분석 추가)
> **최종 업데이트**: 2025년 1월  
> **담당자**: LLM Service Development Team