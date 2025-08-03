# 주식 예측 LSTM 모델 프로젝트

미국 주식 매수/매도 신호 생성을 위한 LSTM 기반 예측 시스템입니다. 60일간의 OHLCV 데이터와 기술적 지표를 학습하여 다음 5일의 주가 추세와 Bollinger Band를 예측합니다.

## 🎯 프로젝트 개요

### 주요 기능
- **데이터 수집**: yfinance를 통한 미국 주식 거래량 상위 100개 종목의 3년치 데이터 수집
- **기술적 지표 계산**: MA(5,20,60), Bollinger Band, RSI, MACD 등
- **LSTM 모델**: Attention 메커니즘을 포함한 고도화된 LSTM 모델
- **실시간 추론**: FastAPI 기반 RESTful API 서버
- **배치 처리**: 여러 종목 동시 예측 (batch_size=5)
- **DB 연동**: 다양한 데이터베이스 포맷 지원

### 예측 결과
- **5일간 주가 예측**: 종가, Bollinger Band 상/하한선
- **매수/매도 신호**: 현재 가격과 예측된 Bollinger Band 비교
- **신호 강도**: 0-1 사이의 신뢰도 점수
- **추세 분석**: 상승/하락/횡보 추세 판단

## 🏗️ 프로젝트 구조

```
V5/
├── data_collector.py          # 주식 데이터 수집
├── data_preprocessor.py       # 데이터 전처리 및 기술적 지표 계산
├── lstm_model.py             # LSTM 모델 구현
├── train_model.py            # 모델 학습 스크립트
├── api_server.py             # FastAPI 서버
├── inference_pipeline.py     # 추론 파이프라인
├── db_formatter.py           # DB 저장용 데이터 포맷터
├── model_template_impl.py    # 기존 템플릿 구현
├── requirements.txt          # Python 의존성
├── Dockerfile               # Docker 설정
├── docker-compose.yml       # Docker Compose 설정
├── runpod_setup.sh          # RunPod 환경 설정 스크립트
└── README.md               # 프로젝트 문서
```

## 🚀 설치 및 설정

### 로컬 환경 설정

```bash
# 저장소 클론
git clone <repository-url>
cd V5

# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### RunPod 환경 설정

```bash
# RunPod에서 실행
chmod +x runpod_setup.sh
./runpod_setup.sh
```

### Docker 사용

```bash
# 이미지 빌드
docker build -t stock-prediction-api .

# 컨테이너 실행
docker run -p 8000:8000 --gpus all stock-prediction-api

# 또는 Docker Compose 사용
docker-compose up -d
```

## 📊 사용법

### 1. 데이터 수집 및 모델 학습

```bash
# 전체 학습 파이프라인 실행
python train_model.py --epochs 100 --batch-size 32 --model-type lstm_attention

# 특정 옵션으로 학습
python train_model.py \
    --data-dir data \
    --model-dir models \
    --epochs 50 \
    --batch-size 64 \
    --model-type lstm_ensemble
```

### 2. API 서버 실행

```bash
# 개발 환경
python api_server.py

# 프로덕션 환경
uvicorn api_server:app --host 0.0.0.0 --port 8000 --workers 4
```

### 3. 단일 종목 예측

```bash
# CLI로 추론 실행
python inference_pipeline.py --symbols AAPL --output predictions.json

# API 호출 (curl)
curl -X POST "http://localhost:8000/predict" \
     -H "Content-Type: application/json" \
     -d '{"symbol": "AAPL", "days": 60}'
```

### 4. 배치 예측

```bash
# CLI로 배치 추론
python inference_pipeline.py \
    --symbols AAPL MSFT GOOGL AMZN NVDA \
    --batch-size 5 \
    --output batch_predictions.json

# API 호출
curl -X POST "http://localhost:8000/predict/batch" \
     -H "Content-Type: application/json" \
     -d '{
       "symbols": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"],
       "days": 60,
       "batch_size": 5
     }'
```

### 5. 데이터베이스 저장

```bash
# 예측 결과를 다양한 형식으로 저장
python db_formatter.py \
    --input predictions.json \
    --output-csv predictions.csv \
    --output-sqlite predictions.db \
    --db-type mysql
