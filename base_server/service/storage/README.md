# AI Trading Platform — Storage Service

> **개요**: SKN12-FINAL-2TEAM의 AI 트레이딩 플랫폼 백엔드 Storage 서비스입니다. AWS S3를 기반으로 한 클라우드 스토리지 서비스로, 파일 업로드/다운로드, 관리, 사전 서명된 URL 생성 등을 제공하는 정적 클래스 패턴의 시스템입니다.

---

## 🏗️ 프로젝트 구조

### 디렉토리 구조
```
storage/
├── __init__.py                    # 패키지 초기화
├── storage_service.py             # 메인 Storage 서비스 (정적 클래스)
├── storage_config.py              # Storage 설정 및 AWS S3 설정
├── storage_client_pool.py         # Storage 클라이언트 풀 (Session 재사용 패턴)
├── storage_client.py              # Storage 클라이언트 인터페이스
└── s3_storage_client.py           # AWS S3 클라이언트 구현
```

---

## 🔧 핵심 기능

### 1. **Storage 서비스 (StorageService)**
- **정적 클래스 패턴**: 111 패턴으로 서비스 인스턴스 관리
- **초기화 관리**: `init()`, `shutdown()`, `is_initialized()` 메서드
- **클라이언트 풀**: Session 재사용 패턴으로 AWS 연결 효율성 향상
- **비동기 지원**: 모든 파일 작업에 대한 비동기 처리

### 2. **파일 업로드/다운로드**
- **파일 업로드**: 로컬 파일 경로 또는 파일 객체를 통한 업로드
- **파일 다운로드**: S3에서 로컬 파일로 다운로드 또는 파일 객체로 반환
- **메타데이터 지원**: Content-Type, 사용자 정의 메타데이터 설정
- **대용량 파일**: 멀티파트 업로드 지원 (100MB 이상)

### 3. **파일 관리**
- **파일 삭제**: S3에서 파일 완전 삭제
- **파일 목록**: 버킷 내 파일 목록 조회 (접두사 기반 필터링)
- **파일 정보**: 파일 크기, 수정일, 메타데이터 등 상세 정보
- **파일 복사/이동**: 버킷 간 또는 동일 버킷 내 파일 이동

### 4. **고급 기능**
- **사전 서명된 URL**: 직접 업로드/다운로드를 위한 임시 URL 생성
- **메트릭 수집**: 업로드/다운로드 성능 및 성공률 추적
- **연결 상태 관리**: AWS 연결 상태 모니터링 및 자동 복구
- **재시도 로직**: 네트워크 오류 시 자동 재시도 (최대 3회)

---

## 📚 사용된 라이브러리

### **Core AWS Framework**
- **aioboto3**: AWS SDK의 비동기 래퍼
- **boto3**: AWS SDK for Python
- **botocore**: AWS 서비스 클라이언트의 핵심 기능

### **백엔드 & 인프라**
- **asyncio**: 비동기 프로그래밍 및 동시성 처리
- **Pydantic**: 데이터 검증 및 설정 관리
- **contextlib.AsyncExitStack**: 비동기 리소스 관리

### **개발 도구**
- **Python 3.8+**: 메인 프로그래밍 언어
- **typing**: 타입 힌트 및 타입 안전성
- **dataclasses**: 데이터 클래스 정의
- **abc**: 추상 클래스 및 인터페이스 정의
- **service.core.logger.Logger**: 구조화된 로깅 시스템

---

## 🪝 핵심 클래스 및 메서드

### **StorageService - 메인 서비스 클래스**

```python
class StorageService:
    """Storage 서비스 (정적 클래스) - 111 패턴"""
    
    _config: Optional[StorageConfig] = None
    _client_pool: Optional[IStorageClientPool] = None
    _initialized: bool = False
    
    @classmethod
    def init(cls, config: StorageConfig) -> bool:
        """서비스 초기화"""
        # StorageClientPool 생성 및 초기화
    
    @classmethod
    async def shutdown(cls):
        """서비스 종료"""
        # 모든 클라이언트 연결 종료
    
    @classmethod
    def get_client(cls):
        """Storage 클라이언트 가져오기 (동기)"""
        # 클라이언트 풀에서 기존 클라이언트 인스턴스 반환
    
    @classmethod
    async def get_client_async(cls):
        """Storage 클라이언트 가져오기 (비동기)"""
        # 비동기 클라이언트 풀에서 클라이언트 반환
```

