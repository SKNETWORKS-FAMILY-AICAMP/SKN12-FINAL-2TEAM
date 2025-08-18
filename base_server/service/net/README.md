# AI Trading Platform — Network Service

> **개요**: SKN12-FINAL-2TEAM의 AI 트레이딩 플랫폼 백엔드 Network 서비스입니다. FastAPI 기반 웹 서버의 네트워크 계층을 관리하며, 미들웨어를 통한 요청 처리, 타임아웃 관리, 성능 모니터링, 보안 강화를 담당하는 시스템입니다.

---

## 🏗️ 프로젝트 구조

### 디렉토리 구조
```
net/
├── __init__.py                    # 패키지 초기화
├── README.md                      # 서비스 문서
├── net_config.py                  # 네트워크 설정 관리
├── fastapi_config.py              # FastAPI 전용 설정
├── fastapi_middleware.py          # FastAPI 미들웨어 서비스
├── net_error_code.py              # 네트워크 에러 코드 정의
├── argparse_util.py               # 명령행 인자 파싱 유틸리티
└── protocol_base.py               # 프로토콜 기본 클래스
```

### 핵심 컴포넌트
- **NetConfig**: 기본 서버 설정 및 FastAPI 미들웨어 설정 통합 관리
- **FastApiConfig**: FastAPI 전용 설정 (타임아웃, 크기 제한, 성능 최적화)
- **FastAPIMiddlewareService**: 미들웨어 관리 및 설정 서비스
- **RequestTimeoutMiddleware**: HTTP 요청 타임아웃 처리
- **RequestSizeLimitMiddleware**: 요청 크기 제한 및 보안
- **SlowRequestLoggingMiddleware**: 성능 모니터링 및 로깅

---

## 🔧 핵심 기능

### 1. **FastAPI 미들웨어 관리**
- **미들웨어 체인 구성**: 요청 처리 파이프라인을 통한 단계별 처리
- **동적 설정**: NetConfig를 통한 런타임 미들웨어 활성화/비활성화
- **순서 최적화**: 성능과 보안을 고려한 미들웨어 배치 순서
- **서비스 패턴**: 기존 Service 패턴과 일관된 구조 유지

### 2. **요청 타임아웃 관리**
- **LLM API 호출 지원**: 긴 작업 시간을 고려한 타임아웃 설정 (기본 600초)
- **비동기 처리**: asyncio.wait_for를 통한 안전한 타임아웃 처리
- **적절한 응답**: 504 Gateway Timeout과 상세한 에러 정보 제공
- **로깅 및 모니터링**: 타임아웃 발생 시 상세한 로그 기록

### 3. **요청 크기 제한 및 보안**
- **업로드 크기 제한**: 기본 50MB, 설정 가능한 최대 요청 크기
- **공격 방지**: 대용량 업로드 공격으로부터 시스템 보호
- **메모리 관리**: 과도한 메모리 사용 방지 및 리소스 제어
- **적절한 에러 응답**: 413 Payload Too Large와 상세한 제한 정보

### 4. **성능 모니터링 및 로깅**
- **느린 요청 감지**: 설정 가능한 임계값 기반 성능 병목 감지
- **응답 시간 헤더**: X-Process-Time 헤더를 통한 클라이언트 측 모니터링
- **선택적 로깅**: 전체 요청 로깅 또는 느린 요청만 로깅 선택 가능
- **메트릭 수집**: 요청 수, 타임아웃, 크기 제한, 느린 요청 통계

### 5. **압축 및 최적화**
- **GZIP 압축**: 500 bytes 이상 요청에 대한 자동 압축
- **압축 최적화**: 설정 가능한 최소 압축 크기 및 압축 활성화/비활성화
- **성능 균형**: 압축 비용과 대역폭 절약의 균형점 설정

---

## 📚 사용된 라이브러리

### **Core Framework**
- **FastAPI**: 현대적인 Python 웹 프레임워크
- **Starlette**: ASGI 기반 미들웨어 및 유틸리티
- **asyncio**: 비동기 프로그래밍 및 이벤트 루프 관리
- **Pydantic**: 데이터 검증 및 설정 관리

### **네트워크 & HTTP**
- **aiohttp**: 비동기 HTTP 클라이언트/서버
- **HTTP/1.1**: 표준 HTTP 프로토콜 지원
- **WebSocket**: 실시간 양방향 통신 지원