```

## 🔧 API 엔드포인트

### 기본 엔드포인트
- `GET /` : API 정보
- `GET /health` : 헬스 체크
- `GET /models/info` : 모델 정보

### 예측 엔드포인트
- `POST /predict` : 단일 종목 예측
- `POST /predict/batch` : 배치 예측

### 요청/응답 예시

**단일 예측 요청:**
```json
{
  "symbol": "AAPL",
  "days": 60
}
```

**응답:**
```json
{
  "symbol": "AAPL",
  "prediction_date": "2024-01-15 10:30:00",
  "current_price": 185.23,
  "predictions": [
    {
      "day": 1,
      "date": "2024-01-16",
      "predicted_close": 187.45,
      "trend": "up"
    }
  ],
  "bollinger_bands": [
    {
      "day": 1,
      "date": "2024-01-16",
      "bb_upper": 190.12,
      "bb_lower": 182.34,
      "bb_middle": 186.23
    }
  ],
  "buy_signal": false,
  "sell_signal": false,
  "confidence_score": 0.82,
  "status": "success"
}
```

## 🧠 모델 아키텍처

### LSTM with Attention 모델
- **입력**: 60일간의 18개 특성 (OHLCV + 기술적 지표)
- **출력**: 5일간의 3개 타겟 (Close, BB_Upper, BB_Lower)
- **구조**:
  - LSTM 레이어 (128, 64 units)
  - Multi-Head Attention (8 heads)
  - Dense 레이어 (128, 64 units)
  - Layer Normalization & Dropout

### 사용되는 특성
- **가격 데이터**: Open, High, Low, Close, Volume
- **이동평균**: MA_5, MA_20, MA_60
- **볼린저 밴드**: BB_Upper, BB_Middle, BB_Lower, BB_Percent, BB_Width
- **기술 지표**: RSI, MACD, MACD_Signal, Price_Change, Volatility

## 📈 성능 및 메트릭

### 모델 평가 지표
- **MSE (Mean Squared Error)**: 전체 및 타겟별
- **MAE (Mean Absolute Error)**: 전체 및 타겟별
- **신뢰도 점수**: 데이터 품질 기반 (0-1)

### 신호 생성 로직
- **매수 신호**: 현재가가 BB 하한에 가깝고 상승 예상
- **매도 신호**: 현재가가 BB 상한에 가깝고 하락 예상
- **신호 강도**: BB 위치 + 예측 방향성 결합

## 🗄️ 데이터베이스 지원

### 지원 형식
- **MySQL/PostgreSQL**: 관계형 데이터베이스
- **MongoDB**: NoSQL 문서 데이터베이스
- **Elasticsearch**: 검색 및 분석 엔진
- **SQLite**: 로컬 데이터베이스
- **CSV/JSON**: 파일 형식

### 스키마 예시 (MySQL)
```sql
CREATE TABLE stock_predictions (
    prediction_id VARCHAR(100) PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    prediction_timestamp DATETIME NOT NULL,
    current_price DECIMAL(10,4) NOT NULL,
    buy_signal BOOLEAN NOT NULL,
    sell_signal BOOLEAN NOT NULL,
    confidence_score DECIMAL(5,4),
    predicted_prices JSON,
    predicted_bb_upper JSON,
    predicted_bb_lower JSON,
    -- ... 기타 필드
);
```

## 🔄 실제 프로젝트 통합

### API 연동 방법
1. **FastAPI 서버 실행** (RunPod에서)
2. **원래 프로젝트에서 HTTP 요청**
3. **예측 결과를 DB에 저장**
4. **실시간 가격과 비교하여 신호 생성**

### 예시 통합 코드
```python
import requests

# 예측 요청
response = requests.post('http://runpod-api-url:8000/predict', 
                        json={'symbol': 'AAPL', 'days': 60})
prediction = response.json()

# DB에 저장
if prediction['status'] == 'success':
    save_to_database(prediction)
    
    # 매수/매도 신호 확인
    if prediction['buy_signal']:
        send_buy_signal(prediction['symbol'])
    elif prediction['sell_signal']:
        send_sell_signal(prediction['symbol'])
```

## 🚨 주의사항

### 투자 관련 면책사항
- 이 모델의 예측은 **참고용**이며, 실제 투자 결정에 사용 시 주의가 필요합니다
- 과거 데이터 기반 예측이므로 미래 수익을 보장하지 않습니다
- 투자는 본인 책임하에 진행하시기 바랍니다

### 기술적 제한사항
- 모델 성능은 시장 상황에 따라 달라질 수 있습니다
- GPU 메모리 부족 시 배치 크기를 조정하세요
- API 요청 제한을 고려하여 호출 빈도를 조절하세요

## 🛠️ 트러블슈팅

### 일반적인 문제

**1. GPU 메모리 부족**
```bash
# 배치 크기 감소
python train_model.py --batch-size 16

# 메모리 증가 허용 설정
export TF_FORCE_GPU_ALLOW_GROWTH=true
```

**2. 데이터 수집 실패**
```bash
# 네트워크 연결 확인
pip install --upgrade yfinance

# API 제한 대기 시간 증가
```

**3. 모델 로드 오류**
```bash
# 모델 파일 경로 확인
ls -la models/

# 전처리기 재생성  
python train_model.py --force-reload
```

## 📞 지원 및 문의

- **이슈 리포트**: GitHub Issues
- **기능 요청**: GitHub Discussions
- **문서 개선**: Pull Request 환영

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

---

**Happy Trading with AI! 🚀📈**