**동작 방식**:
- 정적 클래스 패턴으로 서비스 인스턴스 관리
- StorageClientPool을 통한 AWS 연결 풀 관리
- 동기/비동기 클라이언트 제공 (동기 메서드는 기존 인스턴스 반환, 비동기 메서드는 새 클라이언트 생성)

### **StorageClientPool - 클라이언트 풀 관리**

```python
class StorageClientPool(IStorageClientPool):
    """Storage 클라이언트 풀 구현 - Session 재사용 패턴"""
    
    def __init__(self, config):
        self.config = config
        self._session: Optional[aioboto3.Session] = None
        self._s3_client = None
        self._client_instance: Optional[IStorageClient] = None
        self._lock = asyncio.Lock()
        self._initialized = False
        self._exit_stack: Optional[AsyncExitStack] = None
    
    async def _init_session(self):
        """Session 초기화 (한 번만)"""
        # aioboto3 Session 생성 및 재사용
        # Connection Pool 설정 (max_pool_connections=50)
        # AsyncExitStack을 통한 리소스 관리
```

**동작 방식**:
- aioboto3 Session 재사용으로 연결 효율성 향상
- AsyncExitStack을 통한 적절한 리소스 관리
- Connection Pool 설정으로 동시 연결 수 제한

### **S3StorageClient - S3 클라이언트 구현**

```python
class S3StorageClient(IStorageClient):
    """AWS S3 Storage 클라이언트 - Session 재사용 패턴"""
    
    def __init__(self, config, session=None, s3_client=None):
        self.config = config
        self._session = session  # Pool에서 전달받은 session
        self._s3_client = s3_client  # Pool에서 전달받은 client
        self.metrics = S3Metrics()  # 성능 메트릭 수집
        self._connection_healthy = True
        self._max_retries = 3
        self._retry_delay_base = 1.0
    
    async def upload_file(self, bucket: str, key: str, file_path: str, **kwargs):
        """파일 업로드 (향상된 에러 처리 및 메트릭)"""
        # 재시도 로직, 메트릭 수집, 에러 처리
```

**동작 방식**:
- Pool에서 전달받은 session과 client 재사용
- S3Metrics를 통한 성능 모니터링
- 재시도 로직 및 연결 상태 관리

---

## 🌐 API 연동 방식

### **Storage 설정 및 AWS S3 연동**

```python
# storage_config.py
class StorageConfig(BaseModel):
    """Storage 서비스 설정"""
    storage_type: str = "s3"  # s3, gcs, azure 등
    
    # AWS S3 설정
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    region_name: str = "ap-northeast-2"
    aws_session_token: Optional[str] = None
    
    # 기본 버킷
    default_bucket: Optional[str] = None
    
    # 업로드 설정
    upload_timeout: int = 300  # 5분
    download_timeout: int = 300  # 5분
    multipart_threshold: int = 1024 * 1024 * 100  # 100MB
    max_concurrency: int = 10
    
    # 재시도 설정
    max_retries: int = 3
```

### **AWS S3 연동**

```python
# storage_client_pool.py
async def _init_session(self):
    """Session 초기화 (한 번만)"""
    if self.config.storage_type == "s3":
        # aioboto3 Session 생성
        self._session = aioboto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            region_name=region_name
        )
        
        # S3 클라이언트 생성 (Connection Pool 설정)
        boto_config = Config(
            retries={'max_attempts': 3, 'mode': 'adaptive'},
            max_pool_connections=50,  # Connection Pool 크기
            region_name=region_name
        )
        
        self._s3_client = await self._exit_stack.enter_async_context(
            self._session.client('s3', config=boto_config)
        )
```

### **실제 설정 파일 예시**

```json
{
  "storageConfig": {
    "storage_type": "s3",
    "aws_access_key_id": "your_access_key",
    "aws_secret_access_key": "your_secret_key",
    "region_name": "ap-northeast-2",
    "default_bucket": "skn12-finance-storage",
    "upload_timeout": 300,
    "download_timeout": 300,
    "max_retries": 3
  }
}
```

