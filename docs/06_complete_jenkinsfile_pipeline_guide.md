# 🏗️ 완전한 Jenkinsfile Pipeline as Code 구현 가이드

> **목적**: 저장소에 Jenkinsfile을 추가하여 Pipeline as Code를 구현하고, 완전 자동화된 CI/CD 파이프라인을 구축합니다.
>
> **💡 Pipeline as Code란?**: Jenkins 파이프라인 설정을 코드로 관리하여 버전 관리, 코드 리뷰, 재사용이 가능한 방식입니다.

---

## 🏗️ Pipeline as Code의 장점 이해하기

### 기존 방식 vs Pipeline as Code

| 기존 방식 (Jenkins UI 설정) | Pipeline as Code (Jenkinsfile) |
|---------------------------|--------------------------------|
| ❌ Jenkins UI에서 수동 설정 | ✅ 코드로 파이프라인 정의 |
| ❌ 설정 변경 이력 추적 어려움 | ✅ Git으로 변경 이력 관리 |
| ❌ 팀원 간 설정 공유 어려움 | ✅ 코드 리뷰로 파이프라인 검토 |
| ❌ 백업/복구 복잡 | ✅ Git으로 자동 백업 |
| ❌ 다른 프로젝트에 재사용 어려움 | ✅ Jenkinsfile 복사로 쉬운 재사용 |

### 우리가 구현할 파이프라인 흐름

```
📥 GitHub Push
    ↓
🔍 소스코드 체크아웃 & 환경 확인
    ↓
🧪 코드 품질 검사 (Python Lint, Docker 파일 검사)
    ↓
🏗️ Docker 이미지 빌드 (캐시 활용, 보안 검사)
    ↓
📤 Docker Hub 업로드 (태그 관리)
    ↓
🚀 Deploy Server 자동 배포 (무중단 배포)
    ↓
🧪 배포 후 통합 테스트
    ↓
📧 결과 알림 (성공/실패)
```

---

## 📁 Step 1: Jenkinsfile을 프로젝트에 추가 (5분)

### 1️⃣ Jenkinsfile 생성 확인

#### A. Jenkinsfile이 이미 생성되어 있는지 확인
```bash
# 프로젝트 루트 디렉토리에서 확인
cd C:\SKN12-FINAL-2TEAM
ls -la | findstr Jenkinsfile

# 또는 Windows에서
dir | findstr Jenkinsfile
```

#### B. Jenkinsfile 내용 확인 및 수정
```bash
# Jenkinsfile이 있다면 내용 확인
type Jenkinsfile

# ⚠️ 중요: 다음 부분을 실제 값으로 수정해야 합니다:
# Line 21: [Docker-Hub-사용자명] → 실제 Docker Hub 사용자명
# Line 29: [Deploy-Server-IP] → 실제 Deploy Server IP 주소
```

#### C. 필요한 값으로 Jenkinsfile 수정
```powershell
# PowerShell에서 실제 값으로 교체
# 메모장으로 Jenkinsfile 열기
notepad Jenkinsfile

# 또는 VS Code가 있다면
code Jenkinsfile

# 수정해야 할 내용:
# 1. DOCKER_IMAGE = "[Docker-Hub-사용자명]/ai-trading-platform" 
#    → DOCKER_IMAGE = "skn12-trading/ai-trading-platform" (예시)
#
# 2. DEPLOY_SERVER = "[Deploy-Server-IP]"
#    → DEPLOY_SERVER = "52.79.234.56" (예시 - 실제 Deploy Server IP)
```

---

## 🔧 Step 2: Jenkins Job을 Pipeline from SCM으로 변경 (10분)

### 2️⃣ 기존 Jenkins Job 설정 변경

#### A. Jenkins 웹 UI에서 Job 설정 수정
```
1. Jenkins 접속: http://[Jenkins-IP]:18080
2. 로그인: admin / skn12-jenkins-2025!
3. "SKN12-Trading-Platform-CI" Job 클릭
4. 왼쪽 메뉴에서 "Configure" 클릭
```

#### B. Pipeline 설정 변경
```
"Pipeline" 섹션에서:

기존 설정:
❌ Definition: Pipeline script (직접 스크립트 작성)

새 설정:
✅ Definition: Pipeline script from SCM

SCM 설정:
- SCM: Git
- Repository URL: https://github.com/[사용자명]/SKN12-FINAL-2TEAM.git
- Credentials: github-token (기존에 설정한 GitHub Token)
- Branches to build: */main (또는 원하는 브랜치)
- Script Path: Jenkinsfile (기본값, 변경 안 함)
```

