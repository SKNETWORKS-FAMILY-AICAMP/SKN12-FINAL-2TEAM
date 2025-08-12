# 🐳 Docker Hub 계정 설정 및 연동 가이드 (초보자용)

> **목적**: Docker Hub 계정을 생성하고 Jenkins CI/CD 파이프라인에서 Docker 이미지를 자동으로 업로드/다운로드할 수 있도록 설정합니다.
>
> **💡 Docker Hub란?**: GitHub가 소스코드 저장소라면, Docker Hub는 Docker 이미지 저장소입니다. 우리가 빌드한 애플리케이션 이미지를 저장하고 배포 서버에서 다운로드받을 수 있습니다.

---

## 🏗️ Docker Hub의 역할 이해하기

```
🏠 개발자 PC
    ↓ (git push)
📱 GitHub (소스코드 저장소)
    ↓ (Webhook)
📦 Jenkins Server
    ├─ 소스코드 다운로드 
    ├─ Docker 이미지 빌드
    └─ Docker Hub에 이미지 업로드 📤
         ↓
🐳 Docker Hub (이미지 저장소)
    ├─ ai-trading-platform:latest
    ├─ ai-trading-platform:v1.0.0  
    └─ ai-trading-platform:dev
         ↓ (docker pull) 📥
🚀 Deploy Server
    └─ 이미지 다운로드 후 컨테이너 실행
```

**Docker Hub 저장소 구조**:
```
내 계정: skn12-trading (예시)
└── ai-trading-platform (저장소)
    ├── latest (최신 버전)
    ├── v1.0.0 (릴리스 버전)
    ├── v1.0.1 (패치 버전)
    └── dev (개발 버전)
```

---

## 🔐 Step 1: Docker Hub 계정 생성 (5분)

### 1️⃣ Docker Hub 웹사이트 접속

#### A. 계정 생성 시작
```
1. 웹 브라우저에서 https://hub.docker.com 접속
2. 우측 상단 "Sign Up" 버튼 클릭
```

#### B. 계정 정보 입력
```
Username: skn12-trading (또는 원하는 이름)
         ⚠️ 주의: 이 이름이 이미지 URL에 포함됩니다
         예: skn12-trading/ai-trading-platform

Email: [본인 이메일 주소]
Password: [강력한 비밀번호 설정]
         ⚠️ 추천: 대소문자+숫자+특수문자 조합, 12자 이상

✅ Terms of Service 동의 체크박스 선택
✅ reCAPTCHA 인증 완료
```

#### C. 이메일 인증
```
1. "Sign Up" 버튼 클릭
2. 이메일함에서 Docker Hub 인증 메일 확인
3. "Verify email address" 버튼 클릭
4. "Your email has been verified" 메시지 확인
```

#### D. 로그인 확인
```
1. https://hub.docker.com 에서 로그인
2. Dashboard가 표시되면 성공
3. 우측 상단에 사용자명이 표시되는지 확인
```

### 1️⃣ Docker Hub 플랜 확인
```
💰 Free Plan (무료):
- Public 저장소: 무제한
- Private 저장소: 1개  
- 동시 빌드: 1개
- 월 다운로드 제한: 200개 (개인용 충분)

📝 우리 프로젝트는 Free Plan으로 충분합니다!
```

---

## 📦 Step 2: 저장소(Repository) 생성 (5분)

### 2️⃣ 새 저장소 생성

#### A. 저장소 생성 시작
```
1. Docker Hub Dashboard에서 "Create Repository" 버튼 클릭
2. 또는 상단 메뉴 "Repositories" → "Create Repository"
```

#### B. 저장소 정보 입력
```
Repository Name: ai-trading-platform
Description: SKN12 Final Project - AI Trading Platform
Visibility: Public (무료 플랜에서 Private는 1개만 가능)

📝 설명 예시:
"AI-powered trading platform with real-time market analysis, automated trading algorithms, and comprehensive portfolio management. Built with FastAPI, Redis, MySQL, and AWS services."
```

#### C. 저장소 생성 완료
```
1. "Create" 버튼 클릭
2. "Repository created successfully" 메시지 확인
3. 저장소 URL 확인: 
   https://hub.docker.com/r/[사용자명]/ai-trading-platform
```

