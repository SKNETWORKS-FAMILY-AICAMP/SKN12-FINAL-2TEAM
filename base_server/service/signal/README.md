# AI Trading Platform — Signal Service

> **개요**: SKN12-FINAL-2TEAM의 AI 트레이딩 플랫폼 백엔드 Signal 서비스입니다. 실시간 주식 데이터 모니터링, 볼린저 밴드 기반 기술적 분석, AI 모델 서버 연동을 통한 지능형 매수/매도 시그널 생성 및 사용자 알림을 제공하는 시스템입니다.

---

## 🏗️ 프로젝트 구조

### 디렉토리 구조
```
signal/
├── __init__.py                    # 패키지 초기화
├── README.md                      # 서비스 문서
└── signal_monitoring_service.py   # 메인 시그널 모니터링 서비스
```

### 핵심 컴포넌트
- **SignalMonitoringService**: 실시간 시그널 모니터링 및 생성
- **KoreaInvestmentWebSocketIOCP**: 한국투자증권 실시간 데이터 수신
- **YahooFinanceClient**: Yahoo Finance 데이터 수집
- **Model Server Integration**: AI 예측 모델 연동
- **NotificationService**: 사용자 알림 발송

---

## 🔧 핵심 기능

### 1. **실시간 시그널 모니터링**
- **웹소켓 기반 실시간 데이터**: 한국투자증권 API를 통한 실시간 주가 수신
- **마스터/슬레이브 아키텍처**: 마스터 서버에서만 웹소켓 로직 실행
- **자동 폴백 시스템**: 웹소켓 연결 실패 시 REST API 폴링으로 자동 전환
- **동적 심볼 구독**: 사용자 알림 설정에 따른 실시간 모니터링 목록 관리

### 2. **기술적 분석 기반 시그널 생성**
- **볼린저 밴드 분석**: 5일 이동평균 및 표준편차 기반 매수/매도 신호
- **돌파 신호 감지**: 상단/하단 밴드 돌파 시 즉시 시그널 생성
- **변동성 기반 필터링**: ATR(Average True Range) 기반 노이즈 제거
- **다중 시간대 분석**: 일봉, 분봉 데이터 통합 분석

### 3. **AI 모델 서버 연동**
- **예측 모델 호출**: 별도 모델 서버 API를 통한 미래 가격 예측
- **신뢰도 기반 신호**: AI 예측 결과의 신뢰도 점수 반영
- **시그널 등급 분류**: STRONG_BUY, BUY, SELL, STRONG_SELL 등급
- **예측 정확도 추적**: 실제 가격 변동과 예측 결과 비교 분석

### 4. **사용자 알림 시스템**
- **다중 채널 알림**: 이메일, SMS, 인앱 푸시, 웹훅 지원
- **개인화 알림 설정**: 사용자별 알림 조건 및 채널 설정
- **실시간 알림 발송**: 시그널 발생 즉시 해당 사용자에게 전송
- **알림 히스토리 관리**: 발송된 알림의 상태 및 수신 확인 추적

### 5. **성과 추적 및 분석**
- **시그널 성과 평가**: 일일 수익률 계산 및 성공률 분석
- **백테스팅 결과**: 과거 시그널의 실제 성과 데이터 축적
- **리스크 메트릭**: 최대 손실, 샤프 비율, 승률 등 지표 제공
- **연속성 모니터링**: 연속 손실 시 자동 알림 및 전략 조정

---

## 📚 사용된 라이브러리

### **Core Framework**
- **asyncio**: 비동기 프로그래밍 및 이벤트 루프 관리
- **typing**: 타입 힌트 및 타입 안전성
- **datetime**: 시간 기반 데이터 처리 및 스케줄링

### **외부 API 연동**
- **KoreaInvestmentWebSocketIOCP**: 한국투자증권 실시간 웹소켓
- **YahooFinanceClient**: Yahoo Finance 데이터 수집
- **ExternalService**: 외부 서비스 통합 관리

### **데이터 처리 & 분석**
- **Redis Cache**: 실시간 데이터 캐싱 및 성능 최적화
- **JSON**: 데이터 직렬화 및 API 통신
- **UUID**: 고유 식별자 생성

### **스케줄링 & 알림**
- **SchedulerService**: 주기적 작업 스케줄링
- **NotificationService**: 다중 채널 알림 발송
- **ScheduleJob**: 작업 정의 및 실행 관리

---

## 🪝 핵심 클래스 및 메서드

### **SignalMonitoringService - 메인 서비스 클래스**

