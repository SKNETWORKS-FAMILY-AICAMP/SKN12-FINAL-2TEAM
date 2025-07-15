# AWS 서비스 설정 가이드 (S3, OpenSearch, Bedrock)

이 문서는 Windows Conda 환경에서 AWS S3, OpenSearch, Bedrock 서비스를 처음부터 설정하는 방법을 단계별로 안내합니다.

## 목차
1. [사전 준비사항](#1-사전-준비사항)
2. [AWS 계정 및 IAM 설정](#2-aws-계정-및-iam-설정)
3. [Windows Conda 환경 설정](#3-windows-conda-환경-설정)
4. [AWS S3 설정](#4-aws-s3-설정)
5. [AWS OpenSearch 설정](#5-aws-opensearch-설정)
6. [AWS Bedrock 설정](#6-aws-bedrock-설정)
7. [로컬 환경 연결 테스트](#7-로컬-환경-연결-테스트)
8. [Config 파일 업데이트](#8-config-파일-업데이트)

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

## 3. Windows Conda 환경 설정

### Step 1: Anaconda Prompt 실행
```powershell
# Windows 시작 메뉴에서 "Anaconda Prompt" 검색하여 실행
# 관리자 권한으로 실행 권장
```

### Step 2: 가상환경 생성 및 활성화
```powershell
# Python 3.9 가상환경 생성
conda create -n aws-finance python=3.9 -y

# 가상환경 활성화
conda activate aws-finance
```

### Step 3: 필요한 패키지 설치

⚠️ **의존성 충돌 방지를 위해 순서대로 설치하세요**

```powershell
# 1. 기존 AWS 관련 패키지 완전 제거 (만약 설치되어 있다면)
pip uninstall boto3 botocore awscli aiobotocore aioboto3 s3transfer -y

# 2. pip 업그레이드 (Windows Conda 환경)
python -m pip install --upgrade pip

# 3. AWS 패키지를 호환되는 버전으로 설치
pip install boto3==1.34.0 botocore==1.34.0 s3transfer==0.9.0

# 4. AWS CLI 설치 (boto3와 호환되는 버전)
pip install awscli==1.32.0

# 5. 비동기 AWS 패키지 설치 (필요한 경우)
pip install aiobotocore==2.11.2 aioboto3==12.3.0

# 6. OpenSearch 클라이언트 설치
pip install opensearch-py==2.4.0
pip install requests-aws4auth==1.3.0

# 7. 기타 필요한 패키지
pip install python-dotenv
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

# 호환되는 버전으로 재설치
pip install boto3==1.34.0 botocore==1.34.0 s3transfer==0.9.0 awscli==1.32.0
pip install aiobotocore==2.11.2 aioboto3==12.3.0
```

### Step 3-2: 설치 확인
```powershell
# 설치된 패키지 버전 확인
pip show boto3 botocore awscli

# 의존성 충돌 확인
pip check
```

### Step 4: AWS CLI 설정
```powershell
# AWS 자격 증명 설정
aws configure

# 입력 프롬프트가 나타나면 다음 정보 입력:
# AWS Access Key ID [None]: [IAM에서 받은 Access Key ID]
# AWS Secret Access Key [None]: [IAM에서 받은 Secret Access Key]
# Default region name [None]: ap-northeast-2
# Default output format [None]: json
```

### Step 5: 설정 확인
```powershell
# 설정 확인
aws sts get-caller-identity

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

### Step 1: OpenSearch 도메인 생성 (AWS Console)
1. AWS Console에서 "OpenSearch Service" 검색
2. "도메인 생성" 클릭
3. 도메인 설정:
   - **도메인 이름**: `finance-search-domain`
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

5. 네트워크:
   - **네트워크**: 퍼블릭 액세스
   - **세분화된 액세스 제어**: 활성화
   - **마스터 사용자 생성**: 
     - 마스터 사용자 이름: `admin`
     - 마스터 암호: 강력한 암호 설정

6. 액세스 정책:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::[계정ID]:user/finance-app-user"
      },
      "Action": "es:*",
      "Resource": "arn:aws:es:ap-northeast-2:[계정ID]:domain/finance-search-domain/*"
    }
  ]
}
```

7. "생성" 클릭 (도메인 생성에 10-15분 소요)

### Step 2: OpenSearch 엔드포인트 확인
1. 도메인 생성 완료 후 도메인 클릭
2. "일반 정보"에서 도메인 엔드포인트 확인
   - 예: `https://finance-search-domain-xxxxx.ap-northeast-2.es.amazonaws.com`

### Step 3: OpenSearch 연결 테스트
```python
# test_opensearch_connection.py
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3

def test_opensearch_connection():
    # AWS 자격 증명
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        'ap-northeast-2',
        'es',
        session_token=credentials.token
    )
    
    # OpenSearch 클라이언트 생성
    host = 'finance-search-domain-xxxxx.ap-northeast-2.es.amazonaws.com'  # 실제 엔드포인트로 변경
    client = OpenSearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=awsauth,
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

---

## 6. AWS Bedrock 설정

### Bedrock과 S3 연결 개요
AWS Bedrock은 Knowledge Base 기능을 통해 S3에 저장된 문서들을 직접 사용할 수 있습니다. 이를 통해:
- S3에 저장된 PDF, TXT, DOC 등의 문서를 자동으로 벡터화
- 문서 내용을 기반으로 한 질의응답 (RAG - Retrieval Augmented Generation)
- 실시간 문서 업데이트 및 인덱싱

### Step 1: Bedrock 활성화
1. AWS Console에서 "Bedrock" 서비스 검색
2. **중요**: Bedrock은 일부 리전에서만 사용 가능
   - 우측 상단 리전을 "미국 동부(버지니아 북부) us-east-1"로 변경
3. "Get started" 클릭
4. 좌측 메뉴에서 "Model access" 클릭

### Step 2: 모델 액세스 요청
1. "Manage model access" 클릭
2. 사용할 모델 선택:
   - ✅ Amazon Titan Embeddings G1 - Text
   - ✅ Anthropic Claude 3 Sonnet
   - ✅ Anthropic Claude 3 Haiku
3. "Request model access" 클릭
4. 사용 사례 설명 입력 (선택사항)
5. "Submit" 클릭
6. 대부분의 모델은 즉시 승인되지만, 일부는 검토 시간 필요

### Step 3: Bedrock Knowledge Base 생성 (S3 연결)

#### 3-1: Knowledge Base용 S3 버킷 준비
```bash
# 문서 저장용 S3 버킷 생성 (이미 생성했다면 생략)
aws s3 mb s3://finance-knowledge-base-bucket --region us-east-1

# 테스트 문서 업로드
echo "This is a test document for knowledge base." > test_document.txt
aws s3 cp test_document.txt s3://finance-knowledge-base-bucket/documents/
```

#### 3-2: Knowledge Base 생성 (AWS Console)
1. **Bedrock Console** → 좌측 메뉴 "Knowledge bases" 클릭
2. **"Create knowledge base"** 클릭
3. **Knowledge base 설정**:
   - Name: `finance-knowledge-base`
   - Description: `Financial documents knowledge base`
   - Service role: `AmazonBedrockExecutionRoleForKnowledgeBase_[timestamp]` (자동 생성)

4. **Data source 설정**:
   - Data source name: `finance-documents`
   - S3 URI: `s3://finance-knowledge-base-bucket/documents/`
   - Chunking strategy: `Default chunking` (기본 청킹)

5. **Embeddings model 설정**:
   - Embeddings model: `Titan Embeddings G1 - Text`
   - Dimensions: `1536`

6. **Vector database 설정**:
   - Vector database: `Quick create a new vector store` (OpenSearch Serverless 자동 생성)
   - Collection name: `finance-knowledge-collection`

7. **"Create knowledge base"** 클릭

#### 3-3: Knowledge Base 동기화
1. Knowledge base 생성 완료 후 **"Sync"** 클릭
2. S3 버킷의 문서들이 자동으로 벡터화되어 인덱싱됨
3. 동기화 완료까지 5-10분 소요

### Step 4: Bedrock + S3 연결 테스트
```python
# test_bedrock_knowledge_base.py
import boto3
import json

def test_bedrock_knowledge_base():
    # Bedrock Agent Runtime 클라이언트 생성
    bedrock_agent = boto3.client(
        service_name='bedrock-agent-runtime',
        region_name='us-east-1'
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
                    'modelArn': 'arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0'
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
        region_name='us-east-1'
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

### Step 5: S3 문서 업로드 및 동기화 자동화
```python
# s3_knowledge_base_manager.py
import boto3
import os
from datetime import datetime

class S3KnowledgeBaseManager:
    def __init__(self, bucket_name, knowledge_base_id):
        self.s3_client = boto3.client('s3', region_name='us-east-1')
        self.bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-1')
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

## 7. 로컬 환경 연결 테스트

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
                region_name='us-east-1'
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
    
    # OpenSearch 엔드포인트를 여기에 입력
    opensearch_endpoint = "finance-search-domain-xxxxx.ap-northeast-2.es.amazonaws.com"
    opensearch_ok = tester.test_opensearch(opensearch_endpoint)
    
    bedrock_ok = tester.test_bedrock()
    
    # 결과 요약
    print("\n=== 테스트 결과 요약 ===")
    print(f"S3: {'✓ 성공' if s3_ok else '✗ 실패'}")
    print(f"OpenSearch: {'✓ 성공' if opensearch_ok else '✗ 실패'}")
    print(f"Bedrock: {'✓ 성공' if bedrock_ok else '✗ 실패'}")
```

---

## 8. Config 파일 업데이트

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
    "hosts": ["https://finance-search-domain-xxxxx.ap-northeast-2.es.amazonaws.com"],
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
    "aws_region": "us-east-1",
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

S3_BUCKET_NAME=finance-app-bucket-xxxxx
OPENSEARCH_ENDPOINT=finance-search-domain-xxxxx.ap-northeast-2.es.amazonaws.com
```

---

## 트러블슈팅

### 일반적인 문제와 해결 방법

1. **패키지 의존성 충돌 (boto3, botocore, awscli)**
   ```powershell
   # 증상: ImportError, 버전 호환성 오류
   # 해결: 호환되는 버전으로 재설치
   pip uninstall boto3 botocore awscli aiobotocore s3transfer -y
   pip install boto3==1.34.0 botocore==1.34.0 s3transfer==0.9.0 awscli==1.32.0
   ```

2. **Access Denied 오류**
   - IAM 사용자 권한 확인
   - 정책이 올바르게 연결되었는지 확인
   - AWS CLI 자격 증명이 올바른지 확인

3. **Connection Timeout**
   - 보안 그룹 설정 확인 (OpenSearch)
   - 리전 설정이 올바른지 확인
   - VPN이나 프록시 설정 확인

4. **Bedrock Model Not Found**
   - 모델 액세스가 승인되었는지 확인
   - 올바른 리전(us-east-1)을 사용하는지 확인
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
4. CloudWatch로 비용 알림 설정

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