#### D. 저장소 설정 확인
```
생성된 저장소 페이지에서 확인할 정보:
- Repository Name: ai-trading-platform
- Full Name: [사용자명]/ai-trading-platform  
- Docker Pull Command: docker pull [사용자명]/ai-trading-platform
- Status: Public
- Automated Builds: Not configured (수동 업로드)
```

---

## 🔑 Step 3: Access Token 생성 (Jenkins 연동용) (5분)

> **💡 Access Token이란?**: 비밀번호 대신 사용하는 인증 키입니다. 더 안전하고 권한을 세밀하게 제어할 수 있습니다.

### 3️⃣ Access Token 생성

#### A. Account Settings 이동
```
1. Docker Hub 우측 상단 사용자명 클릭
2. 드롭다운 메뉴에서 "Account Settings" 선택
3. 또는 https://hub.docker.com/settings/general 직접 접속
```

#### B. Security 설정 이동
```
1. 왼쪽 메뉴에서 "Security" 클릭
2. "Access Tokens" 섹션 확인
```

#### C. 새 Access Token 생성
```
1. "New Access Token" 버튼 클릭
2. Token settings 입력:
   
   Token Description: Jenkins-CI-CD-Token
   (설명: Jenkins에서 이미지 업로드용 토큰)
   
   Access permissions: Read, Write, Delete
   ✅ Read: 이미지 다운로드
   ✅ Write: 이미지 업로드  
   ✅ Delete: 이미지 삭제 (필요 시)
```

#### D. Token 생성 및 복사
```
1. "Generate" 버튼 클릭
2. 생성된 Token 표시:
   Token: dckr_pat_1234567890abcdef... (예시)
   
   ⚠️ 매우 중요: 이 Token은 한 번만 표시됩니다!
   반드시 안전한 곳에 복사해두세요!

3. "Copy" 버튼 클릭하여 클립보드에 복사
4. 메모장에 임시 저장:
```

```
=== Docker Hub 접속 정보 ===
Username: [사용자명]
Email: [이메일]
Repository: [사용자명]/ai-trading-platform
Access Token: dckr_pat_1234567890abcdef...

⚠️ 이 정보는 Jenkins 설정에서 사용됩니다!
```

#### E. Token 저장 완료
```
"Done" 버튼 클릭하여 Token 생성 완료
```

---

## 🧪 Step 4: 로컬에서 Docker Hub 연동 테스트 (10분)

> **💡 이 단계는**: Jenkins 설정 전에 로컬 Windows 환경에서 Docker Hub 연동이 정상 작동하는지 테스트합니다.

### 4️⃣ 로컬 Docker Hub 로그인 테스트

#### A. PowerShell에서 Docker 로그인
```powershell
# PowerShell 실행 (관리자 권한 아님)
# Docker Desktop이 실행 중인지 확인

# Docker 버전 확인
docker --version

# Docker Hub 로그인 (Username과 Token 사용)
docker login

# 프롬프트에서 입력:
Username: [Docker Hub 사용자명]
Password: [Access Token 붙여넣기 - 비밀번호 아님!]

# 성공 시 출력:
# Login Succeeded
```

#### B. 로그인 상태 확인
```powershell
# 로그인 정보 확인
docker system info | findstr "Username"

# 결과 예시:
# Username: skn12-trading
```

### 4️⃣ 테스트 이미지 빌드 및 업로드

#### A. 간단한 테스트 이미지 생성
```powershell
# 임시 디렉토리 생성
mkdir C:\docker-test
cd C:\docker-test

# 간단한 Dockerfile 생성
echo 'FROM nginx:alpine
LABEL description="SKN12 Trading Platform Test Image"
COPY index.html /usr/share/nginx/html/
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]' > Dockerfile

# 테스트용 HTML 파일 생성
echo '<html>
<head><title>SKN12 Trading Platform</title></head>
<body>
<h1>🚀 AI Trading Platform</h1>
<p>Docker Hub 연동 테스트 성공!</p>
<p>Build Time: %date% %time%</p>
</body>
</html>' > index.html
```

#### B. 이미지 빌드
```powershell
# 이미지 빌드 (사용자명을 실제 Docker Hub 사용자명으로 변경)
docker build -t [사용자명]/ai-trading-platform:test .

# 예시:
docker build -t skn12-trading/ai-trading-platform:test .

# 빌드 성공 확인
docker images | findstr ai-trading-platform
```