#### C. 추가 옵션 설정
```
Advanced 옵션 (필요 시):
- Lightweight checkout: ✅ 체크 (빠른 체크아웃)
- Shallow clone: ✅ 체크 (디스크 공간 절약)
- Clone depth: 1 (최신 커밋만 다운로드)
```

#### D. 설정 저장
```
"Save" 버튼 클릭
→ Jenkins가 이제 GitHub의 Jenkinsfile을 사용하도록 설정됨
```

---

## 📤 Step 3: Jenkinsfile을 GitHub에 커밋 (5분)

### 3️⃣ Git으로 Jenkinsfile 추가

#### A. 현재 Git 상태 확인
```bash
# 프로젝트 디렉토리에서
cd C:\SKN12-FINAL-2TEAM

# Git 상태 확인
git status

# Jenkinsfile이 Untracked files에 표시되어야 함
```

#### B. Jenkinsfile 커밋 및 푸시
```bash
# Jenkinsfile을 Git에 추가
git add Jenkinsfile

# 커밋 메시지와 함께 커밋
git commit -m "Add Jenkinsfile for Pipeline as Code implementation

✨ Features:
- Complete CI/CD pipeline with 6 stages
- Automated Docker build and push to Docker Hub
- Auto-deploy to production server
- Code quality checks (Python lint, Docker files)
- Post-deploy integration testing
- Comprehensive error handling and cleanup

🔧 Configuration:
- Multi-branch support (main → PROD, develop → DEBUG)
- Docker cache optimization for faster builds
- Zero-downtime deployment strategy
- Health checks for deployed services

📊 Monitoring:
- Build time tracking
- Resource usage monitoring
- Automated cleanup processes
- Detailed logging for troubleshooting"

# GitHub에 푸시
git push origin main
```

#### C. GitHub에서 Jenkinsfile 확인
```
1. 웹 브라우저에서 GitHub 저장소 접속
2. 루트 디렉토리에 "Jenkinsfile" 파일이 있는지 확인
3. 파일 클릭하여 내용이 올바른지 확인
4. 실제 값으로 수정되었는지 재확인:
   - Docker Hub 사용자명
   - Deploy Server IP 주소
```

---

## 🧪 Step 4: Pipeline from SCM 테스트 (15분)

### 4️⃣ 첫 번째 Pipeline 실행

#### A. Jenkins에서 수동 빌드 실행
```
1. Jenkins → "SKN12-Trading-Platform-CI" Job 페이지
2. "Build Now" 클릭
3. Build History에서 새로운 빌드 시작 확인
```

#### B. Pipeline 단계별 모니터링
```
Build 페이지에서 확인할 내용:

1. "Pipeline Steps" 또는 "Stage View" 클릭
2. 각 Stage 실행 상태 모니터링:

Stage 1 - 📥 Checkout & Environment Setup:
- GitHub에서 Jenkinsfile 자동 다운로드
- 소스코드 체크아웃
- 환경 정보 출력

Stage 2 - 🔍 Code Quality Check:
- Python 코드 문법 검사
- Docker 파일 존재 확인

Stage 3 - 🐳 Build Docker Image:
- 이미지 빌드 시간 측정
- 컨테이너 실행 테스트
- 이미지 크기 확인

Stage 4 - 📤 Push to Docker Hub:
- Docker Hub 로그인
- 이미지 업로드 시간 측정
- 업로드 완료 확인

Stage 5 - 🚀 Deploy to Server:
- SSH 연결 및 배포
- 기존 컨테이너 중지/제거
- 새 컨테이너 시작
- 헬스체크 수행

Stage 6 - 🧪 Post-Deploy Testing:
- 외부에서 서비스 접근 테스트
- Base Web Server (8000) 응답 확인
- Model Server (8001) 응답 확인
```

