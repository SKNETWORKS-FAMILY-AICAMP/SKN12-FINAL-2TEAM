# AWS 서비스 설정 가이드 (S3, OpenSearch, Bedrock)

이 문서는 Windows Conda 환경에서 Python 3.11을 사용하여 AWS S3, OpenSearch, Bedrock 서비스를 처음부터 설정하는 방법을 단계별로 안내합니다.

## 목차
1. [사전 준비사항](#1-사전-준비사항)
2. [AWS 계정 및 IAM 설정](#2-aws-계정-및-iam-설정)
3. [Windows Conda 환경 설정 (Python 3.11)](#3-windows-conda-환경-설정-python-311)
4. [AWS S3 설정](#4-aws-s3-설정)
5. [AWS OpenSearch 설정](#5-aws-opensearch-설정)
6. [AWS Bedrock 설정](#6-aws-bedrock-설정)
7. [로컬 환경 연결 테스트](#7-로컬-환경-연결-테스트)
8. [Config 파일 업데이트](#8-config-파일-업데이트)
9. [base_server 실행 가이드](#9-base_server-실행-가이드)
10. [서비스 구조 및 아키텍처](#10-서비스-구조-및-아키텍처)

---

## 1. 사전 준비사항

### 필요한 것들
- AWS 계정 (없다면 https://aws.amazon.com 에서 생성)
- 신용카드 (AWS 계정 생성 시 필요)
- Windows PC with Anaconda 설치
- 인터넷 연결

### 예상 비용
- S3: 저장 용량과 요청 수에 따라 과금 (프리티어: 5GB/월 무료)
- OpenSearch: 인스턴스 타입에 따라 과금 (최소 t3.small.search 약 $25/월)
- Bedrock: 모델 사용량에 따라 과금 (입출력 토큰당 과금)

---

## 2. AWS 계정 및 IAM 설정

### Step 1: AWS 계정 생성
1. https://aws.amazon.com 접속
2. "AWS 계정 생성" 클릭
3. 이메일, 비밀번호 입력
4. 계정 유형 선택 (개인/비즈니스)
5. 결제 정보 입력
6. 본인 인증 완료

### Step 2: Root 계정으로 로그인
1. AWS Management Console 접속: https://console.aws.amazon.com
2. Root 사용자로 로그인
3. 우측 상단 리전을 "아시아 태평양(서울) ap-northeast-2"로 변경

### Step 3: IAM 사용자 생성
1. AWS Console에서 "IAM" 서비스 검색
2. 좌측 메뉴에서 "사용자" → "사용자 추가" 클릭
3. 사용자 이름 입력: `finance-app-user`
4. AWS 자격 증명 유형 선택:
   - ✅ 액세스 키 - 프로그래밍 방식 액세스
5. 다음: 권한 설정
6. "기존 정책 직접 연결" 선택 후 아래 정책들 검색하여 체크:
   - `AmazonS3FullAccess`
   - `AmazonOpenSearchServiceFullAccess`
   - `AmazonBedrockFullAccess`
7. 다음 → 태그 추가 (선택사항) → 다음 → 검토
8. "사용자 만들기" 클릭
9. **중요**: Access Key ID와 Secret Access Key를 안전한 곳에 저장
   - CSV 다운로드 권장
   - 이 화면을 벗어나면 Secret Key를 다시 볼 수 없음

---

## 3. Windows Conda 환경 설정 (Python 3.11)

### Step 1: Anaconda Prompt 실행
```powershell
# Windows 시작 메뉴에서 "Anaconda Prompt" 검색하여 실행
# 관리자 권한으로 실행 권장
```

### Step 2: 가상환경 생성 및 활성화
```powershell
# Python 3.11 가상환경 생성
conda create -n aws-finance python=3.11 -y

# 가상환경 활성화
conda activate aws-finance
```

### Step 3: 필요한 패키지 설치 (Python 3.11 호환)

⚠️ **패키지 버전 호환성 중요!**
- boto3, botocore, awscli 간 버전 호환성 필수
- 의존성 충돌 방지를 위해 검증된 버전 조합 사용

```powershell
# 1. 기존 AWS 관련 패키지 완전 제거 (만약 설치되어 있다면)
pip uninstall boto3 botocore awscli aiobotocore aioboto3 s3transfer -y

# 2. pip 업그레이드 (Windows Conda 환경)
python -m pip install --upgrade pip

# 3. AWS 기본 패키지 설치 (호환성 확인된 버전)
pip install boto3==1.34.106 botocore==1.34.106 s3transfer==0.10.0

# 4. 비동기 AWS 패키지 설치 (botocore 버전 호환성 확인)
# aiobotocore 2.13.0은 botocore<1.34.107 을 요구하므로 버전 조정
pip install aiobotocore==2.13.0 aioboto3==13.0.0

# 5. AWS CLI 설치 (선택사항 - 강력 추천: 설치하지 마세요!)
# AWS CLI는 botocore 버전을 강제로 업그레이드하여 충돌을 일으킵니다
# 필요한 경우 별도 가상환경에서 사용하세요
# pip install awscli

# 6. OpenSearch 클라이언트 설치
pip install opensearch-py==2.6.0
pip install requests-aws4auth==1.3.0

# 7. 기타 필요한 패키지
pip install python-dotenv
pip install pydantic==2.5.0
pip install fastapi==0.104.0
pip install uvicorn==0.24.0
pip install sqlalchemy==2.0.25
pip install asyncio-mysql==0.2.0
```

### Step 3-1: 의존성 충돌 해결 (이미 설치했다면)
```powershell
# 현재 설치된 패키지 확인 (Windows PowerShell)
pip list | findstr "boto aws"

# 충돌하는 패키지들 완전 제거
pip uninstall boto3 botocore awscli aiobotocore aioboto3 s3transfer -y

# 캐시 정리
pip cache purge

# pip 업그레이드 (Windows Conda 환경)
python -m pip install --upgrade pip

# Python 3.11 호환 버전으로 재설치 (호환성 확인된 버전)
pip install boto3==1.34.106 botocore==1.34.106 s3transfer==0.10.0
pip install aiobotocore==2.13.0 aioboto3==13.0.0
# AWS CLI는 botocore 버전을 강제 업그레이드하므로 설치하지 마세요!
# 필요한 경우 별도 가상환경에서 사용
```

### Step 3-2: 설치 확인
```powershell
# 설치된 패키지 버전 확인
pip show boto3 botocore aiobotocore

# 의존성 충돌 확인 (중요!)
pip check

# 성공적인 설치 확인 예시:
# boto3: 1.34.106
# botocore: 1.34.106  
# aiobotocore: 2.13.0 (botocore<1.34.107 요구)
# 의존성 충돌 없음: "No broken requirements found."

# AWS CLI 설치 여부 확인 (설치되어 있으면 안됨!)
pip show awscli
# 결과: "Package(s) not found: awscli" (정상)
```

### Step 4: AWS 자격 증명 설정

#### ✅ Config 파일에 AWS 키 설정 (권장)
base_server는 config 파일에서 AWS 키를 직접 설정할 수 있습니다:

```json
// base_web_server-config.json
{
  "storageConfig": {
    "aws_access_key_id": "YOUR_ACCESS_KEY_ID",
    "aws_secret_access_key": "YOUR_SECRET_ACCESS_KEY"
  },
  "vectordbConfig": {
    "aws_access_key_id": "YOUR_ACCESS_KEY_ID", 
    "aws_secret_access_key": "YOUR_SECRET_ACCESS_KEY"
  }
}
```

**IAM에서 받은 실제 키를 config 파일에 입력하세요.**

### Step 5: 설정 확인
```powershell
# Python 코드로 확인 (권장)
python -c "import boto3; print(boto3.client('sts').get_caller_identity())"

# 정상적으로 설정되면 계정 정보가 출력됨
# {
#     "UserId": "AIDACKCEVSQ6C2EXAMPLE",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/finance-app-user"
# }
```

---

## 4. AWS S3 설정

### Step 1: S3 버킷 생성 (AWS Console)
1. AWS Console에서 "S3" 서비스 검색
2. "버킷 만들기" 클릭
3. 버킷 설정:
   - **버킷 이름**: `finance-app-bucket-[랜덤숫자]` (전 세계적으로 고유해야 함)
   - **AWS 리전**: 아시아 태평양(서울) ap-northeast-2
   - **객체 소유권**: ACL 비활성화됨(권장)
   - **퍼블릭 액세스 차단**: 모든 퍼블릭 액세스 차단 (기본값 유지)
   - **버킷 버전 관리**: 비활성화 (선택사항)
   - **암호화**: 활성화 (SSE-S3 사용)
4. "버킷 만들기" 클릭

### Step 2: 버킷 정책 설정 (선택사항)
1. 생성된 버킷 클릭
2. "권한" 탭 → "버킷 정책" 편집
3. 필요한 경우 CORS 설정 추가:
```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
        "AllowedOrigins": ["*"],
        "ExposeHeaders": [],
        "MaxAgeSeconds": 3000
    }
]
```

### Step 3: S3 연결 테스트 (로컬)
```python
# test_s3_connection.py
import boto3
from botocore.exceptions import ClientError

def test_s3_connection():
    # S3 클라이언트 생성
    s3 = boto3.client('s3', region_name='ap-northeast-2')
    
    try:
        # 버킷 목록 조회
        response = s3.list_buckets()
        print("S3 연결 성공!")
        print("버킷 목록:")
        for bucket in response['Buckets']:
            print(f"  - {bucket['Name']}")
        
        # 테스트 파일 업로드
        bucket_name = 'finance-app-bucket-[여기에 실제 번호]'
        s3.put_object(
            Bucket=bucket_name,
            Key='test/hello.txt',
            Body=b'Hello from S3!'
        )
        print(f"\n테스트 파일 업로드 성공: {bucket_name}/test/hello.txt")
        
    except ClientError as e:
        print(f"S3 연결 실패: {e}")

if __name__ == "__main__":
    test_s3_connection()
```

---

## 5. AWS OpenSearch 설정

### 🔐 **추천 설정: 마스터 사용자 인증 (보안 강화)**

**선택된 방식: 마스터 사용자 인증**
- 세분화된 액세스 제어: ✅ 활성화
- 마스터 사용자/암호 방식 사용
- 자동 암호화 적용 (HTTPS, 노드간, 저장시)
- Config 파일: username/password 입력 필요

### Step 1: OpenSearch 도메인 생성 (AWS Console)
1. AWS Console에서 "OpenSearch Service" 검색
2. "도메인 생성" 클릭
3. 도메인 설정:
   - **도메인 이름**: `finance-opensearch-v2` (기존 이름이 사용불가하므로 새 이름 사용)
   - **도메인 생성 방법**: 표준 생성
   - **템플릿**: 개발/테스트
   - **배포 유형**: 단일 노드 도메인 (개발용)
   - **버전**: OpenSearch 2.11 (또는 최신 버전)

4. 데이터 노드:
   - **인스턴스 유형**: t3.small.search (개발용)
   - **노드 수**: 1
   - **스토리지**: EBS
   - **EBS 볼륨 유형**: GP3
   - **EBS 스토리지 크기**: 10 GB

5. 네트워크 및 보안:
   - **네트워크**: 퍼블릭 액세스
   - **세분화된 액세스 제어**: ✅ **활성화** 
   - **마스터 사용자 생성**: 
     - 마스터 사용자 이름: `admin`
     - 마스터 암호: `FinanceApp2024!` (강력한 암호)

6. 암호화 설정:
   **⚠️ 세분화된 액세스 제어 활성화 시 필수 설정:**
   - **HTTPS 필수**: ✅ 활성화 (자동 설정됨)
   - **노드 간 암호화**: ✅ 활성화 (자동 설정됨)
   - **저장 데이터 암호화**: ✅ 활성화 (자동 설정됨)
   - **AWS KMS 키**: "AWS 소유 키 사용" 선택 (권장)
   
   **주의**: 이 암호화 설정들은 활성화 후 비활성화할 수 없습니다.

7. 액세스 정책 설정:

**마스터 사용자 인증용 도메인 액세스 정책:**
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "AWS": "*"
    },
    "Action": "es:*",
    "Resource": "arn:aws:es:ap-northeast-2:052533586596:domain/finance-opensearch-v2/*"
  }]
}
```

8. "생성" 클릭 (도메인 생성에 10-15분 소요)

### Step 2: 도메인 생성 완료 후 확인사항

#### 1. 도메인 상태 확인
1. AWS Console > OpenSearch Service > Domains
2. `finance-opensearch-v2` 클릭
3. 다음 사항 확인:
   - **도메인 상태**: Active (녹색)
   - **도메인 엔드포인트**: `https://search-finance-opensearch-v2-xxxxx.ap-northeast-2.es.amazonaws.com`
   - **OpenSearch 버전**: 2.11 이상
   - **세분화된 액세스 제어**: "활성화됨" 상태
   - **마스터 사용자**: `admin` 설정 확인

#### 2. 도메인 엔드포인트 URL 복사
**중요**: 실제 도메인 엔드포인트 URL을 복사해서 config 파일에 입력해야 함!

예시: `https://search-finance-opensearch-v2-abc123def.ap-northeast-2.es.amazonaws.com`

#### 3. OpenSearch Dashboards 접속 테스트
1. 도메인 엔드포인트 URL 복사
2. 브라우저에서 `https://[도메인엔드포인트]/_dashboards` 접속
3. 로그인:
   - 방법 1: 접속 불가 (정상)
   - 방법 2: 마스터 사용자로 로그인 가능

### Step 3: OpenSearch 연결 테스트 (마스터 사용자 인증)
```python
# test_opensearch_connection.py
from opensearchpy import OpenSearch, RequestsHttpConnection

def test_opensearch_connection():
    # OpenSearch 클라이언트 생성 (마스터 사용자 인증)
    host = 'search-finance-opensearch-v2-xxxxx.ap-northeast-2.es.amazonaws.com'  # 실제 엔드포인트로 변경
    client = OpenSearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=('admin', 'FinanceApp2024!'),  # 마스터 사용자 인증
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )
    
    try:
        # 클러스터 정보 확인
        info = client.info()
        print("OpenSearch 연결 성공!")
        print(f"클러스터 이름: {info['cluster_name']}")
        print(f"버전: {info['version']['number']}")
        
        # 인덱스 생성 테스트
        index_name = 'test-index'
        if not client.indices.exists(index=index_name):
            client.indices.create(index=index_name)
            print(f"\n인덱스 생성 성공: {index_name}")
        
        # 문서 추가 테스트
        doc = {
            'title': 'Test Document',
            'content': 'This is a test document for OpenSearch'
        }
        response = client.index(
            index=index_name,
            body=doc
        )
        print(f"문서 추가 성공: {response['_id']}")
        
    except Exception as e:
        print(f"OpenSearch 연결 실패: {e}")

if __name__ == "__main__":
    test_opensearch_connection()
```

### Step 4: 마스터 사용자 인증 확인

#### 설정 확인사항:

1. **도메인 설정 확인**
   - 세분화된 액세스 제어: ✅ "활성화됨" 상태
   - 마스터 사용자: `admin` 설정 확인
   - 도메인 액세스 정책: Principal "*" 설정

2. **Config 파일 확인**
   ```json
   "username": "admin",              // 마스터 사용자명
   "password": "FinanceApp2024!",    // 마스터 암호
   "aws_access_key_id": "",         // 비어있어야 함!
   "aws_secret_access_key": "",     // 비어있어야 함!
   ```

3. **마스터 사용자 인증 테스트**
   브라우저에서 OpenSearch Dashboards 접속:
   `https://[도메인엔드포인트]/_dashboards`
   - 로그인: `admin` / `FinanceApp2024!`

4. **연결 실패시 확인사항**
   - 도메인 상태가 "Active"인지 확인
   - 실제 도메인 엔드포인트 URL이 config에 올바르게 입력되었는지 확인
   - 마스터 사용자 암호가 정확한지 확인

### Step 3: Config 파일 업데이트

#### 1. 실제 엔드포인트 URL로 교체
다음 파일들에서 `NEW_DOMAIN_ID` 부분을 실제 도메인 ID로 교체:

**파일 목록:**
- `base_server/application/base_web_server/base_web_server-config_local.json`
- `base_server/application/base_web_server/base_web_server-config_debug.json`
- `base_server/application/base_web_server/base_web_server-config.json`

**변경 예시:**
```json
// 변경 전
"hosts": ["https://search-finance-opensearch-v2-NEW_DOMAIN_ID.ap-northeast-2.es.amazonaws.com"]

// 변경 후 (실제 도메인 ID로)
"hosts": ["https://search-finance-opensearch-v2-abc123def.ap-northeast-2.es.amazonaws.com"]
```

#### 2. 마스터 사용자 인증 설정 (이미 적용됨)
```json
"searchConfig": {
  "search_type": "opensearch",
  "hosts": ["https://search-finance-opensearch-v2-[실제도메인ID].ap-northeast-2.es.amazonaws.com"],
  "username": "admin",                    // 마스터 사용자명
  "password": "FinanceApp2024!",          // 마스터 사용자 암호
  "aws_access_key_id": "",               // 비워둠! (마스터 사용자 방식)
  "aws_secret_access_key": "",           // 비워둠! (마스터 사용자 방식)
  "region_name": "ap-northeast-2",
  "use_ssl": true,
  "verify_certs": true,
  "timeout": 30,
  "default_index": "finance_search_local",
  "max_retries": 3,
  "retry_on_timeout": true
}
```

---

## 9. base_server 실행 가이드

### 🚀 **main.py 실행 방법**

**1. 터미널에서 base_server 디렉토리로 이동:**
```bash
cd base_server
```

**2. 서버 실행:**
```bash
python -m application.base_web_server.main --logLevel=Debug --appEnv=LOCAL
```

**3. 로그 확인사항:**
```
[Info] : Storage 서비스 AWS 연결 성공
[Info] : Search 서비스 OpenSearch 연결 성공    # 이제 403 에러 없이 성공해야 함
[Info] : VectorDB 서비스 Bedrock 연결 성공
[Info] : base_web_server 시작 완료
```

### 🔧 **OpenSearch 인증 로직 (main.py에서 자동 처리)**

main.py의 SearchService 초기화에서:
1. **Config 읽기**: username/password가 있으면 마스터 사용자 인증
2. **OpenSearch 클라이언트 생성**: Basic Auth 사용
3. **연결 테스트**: `index_exists` 호출로 연결 확인
4. **결과**: 403 에러 없이 정상 연결

### 📋 **체크리스트**
- ✅ OpenSearch 도메인: `finance-opensearch-v2` 생성 완료
- ✅ 마스터 사용자: `admin` / `FinanceApp2024!` 설정
- ✅ Config 파일: username/password 입력, AWS 키 제거
- ✅ 도메인 엔드포인트: `NEW_DOMAIN_ID`를 실제 ID로 교체
- ✅ 서버 실행: OpenSearch 연결 성공 확인

---

## 6. AWS Bedrock 설정

### Bedrock과 S3 연결 개요
AWS Bedrock은 Knowledge Base 기능을 통해 S3에 저장된 문서들을 직접 사용할 수 있습니다. 이를 통해:
- S3에 저장된 PDF, TXT, DOC 등의 문서를 자동으로 벡터화
- 문서 내용을 기반으로 한 질의응답 (RAG - Retrieval Augmented Generation)
- 실시간 문서 업데이트 및 인덱싱

**리전 참고사항**: 
- S3는 서울 리전(ap-northeast-2) 사용
- Bedrock도 서울 리전(ap-northeast-2) 사용
- 동일 리전 사용으로 데이터 전송비 최소화

### Step 1: Bedrock 활성화
1. AWS Console에서 "Bedrock" 서비스 검색
2. **중요**: Bedrock은 이제 서울 리전(ap-northeast-2)에서도 지원됨
   - 서울 리전(ap-northeast-2) 사용 권장
   - 우측 상단 리전을 "아시아 태평양(서울) ap-northeast-2"로 확인
3. "Get started" 클릭
4. 좌측 메뉴에서 "Model access" 클릭

### Step 2: 모델 액세스 요청
1. "Manage model access" 클릭
2. 사용할 모델 선택:
   - ✅ Amazon Titan Text Embeddings V2
   - ✅ Anthropic Claude 3 Sonnet
   - ✅ Anthropic Claude 3 Haiku
3. "Request model access" 클릭
4. 사용 사례 설명 입력 (선택사항)
5. "Submit" 클릭
6. 대부분의 모델은 즉시 승인되지만, 일부는 검토 시간 필요

### Step 3: OpenSearch Serverless 컬렉션 생성 (옵션 B - 고급 사용자용)

⚠️ **주의**: 대부분의 경우 Step 4-2의 "Quick create" 옵션을 사용하는 것이 더 간단합니다. 
이 단계는 기존 OpenSearch Serverless 컬렉션을 사용하려는 고급 사용자를 위한 옵션입니다.

#### 3-1: OpenSearch Serverless 콘솔에서 컬렉션 생성
1. AWS Console에서 "OpenSearch Service" 검색
2. 좌측 메뉴에서 "Serverless" → "Collections" 클릭
3. "Create collection" 클릭
4. 컬렉션 설정:
   - **Name**: `finance-knowledge-collection`
   - **Type**: `Vector search`
   - **Description**: `Vector collection for Bedrock Knowledge Base`

#### 3-2: 보안 정책 설정
1. **Encryption policy**: `finance-knowledge-encryption`
   ```json
   {
     "Rules": [
       {
         "ResourceType": "collection",
         "Resource": ["collection/finance-knowledge-collection"]
       }
     ],
     "AWSOwnedKey": true
   }
   ```

2. **Network access policy**: `finance-knowledge-network`
   ```json
   [
     {
       "Rules": [
         {
           "ResourceType": "collection",
           "Resource": ["collection/finance-knowledge-collection"]
         },
         {
           "ResourceType": "dashboard",
           "Resource": ["collection/finance-knowledge-collection"]
         }
       ],
       "AllowFromPublic": true
     }
   ]
   ```

3. **Data access policy**: `finance-knowledge-access`
   ```json
   [
     {
       "Rules": [
         {
           "ResourceType": "collection",
           "Resource": ["collection/finance-knowledge-collection"],
           "Permission": [
             "aoss:CreateCollectionItems",
             "aoss:DeleteCollectionItems",
             "aoss:UpdateCollectionItems",
             "aoss:DescribeCollectionItems"
           ]
         },
         {
           "ResourceType": "index",
           "Resource": ["index/finance-knowledge-collection/*"],
           "Permission": [
             "aoss:CreateIndex",
             "aoss:DeleteIndex",
             "aoss:UpdateIndex",
             "aoss:DescribeIndex",
             "aoss:ReadDocument",
             "aoss:WriteDocument"
           ]
         }
       ],
       "Principal": [
         "arn:aws:iam::[계정ID]:user/finance-app-user",
         "arn:aws:iam::[계정ID]:role/AmazonBedrockExecutionRoleForKnowledgeBase_*"
       ]
     }
   ]
   ```

### Step 4: Bedrock Knowledge Base 생성 (S3 연결)

#### 4-1: Knowledge Base용 S3 버킷 준비
```bash
# 문서 저장용 S3 버킷 생성 (도쿄 리전에 생성)
aws s3 mb s3://finance-knowledge-base-bucket --region ap-northeast-1

# 테스트 문서 업로드
echo "This is a test document for knowledge base." > test_document.txt
aws s3 cp test_document.txt s3://finance-knowledge-base-bucket/documents/
```

#### 4-2: Knowledge Base 생성 (AWS Console)

**실제 AWS Console 단계별 가이드**

1. **Bedrock Console 접속**
   - AWS Console → "Bedrock" 서비스 검색
   - 리전을 "아시아 태평양(도쿄) ap-northeast-1"로 변경
   - 좌측 메뉴에서 "Knowledge bases" 클릭
   - **"Create knowledge base"** 버튼 클릭

2. **Knowledge base details (1단계)**
   - **Name**: `finance-knowledge-base`
   - **Description**: `Financial documents knowledge base for investment analysis`
   - **IAM service role**: 
     - 🟢 **Create and use a new service role** (권장)
     - Role name: `AmazonBedrockExecutionRoleForKnowledgeBase_finance` (자동 생성됨)
   - **Tags** (선택사항): 필요시 추가
   - **Next** 클릭

3. **Set up data source (2단계)**
   - **Data source name**: `finance-documents-source`
   - **Description**: `S3 bucket containing financial documents`
   - **Source type**: `S3` (기본 선택됨)
   - **Data source location**:
     - **S3 URI**: `s3://finance-knowledge-base-bucket/documents/`
     - **Browse S3** 버튼으로 버킷 선택 가능
   
   **Chunking and parsing configurations**
   - **Chunking strategy**: `Default chunking` (권장)
     - Max tokens: 300
     - Overlap percentage: 20%
   - **Parsing strategy**: `Foundation model parsing`
   - **Next** 클릭

4. **Select embeddings model (3단계)**
   - **Embeddings model**: `Titan Embeddings G1 - Text v1.2`
   - **Dimensions**: `1536` (자동 설정됨)
   - **Vector encryption**: `AWS owned key` (기본값)
   - **Next** 클릭

5. **Configure vector store (4단계) - 중요한 선택**

   **옵션 A: Quick create a new vector store (권장 - 초보자용)**
   ```
   ✅ Quick create a new vector store
   
   자동 생성되는 항목:
   - Collection name: finance-knowledge-collection (사용자 지정 가능)
   - OpenSearch Serverless 컬렉션
   - 필요한 보안 정책 (Encryption, Network, Data access)
   - 벡터 인덱스 및 매핑 설정
   - IAM 역할 및 권한
   
   장점:
   - 복잡한 설정 없이 한 번에 생성
   - 모든 권한과 정책이 자동으로 설정됨
   - 초보자에게 적합
   - 설정 오류 가능성 최소화
   ```

   **옵션 B: Select an existing vector store (고급 사용자용)**
   ```
   ⚪ Select an existing vector store
   
   필요한 정보:
   - Vector store type: Amazon OpenSearch Serverless
   - Collection ARN: arn:aws:aoss:ap-northeast-1:[계정ID]:collection/[컬렉션ID]
   - Vector index name: bedrock-knowledge-base-default-index
   - Vector field name: bedrock-knowledge-base-default-vector
   - Text field name: AMAZON_BEDROCK_TEXT_CHUNK
   - Metadata field name: AMAZON_BEDROCK_METADATA
   
   ※ 사전에 OpenSearch Serverless 컬렉션과 인덱스 생성 필요
   ```

6. **Review and create (5단계)**
   - 설정 내용 검토
   - **Create knowledge base** 클릭
   - 생성 완료까지 약 5-10분 소요

7. **Knowledge Base ID 확인**
   - 생성 완료 후 Knowledge base details에서 **Knowledge base ID** 복사
   - 예: `ABC123DEF456`
   - 이 ID는 나중에 설정에서 사용됩니다

#### 4-4: 벡터 인덱스 생성 (옵션 B - 기존 컬렉션 사용 시)

기존 OpenSearch Serverless 컬렉션을 사용하는 경우, 벡터 인덱스를 수동으로 생성해야 합니다:

```python
# create_vector_index.py
import boto3
import json
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

def create_vector_index():
    # AWS 자격 증명
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        'ap-northeast-1',
        'aoss',
        session_token=credentials.token
    )
    
    # OpenSearch Serverless 클라이언트
    host = 'https://[컬렉션-엔드포인트].ap-northeast-1.aoss.amazonaws.com'
    client = OpenSearch(
        hosts=[host],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )
    
    # 벡터 인덱스 매핑 정의
    index_mapping = {
        "settings": {
            "index": {
                "knn": True,
                "knn.algo_param.ef_search": 512
            }
        },
        "mappings": {
            "properties": {
                "bedrock-knowledge-base-default-vector": {
                    "type": "knn_vector",
                    "dimension": 1536,
                    "method": {
                        "name": "hnsw",
                        "space_type": "cosinesimil",
                        "engine": "faiss",
                        "parameters": {
                            "ef_construction": 512,
                            "m": 16
                        }
                    }
                },
                "AMAZON_BEDROCK_TEXT_CHUNK": {
                    "type": "text"
                },
                "AMAZON_BEDROCK_METADATA": {
                    "type": "text"
                }
            }
        }
    }
    
    try:
        # 인덱스 생성
        response = client.indices.create(
            index="bedrock-knowledge-base-default-index",
            body=index_mapping
        )
        print(f"벡터 인덱스 생성 성공: {response}")
        return True
    except Exception as e:
        print(f"벡터 인덱스 생성 실패: {e}")
        return False

if __name__ == "__main__":
    create_vector_index()
```

#### 4-3: Data Source 동기화 (문서 인덱싱)

**생성 완료 후 첫 동기화**
1. Knowledge base 생성 완료 후 Knowledge base 상세 페이지로 이동
2. **"Data sources"** 탭 클릭
3. 생성된 data source 선택 (`finance-documents-source`)
4. **"Sync"** 버튼 클릭
5. 동기화 상태 확인:
   - **In Progress**: 동기화 진행 중
   - **Completed**: 동기화 완료
   - **Failed**: 동기화 실패 (오류 메시지 확인)

**동기화 과정**
- S3 버킷의 문서들이 자동으로 청킹(chunking)됨
- 각 청크가 Titan Embeddings 모델로 벡터화됨
- 벡터들이 OpenSearch Serverless에 저장됨
- 첫 동기화: 5-15분 소요 (문서 수에 따라 차이)

**동기화 완료 확인**
- Data source 상태가 **"Ready"**로 변경됨
- **"Ingestion job history"**에서 성공 로그 확인 가능
- 벡터 수와 처리된 문서 수 표시됨

### Step 5: Bedrock Knowledge Base 연결 테스트
```python
# test_bedrock_knowledge_base.py
import boto3
import json

def test_bedrock_knowledge_base():
    # Bedrock Agent Runtime 클라이언트 생성
    bedrock_agent = boto3.client(
        service_name='bedrock-agent-runtime',
        region_name='ap-northeast-1'
    )
    
    # Knowledge Base ID (Console에서 확인)
    knowledge_base_id = "YOUR_KNOWLEDGE_BASE_ID"  # 실제 ID로 변경
    
    try:
        # 1. Knowledge Base 검색 테스트
        search_response = bedrock_agent.retrieve(
            knowledgeBaseId=knowledge_base_id,
            retrievalQuery={
                'text': 'What is in the test document?'
            }
        )
        
        print("Knowledge Base 검색 성공!")
        print(f"검색 결과 수: {len(search_response['retrievalResults'])}")
        
        for i, result in enumerate(search_response['retrievalResults']):
            print(f"\n결과 {i+1}:")
            print(f"점수: {result['score']}")
            print(f"내용: {result['content']['text'][:200]}...")
            print(f"소스: {result['location']['s3Location']['uri']}")
        
        # 2. RAG 기반 질의응답 테스트
        rag_response = bedrock_agent.retrieve_and_generate(
            input={
                'text': 'What information is available in the knowledge base?'
            },
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': knowledge_base_id,
                    'modelArn': 'arn:aws:bedrock:ap-northeast-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0'
                }
            }
        )
        
        print("\n\nRAG 질의응답 성공!")
        print(f"답변: {rag_response['output']['text']}")
        
        # 참조된 문서 출력
        if 'citations' in rag_response:
            print("\n참조 문서:")
            for citation in rag_response['citations']:
                for reference in citation['retrievedReferences']:
                    print(f"- {reference['location']['s3Location']['uri']}")
    
    except Exception as e:
        print(f"Knowledge Base 테스트 실패: {e}")

def test_bedrock_direct_model():
    """직접 모델 호출 테스트"""
    bedrock = boto3.client(
        service_name='bedrock-runtime',
        region_name='ap-northeast-1'
    )
    
    try:
        # 1. 임베딩 테스트 (Titan Embeddings)
        embedding_response = bedrock.invoke_model(
            modelId='amazon.titan-embed-text-v1',
            body=json.dumps({
                "inputText": "Hello, this is a test for embeddings"
            })
        )
        
        embedding_result = json.loads(embedding_response['body'].read())
        print("Titan Embeddings 연결 성공!")
        print(f"임베딩 차원: {len(embedding_result['embedding'])}")
        
        # 2. 텍스트 생성 테스트 (Claude)
        claude_response = bedrock.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 100,
                "messages": [
                    {
                        "role": "user",
                        "content": "What is AWS Bedrock?"
                    }
                ]
            })
        )
        
        claude_result = json.loads(claude_response['body'].read())
        print("\nClaude 연결 성공!")
        print(f"응답: {claude_result['content'][0]['text'][:100]}...")
        
    except Exception as e:
        print(f"Bedrock 연결 실패: {e}")
        print("모델 액세스가 승인되었는지 확인하세요.")

if __name__ == "__main__":
    print("=== Bedrock 직접 모델 테스트 ===")
    test_bedrock_direct_model()
    
    print("\n=== Bedrock Knowledge Base 테스트 ===")
    test_bedrock_knowledge_base()
```

### Step 6: S3 문서 업로드 및 동기화 자동화
```python
# s3_knowledge_base_manager.py
import boto3
import os
from datetime import datetime

class S3KnowledgeBaseManager:
    def __init__(self, bucket_name, knowledge_base_id):
        self.s3_client = boto3.client('s3', region_name='ap-northeast-1')
        self.bedrock_agent = boto3.client('bedrock-agent', region_name='ap-northeast-1')
        self.bucket_name = bucket_name
        self.knowledge_base_id = knowledge_base_id
        self.documents_prefix = "documents/"
    
    def upload_document(self, file_path, s3_key=None):
        """S3에 문서 업로드"""
        if s3_key is None:
            s3_key = self.documents_prefix + os.path.basename(file_path)
        
        try:
            self.s3_client.upload_file(file_path, self.bucket_name, s3_key)
            print(f"문서 업로드 성공: {s3_key}")
            return True
        except Exception as e:
            print(f"문서 업로드 실패: {e}")
            return False
    
    def sync_knowledge_base(self):
        """Knowledge Base 동기화"""
        try:
            response = self.bedrock_agent.start_ingestion_job(
                knowledgeBaseId=self.knowledge_base_id,
                dataSourceId="YOUR_DATA_SOURCE_ID"  # Console에서 확인
            )
            print(f"동기화 시작: {response['ingestionJob']['ingestionJobId']}")
            return response['ingestionJob']['ingestionJobId']
        except Exception as e:
            print(f"동기화 실패: {e}")
            return None
    
    def check_sync_status(self, job_id):
        """동기화 상태 확인"""
        try:
            response = self.bedrock_agent.get_ingestion_job(
                knowledgeBaseId=self.knowledge_base_id,
                dataSourceId="YOUR_DATA_SOURCE_ID",
                ingestionJobId=job_id
            )
            return response['ingestionJob']['status']
        except Exception as e:
            print(f"상태 확인 실패: {e}")
            return None
    
    def upload_and_sync(self, file_path):
        """문서 업로드 후 자동 동기화"""
        if self.upload_document(file_path):
            job_id = self.sync_knowledge_base()
            if job_id:
                print(f"동기화 작업 ID: {job_id}")
                print("동기화 완료까지 5-10분 소요됩니다.")
                return job_id
        return None

# 사용 예제
if __name__ == "__main__":
    manager = S3KnowledgeBaseManager(
        bucket_name="finance-knowledge-base-bucket",
        knowledge_base_id="YOUR_KNOWLEDGE_BASE_ID"
    )
    
    # 문서 업로드 및 동기화
    manager.upload_and_sync("path/to/your/document.pdf")
```

---

## 7. 설정 파일 업데이트 주의사항

### 중요: Config 파일 필드명 변경
AWS SDK(aioboto3) 호환성을 위해 다음 필드명을 사용해야 합니다:
- ~~`aws_region`~~ → `region_name` (모든 AWS 서비스에서 통일)

### OpenSearch 설정 예시
```json
"searchConfig": {
  "search_type": "opensearch",
  "hosts": ["https://search-finance-opensearch-v2-xxxxx.ap-northeast-2.es.amazonaws.com"],
  "username": "",  // IAM 인증 사용시 비워둠
  "password": "",  // IAM 인증 사용시 비워둠
  "aws_access_key_id": "YOUR_ACCESS_KEY",
  "aws_secret_access_key": "YOUR_SECRET_KEY",
  "region_name": "ap-northeast-2",  // aws_region이 아닌 region_name 사용!
  "use_ssl": true,
  "verify_certs": true,
  "timeout": 30,
  "default_index": "finance_search",
  "max_retries": 3,
  "retry_on_timeout": true
}
```

### Bedrock 설정 예시
```json
"vectordbConfig": {
  "vectordb_type": "bedrock",
  "aws_access_key_id": "YOUR_ACCESS_KEY",
  "aws_secret_access_key": "YOUR_SECRET_KEY",
  "region_name": "ap-northeast-2",  // aws_region이 아닌 region_name 사용!
  "embedding_model": "amazon.titan-embed-text-v2:0",  // 버전 번호 포함 필수!
  "text_model": "anthropic.claude-3-haiku-20240307-v1:0",
  "knowledge_base_id": "YOUR_KNOWLEDGE_BASE_ID",
  "timeout": 60,
  "default_top_k": 10,
  "max_retries": 3
}
```

---

## 10. 서비스 구조 및 아키텍처

### base_server 전체 아키텍처 개요
base_server는 **마이크로서비스 아키텍처**를 기반으로 하는 금융 서비스 플랫폼입니다.

#### 주요 아키텍처 특징:
1. **111 패턴**: 모든 서비스가 정적 클래스 싱글톤으로 구현
2. **비동기 처리**: async/await 기반 비동기 프로그래밍
3. **샤딩 지원**: 데이터베이스 분산 처리
4. **모니터링**: 모든 서비스에 Health Check와 메트릭 수집
5. **재시도 로직**: 장애 대응을 위한 자동 재시도
6. **트랜잭션 일관성**: 아웃박스 패턴을 통한 분산 트랜잭션

### main.py 서비스 초기화 순서
base_server의 main.py에서는 다음 순서로 모든 서비스가 초기화됩니다:

```python
# 1. Database Service (MySQL 샤딩)
database_service = DatabaseService(app_config.databaseConfig)
await database_service.init_service()

# 2. Cache Service (Redis)
cache_client_pool = RedisCacheClientPool(...)
CacheService.Init(cache_client_pool)

# 3. External Service (외부 API)
await ExternalService.init(app_config.externalConfig)

# 4. Storage Service (S3)
if StorageService.init(app_config.storageConfig):
    # S3 연결 테스트 자동 실행
    test_result = await StorageService.list_files("test-bucket", "", max_keys=1)

# 5. Search Service (OpenSearch)
if SearchService.init(app_config.searchConfig):
    # OpenSearch 연결 테스트 자동 실행
    test_result = await SearchService.index_exists("test-index")

# 6. VectorDB Service (Bedrock)
if VectorDbService.init(app_config.vectordbConfig):
    # Bedrock 연결 테스트 자동 실행
    test_result = await VectorDbService.embed_text("test connection")

# 7. Lock Service (Redis 분산 락)
if LockService.init(cache_service):
    # 분산락 테스트 자동 실행
    test_token = await LockService.acquire("test_lock", ttl=5, timeout=3)

# 8. Scheduler Service (작업 스케줄러)
if SchedulerService.init(lock_service):
    # 스케줄러 시작
    await SchedulerService.start()

# 9. Queue Service (메시지/이벤트 큐)
if await initialize_queue_service(database_service):
    # 큐 시스템 초기화 완료
    pass

# 10. Template Service (비즈니스 로직)
TemplateService.init(app_config)
```

### 10개 핵심 서비스 상세 설명

#### 1. DatabaseService (MySQL 샤딩)
- **기능**: 글로벌 DB와 샤드 DB 관리
- **특징**: 자동 라우팅, 트랜잭션 지원, 아웃박스 패턴 지원
- **연결**: SQLAlchemy 비동기 엔진 사용

#### 2. CacheService (Redis)
- **기능**: 세션 관리, 캐시 추상화, 메트릭 수집
- **특징**: UserHash, Ranking 객체 제공
- **연결**: Redis 클라이언트 풀 사용

#### 3. ExternalService (외부 API)
- **기능**: 주식, 뉴스, 환율 API 통합 관리
- **특징**: 재시도 로직, 메트릭 수집, Health Check
- **연결**: aiohttp 클라이언트 사용

#### 4. StorageService (S3)
- **기능**: 파일 업로드/다운로드, 사전 서명된 URL
- **특징**: 배치 처리, 멀티파트 업로드
- **연결**: aioboto3을 사용한 비동기 S3 클라이언트

#### 5. SearchService (OpenSearch)
- **기능**: 전문검색, 인덱스 관리, 벌크 처리
- **특징**: 벡터 검색과 키워드 검색 하이브리드 지원
- **연결**: AWS4Auth 또는 마스터 사용자 인증

#### 6. VectorDbService (Bedrock)
- **기능**: 텍스트 임베딩, 유사도 검색, RAG 생성
- **특징**: Knowledge Base 연동, 3개 클라이언트 사용
- **연결**: boto3 bedrock 클라이언트

#### 7. LockService (Redis 분산 락)
- **기능**: 분산 락 관리, 데드락 방지
- **특징**: 락 자동 연장, 컨텍스트 매니저 지원
- **연결**: CacheService 기반

#### 8. SchedulerService (작업 스케줄러)
- **기능**: 주기적 작업 실행, 분산 실행
- **특징**: 크론 표현식 지원, 작업 상태 관리
- **연결**: LockService 연동

#### 9. QueueService (메시지/이벤트 큐)
- **기능**: 비동기 메시지 처리, 이벤트 발행/구독
- **특징**: 아웃박스 패턴, 지연 처리
- **연결**: DatabaseService, CacheService 연동

#### 10. TemplateService (비즈니스 로직)
- **기능**: 10개 도메인 템플릿 관리
- **특징**: Account, Portfolio, Chat, Market 등 통합
- **연결**: 모든 서비스 통합 사용

### 실제 서비스 활용 예시

#### 1. Chat API에서 Bedrock 사용
```python
# /api/chat/message/send 엔드포인트
# 1. 사용자 메시지를 Bedrock Knowledge Base에서 검색
search_result = await VectorDbService.similarity_search(user_message)

# 2. 검색 결과와 함께 Claude에게 질문
response = await VectorDbService.generate_text(
    f"Context: {search_result}\nQuestion: {user_message}"
)
```

#### 2. Portfolio API에서 S3 사용
```python
# /api/portfolio/export 엔드포인트
# 1. 포트폴리오 리포트 생성
report_content = generate_portfolio_report(portfolio_data)

# 2. S3에 업로드
upload_result = await StorageService.upload_file_obj(
    bucket="finance-reports",
    key=f"portfolio/{user_id}/{timestamp}.pdf",
    file_obj=report_content
)

# 3. Presigned URL 생성
download_url = await StorageService.generate_presigned_url(
    bucket="finance-reports",
    key=upload_result["key"],
    expiration=3600
)
```

#### 3. Market API에서 OpenSearch 사용
```python
# /api/market/news/search 엔드포인트
# 1. 뉴스 키워드 검색
search_result = await SearchService.search(
    index="financial_news",
    query={
        "multi_match": {
            "query": search_keyword,
            "fields": ["title", "content", "tags"]
        }
    }
)
```

### Config 파일 구조
모든 서비스는 JSON 설정 파일을 통해 구성됩니다:

```json
{
  "templateConfig": { "appId": "base_server", "env": "production" },
  "databaseConfig": { "type": "mysql", "host": "localhost", "port": 3306 },
  "cacheConfig": { "type": "redis", "host": "localhost", "port": 6379 },
  "externalConfig": { "timeout": 30, "apis": {...} },
  "storageConfig": { "storage_type": "s3", "region_name": "ap-northeast-2" },
  "searchConfig": { "search_type": "opensearch", "region_name": "ap-northeast-2" },
  "vectordbConfig": { "vectordb_type": "bedrock", "region_name": "ap-northeast-2" },
  "llmConfig": { "default_provider": "openai" },
  "netConfig": { "host": "0.0.0.0", "port": 8000 }
}
```

---

## 8. 로컬 환경 연결 테스트

### 통합 테스트 스크립트
```python
# test_all_services.py
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import json

class AWSServiceTester:
    def __init__(self):
        self.session = boto3.Session()
        self.credentials = self.session.get_credentials()
        
    def test_s3(self):
        print("=== S3 테스트 ===")
        try:
            s3 = boto3.client('s3', region_name='ap-northeast-2')
            buckets = s3.list_buckets()
            print(f"✓ S3 연결 성공! 버킷 수: {len(buckets['Buckets'])}")
            return True
        except Exception as e:
            print(f"✗ S3 연결 실패: {e}")
            return False
    
    def test_opensearch(self, endpoint):
        print("\n=== OpenSearch 테스트 ===")
        try:
            awsauth = AWS4Auth(
                self.credentials.access_key,
                self.credentials.secret_key,
                'ap-northeast-2',
                'es',
                session_token=self.credentials.token
            )
            
            client = OpenSearch(
                hosts=[{'host': endpoint, 'port': 443}],
                http_auth=awsauth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection
            )
            
            info = client.info()
            print(f"✓ OpenSearch 연결 성공! 버전: {info['version']['number']}")
            return True
        except Exception as e:
            print(f"✗ OpenSearch 연결 실패: {e}")
            return False
    
    def test_bedrock(self):
        print("\n=== Bedrock 테스트 ===")
        try:
            bedrock = boto3.client(
                service_name='bedrock-runtime',
                region_name='ap-northeast-1'
            )
            
            response = bedrock.invoke_model(
                modelId='amazon.titan-embed-text-v1',
                body=json.dumps({"inputText": "test"})
            )
            
            print("✓ Bedrock 연결 성공!")
            return True
        except Exception as e:
            print(f"✗ Bedrock 연결 실패: {e}")
            return False

if __name__ == "__main__":
    tester = AWSServiceTester()
    
    # 각 서비스 테스트
    s3_ok = tester.test_s3()
    
    # OpenSearch 엔드포인트를 여기에 입력 (서울 리전)
    opensearch_endpoint = "finance-opensearch-v2-xxxxx.ap-northeast-2.es.amazonaws.com"
    opensearch_ok = tester.test_opensearch(opensearch_endpoint)
    
    bedrock_ok = tester.test_bedrock()
    
    # 결과 요약
    print("\n=== 테스트 결과 요약 ===")
    print(f"S3 (서울): {'✓ 성공' if s3_ok else '✗ 실패'}")
    print(f"OpenSearch (서울): {'✓ 성공' if opensearch_ok else '✗ 실패'}")
    print(f"Bedrock (도쿄): {'✓ 성공' if bedrock_ok else '✗ 실패'}")
    print("\n리전 정보:")
    print("- S3, OpenSearch: ap-northeast-2 (서울)")
    print("- Bedrock: ap-northeast-1 (도쿄) - 서울 리전 미지원")
```

---

## 9. Config 파일 업데이트

### base_web_server-config_local.json 수정
```json
{
  "storageConfig": {
    "storage_type": "s3",
    "aws_access_key_id": "YOUR_ACCESS_KEY_ID",
    "aws_secret_access_key": "YOUR_SECRET_ACCESS_KEY",
    "aws_region": "ap-northeast-2",
    "default_bucket": "finance-app-bucket-xxxxx",
    "upload_timeout": 300,
    "download_timeout": 300,
    "max_retries": 3
  },
  "searchConfig": {
    "search_type": "opensearch",
    "hosts": ["https://finance-opensearch-v2-xxxxx.ap-northeast-2.es.amazonaws.com"],
    "username": "",
    "password": "",
    "aws_access_key_id": "YOUR_ACCESS_KEY_ID",
    "aws_secret_access_key": "YOUR_SECRET_ACCESS_KEY",
    "aws_region": "ap-northeast-2",
    "use_ssl": true,
    "verify_certs": true,
    "timeout": 30,
    "default_index": "finance_search_local",
    "max_retries": 3,
    "retry_on_timeout": true
  },
  "vectordbConfig": {
    "vectordb_type": "bedrock",
    "aws_access_key_id": "YOUR_ACCESS_KEY_ID",
    "aws_secret_access_key": "YOUR_SECRET_ACCESS_KEY",
    "aws_region": "ap-northeast-1",
    "embedding_model": "amazon.titan-embed-text-v1",
    "text_model": "anthropic.claude-3-haiku-20240307-v1:0",
    "knowledge_base_id": "",
    "timeout": 60,
    "default_top_k": 10,
    "max_retries": 3
  }
}
```

### 환경 변수 사용 (보안 권장)
`.env` 파일 생성:
```env
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_DEFAULT_REGION=ap-northeast-2
BEDROCK_REGION=ap-northeast-1

S3_BUCKET_NAME=finance-app-bucket-xxxxx
OPENSEARCH_ENDPOINT=finance-opensearch-v2-xxxxx.ap-northeast-2.es.amazonaws.com
BEDROCK_KNOWLEDGE_BASE_ID=your_knowledge_base_id
```

---

## 트러블슈팅

### 일반적인 문제와 해결 방법

1. **패키지 의존성 충돌 (boto3, botocore, awscli, aiobotocore) - Python 3.11**
   ```powershell
   # 증상 1: awscli 1.34.0 requires botocore==1.35.0, but you have botocore 1.34.106
   # 증상 2: aiobotocore 2.13.0 requires botocore<1.34.107, but you have botocore 1.34.118
   
   # 해결: 호환되는 버전으로 재설치
   pip uninstall boto3 botocore awscli aiobotocore aioboto3 s3transfer -y
   pip install boto3==1.34.106 botocore==1.34.106 s3transfer==0.10.0
   pip install aiobotocore==2.13.0 aioboto3==13.0.0
   
   # AWS CLI는 설치하지 마세요! (botocore 버전을 강제로 업그레이드함)
   # 필요한 경우 별도 가상환경에서 사용
   ```

2. **Access Denied 오류**
   - IAM 사용자 권한 확인
   - 정책이 올바르게 연결되었는지 확인
   - AWS 자격 증명이 올바른지 확인 (환경변수 또는 AWS CLI)

3. **Connection Timeout**
   - 보안 그룹 설정 확인 (OpenSearch)
   - 리전 설정이 올바른지 확인
   - VPN이나 프록시 설정 확인

4. **Bedrock Model Not Found**
   - 모델 액세스가 승인되었는지 확인
   - 올바른 리전(ap-northeast-1)을 사용하는지 확인
   - 모델 ID가 정확한지 확인

5. **S3 Bucket Already Exists**
   - 버킷 이름은 전역적으로 고유해야 함
   - 다른 이름으로 재시도

6. **ModuleNotFoundError: No module named 'opensearchpy'**
   ```powershell
   # 올바른 패키지 이름으로 설치
   pip install opensearch-py==2.4.0
   ```

7. **SSL Certificate 에러**
   ```powershell
   # Windows에서 SSL 인증서 문제 시
   pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org <package_name>
   ```

### 비용 관리 팁
1. 개발/테스트 후 리소스 정리
2. OpenSearch는 시간당 과금이므로 사용하지 않을 때는 삭제
3. S3 라이프사이클 정책 설정으로 오래된 객체 자동 삭제
4. **리전 간 데이터 전송비**: S3(서울) ↔ Bedrock(도쿄) 간 데이터 전송 비용 발생
5. CloudWatch로 비용 알림 설정

---

## 다음 단계
1. 프로덕션 환경 설정 시 VPC, 보안 그룹 등 추가 보안 설정
2. CloudFormation이나 Terraform으로 인프라 코드화
3. AWS Systems Manager Parameter Store로 민감한 정보 관리
4. CloudWatch로 모니터링 및 로깅 설정

---

## 참고 자료
- [AWS S3 개발자 가이드](https://docs.aws.amazon.com/s3/index.html)
- [AWS OpenSearch Service 가이드](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/what-is.html)
- [AWS Bedrock 사용 설명서](https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html)
- [Boto3 문서](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)