#### C. Docker Hub에 이미지 업로드
```powershell
# 이미지 푸시 (업로드)
docker push [사용자명]/ai-trading-platform:test

# 예시:
docker push skn12-trading/ai-trading-platform:test

# 업로드 진행 상황:
# The push refers to repository [docker.io/skn12-trading/ai-trading-platform]
# abc123: Pushed
# def456: Pushed  
# test: digest: sha256:789... size: 1234
```

#### D. Docker Hub 웹에서 확인
```
1. 웹 브라우저에서 Docker Hub 접속
2. 본인 저장소로 이동: 
   https://hub.docker.com/r/[사용자명]/ai-trading-platform
3. "Tags" 탭에서 "test" 태그 확인
4. 업로드 시간, 이미지 크기 등 정보 확인
```

### 4️⃣ 이미지 다운로드 테스트

#### A. 로컬 이미지 삭제 후 재다운로드
```powershell
# 로컬 이미지 삭제
docker rmi [사용자명]/ai-trading-platform:test

# Docker Hub에서 이미지 다운로드
docker pull [사용자명]/ai-trading-platform:test

# 다운로드 확인
docker images | findstr ai-trading-platform

# 컨테이너 실행 테스트
docker run -d -p 8080:80 --name test-container [사용자명]/ai-trading-platform:test

# 웹 브라우저에서 http://localhost:8080 접속
# "🚀 AI Trading Platform" 페이지가 표시되면 성공!

# 테스트 컨테이너 정리
docker stop test-container
docker rm test-container
```

#### B. 테스트 파일 정리
```powershell
# 테스트 디렉토리 삭제
cd C:\
rmdir /s C:\docker-test

# 테스트 이미지 삭제 (선택사항)
docker rmi [사용자명]/ai-trading-platform:test
```

---

## ⚙️ Step 5: Jenkins 연동 준비 (Credentials 정보 정리) (5분)

### 5️⃣ Jenkins에서 사용할 정보 정리

#### A. Docker Hub Credentials 정보 정리
```
다음 정보를 Jenkins 설정 시 사용합니다:

=== Jenkins Docker Hub Credentials ===
Type: Username with password
ID: dockerhub-credentials  
Description: Docker Hub access for SKN12 Trading Platform
Username: [Docker Hub 사용자명]
Password: [Access Token] (비밀번호 아님!)

=== Docker 이미지 정보 ===  
Registry: docker.io (기본값)
Repository: [사용자명]/ai-trading-platform
Image Tags:
- latest (최신 개발 버전)
- v1.0.0 (릴리스 버전)  
- dev (개발 브랜치)
- prod (운영 브랜치)
```

#### B. Jenkinsfile에서 사용할 환경 변수
```groovy
// Jenkins 파이프라인에서 사용할 환경 변수들
environment {
    DOCKER_REGISTRY = "docker.io"
    DOCKER_IMAGE = "[사용자명]/ai-trading-platform"
    DOCKER_CREDENTIALS = "dockerhub-credentials"
    IMAGE_TAG = "${env.BUILD_NUMBER}"  // Jenkins 빌드 번호
    GIT_COMMIT_SHORT = "${env.GIT_COMMIT.take(7)}" // Git 커밋 해시 7자리
}
```

#### C. 이미지 태깅 전략
```
태그 규칙:
1. latest: 항상 최신 main 브랜치 버전
2. v{major}.{minor}.{patch}: 릴리스 버전 (예: v1.0.0)
3. dev-{date}: 개발 버전 (예: dev-20250812)
4. build-{number}: 빌드 번호 (예: build-123)
5. commit-{hash}: Git 커밋 해시 (예: commit-abc1234)

사용 예시:
- 개발: skn12-trading/ai-trading-platform:latest
- 운영: skn12-trading/ai-trading-platform:v1.0.0
- 테스트: skn12-trading/ai-trading-platform:dev-20250812
```

---

## 🔍 Step 6: Docker Hub 저장소 관리 및 최적화 (5분)

### 6️⃣ 저장소 설정 최적화