```python
class SignalMonitoringService:
    """시그널 모니터링 서비스 - 실시간 주가 감시 및 볼린저 밴드 기반 시그널 발생"""
    
    _initialized = False
    _monitoring_symbols: Set[str] = set()  # 모니터링 중인 종목
    _korea_websocket: Optional[KoreaInvestmentWebSocketIOCP] = None
    _scheduler_job_ids: Set[str] = set()  # 스케줄러 작업 ID들
    _is_master_server: bool = False  # 마스터 서버 여부
    
    @classmethod
    async def init(cls):
        """서비스 초기화 - 마스터 서버만 한투증권 로직 실행"""
        # 마스터/슬레이브 서버 환경 확인
        # 웹소켓 연결 및 스케줄러 설정
    
    @classmethod
    async def subscribe_symbol(cls, symbol: str):
        """특정 종목 실시간 모니터링 구독"""
        # 웹소켓 구독 설정
        # 캐시 초기화
        # 알림 설정 동기화
    
    @classmethod
    async def _handle_us_stock_data(cls, data: Dict):
        """미국 주식 실시간 데이터 처리"""
        # 데이터 유효성 검사
        # 볼린저 밴드 계산
        # 시그널 생성 및 저장
```

**동작 방식**:
- 마스터/슬레이브 서버 환경 자동 감지
- 웹소켓 기반 실시간 데이터 수신
- 볼린저 밴드 기반 기술적 분석
- AI 모델 서버 연동을 통한 예측 기반 시그널

### **볼린저 밴드 시그널 생성**

```python
async def _check_bollinger_signal(cls, symbol: str, current_price: float):
    """볼린저 밴드 기반 매수/매도 시그널 생성"""
    
    # 5일 이동평균 및 표준편차 계산
    sma_5 = sum(prices[-5:]) / 5
    std_5 = sqrt(sum((p - sma_5) ** 2 for p in prices[-5:]) / 5)
    
    # 상단/하단 밴드 계산
    upper_band = sma_5 + (2 * std_5)
    lower_band = sma_5 - (2 * std_5)
    
    # 돌파 신호 감지
    if current_price > upper_band:
        signal = "SELL"  # 상단 밴드 돌파 → 매도 신호
    elif current_price < lower_band:
        signal = "BUY"   # 하단 밴드 돌파 → 매수 신호
    else:
        signal = "HOLD"  # 밴드 내부 → 관망
    
    return signal, confidence_score
```

**동작 방식**:
- 최근 5일 가격 데이터 기반 이동평균 계산
- 표준편차를 이용한 변동성 측정
- 상단/하단 밴드 돌파 시 즉시 시그널 생성
- 신뢰도 점수와 함께 시그널 등급 결정

---

## 🌐 API 연동 방식

### **한국투자증권 웹소켓 연동**

```python
# KoreaInvestmentWebSocketIOCP를 통한 실시간 데이터 수신
cls._korea_websocket = ServiceContainer.get_korea_investment_websocket()

if cls._korea_websocket and cls._korea_websocket.is_connected():
    # 실시간 데이터 구독
    await cls._korea_websocket.subscribe_symbol(symbol)
    
    # 데이터 수신 콜백 설정
    cls._korea_websocket.set_data_callback(cls._handle_korea_stock_data)
else:
    # 웹소켓 연결 실패 시 REST API 폴링으로 폴백
    Logger.warn("웹소켓 연결 실패, REST API 폴링 모드로 전환")
    cls._fallback_to_rest_api(symbol)
```

### **AI 모델 서버 연동**

```python
async def _call_model_server_predict(cls, symbol: str) -> Optional[PredictionResult]:
    """모델 서버 API 호출하여 예측 데이터 수집"""
    
    try:
        # 예측 요청 데이터 구성
        request = PredictRequest(
            symbol=symbol,
            timeframe="1d",
            features=["price", "volume", "rsi", "macd", "bollinger"],
            prediction_horizon=5  # 5일 후 예측
        )
        
        # 모델 서버 API 호출
        response = await model_server_client.predict(request)
        
        if response.success:
            return response.prediction
        else:
            Logger.error(f"모델 서버 예측 실패: {response.error}")
            return None
            
    except Exception as e:
        Logger.error(f"모델 서버 연동 오류: {e}")
        return None
```

### **사용자 알림 발송**

```python
async def _send_signal_notification(cls, signal_data: Dict):
    """생성된 시그널을 사용자에게 알림 발송"""
    
    # 해당 종목을 구독하는 사용자 목록 조회
    subscribers = await cls._get_symbol_subscribers(signal_data["symbol"])
    
    for subscriber in subscribers:
        # 사용자별 알림 설정 확인
        notification_settings = subscriber.get_notification_settings()
        
        # 알림 채널별 발송
        if notification_settings.email_enabled:
            await NotificationService.send_email(
                user_id=subscriber.id,
                subject=f"🚨 {signal_data['symbol']} {signal_data['signal']} 시그널",
                content=cls._format_signal_email(signal_data),
                channel=NotificationChannel.EMAIL
            )
        
        if notification_settings.push_enabled:
            await NotificationService.send_push_notification(
                user_id=subscriber.id,
                title=f"📈 {signal_data['symbol']} 시그널",
                body=f"{signal_data['signal']} - 신뢰도: {signal_data['confidence']}%",
                channel=NotificationChannel.PUSH
            )
```