---

## 🔄 Storage 서비스 전체 흐름

### **1. 서비스 초기화**
```
1. StorageService.init(config) 호출
2. StorageConfig 객체 생성 및 검증
3. StorageClientPool 인스턴스 생성
4. aioboto3 Session 초기화 (한 번만)
5. S3 클라이언트 생성 및 Connection Pool 설정
6. 초기화 완료 상태 설정
```

### **2. 파일 업로드 플로우**
```
1. StorageService.upload_file() 호출
2. 클라이언트 풀에서 Storage 클라이언트 인스턴스 가져오기
3. 파일 메타데이터 설정 (Content-Type, 사용자 메타데이터)
4. S3 upload_file API 호출
5. 성공/실패 메트릭 기록
6. 결과 반환 (업로드 시간, 시도 횟수 등)
```

### **3. 파일 다운로드 플로우**
```
1. StorageService.download_file() 호출
2. 클라이언트 풀에서 Storage 클라이언트 인스턴스 가져오기
3. S3 download_file API 호출
4. 로컬 파일로 저장 또는 파일 객체 반환
5. 성공/실패 메트릭 기록
6. 결과 반환 (파일 크기, 다운로드 시간 등)
```

### **4. 파일 관리 플로우**
```
1. StorageService.list_files() 호출
2. S3 list_objects_v2 API 호출
3. 접두사 기반 필터링 적용
4. 파일 목록 및 메타데이터 반환
5. 페이지네이션 지원 (max_keys 파라미터)
```

### **5. 사전 서명된 URL 생성 플로우**
```
1. StorageService.generate_presigned_url() 호출
2. 만료 시간 설정 (기본값: 1시간)
3. S3 generate_presigned_url API 호출
4. 임시 접근 권한이 포함된 URL 반환
5. 클라이언트에서 직접 S3 접근 가능
```

---

## 🔌 파일 작업 구현 상세

### **파일 업로드 확장 가이드**

StorageService는 다양한 형태의 파일 업로드를 지원합니다:

```python
# 1. 로컬 파일 경로를 통한 업로드
result = await StorageService.upload_file(
    bucket="finance-app-bucket",
    key="documents/report.pdf",
    file_path="/tmp/report.pdf",
    extra_args={
        'ContentType': 'application/pdf',
        'Metadata': {
            'user_id': '12345',
            'category': 'financial_report'
        }
    }
)



# 2. 대용량 파일 멀티파트 업로드
# 100MB 이상 파일은 자동으로 멀티파트 업로드
result = await StorageService.upload_file(
    bucket="finance-app-bucket",
    key="videos/presentation.mp4",
    file_path="/tmp/large_video.mp4"
)
```

### **파일 다운로드 및 관리**

```python
# 1. 로컬 파일로 다운로드
result = await StorageService.download_file(
    bucket="finance-app-bucket",
    key="documents/report.pdf",
    file_path="/tmp/downloaded_report.pdf"
)



# 2. 파일 목록 조회
files = await StorageService.list_files(
    bucket="finance-app-bucket",
    prefix="documents/",
    max_keys=100
)

# 3. 파일 정보 조회
file_info = await StorageService.get_file_info(
    bucket="finance-app-bucket",
    key="documents/report.pdf"
)
```

### **고급 파일 작업**

```python
# 사전 서명된 URL 생성
presigned_url = await StorageService.generate_presigned_url(
    bucket="finance-app-bucket",
    key="documents/report.pdf",
    expiration=7200  # 2시간
)
```

---

## 🔬 고급 기능 심층 분석: Session 재사용 패턴

StorageService의 핵심은 **Session 재사용 패턴**을 통한 AWS 연결 효율성 향상입니다.

### **1. 개요**
이 패턴은 **aioboto3 Session**을 한 번 생성하고 재사용하여 AWS S3 연결의 오버헤드를 최소화합니다. 전통적인 방식에서는 매번 새로운 Session을 생성하지만, 이 패턴은 **Connection Pool**과 **AsyncExitStack**을 결합하여 리소스를 효율적으로 관리합니다.

### **2. 핵심 아키텍처 및 데이터 플로우**