### **설정 & 유틸리티**
- **typing**: 타입 힌트 및 타입 안전성
- **argparse**: 명령행 인자 파싱
- **os/sys**: 시스템 환경 및 인자 접근

### **로깅 & 모니터링**
- **Logger**: 구조화된 로깅 시스템
- **메트릭 수집**: 성능 지표 및 통계 데이터
- **헬스체크**: 서비스 상태 모니터링

---

## 🪝 핵심 클래스 및 메서드

### **FastAPIMiddlewareService - 메인 서비스 클래스**

```python
class FastAPIMiddlewareService:
    """FastAPI 미들웨어 관리 서비스"""
    
    _initialized: bool = False
    _config: Optional[Dict[str, Any]] = None
    _metrics: Dict[str, Any] = {}
    
    @classmethod
    def init(cls, net_config: NetConfig) -> bool:
        """FastAPI 미들웨어 서비스 초기화"""
        # NetConfig에서 FastAPI 설정 읽기
        # 메트릭 초기화
        # 서비스 상태 설정
    
    @classmethod
    def setup_middlewares(cls, app, net_config: NetConfig):
        """설정에 따라 미들웨어를 FastAPI 앱에 추가"""
        # 미들웨어 순서: SlowRequestLogging → RequestSizeLimit → RequestTimeout
        # 각 미들웨어의 활성화/비활성화 설정 적용
        # 상세한 로깅으로 디버깅 지원
    
    @classmethod
    def get_metrics(cls) -> Dict[str, Any]:
        """현재 메트릭 반환"""
        # 요청 수, 타임아웃, 크기 제한, 느린 요청 통계
    
    @classmethod
    def health_check(cls) -> Dict[str, Any]:
        """서비스 상태 확인"""
        # 초기화 상태, 메트릭, 헬스체크 결과
```

**동작 방식**:
- NetConfig를 통한 설정 기반 미들웨어 관리
- 기존 Service 패턴과 일관된 구조 유지
- 미들웨어 체인을 통한 단계별 요청 처리
- 실시간 메트릭 수집 및 모니터링

### **RequestTimeoutMiddleware - 타임아웃 처리**

```python
class RequestTimeoutMiddleware(BaseHTTPMiddleware):
    """FastAPI 요청 타임아웃 미들웨어"""
    
    def __init__(self, app, timeout_seconds: int = 300):
        super().__init__(app)
        self.timeout_seconds = timeout_seconds
    
    async def dispatch(self, request: Request, call_next):
        try:
            # 비동기 타임아웃 적용
            response = await asyncio.wait_for(
                call_next(request), 
                timeout=self.timeout_seconds
            )
            return response
            
        except asyncio.TimeoutError:
            # 타임아웃 발생 시 504 응답
            Logger.warn(f"⏰ 요청 타임아웃 발생 ({self.timeout_seconds}초): {request.method} {request.url.path}")
            return Response(
                content=f"Request timeout after {self.timeout_seconds} seconds",
                status_code=504,
                headers={"X-Timeout": str(self.timeout_seconds)}
            )
```

**동작 방식**:
- asyncio.wait_for를 통한 안전한 타임아웃 처리
- LLM API 호출 등 긴 작업 시 클라이언트 hang up 방지
- 타임아웃 발생 시 적절한 HTTP 상태 코드와 에러 정보 제공
- 상세한 로깅으로 디버깅 및 모니터링 지원

### **RequestSizeLimitMiddleware - 크기 제한 및 보안**

```python
class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI 요청 크기 제한 미들웨어"""
    
    def __init__(self, app, max_size: int = 16777216):  # 16MB 기본값
        super().__init__(app)
        self.max_size = max_size
    
    async def dispatch(self, request: Request, call_next):
        try:
            # Content-Length 헤더 확인
            content_length = request.headers.get("content-length")
            
            if content_length:
                content_length_int = int(content_length)
                if content_length_int > self.max_size:
                    Logger.warn(f"📦 요청 크기 제한 초과: {content_length_int} > {self.max_size} bytes")
                    return Response(
                        content=f"Request too large. Max size: {self.max_size} bytes",
                        status_code=413,
                        headers={"X-Max-Size": str(self.max_size)}
                    )
            
            return await call_next(request)
```

**동작 방식**:
- Content-Length 헤더를 통한 사전 크기 검증
- 설정 가능한 최대 요청 크기 (기본 16MB, 최대 50MB)
- 대용량 업로드 공격으로부터 시스템 보호
- 적절한 HTTP 상태 코드와 제한 정보 제공