#### C. Console Output 상세 확인
```
"Console Output" 클릭하여 다음 내용 확인:

✅ 성공 지표:
- "📥 GitHub에서 소스코드 다운로드 중..." 
- "✅ Docker 이미지 빌드 완료"
- "✅ Docker Hub 업로드 완료"
- "✅ Base Web Server (8000) 정상 응답"
- "✅ Model Server (8001) 정상 응답"
- "🎉 빌드가 성공적으로 완료되었습니다!"

❌ 실패 시 확인사항:
- 어느 Stage에서 실패했는지 확인
- 오류 메시지 복사하여 문제 해결
```

### 4️⃣ Blue Ocean으로 시각적 확인

#### A. Blue Ocean UI 접속
```
1. Jenkins Dashboard 왼쪽 메뉴 "Open Blue Ocean" 클릭
2. "SKN12-Trading-Platform-CI" 파이프라인 클릭
3. 최신 빌드 클릭
```

#### B. 시각적 파이프라인 분석
```
Blue Ocean에서 확인할 내용:

🟢 녹색 박스: 성공한 Stage
🔴 빨간색 박스: 실패한 Stage  
🟡 노란색 박스: 실행 중인 Stage
⚪ 회색 박스: 아직 실행되지 않은 Stage

각 Stage 클릭 시:
- 실행 시간 확인
- 로그 출력 확인
- 오류 메시지 확인 (실패 시)
```

---

## 🔄 Step 5: 자동 빌드 테스트 (코드 변경 후 Push) (10분)

### 5️⃣ 실제 코드 변경으로 자동 빌드 테스트

#### A. 간단한 코드 변경
```bash
# 프로젝트 디렉토리에서
cd C:\SKN12-FINAL-2TEAM

# 테스트용 파일 생성 (파이프라인 검증용)
echo "Pipeline as Code 테스트 - $(Get-Date)" > pipeline-test.txt

# README 업데이트 (선택사항)
echo "
## 🚀 CI/CD Pipeline Status

[![Build Status](http://[Jenkins-IP]:18080/buildStatus/icon?job=SKN12-Trading-Platform-CI)](http://[Jenkins-IP]:18080/job/SKN12-Trading-Platform-CI/)

### Pipeline Stages
1. 📥 Checkout & Environment Setup
2. 🔍 Code Quality Check  
3. 🐳 Build Docker Image
4. 📤 Push to Docker Hub
5. 🚀 Deploy to Server
6. 🧪 Post-Deploy Testing

### Service URLs
- Base Web Server: http://[Deploy-Server-IP]:8000
- Model Server: http://[Deploy-Server-IP]:8001
- Docker Hub: https://hub.docker.com/r/[사용자명]/ai-trading-platform
" >> README.md
```

#### B. 변경사항 커밋 및 푸시
```bash
# 변경사항 확인
git status

# 모든 변경사항 추가
git add .

# 의미있는 커밋 메시지
git commit -m "Test Pipeline as Code implementation

🧪 Testing:
- Added pipeline-test.txt for build verification
- Updated README.md with CI/CD status badges
- Triggered automatic build via GitHub webhook

🔄 Expected behavior:
- Jenkins should auto-detect this push
- Complete pipeline should execute automatically
- Both servers should redeploy with latest code"

# GitHub에 푸시 (자동 빌드 트리거)
git push origin main
```

#### C. Jenkins에서 자동 빌드 확인
```
1. Git push 완료 후 즉시 Jenkins 웹 UI로 이동
2. "SKN12-Trading-Platform-CI" Job 페이지에서 새 빌드 시작 확인
3. Build History에서 자동으로 시작된 빌드 번호 확인
4. 자동 빌드가 시작되면 Webhook 연동 성공!

Webhook 문제 시 확인:
- GitHub → Settings → Webhooks → Recent Deliveries
- Jenkins 로그: docker logs jenkins-master | grep webhook
```

---

## 📊 Step 6: Pipeline 모니터링 및 최적화 (10분)

### 6️⃣ 빌드 성능 분석

#### A. 빌드 시간 분석
```
1. Blue Ocean에서 파이프라인 클릭
2. "Trends" 탭으로 이동
3. 빌드 시간 트렌드 확인:
   - 전체 빌드 시간
   - Stage별 실행 시간
   - 시간 변화 추이
```

#### B. 리소스 사용량 모니터링
```bash
# SSH로 Jenkins Server 접속
ssh -i "C:\aws-keys\skn12-trading-keypair.pem" ubuntu@[Jenkins-IP]

# 빌드 중 리소스 사용량 확인
watch -n 5 'echo "=== 시스템 리소스 ===" && free -h && echo "" && df -h && echo "" && docker stats --no-stream'

# 빌드 완료 후 정리 상태 확인
docker images | head -10
docker ps -a | head -10
```