#### **2.1 Session 초기화 (한 번만)**
```python
async def _init_session(self):
    """Session 초기화 (한 번만)"""
    if self._initialized:
        return
        
    async with self._lock:
        if self._initialized:
            return
            
        try:
            # AsyncExitStack 생성 (적절한 리소스 관리)
            self._exit_stack = AsyncExitStack()
            
            # aioboto3 Session 생성 (재사용)
            self._session = aioboto3.Session(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_session_token=aws_session_token,
                region_name=region_name
            )
            
            # S3 클라이언트 생성 (Connection Pool 설정)
            boto_config = Config(
                retries={'max_attempts': 3, 'mode': 'adaptive'},
                max_pool_connections=50,  # Connection Pool 크기
                region_name=region_name
            )
            
            # AsyncExitStack을 사용하여 클라이언트 생성 및 관리
            self._s3_client = await self._exit_stack.enter_async_context(
                self._session.client('s3', config=boto_config)
            )
            
            self._initialized = True
            Logger.info(f"S3 Storage Pool initialized with AsyncExitStack for region: {region_name}")
```

#### **2.2 Connection Pool 설정**
```python
# botocore Config를 통한 Connection Pool 설정
boto_config = Config(
    retries={'max_attempts': 3, 'mode': 'adaptive'},  # 재시도 설정
    max_pool_connections=50,  # 최대 동시 연결 수
    region_name=region_name
)
```

**Connection Pool의 장점**:
- **동시 요청 처리**: 최대 50개의 동시 연결 지원
- **연결 재사용**: HTTP Keep-Alive를 통한 연결 재사용
- **성능 향상**: 새로운 TCP 연결 생성 오버헤드 제거

#### **2.3 AsyncExitStack을 통한 리소스 관리**
```python
# AsyncExitStack을 사용하여 클라이언트 생성 및 관리
self._s3_client = await self._exit_stack.enter_async_context(
    self._session.client('s3', config=boto_config)
)

# 서비스 종료 시 모든 리소스 정리
async def close_all(self):
    """모든 클라이언트 종료"""
    if self._exit_stack:
        await self._exit_stack.__aexit__(None, None, None)
        self._exit_stack = None
```

**AsyncExitStack의 장점**:
- **자동 리소스 정리**: 컨텍스트 매니저 자동 정리
- **예외 안전성**: 예외 발생 시에도 리소스 정리 보장
- **복잡한 리소스 관리**: 여러 리소스를 동시에 관리

### **3. 실제 구현된 동작 과정**

#### **3.1 클라이언트 풀 초기화**
```python
# StorageService.init() 호출 시
if StorageService.init(app_config.storageConfig):
    # StorageClientPool 생성
    cls._client_pool = StorageClientPool(config)
    
    # 비동기 초기화 수행
    client = await StorageService.get_client_async()
```

#### **3.2 Session 재사용**
```python
# 매번 새로운 Session을 생성하지 않고 기존 Session 재사용
def new(self) -> IStorageClient:
    """기존 Storage 클라이언트 인스턴스 반환"""
    if not self._initialized:
        raise RuntimeError("StorageClientPool not initialized")
    
    # 기존에 생성된 클라이언트 인스턴스 반환 (새로 생성하지 않음)
    return self._client_instance
```

#### **3.3 연결 상태 모니터링**
```python
# S3StorageClient에서 연결 상태 추적
class S3StorageClient(IStorageClient):
    def __init__(self, config, session=None, s3_client=None):
        self._connection_healthy = True
        self._max_retries = 3
        self._retry_delay_base = 1.0
    
    async def _get_client(self):
        """S3 클라이언트 가져오기"""
        if self._s3_client is None:
            raise RuntimeError("S3 client not initialized by pool")
        return self._s3_client
```

### **4. 성능 최적화 효과**

#### **4.1 연결 오버헤드 감소**
```
전통적인 방식:
요청 → Session 생성 → S3 클라이언트 생성 → API 호출 → 연결 종료
(매번 새로운 TCP 연결, 인증 오버헤드)

Session 재사용 패턴:
초기화 → Session 생성 → S3 클라이언트 생성
요청 → 기존 연결 재사용 → API 호출
(연결 재사용, 인증 정보 캐싱)
```