---

## 🌐 설정 및 구성 방식

### **NetConfig - 통합 네트워크 설정**

```python
class NetConfig(BaseModel):
    """네트워크 설정 클래스"""
    
    # 기본 서버 설정
    host: str = "0.0.0.0"
    port: int = 8000
    
    # FastAPI 미들웨어 설정
    fastApiConfig: Optional[FastApiConfig] = None

class FastApiConfig(BaseModel):
    """FastAPI 미들웨어 설정 클래스"""
    
    # 타임아웃 관련 설정
    request_timeout: int = 600                    # HTTP 요청 전체 처리 시간(초)
    slow_request_threshold: float = 3.0           # 느린 요청 로깅 기준(초)
    
    # 크기 제한 설정
    max_request_size: int = 52428800              # 요청 본문 최대 크기(50MB)
    
    # 미들웨어 활성화 설정
    enable_request_timeout: bool = True           # 요청 타임아웃 미들웨어 활성화
    enable_size_limit: bool = True                # 요청 크기 제한 미들웨어 활성화
    enable_slow_request_logging: bool = True      # 느린 요청 로깅 활성화
    enable_gzip: bool = True                      # GZIP 압축 활성화
    
    # 압축 설정
    gzip_minimum_size: int = 500                  # GZIP 압축 최소 크기(bytes)
    
    # 로깅 설정
    log_all_requests: bool = False                # 모든 요청 로깅 (운영환경에서는 false)
```

### **설정 파일 예시**

```python
# config.py
from service.net.net_config import NetConfig, FastApiConfig

# FastAPI 미들웨어 설정
fastapi_config = FastApiConfig(
    request_timeout=600,              # LLM API 호출 고려한 10분 타임아웃
    slow_request_threshold=3.0,       # 3초 이상 요청을 느린 요청으로 분류
    max_request_size=52428800,        # 50MB 최대 업로드 크기
    enable_request_timeout=True,      # 타임아웃 미들웨어 활성화
    enable_size_limit=True,           # 크기 제한 미들웨어 활성화
    enable_slow_request_logging=True, # 느린 요청 로깅 활성화
    enable_gzip=True,                 # GZIP 압축 활성화
    gzip_minimum_size=500,            # 500 bytes 이상 압축
    log_all_requests=False            # 운영환경에서는 false
)

# 통합 네트워크 설정
net_config = NetConfig(
    host="0.0.0.0",
    port=8000,
    fastApiConfig=fastapi_config
)
```

---

## 🏥 헬스체크 엔드포인트

### **요구사항 정의서 반영**
요구사항 정의서에서 명시된 "헬스체크 API 제공" 항목을 구현하여 시스템 모니터링 및 운영 지원을 제공합니다.

### **헬스체크 API 엔드포인트**

#### **1. 기본 헬스체크 (`/healthz`)**
```python
from fastapi import APIRouter, HTTPException
from service.net.fastapi_middleware import FastAPIMiddlewareService

router = APIRouter()

@router.get("/healthz")
async def health_check():
    """기본 헬스체크 엔드포인트"""
    try:
        # FastAPI 미들웨어 서비스 상태 확인
        middleware_health = FastAPIMiddlewareService.health_check()
        
        # 전체 시스템 상태 종합
        overall_health = {
            "status": "healthy" if middleware_health["healthy"] else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "services": {
                "fastapi_middleware": middleware_health
            }
        }
        
        if overall_health["status"] == "unhealthy":
            raise HTTPException(status_code=503, detail="Service unhealthy")
        
        return overall_health
        
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")
```

#### **2. 상세 헬스체크 (`/healthz/detailed`)**
```python
@router.get("/healthz/detailed")
async def detailed_health_check():
    """상세 헬스체크 엔드포인트 - 메트릭 포함"""
    try:
        # 미들웨어 서비스 상세 상태
        middleware_health = FastAPIMiddlewareService.health_check()
        middleware_metrics = FastAPIMiddlewareService.get_metrics()
        
        # 시스템 리소스 상태 (예시)
        import psutil
        system_health = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        }
        
        detailed_health = {
            "status": "healthy" if middleware_health["healthy"] else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "services": {
                "fastapi_middleware": middleware_health
            },
            "metrics": middleware_metrics,
            "system": system_health
        }
        
        return detailed_health
        
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Detailed health check failed: {str(e)}")
```