---

## 🔄 Signal 서비스 전체 흐름

### **1. 서비스 초기화**
```
1. 마스터/슬레이브 서버 환경 확인
2. 한국투자증권 웹소켓 연결 설정
3. 스케줄러 작업 등록 (알림 동기화, 성과 업데이트)
4. 테스트 종목(AAPL) 자동 구독
5. 캐시 시스템 초기화
```

### **2. 실시간 데이터 수신 플로우**
```
1. 웹소켓을 통한 실시간 가격 데이터 수신
2. 데이터 유효성 검사 및 전처리
3. Redis 캐시에 최신 데이터 저장
4. 5일 이동평균 및 표준편차 계산
5. 볼린저 밴드 상단/하단 돌파 감지
```

### **3. 시그널 생성 및 분석 플로우**
```
1. 볼린저 밴드 돌파 시 1차 시그널 생성
2. AI 모델 서버에 예측 요청
3. 예측 결과와 기술적 신호 통합 분석
4. 최종 시그널 등급 결정 (STRONG_BUY ~ STRONG_SELL)
5. 시그널 데이터베이스 저장
```

### **4. 알림 발송 플로우**
```
1. 시그널 발생 종목을 구독하는 사용자 목록 조회
2. 사용자별 알림 설정 확인 (이메일, 푸시, SMS)
3. 알림 채널별 메시지 포맷팅
4. NotificationService를 통한 실제 발송
5. 발송 결과 추적 및 로그 기록
```

### **5. 성과 추적 플로우**
```
1. 일일 시그널 성과 평가 (자정 실행)
2. 실제 가격 변동과 예측 결과 비교
3. 수익률, 승률, 최대 손실 등 메트릭 계산
4. 성과 데이터 데이터베이스 업데이트
5. 연속 손실 시 자동 경고 알림
```

---

## 🔌 시그널 생성 알고리즘 상세

### **볼린저 밴드 계산**

```python
def calculate_bollinger_bands(prices: List[float], period: int = 5, std_dev: int = 2):
    """볼린저 밴드 계산"""
    
    if len(prices) < period:
        return None, None, None
    
    # 이동평균 계산
    sma = sum(prices[-period:]) / period
    
    # 표준편차 계산
    variance = sum((p - sma) ** 2 for p in prices[-period:]) / period
    std = sqrt(variance)
    
    # 상단/하단 밴드
    upper_band = sma + (std_dev * std)
    lower_band = sma - (std_dev * std)
    
    return upper_band, sma, lower_band
```

### **돌파 신호 감지**

```python
def detect_breakout_signal(current_price: float, upper_band: float, lower_band: float):
    """볼린저 밴드 돌파 신호 감지"""
    
    # 돌파 임계값 (밴드 경계의 1% 이내)
    upper_threshold = upper_band * 0.99
    lower_threshold = lower_band * 1.01
    
    if current_price > upper_threshold:
        return {
            "signal": "SELL",
            "strength": "STRONG" if current_price > upper_band else "WEAK",
            "breakout_type": "upper_band",
            "distance": (current_price - upper_band) / upper_band * 100
        }
    elif current_price < lower_threshold:
        return {
            "signal": "BUY",
            "strength": "STRONG" if current_price < lower_band else "WEAK",
            "breakout_type": "lower_band",
            "distance": (lower_band - current_price) / lower_band * 100
        }
    else:
        return {
            "signal": "HOLD",
            "strength": "NEUTRAL",
            "breakout_type": "none",
            "distance": 0.0
        }
```

### **AI 예측 통합**

```python
def integrate_ai_prediction(technical_signal: Dict, ai_prediction: PredictionResult):
    """기술적 신호와 AI 예측 통합"""
    
    # 신뢰도 가중 평균 계산
    tech_confidence = technical_signal.get("confidence", 0.5)
    ai_confidence = ai_prediction.confidence
    
    # 가중 평균 (기술적 60%, AI 40%)
    combined_confidence = (tech_confidence * 0.6) + (ai_confidence * 0.4)
    
    # 신호 방향 일치성 확인
    tech_direction = technical_signal["signal"]
    ai_direction = ai_prediction.direction
    
    if tech_direction == ai_direction:
        # 방향 일치 시 신뢰도 증가
        combined_confidence *= 1.2
        signal_strength = "STRONG"
    else:
        # 방향 불일치 시 신뢰도 감소
        combined_confidence *= 0.8
        signal_strength = "WEAK"
    
    # 최종 시그널 등급 결정
    if combined_confidence >= 0.8:
        if tech_direction == "BUY":
            final_signal = "STRONG_BUY"
        else:
            final_signal = "STRONG_SELL"
    elif combined_confidence >= 0.6:
        if tech_direction == "BUY":
            final_signal = "BUY"
        else:
            final_signal = "SELL"
    else:
        final_signal = "HOLD"
    
    return {
        "final_signal": final_signal,
        "confidence": combined_confidence,
        "strength": signal_strength,
        "tech_signal": technical_signal,
        "ai_prediction": ai_prediction
    }
```