#### **4.2 동시성 향상**
```python
# Connection Pool을 통한 동시 요청 처리
max_pool_connections=50  # 최대 50개 동시 연결

# 여러 파일을 동시에 업로드 (Connection Pool이 자동으로 관리)
# StorageService.upload_file()을 여러 번 호출하면 자동으로 동시 처리
```

### **5. 에러 처리 및 복구**

#### **5.1 재시도 로직**
```python
async def upload_file(self, bucket: str, key: str, file_path: str, **kwargs):
    """파일 업로드 (향상된 에러 처리 및 메트릭)"""
    for attempt in range(self._max_retries):
        try:
            s3_client = await self._get_client()
            
            await s3_client.upload_file(
                Filename=file_path,
                Bucket=bucket,
                Key=key,
                ExtraArgs=extra_args
            )
            
            # 성공 시 메트릭 기록
            self._connection_healthy = True
            return {"success": True, "attempt": attempt + 1}
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            
            if error_code in ['NoSuchBucket', 'AccessDenied', 'InvalidBucketName']:
                # 재시도해도 해결되지 않는 오류들
                break
            
            if attempt < self._max_retries - 1:
                # 지수 백오프로 재시도
                delay = self._retry_delay_base * (2 ** attempt)
                await asyncio.sleep(delay)
```

#### **5.2 연결 상태 모니터링**
```python
# 메트릭을 통한 성능 모니터링
@dataclass
class S3Metrics:
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    total_upload_time: float = 0.0
    total_download_time: float = 0.0
    bytes_uploaded: int = 0
    bytes_downloaded: int = 0
    last_operation_time: Optional[float] = None
```

### **6. 실제 사용 사례**

#### **6.1 Crawler Template에서의 활용**
```python
# template/crawler/crawler_template_impl.py
v_upload_result = await StorageService.upload_file(
    bucket=v_s3_bucket,
    key=v_s3_key,
    file_path=v_temp_file,
    extra_args={
        'ContentType': 'application/json',
        'Metadata': {
            'task_id': p_task_id,
            'content_type': 'yahoo_finance_news',
            'document_count': str(len(v_json_documents))
        }
    }
)
```

#### **6.2 Knowledge Base 동기화**
```python
# S3 업로드 후 VectorDB 동기화
if v_upload_result.get('success', False):
    # VectorDbService를 통한 Knowledge Base 동기화
    v_ingestion_result = await VectorDbService.start_ingestion_job(v_data_source_id)
```

### **7. 핵심 특징 및 장점**

#### **7.1 효율적인 리소스 관리**
- **Session 재사용**: AWS 인증 및 연결 정보 재사용
- **Connection Pool**: 동시 연결 수 제한 및 관리
- **AsyncExitStack**: 자동 리소스 정리 및 예외 안전성

#### **7.2 성능 최적화**
- **연결 오버헤드 감소**: TCP 연결 재사용
- **동시성 향상**: 최대 50개 동시 연결 지원
- **메모리 효율성**: 불필요한 객체 생성 방지

#### **7.3 안정성 및 신뢰성**
- **재시도 로직**: 네트워크 오류 시 자동 재시도
- **연결 상태 모니터링**: 실시간 연결 상태 추적
- **메트릭 수집**: 성능 및 성공률 모니터링

이 패턴은 단순한 파일 업로드/다운로드를 넘어서 **AWS S3와의 효율적인 연결 관리**, **동시성 처리**, **리소스 최적화**를 제공하는 고도화된 클라우드 스토리지 시스템입니다.

---

### **의존성 설치**
```bash
# aioboto3 및 관련 패키지 설치
pip install aioboto3 boto3 botocore

# 또는 requirements.txt 기반 설치
pip install -r requirements.txt
```

### **AWS 설정**
```bash
# AWS CLI 설정
aws configure

# 또는 환경 변수 설정
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
export AWS_DEFAULT_REGION="ap-northeast-2"
```

---

## 📚 추가 리소스

- **aioboto3 문서**: https://aioboto3.readthedocs.io/
- **boto3 문서**: https://boto3.amazonaws.com/v1/documentation/api/latest/index.html
- **AWS S3 문서**: https://docs.aws.amazon.com/s3/

---