#### **3. 헬스체크 응답 스키마**
```json
{
  "status": "healthy|unhealthy",
  "timestamp": "2025-01-20T10:30:00Z",
  "version": "1.0.0",
  "services": {
    "fastapi_middleware": {
      "service_name": "FastAPIMiddlewareService",
      "initialized": true,
      "healthy": true,
      "metrics": {
        "total_requests": 1250,
        "timeout_count": 3,
        "size_limit_exceeded": 1,
        "slow_requests": 15
      }
    }
  },
  "metrics": {
    "total_requests": 1250,
    "timeout_count": 3,
    "size_limit_exceeded": 1,
    "slow_requests": 15
  },
  "system": {
    "cpu_percent": 25.6,
    "memory_percent": 68.2,
    "disk_percent": 45.1
  }
}
```

### **헬스체크 활용 방법**

#### **1. 로드 밸런서 연동**
```bash
# Nginx upstream 헬스체크 설정 예시
upstream backend {
    server 127.0.0.1:8000 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8001 max_fails=3 fail_timeout=30s;
}

server {
    location /healthz {
        proxy_pass http://backend;
        access_log off;
    }
}
```

#### **2. 모니터링 시스템 연동**
```bash
# Prometheus 헬스체크 설정
scrape_configs:
  - job_name: 'ai-trading-platform'
    metrics_path: /healthz/detailed
    static_configs:
      - targets: ['localhost:8000']
```

---

## 📦 패킷 명세서

### **패킷명세서.md 기준 네트워크 계층 구조**

#### **1. HTTP 요청 패킷 구조**

##### **기본 요청 헤더**
```http
GET /api/v1/healthz HTTP/1.1
Host: localhost:8000
User-Agent: AI-Trading-Platform/1.0
Accept: application/json
Content-Type: application/json
Content-Length: 0
X-Request-ID: req_1234567890
X-Client-Version: 1.0.0
```

##### **POST 요청 본문 예시**
```http
POST /api/v1/chat HTTP/1.1
Host: localhost:8000
Content-Type: application/json
Content-Length: 156
X-Request-ID: req_1234567891

{
  "message": "테슬라 주식 분석해줘",
  "session_id": "sess_abc123",
  "model": "gpt-4",
  "temperature": 0.7,
  "max_tokens": 1000
}
```

#### **2. HTTP 응답 패킷 구조**

##### **성공 응답 (200 OK)**
```http
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 245
X-Process-Time: 1.234
X-Request-ID: req_1234567890
Server: AI-Trading-Platform/1.0

{
  "status": "success",
  "data": {
    "response": "테슬라 주식 분석 결과...",
    "session_id": "sess_abc123",
    "model_used": "gpt-4",
    "tokens_used": 856
  },
  "timestamp": "2025-01-20T10:30:00Z"
}
```

##### **에러 응답 (4xx/5xx)**
```http
HTTP/1.1 504 Gateway Timeout
Content-Type: text/plain
Content-Length: 45
X-Timeout: 600
X-Request-ID: req_1234567892
Server: AI-Trading-Platform/1.0

Request timeout after 600 seconds
```

#### **3. 에러 페이로드 구조**

##### **표준 에러 응답 스키마**
```json
{
  "error": {
    "code": "TIMEOUT_ERROR",
    "message": "Request timeout after 600 seconds",
    "details": {
      "timeout_seconds": 600,
      "request_path": "/api/v1/chat",
      "request_method": "POST"
    },
    "timestamp": "2025-01-20T10:30:00Z",
    "request_id": "req_1234567892"
  }
}
```

##### **에러 코드 정의 (net_error_code.py)**
```python
class ENetErrorCode(IntEnum):
    SUCCESS = 0
    FATAL = -1
    INVALID_REQUEST = 1001
    ACCESS_DENIED = 1003
    SERVER_ERROR = 5000
    SESSION_EXPIRED = 10000
    REQUEST_TIMEOUT = 10001      # 새로 추가
    REQUEST_TOO_LARGE = 10002    # 새로 추가
    SLOW_REQUEST = 10003         # 새로 추가
```

#### **4. 미들웨어 응답 헤더**

##### **성능 모니터링 헤더**
```http
X-Process-Time: 1.234          # 요청 처리 시간 (초)
X-Request-ID: req_1234567890   # 요청 추적 ID
X-Timeout: 600                 # 설정된 타임아웃 값
X-Max-Size: 52428800           # 최대 요청 크기
X-Slow-Request: true           # 느린 요청 여부
```