#### A. Repository 설정 개선
```
1. Docker Hub 저장소 페이지에서 "Settings" 탭 클릭
2. "General" 설정:
   - Description 업데이트 (상세한 프로젝트 설명)
   - README.md 작성 (선택사항)

3. "Collaborators" 설정:
   - 팀원이 있다면 협업자 추가
   - 권한 설정: Read, Write, Admin

4. "Webhooks" 설정 (고급):
   - 이미지 업로드 시 알림 받기
   - Slack, Discord 연동 가능
```

#### B. README 작성 (선택사항)
```markdown
# 🚀 AI Trading Platform

SKN12 Final Project - AI-powered trading platform with real-time market analysis.

## Features
- Real-time market data processing
- AI-based trading algorithms  
- Portfolio management
- Risk assessment tools

## Quick Start
```bash
# Pull the latest image
docker pull [사용자명]/ai-trading-platform:latest

# Run the application
docker run -d \
  --name trading-platform \
  -p 8000:8000 \
  -p 8001:8001 \
  -e APP_ENV=PROD \
  [사용자명]/ai-trading-platform:latest
```

## Architecture
- **Base Web Server**: Port 8000 (FastAPI)
- **Model Server**: Port 8001 (ML Services)
- **Database**: MySQL with sharding
- **Cache**: Redis with namespace isolation
- **Search**: OpenSearch for advanced queries
- **AI**: AWS Bedrock for model inference

## Environment Variables
- `APP_ENV`: Application environment (LOCAL/DEBUG/PROD)

## Volumes
- `/app/application/base_web_server`: Configuration files
- `/app/logs`: Application logs

## Tags
- `latest`: Latest development version
- `v1.x.x`: Stable releases
- `dev-YYYYMMDD`: Development snapshots
```

### 6️⃣ 보안 및 접근 관리

#### A. Access Token 관리
```
보안 모범 사례:
1. ✅ 토큰은 안전한 곳에 보관 (Jenkins Credentials)
2. ✅ 주기적으로 토큰 갱신 (6개월마다)
3. ✅ 불필요한 권한 제거 (Read-only로 충분한 경우)
4. ✅ 토큰 사용 로그 모니터링

토큰 갱신 방법:
1. Docker Hub → Account Settings → Security
2. 기존 토큰 "Delete" 
3. 새 토큰 생성
4. Jenkins Credentials 업데이트
```

#### B. 저장소 보안 설정
```
1. Private 저장소 고려 (중요한 운영 이미지)
2. Vulnerability Scanning 활성화
3. 오래된 이미지 태그 정리 (스토리지 절약)
4. Base 이미지 정기 업데이트
```

---

## 📊 Step 7: 모니터링 및 사용량 관리 (5분)

### 7️⃣ Docker Hub 사용량 확인

#### A. 사용량 대시보드 확인
```
1. Docker Hub → Account Settings → "Plan & billing"
2. 현재 사용량 확인:
   - Repository 개수: 1/무제한 (Public)
   - Storage 사용량: XXX MB
   - Pull 횟수: XXX/200 (월 제한)
   - Bandwidth 사용량: XXX GB

3. 월별 사용 패턴 모니터링
```

#### B. 사용량 최적화 팁
```
💰 비용 절약 및 효율성 개선:

1. 이미지 크기 최적화:
   - Multi-stage build 사용
   - 불필요한 패키지 제거
   - Alpine Linux 기반 이미지 사용

2. 태그 정리:
   - 오래된 개발 태그 삭제
   - 릴리스 버전만 장기 보관
   - 자동 정리 스크립트 작성

3. Layer 캐싱 활용:
   - 자주 변경되는 파일을 뒤쪽 레이어에 배치
   - 종속성 설치를 앞쪽 레이어에 배치
```

### 7️⃣ 알림 및 모니터링 설정

#### A. Docker Hub Webhooks 설정 (선택사항)
```
1. 저장소 → Settings → Webhooks
2. "Create webhook" 클릭
3. 설정:
   - Webhook name: jenkins-notification
   - Webhook URL: http://[Jenkins-IP]:18080/docker-hub-webhook/
   - Triggers: Repository push

4. Jenkins에서 빌드 트리거로 활용 가능
```

#### B. 이메일 알림 설정
```
1. Account Settings → Notifications
2. 활성화할 알림:
   - ✅ Repository push notifications
   - ✅ Security scan results  
   - ✅ Storage limit warnings
   - ✅ Pull rate limit warnings
```