#### C. 로그 분석 및 최적화 포인트 찾기
```bash
# Jenkins 컨테이너 로그에서 성능 관련 정보 확인
docker logs jenkins-master | grep -i "시간\|time\|duration" | tail -20

# Docker 빌드 캐시 활용도 확인
docker logs jenkins-master | grep -i "cache\|cached" | tail -10
```

### 6️⃣ Pipeline 최적화 설정

#### A. 고급 Pipeline 옵션 (Jenkinsfile 수정)
```groovy
// 병렬 처리 예시 (코드 품질 검사 단계)
stage('🔍 Code Quality Check') {
    parallel {
        stage('Python Lint') {
            // Python 코드 검사
        }
        stage('Docker Files Check') {
            // Docker 파일 검사
        }
        stage('Security Scan') {
            // 보안 스캔 (추가)
        }
    }
}

// 조건부 실행 예시
stage('🚀 Deploy to Production') {
    when {
        branch 'main'  // main 브랜치에서만 실행
    }
    steps {
        // 프로덕션 배포 로직
    }
}
```

#### B. 캐시 최적화 설정
```groovy
// Docker 빌드 캐시 활용
sh '''
    # 이전 이미지를 캐시로 활용
    docker build \
        --cache-from ${DOCKER_IMAGE}:latest \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        -t ${DOCKER_IMAGE}:${IMAGE_TAG} \
        .
'''
```

---

## 🔔 Step 7: 알림 및 모니터링 설정 (선택사항) (10분)

### 7️⃣ Slack 알림 설정 (플러그인 필요)

#### A. Slack 플러그인 설치
```
1. Jenkins → "Manage Jenkins" → "Plugins"
2. "Available plugins"에서 "Slack Notification" 검색
3. 설치 후 Jenkins 재시작
```

#### B. Slack Workspace 연동
```
1. Slack App 생성: https://api.slack.com/apps
2. Jenkins에서 Slack 설정:
   - "Manage Jenkins" → "System"
   - "Slack" 섹션에서 Workspace, Token 설정
```

#### C. Jenkinsfile에 Slack 알림 추가
```groovy
post {
    success {
        slackSend(
            channel: '#ci-cd',
            color: 'good',
            message: "✅ 배포 성공: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
        )
    }
    failure {
        slackSend(
            channel: '#ci-cd',
            color: 'danger',
            message: "❌ 빌드 실패: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
        )
    }
}
```

### 7️⃣ 이메일 알림 설정

#### A. SMTP 설정
```
1. "Manage Jenkins" → "System"
2. "E-mail Notification" 섹션:
   - SMTP server: smtp.gmail.com
   - Use SMTP Authentication: ✅
   - Username: [Gmail 계정]
   - Password: [앱 비밀번호]
   - SMTP Port: 587
   - Use TLS: ✅
```

#### B. Pipeline에 이메일 알림 추가
```groovy
post {
    failure {
        emailext (
            subject: "❌ Jenkins 빌드 실패: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
            body: """
빌드가 실패했습니다.

빌드 정보:
- Job: ${env.JOB_NAME}
- 빌드 번호: ${env.BUILD_NUMBER}
- 브랜치: ${env.BRANCH_NAME}
- 실패 시간: ${new Date()}

로그 확인: ${env.BUILD_URL}console
            """,
            to: "admin@skn12-trading.com"
        )
    }
}
```

---

## ✅ Pipeline as Code 구현 완료 체크리스트

### 🎯 Jenkinsfile 설정 완료:
- [ ] Jenkinsfile이 프로젝트 루트에 생성됨
- [ ] Docker Hub 사용자명과 Deploy Server IP가 올바르게 설정됨
- [ ] GitHub에 Jenkinsfile이 커밋 및 푸시됨
- [ ] Jenkins Job이 "Pipeline script from SCM"으로 변경됨

### 🔄 자동화 테스트 완료:
- [ ] 수동 빌드 테스트 성공 ("Build Now")
- [ ] 자동 빌드 테스트 성공 (GitHub Push 후 자동 실행)
- [ ] 모든 6개 Stage가 성공적으로 완료됨
- [ ] Deploy Server에 서비스가 정상 배포됨