##### **보안 헤더**
```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

#### **5. WebSocket 패킷 구조**

##### **WebSocket 연결 요청**
```http
GET /ws/chat HTTP/1.1
Host: localhost:8000
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13
X-Request-ID: ws_req_1234567890
```

##### **WebSocket 메시지 형식**
```json
{
  "type": "chat_message",
  "data": {
    "message": "실시간 주식 분석 요청",
    "session_id": "sess_abc123"
  },
  "timestamp": "2025-01-20T10:30:00Z",
  "message_id": "msg_1234567890"
}
```

---

## 📝 로깅 운영 고려사항

### **운영환경별 로깅 전략**

#### **1. 개발환경 (Development)**
```python
# 개발환경 설정
fastapi_config = FastApiConfig(
    log_all_requests=True,           # 모든 요청 로깅
    enable_slow_request_logging=True,
    slow_request_threshold=1.0,      # 1초 이상을 느린 요청으로 분류
    enable_request_timeout=True,
    request_timeout=300              # 5분 타임아웃
)
```

**특징**:
- **전체 요청 로깅**: 모든 HTTP 요청/응답을 상세히 기록
- **낮은 임계값**: 성능 병목을 빠르게 감지
- **상세한 디버깅**: 개발 과정에서 문제 해결 지원

#### **2. 스테이징환경 (Staging)**
```python
# 스테이징환경 설정
fastapi_config = FastApiConfig(
    log_all_requests=False,          # 느린 요청만 로깅
    enable_slow_request_logging=True,
    slow_request_threshold=2.0,      # 2초 이상을 느린 요청으로 분류
    enable_request_timeout=True,
    request_timeout=600              # 10분 타임아웃
)
```

**특징**:
- **선택적 로깅**: 성능 문제가 있는 요청만 로깅
- **중간 임계값**: 운영 환경과 유사한 조건에서 테스트
- **성능 모니터링**: 실제 사용 패턴 분석

#### **3. 운영환경 (Production)**
```python
# 운영환경 설정
fastapi_config = FastApiConfig(
    log_all_requests=False,          # 느린 요청만 로깅 (성능 최적화)
    enable_slow_request_logging=True,
    slow_request_threshold=5.0,      # 5초 이상을 느린 요청으로 분류
    enable_request_timeout=True,
    request_timeout=600              # 10분 타임아웃
)
```

**특징**:
- **최소 로깅**: 시스템 성능에 영향을 주지 않는 최소한의 로깅
- **높은 임계값**: 실제 성능 문제만 감지
- **리소스 절약**: 로깅으로 인한 오버헤드 최소화

### **로깅 레벨별 운영 전략**

#### **1. DEBUG 레벨 (개발환경)**
```python
# 모든 요청 상세 로깅
Logger.debug(f"📥 요청 수신: {request.method} {request.url.path}")
Logger.debug(f"📋 요청 헤더: {dict(request.headers)}")
Logger.debug(f"📦 요청 본문: {await request.body()}")
Logger.debug(f"📤 응답 생성: {response.status_code}")
```

#### **2. INFO 레벨 (스테이징환경)**
```python
# 중요 이벤트만 로깅
Logger.info(f"🚀 서비스 시작: {service_name}")
Logger.info(f"✅ 미들웨어 설정 완료: {enabled_middlewares}")
Logger.info(f"📊 메트릭 수집: {metrics}")
```

#### **3. WARN 레벨 (운영환경)**
```python
# 경고 상황만 로깅
Logger.warn(f"🐌 느린 요청 감지: {request.method} {request.url.path} - {process_time:.2f}초")
Logger.warn(f"⏰ 요청 타임아웃 발생: {request.method} {request.url.path}")
Logger.warn(f"📦 요청 크기 제한 초과: {content_length} > {max_size} bytes")
```

#### **4. ERROR 레벨 (모든 환경)**
```python
# 에러 상황 상세 로깅
Logger.error(f"❌ 미들웨어 처리 중 오류: {e}")
Logger.error(f"❌ 요청 처리 실패: {request.method} {request.url.path} - {e}")
Logger.error(f"❌ 서비스 초기화 실패: {e}")
```

### **로깅 성능 최적화**

#### **1. 비동기 로깅**
```python
# 로깅이 메인 요청 처리에 영향을 주지 않도록 비동기 처리
async def log_request_async(request: Request, response: Response, process_time: float):
    """비동기 요청 로깅"""
    try:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "process_time": process_time,
            "request_id": request.headers.get("X-Request-ID")
        }
        
        # 백그라운드에서 로깅 처리
        asyncio.create_task(process_log_async(log_data))
        
    except Exception as e:
        # 로깅 실패가 메인 로직에 영향을 주지 않도록
        pass