---

## 🎯 코드 철학

### **1. 마스터/슬레이브 아키텍처**
- **마스터 서버**: 한국투자증권 웹소켓 및 실시간 시그널 생성
- **슬레이브 서버**: 일반 웹서버 기능만 담당하여 시스템 부하 분산
- **자동 환경 감지**: 서버 환경에 따른 기능 자동 활성화/비활성화

### **2. 실시간성과 안정성**
- **웹소켓 우선**: 실시간 데이터 수신을 위한 웹소켓 연결
- **폴백 시스템**: 웹소켓 실패 시 REST API로 자동 전환
- **연결 상태 모니터링**: 지속적인 연결 상태 확인 및 자동 재연결

### **3. 데이터 품질 및 성능**
- **캐싱 전략**: Redis를 통한 실시간 데이터 및 계산 결과 캐싱
- **데이터 유효성 검사**: 수신된 데이터의 품질 및 일관성 검증
- **성능 최적화**: 불필요한 API 호출 최소화 및 배치 처리

### **4. 사용자 경험**
- **개인화 알림**: 사용자별 알림 조건 및 채널 설정
- **실시간 발송**: 시그널 발생 즉시 알림 전송
- **알림 히스토리**: 발송된 알림의 상태 및 수신 확인 추적

---

## 🚀 개선할 점

### **1. 성능 최적화**
- [ ] **병렬 처리**: 여러 종목의 시그널 분석을 동시에 처리
- [ ] **배치 알림**: 사용자별 알림을 배치로 묶어서 처리
- [ ] **캐시 전략**: 더 효율적인 데이터 캐싱 및 TTL 관리

### **2. 기능 확장**
- [ ] **다중 지표**: RSI, MACD, 스토캐스틱 등 추가 기술적 지표
- [ ] **머신러닝 통합**: 로컬 ML 모델을 통한 실시간 예측
- [ ] **백테스팅 엔진**: 과거 데이터를 이용한 전략 성과 검증

### **3. 알림 시스템 강화**
- [ ] **스마트 알림**: 사용자 행동 패턴 기반 알림 타이밍 최적화
- [ ] **알림 우선순위**: 시그널 중요도에 따른 알림 우선순위 설정
- [ ] **알림 템플릿**: 사용자 맞춤형 알림 메시지 템플릿

### **4. 모니터링 및 관측성**
- [ ] **시그널 품질 메트릭**: 정확도, 지연시간, 오탐률 측정
- [ ] **시스템 성능 모니터링**: API 응답시간, 캐시 히트율, 알림 발송 성공률
- [ ] **사용자 행동 분석**: 알림 클릭률, 시그널 반응률 등 사용자 참여도

### **5. 보안 및 안정성**
- [ ] **API 키 관리**: 환경 변수 및 시크릿 관리 시스템
- [ ] **요청 제한**: Rate limiting 및 사용량 제한
- [ ] **에러 복구**: 시스템 장애 시 자동 복구 및 알림

---

## 🛠️ 개발 환경 설정

### **환경 변수**
```bash
# .env
KOREA_INVESTMENT_APP_KEY=your_korea_investment_app_key
KOREA_INVESTMENT_APP_SECRET=your_korea_investment_app_secret
KOREA_INVESTMENT_ACCOUNT=your_korea_investment_account
MODEL_SERVER_URL=http://localhost:8001/api/predict
REDIS_URL=redis://localhost:6379/0
```

### **의존성 설치**
```bash
# requirements.txt 기반 설치
pip install -r requirements.txt

# 또는 개별 설치
pip install asyncio redis websockets aiohttp
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

- **한국투자증권 API 문서**: https://apiportal.koreainvestment.com/
- **Yahoo Finance API**: https://finance.yahoo.com/
- **볼린저 밴드 지표**: https://www.investopedia.com/terms/b/bollingerbands.asp
- **Redis 문서**: https://redis.io/documentation
- **asyncio 문서**: https://docs.python.org/3/library/asyncio.html

---

> **문서 버전**: v2.0 (LLM 서비스 README 구조 기반으로 완전 재작성)
> **최종 업데이트**: 2025년 1월  
> **담당자**: Signal Service Development Team