### 📊 모니터링 설정 완료:
- [ ] Blue Ocean UI로 시각적 파이프라인 확인
- [ ] Build History에서 성공/실패 상태 확인
- [ ] Console Output으로 상세 로그 확인
- [ ] 빌드 시간 및 리소스 사용량 모니터링

### 🔔 알림 설정 완료 (선택사항):
- [ ] Slack 알림 설정 (플러그인 설치 시)
- [ ] 이메일 알림 설정
- [ ] 성공/실패 시 적절한 알림 수신

---

## 🔧 문제 해결 및 고급 팁

### 자주 발생하는 문제들:

#### 문제 1: "Jenkinsfile not found"
```
원인: Git 저장소에 Jenkinsfile이 없거나 경로가 잘못됨

해결책:
1. GitHub에서 Jenkinsfile 존재 확인
2. Jenkins Job 설정에서 "Script Path" 확인 (기본값: Jenkinsfile)
3. 브랜치 설정 확인 (*/main)
```

#### 문제 2: Pipeline 단계별 실패
```
Stage 1 실패: GitHub 접근 권한 확인
- github-token Credentials 재설정
- 저장소 URL 정확성 확인

Stage 3 실패: Docker 빌드 오류
- base_server 디렉토리 존재 확인
- Dockerfile 문법 오류 확인
- 메모리 부족 여부 확인

Stage 4 실패: Docker Hub 업로드 오류
- dockerhub-credentials 재설정
- 네트워크 연결 확인
- Docker Hub 저장소 권한 확인

Stage 5 실패: SSH 연결 오류
- deploy-server-ssh-key 재설정
- Deploy Server 보안 그룹 확인
- SSH 키 권한 확인
```

#### 문제 3: 성능 최적화
```
빌드 속도 향상:
1. Docker 빌드 캐시 활용
2. 병렬 처리 단계 추가
3. 불필요한 패키지 설치 제거

리소스 사용량 최적화:
1. 정기적인 이미지 정리
2. 빌드 캐시 주기적 정리
3. Jenkins 힙 메모리 조정
```

### 고급 Pipeline 패턴:

#### Multi-branch Pipeline:
```groovy
pipeline {
    agent any
    
    stages {
        stage('Deploy') {
            parallel {
                stage('Deploy to Staging') {
                    when { branch 'develop' }
                    steps {
                        // 스테이징 배포
                    }
                }
                stage('Deploy to Production') {
                    when { branch 'main' }
                    steps {
                        // 프로덕션 배포
                    }
                }
            }
        }
    }
}
```

#### 조건부 실행:
```groovy
stage('Integration Tests') {
    when {
        not { changeRequest() }  // PR이 아닐 때만
        anyOf {
            branch 'main'
            branch 'develop'
        }
    }
    steps {
        // 통합 테스트
    }
}
```

---

## 🎯 다음 단계 미리보기

### 1️⃣ 무중단 배포 구현:
- Blue-Green 배포 전략
- Health Check 기반 트래픽 전환
- 자동 롤백 기능

### 2️⃣ 모니터링 강화:
- Prometheus + Grafana 연동
- 애플리케이션 메트릭 수집
- 알람 및 대시보드 구성

### 3️⃣ 보안 강화:
- 컨테이너 이미지 보안 스캔
- Secret 관리 개선
- 네트워크 보안 설정

---

## 🎉 축하합니다!

완전한 Pipeline as Code가 구현되었습니다! 🏗️

### ✅ 지금까지 구축한 것:
- 📝 **Jenkinsfile**: 모든 파이프라인 설정이 코드로 관리됨
- 🔄 **완전 자동화**: GitHub Push → 빌드 → 테스트 → 배포
- 📊 **시각적 모니터링**: Blue Ocean으로 파이프라인 상태 확인
- 🔔 **알림 시스템**: 빌드 결과를 즉시 알림으로 수신

### 🚀 달성한 것:
1. **코드 변경 1초** → **서비스 배포 완료** (전체 5-10분)
2. **완전 무인 자동화** (사람 개입 없이 배포)
3. **품질 보장** (테스트 + 헬스체크)
4. **장애 대응** (자동 롤백 + 알림)

이제 진정한 DevOps 환경이 완성되었습니다! 코드를 Push만 하면 자동으로 전체 시스템이 업데이트됩니다! 🚀