```

#### **2. 로그 버퍼링 및 배치 처리**
```python
class LogBuffer:
    """로그 버퍼링 및 배치 처리"""
    
    def __init__(self, buffer_size: int = 100, flush_interval: int = 5):
        self.buffer = []
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.last_flush = time.time()
    
    async def add_log(self, log_entry: dict):
        """로그 엔트리 추가"""
        self.buffer.append(log_entry)
        
        # 버퍼가 가득 찼거나 시간 간격이 지났으면 플러시
        if len(self.buffer) >= self.buffer_size or \
           time.time() - self.last_flush >= self.flush_interval:
            await self.flush()
    
    async def flush(self):
        """버퍼의 로그를 일괄 처리"""
        if not self.buffer:
            return
        
        try:
            # 로그를 일괄적으로 파일이나 외부 시스템에 전송
            await self.send_logs_batch(self.buffer)
            self.buffer.clear()
            self.last_flush = time.time()
            
        except Exception as e:
            Logger.error(f"로그 플러시 실패: {e}")
```

#### **3. 로그 로테이션 및 보관**
```python
# 로그 파일 로테이션 설정
import logging.handlers

# 일별 로그 로테이션
daily_handler = logging.handlers.TimedRotatingFileHandler(
    filename='logs/network_service.log',
    when='midnight',
    interval=1,
    backupCount=30  # 30일간 보관
)

# 로그 포맷 설정
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
daily_handler.setFormatter(formatter)
```

### **운영환경별 로깅 체크리스트**

#### **개발환경**
- [ ] `log_all_requests=True` 설정
- [ ] DEBUG 레벨 로깅 활성화
- [ ] 상세한 요청/응답 정보 로깅
- [ ] 느린 요청 임계값 낮게 설정 (1-2초)

#### **스테이징환경**
- [ ] `log_all_requests=False` 설정
- [ ] INFO 레벨 로깅 활성화
- [ ] 느린 요청만 선택적 로깅
- [ ] 중간 임계값 설정 (2-3초)

#### **운영환경**
- [ ] `log_all_requests=False` 설정
- [ ] WARN/ERROR 레벨만 로깅
- [ ] 성능에 영향을 주는 로깅 최소화
- [ ] 높은 임계값 설정 (5초 이상)
- [ ] 로그 로테이션 및 보관 정책 적용

---

## 🔄 Network 서비스 전체 흐름

### **1. 서비스 초기화**
```
1. NetConfig 객체 생성 및 설정 로드
2. FastAPIMiddlewareService.init() 호출
3. 메트릭 초기화 및 서비스 상태 설정
4. Logger를 통한 초기화 완료 로그
```

### **2. 미들웨어 설정 플로우**
```
1. FastAPI 앱 인스턴스에 미들웨어 추가
2. 미들웨어 순서: SlowRequestLogging → RequestSizeLimit → RequestTimeout
3. 각 미들웨어의 활성화/비활성화 설정 적용
4. 설정 완료 로그 및 상태 반환
```

### **3. 요청 처리 플로우**
```
1. HTTP 요청 수신
2. SlowRequestLoggingMiddleware: 요청 시작 시간 기록
3. RequestSizeLimitMiddleware: Content-Length 검증
4. RequestTimeoutMiddleware: 타임아웃 설정 및 처리
5. 실제 요청 처리 (비즈니스 로직)
6. 응답 생성 및 미들웨어 체인 역순 처리
7. SlowRequestLoggingMiddleware: 응답 시간 계산 및 로깅
```

### **4. 에러 처리 플로우**
```
1. 타임아웃 발생: 504 Gateway Timeout 응답
2. 크기 제한 초과: 413 Payload Too Large 응답
3. 기타 에러: 500 Internal Server Error 응답
4. 모든 에러에 대한 상세 로깅 및 메트릭 업데이트
```

### **5. 모니터링 및 메트릭 플로우**
```
1. 실시간 메트릭 수집: 요청 수, 성공/실패, 지연시간
2. 느린 요청 감지: 임계값 초과 시 경고 로그
3. 헬스체크: 서비스 상태 및 메트릭 반환
4. 성능 분석: 응답 시간 분포 및 병목 지점 파악
```

---

## 🔌 미들웨어 체인 구현 상세

### **미들웨어 순서 및 역할**

```python
def setup_middlewares(cls, app, net_config: NetConfig):
    """설정에 따라 미들웨어를 FastAPI 앱에 추가"""
    
    # 1. 느린 요청 로깅 미들웨어 (가장 바깥쪽)
    if enable_slow_logging:
        app.add_middleware(
            SlowRequestLoggingMiddleware,
            threshold=slow_threshold,
            log_all_requests=False
        )
    
    # 2. 요청 크기 제한 미들웨어
    if enable_size_limit:
        app.add_middleware(
            RequestSizeLimitMiddleware,
            max_size=max_size
        )
    
    # 3. 요청 타임아웃 미들웨어 (가장 안쪽)
    if enable_timeout:
        app.add_middleware(
            RequestTimeoutMiddleware,
            timeout_seconds=timeout_seconds
        )