---

## ✅ Docker Hub 설정 완료 체크리스트

### 🎯 기본 설정 완료:
- [ ] Docker Hub 계정 생성 및 이메일 인증
- [ ] 저장소 생성 (ai-trading-platform)
- [ ] Access Token 생성 및 안전한 보관
- [ ] 로컬에서 Docker Hub 로그인 테스트 성공
- [ ] 테스트 이미지 업로드/다운로드 성공

### 🔐 보안 설정 완료:
- [ ] Access Token 권한 적절히 설정 (Read, Write, Delete)
- [ ] Token 정보를 안전한 곳에 보관
- [ ] Jenkins Credentials 정보 준비 완료

### 📊 관리 설정 완료:
- [ ] 저장소 설명 및 README 작성
- [ ] 이미지 태깅 전략 수립
- [ ] 사용량 모니터링 설정
- [ ] 알림 설정 (선택사항)

### 📝 문서화 완료:
- [ ] Docker Hub 접속 정보 정리
- [ ] Jenkins 연동 정보 준비
- [ ] 이미지 태깅 규칙 문서화

---

## 🎯 다음 단계 미리보기

### 1️⃣ Jenkins 서버 설정:
- Docker Compose로 Jenkins 컨테이너 실행
- Docker Hub Credentials 등록
- Pipeline 플러그인 설치

### 2️⃣ GitHub 연동:
- GitHub Personal Access Token 생성
- Webhook 설정
- Jenkins Pipeline 구성

### 3️⃣ CI/CD 파이프라인 구축:
- Jenkinsfile 작성
- 자동 빌드 및 Docker Hub 푸시
- Deploy 서버로 자동 배포

---

## 💡 문제 해결 FAQ

### Q1: "Access denied" 오류가 발생해요
```
원인: Access Token 권한 부족 또는 잘못된 토큰

해결책:
1. Docker Hub에서 토큰 권한 확인 (Read, Write 필요)
2. 토큰 재생성 후 다시 로그인
3. Username과 Token이 정확한지 확인
```

### Q2: 이미지 푸시가 너무 느려요
```
원인: 이미지 크기가 크거나 네트워크 문제

해결책:
1. .dockerignore 파일로 불필요한 파일 제외
2. Multi-stage build로 최종 이미지 크기 축소
3. Docker layer 캐싱 활용
4. 안정적인 네트워크 환경에서 업로드
```

### Q3: 월 다운로드 제한에 걸렸어요
```
원인: Free Plan의 월 200회 다운로드 제한 초과

해결책:
1. 불필요한 pull 작업 줄이기
2. 로컬 캐시 활용하기
3. Pro Plan 업그레이드 고려 ($5/월)
4. 다른 Registry 사용 (AWS ECR, GitHub Container Registry)
```

### Q4: 이미지가 너무 많이 쌓여요
```
해결책: 자동 정리 스크립트 작성
```
```bash
#!/bin/bash
# 30일 이상 된 dev 태그 삭제
docker rmi $(docker images [사용자명]/ai-trading-platform --filter "dangling=false" --format "table {{.Repository}}:{{.Tag}}\t{{.CreatedAt}}" | grep "dev-" | awk '$2 < "'$(date -d '30 days ago' '+%Y-%m-%d')'" {print $1}')
```

---

## 🎉 축하합니다!

Docker Hub 설정이 완료되었습니다! 🐳

### ✅ 지금까지 구축한 것:
- 🔐 **Docker Hub 계정**: 안전한 이미지 저장소
- 📦 **저장소 생성**: ai-trading-platform 이미지 관리
- 🔑 **Access Token**: Jenkins 자동화를 위한 인증
- 🧪 **연동 테스트**: 로컬에서 업로드/다운로드 검증

### 🚀 다음 할 일:
1. **Jenkins 컨테이너 설치** 및 설정
2. **Docker Hub Credentials** Jenkins에 등록
3. **GitHub Webhook** 설정
4. **CI/CD Pipeline** 구성 및 테스트

이제 Docker 이미지 관리 인프라가 준비되었습니다. Jenkins와 연동하여 완전 자동화된 CI/CD 파이프라인을 만들어봅시다! 🚀