```

**미들웨어 체인 동작 원리**:
- **SlowRequestLoggingMiddleware**: 요청 시작과 종료 시간을 기록하여 처리 시간 계산
- **RequestSizeLimitMiddleware**: 요청 본문 크기를 사전 검증하여 시스템 보호
- **RequestTimeoutMiddleware**: 실제 요청 처리 시간을 제한하여 리소스 보호
- **순서의 중요성**: 바깥쪽에서 안쪽으로 요청이 들어가고, 안쪽에서 바깥쪽으로 응답이 나감

### **타임아웃 처리 메커니즘**

```python
# asyncio.wait_for를 통한 안전한 타임아웃 처리
response = await asyncio.wait_for(
    call_next(request), 
    timeout=self.timeout_seconds
)
```

**타임아웃 처리 특징**:
- **비동기 안전성**: asyncio.wait_for를 통한 안전한 타임아웃 처리
- **LLM API 지원**: 긴 작업 시간을 고려한 600초 기본 타임아웃
- **적절한 에러 응답**: 504 Gateway Timeout과 상세한 타임아웃 정보
- **로깅 및 모니터링**: 타임아웃 발생 시 상세한 로그 기록

### **크기 제한 검증 메커니즘**

```python
# Content-Length 헤더를 통한 사전 크기 검증
content_length = request.headers.get("content-length")

if content_length:
    content_length_int = int(content_length)
    if content_length_int > self.max_size:
        # 크기 제한 초과 시 즉시 413 응답
        return Response(
            content=f"Request too large. Max size: {self.max_size} bytes",
            status_code=413,
            headers={"X-Max-Size": str(self.max_size)}
        )
```

**크기 제한 특징**:
- **사전 검증**: Content-Length 헤더를 통한 요청 처리 전 크기 확인
- **시스템 보호**: 대용량 업로드 공격으로부터 시스템 보호
- **메모리 관리**: 과도한 메모리 사용 방지 및 리소스 제어
- **사용자 친화적**: 명확한 에러 메시지와 제한 정보 제공

---

## 🎯 코드 철학

### **1. 기존 Service 패턴 준수**
- **정적 클래스 구조**: init(), shutdown(), is_initialized() 메서드
- **ServiceContainer 연동**: 기존 서비스 아키텍처와 일관된 구조
- **설정 기반 초기화**: NetConfig를 통한 유연한 설정 관리
- **상태 관리**: 초기화 상태 추적 및 안전한 종료 처리

### **2. 안전한 개선 및 확장**
- **기존 로직 유지**: CLAUDE.md 패턴 준수로 안전한 개선
- **예외 처리 강화**: 모든 단계에서 예외 상황 대응
- **로깅 개선**: 기존 Logger 패턴 활용으로 일관성 유지
- **메트릭 수집**: 성능 모니터링을 위한 상세한 통계 데이터

### **3. 성능과 보안의 균형**
- **미들웨어 체인 최적화**: 성능과 보안을 고려한 배치 순서
- **설정 가능한 임계값**: 환경에 따른 유연한 설정 조정
- **리소스 제어**: 타임아웃과 크기 제한을 통한 시스템 보호
- **압축 최적화**: GZIP 압축을 통한 대역폭 절약

### **4. 개발자 경험 향상**
- **상세한 로깅**: 디버깅 및 문제 해결을 위한 풍부한 정보
- **헬스체크**: 서비스 상태 모니터링 및 운영 지원
- **메트릭 API**: 성능 분석을 위한 실시간 통계 데이터
- **설정 검증**: Pydantic을 통한 설정 유효성 검증

---

## 🚀 개선할 점

### **1. 성능 최적화**
- [ ] **미들웨어 캐싱**: 자주 사용되는 설정 및 결과 캐싱
- [ ] **비동기 처리**: 미들웨어 내부 작업의 비동기 처리 최적화
- [ ] **메모리 최적화**: 대용량 요청 처리 시 메모리 사용량 최적화

### **2. 기능 확장**
- [ ] **Rate Limiting**: IP 기반 요청 제한 및 DDoS 방어
- [ ] **CORS 관리**: Cross-Origin Resource Sharing 설정 및 관리
- [ ] **인증 미들웨어**: JWT 토큰 검증 및 권한 관리
- [ ] **로드 밸런싱**: 다중 서버 환경에서의 요청 분산

### **3. 보안 강화**
- [ ] **입력 검증**: 요청 데이터의 유효성 검증 강화
- [ ] **SQL Injection 방지**: 데이터베이스 쿼리 보안 강화
- [ ] **XSS 방지**: Cross-Site Scripting 공격 방어
- [ ] **CSRF 보호**: Cross-Site Request Forgery 방어

### **4. 모니터링 및 관측성**
- [ ] **Prometheus 메트릭**: 표준 메트릭 형식으로 내보내기
- [ ] **분산 추적**: OpenTelemetry를 통한 요청 추적
- [ ] **알림 시스템**: 성능 저하 및 에러 발생 시 자동 알림
- [ ] **대시보드**: 실시간 성능 모니터링 대시보드

### **5. 테스트 및 품질**
- [ ] **단위 테스트**: 각 미들웨어별 단위 테스트 작성
- [ ] **통합 테스트**: 전체 미들웨어 체인 통합 테스트
- [ ] **성능 테스트**: 부하 테스트 및 성능 벤치마크
- [ ] **보안 테스트**: 보안 취약점 검사 및 테스트

---

## 🛠️ 개발 환경 설정

### **환경 변수**
```bash
# .env
APP_ENV=DEVELOPMENT
LOG_LEVEL=DEBUG
HOST=0.0.0.0
PORT=8000
REQUEST_TIMEOUT=600
MAX_REQUEST_SIZE=52428800
SLOW_REQUEST_THRESHOLD=3.0
```

### **의존성 설치**
```bash
# requirements.txt 기반 설치
pip install -r requirements.txt

# 또는 개별 설치
pip install fastapi starlette pydantic asyncio
```

### **FastAPI 앱 설정 예시**
```python
from fastapi import FastAPI
from service.net.net_config import NetConfig, FastApiConfig
from service.net.fastapi_middleware import FastAPIMiddlewareService

# FastAPI 앱 생성
app = FastAPI(title="AI Trading Platform API")

# 네트워크 설정
fastapi_config = FastApiConfig(
    request_timeout=600,
    slow_request_threshold=3.0,
    max_request_size=52428800,
    enable_request_timeout=True,
    enable_size_limit=True,
    enable_slow_request_logging=True,
    enable_gzip=True
)

net_config = NetConfig(
    host="0.0.0.0",
    port=8000,
    fastApiConfig=fastapi_config
)

# 미들웨어 서비스 초기화
FastAPIMiddlewareService.init(net_config)

# 미들웨어 설정
FastAPIMiddlewareService.setup_middlewares(app, net_config)

# 라우터 등록
# app.include_router(...)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=net_config.host, port=net_config.port)
```

---

## 📚 추가 리소스

- **FastAPI 문서**: https://fastapi.tiangolo.com/
- **Starlette 문서**: https://www.starlette.io/
- **ASGI 문서**: https://asgi.readthedocs.io/
- **Pydantic 문서**: https://pydantic-docs.helpmanual.io/
- **asyncio 문서**: https://docs.python.org/3/library/asyncio.html

---

> **문서 버전**: v1.1 (헬스체크 엔드포인트, 패킷 명세서, 로깅 운영 고려사항 추가)
> **최종 업데이트**: 2025년 1월  
> **담당자**: Network Service Development Team
